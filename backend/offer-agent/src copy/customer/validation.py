"""
Customer validation system with comprehensive data quality checks.
Validates customer matches and provides confidence scoring.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from customer.lookup import CustomerMatch
from customer.analyzer import CustomerDataAnalyzer, CustomerSignature
from lemonsoft.api_client import LemonsoftAPIClient
from utils.logger import get_logger
from utils.exceptions import CustomerValidationError


@dataclass
class ValidationResult:
    """Results of customer validation checks."""
    is_valid: bool
    confidence_score: float
    validation_checks: Dict[str, bool]
    warnings: List[str]
    errors: List[str]
    validation_details: Dict[str, Any]


class CustomerValidator:
    """Comprehensive customer validation with multiple verification layers."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.analyzer = CustomerDataAnalyzer()
        self.api_client = LemonsoftAPIClient()
        
        # Validation thresholds
        self.min_confidence_score = 0.6
        self.high_confidence_threshold = 0.8
        
        # Validation weights
        self.validation_weights = {
            'basic_info_complete': 0.1,
            'contact_info_valid': 0.15,
            'business_id_valid': 0.25,
            'name_match_quality': 0.2,
            'domain_consistency': 0.15,
            'customer_status_active': 0.15
        }
    
    async def validate_customer_match(
        self, 
        customer_match: CustomerMatch, 
        original_customer_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Perform comprehensive validation of a customer match.
        
        Args:
            customer_match: Customer match to validate
            original_customer_info: Original customer information from email
            
        Returns:
            Validation result with confidence scoring
        """
        self.logger.debug(f"Validating customer match: {customer_match.customer_name}")
        
        validation_checks = {}
        warnings = []
        errors = []
        validation_details = {}
        
        try:
            # Basic information completeness check
            basic_check = await self._check_basic_info_completeness(customer_match)
            validation_checks['basic_info_complete'] = basic_check['is_valid']
            validation_details['basic_info'] = basic_check
            
            # Contact information validation
            contact_check = await self._validate_contact_information(customer_match)
            validation_checks['contact_info_valid'] = contact_check['is_valid']
            validation_details['contact_info'] = contact_check
            warnings.extend(contact_check.get('warnings', []))
            
            # Business identifier validation
            business_check = await self._validate_business_identifiers(
                customer_match, original_customer_info
            )
            validation_checks['business_id_valid'] = business_check['is_valid']
            validation_details['business_id'] = business_check
            
            # Name match quality assessment
            name_check = await self._assess_name_match_quality(
                customer_match, original_customer_info
            )
            validation_checks['name_match_quality'] = name_check['is_valid']
            validation_details['name_match'] = name_check
            
            # Domain consistency check
            domain_check = await self._check_domain_consistency(
                customer_match, original_customer_info
            )
            validation_checks['domain_consistency'] = domain_check['is_valid']
            validation_details['domain_consistency'] = domain_check
            warnings.extend(domain_check.get('warnings', []))
            
            # Customer status verification
            status_check = await self._verify_customer_status(customer_match)
            validation_checks['customer_status_active'] = status_check['is_valid']
            validation_details['customer_status'] = status_check
            if not status_check['is_valid']:
                errors.append(f"Customer {customer_match.customer_id} is not active")
            
            # Calculate overall confidence score
            confidence_score = self._calculate_validation_confidence(
                validation_checks, customer_match.confidence_score
            )
            
            # Determine overall validity
            is_valid = (
                confidence_score >= self.min_confidence_score and
                validation_checks.get('customer_status_active', False)
            )
            
            # Add warnings for low confidence
            if confidence_score < self.high_confidence_threshold:
                warnings.append(f"Match confidence below high threshold: {confidence_score:.2f}")
            
            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                validation_checks=validation_checks,
                warnings=warnings,
                errors=errors,
                validation_details=validation_details
            )
            
            self.logger.info(
                f"Customer validation completed",
                extra={
                    'extra_fields': {
                        'customer_id': customer_match.customer_id,
                        'customer_name': customer_match.customer_name,
                        'is_valid': is_valid,
                        'confidence_score': confidence_score,
                        'checks_passed': sum(validation_checks.values()),
                        'total_checks': len(validation_checks)
                    }
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Customer validation failed: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_checks=validation_checks,
                warnings=warnings,
                errors=errors,
                validation_details=validation_details
            )
    
    async def _check_basic_info_completeness(self, customer_match: CustomerMatch) -> Dict[str, Any]:
        """Check if basic customer information is complete."""
        result = {
            'is_valid': True,
            'completeness_score': 0.0,
            'missing_fields': [],
            'present_fields': []
        }
        
        # Required fields and their importance
        required_fields = {
            'customer_id': 1.0,
            'customer_name': 1.0,
            'email': 0.7,
            'phone': 0.5,
            'address': 0.3
        }
        
        total_weight = sum(required_fields.values())
        present_weight = 0.0
        
        for field, weight in required_fields.items():
            value = getattr(customer_match, field, None)
            if value and str(value).strip():
                result['present_fields'].append(field)
                present_weight += weight
            else:
                result['missing_fields'].append(field)
        
        result['completeness_score'] = present_weight / total_weight
        result['is_valid'] = result['completeness_score'] >= 0.6  # 60% completeness required
        
        return result
    
    async def _validate_contact_information(self, customer_match: CustomerMatch) -> Dict[str, Any]:
        """Validate contact information format and consistency."""
        result = {
            'is_valid': True,
            'email_valid': True,
            'phone_valid': True,
            'warnings': []
        }
        
        # Email validation
        if customer_match.email:
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(customer_match.email):
                result['email_valid'] = False
                result['warnings'].append("Invalid email format")
        
        # Phone validation (Finnish format)
        if customer_match.phone:
            # Remove common formatting
            phone_clean = re.sub(r'[\s\-\(\)]', '', customer_match.phone)
            
            # Check Finnish phone patterns
            finnish_patterns = [
                re.compile(r'^\+358\d{6,10}$'),  # +358 prefix
                re.compile(r'^0\d{6,9}$'),       # 0 prefix
                re.compile(r'^\d{6,10}$')        # No prefix
            ]
            
            phone_valid = any(pattern.match(phone_clean) for pattern in finnish_patterns)
            if not phone_valid:
                result['phone_valid'] = False
                result['warnings'].append("Phone number format may be invalid")
        
        result['is_valid'] = result['email_valid'] and result['phone_valid']
        
        return result
    
    async def _validate_business_identifiers(
        self, 
        customer_match: CustomerMatch, 
        original_customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate Finnish business identifiers if available."""
        result = {
            'is_valid': True,
            'y_tunnus_valid': None,
            'vat_number_valid': None,
            'identifiers_found': []
        }
        
        # Look for business identifiers in match details
        match_details = customer_match.match_details or {}
        
        # Check for Y-tunnus (Finnish business ID)
        y_tunnus = None
        if 'y_tunnus' in match_details:
            y_tunnus = match_details['y_tunnus']
        
        if y_tunnus:
            result['y_tunnus_valid'] = self._validate_y_tunnus(y_tunnus)
            result['identifiers_found'].append('y_tunnus')
            if not result['y_tunnus_valid']:
                result['is_valid'] = False
        
        # Check for VAT number
        vat_number = None
        if 'vat_number' in match_details:
            vat_number = match_details['vat_number']
        
        if vat_number:
            result['vat_number_valid'] = self._validate_finnish_vat(vat_number)
            result['identifiers_found'].append('vat_number')
            if not result['vat_number_valid']:
                result['is_valid'] = False
        
        return result
    
    def _validate_y_tunnus(self, y_tunnus: str) -> bool:
        """Validate Finnish business ID (Y-tunnus) format and checksum."""
        if not y_tunnus or len(y_tunnus) != 9 or y_tunnus[7] != '-':
            return False
        
        try:
            # Extract numbers
            business_number = y_tunnus[:7]
            check_digit = int(y_tunnus[8])
            
            # Calculate checksum
            multipliers = [7, 9, 10, 5, 8, 4, 2]
            total = sum(int(digit) * mult for digit, mult in zip(business_number, multipliers))
            
            remainder = total % 11
            if remainder == 0:
                expected_check = 0
            elif remainder == 1:
                return False  # Invalid
            else:
                expected_check = 11 - remainder
            
            return check_digit == expected_check
            
        except (ValueError, IndexError):
            return False
    
    def _validate_finnish_vat(self, vat_number: str) -> bool:
        """Validate Finnish VAT number format."""
        if not vat_number or not vat_number.startswith('FI'):
            return False
        
        # Remove FI prefix and validate length
        vat_digits = vat_number[2:]
        if len(vat_digits) != 8:
            return False
        
        try:
            # All should be digits
            int(vat_digits)
            return True
        except ValueError:
            return False
    
    async def _assess_name_match_quality(
        self, 
        customer_match: CustomerMatch, 
        original_customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality of name matching."""
        result = {
            'is_valid': True,
            'match_quality_score': 0.0,
            'match_type': 'unknown',
            'name_variations_checked': []
        }
        
        search_terms = original_customer_info.get('search_terms', [])
        customer_name = customer_match.customer_name.lower()
        
        if not search_terms:
            result['match_quality_score'] = 0.5  # Neutral score
            result['match_type'] = 'no_search_terms'
            return result
        
        best_score = 0.0
        best_match_type = 'none'
        
        for term in search_terms:
            term_lower = term.lower()
            
            # Exact match
            if term_lower == customer_name:
                best_score = 1.0
                best_match_type = 'exact'
                break
            
            # Substring match
            if term_lower in customer_name or customer_name in term_lower:
                score = min(len(term_lower), len(customer_name)) / max(len(term_lower), len(customer_name))
                if score > best_score:
                    best_score = score
                    best_match_type = 'substring'
            
            # Word overlap
            term_words = set(term_lower.split())
            name_words = set(customer_name.split())
            overlap = len(term_words.intersection(name_words))
            if overlap > 0:
                score = overlap / max(len(term_words), len(name_words))
                if score > best_score:
                    best_score = score
                    best_match_type = 'word_overlap'
        
        result['match_quality_score'] = best_score
        result['match_type'] = best_match_type
        result['is_valid'] = best_score >= 0.3  # Minimum 30% similarity
        
        return result
    
    async def _check_domain_consistency(
        self, 
        customer_match: CustomerMatch, 
        original_customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check consistency between customer email domain and contact email."""
        result = {
            'is_valid': True,
            'domain_match': False,
            'domain_similarity': 0.0,
            'warnings': []
        }
        
        customer_email = customer_match.email
        original_email = original_customer_info.get('email_address', '')
        
        if not customer_email or not original_email:
            result['domain_similarity'] = 0.5  # Neutral score when data missing
            return result
        
        try:
            customer_domain = customer_email.split('@')[1].lower()
            original_domain = original_email.split('@')[1].lower()
            
            if customer_domain == original_domain:
                result['domain_match'] = True
                result['domain_similarity'] = 1.0
            else:
                # Check for subdomain relationships
                if customer_domain in original_domain or original_domain in customer_domain:
                    result['domain_similarity'] = 0.8
                    result['warnings'].append("Domains are related but not identical")
                else:
                    result['domain_similarity'] = 0.0
                    result['warnings'].append("Email domains do not match")
        
        except (IndexError, AttributeError):
            result['warnings'].append("Invalid email format preventing domain comparison")
            result['domain_similarity'] = 0.0
        
        return result
    
    async def _verify_customer_status(self, customer_match: CustomerMatch) -> Dict[str, Any]:
        """Verify customer status in Lemonsoft system."""
        result = {
            'is_valid': True,
            'is_active': True,
            'last_activity': None,
            'status_details': {}
        }
        
        try:
            # Get current customer data from Lemonsoft
            customer_data = await self.api_client.get_customer(customer_match.customer_id)
            
            if not customer_data:
                result['is_valid'] = False
                result['is_active'] = False
                result['status_details']['error'] = 'Customer not found in system'
                return result
            
            # Check active status
            is_active = customer_data.get('active', True)
            result['is_active'] = is_active
            result['is_valid'] = is_active
            
            # Extract status details
            result['status_details'] = {
                'customer_type': customer_data.get('type', 'unknown'),
                'created_date': customer_data.get('created_date'),
                'last_modified': customer_data.get('last_modified'),
                'payment_terms': customer_data.get('payment_terms'),
                'credit_limit': customer_data.get('credit_limit')
            }
            
            # Check last activity
            last_order_date = customer_data.get('last_order_date')
            if last_order_date:
                result['last_activity'] = last_order_date
            
        except Exception as e:
            self.logger.warning(f"Could not verify customer status: {e}")
            result['status_details']['verification_error'] = str(e)
            # Don't fail validation if we can't verify - system might be temporarily unavailable
        
        return result
    
    def _calculate_validation_confidence(
        self, 
        validation_checks: Dict[str, bool], 
        original_confidence: float
    ) -> float:
        """Calculate overall validation confidence score."""
        
        # Calculate weighted validation score
        validation_score = 0.0
        total_weight = 0.0
        
        for check_name, passed in validation_checks.items():
            weight = self.validation_weights.get(check_name, 0.1)
            if passed:
                validation_score += weight
            total_weight += weight
        
        # Normalize validation score
        if total_weight > 0:
            validation_score = validation_score / total_weight
        else:
            validation_score = 0.5  # Neutral if no weights defined
        
        # Combine with original match confidence (70% validation, 30% original)
        combined_confidence = (validation_score * 0.7) + (original_confidence * 0.3)
        
        return min(combined_confidence, 1.0)
    
    async def batch_validate_customers(
        self, 
        customer_matches: List[CustomerMatch], 
        original_customer_info: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate multiple customer matches in batch."""
        self.logger.info(f"Batch validating {len(customer_matches)} customer matches")
        
        validation_tasks = [
            self.validate_customer_match(match, original_customer_info)
            for match in customer_matches
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Validation failed for match {i}: {result}")
                # Create failed validation result
                failed_result = ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    validation_checks={},
                    warnings=[],
                    errors=[f"Validation exception: {str(result)}"],
                    validation_details={}
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)
        
        return valid_results 