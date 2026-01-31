"""
Lemonsoft Person Adapter

Implements the PersonRepository interface for Lemonsoft ERP.
Handles salesperson/person lookup operations.
"""
from typing import Optional, List

from src.erp.base.person_repository import PersonRepository
from src.domain.person import Person
from src.erp.lemonsoft.field_mapper import LemonsoftFieldMapper
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class LemonsoftPersonAdapter(PersonRepository):
    """
    Lemonsoft implementation of the PersonRepository interface.

    This adapter handles person/salesperson lookup in Lemonsoft ERP.
    """

    def __init__(self):
        """Initialize the Lemonsoft person adapter."""
        self.logger = get_logger(__name__)
        self.client = LemonsoftAPIClient()
        self.mapper = LemonsoftFieldMapper()

    async def find_by_email(self, email: str) -> Optional[Person]:
        """
        Find person/salesperson by email address.

        Args:
            email: Email address to search for

        Returns:
            Person object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Looking up person by email: {email}")

            # Extract just the username part before @ for search
            # (Lemonsoft search often works better with username only)
            search_email = email.split('@')[0]

            async with self.client as client:
                await client.ensure_ready()

                # Search persons API
                response = await client.get(
                    '/api/persons',
                    params={'filter.search': search_email}
                )

                if response.status_code != 200:
                    self.logger.warning(f"Person search failed: {response.status_code}")
                    return None

                data = response.json()

                # Extract persons from response
                persons = self._extract_persons_from_response(data)

                if not persons:
                    self.logger.info(f"No person found with email: {email}")
                    return None

                # Find the best match (exact email match if possible)
                person_data = self._find_best_email_match(persons, email)

                if not person_data:
                    # If no exact match, take the first result
                    person_data = persons[0]

                # Map to generic Person model
                person = self.mapper.to_person(person_data)

                self.logger.info(f"Found person: {person.name} (number: {person.number})")
                return person

        except Exception as e:
            self.logger.error(f"Error finding person by email '{email}': {e}")
            raise ExternalServiceError(f"Failed to find person: {e}")

    async def find_by_number(self, person_number: str) -> Optional[Person]:
        """
        Find person by person number.

        Args:
            person_number: Person number/ID to search for

        Returns:
            Person object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Looking up person by number: {person_number}")

            async with self.client as client:
                await client.ensure_ready()

                # Search persons API by number
                response = await client.get(
                    '/api/persons',
                    params={'filter.number': person_number}
                )

                if response.status_code != 200:
                    self.logger.warning(f"Person search failed: {response.status_code}")
                    return None

                data = response.json()

                # Extract persons from response
                persons = self._extract_persons_from_response(data)

                if not persons:
                    self.logger.info(f"No person found with number: {person_number}")
                    return None

                # Take the first matching person
                person_data = persons[0]

                # Map to generic Person model
                person = self.mapper.to_person(person_data)

                self.logger.info(f"Found person: {person.name} (number: {person.number})")
                return person

        except Exception as e:
            self.logger.error(f"Error finding person by number '{person_number}': {e}")
            raise ExternalServiceError(f"Failed to find person: {e}")

    async def search(self, query: str, limit: int = 10) -> List[Person]:
        """
        Search for persons by query string.

        Args:
            query: Search query (can be name, email, number, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Person objects

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Searching persons with query: {query}, limit: {limit}")

            persons = []

            async with self.client as client:
                await client.ensure_ready()

                response = await client.get(
                    '/api/persons',
                    params={'filter.search': query}
                )

                if response.status_code != 200:
                    self.logger.warning(f"Person search failed: {response.status_code}")
                    return []

                data = response.json()

                # Extract persons from response
                person_list = self._extract_persons_from_response(data)

                # Map to generic Person models
                for person_data in person_list[:limit]:
                    person = self.mapper.to_person(person_data)
                    persons.append(person)

            self.logger.info(f"Found {len(persons)} persons matching '{query}'")
            return persons

        except Exception as e:
            self.logger.error(f"Error searching persons with query '{query}': {e}")
            raise ExternalServiceError(f"Failed to search persons: {e}")

    # ==================== HELPER METHODS ====================

    def _extract_persons_from_response(self, data) -> List[dict]:
        """
        Extract person list from Lemonsoft API response.

        Args:
            data: API response data

        Returns:
            List of person dictionaries
        """
        persons = []

        if isinstance(data, list):
            persons = data
        elif isinstance(data, dict):
            # Try various possible keys
            persons = data.get('results', data.get('data', data.get('persons', [])))

            # If still not a list, check if it's a single person
            if not isinstance(persons, list):
                if 'number' in data or 'id' in data:
                    persons = [data]
                else:
                    persons = []

        return persons

    def _find_best_email_match(self, persons: List[dict], email: str) -> Optional[dict]:
        """
        Find the best email match from a list of persons.

        Args:
            persons: List of person dictionaries
            email: Email to match

        Returns:
            Best matching person dictionary or None
        """
        email_lower = email.lower()

        for person in persons:
            person_email = person.get('email', '').lower()
            if person_email == email_lower:
                return person

        # No exact match
        return None
