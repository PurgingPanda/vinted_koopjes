"""
Enhanced error handling and retry logic for Playwright-based scraping
"""
import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass


class BlockedError(ScrapingError):
    """Raised when scraper is blocked or detected"""
    pass


class CaptchaError(ScrapingError):
    """Raised when CAPTCHA is encountered"""
    pass


class RateLimitError(ScrapingError):
    """Raised when rate limited"""
    pass


class RetryableError(ScrapingError):
    """Base class for errors that should trigger retries"""
    pass


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for adding retry logic with exponential backoff
    
    :param max_retries: Maximum number of retry attempts
    :param base_delay: Base delay in seconds
    :param max_delay: Maximum delay in seconds
    :param exponential_base: Base for exponential backoff
    :param jitter: Add random jitter to delays
    :param retryable_exceptions: List of exceptions that should trigger retries
    """
    if retryable_exceptions is None:
        retryable_exceptions = [
            RetryableError,
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError
        ]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on non-retryable errors
                    if not any(isinstance(e, exc_type) for exc_type in retryable_exceptions):
                        logger.error(f"❌ Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Don't retry on final attempt
                    if attempt == max_retries:
                        logger.error(f"❌ Final retry failed for {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    logger.warning(
                        f"⚠️ Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, convert to async and run
            if asyncio.iscoroutinefunction(func):
                raise ValueError("Cannot apply sync retry to async function")
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on non-retryable errors
                    if not any(isinstance(e, exc_type) for exc_type in retryable_exceptions):
                        logger.error(f"❌ Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Don't retry on final attempt
                    if attempt == max_retries:
                        logger.error(f"❌ Final retry failed for {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    logger.warning(
                        f"⚠️ Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def classify_error(exception: Exception, response_text: str = "", status_code: int = 0) -> Exception:
    """
    Classify errors into specific error types for better handling
    
    :param exception: The original exception
    :param response_text: Response text/content for analysis
    :param status_code: HTTP status code if available
    :return: Classified exception
    """
    error_msg = str(exception).lower()
    response_lower = response_text.lower()
    
    # Check for blocking/detection indicators
    blocking_indicators = [
        'blocked', 'bot', 'automated', 'suspicious', 'access denied', 
        'forbidden', 'not allowed', 'security', 'detected'
    ]
    
    if (status_code == 403 or 
        any(indicator in error_msg or indicator in response_lower for indicator in blocking_indicators)):
        return BlockedError(f"Access blocked or detected: {exception}")
    
    # Check for CAPTCHA
    captcha_indicators = ['captcha', 'recaptcha', 'challenge', 'verify']
    if any(indicator in error_msg or indicator in response_lower for indicator in captcha_indicators):
        return CaptchaError(f"CAPTCHA challenge detected: {exception}")
    
    # Check for rate limiting
    rate_limit_indicators = ['rate limit', 'too many requests', 'throttle', 'slow down']
    if (status_code == 429 or 
        any(indicator in error_msg or indicator in response_lower for indicator in rate_limit_indicators)):
        return RateLimitError(f"Rate limited: {exception}")
    
    # Check for network/connection issues (retryable)
    network_indicators = [
        'connection', 'timeout', 'network', 'dns', 'resolve', 'unreachable',
        'connection reset', 'connection refused', 'temporarily unavailable'
    ]
    if any(indicator in error_msg for indicator in network_indicators):
        return RetryableError(f"Network error (retryable): {exception}")
    
    # Check for server errors (retryable)
    if 500 <= status_code < 600:
        return RetryableError(f"Server error (retryable): {exception}")
    
    # Return original exception for non-classified errors
    return exception


class ErrorHandler:
    """Centralized error handling for scraping operations"""
    
    def __init__(self):
        self.error_counts = {}
        self.blocked_until = None
    
    def handle_error(self, error: Exception, context: str = "") -> Exception:
        """
        Handle and classify errors, updating internal state
        
        :param error: The error to handle
        :param context: Additional context about where the error occurred
        :return: Classified error
        """
        classified_error = classify_error(error)
        
        # Log the error with context
        error_type = type(classified_error).__name__
        logger.error(f"❌ {error_type} in {context}: {classified_error}")
        
        # Track error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Handle blocking scenarios
        if isinstance(classified_error, BlockedError):
            # Set blocked state for some time
            self.blocked_until = time.time() + 1800  # 30 minutes
            logger.warning("🚫 Setting blocked state for 30 minutes")
        
        elif isinstance(classified_error, CaptchaError):
            # CAPTCHA requires immediate attention
            self.blocked_until = time.time() + 3600  # 1 hour
            logger.warning("🧩 CAPTCHA detected - setting blocked state for 1 hour")
        
        elif isinstance(classified_error, RateLimitError):
            # Rate limit requires backing off
            self.blocked_until = time.time() + 900  # 15 minutes
            logger.warning("🐌 Rate limited - backing off for 15 minutes")
        
        return classified_error
    
    def is_blocked(self) -> bool:
        """Check if we're currently in a blocked state"""
        if self.blocked_until is None:
            return False
        
        if time.time() >= self.blocked_until:
            logger.info("✅ Blocked state expired, resuming operations")
            self.blocked_until = None
            return False
        
        return True
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()
    
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_counts.clear()
        logger.info("📊 Error statistics reset")


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_scraping_error(error: Exception, context: str = "") -> Exception:
    """
    Convenience function for handling scraping errors
    
    :param error: The error to handle
    :param context: Context about where the error occurred
    :return: Classified error
    """
    return global_error_handler.handle_error(error, context)


def is_scraping_blocked() -> bool:
    """Check if scraping is currently blocked"""
    return global_error_handler.is_blocked()


def get_scraping_error_stats() -> Dict[str, int]:
    """Get current scraping error statistics"""
    return global_error_handler.get_error_stats()