"""
Nightly Learning Agent - AWS Lambda Function

Analyzes user corrections to AI-generated offers by:
1. Fetching offers created in the past 3 days from S3
2. Comparing original AI product selections with final user-edited versions
3. Using Gemini AI to extract learnings from the differences
4. Storing product swap learnings in S3 CSV
5. Storing general rules in S3 text file
6. Tracking processing state to avoid duplicate analysis

Designed to run as AWS Lambda on CloudWatch schedule (daily at 2 AM).
"""

import json
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import asyncio
import httpx

# Google Generative AI for learning extraction
from google import genai
from google.genai import types


# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class OfferComparisonResult:
    """Result of comparing original AI offer with user-edited version."""
    
    def __init__(self):
        self.added_rows: List[Dict] = []
        self.deleted_rows: List[Dict] = []
        self.modified_rows: List[Dict] = []  # Changed product codes
        self.quantity_changes: List[Dict] = []
        self.has_changes: bool = False


class LearningAgent:
    """
    Analyzes offer corrections and generates learnings for the AI agent.
    """
    
    def __init__(self):
        """Initialize the learning agent with AWS and Gemini clients."""
        # AWS Configuration
        self.s3_bucket = os.environ.get('AWS_S3_BUCKET_LEARNING', 'offer-learning-data')
        self.region = os.environ.get('AWS_REGION', 'eu-north-1')
        
        # Lemonsoft API Configuration
        self.lemonsoft_api_url = os.environ.get('LEMONSOFT_API_URL', '')
        self.lemonsoft_api_key = os.environ.get('LEMONSOFT_API_KEY', '')
        self.lemonsoft_username = os.environ.get('LEMONSOFT_USERNAME', '')
        self.lemonsoft_password = os.environ.get('LEMONSOFT_PASSWORD', '')
        self.lemonsoft_database = os.environ.get('LEMONSOFT_DATABASE', '')
        
        # Gemini Configuration (matching ProductMatcher)
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
        self.gemini_model = os.environ.get('GEMINI_MODEL_ITERATION', 'gemini-2.5-flash')
        
        # Initialize clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.gemini_client = None
        self.lemonsoft_token = None
        self.http_client = None
        
        # Initialize Gemini
        if self.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
    
    async def initialize(self):
        """Async initialization for HTTP clients and authentication."""
        self.http_client = httpx.AsyncClient(timeout=30.0)
        await self._authenticate_lemonsoft()
    
    async def _authenticate_lemonsoft(self):
        """Authenticate with Lemonsoft API to get access token."""
        try:
            auth_payload = {
                'username': self.lemonsoft_username,
                'password': self.lemonsoft_password,
                'database': self.lemonsoft_database,
                'api_key': self.lemonsoft_api_key
            }
            
            response = await self.http_client.post(
                f"{self.lemonsoft_api_url}/api/authenticate",
                json=auth_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                self.lemonsoft_token = result.get('token') or result.get('access_token')
                logger.info("Successfully authenticated with Lemonsoft API")
            else:
                logger.error(f"Lemonsoft authentication failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to authenticate with Lemonsoft: {e}")
    
    async def fetch_offer_from_lemonsoft(self, offer_number: str) -> Optional[Dict]:
        """
        Fetch current offer state from Lemonsoft API.
        
        Args:
            offer_number: The offer number to fetch
            
        Returns:
            Dict with offer data including rows, or None if error
        """
        if not self.lemonsoft_token:
            logger.error("No Lemonsoft token available")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.lemonsoft_token}',
                'Content-Type': 'application/json'
            }
            
            response = await self.http_client.get(
                f"{self.lemonsoft_api_url}/api/offers/{offer_number}",
                headers=headers
            )
            
            if response.status_code == 200:
                offer_data = response.json()
                logger.info(f"Fetched offer {offer_number} from Lemonsoft")
                return offer_data
            else:
                logger.warning(f"Failed to fetch offer {offer_number}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching offer {offer_number}: {e}")
            return None
    
    def calculate_offer_hash(self, offer_rows: List[Dict]) -> str:
        """
        Calculate MD5 hash of offer rows to detect changes.
        
        Args:
            offer_rows: List of offer row dictionaries
            
        Returns:
            MD5 hash string
        """
        # Sort rows by position to ensure consistent hashing
        sorted_rows = sorted(offer_rows, key=lambda x: x.get('position', 0))
        
        # Create a string representation of key fields
        hash_input = ""
        for row in sorted_rows:
            product_code = row.get('product_code', '')
            quantity = row.get('quantity', 0)
            discount = row.get('discount', 0)
            hash_input += f"{product_code}|{quantity}|{discount};"
        
        # Calculate MD5 hash
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def get_processing_state(self, offer_number: str) -> Optional[Dict]:
        """
        Get the last processing state for an offer.
        
        Args:
            offer_number: The offer number
            
        Returns:
            Dict with state data or None if not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=f"learning-state/{offer_number}.json"
            )
            
            state_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Retrieved processing state for offer {offer_number}")
            return state_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info(f"No previous processing state for offer {offer_number}")
                return None
            else:
                logger.error(f"Error retrieving processing state: {e}")
                return None
    
    def save_processing_state(self, offer_number: str, offer_hash: str):
        """
        Save the processing state for an offer.
        
        Args:
            offer_number: The offer number
            offer_hash: The hash of the current offer state
        """
        try:
            state_data = {
                'offer_number': offer_number,
                'last_processed_hash': offer_hash,
                'last_check_timestamp': datetime.utcnow().isoformat()
            }
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=f"learning-state/{offer_number}.json",
                Body=json.dumps(state_data).encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"Saved processing state for offer {offer_number}")
            
        except Exception as e:
            logger.error(f"Failed to save processing state for {offer_number}: {e}")
    
    def get_offer_context(self, offer_number: str) -> Optional[Dict]:
        """
        Retrieve original AI offer context from S3.
        
        Args:
            offer_number: The offer number
            
        Returns:
            Dict with original context or None if not found
        """
        try:
            # List objects with this offer number prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=f"offer-requests/{offer_number}_"
            )
            
            if 'Contents' not in response or not response['Contents']:
                logger.warning(f"No offer context found for {offer_number}")
                return None
            
            # Get the most recent file
            latest_key = response['Contents'][-1]['Key']
            
            # Download the file
            obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=latest_key)
            context_data = json.loads(obj['Body'].read().decode('utf-8'))
            
            logger.info(f"Retrieved offer context for {offer_number}")
            return context_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve offer context for {offer_number}: {e}")
            return None
    
    def compare_offers(
        self,
        original_context: Dict,
        current_offer: Dict
    ) -> OfferComparisonResult:
        """
        Compare original AI-generated offer with current user-edited version.
        
        Args:
            original_context: Original offer context from S3
            current_offer: Current offer state from Lemonsoft API
            
        Returns:
            OfferComparisonResult with detected changes
        """
        result = OfferComparisonResult()
        
        # Get original AI products
        original_products = {
            p['product_code']: p 
            for p in original_context.get('ai_matched_products', [])
        }
        
        # Get current offer rows
        current_rows = current_offer.get('offer_rows', [])
        current_products = {
            row['product_code']: row 
            for row in current_rows
        }
        
        # Find added products (in current but not in original)
        for product_code, row in current_products.items():
            if product_code not in original_products:
                result.added_rows.append({
                    'product_code': product_code,
                    'product_name': row.get('product_name', ''),
                    'quantity': row.get('quantity', 0),
                    'position': row.get('position', 0)
                })
                result.has_changes = True
        
        # Find deleted products (in original but not in current)
        for product_code, product in original_products.items():
            if product_code not in current_products:
                result.deleted_rows.append({
                    'product_code': product_code,
                    'product_name': product.get('product_name', ''),
                    'quantity': product.get('quantity', 0),
                    'customer_term': self._get_customer_term(product, original_context)
                })
                result.has_changes = True
        
        # Find modified products (same position but different product code)
        # This requires matching by position in the offer
        original_by_pos = {}
        for i, product in enumerate(original_context.get('ai_matched_products', [])):
            original_by_pos[i] = product
        
        current_by_pos = {}
        for row in sorted(current_rows, key=lambda x: x.get('position', 0)):
            pos = row.get('position', 0)
            current_by_pos[pos] = row
        
        # Compare by position to detect product swaps
        for pos, original_product in original_by_pos.items():
            if pos in current_by_pos:
                current_row = current_by_pos[pos]
                original_code = original_product.get('product_code')
                current_code = current_row.get('product_code')
                
                if original_code != current_code:
                    result.modified_rows.append({
                        'position': pos,
                        'original_code': original_code,
                        'original_name': original_product.get('product_name', ''),
                        'current_code': current_code,
                        'current_name': current_row.get('product_name', ''),
                        'customer_term': self._get_customer_term(original_product, original_context),
                        'quantity': current_row.get('quantity', 0)
                    })
                    result.has_changes = True
                
                # Check for quantity changes
                original_qty = float(original_product.get('quantity', 0))
                current_qty = float(current_row.get('quantity', 0))
                
                if abs(original_qty - current_qty) > 0.01:  # Allow small floating point differences
                    result.quantity_changes.append({
                        'product_code': current_code,
                        'product_name': current_row.get('product_name', ''),
                        'original_quantity': original_qty,
                        'current_quantity': current_qty
                    })
                    result.has_changes = True
        
        return result
    
    def _get_customer_term(self, product: Dict, context: Dict) -> str:
        """
        Extract the original customer term from product match details or email.
        
        Args:
            product: Product dictionary
            context: Original offer context
            
        Returns:
            Customer's original term for this product
        """
        # Try to get from match_details
        match_details = product.get('match_details', {})
        if isinstance(match_details, dict):
            customer_term = match_details.get('original_customer_term')
            if customer_term:
                return customer_term
            
            customer_term = match_details.get('unclear_term')
            if customer_term:
                return customer_term
        
        # Fallback to product name
        return product.get('product_name', 'Unknown')
    
    def analyze_changes_with_gemini(
        self,
        comparison: OfferComparisonResult,
        original_context: Dict
    ) -> List[Dict]:
        """
        Use Gemini AI to analyze changes and extract learnings.
        
        Args:
            comparison: OfferComparisonResult with detected changes
            original_context: Original offer context
            
        Returns:
            List of learning dictionaries
        """
        if not self.gemini_client:
            logger.error("Gemini client not initialized")
            return []
        
        learnings = []
        
        # Analyze product swaps (modified rows)
        for change in comparison.modified_rows:
            try:
                learning = self._analyze_product_swap(change, original_context)
                if learning:
                    learnings.append(learning)
            except Exception as e:
                logger.error(f"Error analyzing product swap: {e}")
        
        # Analyze deleted/added pairs (might indicate replacements)
        if comparison.deleted_rows and comparison.added_rows:
            try:
                learning = self._analyze_product_replacement(
                    comparison.deleted_rows,
                    comparison.added_rows,
                    original_context
                )
                if learning:
                    learnings.extend(learning)
            except Exception as e:
                logger.error(f"Error analyzing product replacement: {e}")
        
        return learnings
    
    def _analyze_product_swap(
        self,
        change: Dict,
        original_context: Dict
    ) -> Optional[Dict]:
        """
        Analyze a single product swap using Gemini AI.
        
        Args:
            change: Dictionary with swap details
            original_context: Original offer context
            
        Returns:
            Learning dictionary or None
        """
        # Build prompt for Gemini
        prompt = f"""Analyze this product swap in an HVAC/plumbing offer to determine if it represents a learning opportunity.

