"""
Logging infrastructure for the Offer Automation System.
Provides structured logging, audit trails, and error tracking.
"""

import logging
import logging.handlers
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

import structlog
from structlog.types import FilteringBoundLogger

from src.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add process/thread info for debugging
        log_entry['process_id'] = record.process
        log_entry['thread_id'] = record.thread
        
        return json.dumps(log_entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Enhanced text formatter with colors and structured info."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and structure."""
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Base format
        formatted = f"{color}[{record.levelname}]{reset} "
        formatted += f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} "
        formatted += f"| {record.name} | {record.getMessage()}"
        
        # Add extra context if available
        if hasattr(record, 'extra_fields'):
            extra_str = " | ".join([f"{k}={v}" for k, v in record.extra_fields.items()])
            formatted += f" | {extra_str}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class AuditLogger:
    """Simplified audit logger for business process tracking."""
    
    def __init__(self, logger_name: str = "offer_automation.audit"):
        """Initialize audit logger."""
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, extra: dict = None):
        """Log info message (for compatibility)."""
        self.logger.info(message)
    
    def warning(self, message: str, extra: dict = None):
        """Log warning message (for compatibility)."""
        self.logger.warning(message)
    
    def error(self, message: str, extra: dict = None):
        """Log error message (for compatibility)."""
        self.logger.error(message)
    

    
    def log_process_start(self, request_id: str, email_content: str, attachments: list = None):
        """Log the start of offer automation process."""
        attachment_count = len(attachments) if attachments else 0
        self.logger.info(f"Process started - ID: {request_id}, Email length: {len(email_content)}, Attachments: {attachment_count}")
    
    def log_customer_lookup(self, request_id: str, search_term: str, result: dict, method: str = "primary"):
        """Log customer lookup attempts and results."""
        success = bool(result)
        customer_name = result.get('customer_name') if result else 'None'
        self.logger.info(f"Customer lookup - Term: {search_term}, Method: {method}, Success: {success}, Found: {customer_name}")
    
    def log_product_identification(self, request_id: str, product_request: str, products_found: list, method: str = "rag"):
        """Log product identification results."""
        products_count = len(products_found)
        self.logger.info(f"Product identification - Method: {method}, Products found: {products_count}")
    
    def log_offer_creation(self, request_id: str, offer_data: dict):
        """Log offer creation in Lemonsoft."""
        offer_number = offer_data.get('offer_number', 'Unknown')
        total_amount = offer_data.get('total_amount', 0)
        self.logger.info(f"Offer created - Number: {offer_number}, Total: EUR{total_amount}")
    
    def log_api_call(self, request_id: str, service: str, endpoint: str, method: str, status_code: int, duration: float):
        """Log external API calls."""
        duration_ms = round(duration * 1000, 2)
        success = 200 <= status_code < 300
        self.logger.info(f"API call - {service} {method} {endpoint}, Status: {status_code}, Duration: {duration_ms}ms, Success: {success}")
    
    def log_error(self, request_id: str, error_type: str, error_message: str, context: dict = None):
        """Log errors with context."""
        self.logger.error(f"Error - Type: {error_type}, Message: {error_message}")
    
    def log_process_completion(self, request_id: str, success: bool, duration: float, result: dict = None):
        """Log process completion."""
        duration_seconds = round(duration, 2)
        self.logger.info(f"Process completed - Success: {success}, Duration: {duration_seconds}s")



def setup_logging() -> logging.Logger:
    """
    Set up simplified logging infrastructure for the application.
    
    Returns:
        logging.Logger: Configured root logger
    """
    import os
    import codecs
    
    # Fix Unicode/emoji support on Windows
    if os.name == 'nt':  # Windows
        try:
            # Set console to UTF-8 mode to support emojis
            os.system('chcp 65001 > nul')
            # Reconfigure stdout to handle UTF-8
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Fallback: wrap stdout/stderr with UTF-8 codec
            try:
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
            except Exception:
                pass  # If all fails, continue without emoji support
    
    settings = get_settings()
    
    # Create logs directory
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Unicode-safe console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # Unicode-safe formatter
    class UnicodeFormatter(logging.Formatter):
        def format(self, record):
            try:
                # Standard formatting
                result = super().format(record)
                # Ensure the result is properly encoded
                if isinstance(result, bytes):
                    result = result.decode('utf-8', errors='replace')
                return result
            except UnicodeEncodeError:
                # Fallback: remove non-ASCII characters
                result = super().format(record)
                return result.encode('ascii', errors='replace').decode('ascii')
    
    # Simple format: LEVEL | logger_name | message
    unicode_formatter = UnicodeFormatter('%(levelname)s | %(name)s | %(message)s')
    console_handler.setFormatter(unicode_formatter)
    
    # Add only console handler for now
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING) 
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging system initialized - Level: {settings.log_level}")
    
    return root_logger


@contextmanager
def log_api_call(service: str, endpoint: str, method: str = "GET", request_id: str = None):
    """
    Context manager for logging API calls with timing.
    
    Usage:
        with log_api_call("lemonsoft", "/api/offers", "POST") as log_ctx:
            response = make_api_call()
            log_ctx.set_status(response.status_code)
    """
    start_time = datetime.utcnow()
    audit_logger = AuditLogger()
    
    class LogContext:
        def __init__(self):
            self.status_code = None
            self.error = None
        
        def set_status(self, status_code: int):
            self.status_code = status_code
        
        def set_error(self, error: Exception):
            self.error = error
    
    log_ctx = LogContext()
    
    try:
        yield log_ctx
    finally:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        if log_ctx.error:
            audit_logger.log_error(
                request_id or "unknown",
                "api_error",
                str(log_ctx.error),
                {
                    'service': service,
                    'endpoint': endpoint,
                    'method': method,
                    'duration': duration
                }
            )
        else:
            audit_logger.log_api_call(
                request_id or "unknown",
                service,
                endpoint,
                method,
                log_ctx.status_code or 0,
                duration
            )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    return logging.getLogger(name)


def get_audit_logger() -> AuditLogger:
    """Get the audit logger instance."""
    return AuditLogger() 