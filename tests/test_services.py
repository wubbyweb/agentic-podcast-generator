"""Tests for service classes."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from services.openrouter_client import OpenRouterClient
from services.logger import setup_logging, get_agent_logger

class TestOpenRouterClient:
    """Test OpenRouter API client."""

    @pytest.fixture
    def client(self):
        """Create OpenRouter client instance."""
        return OpenRouterClient("test-api-key")

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager."""
        async with client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)

        assert client.session is None

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, client, mock_openrouter_response):
        """Test successful chat completion."""
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_openrouter_response
            mock_post.return_value = mock_response

            async with client:
                result = await client.chat_completion(
                    model="test-model",
                    messages=[{"role": "user", "content": "test"}]
                )

                assert result == mock_openrouter_response
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(self, client, mock_openrouter_response):
        """Test chat completion with tools."""
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_openrouter_response
            mock_post.return_value = mock_response

            tools = [{"type": "function", "function": {"name": "test_tool"}}]

            async with client:
                result = await client.chat_completion(
                    model="test-model",
                    messages=[{"role": "user", "content": "test"}],
                    tools=tools
                )

                # Verify tools were included in the request
                call_args = mock_post.call_args
                request_data = call_args[1]['json']
                assert 'tools' in request_data
                assert request_data['tools'] == tools

    @pytest.mark.asyncio
    async def test_chat_completion_with_parameters(self, client, mock_openrouter_response):
        """Test chat completion with custom parameters."""
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_openrouter_response
            mock_post.return_value = mock_response

            async with client:
                result = await client.chat_completion(
                    model="test-model",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.5,
                    max_tokens=100,
                    top_p=0.9
                )

                call_args = mock_post.call_args
                request_data = call_args[1]['json']
                assert request_data['temperature'] == 0.5
                assert request_data['max_tokens'] == 100
                assert request_data['top_p'] == 0.9

    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, client):
        """Test chat completion with API error."""
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = aiohttp.ClientError("API Error")
            mock_post.return_value = mock_response

            async with client:
                with pytest.raises(aiohttp.ClientError):
                    await client.chat_completion(
                        model="test-model",
                        messages=[{"role": "user", "content": "test"}]
                    )

    def test_extract_response_content(self, client, mock_openrouter_response):
        """Test extracting content from response."""
        content = client.extract_response_content(mock_openrouter_response)
        assert content == "Test response content"

    def test_extract_response_content_invalid(self, client):
        """Test extracting content from invalid response."""
        invalid_response = {"choices": []}

        with pytest.raises(ValueError):
            client.extract_response_content(invalid_response)

    def test_extract_tool_calls(self, client):
        """Test extracting tool calls from response."""
        response_with_tools = {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {"id": "call1", "function": {"name": "test_func"}}
                    ]
                }
            }]
        }

        tool_calls = client.extract_tool_calls(response_with_tools)
        assert len(tool_calls) == 1
        assert tool_calls[0]["id"] == "call1"

    def test_extract_tool_calls_no_tools(self, client, mock_openrouter_response):
        """Test extracting tool calls when none are present."""
        tool_calls = client.extract_tool_calls(mock_openrouter_response)
        assert tool_calls == []

    def test_get_usage_info(self, client, mock_openrouter_response):
        """Test extracting usage information."""
        usage = client.get_usage_info(mock_openrouter_response)

        assert usage["prompt_tokens"] == 10
        assert usage["completion_tokens"] == 20
        assert usage["total_tokens"] == 30

    def test_get_usage_info_missing(self, client):
        """Test extracting usage info from response without usage data."""
        response = {"choices": [{"message": {"content": "test"}}]}

        usage = client.get_usage_info(response)

        assert usage["prompt_tokens"] == 0
        assert usage["completion_tokens"] == 0
        assert usage["total_tokens"] == 0

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test listing available models."""
        mock_models = {"data": [{"id": "model1"}, {"id": "model2"}]}

        with patch.object(client.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_models
            mock_get.return_value = mock_response

            async with client:
                models = await client.list_models()

                assert models == [{"id": "model1"}, {"id": "model2"}]

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, client):
        """Test successful connection validation."""
        with patch.object(client, 'list_models') as mock_list:
            mock_list.return_value = [{"id": "model1"}]

            result = await client.validate_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, client):
        """Test failed connection validation."""
        with patch.object(client, 'list_models') as mock_list:
            mock_list.side_effect = Exception("Connection failed")

            result = await client.validate_connection()
            assert result is False

class TestLogger:
    """Test logging functionality."""

    def test_setup_logging(self):
        """Test logging setup."""
        # This should not raise an exception
        setup_logging(level="INFO")

    def test_get_agent_logger(self):
        """Test getting agent-specific logger."""
        logger = get_agent_logger("test_agent")

        assert logger is not None
        # The logger name should contain the agent name
        assert "test_agent" in str(logger)

    def test_get_agent_logger_multiple_calls(self):
        """Test that multiple calls return the same logger instance."""
        logger1 = get_agent_logger("test_agent")
        logger2 = get_agent_logger("test_agent")

        # They should be the same object (cached)
        assert logger1 is logger2

    @patch('services.logger.logging')
    def test_setup_logging_with_file(self, mock_logging):
        """Test logging setup with file output."""
        setup_logging(level="DEBUG", log_file="test.log")

        # Verify file handler was created
        mock_logging.FileHandler.assert_called_with("test.log")

    @patch('services.logger.logging')
    def test_setup_logging_custom_format(self, mock_logging):
        """Test logging setup with custom format."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(level="INFO", format_string=custom_format)

        # Verify formatter was created with custom format
        mock_logging.Formatter.assert_called_with(custom_format, datefmt="%Y-%m-%d %H:%M:%S")