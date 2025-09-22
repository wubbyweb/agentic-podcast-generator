"""Retry mechanisms and error handling utilities."""

import asyncio
import functools
from typing import Callable, Any, Type, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    jitter: bool = True
):
    """Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        exceptions: Tuple of exceptions to catch and retry
        jitter: Whether to add random jitter to delay
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    start_time = datetime.utcnow()
                    result = await func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                    if attempt > 0:
                        logger.info(
                            f"Operation {func.__name__} succeeded on attempt {attempt + 1} "
                            f"after {duration:.2f}ms"
                        )

                    return result

                except exceptions as e:
                    last_exception = e
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                    if attempt == max_retries:
                        logger.error(
                            f"Operation {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {e}"
                        )
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

def retry_sync_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    jitter: bool = True
):
    """Synchronous version of retry_with_backoff decorator."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    start_time = datetime.utcnow()
                    result = func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                    if attempt > 0:
                        logger.info(
                            f"Operation {func.__name__} succeeded on attempt {attempt + 1} "
                            f"after {duration:.2f}ms"
                        )

                    return result

                except exceptions as e:
                    last_exception = e
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                    if attempt == max_retries:
                        logger.error(
                            f"Operation {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {e}"
                        )
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    import time
                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def _can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if self.state == 'CLOSED':
            return True

        if self.state == 'OPEN':
            if self.last_failure_time and \
               (datetime.utcnow() - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False

        return True  # HALF_OPEN state

    def _record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'

    def _record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self._can_attempt():
            raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise e