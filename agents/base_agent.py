"""Base Agent class with common functionality."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import config
from database.connection import log_agent_action, log_agent_handoff
from services.openrouter_client import OpenRouterClient
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, model_config_name: str):
        self.name = name
        self.model_config = config.get_model_config(model_config_name)
        self.logger = logging.getLogger(f"agent.{name}")
        self.session_id: Optional[int] = None
        self.openrouter: Optional[OpenRouterClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.openrouter = OpenRouterClient(config.openrouter_api_key)
        await self.openrouter.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.openrouter:
            await self.openrouter.__aexit__(exc_type, exc_val, exc_tb)

    async def log_action(
        self,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log agent action to database and console."""
        if not self.session_id:
            self.logger.warning("No session ID set for logging")
            return

        # Serialize data for storage
        input_json = json.dumps(input_data) if input_data else None
        output_json = json.dumps(output_data) if output_data else None

        # Calculate duration if available
        duration_ms = None
        if hasattr(self, '_action_start_time'):
            duration_ms = int((datetime.utcnow() - self._action_start_time).total_seconds() * 1000)

        # Log to database
        await log_agent_action(
            session_id=self.session_id,
            agent_name=self.name,
            action=action,
            input_data=input_json,
            output_data=output_json,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )

        # Log to console
        status = "SUCCESS" if success else "FAILED"
        duration_str = f" ({duration_ms}ms)" if duration_ms else ""
        self.logger.info(f"[{status}] {action}{duration_str}")

        if error_message:
            self.logger.error(f"Error in {action}: {error_message}")

    async def handoff_to(
        self,
        target_agent: str,
        action: str,
        payload: Dict[str, Any]
    ) -> None:
        """Handle communication with other agents."""
        if not self.session_id:
            self.logger.warning("No session ID set for handoff logging")
            return

        # Log the handoff
        payload_json = json.dumps(payload)
        await log_agent_handoff(
            session_id=self.session_id,
            from_agent=self.name,
            to_agent=target_agent,
            action=action,
            payload=payload_json
        )

        # Log to console
        self.logger.info(f"HANDOFF → {target_agent}: {action}")

    @retry_with_backoff(max_retries=config.max_retries)
    async def call_openrouter(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make a call to OpenRouter API with retry logic."""
        if not self.openrouter:
            raise RuntimeError("OpenRouter client not initialized")

        # Use agent-specific model configuration
        model = self.model_config.name

        # Override with provided parameters if specified
        if temperature is None:
            temperature = self.model_config.temperature
        if max_tokens is None:
            max_tokens = self.model_config.max_tokens

        return await self.openrouter.chat_completion(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def execute_with_logging(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary function with comprehensive logging."""
        self._action_start_time = datetime.utcnow()

        try:
            # Log action start
            await self.log_action("execute_start", input_data=input_data)

            # Execute the main logic
            result = await self.execute(input_data)

            # Log successful completion
            await self.log_action("execute_complete", output_data=result)

            return result

        except Exception as e:
            # Log failure
            error_msg = str(e)
            await self.log_action(
                "execute_failed",
                input_data=input_data,
                success=False,
                error_message=error_msg
            )
            raise

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary function.

        Args:
            input_data: Input data for the agent

        Returns:
            Dictionary containing the agent's output
        """
        pass

    def validate_input(self, input_data: Dict[str, Any], required_keys: list) -> None:
        """Validate that required keys are present in input data."""
        missing_keys = [key for key in required_keys if key not in input_data]
        if missing_keys:
            raise ValueError(f"Missing required input keys: {missing_keys}")

    def create_system_message(self, system_prompt: str) -> Dict[str, str]:
        """Create a system message for OpenRouter API."""
        return {
            "role": "system",
            "content": system_prompt
        }

    def create_user_message(self, user_content: str) -> Dict[str, str]:
        """Create a user message for OpenRouter API."""
        return {
            "role": "user",
            "content": user_content
        }

    def create_assistant_message(self, assistant_content: str) -> Dict[str, str]:
        """Create an assistant message for OpenRouter API."""
        return {
            "role": "assistant",
            "content": assistant_content
        }

    def create_tool_message(self, tool_call_id: str, tool_result: str) -> Dict[str, str]:
        """Create a tool result message for OpenRouter API."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": tool_result
        }