"""OpenRouter API client with retry logic and model management."""

import aiohttp
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from config.settings import config
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for OpenRouter API with retry logic and model management."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=config.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": config.user_agent
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @retry_with_backoff(max_retries=config.max_retries)
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send chat completion request to OpenRouter.

        Args:
            model: Model name (e.g., 'openai/gpt-4')
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter

        Returns:
            API response dictionary
        """

        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        # Build request payload
        payload = {
            "model": model,
            "messages": messages
        }

        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        logger.debug(f"Sending request to {model} with {len(messages)} messages")

        start_time = datetime.utcnow()

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()

                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(
                    f"OpenRouter API call completed in {duration:.2f}ms "
                    f"(model: {model}, tokens: {result.get('usage', {}).get('total_tokens', 'N/A')})"
                )

                return result

        except aiohttp.ClientError as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"OpenRouter API call failed after {duration:.2f}ms: {e}"
            )
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from OpenRouter."""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        async with self.session.get(f"{self.base_url}/models") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("data", [])

    def extract_response_content(self, response: Dict[str, Any]) -> str:
        """Extract content from OpenRouter API response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            raise ValueError("Invalid response format from OpenRouter API")

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenRouter API response."""
        try:
            message = response["choices"][0]["message"]
            return message.get("tool_calls", [])
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract tool calls from response: {e}")
            return []

    def get_usage_info(self, response: Dict[str, Any]) -> Dict[str, int]:
        """Extract token usage information from response."""
        try:
            usage = response.get("usage", {})
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        except Exception as e:
            logger.warning(f"Failed to extract usage info: {e}")
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async def validate_connection(self) -> bool:
        """Validate connection to OpenRouter API."""
        try:
            async with self:
                models = await self.list_models()
                return len(models) > 0
        except Exception as e:
            logger.error(f"OpenRouter connection validation failed: {e}")
            return False