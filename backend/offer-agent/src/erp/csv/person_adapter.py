"""
CSV Person Adapter

Implements the PersonRepository interface for CSV-based person data.
"""
from typing import Optional, List
import pandas as pd
from pathlib import Path

from src.erp.base.person_repository import PersonRepository
from src.domain.person import Person
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class CSVPersonAdapter(PersonRepository):
    """CSV implementation of the PersonRepository interface."""

    def __init__(self, csv_file_path: Optional[str] = None):
        """Initialize the CSV person adapter."""
        self.logger = get_logger(__name__)

        if csv_file_path is None:
            current_dir = Path(__file__).parent
            csv_file_path = current_dir / 'data' / 'persons.csv'

        self.csv_file_path = str(csv_file_path)
        self._persons_df: Optional[pd.DataFrame] = None

        self.logger.info(f"CSV Person Adapter initialized with file: {self.csv_file_path}")

    def _load_persons(self) -> pd.DataFrame:
        """Load persons from CSV file."""
        if self._persons_df is not None:
            return self._persons_df

        try:
            self._persons_df = pd.read_csv(
                self.csv_file_path,
                sep=';',
                dtype=str,
                keep_default_na=False
            )
            self.logger.info(f"Loaded {len(self._persons_df)} persons from CSV")
            return self._persons_df
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise ExternalServiceError(f"Failed to load person data from CSV: {e}")

    async def find_by_email(self, email: str) -> Optional[Person]:
        """Find person by email address."""
        try:
            df = self._load_persons()
            matches = df[df['email'].str.strip().str.lower() == email.strip().lower()]

            if matches.empty:
                return None

            row = matches.iloc[0]
            return Person(
                id=row['number'],
                number=row['number'],
                name=row['name'],
                email=row['email'],
                phone=row.get('phone', ''),
                role=row.get('role', 'Sales'),
                active=row.get('active', 'true').lower() == 'true',
            )
        except Exception as e:
            self.logger.error(f"Error finding person by email: {e}")
            raise ExternalServiceError(f"Failed to find person: {e}")

    async def find_by_number(self, person_number: str) -> Optional[Person]:
        """Find person by person number (alias for get_by_number)."""
        return await self.get_by_number(person_number)

    async def search(self, query: str, limit: int = 10) -> List[Person]:
        """Search for persons by query string."""
        return await self.search_by_name(query, limit)

    async def get_by_number(self, person_number: str) -> Optional[Person]:
        """Get person by person number."""
        try:
            df = self._load_persons()
            matches = df[df['number'].str.strip() == str(person_number).strip()]

            if matches.empty:
                return None

            row = matches.iloc[0]
            return Person(
                id=row['number'],
                number=row['number'],
                name=row['name'],
                email=row.get('email', ''),
                phone=row.get('phone', ''),
                role=row.get('role', 'Sales'),
                active=row.get('active', 'true').lower() == 'true',
            )
        except Exception as e:
            self.logger.error(f"Error getting person by number: {e}")
            raise ExternalServiceError(f"Failed to get person: {e}")

    async def search_by_name(self, name: str, limit: int = 10) -> List[Person]:
        """Search persons by name."""
        try:
            df = self._load_persons()
            name_lower = name.lower()

            matches = df[df['name'].str.lower().str.contains(name_lower, na=False)]
            matches = matches.head(limit)

            persons = []
            for _, row in matches.iterrows():
                persons.append(Person(
                    id=row['number'],
                    number=row['number'],
                    name=row['name'],
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    role=row.get('role', 'Sales'),
                    active=row.get('active', 'true').lower() == 'true',
                ))

            return persons
        except Exception as e:
            self.logger.error(f"Error searching persons: {e}")
            raise ExternalServiceError(f"Failed to search persons: {e}")

    async def get_active_salespeople(self) -> List[Person]:
        """Get all active salespeople."""
        try:
            df = self._load_persons()
            active = df[df.get('active', 'true').str.lower() == 'true']

            persons = []
            for _, row in active.iterrows():
                persons.append(Person(
                    id=row['number'],
                    number=row['number'],
                    name=row['name'],
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    role=row.get('role', 'Sales'),
                    active=True,
                ))

            return persons
        except Exception as e:
            self.logger.error(f"Error getting salespeople: {e}")
            raise ExternalServiceError(f"Failed to get salespeople: {e}")
