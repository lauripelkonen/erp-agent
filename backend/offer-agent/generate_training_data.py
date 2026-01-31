"""
Training Data Generator for Product Matching

This script analyzes past customer requests and sales team offers to extract
product matching patterns, generating training examples for improving the
matching agent's performance.

Usage:
    python generate_training_data.py
    
The script will automatically use customer_example1.txt and offer_example1.txt 
from the examples/ directory and append results to training_dataset.csv
"""

import json
import logging
import os
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import uuid
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.product_matching.config import Config
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates training data from customer requests and sales offers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in configuration")
        
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.logger.info(f"Gemini client initialized with model: {Config.GEMINI_MODEL}")

    
    def analyze_matches_with_gemini(self, customer_text: str, offer_text: str) -> Dict:
        """Use Gemini to analyze which customer terms match which sales products."""
        self.logger.info("Analyzing matches using Gemini AI...")
        
        # Simple system prompt that just asks for matches
        system_prompt = f"""You are an expert in Finnish HVAC/plumbing product matching. 

Read the customer request and sales offer below, then identify which customer product terms correspond to which offered products.

IMPORTANT: When extracting customer terms, include the FULL CONTEXTUAL DESCRIPTION. For example:
- If customer says "Sinkitty M-press" followed by "22-¾ SK 4kpl", the customer_term should be "Sinkitty M-press 22-¾ SK"  
- If customer says "Kupari m-press osat" followed by "15 haara 1kpl", the customer_term should be "Kupari m-press haara 15"
- Always include the category/type context that applies to specific items

For each match you find, provide:
1. The customer's FULL contextual term/description (including category context)
2. The matched product from the offer (code and name)  
3. Confidence score (0.0-1.0)
4. Brief reasoning for the match
5. Match type (exact, equivalent, substitute, approximate)


NOTE: All requested products might not be included in the offer - offer can be only subset of requested products.

Respond in JSON format:
{{
  "matches": [
    {{
      "customer_term": "FULL contextual customer term from request",
      "matched_product": {{
        "code": "PRODUCT_CODE",
        "name": "Product Name from offer",
        "confidence": 0.95,
        "reasoning": "brief explanation",
        "match_type": "exact|equivalent|substitute|approximate"
      }}
    }}
  ],
  "unmatched_customer_terms": ["customer terms with no match (with full context)"],
  "unmatched_products": ["offer products that match no customer term"]
}}

CUSTOMER REQUEST:
{customer_text}

SALES OFFER:
{offer_text}"""

        try:
            # Configure Gemini for JSON response
            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1
            )
            
            # Generate analysis
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL_THINKING,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=system_prompt)]
                    )
                ],
                config=config
            )
            
            if not response or not response.candidates:
                raise ValueError("Empty response from Gemini")
            
            # Extract and parse JSON response
            response_text = response.candidates[0].content.parts[0].text
            
            # Clean up response (remove markdown formatting if present)
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {e}")
                self.logger.error(f"Raw response: {response_text[:500]}...")
                # Fallback: create basic structure
                analysis_result = {
                    "matches": [],
                    "unmatched_customer_terms": [],
                    "unmatched_products": [],
                    "analysis_notes": "Analysis failed - JSON parsing error"
                }
            
            self.logger.info(f"Gemini analysis complete: {len(analysis_result.get('matches', []))} matches found")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            # Return fallback structure
            return {
                "matches": [],
                "unmatched_customer_terms": [],
                "unmatched_products": [],
                "analysis_notes": f"Analysis failed: {str(e)}"
            }
    
    def generate_training_example(self, customer_request_file: str, sales_offer_file: str) -> List[Dict]:
        """Generate training examples from customer request and sales offer files."""
        self.logger.info(f"Generating training examples from: {customer_request_file} + {sales_offer_file}")
        
        # Read input files
        try:
            with open(customer_request_file, 'r', encoding='utf-8') as f:
                customer_text = f.read()
            with open(sales_offer_file, 'r', encoding='utf-8') as f:
                offer_text = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read input files: {e}")
            raise
        
        # Analyze matches with Gemini
        analysis = self.analyze_matches_with_gemini(customer_text, offer_text)
        
        # Build training rows for CSV
        matches = analysis.get("matches", [])
        training_rows = []
        
        for match in matches:
            customer_term = match.get("customer_term", "")
            matched_product = match.get("matched_product", {})
            
            training_row = {
                "customer_term": customer_term,
                "matched_product_code": matched_product.get("code", ""),
                "matched_product_name": matched_product.get("name", ""),
                "confidence_score": matched_product.get("confidence", 0.0),
                "reasoning": matched_product.get("reasoning", ""),
                "match_type": matched_product.get("match_type", ""),
                "timestamp": datetime.now().isoformat(),
                "source_files": f"{Path(customer_request_file).name} + {Path(sales_offer_file).name}"
            }
            training_rows.append(training_row)
        
        self.logger.info(f"Generated {len(training_rows)} training rows from matches")
        return training_rows
    
    def save_to_csv(self, training_rows: List[Dict], csv_file: str = "training_dataset.csv"):
        """Save training rows to CSV file, appending if file exists."""
        csv_path = Path(csv_file)
        file_exists = csv_path.exists()
        
        # Define CSV columns in the order requested
        fieldnames = [
            "customer_term",
            "matched_product_code",
            "matched_product_name",
            "confidence_score",
            "reasoning",
            "match_type",
            "timestamp",
            "source_files"
        ]
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
                self.logger.info(f"Created new CSV file: {csv_file}")
            
            # Write the rows
            writer.writerows(training_rows)
            
        self.logger.info(f"Appended {len(training_rows)} rows to {csv_file}")
    


