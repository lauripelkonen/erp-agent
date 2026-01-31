"""
Customer identification and lookup system with LLM integration.
Handles intelligent customer matching from email content using multiple strategies.
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime

import openai

from config.settings import get_settings
from utils.logger import get_logger, get_audit_logger
from utils.exceptions import CustomerNotFoundError, MultipleCustomersFoundError, ExternalServiceError
from utils.retry import retry_on_exception, LEMONSOFT_RETRY_CONFIG, WEB_SEARCH_RETRY_CONFIG
from lemonsoft.api_client import LemonsoftAPIClient
from customer.gemini_search import get_web_search_client


@dataclass
class CustomerMatch:
    """Represents a potential customer match with confidence scoring."""
    customer_id: str
    customer_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    confidence_score: float = 0.0
    match_method: str = "unknown"
    match_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.match_details is None:
            self.match_details = {}


class CustomerSearchStrategy:
    """Base class for customer search strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")
    
    async def search(self, search_terms: List[str], customer_info: Dict[str, Any]) -> List[CustomerMatch]:
        """Search for customers using this strategy."""
        raise NotImplementedError


class LemonsoftCustomerSearch(CustomerSearchStrategy):
    """Direct search in Lemonsoft customer database."""
    
    def __init__(self):
        super().__init__("lemonsoft_search")
        self.api_client = LemonsoftAPIClient()
    
    @retry_on_exception(config=LEMONSOFT_RETRY_CONFIG)
    async def search(self, search_terms: List[str], customer_info: Dict[str, Any]) -> List[CustomerMatch]:
        """Search customers in Lemonsoft database using various terms."""
        matches = []
        
        try:
            # Search by each term individually
            for term in search_terms[:5]:  # Limit to top 5 terms
                if len(term) < 3:  # Skip very short terms
                    continue
                
                self.logger.debug(f"Searching Lemonsoft for: {term}")
                
                # Try different search variations
                search_variations = [
                    term,
                    term.replace(' ', ''),  # Remove spaces
                    term.replace('-', ''),  # Remove hyphens
                    term.split()[0] if ' ' in term else term,  # First word only
                ]
                
                for variation in search_variations:
                    customers = await self._search_lemonsoft_customers(variation)
                    
                    for customer in customers:
                        match = self._create_customer_match(
                            customer, term, variation, customer_info
                        )
                        if match.confidence_score > 0.3:  # Minimum threshold
                            matches.append(match)
                
                # Break early if we found high-confidence matches
                if any(m.confidence_score > 0.8 for m in matches):
                    break
        
        except Exception as e:
            self.logger.error(f"Lemonsoft customer search failed: {e}")
            raise ExternalServiceError(
                f"Failed to search Lemonsoft customers: {str(e)}",
                service="lemonsoft",
                context={'search_terms': search_terms}
            )
        
        return matches
    
    async def _search_lemonsoft_customers(self, search_term: str) -> List[Dict[str, Any]]:
        """Perform actual Lemonsoft API search."""
        try:
            # Use the Lemonsoft customer search API
            response = await self.api_client.get(
                f"/api/customers/search",
                params={'q': search_term, 'limit': 10}
            )
            
            return response.get('customers', [])
            
        except Exception as e:
            self.logger.warning(f"Lemonsoft search failed for '{search_term}': {e}")
            return []
    
    def _create_customer_match(
        self, 
        customer: Dict[str, Any], 
        search_term: str, 
        variation: str, 
        customer_info: Dict[str, Any]
    ) -> CustomerMatch:
        """Create CustomerMatch from Lemonsoft customer data."""
        customer_name = customer.get('name', '')
        
        # Calculate confidence based on name similarity
        name_similarity = SequenceMatcher(None, search_term.lower(), customer_name.lower()).ratio()
        
        # Boost confidence for exact domain matches
        email_boost = 0.0
        customer_email = customer.get('email', '')
        if customer_email and customer_info.get('email_address'):
            search_domain = customer_info['email_address'].split('@')[1] if '@' in customer_info['email_address'] else ''
            customer_domain = customer_email.split('@')[1] if '@' in customer_email else ''
            if search_domain and customer_domain and search_domain == customer_domain:
                email_boost = 0.3
        
        # Calculate final confidence
        confidence = min(name_similarity + email_boost, 1.0)
        
        return CustomerMatch(
            customer_id=str(customer.get('id', '')),
            customer_name=customer_name,
            email=customer.get('email'),
            phone=customer.get('phone'),
            address=customer.get('address'),
            confidence_score=confidence,
            match_method="lemonsoft_direct",
            match_details={
                'search_term': search_term,
                'variation_used': variation,
                'name_similarity': name_similarity,
                'email_boost': email_boost,
                'customer_data': customer
            }
        )


class FuzzyNameMatcher(CustomerSearchStrategy):
    """Advanced fuzzy matching for customer names."""
    
    def __init__(self):
        super().__init__("fuzzy_matcher")
        self.api_client = LemonsoftAPIClient()
    
    async def search(self, search_terms: List[str], customer_info: Dict[str, Any]) -> List[CustomerMatch]:
        """Perform fuzzy matching on all customers."""
        matches = []
        
        try:
            # Get all customers (or a reasonable subset)
            all_customers = await self._get_customer_list()
            
            for customer in all_customers:
                best_match = self._find_best_fuzzy_match(customer, search_terms, customer_info)
                if best_match and best_match.confidence_score > 0.5:
                    matches.append(best_match)
            
            # Sort by confidence and limit results
            matches.sort(key=lambda x: x.confidence_score, reverse=True)
            return matches[:10]
            
        except Exception as e:
            self.logger.error(f"Fuzzy matching failed: {e}")
            return []
    
    async def _get_customer_list(self) -> List[Dict[str, Any]]:
        """Get list of customers for fuzzy matching."""
        try:
            # Get recent customers or use search with wildcard
            response = await self.api_client.get(
                "/api/customers",
                params={'limit': 500, 'active': True}
            )
            return response.get('customers', [])
        except Exception as e:
            self.logger.warning(f"Failed to get customer list: {e}")
            return []
    
    def _find_best_fuzzy_match(
        self, 
        customer: Dict[str, Any], 
        search_terms: List[str], 
        customer_info: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Find best fuzzy match for a customer."""
        customer_name = customer.get('name', '').lower()
        best_score = 0.0
        best_term = ""
        
        # Try matching against each search term
        for term in search_terms:
            term_lower = term.lower()
            
            # Different matching strategies
            scores = [
                SequenceMatcher(None, term_lower, customer_name).ratio(),
                self._calculate_word_overlap(term_lower, customer_name),
                self._calculate_substring_match(term_lower, customer_name),
                self._calculate_acronym_match(term_lower, customer_name),
            ]
            
            score = max(scores)
            if score > best_score:
                best_score = score
                best_term = term
        
        if best_score < 0.5:
            return None
        
        return CustomerMatch(
            customer_id=str(customer.get('id', '')),
            customer_name=customer.get('name', ''),
            email=customer.get('email'),
            phone=customer.get('phone'),
            address=customer.get('address'),
            confidence_score=best_score,
            match_method="fuzzy_matching",
            match_details={
                'best_term': best_term,
                'score_breakdown': {
                    'sequence_match': SequenceMatcher(None, best_term.lower(), customer_name).ratio(),
                    'word_overlap': self._calculate_word_overlap(best_term.lower(), customer_name),
                    'substring_match': self._calculate_substring_match(best_term.lower(), customer_name),
                    'acronym_match': self._calculate_acronym_match(best_term.lower(), customer_name),
                }
            }
        )
    
    def _calculate_word_overlap(self, term: str, customer_name: str) -> float:
        """Calculate word overlap ratio."""
        term_words = set(term.split())
        customer_words = set(customer_name.split())
        
        if not term_words or not customer_words:
            return 0.0
        
        overlap = len(term_words.intersection(customer_words))
        return overlap / max(len(term_words), len(customer_words))
    
    def _calculate_substring_match(self, term: str, customer_name: str) -> float:
        """Calculate substring matching score."""
        if term in customer_name or customer_name in term:
            return min(len(term), len(customer_name)) / max(len(term), len(customer_name))
        return 0.0
    
    def _calculate_acronym_match(self, term: str, customer_name: str) -> float:
        """Calculate acronym matching score."""
        # Check if term could be an acronym of customer name
        customer_words = customer_name.split()
        if len(customer_words) >= len(term):
            acronym = ''.join(word[0] for word in customer_words if word)
            if acronym.lower() == term.lower():
                return 0.9
        
        # Check reverse (customer name acronym matches term)
        term_words = term.split()
        if len(term_words) >= len(customer_name.replace(' ', '')):
            term_acronym = ''.join(word[0] for word in term_words if word)
            if term_acronym.lower() == customer_name.replace(' ', '').lower():
                return 0.8
        
        return 0.0


class WebSearchCustomerFinder(CustomerSearchStrategy):
    """Web search fallback for company identification using Gemini 2.0 Search Grounding."""
    
    def __init__(self):
        super().__init__("web_search")
        self.settings = get_settings()
        self.search_client = get_web_search_client()
    
    @retry_on_exception(config=WEB_SEARCH_RETRY_CONFIG)
    async def search(self, search_terms: List[str], customer_info: Dict[str, Any]) -> List[CustomerMatch]:
        """Search web for company information using Gemini Search Grounding and match to known customers."""
        matches = []
        
        if not self.search_client:
            self.logger.warning("No web search client available - Search Grounding may be disabled")
            return []
        
        try:
            for term in search_terms[:3]:  # Limit web searches
                if len(term) < 4:  # Skip very short terms
                    continue
                
                company_info = await self.search_client.search_company(term)
                if company_info:
                    # Try to match found company info back to Lemonsoft customers
                    lemonsoft_matches = await self._match_web_result_to_customers(
                        company_info, term, customer_info
                    )
                    matches.extend(lemonsoft_matches)
            
            return matches
            
        except Exception as e:
            self.logger.warning(f"Gemini Search Grounding failed: {e}")
            return []
    
    async def _match_web_result_to_customers(
        self, 
        company_info: Dict[str, Any], 
        original_term: str, 
        customer_info: Dict[str, Any]
    ) -> List[CustomerMatch]:
        """Match Gemini Search Grounding results back to Lemonsoft customers."""
        try:
            # Use the found company name to search Lemonsoft again
            lemonsoft_search = LemonsoftCustomerSearch()
            company_name = company_info.get('company_name', '')
            
            if company_name:
                matches = await lemonsoft_search.search([company_name], customer_info)
                
                # Adjust confidence scores for web-search-assisted matches
                for match in matches:
                    match.match_method = "gemini_search_grounding_assisted"
                    match.confidence_score *= 0.85  # Slight reduction for indirect method
                    match.match_details.update({
                        'gemini_search_info': company_info,
                        'original_search_term': original_term,
                        'grounding_source': 'gemini_2.0_search'
                    })
                
                return matches
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to match Gemini search results to customers: {e}")
            return []


class LLMCustomerAnalyzer(CustomerSearchStrategy):
    """LLM-powered customer analysis and disambiguation."""
    
    def __init__(self):
        super().__init__("llm_analyzer")
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(
            api_key=self.settings.gemini_api_key,
            base_url=self.settings.openai_base_url
        )
    
    async def analyze_and_disambiguate(
        self, 
        potential_matches: List[CustomerMatch], 
        customer_info: Dict[str, Any], 
        email_content: str = ""
    ) -> List[CustomerMatch]:
        """Use LLM to analyze and disambiguate customer matches."""
        if not potential_matches:
            return []
        
        try:
            # Prepare context for LLM analysis
            analysis_prompt = self._create_analysis_prompt(
                potential_matches, customer_info, email_content
            )
            
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at customer identification and disambiguation. Analyze the provided customer matches and email context to determine the most likely customer match."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            analysis_result = response.choices[0].message.content
            
            # Parse LLM response and update confidence scores
            updated_matches = self._parse_llm_analysis(
                potential_matches, analysis_result, customer_info
            )
            
            return updated_matches
            
        except Exception as e:
            self.logger.warning(f"LLM customer analysis failed: {e}")
            # Return original matches if LLM analysis fails
            return potential_matches
    
    def _create_analysis_prompt(
        self, 
        matches: List[CustomerMatch], 
        customer_info: Dict[str, Any], 
        email_content: str
    ) -> str:
        """Create prompt for LLM customer analysis."""
        prompt_parts = [
            "Please analyze the following customer identification scenario:",
            "",
            "EMAIL CONTEXT:",
            f"Sender email: {customer_info.get('email_address', 'unknown')}",
            f"Search terms extracted: {', '.join(customer_info.get('search_terms', [])[:5])}",
            f"Company indicators: {', '.join(customer_info.get('company_indicators', []))}",
            ""
        ]
        
        if email_content:
            prompt_parts.extend([
                "EMAIL CONTENT EXCERPT:",
                email_content[:500] + "..." if len(email_content) > 500 else email_content,
                ""
            ])
        
        prompt_parts.extend([
            "POTENTIAL CUSTOMER MATCHES:",
            ""
        ])
        
        for i, match in enumerate(matches[:5], 1):  # Limit to top 5
            prompt_parts.extend([
                f"Match {i}:",
                f"  Name: {match.customer_name}",
                f"  ID: {match.customer_id}",
                f"  Email: {match.email or 'N/A'}",
                f"  Confidence: {match.confidence_score:.2f}",
                f"  Method: {match.match_method}",
                ""
            ])
        
        prompt_parts.extend([
            "TASK:",
            "1. Analyze each match against the email context",
            "2. Provide a confidence score (0.0-1.0) for each match",
            "3. Identify the most likely customer or state if none are satisfactory",
            "4. Provide reasoning for your assessment",
            "",
            "RESPONSE FORMAT:",
            "For each match, provide:",
            "Match X: [confidence_score] - [reasoning]",
            "",
            "Best match: [Match number or 'None'] - [overall reasoning]"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_analysis(
        self, 
        original_matches: List[CustomerMatch], 
        analysis_result: str, 
        customer_info: Dict[str, Any]
    ) -> List[CustomerMatch]:
        """Parse LLM analysis and update confidence scores."""
        updated_matches = []
        
        try:
            lines = analysis_result.strip().split('\n')
            
            # Extract confidence scores from LLM analysis
            match_scores = {}
            best_match_info = ""
            
            for line in lines:
                # Look for match confidence scores
                match_pattern = r'Match (\d+):\s*([0-9.]+)\s*-\s*(.+)'
                match_result = re.search(match_pattern, line, re.IGNORECASE)
                
                if match_result:
                    match_idx = int(match_result.group(1)) - 1  # Convert to 0-based
                    llm_confidence = float(match_result.group(2))
                    reasoning = match_result.group(3)
                    
                    if 0 <= match_idx < len(original_matches):
                        match_scores[match_idx] = {
                            'llm_confidence': llm_confidence,
                            'reasoning': reasoning
                        }
                
                # Look for best match conclusion
                if 'best match:' in line.lower():
                    best_match_info = line
            
            # Update matches with LLM analysis
            for i, match in enumerate(original_matches):
                updated_match = CustomerMatch(
                    customer_id=match.customer_id,
                    customer_name=match.customer_name,
                    email=match.email,
                    phone=match.phone,
                    address=match.address,
                    confidence_score=match.confidence_score,
                    match_method=f"{match.match_method}_llm_analyzed",
                    match_details=match.match_details.copy()
                )
                
                if i in match_scores:
                    llm_data = match_scores[i]
                    
                    # Combine original confidence with LLM confidence
                    combined_confidence = (
                        match.confidence_score * 0.6 + 
                        llm_data['llm_confidence'] * 0.4
                    )
                    
                    updated_match.confidence_score = min(combined_confidence, 1.0)
                    updated_match.match_details.update({
                        'llm_analysis': {
                            'llm_confidence': llm_data['llm_confidence'],
                            'reasoning': llm_data['reasoning'],
                            'combined_confidence': combined_confidence
                        },
                        'best_match_info': best_match_info
                    })
                
                updated_matches.append(updated_match)
            
            # Sort by updated confidence scores
            updated_matches.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return updated_matches
            
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM analysis: {e}")
            return original_matches

    async def search(self, search_terms: List[str], customer_info: Dict[str, Any]) -> List[CustomerMatch]:
        """LLM analyzer doesn't perform direct search - use analyze_and_disambiguate instead."""
        return []


class CustomerLookup:
    """Main customer lookup orchestrator with multiple search strategies."""
    
    def __init__(self):
        """Initialize customer lookup with all search strategies."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit_logger = get_audit_logger()
        
        # Initialize search strategies
        self.strategies = [
            LemonsoftCustomerSearch(),
            FuzzyNameMatcher(),
            WebSearchCustomerFinder(),
        ]
        
        self.llm_analyzer = LLMCustomerAnalyzer()
    
    async def find_customer(
        self, 
        customer_info: Dict[str, Any], 
        email_content: str = ""
    ) -> Optional[CustomerMatch]:
        """
        Find customer using multiple search strategies and LLM analysis.
        
        Args:
            customer_info: Extracted customer information from email
            email_content: Original email content for context
            
        Returns:
            Best customer match or None if no suitable match found
        """
        request_id = customer_info.get('request_id', 'unknown')
        search_terms = customer_info.get('search_terms', [])
        
        try:
            self.logger.info(
                f"Starting customer lookup",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'search_terms_count': len(search_terms),
                        'email_domain': customer_info.get('email_address', '').split('@')[1] if '@' in customer_info.get('email_address', '') else 'unknown'
                    }
                }
            )
            
            if not search_terms:
                self.logger.warning("No search terms provided for customer lookup")
                raise CustomerNotFoundError(
                    "No customer search terms could be extracted from email",
                    context={'customer_info': customer_info}
                )
            
            # Run all search strategies in parallel
            all_matches = []
            
            search_tasks = [
                strategy.search(search_terms, customer_info)
                for strategy in self.strategies
            ]
            
            strategy_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Collect matches from successful strategies
            for i, result in enumerate(strategy_results):
                if isinstance(result, Exception):
                    self.logger.warning(
                        f"Strategy {self.strategies[i].name} failed: {result}"
                    )
                    continue
                
                if result:
                    self.logger.debug(
                        f"Strategy {self.strategies[i].name} found {len(result)} matches"
                    )
                    all_matches.extend(result)
            
            # Remove duplicates and sort by confidence
            unique_matches = self._deduplicate_matches(all_matches)
            unique_matches.sort(key=lambda x: x.confidence_score, reverse=True)
            
            self.logger.info(
                f"Found {len(unique_matches)} unique customer matches",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'total_matches': len(all_matches),
                        'unique_matches': len(unique_matches),
                        'top_confidence': unique_matches[0].confidence_score if unique_matches else 0.0
                    }
                }
            )
            
            # Use LLM analysis for disambiguation if we have multiple matches
            if len(unique_matches) > 1:
                self.logger.info(f"Running LLM analysis for customer disambiguation")
                analyzed_matches = await self.llm_analyzer.analyze_and_disambiguate(
                    unique_matches[:5],  # Analyze top 5 matches
                    customer_info,
                    email_content
                )
                unique_matches = analyzed_matches
            
            # Determine final result
            if not unique_matches:
                self.logger.warning(f"No customer matches found")
                self.audit_logger.log_customer_lookup(
                    request_id, 
                    str(search_terms), 
                    None, 
                    method="comprehensive_search",
                    context={'strategies_used': [s.name for s in self.strategies]}
                )
                raise CustomerNotFoundError(
                    "No matching customers found in database",
                    context={
                        'search_terms': search_terms,
                        'strategies_used': [s.name for s in self.strategies]
                    }
                )
            
            best_match = unique_matches[0]
            
            # Check for multiple high-confidence matches
            high_confidence_matches = [
                m for m in unique_matches 
                if m.confidence_score > 0.8 and abs(m.confidence_score - best_match.confidence_score) < 0.1
            ]
            
            if len(high_confidence_matches) > 1:
                self.logger.warning(f"Multiple high-confidence customer matches found")
                self.audit_logger.log_customer_lookup(
                    request_id, 
                    str(search_terms), 
                    high_confidence_matches, 
                    method="comprehensive_search",
                    context={'ambiguous_matches': len(high_confidence_matches)}
                )
                raise MultipleCustomersFoundError(
                    f"Found {len(high_confidence_matches)} highly similar customer matches",
                    customers=high_confidence_matches,
                    context={'search_terms': search_terms}
                )
            
            # Return best match if confidence is sufficient
            if best_match.confidence_score < 0.6:
                self.logger.warning(
                    f"Best customer match has low confidence: {best_match.confidence_score:.2f}"
                )
                raise CustomerNotFoundError(
                    f"Customer match confidence too low: {best_match.confidence_score:.2f}",
                    context={
                        'best_match': {
                            'name': best_match.customer_name,
                            'confidence': best_match.confidence_score,
                            'method': best_match.match_method
                        },
                        'search_terms': search_terms
                    }
                )
            
            # Log successful customer identification
            self.audit_logger.log_customer_lookup(
                request_id, 
                str(search_terms), 
                best_match, 
                method="comprehensive_search",
                context={
                    'final_confidence': best_match.confidence_score,
                    'match_method': best_match.match_method,
                    'total_candidates': len(unique_matches)
                }
            )
            
            self.logger.info(
                f"Customer identified: {best_match.customer_name}",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'customer_id': best_match.customer_id,
                        'customer_name': best_match.customer_name,
                        'confidence_score': best_match.confidence_score,
                        'match_method': best_match.match_method
                    }
                }
            )
            
            return best_match
            
        except (CustomerNotFoundError, MultipleCustomersFoundError):
            # Re-raise customer-specific errors as-is
            raise
        except Exception as e:
            self.logger.error(f"Customer lookup failed: {e}", exc_info=True)
            raise ExternalServiceError(
                f"Customer lookup system error: {str(e)}",
                service="customer_lookup",
                context={'search_terms': search_terms}
            )
    
    def _deduplicate_matches(self, matches: List[CustomerMatch]) -> List[CustomerMatch]:
        """Remove duplicate customer matches."""
        seen_customers = {}
        unique_matches = []
        
        for match in matches:
            customer_key = match.customer_id
            
            if customer_key not in seen_customers:
                seen_customers[customer_key] = match
                unique_matches.append(match)
            else:
                # Keep the match with higher confidence
                existing_match = seen_customers[customer_key]
                if match.confidence_score > existing_match.confidence_score:
                    # Replace in both dict and list
                    seen_customers[customer_key] = match
                    for i, existing in enumerate(unique_matches):
                        if existing.customer_id == customer_key:
                            unique_matches[i] = match
                            break
        
        return unique_matches
    
    async def validate_customer(self, customer_match: CustomerMatch) -> bool:
        """
        Validate that a customer match is still valid and active.
        
        Args:
            customer_match: Customer match to validate
            
        Returns:
            True if customer is valid and active
        """
        try:
            # Check if customer still exists and is active in Lemonsoft
            api_client = LemonsoftAPIClient()
            customer_data = await api_client.get(f"/api/customers/{customer_match.customer_id}")
            
            if not customer_data:
                self.logger.warning(f"Customer {customer_match.customer_id} not found during validation")
                return False
            
            # Check if customer is active
            is_active = customer_data.get('active', True)
            if not is_active:
                self.logger.warning(f"Customer {customer_match.customer_id} is inactive")
                return False
            
            self.logger.debug(f"Customer {customer_match.customer_id} validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Customer validation failed for {customer_match.customer_id}: {e}")
            return False 