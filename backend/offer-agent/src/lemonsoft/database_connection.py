"""
Database connection utility for Lemonsoft SQL Server
Supports both Windows Authentication and SQL Server Authentication
"""

import pyodbc
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import BaseOfferAutomationError


class DatabaseConnectionError(BaseOfferAutomationError):
    """Database connection specific error."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            context={'service_name': 'lemonsoft_database'},
            recovery_suggestions=[
                "Check database server connectivity",
                "Verify authentication credentials",
                "Ensure database permissions are configured",
                "Check VPN connection if accessing remotely"
            ],
            **kwargs
        )


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    server: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_windows_auth: bool = True
    connection_timeout: int = 30
    command_timeout: int = 60
    
    def get_connection_string(self) -> str:
        """Generate ODBC connection string based on authentication method."""
        # Get driver from settings or use default
        settings = get_settings()
        
        # Default to ODBC Driver 17 for Docker (better network compatibility), modern driver for local
        default_driver = 'ODBC Driver 17 for SQL Server' if settings.deployment_mode == 'docker' else 'ODBC Driver 18 for SQL Server'
        driver = getattr(settings, 'database_driver', default_driver)
        
        # Check if DATABASE_DRIVER environment variable is set (this overrides everything)
        import os
        env_driver = os.getenv('DATABASE_DRIVER')
        if env_driver:
            print(f"Database driver override from env: {env_driver}")
            driver = env_driver
        else:
            print(f"Using default database driver: {driver}")
        
        base = f"DRIVER={{{driver}}};SERVER={self.server};DATABASE={self.database};"
        
        # Handle different driver types with appropriate settings
        if "ODBC Driver 18" in driver:
            # ODBC Driver 18 specific settings - optimized for SQL Server authentication
            if self.use_windows_auth:
                # Windows Authentication for ODBC Driver 18
                base += "Encrypt=Optional;TrustServerCertificate=yes;"
                base += "Connection Timeout=30;Login Timeout=30;"
                base += "Authentication=ActiveDirectoryIntegrated;"
            else:
                # SQL Server Authentication for ODBC Driver 18 - key fix for Docker
                base += "Encrypt=Optional;TrustServerCertificate=yes;"
                base += "Connection Timeout=30;Login Timeout=30;"
                base += "Authentication=SqlPassword;"
                base += "ConnectRetryCount=2;ConnectRetryInterval=5;"
                # Critical: Disable connection pooling for Docker containers
                base += "Pooling=false;"
        elif "ODBC Driver 17" in driver:
            # ODBC Driver 17 specific settings
            base += "Encrypt=No;TrustServerCertificate=yes;"
            base += "Connection Timeout=30;Login Timeout=30;"
        elif driver == "SQL Server":
            # Legacy SQL Server driver (FreeTDS) - add TDS-specific parameters
            base += "Connection Timeout=30;"
            base += "TDS_Version=7.2;"  # Changed to 7.2 per Stack Overflow success
            base += "ClientCharset=UTF-8;"
            # Don't add Encrypt settings for legacy driver - FreeTDS handles this differently
        elif driver == "FreeTDS":
            # Direct FreeTDS driver (Stack Overflow solution)
            base += "TDS_Version=7.2;"  # Start with 7.2, fallback to 4.2 if needed
            base += "Connection Timeout=30;"
        
        if self.use_windows_auth:
            return base + "Trusted_Connection=yes;"
        else:
            if not self.username or not self.password:
                raise DatabaseConnectionError("Username and password required for SQL Server authentication")
            return base + f"UID={self.username};PWD={self.password};"


class LemonsoftDatabaseClient:
    """Database client for Lemonsoft with context manager support."""
    """
    Database client for direct SQL Server access to Lemonsoft database.
    
    Supports both Windows Authentication (for local development) and
    SQL Server Authentication (for Docker/VPN deployment).
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database client.
        
        Args:
            config: Database configuration. If None, loads from settings.
        """
        self.logger = get_logger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_settings()
        
        self.logger.info(f"Database client initialized for {self.config.server}/{self.config.database}")
        self.logger.info(f"Authentication method: {'Windows' if self.config.use_windows_auth else 'SQL Server'}")
    
    def _load_config_from_settings(self) -> DatabaseConfig:
        """Load database configuration from application settings."""
        settings = get_settings()
        
        # Get database connection info from environment variables
        database_host = settings.database_host
        database_port = settings.database_port
        database_name = settings.database_name
        
        # Build server string with port if provided
        server = f"{database_host},{database_port}" if database_port else database_host
        
        # Determine authentication method
        # Use SQL Server auth if we have SQL password configured
        use_windows_auth = True
        
        # For Docker deployment, force SQL Server authentication
        if hasattr(settings, 'deployment_mode') and settings.deployment_mode == 'docker':
            use_windows_auth = False
        
        # If we have SQL Server password configured, use SQL Server auth
        if hasattr(settings, 'lemonsoft_sql_password') and settings.lemonsoft_sql_password:
            use_windows_auth = False
        
        return DatabaseConfig(
            server=server,
            database=database_name,
            username="laurip" if not use_windows_auth else None,
            password=settings.lemonsoft_sql_password if not use_windows_auth else None,
            use_windows_auth=use_windows_auth,
            connection_timeout=30,
            command_timeout=60
        )
    
    @contextmanager
    def get_connection(self):
        """
        Get a synchronous database connection with automatic cleanup.
        
        Yields:
            pyodbc.Connection: Database connection
        """
        conn = None
        try:
            conn_str = self.config.get_connection_string()
            # Log connection string but mask password
            safe_conn_str = conn_str.replace(f"PWD={self.config.password}", "PWD=***") if self.config.password else conn_str
            self.logger.info(f"Database connection string: {safe_conn_str}")
            self.logger.debug(f"Connecting to database with timeout {self.config.connection_timeout}s")
            
            conn = pyodbc.connect(
                conn_str, 
                timeout=self.config.connection_timeout,
                autocommit=True
            )
            conn.timeout = self.config.command_timeout
            
            self.logger.debug("Database connection established")
            yield conn
            
        except pyodbc.Error as e:
            # If ODBC Driver 18 fails with HYT00 timeout, try Driver 17 as fallback
            if "HYT00" in str(e) and "ODBC Driver 18" in self.config.get_connection_string():
                self.logger.warning("ODBC Driver 18 failed with timeout, trying fallback to Driver 17...")
                try:
                    # Create a temporary config with Driver 17
                    fallback_config = DatabaseConfig(
                        server=self.config.server,
                        database=self.config.database,
                        username=self.config.username,
                        password=self.config.password,
                        use_windows_auth=self.config.use_windows_auth,
                        connection_timeout=self.config.connection_timeout,
                        command_timeout=self.config.command_timeout
                    )
                    
                    # Override the driver for fallback - need to set environment variable
                    import os
                    original_env_driver = os.getenv('DATABASE_DRIVER')
                    fallback_driver = "ODBC Driver 17 for SQL Server"
                    
                    # Temporarily set environment variable to override driver
                    os.environ['DATABASE_DRIVER'] = fallback_driver
                    
                    fallback_conn_str = fallback_config.get_connection_string()
                    safe_fallback_conn_str = fallback_conn_str.replace(f"PWD={fallback_config.password}", "PWD=***") if fallback_config.password else fallback_conn_str
                    self.logger.info(f"Fallback connection string: {safe_fallback_conn_str}")
                    
                    conn = pyodbc.connect(
                        fallback_conn_str,
                        timeout=self.config.connection_timeout,
                        autocommit=True
                    )
                    conn.timeout = self.config.command_timeout
                    
                    # Restore original environment variable
                    if original_env_driver is not None:
                        os.environ['DATABASE_DRIVER'] = original_env_driver
                    else:
                        os.environ.pop('DATABASE_DRIVER', None)
                    
                    self.logger.info("✅ Fallback to ODBC Driver 17 successful!")
                    yield conn
                    return
                    
                except Exception as fallback_error:
                    self.logger.error(f"Fallback to Driver 17 also failed: {fallback_error}")
                    # Restore original environment variable
                    try:
                        if original_env_driver is not None:
                            os.environ['DATABASE_DRIVER'] = original_env_driver
                        else:
                            os.environ.pop('DATABASE_DRIVER', None)
                    except:
                        pass
            
            error_msg = f"Database connection failed: {e}"
            self.logger.error(error_msg)
            
            # Provide specific error guidance
            if "28000" in str(e):
                error_msg += " (Authentication failed - check username/password)"
            elif "42000" in str(e):
                error_msg += " (Access denied - check database permissions)"
            elif "08001" in str(e):
                error_msg += " (Connection failed - check server name/network)"
            elif "HYT00" in str(e):
                error_msg += " (Login timeout - check server authentication settings)"
            
            raise DatabaseConnectionError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected database error: {e}"
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg)
            
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    async def execute_query_async(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query asynchronously.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of dictionaries representing query results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._execute_query_sync, 
            query, 
            params
        )
    
    def _execute_query_sync(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query synchronously.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of dictionaries representing query results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                self.logger.debug(f"Executing query: {query[:100]}...")
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [column[0] for column in cursor.description] if cursor.description else []
                
                # Fetch all results
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = value
                    results.append(row_dict)
                
                self.logger.debug(f"Query returned {len(results)} rows")
                return results
                
            except pyodbc.Error as e:
                error_msg = f"Query execution failed: {e}"
                self.logger.error(error_msg)
                raise DatabaseConnectionError(error_msg)
                
            finally:
                cursor.close()
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return connection info.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            results = await self.execute_query_async("SELECT USER_NAME(), SYSTEM_USER, DB_NAME(), GETDATE()")
            
            if results:
                result = results[0]
                keys = list(result.keys())
                return {
                    'status': 'success',
                    'database_user': result[keys[0]] if len(keys) > 0 else None,
                    'system_user': result[keys[1]] if len(keys) > 1 else None,
                    'database_name': result[keys[2]] if len(keys) > 2 else None,
                    'server_time': result[keys[3]] if len(keys) > 3 else None,
                    'authentication_method': 'Windows' if self.config.use_windows_auth else 'SQL Server'
                }
            else:
                return {'status': 'failed', 'error': 'No results returned'}
                
        except Exception as e:
            return {
                'status': 'failed', 
                'error': str(e),
                'authentication_method': 'Windows' if self.config.use_windows_auth else 'SQL Server'
            }
    
    async def get_pricing_data(self, product_codes: List[str], customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pricing data for specified products.
        
        Args:
            product_codes: List of product codes to get pricing for
            customer_id: Optional customer ID for customer-specific pricing
            
        Returns:
            List of pricing records
        """
        if not product_codes:
            return []
        
        # Build query based on your Lemonsoft database schema
        # This is a placeholder - you'll need to adjust based on actual table structure
        placeholders = ','.join(['?' for _ in product_codes])
        
        base_query = f"""
        SELECT 
            p.ProductCode,
            p.ProductName,
            p.ListPrice,
            p.Unit,
            p.VATRate
        FROM Products p
        WHERE p.ProductCode IN ({placeholders})
        """
        
        # If customer-specific pricing exists, add customer pricing logic
        if customer_id:
            query = f"""
            SELECT 
                p.ProductCode,
                p.ProductName,
                COALESCE(cp.CustomerPrice, p.ListPrice) as Price,
                p.Unit,
                p.VATRate,
                cp.DiscountPercent
            FROM Products p
            LEFT JOIN CustomerPricing cp ON p.ProductCode = cp.ProductCode AND cp.CustomerID = ?
            WHERE p.ProductCode IN ({placeholders})
            """
            params = [customer_id] + product_codes
        else:
            query = base_query
            params = product_codes
        
        return await self.execute_query_async(query, params)
    
    def execute_query(self, query: str, params: Optional[List] = None) -> List[Tuple]:
        """
        Execute a SQL query synchronously and return raw results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of tuples representing query results
        """
        return self._execute_query_sync_simple(query, params)
    
    def execute_query_sync(self, query: str, params: Optional[List] = None) -> List[Tuple]:
        """
        Execute a SQL query synchronously and return raw results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of tuples representing query results
        """
        return self._execute_query_sync_simple(query, params)
    
    def _execute_query_sync_simple(self, query: str, params: Optional[List] = None) -> List[Tuple]:
        """Execute query and return simple tuple results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                self.logger.debug(f"Executing query: {query[:100]}...")
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Fetch all results as tuples
                rows = cursor.fetchall()
                
                self.logger.debug(f"Query returned {len(rows)} rows")
                return rows
                
            except pyodbc.Error as e:
                error_msg = f"Query execution failed: {e}"
                self.logger.error(error_msg)
                raise DatabaseConnectionError(error_msg)
                
            finally:
                cursor.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def close(self):
        """Close the database client and cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            self.logger.info("Database client closed")


# Factory function for easy client creation
def create_database_client(use_windows_auth: Optional[bool] = None) -> LemonsoftDatabaseClient:
    """
    Create a database client with appropriate authentication method.
    
    Args:
        use_windows_auth: If specified, forces the authentication method.
                         If None, auto-detects based on environment.
    
    Returns:
        Configured database client
    """
    settings = get_settings()
    
    if use_windows_auth is None:
        # Auto-detect authentication method based on deployment mode
        # Development: Windows auth, Production/Docker: SQL Server auth
        use_windows_auth = settings.deployment_mode in ['local', 'development']
    
    # Build server string with port
    server = f"{settings.database_host},{settings.database_port}" if settings.database_port else settings.database_host
    
    config = DatabaseConfig(
        server=server,
        database=settings.database_name,
        username="laurip" if not use_windows_auth else None,
        password=settings.lemonsoft_sql_password if not use_windows_auth and settings.lemonsoft_sql_password else None,
        use_windows_auth=use_windows_auth
    )
    
    return LemonsoftDatabaseClient(config) 