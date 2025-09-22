"""Tests for utility functions."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from utils.retry import retry_with_backoff, retry_sync_with_backoff, CircuitBreaker

class TestRetryDecorator:
    """Test retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test successful function call with no retries needed."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff_eventual_success(self):
        """Test function that fails initially but succeeds on retry."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff_exhaust_retries(self):
        """Test function that exhausts all retries."""
        call_count = 0

        @retry_with_backoff(max_retries=2)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await test_function()

        assert call_count == 3  # initial call + 2 retries

    @pytest.mark.asyncio
    async def test_retry_with_backoff_custom_exceptions(self):
        """Test retry with custom exception types."""
        call_count = 0

        @retry_with_backoff(max_retries=2, exceptions=(ValueError,))
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Value error")

        with pytest.raises(ValueError, match="Value error"):
            await test_function()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_ignored_exception(self):
        """Test that non-matching exceptions are not retried."""
        call_count = 0

        @retry_with_backoff(max_retries=2, exceptions=(ValueError,))
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise TypeError("Type error")

        with pytest.raises(TypeError, match="Type error"):
            await test_function()

        assert call_count == 1  # No retries for non-matching exception

    def test_retry_sync_with_backoff_success(self):
        """Test synchronous retry decorator."""
        call_count = 0

        @retry_sync_with_backoff(max_retries=2)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = test_function()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff_jitter(self):
        """Test retry with jitter enabled."""
        call_count = 0

        @retry_with_backoff(max_retries=2, jitter=True)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        with patch('asyncio.sleep') as mock_sleep:
            result = await test_function()

            assert result == "success"
            # Verify sleep was called with jittered values
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff_custom_delays(self):
        """Test retry with custom delay parameters."""
        call_count = 0

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2
        )
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        with patch('asyncio.sleep') as mock_sleep:
            start_time = asyncio.get_event_loop().time()
            result = await test_function()
            end_time = asyncio.get_event_loop().time()

            assert result == "success"
            # Verify delays were applied
            assert mock_sleep.call_count == 2

class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker()

        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.expected_exception == Exception
        assert cb.failure_count == 0
        assert cb.state == 'CLOSED'
        assert cb.last_failure_time is None

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker()

        assert cb._can_attempt() is True

    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trigger failure
        cb._record_failure()
        assert cb.state == 'OPEN'
        assert cb._can_attempt() is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trigger failure
        cb._record_failure()
        assert cb.state == 'OPEN'

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        assert cb._can_attempt() is True
        assert cb.state == 'HALF_OPEN'

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_recovery(self):
        """Test circuit breaker recovery after successful call."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trigger failure and wait for half-open
        cb._record_failure()
        await asyncio.sleep(0.2)

        # Record success
        cb._record_success()

        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_in_half_open(self):
        """Test circuit breaker failure while in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trigger failure and wait for half-open
        cb._record_failure()
        await asyncio.sleep(0.2)
        assert cb.state == 'HALF_OPEN'

        # Record another failure
        cb._record_failure()

        assert cb.state == 'OPEN'

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_success(self):
        """Test successful circuit breaker call."""
        cb = CircuitBreaker()

        async def success_function():
            return "success"

        result = await cb.call(success_function)

        assert result == "success"
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_failure(self):
        """Test failed circuit breaker call."""
        cb = CircuitBreaker(failure_threshold=1)

        async def failure_function():
            raise Exception("Test failure")

        with pytest.raises(Exception, match="Test failure"):
            await cb.call(failure_function)

        assert cb.state == 'OPEN'
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_blocks_calls(self):
        """Test that open circuit breaker blocks calls."""
        cb = CircuitBreaker(failure_threshold=1)

        # Trigger failure to open circuit
        async def failure_function():
            raise Exception("Test failure")

        with pytest.raises(Exception):
            await cb.call(failure_function)

        # Now calls should be blocked
        async def success_function():
            return "success"

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(success_function)