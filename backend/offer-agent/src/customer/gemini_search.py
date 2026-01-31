"""
Gemini 2.0 Search Grounding implementation for web search functionality.
Replaces traditional web scraping with Google's Search Grounding tool.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    import google.generativeai as genai
    from google.generativeai.types import Tool, GenerateContentConfig, GoogleSearch
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

from config.settings import get_settings
from utils.logger import get_logger
from utils.exceptions import ExternalServiceError
from utils.retry import retry_on_exception, WEB_SEARCH_RETRY_CONFIG


@dataclass
class SearchResult:
    """Represents a search result from Gemini Search Grounding."""
    title: str
    url: str
    snippet: str
    source: str = "gemini_search_grounding"


class GeminiSearchGrounding:
    """
    Gemini 2.0 Search Grounding for intelligent web searches.
    Uses Google's built-in search capabilities through Gemini 2.0 Flash.
    """
    
    def __init__(self):
        """Initialize Gemini Search Grounding client."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not available. "
                "Install with: pip install google-generativeai>=0.7.0"
            )
        
        if not self.settings.enable_search_grounding:
            self.logger.warning("Search Grounding is disabled in settings")
            return
        
        # Configure Google GenAI client
        genai.configure(api_key=self.settings.gemini_api_key)
        self.client = genai.Client()
        self.model_id = "gemini-2.0-flash"
        
        # Configure Google Search tool
        self.google_search_tool = Tool(google_search=GoogleSearch())
        
        self.logger.info("Gemini Search Grounding initialized successfully")
    
    @retry_on_exception(config=WEB_SEARCH_RETRY_CONFIG)
    async def search_company(self, search_term: str, location: str = "Finland") -> Optional[Dict[str, Any]]:
        """
        Search for company information using Gemini 2.0 Search Grounding.
        
        Args:
            search_term: Company name or search term
            location: Geographic location to focus search (default: Finland)
            
        Returns:
            Company information extracted from search results or None
        """
        if not self.settings.enable_search_grounding:
            self.logger.debug("Search Grounding disabled, skipping web search")
            return None
        
        try:
            # Construct search query
            search_query = f"{search_term} company {location} contact information business"
            
            self.logger.info(f"Performing Gemini Search Grounding for: {search_query}")
            
            # Execute search with Gemini 2.0 Search Grounding
            response = await self._execute_search(search_query)
            
            if not response:
                return None
            
            # Extract company information from grounded search results
            company_info = self._extract_company_info(response, search_term)
            
            if company_info:
                self.logger.info(f"Found company info via Search Grounding: {company_info.get('company_name')}")
                return company_info
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Gemini Search Grounding failed for '{search_term}': {e}")
            return None
    
    async def _execute_search(self, query: str) -> Optional[str]:
        """Execute search using Gemini 2.0 with Google Search tool."""
        try:
            # Create search prompt for company identification
            search_prompt = f"""
            Search for information about: {query}
            
            Please find and provide:
            1. Company name and any variations
            2. Contact information (email, phone, address)
            3. Business type or industry
            4. Location/country
            5. Any other relevant company details
            
            Focus on finding accurate, current business information.
            """
            
            # Use Gemini 2.0 with Search Grounding
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=search_prompt,
                config=GenerateContentConfig(
                    tools=[self.google_search_tool],
                    response_modalities=["TEXT"],
                    temperature=0.1,  # Low temperature for factual information
                )
            )
            
            # Extract response text
            if response.candidates and response.candidates[0].content.parts:
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text
                
                # Log grounding metadata if available
                if (hasattr(response.candidates[0], 'grounding_metadata') and 
                    response.candidates[0].grounding_metadata and
                    response.candidates[0].grounding_metadata.search_entry_point):
                    
                    rendered_content = response.candidates[0].grounding_metadata.search_entry_point.rendered_content
                    self.logger.debug(f"Search grounding metadata: {rendered_content[:200]}...")
                
                return response_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Gemini Search Grounding execution failed: {e}")
            raise ExternalServiceError(
                f"Search Grounding API error: {str(e)}",
                service="gemini_search_grounding",
                context={'query': query}
            )
    
    def _extract_company_info(self, search_response: str, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured company information from Gemini search response.
        
        Args:
            search_response: Text response from Gemini with search results
            search_term: Original search term
            
        Returns:
            Structured company information or None
        """
        try:
            if not search_response:
                return None
            
            # Initialize company info structure
            company_info = {
                'search_term': search_term,
                'source': 'gemini_search_grounding',
                'raw_response': search_response
            }
            
            # Extract company name using patterns
            company_name = self._extract_company_name(search_response, search_term)
            if company_name:
                company_info['company_name'] = company_name
            
            # Extract contact information
            contact_info = self._extract_contact_info(search_response)
            company_info.update(contact_info)
            
            # Extract business details
            business_info = self._extract_business_details(search_response)
            company_info.update(business_info)
            
            # Only return if we found meaningful information
            if company_info.get('company_name') or company_info.get('email') or company_info.get('phone'):
                return company_info
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract company info from search response: {e}")
            return None
    
    def _extract_company_name(self, text: str, search_term: str) -> Optional[str]:
        """Extract company name from search response text."""
        try:
            # Common Finnish company suffixes
            company_patterns = [
                rf'({re.escape(search_term)}[^.\n]*(?:Oy|Oyj|Ltd|AB|Inc|Corp|Company|Yritys))',
                rf'((?:Oy|Oyj|Ltd|AB|Inc|Corp)\s+{re.escape(search_term)}[^.\n]*)',
                rf'({re.escape(search_term)}[^.\n]*)',  # Fallback pattern
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Return the first clean match
                    company_name = matches[0].strip()
                    if len(company_name) > 3:  # Minimum length check
                        return company_name
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Company name extraction failed: {e}")
            return None
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from search response text."""
        contact_info = {}
        
        try:
            # Email patterns
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            if emails:
                contact_info['email'] = emails[0]  # Take the first email found
            
            # Phone patterns (Finnish and international)
            phone_patterns = [
                r'\+358[- ]?\d{1,3}[- ]?\d{3,7}',  # Finnish international format
                r'0\d{1,3}[- ]?\d{3,7}',  # Finnish national format
                r'\+\d{1,3}[- ]?\d{3,4}[- ]?\d{3,7}',  # General international
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, text)
                if phones:
                    contact_info['phone'] = phones[0]
                    break
            
            # Address extraction (basic)
            # Look for lines that might contain address information
            address_keywords = ['address', 'osoite', 'street', 'katu', 'tie', 'postal', 'postinumero']
            lines = text.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in address_keywords):
                    # Simple address extraction
                    clean_line = line.strip()
                    if len(clean_line) > 10 and len(clean_line) < 200:
                        contact_info['address'] = clean_line
                        break
            
        except Exception as e:
            self.logger.warning(f"Contact info extraction failed: {e}")
        
        return contact_info
    
    def _extract_business_details(self, text: str) -> Dict[str, str]:
        """Extract business details from search response text."""
        business_info = {}
        
        try:
            # Industry/business type keywords
            industry_keywords = [
                'technology', 'tekniikka', 'software', 'ohjelmisto',
                'manufacturing', 'valmistus', 'construction', 'rakentaminen',
                'services', 'palvelut', 'consulting', 'konsultointi',
                'engineering', 'insinööri', 'logistics', 'logistiikka'
            ]
            
            text_lower = text.lower()
            for keyword in industry_keywords:
                if keyword in text_lower:
                    business_info['industry'] = keyword.title()
                    break
            
            # Location extraction
            finnish_cities = [
                'helsinki', 'espoo', 'tampere', 'vantaa', 'oulu', 'turku',
                'jyväskylä', 'lahti', 'kuopio', 'pori', 'kouvola', 'joensuu'
            ]
            
            for city in finnish_cities:
                if city in text_lower:
                    business_info['location'] = city.title()
                    break
            
        except Exception as e:
            self.logger.warning(f"Business details extraction failed: {e}")
        
        return business_info


class LegacyWebSearch:
    """
    Fallback web search implementation using traditional scraping.
    Used when Gemini Search Grounding is not available or disabled.
    """
    
    def __init__(self):
        """Initialize legacy web search."""
        self.logger = get_logger(__name__)
        self.logger.warning("Using legacy web search - consider enabling Gemini Search Grounding")
    
    async def search_company(self, search_term: str, location: str = "Finland") -> Optional[Dict[str, Any]]:
        """Fallback to basic web search (placeholder implementation)."""
        self.logger.info(f"Legacy web search not implemented for: {search_term}")
        return None


def get_web_search_client() -> Any:
    """
    Factory function to get appropriate web search client.
    
    Returns:
        GeminiSearchGrounding if available and enabled, otherwise LegacyWebSearch
    """
    settings = get_settings()
    
    if (GOOGLE_GENAI_AVAILABLE and 
        settings.enable_search_grounding and 
        settings.gemini_api_key):
        try:
            return GeminiSearchGrounding()
        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(f"Failed to initialize Gemini Search Grounding: {e}")
    
    return LegacyWebSearch() 