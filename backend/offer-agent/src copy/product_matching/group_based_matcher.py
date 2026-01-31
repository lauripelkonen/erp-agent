import logging
import os
import sys
import json
import httpx
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types

# Add both src and emails directories to path for imports (same as main.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lemonsoft.api_client import LemonsoftAPIClient
from src.lemonsoft.database_connection import create_database_client

try:
    from .config import Config
except ImportError:
    # Fallback configuration when config module is not available
    class Config:
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

class GroupBasedMatcher:
    """Group-based product matcher using hierarchical product group navigation.
    
    This matcher uses AI agents with function calling to navigate through product groups,
    select appropriate groups, and find products within those groups using API filtering.
    """

    def __init__(self, max_products_display: int = 100):
        self.logger = logging.getLogger(__name__)
        self.max_products_display = max_products_display
        
        # Initialize Lemonsoft API client
        self.lemonsoft_client = LemonsoftAPIClient()
        self.logger.info("Lemonsoft API client initialized for group-based product matching")
        
        # SQL proxy configuration based on deployment mode (same pattern as pricing calculator)
        self.deployment_mode = os.getenv('DEPLOYMENT_MODE', 'direct').lower()
        self.logger.info(f"Group-based matcher deployment mode: {self.deployment_mode}")
        

        # SQL proxy configuration for Docker mode
        if self.deployment_mode == 'docker':
            self.sql_proxy_url = os.getenv('SQL_PROXY_URL', 'https://xxxxx.azurewebsites.net')
            self.sql_proxy_api_key = os.getenv('SQL_PROXY_API_KEY', '')
            self.azure_function_key = os.getenv('AZURE_FUNCTION_KEY', '')
            self.logger.info(f"SQL proxy configured: {self.sql_proxy_url}")
            self.http_client = None  # Will be initialized when needed
        else:
            self.http_client = None
        
        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # Load product groups from JSON
        self.product_groups = self._load_product_groups()
        self.current_group = None  # Track currently selected group
        
        # API usage tracking
        self.api_calls_made = 0
        
        self.logger.info(f"GroupBasedMatcher initialized with {len(self.product_groups)} main groups")

    def _load_product_groups(self) -> List[Dict]:
        """Load product groups from JSON file."""
        script_dir = Path(__file__).parent
        groups_file = script_dir / "product_groups.json"
        
        try:
            with open(groups_file, 'r', encoding='utf-8') as f:
                groups = json.load(f)
            
            self.logger.info(f"Loaded {len(groups)} main product groups from {groups_file}")
            
            # Count total subgroups for logging
            total_subgroups = sum(len(group.get('subgroups', [])) for group in groups)
            self.logger.info(f"Total subgroups available: {total_subgroups}")
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Failed to load product groups from {groups_file}: {e}")
            return []

    def _format_product_groups_for_prompt(self) -> str:
        """Format product groups for inclusion in system prompt."""
        if not self.product_groups:
            return "No product groups available."
        
        groups_text = "AVAILABLE PRODUCT GROUPS:\n\n"
        
        for main_group in self.product_groups:
            groups_text += f"📁 {main_group['id']} - {main_group['name']}\n"
            
            subgroups = main_group.get('subgroups', [])
            if subgroups:
                for subgroup in subgroups:
                    groups_text += f"  └── {subgroup['id']} - {subgroup['name']}\n"
            
            groups_text += "\n"
        
        return groups_text

    # --------------------------- SQL execution methods --------------------------
    async def _initialize_http_client(self):
        """Initialize HTTP client for Function App proxy if needed."""
        if self.deployment_mode == 'docker' and self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
    async def _execute_sql_query(self, query: str, params: list = None) -> list:
        """
        Execute SQL query using the appropriate method based on deployment mode.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        if self.deployment_mode == 'docker':
            await self._initialize_http_client()
            return await self._execute_sql_via_function_app(query, params)
        else:
            # Direct database mode - use existing create_database_client pattern
            db_client = create_database_client()
            if not db_client:
                raise Exception("Failed to create database client")
            return db_client._execute_query_sync(query, params)
    
    async def _execute_sql_via_function_app(self, query: str, params: list = None) -> list:
        """Execute SQL query via Azure Function App proxy."""
        try:
            headers = {
                'x-functions-key': self.azure_function_key,
                'X-API-Key': self.sql_proxy_api_key,
                'Content-Type': 'application/json'
            }
            
            database_name = os.getenv('DATABASE_NAME', 'LemonDB1')
            
            payload = {
                'query': query,
                'params': params or [],
                'database': database_name
            }
            
            self.logger.debug(f"Executing SQL via Function App: {query[:100]}...")
            
            response = await self.http_client.post(
                f"{self.sql_proxy_url}/api/query",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.debug(f"Function App query successful: {result.get('row_count', 0)} rows")
                    return result.get('data', [])
                else:
                    raise Exception(f"Function App query failed: {result.get('error')}")
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                raise Exception(f"Function App request failed: {error_text}")
                
        except Exception as e:
            self.logger.error(f"SQL query via Function App failed: {e}")
            raise

    async def _sql_search_by_searchcode(self, pattern: str, group_code: int):
        """Search for products using SQL query on product_searchcode field.
        
        Uses product_dimensions.product_group_code to filter by group.
        """
        try:
            if not pattern:
                return []
                
            # Create SQL LIKE pattern
            sql_pattern = f'%{pattern}%'
            
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
            SELECT TOP 200
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
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
            WHERE pd.product_group_code = {group_code}
                AND (
                    p.product_description LIKE '{sql_pattern}'
                    OR p.product_description2 LIKE '{sql_pattern}'
                    OR p.product_searchcode LIKE '{sql_pattern}'
                    OR pt.text_note LIKE '{sql_pattern}'
                )
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa 
                    WHERE pa.product_id = p.product_id 
                        AND pa.attribute_code IN (30)
                )
            ORDER BY p.product_code
            """
            
            results = await self._execute_sql_query(query, [])
            
            if results:
                # Convert SQL results to API-compatible format
                api_format_results = []
                for row in results:
                    # Handle both dict (direct DB) and tuple (Function App) responses
                    if isinstance(row, dict):
                        api_format_results.append({
                            'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                            'sku': str(row.get('product_code', '')) if row.get('product_code') else '',
                            'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                            'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                            'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                            'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                            'description': str(row.get('description', '')) if row.get('description') else '',  # From product_texts
                            'group_code': int(row.get('product_group_code')) if row.get('product_group_code') else group_code,
                            'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                            'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0
                        })
                    else:
                        # Legacy tuple handling for Function App (now with stock/sales at positions 9, 10)
                        api_format_results.append({
                            'id': str(row[0]) if row[0] else '',
                            'sku': str(row[1]) if row[1] else '',
                            'name': str(row[2]) if row[2] else '',
                            'extra_name': str(row[3]) if len(row) > 3 and row[3] else '',
                            'price': float(row[7]) if len(row) > 7 and row[7] else 0.0,
                            'product_searchcode': str(row[4]) if len(row) > 4 and row[4] else '',
                            'description': str(row[8]) if len(row) > 8 and row[8] else '',
                            'group_code': int(row[6]) if len(row) > 6 and row[6] else group_code,
                            'total_stock': float(row[9]) if len(row) > 9 and row[9] else 0.0,
                            'yearly_sales_qty': float(row[10]) if len(row) > 10 and row[10] else 0.0
                        })
                
                self.logger.info(f"Found {len(api_format_results)} products from SQL searchcode search in group {group_code}")
                return api_format_results
            else:
                self.logger.info(f"No products found from SQL searchcode search in group {group_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"SQL searchcode search failed for group {group_code}: {e}")
            return []
    
    async def _sql_fetch_group_sorted(self, group_code: int, sort_by: str, limit: int = 100) -> List[Dict]:
        """Fetch products from group with SQL-based sorting for better performance."""
        try:
            # Determine ORDER BY clause
            order_clause = "p.product_code"  # Default sort
            if sort_by == 'name':
                order_clause = "p.product_description"
            elif sort_by == 'price':
                order_clause = "COALESCE(p.product_price, 0) DESC"
            elif sort_by == 'sku':
                order_clause = "p.product_code"
                
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
            SELECT TOP {limit}
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
                pd.product_group_code,
                COALESCE(p.product_price, 0) as price,
                COALESCE(ts.total_current_stock, 0) as total_stock,
                COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
            FROM products p
            INNER JOIN product_dimensions pd ON p.product_id = pd.product_id
            LEFT JOIN total_stock ts ON p.product_code = ts.product_code
            LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
            WHERE pd.product_group_code = {group_code}
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa 
                    WHERE pa.product_id = p.product_id 
                        AND pa.attribute_code IN (30)
                )
            ORDER BY {order_clause}
            """
            
            results = await self._execute_sql_query(query, [])
            
            if results:
                api_format_results = []
                for row in results:
                    # Handle both dict (direct DB) and tuple (Function App) responses
                    if isinstance(row, dict):
                        group_code_from_sql = int(row.get('product_group_code')) if row.get('product_group_code') else group_code
                        priority = self._classify_product_priority(group_code_from_sql)
                        
                        api_format_results.append({
                            'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                            'sku': str(row.get('product_code', '')) if row.get('product_code') else '',
                            'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                            'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                            'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                            'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                            'group_code': group_code_from_sql,
                            'priority': priority,
                            'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                            'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0
                        })
                    else:
                        # Legacy tuple handling for Function App (now with stock/sales at positions 8, 9)
                        group_code_from_sql = int(row[6]) if len(row) > 6 and row[6] else group_code
                        priority = self._classify_product_priority(group_code_from_sql)
                        
                        api_format_results.append({
                            'id': str(row[0]) if row[0] else '',
                            'sku': str(row[1]) if row[1] else '',
                            'name': str(row[2]) if row[2] else '',
                            'extra_name': str(row[3]) if len(row) > 3 and row[3] else '',
                            'price': float(row[7]) if len(row) > 7 and row[7] else 0.0,
                            'product_searchcode': str(row[4]) if len(row) > 4 and row[4] else '',
                            'group_code': group_code_from_sql,
                            'priority': priority,
                            'total_stock': float(row[8]) if len(row) > 8 and row[8] else 0.0,
                            'yearly_sales_qty': float(row[9]) if len(row) > 9 and row[9] else 0.0
                        })
                    
                return api_format_results
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"SQL sorted fetch failed for group {group_code}: {e}")
            return []
    
    async def _fallback_api_fetch(self, group_code: int, search_results: List[Dict]):
        """Fallback API fetch when no SQL sorting is needed."""
        try:
            # Ensure Lemonsoft client is initialized
            if not hasattr(self.lemonsoft_client, 'client') or not self.lemonsoft_client.client:
                await self.lemonsoft_client.initialize()
            
            self.logger.info(f"Fetching ALL products from group {group_code} (no filters)")
            
            params = {'filter.group_code': group_code, 'filter.page_size': 200}
            response = await self.lemonsoft_client.get('/api/products', params=params)
            
            if response is not None and hasattr(response, 'status_code'):
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data is not None and isinstance(data, dict):
                            results = data.get('results')
                            if results is None:
                                self.logger.info(f"API returned results:null for name search; treating as empty list")
                                results = []
                            if isinstance(results, list):
                                # Extract essential fields with priority classification
                                essential_results = []
                                for product in results:
                                    if isinstance(product, dict):
                                        group_code_from_api = product.get('group_code')
                                        priority = self._classify_product_priority(group_code_from_api)
                                        essential_results.append({
                                            'name': product.get('name', ''),
                                            'extra_name': product.get('extra_name', ''),
                                            'sku': product.get('sku', ''),
                                            'price': product.get('price', 0.0),
                                            'id': product.get('id', ''),
                                            'group_code': group_code_from_api,
                                            'priority': priority
                                        })
                                search_results.extend(essential_results)
                                self.logger.info(f"Found {len(essential_results)} products in group {group_code} (no filters)")
                            else:
                                self.logger.info(f"API returned invalid results format when fetching all from group {group_code}: {type(results)}")
                        else:
                            self.logger.info(f"API returned invalid data format when fetching all from group {group_code}: {type(data)}")
                    except Exception as json_e:
                        self.logger.info(f"Failed to parse JSON response when fetching all from group {group_code}: {json_e}")
                else:
                    self.logger.info(f"API returned status {response.status_code} when fetching all from group {group_code}")
            else:
                self.logger.info(f"API returned invalid response object when fetching all from group {group_code}: {type(response)}")
        except Exception as e:
            self.logger.info(f"Exception during all products fetch from group {group_code}: {type(e).__name__}: {e}")

    def _classify_product_priority(self, group_code):
        """Classify product as priority or non-priority based on group_code.
        
        Args:
            group_code: Integer group code from API or SQL
            
        Returns:
            str: 'priority' if group_code >= 101010, 'non-priority' if < 101010
        """
        if group_code is None:
            return 'non-priority'  # Default to non-priority if no group_code
        
        try:
            group_code_int = int(group_code)
            return 'priority' if group_code_int >= 101010 else 'non-priority'
        except (ValueError, TypeError):
            return 'non-priority'  # Default to non-priority if invalid group_code

    async def _fetch_products_from_group(self, group_code: int, limit: int = None, 
                                       name_filter: str = None,
                                       sku_filter: str = None,
                                       sort_by: str = None) -> Dict:
        """Fetch products from specific group using comprehensive search like original matcher.
        
        Performs 4 searches in total:
        1. API search by name field (with name_filter)
        2. API search by extra_name field (with name_filter)  
        3. Optional API search by SKU field (if sku_filter provided)
        4. SQL search by product_searchcode field (with name_filter)
        
        Results are combined and deduplicated by SKU.
        
        Args:
            group_code: Group code to fetch products from
            limit: Maximum number of products to display
            name_filter: Filter term to search in name, extra_name, and searchcode
            sku_filter: Optional specific SKU filter
            sort_by: Sort products by field (name, price, etc.)
        
        Returns:
            Dict with success status, products list, and metadata
        """
        try:
            # Ensure Lemonsoft client is initialized
            if not hasattr(self.lemonsoft_client, 'client') or not self.lemonsoft_client.client:
                await self.lemonsoft_client.initialize()

            search_results = []
            
            # Convert name_filter to API pattern format (same logic as product_matcher.py)
            api_pattern = None
            if name_filter:
                if '%' in name_filter:
                    # Pattern already contains % wildcards, use as-is (httpx will URL encode)
                    api_pattern = name_filter
                else:
                    # If no % wildcards provided, assume contains search and add % on both sides
                    api_pattern = f'%{name_filter}%'

            self.logger.info(f"Searching group {group_code} with name_filter: '{name_filter}' -> API pattern: '{api_pattern}'")

            # 0. If no filters provided but sort_by is specified, use SQL for proper sorting
            if not name_filter and not sku_filter and sort_by:
                try:
                    self.logger.info(f"Fetching ALL products from group {group_code} with SQL-based sorting: {sort_by}")
                    sql_results = await self._sql_fetch_group_sorted(group_code, sort_by, limit=100)
                    if sql_results:
                        search_results.extend(sql_results)
                        self.logger.info(f"Found {len(sql_results)} products in group {group_code} with SQL sorting")
                    else:
                        self.logger.info(f"No products found in group {group_code} with SQL sorting")
                except Exception as e:
                    self.logger.info(f"Exception during SQL sorted fetch from group {group_code}: {type(e).__name__}: {e}")
                    # Fallback to API if SQL fails
                    await self._fallback_api_fetch(group_code, search_results)
            
            # 0a. If no filters and no sorting, do a simple API group fetch
            elif not name_filter and not sku_filter:
                await self._fallback_api_fetch(group_code, search_results)

            # 1. Search in main product name within group
            if api_pattern:
                try:
                    # Ensure Lemonsoft client is initialized
                    if not hasattr(self.lemonsoft_client, 'client') or not self.lemonsoft_client.client:
                        await self.lemonsoft_client.initialize()
                    
                    self.logger.info(f"Searching in name field within group {group_code} with pattern: '{api_pattern}'")
                    
                    params = {'filter.group_code': group_code, 'filter.name': api_pattern, 'filter.page_size': 100}
                    response = await self.lemonsoft_client.get('/api/products', params=params)
                    
                    if response is not None and hasattr(response, 'status_code'):
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if data is not None and isinstance(data, dict):
                                    results = data.get('results', [])
                                    if results is not None and isinstance(results, list):
                                        # Extract essential fields with priority classification
                                        essential_results = []
                                        for product in results:
                                            if isinstance(product, dict):
                                                group_code_from_api = product.get('group_code')
                                                priority = self._classify_product_priority(group_code_from_api)
                                                essential_results.append({
                                                    'name': product.get('name', ''),
                                                    'extra_name': product.get('extra_name', ''),
                                                    'sku': product.get('sku', ''),
                                                    'price': product.get('price', 0.0),
                                                    'id': product.get('id', ''),
                                                    'group_code': group_code_from_api,
                                                    'priority': priority
                                                })
                                        search_results.extend(essential_results)
                                        self.logger.info(f"Found {len(essential_results)} products searching by name in group {group_code}")
                                    else:
                                        self.logger.info(f"API returned invalid results format when searching by name: {type(results)}")
                                else:
                                    self.logger.info(f"API returned invalid data format when searching by name: {type(data)}")
                            except Exception as json_e:
                                self.logger.info(f"Failed to parse JSON response when searching by name: {json_e}")
                        else:
                            self.logger.info(f"API returned status {response.status_code} when searching by name in group {group_code}")
                    else:
                        self.logger.info(f"API returned invalid response object when searching by name: {type(response)}")
                except Exception as e:
                    self.logger.info(f"Exception during name search in group {group_code}: {type(e).__name__}: {e}")

            # 2. Search in extra_name field within group
            if api_pattern:
                try:
                    # Ensure Lemonsoft client is initialized
                    if not hasattr(self.lemonsoft_client, 'client') or not self.lemonsoft_client.client:
                        await self.lemonsoft_client.initialize()
                    
                    self.logger.info(f"Searching in extra_name field within group {group_code} with pattern: '{api_pattern}'")
                    
                    params = {'filter.group_code': group_code, 'filter.extra_name': api_pattern, 'filter.page_size': 100}
                    response = await self.lemonsoft_client.get('/api/products', params=params)
                    
                    if response is not None and hasattr(response, 'status_code'):
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if data is not None and isinstance(data, dict):
                                    results = data.get('results')
                                    if results is None:
                                        self.logger.info(f"API returned results:null for extra_name search; treating as empty list")
                                        results = []
                                    if isinstance(results, list):
                                        # Extract essential fields with priority classification
                                        essential_results = []
                                        for product in results:
                                            if isinstance(product, dict):
                                                group_code_from_api = product.get('group_code')
                                                priority = self._classify_product_priority(group_code_from_api)
                                                essential_results.append({
                                                    'name': product.get('name', ''),
                                                    'extra_name': product.get('extra_name', ''),
                                                    'sku': product.get('sku', ''),
                                                    'price': product.get('price', 0.0),
                                                    'id': product.get('id', ''),
                                                    'group_code': group_code_from_api,
                                                    'priority': priority
                                                })
                                        search_results.extend(essential_results)
                                        self.logger.info(f"Found {len(essential_results)} products searching by extra_name in group {group_code}")
                                    else:
                                        self.logger.info(f"API returned invalid results format when searching by extra_name: {type(results)}")
                                else:
                                    self.logger.info(f"API returned invalid data format when searching by extra_name: {type(data)}")
                            except Exception as json_e:
                                self.logger.info(f"Failed to parse JSON response when searching by extra_name: {json_e}")
                        else:
                            self.logger.info(f"API returned status {response.status_code} when searching by extra_name in group {group_code}")
                    else:
                        self.logger.info(f"API returned invalid response object when searching by extra_name: {type(response)}")
                except Exception as e:
                    self.logger.info(f"Exception during extra_name search in group {group_code}: {type(e).__name__}: {e}")

            # 3. Optional SKU search within group
            if sku_filter:
                try:
                    sku_pattern = sku_filter
                    
                    # Ensure Lemonsoft client is initialized
                    if not hasattr(self.lemonsoft_client, 'client') or not self.lemonsoft_client.client:
                        await self.lemonsoft_client.initialize()
                    
                    self.logger.info(f"Searching by SKU within group {group_code} with pattern: '{sku_pattern}'")
                    
                    params = {'filter.group_code': group_code, 'filter.sku': sku_pattern, 'filter.page_size': 200}
                    response = await self.lemonsoft_client.get('/api/products', params=params)
                    
                    if response is not None and hasattr(response, 'status_code'):
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if data is not None and isinstance(data, dict):
                                    results = data.get('results')
                                    if results is None:
                                        self.logger.info(f"API returned results:null for sku search; treating as empty list")
                                        results = []
                                    if isinstance(results, list):
                                        essential_results = []
                                        for product in results:
                                            if isinstance(product, dict):
                                                group_code_from_api = product.get('group_code')
                                                priority = self._classify_product_priority(group_code_from_api)
                                                essential_results.append({
                                                    'name': product.get('name', ''),
                                                    'extra_name': product.get('extra_name', ''),
                                                    'sku': product.get('sku', ''),
                                                    'price': product.get('price', 0.0),
                                                    'id': product.get('id', ''),
                                                    'group_code': group_code_from_api,
                                                    'priority': priority
                                                })
                                        search_results.extend(essential_results)
                                        self.logger.info(f"Found {len(essential_results)} products searching by SKU in group {group_code}")
                                    else:
                                        self.logger.info(f"API returned invalid results format when searching by SKU: {type(results)}")
                                else:
                                    self.logger.info(f"API returned invalid data format when searching by SKU: {type(data)}")
                            except Exception as json_e:
                                self.logger.info(f"Failed to parse JSON response when searching by SKU: {json_e}")
                        else:
                            self.logger.info(f"API returned status {response.status_code} when searching by SKU in group {group_code}")
                    else:
                        self.logger.info(f"API returned invalid response object when searching by SKU: {type(response)}")

                except Exception as e:
                    self.logger.info(f"Exception during SKU search in group {group_code}: {type(e).__name__}: {e}")

            # 4. SQL search in product_searchcode field within group
            if name_filter:  # Only do SQL search if we have a search term
                try:
                    self.logger.info(f"Searching in product_searchcode field within group {group_code} with SQL pattern: '{name_filter}'")
                    sql_results = await self._sql_search_by_searchcode(name_filter, group_code)
                    if sql_results:
                        # Convert SQL results to same format as API results with priority classification
                        for sql_product in sql_results:
                            if isinstance(sql_product, dict):
                                group_code_from_sql = sql_product.get('group_code')
                                priority = self._classify_product_priority(group_code_from_sql)
                                
                                search_results.append({
                                    'name': sql_product.get('name', ''),
                                    'extra_name': sql_product.get('extra_name', ''),
                                    'sku': sql_product.get('sku', ''),
                                    'price': float(sql_product.get('price', 0.0)) if sql_product.get('price') else 0.0,
                                    'id': sql_product.get('id', ''),
                                    'product_searchcode': sql_product.get('product_searchcode', ''),
                                    'description': sql_product.get('description', ''),  # Add description from product_texts
                                    'group_code': group_code_from_sql,
                                    'priority': priority
                                })
                        self.logger.info(f"Found {len(sql_results)} additional products from SQL searchcode search in group {group_code}")
                    else:
                        self.logger.info(f"No additional products found from SQL searchcode search in group {group_code}")
                except Exception as e:
                    self.logger.info(f"Exception during SQL searchcode search in group {group_code}: {type(e).__name__}: {e}")

            # Remove duplicates by SKU
            unique_products = {}
            for product in search_results:
                if isinstance(product, dict):
                    sku = product.get('sku', '')
                    if sku and sku not in unique_products:
                        unique_products[sku] = product

            filtered_products = list(unique_products.values())
            
            self.logger.info(f"After deduplication: {len(filtered_products)} unique products in group {group_code}")

            # Separate products by priority for agent processing
            priority_products = []
            non_priority_products = []
            
            for product in filtered_products:
                if isinstance(product, dict):
                    priority = product.get('priority', 'non-priority')
                    if priority == 'priority':
                        priority_products.append(product)
                    else:
                        non_priority_products.append(product)

            # Combine with priority first
            all_products = priority_products + non_priority_products
            
            # Apply sorting if specified (only needed if not already sorted by SQL)
            sql_sorted = not name_filter and not sku_filter and sort_by
            if sort_by and all_products and not sql_sorted:
                if sort_by == 'name':
                    all_products.sort(key=lambda x: x.get('name', '').lower())
                elif sort_by == 'price':
                    all_products.sort(key=lambda x: float(x.get('price', 0)))
                elif sort_by == 'sku':
                    all_products.sort(key=lambda x: x.get('sku', ''))
            
            # Limit display results
            display_limit = min(len(all_products), limit or self.max_products_display)
            display_products = all_products[:display_limit]
            
            self.logger.info(f"Priority breakdown in group {group_code}: {len(priority_products)} priority, {len(non_priority_products)} non-priority")
            self.logger.info(f"✅ Found {len(all_products)} total products in group {group_code}, showing {len(display_products)}")
            
            return {
                'success': True,
                'products': display_products,
                'total_found': len(all_products),
                'displayed': len(display_products),
                'group_code': group_code,
                'priority_count': len(priority_products),
                'non_priority_count': len(non_priority_products)
            }
                
        except Exception as e:
            self.logger.error(f"Error in comprehensive search for group {group_code}: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

    def _get_group_info_by_code(self, group_code: int) -> Optional[Dict]:
        """Get group information by group code."""
        for main_group in self.product_groups:
            if main_group['id'] == group_code:
                return {
                    'type': 'main',
                    'id': main_group['id'],
                    'name': main_group['name'],
                    'parent': None
                }
            
            for subgroup in main_group.get('subgroups', []):
                if subgroup['id'] == group_code:
                    return {
                        'type': 'subgroup',
                        'id': subgroup['id'],
                        'name': subgroup['name'],
                        'parent': main_group['name']
                    }
        
        return None

    
    async def close(self):
        """Close the group-based matcher and clean up resources."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        if self.lemonsoft_client:
            await self.lemonsoft_client.close()