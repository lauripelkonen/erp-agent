"""
CSV Product Adapter

Implements the ProductRepository interface for CSV-based product data.
Handles product catalog access and search operations from CSV files.
"""
from typing import Optional, List, Dict, Any
import os
import pandas as pd
from pathlib import Path

from src.erp.base.product_repository import ProductRepository
from src.domain.product import Product
from src.erp.csv.field_mapper import CSVFieldMapper
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class CSVProductAdapter(ProductRepository):
    """
    CSV implementation of the ProductRepository interface.

    This adapter handles product catalog operations from a CSV file.
    """

    def __init__(self, csv_file_path: Optional[str] = None):
        """
        Initialize the CSV product adapter.

        Args:
            csv_file_path: Path to the products CSV file.
                          Defaults to src/erp/csv/data/products.csv
        """
        self.logger = get_logger(__name__)
        self.mapper = CSVFieldMapper()

        # Set default CSV file path if not provided
        if csv_file_path is None:
            current_dir = Path(__file__).parent
            csv_file_path = current_dir / 'data' / 'products.csv'

        self.csv_file_path = str(csv_file_path)
        self._products_df: Optional[pd.DataFrame] = None

        self.logger.info(f"CSV Product Adapter initialized with file: {self.csv_file_path}")

    def _load_products(self) -> pd.DataFrame:
        """
        Load products from CSV file.

        Returns:
            DataFrame with product data

        Raises:
            ExternalServiceError: If CSV file cannot be loaded
        """
        if self._products_df is not None:
            return self._products_df

        try:
            if not os.path.exists(self.csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

            # Load CSV with semicolon separator
            self._products_df = pd.read_csv(
                self.csv_file_path,
                sep=';',
                dtype=str,  # Load all as strings initially
                keep_default_na=False  # Keep empty strings as empty, not NaN
            )

            # Convert numeric columns
            numeric_columns = ['Paksuus', 'Yksikkö paino', 'Eräkoko']
            for col in numeric_columns:
                if col in self._products_df.columns:
                    self._products_df[col] = pd.to_numeric(
                        self._products_df[col],
                        errors='coerce'
                    ).fillna(0)

            self.logger.info(f"Loaded {len(self._products_df)} products from CSV")
            return self._products_df

        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise ExternalServiceError(f"Failed to load product data from CSV: {e}")

    def _csv_row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert pandas Series to dictionary.

        Args:
            row: Pandas Series representing a CSV row

        Returns:
            Dictionary with row data
        """
        return row.to_dict()

    async def get_by_code(self, product_code: str) -> Optional[Product]:
        """
        Get product by product code/SKU.

        Args:
            product_code: Product code to search for

        Returns:
            Product object if found, None otherwise

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        try:
            self.logger.info(f"Looking up product by code: {product_code}")

            df = self._load_products()

            # Search for exact product code match (case-insensitive)
            product_code_clean = str(product_code).strip()
            matches = df[df['Tuotekoodi'].str.strip().str.lower() == product_code_clean.lower()]

            if matches.empty:
                self.logger.info(f"Product not found: {product_code}")
                return None

            # Get first match
            csv_data = self._csv_row_to_dict(matches.iloc[0])
            product = self.mapper.to_product(csv_data)

            self.logger.info(f"Found product: {product.name} (code: {product.code})")
            return product

        except Exception as e:
            self.logger.error(f"Error finding product by code '{product_code}': {e}")
            raise ExternalServiceError(f"Failed to find product: {e}")

    async def search(self, query: str, limit: int = 10) -> List[Product]:
        """
        Search for products by query string.

        Args:
            query: Search query (product code, name, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching Product objects

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        try:
            self.logger.info(f"Searching products with query: {query}, limit: {limit}")

            df = self._load_products()

            # Search across ALL columns dynamically (case-insensitive)
            query_lower = str(query).lower().strip()
            all_columns = list(df.columns)

            # Create search mask across ALL columns
            mask = pd.Series([False] * len(df))

            for col in all_columns:
                mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False, regex=False)

            matches = df[mask].head(limit)

            # Convert to Product objects
            products = []
            for _, row in matches.iterrows():
                csv_data = self._csv_row_to_dict(row)
                product = self.mapper.to_product(csv_data)
                products.append(product)

            self.logger.info(f"Found {len(products)} products matching '{query}'")
            return products

        except Exception as e:
            self.logger.error(f"Error searching products with query '{query}': {e}")
            raise ExternalServiceError(f"Failed to search products: {e}")

    async def get_product_group_products(self, product_group: str) -> List[Product]:
        """
        Get all products in a product group.

        Args:
            product_group: Product group identifier

        Returns:
            List of Product objects in the group

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        try:
            self.logger.info(f"Fetching products in group: {product_group}")

            df = self._load_products()

            # Filter by product group
            product_group_clean = str(product_group).strip()
            matches = df[df['Tuoteryhmä'].str.strip() == product_group_clean]

            # Convert to Product objects
            products = []
            for _, row in matches.iterrows():
                csv_data = self._csv_row_to_dict(row)
                product = self.mapper.to_product(csv_data)
                products.append(product)

            self.logger.info(f"Found {len(products)} products in group '{product_group}'")
            return products

        except Exception as e:
            self.logger.error(f"Error fetching products in group '{product_group}': {e}")
            raise ExternalServiceError(f"Failed to get product group products: {e}")

    async def check_availability(self, product_code: str, quantity: float) -> bool:
        """
        Check if product is available in requested quantity.

        Note: CSV doesn't have stock information, so this always returns True
        if the product exists.

        Args:
            product_code: Product code to check
            quantity: Requested quantity

        Returns:
            True if product exists (CSV has no stock tracking)

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        try:
            self.logger.info(f"Checking availability for {product_code}, quantity: {quantity}")

            # Get product to check if it exists
            product = await self.get_by_code(product_code)

            if not product:
                self.logger.warning(f"Product not found: {product_code}")
                return False

            # CSV doesn't track stock, so assume available if product exists
            self.logger.info(f"Product {product_code} exists (no stock tracking in CSV)")
            return True

        except Exception as e:
            self.logger.error(f"Error checking availability for '{product_code}': {e}")
            raise ExternalServiceError(f"Failed to check product availability: {e}")

    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """
        Perform wildcard search on products using a search pattern.

        This implements CSV-specific product search by searching across
        ALL columns in the CSV file. Pattern parts separated by % are
        combined with AND logic - all parts must match somewhere in the row.

        For example: '%supistusmuhvi%316%' finds rows where 'supistusmuhvi'
        appears in ANY column AND '316' appears in ANY column (can be different columns).

        Args:
            pattern: Search pattern (can include wildcards with % separator)

        Returns:
            DataFrame with product search results formatted to show column:value pairs,
            None if no matches found.

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        try:
            self.logger.info(f"CSV wildcard search for pattern: '{pattern}'")

            df = self._load_products()

            # Get ALL columns from the CSV dynamically
            all_columns = list(df.columns)
            self.logger.info(f"Searching across {len(all_columns)} columns")

            # Parse the pattern - split by % and filter out empty strings
            pattern_clean = str(pattern).strip()
            search_terms = [term.strip().lower() for term in pattern_clean.split('%') if term.strip()]

            if not search_terms:
                self.logger.info(f"No valid search terms in pattern '{pattern}'")
                return None

            self.logger.info(f"Search terms (AND logic): {search_terms}")

            # For each row, check if ALL search terms appear somewhere across ANY column
            def row_matches_all_terms(row):
                """Check if all search terms are found somewhere in the row (across any columns)."""
                for term in search_terms:
                    term_found = False
                    for col in all_columns:
                        cell_value = str(row[col]).lower() if pd.notna(row[col]) else ''
                        if term in cell_value:
                            term_found = True
                            break
                    if not term_found:
                        return False
                return True

            # Apply the matching function
            mask = df.apply(row_matches_all_terms, axis=1)
            matches = df[mask]

            if matches.empty:
                self.logger.info(f"No products found for pattern '{pattern}' (terms: {search_terms})")
                return None

            self.logger.info(f"Found {len(matches)} products matching all terms: {search_terms}")

            # Convert to search result format with FULL column information for agent
            search_results = []
            for _, row in matches.iterrows():
                csv_data = self._csv_row_to_dict(row)

                # Classify priority based on product group
                group_code = 0
                try:
                    product_group = csv_data.get('Tuoteryhmä', '')
                    group_code = int(product_group) if product_group else 0
                except (ValueError, TypeError):
                    group_code = 0

                priority = self.mapper.classify_product_priority(group_code)

                # Build result with ALL columns visible to agent
                result = self.mapper.to_search_result(csv_data, priority)

                # Add formatted column:value string for agent visibility
                # Show which column contains which value
                column_values = []
                for col in all_columns:
                    val = str(csv_data.get(col, '')).strip()
                    if val:  # Only include non-empty values
                        column_values.append(f"{col}={val}")

                result['all_fields'] = ' | '.join(column_values)
                result['raw_csv_data'] = csv_data  # Full row data for debugging

                search_results.append(result)

            result_df = pd.DataFrame(search_results)
            self.logger.info(f"✅ Found {len(result_df)} products for pattern '{pattern}'")
            return result_df

        except Exception as e:
            self.logger.error(f"Wildcard search failed for pattern '{pattern}': {e}")
            raise ExternalServiceError(f"Failed to perform wildcard search: {e}")

    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        Search for products by exact product codes (batch lookup).

        This implements CSV-specific batch product lookup.

        Args:
            product_codes: List of product codes to search for

        Returns:
            DataFrame with product search results, None if no matches found.

        Raises:
            ExternalServiceError: If CSV file is unavailable
        """
        if not product_codes:
            self.logger.warning("No product codes provided for search")
            return None

        try:
            # Clean and prepare product codes
            clean_codes = [str(code).strip().lower() for code in product_codes if code]

            if not clean_codes:
                return None

            self.logger.info(
                f"CSV product code search - Searching for {len(clean_codes)} codes: {clean_codes}"
            )

            df = self._load_products()

            # Search for exact matches (case-insensitive)
            df['Tuotekoodi_lower'] = df['Tuotekoodi'].str.strip().str.lower()
            matches = df[df['Tuotekoodi_lower'].isin(clean_codes)]

            # Drop temporary column
            matches = matches.drop(columns=['Tuotekoodi_lower'])

            if matches.empty:
                self.logger.info(f"No products found for codes: {clean_codes}")
                return None

            # Convert to search result format
            search_results = []
            found_codes = []

            for _, row in matches.iterrows():
                csv_data = self._csv_row_to_dict(row)
                product_code = str(csv_data.get('Tuotekoodi', '')).strip()
                found_codes.append(product_code.lower())

                # Classify priority based on product group
                group_code = 0
                try:
                    product_group = csv_data.get('Tuoteryhmä', '')
                    group_code = int(product_group) if product_group else 0
                except (ValueError, TypeError):
                    group_code = 0

                priority = self.mapper.classify_product_priority(group_code)

                search_result = self.mapper.to_search_result(csv_data, priority)
                search_result['data_source'] = 'PRODUCT_CODE_SEARCH'
                search_results.append(search_result)

            # Log what was found
            missing_codes = set(clean_codes) - set(found_codes)
            if missing_codes:
                self.logger.warning(f"Product codes not found: {list(missing_codes)}")

            result_df = pd.DataFrame(search_results)
            self.logger.info(f"Found {len(result_df)} products out of {len(clean_codes)} requested codes")
            return result_df

        except Exception as e:
            self.logger.error(f"Product code search failed: {e}")
            raise ExternalServiceError(f"Failed to search by product codes: {e}")
