"""
Advanced customer data analyzer with pattern recognition and validation.
Analyzes customer information from various sources to improve matching accuracy.
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import difflib

from src.utils.logger import get_logger
from src.config.settings import get_settings


@dataclass
class CustomerSignature:
    """Represents a unique signature for customer identification."""
    company_name_variants: Set[str]
    email_domains: Set[str]
    phone_patterns: Set[str]
    address_components: Set[str]
    business_identifiers: Set[str]  # VAT numbers, business IDs
    industry_keywords: Set[str]
    
    def __post_init__(self):
        # Ensure all fields are sets
        for field_name in self.__dataclass_fields__:
            field_value = getattr(self, field_name)
            if not isinstance(field_value, set):
                setattr(self, field_name, set(field_value) if field_value else set())


class CustomerDataAnalyzer:
    """Advanced customer data analysis for improved matching and validation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Finnish business patterns
        self.finnish_business_patterns = {
            'y_tunnus': re.compile(r'\b\d{7}-\d\b'),  # Finnish business ID
            'vat_number': re.compile(r'\bFI\d{8}\b'),  # Finnish VAT number
            'company_forms': re.compile(r'\b(Oy|Ltd|AB|Oyj|Inc|Ky|Ay|T:mi)\b', re.IGNORECASE),
        }
        
        # Common Finnish company name variations
        self.finnish_company_variations = [
            'Oy', 'Ltd', 'AB', 'Oyj', 'Inc', 'Ky', 'Ay', 'T:mi',
            'Osakeyhtiö', 'Limited', 'Aktiebolag', 'Julkinen osakeyhtiö',
            'Kommandiittiyhtiö', 'Avoin yhtiö', 'Toiminimi'
        ]
        
        # Industry keyword mappings
        self.industry_keywords = {
            'manufacturing': ['tehdas', 'tuotanto', 'valmistus', 'manufacturing', 'factory'],
            'construction': ['rakennus', 'rakentaminen', 'construction', 'building'],
            'technology': ['teknologia', 'IT', 'ohjelmisto', 'technology', 'software'],
            'healthcare': ['terveys', 'lääke', 'health', 'medical', 'pharmaceutical'],
            'retail': ['kauppa', 'myynti', 'retail', 'shop', 'store'],
            'logistics': ['logistiikka', 'kuljetus', 'logistics', 'transport', 'shipping'],
        }
    
    async def analyze_customer_info(self, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of customer information.
        
        Args:
            customer_info: Raw customer information from email parsing
            
        Returns:
            Enhanced customer information with analysis results
        """
        self.logger.debug("Starting customer data analysis")
        
        analysis_results = {
            'original_info': customer_info.copy(),
            'enhanced_search_terms': [],
            'company_signature': None,
            'confidence_boosters': {},
            'industry_classification': [],
            'business_identifiers': {},
            'contact_patterns': {},
            'analysis_metadata': {
                'analyzed_at': datetime.utcnow().isoformat(),
                'analyzer_version': '1.0'
            }
        }
        
        try:
            # Extract and normalize company names
            company_names = await self._extract_company_names(customer_info)
            analysis_results['enhanced_search_terms'].extend(company_names)
            
            # Generate company name variations
            name_variations = await self._generate_name_variations(company_names)
            analysis_results['enhanced_search_terms'].extend(name_variations)
            
            # Extract business identifiers
            business_ids = await self._extract_business_identifiers(customer_info)
            analysis_results['business_identifiers'] = business_ids
            
            # Analyze contact patterns
            contact_analysis = await self._analyze_contact_patterns(customer_info)
            analysis_results['contact_patterns'] = contact_analysis
            
            # Industry classification
            industry_info = await self._classify_industry(customer_info)
            analysis_results['industry_classification'] = industry_info
            
            # Create customer signature
            signature = await self._create_customer_signature(
                company_names, customer_info, business_ids, contact_analysis
            )
            analysis_results['company_signature'] = signature
            
            # Calculate confidence boosters
            boosters = await self._calculate_confidence_boosters(
                customer_info, business_ids, contact_analysis
            )
            analysis_results['confidence_boosters'] = boosters
            
            # Remove duplicates from search terms
            analysis_results['enhanced_search_terms'] = list(set(
                analysis_results['enhanced_search_terms']
            ))
            
            self.logger.info(
                f"Customer analysis completed",
                extra={
                    'extra_fields': {
                        'enhanced_terms_count': len(analysis_results['enhanced_search_terms']),
                        'business_ids_found': len(business_ids),
                        'industry_matches': len(industry_info)
                    }
                }
            )
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Customer analysis failed: {e}", exc_info=True)
            # Return original info with minimal enhancement
            analysis_results['enhanced_search_terms'] = customer_info.get('search_terms', [])
            return analysis_results
    
    async def _extract_company_names(self, customer_info: Dict[str, Any]) -> List[str]:
        """Extract and normalize company names from various sources."""
        company_names = []
        
        # From direct search terms
        search_terms = customer_info.get('search_terms', [])
        for term in search_terms:
            if len(term) > 2:  # Skip very short terms
                company_names.append(term)
        
        # From email domain
        email_address = customer_info.get('email_address', '')
        if email_address and '@' in email_address:
            domain = email_address.split('@')[1]
            domain_parts = domain.split('.')
            
            # Extract potential company name from domain
            if len(domain_parts) > 1:
                potential_name = domain_parts[0]
                if len(potential_name) > 3:
                    company_names.append(potential_name.title())
        
        # From company indicators
        company_indicators = customer_info.get('company_indicators', [])
        company_names.extend(company_indicators)
        
        # Clean and deduplicate
        cleaned_names = []
        for name in company_names:
            cleaned = self._clean_company_name(name)
            if cleaned and len(cleaned) > 2:
                cleaned_names.append(cleaned)
        
        return list(set(cleaned_names))
    
    def _clean_company_name(self, name: str) -> str:
        """Clean and normalize company name."""
        if not name:
            return ""
        
        # Remove common prefixes and suffixes
        cleaned = name.strip()
        
        # Remove email-like patterns
        cleaned = re.sub(r'[@\.]', ' ', cleaned)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Capitalize properly
        if cleaned.islower() or cleaned.isupper():
            cleaned = cleaned.title()
        
        return cleaned
    
    async def _generate_name_variations(self, company_names: List[str]) -> List[str]:
        """Generate variations of company names for better matching."""
        variations = []
        
        for name in company_names:
            # Remove company form suffixes
            base_name = name
            for form in self.finnish_company_variations:
                pattern = rf'\s*{re.escape(form)}\s*$'
                base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE).strip()
            
            if base_name and base_name != name:
                variations.append(base_name)
            
            # Add variations with different company forms
            for form in ['Oy', 'Ltd', 'AB']:
                if form.lower() not in name.lower():
                    variations.append(f"{base_name} {form}")
            
            # Generate acronyms for multi-word names
            words = base_name.split()
            if len(words) > 1:
                acronym = ''.join(word[0].upper() for word in words if word)
                if len(acronym) > 1:
                    variations.append(acronym)
            
            # Remove common words and generate shorter versions
            common_words = ['company', 'corporation', 'group', 'international', 'global']
            filtered_words = [w for w in words if w.lower() not in common_words]
            if len(filtered_words) < len(words) and filtered_words:
                variations.append(' '.join(filtered_words))
        
        return list(set(variations))
    
    async def _extract_business_identifiers(self, customer_info: Dict[str, Any]) -> Dict[str, str]:
        """Extract Finnish business identifiers from customer information."""
        identifiers = {}
        
        # Combine all text sources
        text_sources = [
            customer_info.get('email_content', ''),
            ' '.join(customer_info.get('search_terms', [])),
            ' '.join(customer_info.get('company_indicators', [])),
        ]
        
        combined_text = ' '.join(text_sources)
        
        # Extract Y-tunnus (Finnish business ID)
        y_tunnus_matches = self.finnish_business_patterns['y_tunnus'].findall(combined_text)
        if y_tunnus_matches:
            identifiers['y_tunnus'] = y_tunnus_matches[0]
        
        # Extract VAT number
        vat_matches = self.finnish_business_patterns['vat_number'].findall(combined_text)
        if vat_matches:
            identifiers['vat_number'] = vat_matches[0]
        
        # Extract company form
        form_matches = self.finnish_business_patterns['company_forms'].findall(combined_text)
        if form_matches:
            identifiers['company_form'] = form_matches[0]
        
        return identifiers
    
    async def _analyze_contact_patterns(self, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze contact information patterns."""
        patterns = {
            'email_domain': '',
            'email_structure': '',
            'phone_country': '',
            'domain_age_estimate': '',
            'professional_email': False
        }
        
        # Analyze email
        email_address = customer_info.get('email_address', '')
        if email_address and '@' in email_address:
            local_part, domain = email_address.split('@', 1)
            patterns['email_domain'] = domain
            
            # Analyze email structure
            if '.' in local_part:
                if len(local_part.split('.')) == 2:
                    patterns['email_structure'] = 'firstname.lastname'
                else:
                    patterns['email_structure'] = 'complex'
            elif any(char.isdigit() for char in local_part):
                patterns['email_structure'] = 'name_with_numbers'
            else:
                patterns['email_structure'] = 'simple_name'
            
            # Check if it's a professional email
            patterns['professional_email'] = not any(
                domain.endswith(public_domain) 
                for public_domain in ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
            )
        
        # Analyze phone patterns (if available)
        phone_info = customer_info.get('phone_number', '')
        if phone_info:
            if phone_info.startswith('+358') or phone_info.startswith('0'):
                patterns['phone_country'] = 'finland'
            elif phone_info.startswith('+'):
                patterns['phone_country'] = 'international'
            else:
                patterns['phone_country'] = 'unknown'
        
        return patterns
    
    async def _classify_industry(self, customer_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Classify customer industry based on keywords and patterns."""
        industry_matches = []
        
        # Combine text for analysis
        text_sources = [
            customer_info.get('email_content', ''),
            ' '.join(customer_info.get('search_terms', [])),
            ' '.join(customer_info.get('company_indicators', [])),
        ]
        
        combined_text = ' '.join(text_sources).lower()
        
        # Check each industry category
        for industry, keywords in self.industry_keywords.items():
            matches = []
            confidence = 0.0
            
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matches.append(keyword)
                    confidence += 1.0
            
            if matches:
                # Normalize confidence
                confidence = min(confidence / len(keywords), 1.0)
                
                industry_matches.append({
                    'industry': industry,
                    'confidence': confidence,
                    'matched_keywords': matches,
                    'keyword_count': len(matches)
                })
        
        # Sort by confidence
        industry_matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return industry_matches[:3]  # Return top 3 matches
    
    async def _create_customer_signature(
        self, 
        company_names: List[str], 
        customer_info: Dict[str, Any],
        business_ids: Dict[str, str],
        contact_patterns: Dict[str, Any]
    ) -> CustomerSignature:
        """Create unique customer signature for matching."""
        
        # Company name variants
        name_variants = set(company_names)
        
        # Email domains
        email_domains = set()
        if contact_patterns.get('email_domain'):
            email_domains.add(contact_patterns['email_domain'])
        
        # Phone patterns
        phone_patterns = set()
        if contact_patterns.get('phone_country'):
            phone_patterns.add(contact_patterns['phone_country'])
        
        # Address components (if available)
        address_components = set()
        # This would be populated from address parsing if available
        
        # Business identifiers
        business_identifiers = set(business_ids.values())
        
        # Industry keywords
        industry_keywords = set()
        # Extract from email content and other sources
        
        return CustomerSignature(
            company_name_variants=name_variants,
            email_domains=email_domains,
            phone_patterns=phone_patterns,
            address_components=address_components,
            business_identifiers=business_identifiers,
            industry_keywords=industry_keywords
        )
    
    async def _calculate_confidence_boosters(
        self,
        customer_info: Dict[str, Any],
        business_ids: Dict[str, str],
        contact_patterns: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence boosters for customer matching."""
        boosters = {}
        
        # Business ID boost
        if business_ids.get('y_tunnus'):
            boosters['finnish_business_id'] = 0.4
        if business_ids.get('vat_number'):
            boosters['vat_number'] = 0.3
        
        # Professional email boost
        if contact_patterns.get('professional_email'):
            boosters['professional_email'] = 0.2
        
        # Company form boost
        if business_ids.get('company_form'):
            boosters['company_form'] = 0.1
        
        # Email structure boost
        email_structure = contact_patterns.get('email_structure', '')
        if email_structure in ['firstname.lastname', 'name_with_numbers']:
            boosters['structured_email'] = 0.1
        
        return boosters
    
    def compare_signatures(self, sig1: CustomerSignature, sig2: CustomerSignature) -> float:
        """
        Compare two customer signatures and return similarity score.
        
        Args:
            sig1: First customer signature
            sig2: Second customer signature
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        scores = []
        
        # Compare company name variants
        name_intersection = sig1.company_name_variants.intersection(sig2.company_name_variants)
        name_union = sig1.company_name_variants.union(sig2.company_name_variants)
        if name_union:
            scores.append(len(name_intersection) / len(name_union))
        
        # Compare email domains
        domain_intersection = sig1.email_domains.intersection(sig2.email_domains)
        domain_union = sig1.email_domains.union(sig2.email_domains)
        if domain_union:
            scores.append(len(domain_intersection) / len(domain_union))
        
        # Compare business identifiers (high weight)
        business_intersection = sig1.business_identifiers.intersection(sig2.business_identifiers)
        business_union = sig1.business_identifiers.union(sig2.business_identifiers)
        if business_union:
            business_score = len(business_intersection) / len(business_union)
            scores.extend([business_score] * 3)  # Give higher weight
        
        # Return average score or 0 if no comparable elements
        return sum(scores) / len(scores) if scores else 0.0 