ORIGINAL AI SELECTION:
- Customer requested: "{change['customer_term']}"
- AI selected: {change['original_code']} - {change['original_name']}

USER CORRECTION:
- User changed to: {change['current_code']} - {change['current_name']}

CONTEXT:
- Customer email: {original_context.get('email', {}).get('body', '')[:500]}
- Offer for: {original_context.get('customer', {}).get('name', 'Unknown')}

ANALYSIS TASK:
Determine if this change represents:
1. A product_swap: User prefers a specific brand/variant for this product type
2. A general_rule: A broader principle about product selection
3. Not a learning: Just a one-off correction or unclear situation

RESPONSE FORMAT (JSON):
{{
  "is_learning": true/false,
  "learning_type": "product_swap" or "general_rule",
  "confidence": 0.0-1.0,
  "reasoning": "Why this is or isn't a learning opportunity",
  "customer_term": "The term customer used",
  "preferred_product_code": "The product code to use in future",
  "preferred_product_name": "The product name",
  "rule_text": "For general_rule type: the rule to remember"
}}

Only return JSON, no other text."""
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
            
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config
            )
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else None
            if not response_text and hasattr(response, 'candidates'):
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            part = candidate.content.parts[0]
                            if hasattr(part, 'text'):
                                response_text = part.text
                except Exception as e:
                    logger.warning(f"Error extracting text from candidates: {e}")
            
            if not response_text:
                logger.warning("No response from Gemini for product swap analysis")
                return None
            
            # Parse JSON response
            result = json.loads(response_text.strip())
            
            if result.get('is_learning', False):
                logger.info(f"Learning identified: {result.get('learning_type')} - {result.get('reasoning')}")
                return {
                    'type': result.get('learning_type'),
                    'confidence': result.get('confidence', 0.8),
                    'reasoning': result.get('reasoning', ''),
                    'customer_term': result.get('customer_term', change['customer_term']),
                    'product_code': result.get('preferred_product_code', change['current_code']),
                    'product_name': result.get('preferred_product_name', change['current_name']),
                    'rule_text': result.get('rule_text', ''),
                    'source_offer': original_context.get('offer_number', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini analysis failed for product swap: {e}")
            return None
    
    def _analyze_product_replacement(
        self,
        deleted_rows: List[Dict],
        added_rows: List[Dict],
        original_context: Dict
    ) -> List[Dict]:
        """
        Analyze deleted and added rows to find potential product replacements.
        
        Returns:
            List of learning dictionaries
        """
        learnings = []
        
        # For now, just create a general observation if significant changes
        if len(deleted_rows) > 0 or len(added_rows) > 0:
            try:
                # Build a summary of changes
                summary_prompt = f"""Analyze these product changes in an HVAC/plumbing offer:

