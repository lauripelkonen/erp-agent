"""
Configuration validator for the Offer Automation System.
Validates that all required environment variables are set and accessible.
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path

import aiohttp
import redis.asyncio as redis
from qdrant_client import QdrantClient

from src.config.settings import get_settings, Settings
from src.utils.logger import get_logger


class ConfigurationValidator:
    """Validates configuration and external service connectivity."""
    
    def __init__(self, settings: Settings = None):
        """Initialize validator with settings."""
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)
        self.validation_results: Dict[str, Any] = {}
    
    async def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate all configuration settings and external services.
        
        Returns:
            Tuple[bool, Dict]: (is_valid, validation_results)
        """
        self.logger.info("Starting configuration validation...")
        
        validation_checks = [
            ("environment_variables", self._validate_environment_variables),
            ("openai_connection", self._validate_openai_connection),
            ("lemonsoft_connection", self._validate_lemonsoft_connection),
            ("redis_connection", self._validate_redis_connection),
            ("email_configuration", self._validate_email_configuration),
            ("file_permissions", self._validate_file_permissions),
            ("gemini_connection", self._validate_gemini_connection),
        ]
        
        all_valid = True
        
        for check_name, check_func in validation_checks:
            try:
                self.logger.info(f"Validating {check_name}...")
                is_valid, details = await check_func()
                self.validation_results[check_name] = {
                    "valid": is_valid,
                    "details": details
                }
                if not is_valid:
                    all_valid = False
                    self.logger.warning(f"Validation failed for {check_name}: {details}")
                else:
                    self.logger.info(f"Validation passed for {check_name}")
            except Exception as e:
                self.logger.error(f"Error during {check_name} validation: {str(e)}")
                self.validation_results[check_name] = {
                    "valid": False,
                    "details": f"Validation error: {str(e)}"
                }
                all_valid = False
        
        self.validation_results["overall_valid"] = all_valid
        return all_valid, self.validation_results
    
    async def _validate_environment_variables(self) -> Tuple[bool, str]:
        """Validate that all required environment variables are set."""
        required_vars = [
            "openai_api_key",
            "lemonsoft_username",
            "lemonsoft_password", 
            "lemonsoft_database",
            "lemonsoft_api_key",
            "email_username",
            "email_password",
            "session_secret_key",
            "gemini_api_key",
            "openai_base_url",
        ]
        
        missing_vars = []
        for var in required_vars:
            value = getattr(self.settings, var, None)
            if not value or (isinstance(value, str) and value.startswith("your_")):
                missing_vars.append(var.upper())
        
        if missing_vars:
            return False, f"Missing required environment variables: {', '.join(missing_vars)}"
        
        return True, "All required environment variables are set"
    
    async def _validate_openai_connection(self) -> Tuple[bool, str]:
        """Validate OpenAI API connection."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            
            # Test with a simple API call
            response = await client.models.list()
            if response.data:
                return True, f"OpenAI connection successful. Available models: {len(response.data)}"
            else:
                return False, "OpenAI API returned no models"
                
        except ImportError:
            return False, "OpenAI package not installed"
        except Exception as e:
            return False, f"OpenAI connection failed: {str(e)}"
    
    async def _validate_lemonsoft_connection(self) -> Tuple[bool, str]:
        """Validate Lemonsoft API connection."""
        try:
            headers = self.settings.get_lemonsoft_headers()
            login_url = f"{self.settings.lemonsoft_api_url}/auth/login"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    login_url,
                    json=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("session_id"):
                            return True, f"Lemonsoft connection successful. Session ID received."
                        else:
                            return False, f"Lemonsoft login failed: {data}"
                    else:
                        text = await response.text()
                        return False, f"Lemonsoft connection failed: HTTP {response.status} - {text}"
                        
        except aiohttp.ClientError as e:
            return False, f"Lemonsoft connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error connecting to Lemonsoft: {str(e)}"

    async def _validate_redis_connection(self) -> Tuple[bool, str]:
        """Validate Redis connection."""
        try:
            redis_client = redis.from_url(
                self.settings.redis_url,
                password=self.settings.redis_password,
                socket_timeout=10
            )
            
            # Test connection
            pong = await redis_client.ping()
            if pong:
                info = await redis_client.info()
                version = info.get("redis_version", "unknown")
                await redis_client.close()
                return True, f"Redis connection successful. Version: {version}"
            else:
                await redis_client.close()
                return False, "Redis ping failed"
                
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"
    
    async def _validate_email_configuration(self) -> Tuple[bool, str]:
        """Validate email SMTP configuration."""
        try:
            import smtplib
            from email.mime.text import MimeText
            
            # Test SMTP connection
            with smtplib.SMTP(self.settings.email_smtp_host, self.settings.email_smtp_port) as server:
                server.starttls()
                server.login(self.settings.email_username, self.settings.email_password)
                
            return True, "SMTP configuration valid and authentication successful"
            
        except ImportError:
            return False, "Email libraries not available"
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed - check username/password"
        except smtplib.SMTPConnectError:
            return False, f"SMTP connection failed - check host/port ({self.settings.email_smtp_host}:{self.settings.email_smtp_port})"
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"
    
    async def _validate_file_permissions(self) -> Tuple[bool, str]:
        """Validate file system permissions and required directories."""
        try:
            issues = []
            
            # Check product CSV file
            product_path = Path(self.settings.product_csv_path)
            if not product_path.exists():
                issues.append(f"Product CSV file not found: {product_path}")
            elif not product_path.is_file():
                issues.append(f"Product CSV path is not a file: {product_path}")
            elif not product_path.stat().st_size > 0:
                issues.append(f"Product CSV file is empty: {product_path}")
            
            # Check required directories
            required_dirs = ["/app/logs", "/app/output", "/app/temp"]
            for dir_path in required_dirs:
                path = Path(dir_path)
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create directory {dir_path}: {str(e)}")
                elif not path.is_dir():
                    issues.append(f"Path exists but is not a directory: {dir_path}")
                
                # Test write permissions
                try:
                    test_file = path / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                except Exception as e:
                    issues.append(f"No write permission in {dir_path}: {str(e)}")
            
            if issues:
                return False, "; ".join(issues)
            
            return True, "All file permissions and directories are valid"
            
        except Exception as e:
            return False, f"File permission validation error: {str(e)}"
    
    async def _validate_gemini_connection(self) -> Tuple[bool, str]:
        """Validate Gemini API connection using OpenAI-compatible endpoint."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.settings.gemini_api_key,
                base_url=self.settings.openai_base_url
            )
            
            # Test basic connection with a simple completion
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10,
                timeout=10
            )
            
            # Test embeddings endpoint
            embed_response = await client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input="test embedding"
            )
            
            # Check Search Grounding availability if enabled
            search_grounding_status = ""
            if self.settings.enable_search_grounding:
                try:
                    import google.generativeai as genai
                    search_grounding_status = " | Search Grounding: Available"
                except ImportError:
                    search_grounding_status = " | Search Grounding: Package not installed (pip install google-generativeai>=0.7.0)"
            
            return True, f"✓ Chat: {response.model} | Embeddings: {embed_response.model}{search_grounding_status}"
            
        except Exception as e:
            return False, f"✗ Connection failed: {str(e)}"
    
    def print_validation_report(self) -> None:
        """Print a detailed validation report."""
        if not self.validation_results:
            print("❌ No validation results available. Run validate_all() first.")
            return
        
        print("\n" + "="*50)
        print("🔍 CONFIGURATION VALIDATION REPORT")
        print("="*50)
        
        overall_status = "✅ PASSED" if self.validation_results.get("overall_valid") else "❌ FAILED"
        print(f"Overall Status: {overall_status}")
        print()
        
        for check_name, result in self.validation_results.items():
            if check_name == "overall_valid":
                continue
                
            status = "✅" if result["valid"] else "❌"
            print(f"{status} {check_name.replace('_', ' ').title()}")
            print(f"   {result['details']}")
            print()
        
        if not self.validation_results.get("overall_valid"):
            print("🚨 SETUP REQUIRED:")
            print("1. Copy env.template to .env")
            print("2. Edit .env with your actual configuration values")
            print("3. Ensure all external services are running")
            print("4. Re-run validation")


async def validate_configuration() -> bool:
    """
    Convenience function to validate configuration.
    
    Returns:
        bool: True if all validations pass
    """
    validator = ConfigurationValidator()
    is_valid, results = await validator.validate_all()
    validator.print_validation_report()
    return is_valid


if __name__ == "__main__":
    # Allow running this module directly for configuration testing
    import asyncio
    
    async def main():
        await validate_configuration()
    
    asyncio.run(main()) 