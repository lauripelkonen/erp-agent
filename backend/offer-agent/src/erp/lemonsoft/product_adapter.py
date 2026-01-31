"""
Lemonsoft Product Adapter

Implements the ProductRepository interface for Lemonsoft ERP.
Handles product catalog access and search operations.
"""
from typing import Optional, List, Dict, Any
import os
import re
import pandas as pd

from src.erp.base.product_repository import ProductRepository
from src.domain.product import Product
from src.erp.lemonsoft.field_mapper import LemonsoftFieldMapper
from src.lemonsoft.api_client import LemonsoftAPIClient
from src.lemonsoft.database_connection import create_database_client
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError


class LemonsoftProductAdapter(ProductRepository):
    """
    Lemonsoft implementation of the ProductRepository interface.

    This adapter handles product catalog operations in Lemonsoft ERP.
    """

    def __init__(self):
        """Initialize the Lemonsoft product adapter."""
        self.logger = get_logger(__name__)
        self.client = LemonsoftAPIClient()
        self.mapper = LemonsoftFieldMapper()

    async def get_by_code(self, product_code: str) -> Optional[Product]:
        """
        Get product by product code/SKU.

        Args:
            product_code: Product code to search for

        Returns:
            Product object if found, None otherwise

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Looking up product by code: {product_code}")

            async with self.client as client:
                await client.ensure_ready()

                # Use existing get_product method
                lemonsoft_product = await client.get_product(product_code)

                if not lemonsoft_product:
                    self.logger.info(f"Product not found: {product_code}")
                    return None

                # Convert LemonsoftProduct dataclass to dict for mapper
                product_data = {
                    'product_code': lemonsoft_product.product_code,
                    'product_name': lemonsoft_product.name,
                    'description': lemonsoft_product.description,
                    'unit': lemonsoft_product.unit,
                    'product_group': lemonsoft_product.product_group,
                    'product_exp_price': lemonsoft_product.unit_price,
                    'unit_price': lemonsoft_product.unit_price,
                    'stock_quantity': lemonsoft_product.available_quantity,
                    'active': True
                }

                # Map to generic Product model
                product = self.mapper.to_product(product_data)

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
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Searching products with query: {query}, limit: {limit}")

            products = []

            async with self.client as client:
                await client.ensure_ready()

                # Use existing search_products method
                lemonsoft_products = await client.search_products(
                    query=query,
                    limit=limit
                )

                # Convert each LemonsoftProduct to generic Product
                for lemonsoft_product in lemonsoft_products:
                    product_data = {
                        'product_code': lemonsoft_product.product_code,
                        'product_name': lemonsoft_product.name,
                        'description': lemonsoft_product.description,
                        'unit': lemonsoft_product.unit,
                        'product_group': lemonsoft_product.product_group,
                        'product_exp_price': lemonsoft_product.unit_price,
                        'unit_price': lemonsoft_product.unit_price,
                        'stock_quantity': lemonsoft_product.available_quantity,
                        'active': True
                    }

                    product = self.mapper.to_product(product_data)
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
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Fetching products in group: {product_group}")

            products = []

            async with self.client as client:
                await client.ensure_ready()

                # Use existing search_products with product_group filter
                lemonsoft_products = await client.search_products(
                    product_group=product_group,
                    limit=1000  # Get all products in group
                )

                # Convert each LemonsoftProduct to generic Product
                for lemonsoft_product in lemonsoft_products:
                    product_data = {
                        'product_code': lemonsoft_product.product_code,
                        'product_name': lemonsoft_product.name,
                        'description': lemonsoft_product.description,
                        'unit': lemonsoft_product.unit,
                        'product_group': lemonsoft_product.product_group,
                        'product_exp_price': lemonsoft_product.unit_price,
                        'unit_price': lemonsoft_product.unit_price,
                        'stock_quantity': lemonsoft_product.available_quantity,
                        'active': True
                    }

                    product = self.mapper.to_product(product_data)
                    products.append(product)

            self.logger.info(f"Found {len(products)} products in group '{product_group}'")
            return products

        except Exception as e:
            self.logger.error(f"Error fetching products in group '{product_group}': {e}")
            raise ExternalServiceError(f"Failed to get product group products: {e}")

    async def check_availability(self, product_code: str, quantity: float) -> bool:
        """
        Check if product is available in requested quantity.

        Args:
            product_code: Product code to check
            quantity: Requested quantity

        Returns:
            True if product is available in requested quantity

        Raises:
            ExternalServiceError: If Lemonsoft API is unavailable
        """
        try:
            self.logger.info(f"Checking availability for {product_code}, quantity: {quantity}")

            # Get product to check stock
            product = await self.get_by_code(product_code)

            if not product:
                self.logger.warning(f"Product not found: {product_code}")
                return False

            # Check if stock quantity is sufficient
            if product.stock_quantity is None:
                # If stock quantity not tracked, assume available
                self.logger.info(f"Stock not tracked for {product_code}, assuming available")
                return True

            available = product.stock_quantity >= quantity

            if available:
                self.logger.info(
                    f"Product {product_code} available: {product.stock_quantity} >= {quantity}"
                )
            else:
                self.logger.warning(
                    f"Product {product_code} NOT available: {product.stock_quantity} < {quantity}"
                )

            return available

        except Exception as e:
            self.logger.error(f"Error checking availability for '{product_code}': {e}")
            raise ExternalServiceError(f"Failed to check product availability: {e}")

    async def wildcard_search(self, pattern: str) -> Optional[pd.DataFrame]:
        """
        Perform wildcard search on products using a search pattern.

        This implements Lemonsoft-specific product search using SQL database queries.
        It searches across product codes, descriptions, and search codes.

        Args:
            pattern: Search pattern (can include wildcards, spaces, etc.)

        Returns:
            DataFrame with product search results, None if no matches found.

        Raises:
            ExternalServiceError: If database is unavailable
        """
        try:
            self.logger.info(f"🔍 Lemonsoft wildcard search for pattern: '{pattern}'")

            # Prepare search pattern for SQL LIKE
            sql_pattern = f"%{pattern}%"

            # Build WHERE clause for LIKE search across multiple fields
            where_clause = f"""
                p.product_code LIKE '{sql_pattern}'
                OR p.product_description LIKE '{sql_pattern}'
                OR p.product_description2 LIKE '{sql_pattern}'
                OR p.product_searchcode LIKE '{sql_pattern}'
            """

            # Complex SQL query with sales and stock data
            query = f"""
            WITH yearly_sales AS (
                SELECT
                    ir.invoicerow_productcode as product_code,
                    SUM(ir.invoicerow_amount) as total_sales_qty
                FROM invoicerows ir
                JOIN invoices i ON ir.invoice_id = i.invoice_id
                WHERE i.invoice_date >= DATEADD(year, -1, GETDATE())
                  AND ir.invoicerow_amount > 0
                GROUP BY ir.invoicerow_productcode
            ),
            total_stock AS (
                SELECT
                    p.product_code,
                    SUM(COALESCE(ps.stock_instock, 0)) as total_current_stock
                FROM products p
                LEFT JOIN product_stocks ps ON p.product_id = ps.product_id
                GROUP BY p.product_code
            )
            SELECT
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
                p.product_nonstock_bit,
                pd.product_group_code,
                COALESCE(p.product_price, 0) as price,
                pt.text_note as description,
                COALESCE(ts.total_current_stock, 0) as total_stock,
                COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
            FROM products p
            INNER JOIN product_dimensions pd ON p.product_id = pd.product_id
            LEFT JOIN product_texts pt ON p.product_id = pt.product_id
                AND pt.text_header_number = 3
                AND (pt.language_code IS NULL OR pt.language_code = '')
            LEFT JOIN total_stock ts ON p.product_code = ts.product_code
            LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
            WHERE
                ({where_clause})
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND (p.product_nonstock_bit IS NULL OR p.product_nonstock_bit = 0)
                AND pd.product_group_code != 0
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa
                    WHERE pa.product_id = p.product_id
                        AND pa.attribute_code IN (30)
                )
            ORDER BY p.product_code
            """

            # Execute SQL query
            results = await self._execute_sql_query(query)

            if not results:
                self.logger.info(f"❌ No products found for pattern '{pattern}'")
                return None

            # Convert results to DataFrame format expected by ProductMatcher
            search_results = []
            for row in results:
                # Handle both dict (direct DB) and tuple (Function App) responses
                if isinstance(row, dict):
                    group_code = int(row.get('product_group_code', 0)) if row.get('product_group_code') else 0
                    priority = self._classify_product_priority(group_code)

                    search_results.append({
                        'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                        'sku': str(row.get('product_code', '')) if row.get('product_code') else '',
                        'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                        'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                        'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                        'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                        'description': str(row.get('description', '')) if row.get('description') else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                        'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0,
                        'data_source': 'SQL_DATABASE'
                    })
                else:
                    # Legacy tuple handling for Function App
                    group_code = int(row[7]) if row[7] else 0
                    priority = self._classify_product_priority(group_code)

                    search_results.append({
                        'id': str(row[0]) if row[0] else '',
                        'sku': str(row[1]) if row[1] else '',
                        'name': str(row[2]) if row[2] else '',
                        'extra_name': str(row[3]) if row[3] else '',
                        'price': float(row[8]) if row[8] else 0.0,
                        'product_searchcode': str(row[4]) if row[4] else '',
                        'description': str(row[9]) if row[9] else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row[10]) if len(row) > 10 and row[10] else 0.0,
                        'yearly_sales_qty': float(row[11]) if len(row) > 11 and row[11] else 0.0,
                        'data_source': 'SQL_DATABASE'
                    })

            if search_results:
                df = pd.DataFrame(search_results)
                self.logger.info(f"✅ Found {len(df)} products for pattern '{pattern}'")
                return df
            else:
                return None

        except Exception as e:
            self.logger.error(f"Wildcard search failed for pattern '{pattern}': {e}")
            raise ExternalServiceError(f"Failed to perform wildcard search: {e}")

    async def search_by_product_codes(self, product_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        Search for products by exact product codes (batch lookup).

        This implements Lemonsoft-specific batch product lookup using SQL database.

        Args:
            product_codes: List of product codes to search for

        Returns:
            DataFrame with product search results, None if no matches found.

        Raises:
            ExternalServiceError: If database is unavailable
        """
        if not product_codes:
            self.logger.warning("No product codes provided for search")
            return None

        try:
            # Clean and prepare product codes
            clean_codes = [str(code).strip() for code in product_codes if code]

            if not clean_codes:
                return None

            self.logger.info(f"🔢 Lemonsoft product code search - Searching for {len(clean_codes)} codes: {clean_codes}")

            # Build IN clause for SQL query
            # Escape single quotes by doubling them
            escaped_codes = [code.replace("'", "''") for code in clean_codes]
            codes_list = "', '".join(escaped_codes)

            query = f"""
            WITH yearly_sales AS (
                SELECT
                    ir.invoicerow_productcode as product_code,
                    SUM(ir.invoicerow_amount) as total_sales_qty
                FROM invoicerows ir
                JOIN invoices i ON ir.invoice_id = i.invoice_id
                WHERE i.invoice_date >= DATEADD(year, -1, GETDATE())
                  AND ir.invoicerow_amount > 0
                  AND ir.invoicerow_productcode IN ('{codes_list}')
                GROUP BY ir.invoicerow_productcode
            ),
            total_stock AS (
                SELECT
                    p.product_code,
                    SUM(COALESCE(ps.stock_instock, 0)) as total_current_stock
                FROM products p
                LEFT JOIN product_stocks ps ON p.product_id = ps.product_id
                WHERE p.product_code IN ('{codes_list}')
                GROUP BY p.product_code
            )
            SELECT
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
                p.product_nonstock_bit,
                pd.product_group_code,
                COALESCE(p.product_price, 0) as price,
                pt.text_note as description,
                COALESCE(ts.total_current_stock, 0) as total_stock,
                COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
            FROM products p
            INNER JOIN product_dimensions pd ON p.product_id = pd.product_id
            LEFT JOIN product_texts pt ON p.product_id = pt.product_id
                AND pt.text_header_number = 3
                AND (pt.language_code IS NULL OR pt.language_code = '')
            LEFT JOIN total_stock ts ON p.product_code = ts.product_code
            LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
            WHERE
                p.product_code IN ('{codes_list}')
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND (p.product_nonstock_bit IS NULL OR p.product_nonstock_bit = 0)
                AND pd.product_group_code != 0
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa
                    WHERE pa.product_id = p.product_id
                        AND pa.attribute_code IN (30)
                )
            ORDER BY p.product_code
            """

            results = await self._execute_sql_query(query)

            if not results:
                self.logger.info(f"❌ No products found for codes: {clean_codes}")
                return None

            search_results = []
            found_codes = []

            # Process SQL results
            for row in results:
                # Handle both dict (direct DB) and tuple (Function App) responses
                if isinstance(row, dict):
                    product_code = str(row.get('product_code', ''))
                    found_codes.append(product_code)

                    group_code = int(row.get('product_group_code', 0)) if row.get('product_group_code') else 0
                    priority = self._classify_product_priority(group_code)

                    search_results.append({
                        'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                        'sku': product_code,
                        'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                        'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                        'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                        'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                        'description': str(row.get('description', '')) if row.get('description') else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                        'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0,
                        'data_source': 'PRODUCT_CODE_SEARCH'
                    })
                else:
                    # Legacy tuple handling for Function App
                    product_code = str(row[1]) if row[1] else ''
                    found_codes.append(product_code)

                    group_code = int(row[7]) if row[7] else 0
                    priority = self._classify_product_priority(group_code)

                    search_results.append({
                        'id': str(row[0]) if row[0] else '',
                        'sku': product_code,
                        'name': str(row[2]) if row[2] else '',
                        'extra_name': str(row[3]) if row[3] else '',
                        'price': float(row[8]) if row[8] else 0.0,
                        'product_searchcode': str(row[4]) if row[4] else '',
                        'description': str(row[9]) if row[9] else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row[10]) if len(row) > 10 and row[10] else 0.0,
                        'yearly_sales_qty': float(row[11]) if len(row) > 11 and row[11] else 0.0,
                        'data_source': 'PRODUCT_CODE_SEARCH'
                    })

            # Log what was found
            missing_codes = set(clean_codes) - set(found_codes)
            if missing_codes:
                self.logger.warning(f"⚠️ Product codes not found: {list(missing_codes)}")

            if search_results:
                df = pd.DataFrame(search_results)
                self.logger.info(f"✅ Found {len(df)} products out of {len(clean_codes)} requested codes")
                return df
            else:
                return None

        except Exception as e:
            self.logger.error(f"Product code search failed: {e}")
            raise ExternalServiceError(f"Failed to search by product codes: {e}")

    # ==================== HELPER METHODS ====================

    async def _execute_sql_query(self, query: str) -> List[Any]:
        """
        Execute SQL query against Lemonsoft database.

        Args:
            query: SQL query string

        Returns:
            List of result rows (as dicts or tuples depending on mode)

        Raises:
            Exception: If database is unavailable or query fails
        """
        try:
            # Create database client
            db_client = create_database_client()
            if not db_client:
                raise Exception("Failed to create database client")

            # Execute query (synchronous, but we're in async context)
            results = db_client._execute_query_sync(query, [])

            return results if results else []

        except Exception as e:
            self.logger.error(f"SQL query execution failed: {e}")
            raise

    def _classify_product_priority(self, group_code: int) -> str:
        """
        Classify product as priority or non-priority based on group code.

        This is Lemonsoft-specific logic based on product group codes.

        Args:
            group_code: Product group code

        Returns:
            'priority' or 'non_priority'
        """
        # Lemonsoft-specific priority groups
        # Group codes 1-999 are priority products
        # Group codes >= 1000 are non-priority
        return 'priority' if group_code < 1000 else 'non_priority'