PRODUCTS REMOVED BY USER:
{json.dumps(deleted_rows, indent=2)}

PRODUCTS ADDED BY USER:
{json.dumps(added_rows, indent=2)}

CONTEXT:
- Original offer for: {original_context.get('customer', {}).get('name', 'Unknown')}

Can you identify any general rules or patterns from these changes?

RESPONSE FORMAT (JSON):
{{
  "has_pattern": true/false,
  "rule_text": "The general rule if a pattern is found",
  "confidence": 0.0-1.0,
  "reasoning": "Why this pattern exists"
}}"""
                
                config = types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
                
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=summary_prompt,
                    config=config
                )
                
                response_text = response.text if hasattr(response, 'text') else None
                if response_text:
                    result = json.loads(response_text.strip())
                    
                    if result.get('has_pattern', False):
                        learnings.append({
                            'type': 'general_rule',
                            'confidence': result.get('confidence', 0.7),
                            'reasoning': result.get('reasoning', ''),
                            'rule_text': result.get('rule_text', ''),
                            'source_offer': original_context.get('offer_number', '')
                        })
                
            except Exception as e:
                logger.error(f"Error analyzing product replacement pattern: {e}")
        
        return learnings
    
    def save_learnings(self, learnings: List[Dict]):
        """
        Save learnings to S3 (CSV for product swaps, text for rules).
        
        Args:
            learnings: List of learning dictionaries
        """
        for learning in learnings:
            try:
                if learning['type'] == 'product_swap':
                    self._append_to_product_swaps_csv(learning)
                elif learning['type'] == 'general_rule':
                    self._append_to_general_rules_txt(learning)
            except Exception as e:
                logger.error(f"Failed to save learning: {e}")
    
    def _append_to_product_swaps_csv(self, learning: Dict):
        """
        Append a product swap learning to the CSV file in S3.
        
        Args:
            learning: Learning dictionary with product swap details
        """
        # Download existing CSV if it exists
        csv_key = "learnings/product_swaps.csv"
        existing_content = ""
        
        try:
            obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=csv_key)
            existing_content = obj['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # File doesn't exist, create with header
                existing_content = "customer_term,matched_product_code,matched_product_name,confidence_score,reasoning,match_type,timestamp,source_files\n"
            else:
                logger.error(f"Error reading product_swaps.csv: {e}")
                return
        
        # Create new row
        timestamp = datetime.utcnow().isoformat()
        new_row = f'"{learning["customer_term"]}","{learning["product_code"]}","{learning["product_name"]}",{learning["confidence"]},"{learning["reasoning"]}","learned_from_correction","{timestamp}","{learning["source_offer"]}"\n'
        
        # Append and upload
        updated_content = existing_content + new_row
        
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=csv_key,
            Body=updated_content.encode('utf-8'),
            ContentType='text/csv'
        )
        
        logger.info(f"Appended product swap learning to CSV: {learning['customer_term']} -> {learning['product_code']}")
    
    def _append_to_general_rules_txt(self, learning: Dict):
        """
        Append a general rule to the text file in S3.
        
        Args:
            learning: Learning dictionary with rule text
        """
        # Download existing file if it exists
        txt_key = "learnings/general_rules.txt"
        existing_content = ""
        
        try:
            obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=txt_key)
            existing_content = obj['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                logger.error(f"Error reading general_rules.txt: {e}")
                return
        
        # Create new line
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        new_line = f"{date_str}: {learning['rule_text']}\n"
        
        # Append and upload
        updated_content = existing_content + new_line
        
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=txt_key,
            Body=updated_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        logger.info(f"Appended general rule: {learning['rule_text']}")
    
    async def process_offer(self, offer_number: str) -> Dict[str, Any]:
        """
        Process a single offer: compare, analyze, and extract learnings.
        
        Args:
            offer_number: The offer number to process
            
        Returns:
            Dict with processing results
        """
        logger.info(f"Processing offer: {offer_number}")
        
        # Fetch current offer from Lemonsoft
        current_offer = await self.fetch_offer_from_lemonsoft(offer_number)
        if not current_offer:
            return {
                'success': False,
                'error': 'Could not fetch offer from Lemonsoft',
                'offer_number': offer_number
            }
        
        # Calculate current offer hash
        current_rows = current_offer.get('offer_rows', [])
        current_hash = self.calculate_offer_hash(current_rows)
        
        # Check processing state
        state = self.get_processing_state(offer_number)
        if state and state.get('last_processed_hash') == current_hash:
            logger.info(f"Offer {offer_number} unchanged since last check, skipping")
            return {
                'success': True,
                'skipped': True,
                'reason': 'No changes detected',
                'offer_number': offer_number
            }
        
        # Get original AI context
        original_context = self.get_offer_context(offer_number)
        if not original_context:
            logger.warning(f"No original context found for offer {offer_number}")
            return {
                'success': False,
                'error': 'No original context found',
                'offer_number': offer_number
            }
        
        # Compare offers
        comparison = self.compare_offers(original_context, current_offer)
        
        if not comparison.has_changes:
            logger.info(f"No meaningful changes detected in offer {offer_number}")
            # Update state anyway to avoid reprocessing
            self.save_processing_state(offer_number, current_hash)
            return {
                'success': True,
                'changes_detected': False,
                'offer_number': offer_number
            }
        
        logger.info(
            f"Changes detected in offer {offer_number}: "
            f"{len(comparison.modified_rows)} swaps, "
            f"{len(comparison.added_rows)} additions, "
            f"{len(comparison.deleted_rows)} deletions"
        )
        
        # Analyze changes with Gemini
        learnings = self.analyze_changes_with_gemini(comparison, original_context)
        
        # Save learnings
        if learnings:
            self.save_learnings(learnings)
            logger.info(f"Saved {len(learnings)} learnings from offer {offer_number}")
        
        # Update processing state
        self.save_processing_state(offer_number, current_hash)
        
        return {
            'success': True,
            'changes_detected': True,
            'learnings_count': len(learnings),
            'offer_number': offer_number,
            'comparison': {
                'modified_rows': len(comparison.modified_rows),
                'added_rows': len(comparison.added_rows),
                'deleted_rows': len(comparison.deleted_rows)
            }
        }
    
    async def run(self) -> Dict[str, Any]:
        """
        Main entry point: Process all offers from the past 3 days.
        
        Returns:
            Dict with overall results
        """
        logger.info("Starting nightly learning agent run")
        
        await self.initialize()
        
        # List offers from past 3 days
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='offer-requests/'
            )
            
            if 'Contents' not in response:
                logger.info("No offer requests found")
                return {
                    'success': True,
                    'offers_processed': 0,
                    'message': 'No offers found'
                }
            
            # Extract unique offer numbers from recent files
            offer_numbers = set()
            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) >= cutoff_date:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    offer_number = filename.split('_')[0]
                    offer_numbers.add(offer_number)
            
            offer_list = sorted(list(offer_numbers))
            logger.info(f"Found {len(offer_list)} offers to process from past 3 days")
            
            # Process each offer
            results = []
            for offer_number in offer_list:
                try:
                    result = await self.process_offer(offer_number)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing offer {offer_number}: {e}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'offer_number': offer_number
                    })
            
            # Summarize results
            successful = sum(1 for r in results if r.get('success'))
            skipped = sum(1 for r in results if r.get('skipped'))
            with_learnings = sum(1 for r in results if r.get('learnings_count', 0) > 0)
            total_learnings = sum(r.get('learnings_count', 0) for r in results)
            
            summary = {
                'success': True,
                'offers_processed': len(results),
                'successful': successful,
                'skipped': skipped,
                'with_learnings': with_learnings,
                'total_learnings': total_learnings,
                'results': results
            }
            
            logger.info(
                f"Learning agent run complete: {len(results)} offers processed, "
                f"{total_learnings} learnings extracted"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in learning agent run: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if self.http_client:
                await self.http_client.aclose()


# Lambda handler function
def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context
        
    Returns:
        Response dict
    """
    agent = LearningAgent()
    
    # Run the async process
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(agent.run())
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


# For local testing
if __name__ == "__main__":
    async def test_run():
        agent = LearningAgent()
        result = await agent.run()
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_run())

