"""
Enhanced Customer Lookup for Lemonsoft API
Implements multiple search strategies for finding customers based on company names.
"""

import asyncio
import json
import logging
import httpx
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.utils.exceptions import BaseOfferAutomationError

load_dotenv()

class EnhancedCustomerLookup:
    """Enhanced customer lookup with multiple search strategies and fallbacks."""
    
    def __init__(self):
        """Initialize the enhanced customer lookup."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.lemonsoft_client = LemonsoftAPIClient()
        
        # Initialize Gemini client if available
        if GENAI_AVAILABLE and self.settings.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.settings.gemini_api_key)
            self.gemini_model = "gemini-2.5-flash"
        else:
            self.gemini_client = None
            self.gemini_model = None
            self.logger.warning("Gemini API not available - LLM features will be disabled")
        
        # Known Y-tunnus for common companies (in production, use web search)
        self.known_companies = {
            'lvi-nordic': {'ytunnus': '1740598-7', 'official_name': 'LVI-Nordic Oy'}
        }
    
    async def find_customer(self, company_name: str, customer_number: str = None) -> Dict[str, Any]:
        """
        Find customer using multiple search strategies.
        
        Args:
            company_name: Company name to search for
            customer_number: Optional customer number to search for directly
            
        Returns:
            Dict with success flag and customer data
        """
        import sys
        
        # Check if customer_number is valid (not None, empty string, or "null")
        if customer_number and customer_number.strip() and customer_number.lower() != 'null':
            self.logger.info(f"🔍 Searching by customer number: {customer_number}")
            sys.stdout.flush()
            try:
                async with self.lemonsoft_client as client:
                    # Make API request to get customer by customer number using filter
                    response = await client.get('/api/customers', params={'filter.customer_number': customer_number})
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract customer data from response - handle list format
                        customers = []
                        if isinstance(data, list):
                            customers = data
                        elif isinstance(data, dict):
                            customers = data.get('results', data.get('data', data.get('customers', [])))
                        
                        if customers and len(customers) > 0:
                            # Take the first customer from results
                            customer_data = customers[0]
                            api_customer_name = customer_data.get('name', '')
                            
                            if api_customer_name:
                                # Use Gemini LLM to verify if the names match
                                if company_name.lower() == 'null':
                                    name_matches = True
                                else:
                                    name_matches = True
                                    #name_matches = await self._verify_company_name_match(api_customer_name, company_name) # for now disabled, dont know if it adds value
                                
                                if name_matches:
                                    # Names match - create enhanced customer data using API response
                                    enhanced_customer = {
                                        'id': customer_data.get('id'),
                                        'number': customer_data.get('number'),
                                        'name': api_customer_name,  # Use official name from API
                                        'street': customer_data.get('street', ''),
                                        'city': customer_data.get('city', ''),
                                        'postal_code': customer_data.get('postal_code', ''),
                                        'person_responsible_number': customer_data.get('person_responsible_number', ''),
                                        'vat_number': customer_data.get('vat', ''),
                                        'phone': customer_data.get('phone', ''),
                                        'email': customer_data.get('email', ''),
                                        'deny_credit': customer_data.get('deny_credit', False),
                                    }
                                    
                                    # Extract CEO contact from contacts list
                                    ceo_contact = self._extract_ceo_contact(customer_data)
                                    enhanced_customer['ceo_contact'] = ceo_contact
                                    
                                    # Copy additional fields
                                    for key in ['contacts', 'attributes', 'currency_code']:
                                        if key in customer_data:
                                            enhanced_customer[key] = customer_data[key]
                                    
                                    self.logger.info(f"Customer number {customer_number} matches company name '{company_name}' - using official name: '{api_customer_name}'")
                                    
                                    return {
                                        'success': True,
                                        'customer_data': enhanced_customer,
                                        'search_results_count': 1
                                    }
                                else:
                                    self.logger.warning(f"Customer number {customer_number} found but name '{api_customer_name}' doesn't match '{company_name}'")
                                    return {
                                        'success': False,
                                        'error': f"Customer {customer_number} found but name '{api_customer_name}' doesn't match provided company name '{company_name}'",
                                        'customer_data': None
                                    }
                            else:
                                self.logger.warning(f"Customer {customer_number} found but has no name")
                                return {
                                    'success': False,
                                    'error': f"Customer {customer_number} found but has no name to verify",
                                    'customer_data': None
                                }
                        else:
                            self.logger.warning(f"No customer found with number {customer_number}")
                            return {
                                'success': False,
                                'error': f"No customer found with number {customer_number}",
                                'customer_data': None
                            }
                    else:
                        self.logger.warning(f"Customer {customer_number} not found - API returned {response.status_code}")
                        return {
                            'success': False,
                            'error': f"Customer {customer_number} not found",
                            'customer_data': None
                        }
                        
            except Exception as e:
                self.logger.error(f"Error looking up customer by number {customer_number}: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f"Error looking up customer {customer_number}: {str(e)}",
                    'customer_data': None
                }
        
        if not company_name or not company_name.strip() or company_name.lower() == 'null':
            return {
                'success': False,
                'error': 'No company name provided',
                'customer_data': None
            }
        
        company_name = company_name.strip()
        self.logger.info(f"🚀 Starting enhanced customer search for: '{company_name}'")
        sys.stdout.flush()
        
        customers = []
        try:
            async with self.lemonsoft_client as client:
                # Strategy 1: Enhanced primary search
                self.logger.info("📋 Strategy 1: Enhanced primary search")
                sys.stdout.flush()
                customers = await self._enhanced_customer_search(client, company_name)
                
                if not customers:
                    # Strategy 2: Fallback search methods
                    self.logger.info("📋 Strategy 2: Primary search failed, trying fallback methods")
                    sys.stdout.flush()
                    customers = await self._fallback_customer_search(client, company_name)
                
                if not customers:
                    # Strategy 3: Y-tunnus web search fallback
                    self.logger.info("📋 Strategy 3: Fallback search failed, trying Y-tunnus search")
                    sys.stdout.flush()
                    customers = await self._get_customer_with_ytunnus_fallback(client, company_name)
                
                if customers:
                    # Return the best match with enhanced details
                    best_customer = customers[0]
                    
                    self.logger.info(f"✅ Found {len(customers)} customer matches, using best match: {best_customer.get('name', 'Unknown')}")
                    sys.stdout.flush()
                    
                    # Fetch enhanced customer details including contacts
                    enhanced_customer = await self._fetch_enhanced_customer_details(client, best_customer)
                    
                    self.logger.info(f"✅  Final customer selected: {enhanced_customer.get('name')} (ID: {enhanced_customer.get('id')})")
                    sys.stdout.flush()
                    
                    return {
                        'success': True,
                        'customer_data': enhanced_customer,
                        'search_results_count': len(customers)
                    }
                else:
                    self.logger.warning(f"❌ No customers found for: '{company_name}' after trying all 3 strategies")
                    sys.stdout.flush()
                    return {
                        'success': False,
                        'error': f"No customer found for company: {company_name}",
                        'customer_data': None
                    }
                    
        except Exception as e:
            self.logger.error(f"Error during customer lookup: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Customer lookup failed: {str(e)}",
                'customer_data': None
            }
    
    async def _enhanced_customer_search(self, client, search_term: str, limit: int = 50) -> List[Dict]:
        """Enhanced customer search using proven working methods."""
        self.logger.info(f"Enhanced search for: '{search_term}'")
        
        # Use the proven working search methods
        search_methods = [
            {'name': 'Basic search', 'params': {'search': search_term, 'limit': limit}},
            {'name': 'Name search', 'params': {'name': search_term, 'limit': limit}},
            {'name': 'Uppercase search', 'params': {'search': search_term.upper(), 'limit': limit}},
            {'name': 'Lowercase search', 'params': {'search': search_term.lower(), 'limit': limit}},
            {'name': 'Partial search', 'params': {'search': search_term.split('-')[0], 'limit': limit}}
        ]
        
        all_customers = []
        seen_ids = set()
        
        for i, method in enumerate(search_methods, 1):
            try:
                self.logger.info(f"Method {i} ({method['name']}): Params={method['params']}")
                response = await client.get('/api/customers', params=method['params'])
                
                self.logger.info(f"API Response: status={response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"Response data type: {type(data)}")
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        customers = data
                    elif isinstance(data, dict):
                        customers = data.get('results', data.get('data', data.get('customers', [])))
                        self.logger.info(f"Dict keys: {list(data.keys()) if data else 'None'}")
                    else:
                        customers = []
                    
                    self.logger.info(f"Found {len(customers) if customers else 0} customers")
                    
                    if customers:
                        # Log first few customer names for debugging
                        for j, customer in enumerate(customers[:3]):
                            self.logger.info(f"  Customer {j+1}: {customer.get('name', 'Unknown')} (ID: {customer.get('id', 'Unknown')})")
                        
                        # Add unique customers only
                        for customer in customers:
                            customer_id = customer.get('id')
                            if customer_id and customer_id not in seen_ids:
                                all_customers.append(customer)
                                seen_ids.add(customer_id)
                else:
                    self.logger.warning(f"API call failed with status {response.status_code}")
                    try:
                        error_data = response.json()
                        self.logger.warning(f"Error response: {error_data}")
                    except:
                        self.logger.warning(f"Error response text: {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Error in search method {method['name']}: {e}", exc_info=True)
                continue
        
        # Rank customers by relevance
        ranked_customers = self._LLM_decision(all_customers, search_term)
        
        self.logger.info(f"Total unique customers found: {len(ranked_customers)}")
        return ranked_customers
    
    def _LLM_decision(self, customers: List[Dict], search_term: str) -> List[Dict]:
        """
        Use Gemini LLM to decide which companies match the search term and rank them.
        
        Args:
            customers: List of customer dictionaries from Lemonsoft
            search_term: Original company name being searched for
            
        Returns:
            List of customers ranked by relevance, with best matches first
        """
        if not customers:
            return []
        
        if not self.gemini_client:
            self.logger.warning("Gemini not available, returning customers without LLM ranking")
            return customers
        
        try:
            # Prepare customer data for LLM analysis
            customer_summaries = []
            for i, customer in enumerate(customers):
                name = customer.get('name', 'Unknown')
                address = customer.get('address', '')
                city = customer.get('city', '')
                postal_code = customer.get('postalCode', '')
                vat_number = customer.get('vatNumber', '')
                
                summary = {
                    'index': i,
                    'name': name,
                    'address': address,
                    'city': city,
                    'postal_code': postal_code,
                    'vat_number': vat_number
                }
                customer_summaries.append(summary)
            
            prompt = f"""You are an expert at matching company names in Finnish business contexts.

TASK: Analyze these customer records and determine which ones match the search term "{search_term}".

CUSTOMER RECORDS:
{json.dumps(customer_summaries, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Compare each customer name with the search term "{search_term}"
2. Consider common Finnish business name variations (Oy, Ab, Ltd, etc.)
3. Look for exact matches, partial matches, and reasonable variations
4. Consider address information as secondary confirmation
5. Return a JSON list of matching customer indices, ranked by relevance (best match first)

RESPONSE FORMAT:
{{
  "matches": [
    {{
      "index": 0,
      "confidence": 0.95,
      "reasoning": "Exact match with search term"
    }},
    {{
      "index": 2,
      "confidence": 0.80,
      "reasoning": "Partial match, same company different suffix"
    }}
  ]
}}

Only include customers with confidence >= 0.6. If no good matches found, return empty matches array.

DO NOT INCLUDE ANY OTHER TEXT THAN THE JSON RESPONSE - EVEN IF IT IS EMPTY.
"""

            self.logger.info(f"🤖 Asking Gemini to rank {len(customers)} customers for '{search_term}'")
            
            config = types.GenerateContentConfig(
                temperature=0.3
            )

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )

            # Extract response text
            response_text = self._extract_gemini_response_text(response)
            if not response_text:
                self.logger.warning("No response from Gemini LLM decision")
                return customers  # Return original list if LLM fails
            
            # Parse JSON response
            try:
                # Clean up response text
                json_text = response_text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                decision_result = json.loads(json_text)
                matches = decision_result.get('matches', [])
                
                if not matches:
                    self.logger.info("Gemini found no confident matches")
                    return []
                
                # Sort matches by confidence and build ranked customer list
                matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                ranked_customers = []
                
                for match in matches:
                    index = match.get('index')
                    confidence = match.get('confidence', 0)
                    reasoning = match.get('reasoning', '')
                    
                    if 0 <= index < len(customers):
                        customer = customers[index].copy()
                        customer['llm_confidence'] = confidence
                        customer['llm_reasoning'] = reasoning
                        ranked_customers.append(customer)
                        
                        self.logger.info(f"✅ LLM Match: {customer.get('name')} "
                                       f"(confidence: {confidence:.2f}) - {reasoning}")
                
                return ranked_customers
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse LLM decision JSON: {e}")
                self.logger.error(f"Raw LLM response: {response_text}")
                return customers  # Return original list if parsing fails
                
        except Exception as e:
            self.logger.error(f"Error in LLM decision making: {e}", exc_info=True)
            return customers  # Return original list if LLM fails

    async def _fallback_customer_search(self, client, search_term: str) -> List[Dict]:
        """
        Generate new regex search parameters with Gemini LLM when primary search fails.
        
        Args:
            client: Lemonsoft API client
            search_term: Original search term that failed
            
        Returns:
            List of customers found using LLM-generated search strategies
        """
        self.logger.info(f"Fallback search methods for: '{search_term}'")
        
        if not self.gemini_client:
            self.logger.warning("Gemini not available for fallback search, using basic alternatives")
            # Basic fallback without LLM
            fallback_terms = [
                search_term.split()[0] if ' ' in search_term else search_term,  # First word only
                search_term.replace('-', ' '),  # Replace hyphens with spaces
                search_term.replace(' ', ''),   # Remove spaces
                search_term.lower(),
                search_term.upper(),
            ]
            
            all_customers = []
            seen_ids = set()
            
            for term in fallback_terms:
                try:
                    response = await client.get('/api/customers', params={'search': term, 'limit': 20})
                    if response.status_code == 200:
                        data = response.json()
                        customers = data if isinstance(data, list) else data.get('results', data.get('data', []))
                        
                        for customer in customers or []:
                            customer_id = customer.get('id')
                            if customer_id and customer_id not in seen_ids:
                                all_customers.append(customer)
                                seen_ids.add(customer_id)
                except Exception as e:
                    self.logger.error(f"Error in basic fallback search with '{term}': {e}")
                    continue
            
            return self._LLM_decision(all_customers, search_term)
        
        try:
            # Ask Gemini to generate alternative search strategies
            prompt = f"""You are an expert at Finnish company name variations and search strategies.

TASK: Generate alternative search terms for finding the company "{search_term}" in Lemonsoft API.

CONTEXT:
- The original search for "{search_term}" returned no results
- Lemonsoft API supports wildcard searches with filter.name=%25term%25 pattern
- The %25 represents URL-encoded % wildcards for partial matching
- Need creative variations that might match database entries
- Consider Finnish business naming conventions (Oy, Ab, Ltd, etc.)

INSTRUCTIONS:
1. Generate 6-10 alternative search terms optimized for filter.name=%25term%25 pattern
2. Include core keywords, abbreviations, and partial matches
3. Consider removing Finnish suffixes (Oy, Ab, Ltd) for broader matching
4. Include both short and longer variations
5. Focus on terms that would work well with wildcard matching
6. Consider word variations, abbreviations, and alternative spellings

RESPONSE FORMAT (JSON only):
{{
  "search_strategies": [
    {{
      "term": "nordic",
      "strategy": "core_keyword", 
      "reasoning": "Core company identifier without suffixes",
      "api_pattern": "filter.name=%25nordic%25"
    }},
    {{
      "term": "lvi-nord",
      "strategy": "partial_abbreviation",
      "reasoning": "Abbreviated version with partial hyphenation", 
      "api_pattern": "filter.name=%25lvi-nord%25"
    }}
  ]
}}

Original term: "{search_term}"
"""

            self.logger.info(f"🤖 Asking Gemini for fallback search strategies for '{search_term}'")
            
            config = types.GenerateContentConfig(
                temperature=0.3,  # Slightly higher for creativity
                candidate_count=1,
            )

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )

            response_text = self._extract_gemini_response_text(response)
            if not response_text:
                self.logger.warning("No response from Gemini for fallback strategies")
                return []
            
            # Parse LLM response
            try:
                json_text = response_text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                strategies_result = json.loads(json_text)
                strategies = strategies_result.get('search_strategies', [])
                
                if not strategies:
                    self.logger.warning("Gemini returned no fallback strategies")
                    return []
                
                self.logger.info(f"🎯 Gemini generated {len(strategies)} fallback search strategies")
                
                # Execute each strategy
                all_customers = []
                seen_ids = set()
                
                for strategy in strategies[:8]:  # Limit to prevent too many API calls
                    term = strategy.get('term', '').strip()
                    strategy_type = strategy.get('strategy', 'unknown')
                    reasoning = strategy.get('reasoning', '')
                    
                    if not term:
                        continue
                    
                    self.logger.info(f"🔍 Trying fallback strategy '{strategy_type}': '{term}' - {reasoning}")
                    
                    try:
                        # Use Lemonsoft API wildcard search pattern with URL encoding
                        # %25 represents URL-encoded % for wildcard matching
                        search_params_list = [
                            {'filter.name': f'%25{term}%25', 'filter.page_size': 20},
                            {'filter.name': f'%25{term.upper()}%25', 'filter.page_size': 20},
                            {'filter.name': f'%25{term.lower()}%25', 'filter.page_size': 20},
                            {'search': term, 'limit': 20},  # Fallback to basic search
                            {'name': term, 'limit': 20},   # Alternative fallback
                        ]
                        
                        for params in search_params_list:
                            try:
                                response = await client.get('/api/customers', params=params)
                                if response.status_code == 200:
                                    data = response.json()
                                    customers = data if isinstance(data, list) else data.get('results', data.get('data', []))
                                    
                                    if customers:
                                        self.logger.info(f"✅ Found {len(customers)} customers with {params}")
                                        
                                        for customer in customers:
                                            customer_id = customer.get('id')
                                            if customer_id and customer_id not in seen_ids:
                                                all_customers.append(customer)
                                                seen_ids.add(customer_id)
                                        break  # Found results, no need to try other params
                                        
                            except Exception as e:
                                self.logger.error(f"Error in fallback search with params {params}: {e}")
                                continue
                                
                    except Exception as e:
                        self.logger.error(f"Error executing fallback strategy '{term}': {e}")
                        continue
                
                self.logger.info(f"🎯 Fallback search found {len(all_customers)} unique customers")
                return self._LLM_decision(all_customers, search_term)
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse fallback strategies JSON: {e}")
                self.logger.error(f"Raw LLM response: {response_text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error in LLM fallback search: {e}", exc_info=True)
            return []

    async def _get_customer_with_ytunnus_fallback(self, client, company_name: str) -> List[Dict]:
        """
        Search Google for company Y-tunnus and use it to find customer in Lemonsoft.
        
        Args:
            client: Lemonsoft API client
            company_name: Company name to search for
            
        Returns:
            List of customers found using Y-tunnus search
        """
        self.logger.info(f"Searching with Y-tunnus fallback for: {company_name}")
        
        # First check known companies
        company_lower = company_name.lower()
        for known_name, info in self.known_companies.items():
            if known_name in company_lower:
                self.logger.info(f"Found known Y-tunnus: {info['ytunnus']}")
                return await self._search_by_ytunnus(client, info['ytunnus'])
        
        # If no known Y-tunnus, search Google
        ytunnus = await self._search_ytunnus_with_google(company_name)
        if ytunnus:
            self.logger.info(f"Found Y-tunnus from Google search: {ytunnus}")
            return await self._search_by_ytunnus(client, ytunnus)
        
        self.logger.info("No Y-tunnus found through web search")
        return []
    
    async def _search_ytunnus_with_google(self, company_name: str) -> Optional[str]:
        """
        Search Google for company Y-tunnus using Serper API.
        
        Args:
            company_name: Company name to search for
            
        Returns:
            Y-tunnus if found, None otherwise
        """
        serper_api_key = os.getenv('SERPER_API_KEY')
        if not serper_api_key:
            self.logger.warning("SERPER_API_KEY not configured, cannot perform web search")
            return None
        
        try:
            search_query = f"{company_name} y-tunnus"
            self.logger.info(f"🔍 Searching Google for: '{search_query}'")
            
            async with httpx.AsyncClient() as http_client:
                payload = {
                    "q": search_query,
                    "location": "Finland",
                    "gl": "fi",
                    "hl": "fi",
                    "num": 10
                }
                headers = {
                    'X-API-KEY': serper_api_key,
                    'Content-Type': 'application/json'
                }
                
                response = await http_client.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                # Check for Serper API errors
                if response.status_code == 402:
                    raise Exception("SERPER_CREDITS_EXHAUSTED: Payment required - API credits exhausted")
                elif response.status_code == 429:
                    raise Exception("SERPER_RATE_LIMIT: Too many requests - API rate limit exceeded")
                elif response.status_code == 401:
                    raise Exception("SERPER_AUTH_ERROR: Unauthorized - Invalid API key")
                elif response.status_code != 200:
                    raise Exception(f"SERPER_API_ERROR: HTTP {response.status_code} - {response.reason_phrase}")
                
                search_results = response.json()
                
                # Check for error messages in response
                if isinstance(search_results, dict) and search_results.get('error'):
                    error_msg = search_results.get('error', 'Unknown error')
                    if any(keyword in str(error_msg).lower() for keyword in ['credit', 'quota', 'limit']):
                        raise Exception(f"SERPER_CREDITS_EXHAUSTED: {error_msg}")
                    raise Exception(f"SERPER_API_ERROR: {error_msg}")
                
                # Extract Y-tunnus from search results using LLM
                return await self._extract_ytunnus_from_search_results(search_results, company_name)
                
        except Exception as e:
            error_msg = str(e)
            if any(keyword in error_msg for keyword in ['SERPER_CREDITS_EXHAUSTED', 'SERPER_RATE_LIMIT', 'SERPER_AUTH_ERROR']):
                self.logger.error(f"Serper API error: {error_msg}")
            else:
                self.logger.error(f"Error searching for Y-tunnus: {e}", exc_info=True)
            return None
    
    async def _extract_ytunnus_from_search_results(self, search_results: Dict, company_name: str) -> Optional[str]:
        """
        Use Gemini LLM to extract Y-tunnus from Google search results.
        
        Args:
            search_results: Google search results from Serper API
            company_name: Original company name being searched
            
        Returns:
            Y-tunnus if found, None otherwise
        """
        if not self.gemini_client:
            self.logger.warning("Gemini not available for Y-tunnus extraction")
            return self._extract_ytunnus_with_regex(search_results)
        
        try:
            # Prepare search results for LLM analysis
            organic_results = search_results.get('organic', [])
            snippets = []
            
            for result in organic_results[:5]:  # Analyze top 5 results
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                if snippet:
                    snippets.append({
                        'title': title,
                        'snippet': snippet,
                        'url': result.get('link', '')
                    })
            
            if not snippets:
                self.logger.info("No snippets found in search results")
                return None
            
            prompt = f"""You are an expert at extracting Finnish business registration numbers (Y-tunnus) from web search results.

TASK: Find the Y-tunnus (Business ID) for the company "{company_name}" from these search results.

SEARCH RESULTS:
{json.dumps(snippets, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Look for Y-tunnus (Finnish business ID) in the format: XXXXXXX-X (7 digits, hyphen, 1 digit)
2. Ensure the Y-tunnus belongs to the company "{company_name}" mentioned in the search
3. Y-tunnus examples: 1740598-7, 0123456-9, 2345678-1
4. Only return Y-tunnus if you're confident it belongs to the correct company

RESPONSE FORMAT (JSON only):
{{
  "ytunnus": "1234567-8",
  "confidence": 0.95,
  "source": "snippet description where found",
  "found": true
}}

If no Y-tunnus found or uncertain, return:
{{
  "ytunnus": null,
  "confidence": 0.0,
  "source": "no reliable Y-tunnus found",
  "found": false
}}
"""

            self.logger.info(f"🤖 Asking Gemini to extract Y-tunnus for '{company_name}'")
            
            config = types.GenerateContentConfig(
                temperature=0.1,
                candidate_count=1,
            )

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )

            response_text = self._extract_gemini_response_text(response)
            if not response_text:
                self.logger.warning("No response from Gemini for Y-tunnus extraction")
                return self._extract_ytunnus_with_regex(search_results)
            
            # Parse LLM response
            try:
                json_text = response_text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]
                json_text = json_text.strip()
                
                extraction_result = json.loads(json_text)
                
                found = extraction_result.get('found', False)
                ytunnus = extraction_result.get('ytunnus')
                confidence = extraction_result.get('confidence', 0.0)
                source = extraction_result.get('source', '')
                
                if found and ytunnus and confidence >= 0.7:
                    # Validate Y-tunnus format
                    if re.match(r'^\d{7}-\d$', ytunnus):
                        self.logger.info(f"✅ Gemini extracted Y-tunnus: {ytunnus} "
                                       f"(confidence: {confidence:.2f}) - {source}")
                        return ytunnus
                    else:
                        self.logger.warning(f"Invalid Y-tunnus format from Gemini: {ytunnus}")
                else:
                    self.logger.info(f"Gemini did not find reliable Y-tunnus (confidence: {confidence:.2f})")
                
                return None
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse Y-tunnus extraction JSON: {e}")
                self.logger.error(f"Raw LLM response: {response_text}")
                return self._extract_ytunnus_with_regex(search_results)
                
        except Exception as e:
            self.logger.error(f"Error in LLM Y-tunnus extraction: {e}", exc_info=True)
            return self._extract_ytunnus_with_regex(search_results)
    
    def _extract_ytunnus_with_regex(self, search_results: Dict) -> Optional[str]:
        """
        Fallback method to extract Y-tunnus using regex patterns.
        
        Args:
            search_results: Google search results
            
        Returns:
            Y-tunnus if found, None otherwise
        """
        self.logger.info("Using regex fallback for Y-tunnus extraction")
        
        # Y-tunnus pattern: 7 digits, hyphen, 1 digit
        ytunnus_pattern = r'\b\d{7}-\d\b'
        
        organic_results = search_results.get('organic', [])
        for result in organic_results:
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            
            # Search in both title and snippet
            for text in [title, snippet]:
                matches = re.findall(ytunnus_pattern, text)
                if matches:
                    ytunnus = matches[0]
                    self.logger.info(f"✅ Regex found Y-tunnus: {ytunnus}")
                    return ytunnus
        
        self.logger.info("No Y-tunnus found with regex")
        return None
    
    async def _search_by_ytunnus(self, client, ytunnus: str) -> List[Dict]:
        """
        Search Lemonsoft API using Y-tunnus.
        
        Args:
            client: Lemonsoft API client
            ytunnus: Y-tunnus to search for
            
        Returns:
            List of customers found
        """
        self.logger.info(f"Searching Lemonsoft by Y-tunnus: {ytunnus}")
        
        # Try different parameter names for Y-tunnus search
        ytunnus_methods = [
            {'params': {'filter.vat': ytunnus}},
            {'params': {'vat': ytunnus}},
            {'params': {'business_id': ytunnus}},
            {'params': {'company_number': ytunnus}},
            {'params': {'search': ytunnus}},
            {'params': {'vatNumber': ytunnus}},
        ]
        
        for method in ytunnus_methods:
            try:
                response = await client.get('/api/customers', params=method['params'])
                if response.status_code == 200:
                    data = response.json()
                    # Use same parsing logic
                    if isinstance(data, list):
                        customers = data
                    elif isinstance(data, dict):
                        customers = data.get('results', data.get('data', []))
                    else:
                        customers = []
                    
                    if customers:
                        self.logger.info(f"✅ Found {len(customers)} customers via Y-tunnus search with {method['params']}")
                        return customers
                        
            except Exception as e:
                self.logger.error(f"Error in Y-tunnus search with {method['params']}: {e}")
                continue
        
        self.logger.info("No customers found via Y-tunnus search")
        return []
    
    def _extract_gemini_response_text(self, response) -> Optional[str]:
        """
        Extract text from Gemini API response.
        
        Args:
            response: Gemini API response object
            
        Returns:
            Response text if found, None otherwise
        """
        try:
            # Try different response formats
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        part = candidate.content.parts[0]
                        if hasattr(part, 'text') and part.text:
                            return part.text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting Gemini response text: {e}")
        
        return None
    
    async def _fetch_enhanced_customer_details(self, client, customer: Dict) -> Dict:
        """
        Fetch enhanced customer details including contacts, city, postal_code, etc.
        
        Args:
            client: Lemonsoft API client
            customer: Basic customer data from search
            
        Returns:
            Enhanced customer data with additional fields and CEO contact
        """
        customer_id = customer.get('id')
        if not customer_id:
            return customer
        
        try:
            self.logger.info(f"Fetching enhanced details for customer ID: {customer_id}")
            
            # Fetch detailed customer information
            response = await client.get(f'/api/customers/{customer_id}')
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch customer details: {response.status_code}")
                return customer
            
            detailed_customer = response.json()
            
            # Debug: Log what we got from the API
            person_resp_from_api = detailed_customer.get('person_responsible_number')
            self.logger.info(f"🔍 DEBUG - person_responsible_number from API: {person_resp_from_api} (type: {type(person_resp_from_api)})")
            
            # Check if the field might have a different name
            alternative_names = ['person_responsible', 'responsible_person', 'salesperson', 'person_seller', 
                                'seller_number', 'responsible_salesperson', 'responsible_person_number']
            for alt_name in alternative_names:
                if alt_name in detailed_customer:
                    self.logger.info(f"🔍 DEBUG - Found alternative field '{alt_name}': {detailed_customer.get(alt_name)}")
            
            # Log all fields that contain 'person' or 'seller' in the name
            person_fields = {k: v for k, v in detailed_customer.items() if 'person' in k.lower() or 'seller' in k.lower() or 'responsible' in k.lower()}
            if person_fields:
                self.logger.info(f"🔍 DEBUG - All person/seller/responsible fields from API: {person_fields}")
            else:
                self.logger.warning(f"⚠️ No person/seller/responsible fields found in customer API response")
            
            # Extract enhanced fields
            enhanced_data = {
                'id': detailed_customer.get('id', customer.get('id')),
                'number': detailed_customer.get('number', customer.get('number')),
                'name': detailed_customer.get('name', customer.get('name')),
                'street': detailed_customer.get('street', customer.get('street', '')),
                'city': detailed_customer.get('city', customer.get('city', '')),
                'postal_code': detailed_customer.get('postal_code', customer.get('postal_code', '')),
                'person_responsible_number': detailed_customer.get('person_responsible_number', ''),
                'vat_number': detailed_customer.get('vat_number', customer.get('vat_number', '')),
                'phone': detailed_customer.get('phone', customer.get('phone', '')),
                'email': detailed_customer.get('email', customer.get('email', '')),
                'deny_credit': detailed_customer.get('deny_credit', False),
            }
            
            # Extract CEO contact from contacts list
            ceo_contact = self._extract_ceo_contact(detailed_customer)
            if ceo_contact:
                enhanced_data['ceo_contact'] = ceo_contact
                self.logger.info(f"Found CEO contact: {ceo_contact}")
            else:
                enhanced_data['ceo_contact'] = ''
                self.logger.info("No CEO contact found")
            
            # Copy any additional fields that might be useful
            for key in ['contacts', 'attributes', 'currency_code']:
                if key in detailed_customer:
                    enhanced_data[key] = detailed_customer[key]
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Error fetching enhanced customer details: {e}")
            # Return original customer data if enhancement fails
            return customer
    
    def _extract_ceo_contact(self, customer_data: Dict) -> str:
        """
        Extract CEO contact from customer contacts.
        
        Args:
            customer_data: Full customer data including contacts
            
        Returns:
            CEO contact name if found, empty string otherwise
        """
        try:
            contacts = customer_data.get('contacts', [])
            if not contacts:
                return ''
            
            # Look for contact with attribute 5 "toimitusjohtaja" (CEO)
            for contact in contacts:
                contact_name = contact.get('name', '')
                attributes = contact.get('attributes', [])
                
                for attribute in attributes:
                    if (attribute.get('id') == 5 and 
                        attribute.get('selected') == True and
                        'toimitusjohtaja' in attribute.get('name', '').lower()):
                        self.logger.info(f"Found CEO contact: {contact_name} with attribute: {attribute.get('name')}")
                        return contact_name
            
            # Fallback: look for any contact with "toimitusjohtaja" in the attribute name
            for contact in contacts:
                contact_name = contact.get('name', '')
                attributes = contact.get('attributes', [])
                
                for attribute in attributes:
                    if (attribute.get('selected') == True and
                        'toimitusjohtaja' in attribute.get('name', '').lower()):
                        self.logger.info(f"Found CEO contact (fallback): {contact_name} with attribute: {attribute.get('name')}")
                        return contact_name
            
            # No CEO found
            self.logger.info("No CEO contact found in customer contacts")
            return ''
            
        except Exception as e:
            self.logger.error(f"Error extracting CEO contact: {e}")
            return ''
    
    async def _verify_company_name_match(self, api_customer_name: str, provided_company_name: str) -> bool:
        """
        Use Gemini LLM to verify if the API customer name matches the provided company name.
        
        Args:
            api_customer_name: Customer name from Lemonsoft API
            provided_company_name: Company name provided by user
            
        Returns:
            True if names match, False otherwise
        """
        if not self.gemini_client:
            self.logger.warning("Gemini not available for name verification, using basic string comparison")
            # Fallback to basic comparison
            api_name_clean = api_customer_name.lower().strip()
            provided_name_clean = provided_company_name.lower().strip()
            return api_name_clean == provided_name_clean or api_name_clean in provided_name_clean or provided_name_clean in api_name_clean
        
        try:
            prompt = f"""You are an expert at comparing Finnish company names to determine if they refer to the same company.

TASK: Compare these two company names and determine if they refer to the same company.

API CUSTOMER NAME: "{api_customer_name}"
PROVIDED COMPANY NAME: "{provided_company_name}"

INSTRUCTIONS:
1. Consider Finnish business naming conventions (Oy, Ab, Ltd, etc.)
2. Consider common abbreviations and variations
3. Consider that one name might be more formal than the other
4. Consider partial matches where one is clearly a shortened version of the other
5. Be flexible with punctuation, spacing, and capitalization
6. BE VERY FORGIVING - users often type shortened/informal versions of company names
7. If the core company name matches, consider it a match even if prefixes like "LVI", "Sähkö", etc. are missing
8. Return ONLY "true" or "false" - no other text

EXAMPLES OF MATCHES (ALL SHOULD BE TRUE):
- "LVI-Nordic Oy" matches "LVI-Nordic"
- "RAUMAN LÄMPÖ-KARTANO OY" matches "Rauman Lämpö-Kartano"
- "Assemblin Finland Oy" matches "Assemblin"
- "Takstek Oy" matches "LVI Takstek" (user added industry prefix)
- "Takstek Oy" matches "Takstek" (user omitted suffix)
- "LVI-Takstek Oy" matches "Takstek" (user omitted industry prefix)
- "Sähkö-Asennus Oy" matches "Asennus" (core name matches)
- "Putki-Pojat Oy" matches "Pojat" (partial match of core business name)

EXAMPLES OF NON-MATCHES (SHOULD BE FALSE):
- "Nordic Oy" does NOT match "Southern Oy" (completely different core names)
- "Asennus Oy" does NOT match "Rakennus Oy" (clearly different core names)

BE LENIENT: If the PROVIDED name could reasonably be a shortened/informal version of the API name, return true. Only return false, if the names are clearly different.
Focus on the CORE business name, not prefixes or suffixes.

RESPONSE: Return only "true" if they could refer to the same company, or "false" if clearly different. Dont provide ANY other text than "true" or "false"!!!
"""

            self.logger.info(f"🤖 Asking Gemini to compare '{api_customer_name}' with '{provided_company_name}'")
            
            config = types.GenerateContentConfig(
                temperature=0.6, 
                candidate_count=1,
            )

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )

            response_text = self._extract_gemini_response_text(response)
            if not response_text:
                self.logger.warning("No response from Gemini for name verification, using fallback")
                # Fallback to basic comparison
                api_name_clean = api_customer_name.lower().strip()
                provided_name_clean = provided_company_name.lower().strip()
                return api_name_clean == provided_name_clean or api_name_clean in provided_name_clean or provided_name_clean in api_name_clean
            
            # Clean and parse response
            result = response_text.strip().lower()
            
            if result == "true" or "true" in result:
                self.logger.info(f"✅ Gemini confirmed name match: '{api_customer_name}' ≈ '{provided_company_name}'")
                return True
            elif result == "false" or "false" in result:
                self.logger.info(f"❌ Gemini confirmed no match: '{api_customer_name}' ≠ '{provided_company_name}'")
                return False
            else:
                self.logger.warning(f"Unexpected Gemini response for name verification: '{result}', using fallback")
                # Fallback to basic comparison
                api_name_clean = api_customer_name.lower().strip()
                provided_name_clean = provided_company_name.lower().strip()
                return api_name_clean == provided_name_clean or api_name_clean in provided_name_clean or provided_name_clean in api_name_clean
                
        except Exception as e:
            self.logger.error(f"Error in LLM name verification: {e}", exc_info=True)
            # Fallback to basic comparison
            api_name_clean = api_customer_name.lower().strip()
            provided_name_clean = provided_company_name.lower().strip()
            return api_name_clean == provided_name_clean or api_name_clean in provided_name_clean or provided_name_clean in api_name_clean
    
