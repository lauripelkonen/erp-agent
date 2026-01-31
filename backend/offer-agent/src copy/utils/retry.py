"""
Retry and resilience utilities for external service calls.
Provides configurable retry logic with exponential backoff.
"""

import asyncio
import time
import functools
from typing import Callable, Any, Type, Tuple, List, Optional
from dataclasses import dataclass
import logging
from contextlib import contextmanager

from src.utils.exceptions import ExternalServiceError, BaseOfferAutomationError


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        ExternalServiceError,
    )


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for retry attempt with exponential backoff.
    
    Args:
        attempt: Current attempt number (1-based)
        config: Retry configuration
    
    Returns:
        float: Delay in seconds
    """
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add random jitter (±20% of delay)
        import random
        jitter_amount = delay * 0.2
        delay += random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)


def retry_on_exception(
    config: RetryConfig = None,
    logger: logging.Logger = None
):
    """
    Decorator for retrying function calls on specific exceptions.
    
    Args:
        config: Retry configuration
        logger: Logger for retry attempts
    
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}: {e}"
                        )
                        break
                    
                    # Calculate delay and wait
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator


def async_retry_on_exception(
    config: RetryConfig = None,
    logger: logging.Logger = None
):
    """
    Async decorator for retrying function calls on specific exceptions.
    
    Args:
        config: Retry configuration
        logger: Logger for retry attempts
    
    Returns:
        Decorated async function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}: {e}"
                        )
                        break
                    
                    # Calculate delay and wait
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before testing service recovery
            expected_exception: Exception type to consider as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def can_execute(self) -> bool:
        """Check if request can be executed based on circuit state."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            # Check if recovery timeout has passed
            if (
                self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("Circuit breaker closed - service recovered")
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.logger.warning("Circuit breaker opened again - service still failing")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(
                f"Circuit breaker opened - {self.failure_count} failures exceeded threshold"
            )
    
    def __call__(self, func: Callable) -> Callable:
        """Use circuit breaker as decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise ExternalServiceError(
                    f"Circuit breaker is OPEN for {func.__name__}",
                    context={'circuit_state': self.state, 'failure_count': self.failure_count}
                )
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise
        
        return wrapper


@contextmanager
def timeout_context(seconds: float):
    """
    Context manager for setting operation timeout.
    
    Args:
        seconds: Timeout in seconds
    
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the timeout handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))
    
    try:
        yield
    finally:
        # Restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def acquire(self) -> bool:
        """
        Try to acquire permission for API call.
        
        Returns:
            bool: True if call is allowed, False if rate limited
        """
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we can make a new call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        else:
            self.logger.warning(f"Rate limit exceeded: {len(self.calls)} calls in {self.time_window}s window")
            return False
    
    def wait_time(self) -> float:
        """
        Calculate time to wait before next call is allowed.
        
        Returns:
            float: Wait time in seconds
        """
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))


# Pre-configured retry configurations for different services
LEMONSOFT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=(ConnectionError, TimeoutError, ExternalServiceError)
)

OPENAI_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=60.0,
    retryable_exceptions=(ConnectionError, TimeoutError, ExternalServiceError)
)

WEB_SEARCH_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.5,
    max_delay=20.0,
    retryable_exceptions=(ConnectionError, TimeoutError, ExternalServiceError)
)

EMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=5.0,
    max_delay=60.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)

# Pre-configured retry settings for external APIs
EXTERNAL_API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        ExternalServiceError,
    )
) 