def main():
    """Main function - automatically processes example files and appends to CSV."""
    try:
        # Set up paths
        examples_dir = Path(__file__).parent / "examples"
        customer_file = examples_dir / "customer_example1.txt"
        offer_file = examples_dir / "offer_example1.txt"
        csv_file = "training_dataset.csv"
        
        # Check if input files exist
        if not customer_file.exists():
            logger.error(f"Customer file not found: {customer_file}")
            logger.info("Please ensure customer_example1.txt exists in the examples/ directory")
            sys.exit(1)
            
        if not offer_file.exists():
            logger.error(f"Offer file not found: {offer_file}")
            logger.info("Please ensure offer_example1.txt exists in the examples/ directory")
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("TRAINING DATA GENERATOR")
        logger.info("=" * 60)
        logger.info(f"Customer file: {customer_file}")
        logger.info(f"Offer file: {offer_file}")
        logger.info(f"Output CSV: {csv_file}")
        logger.info("=" * 60)
        
        # Initialize generator
        generator = TrainingDataGenerator()
        
        # Generate training rows
        training_rows = generator.generate_training_example(str(customer_file), str(offer_file))
        
        if training_rows:
            # Save to CSV
            generator.save_to_csv(training_rows, csv_file)
            
            # Print summary
            logger.info("=" * 60)
            logger.info("GENERATION COMPLETE")
            logger.info(f"Added {len(training_rows)} new rows to {csv_file}")
            logger.info("Sample rows:")
            for i, row in enumerate(training_rows[:3], 1):
                logger.info(f"  {i}. {row['customer_term'][:50]}... -> {row['matched_product_code']}")
            
            # Show CSV stats
            csv_path = Path(csv_file)
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    total_rows = sum(1 for _ in reader)
                logger.info(f"Total rows in CSV: {total_rows}")
        else:
            logger.warning("No matches found - no rows added to CSV")
            
        logger.info("=" * 60)
        logger.info("To add more training data:")
        logger.info("1. Update examples/customer_example1.txt with new customer requests")
        logger.info("2. Update examples/offer_example1.txt with corresponding offers")
        logger.info("3. Run: python generate_training_data.py")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()