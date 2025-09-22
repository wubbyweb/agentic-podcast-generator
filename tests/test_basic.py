"""Basic tests for the agentic system."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from config.settings import config
from agents.master_agent import MasterAgent
from database.connection import init_database, close_database

class TestBasicFunctionality:
    """Basic functionality tests."""

    def test_config_validation(self):
        """Test that configuration validation works."""
        # This should not raise an exception even without API key
        # (we'll mock it in actual tests)
        assert hasattr(config, 'openrouter_api_key')

    def test_master_agent_initialization(self):
        """Test that Master Agent can be initialized."""
        # Mock the OpenRouter client to avoid API calls
        with patch('agents.master_agent.OpenRouterClient'):
            master = MasterAgent()
            assert master.name == "master"
            assert hasattr(master, 'execute')

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database initialization."""
        try:
            await init_database()
            # If we get here without exception, database init worked
            assert True
        finally:
            await close_database()

    def test_import_all_modules(self):
        """Test that all main modules can be imported."""
        try:
            from agents import BaseAgent, MasterAgent
            from agents.sub_agents import WebResearcher, KeywordGenerator, PostGenerator, VoiceDialogGenerator
            from config import Config
            from database import init_database, get_db_session
            from services import OpenRouterClient, setup_logging
            from utils import retry_with_backoff

            # If we get here, all imports worked
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

class TestAgentCommunication:
    """Test agent communication patterns."""

    @pytest.mark.asyncio
    async def test_agent_execution_flow(self):
        """Test the basic agent execution flow."""
        # This is a high-level integration test
        # In a real scenario, you'd mock the OpenRouter API

        with patch('agents.master_agent.OpenRouterClient') as mock_client:
            # Mock the OpenRouter client
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__ = Mock(return_value=mock_instance)
            mock_instance.__aexit__ = Mock(return_value=None)

            # Mock the API response
            mock_response = {
                "choices": [{
                    "message": {
                        "content": '{"themes": ["test"], "audience": "general", "goals": ["inform"], "research_directions": ["web"], "style": "casual"}'
                    }
                }],
                "usage": {"total_tokens": 100}
            }
            mock_instance.chat_completion = Mock(return_value=mock_response)

            # Test Master Agent execution
            master = MasterAgent()

            # This would normally call OpenRouter, but we're mocking it
            # result = await master.execute({"topic": "Test Topic"})

            # For now, just test that the agent can be created
            assert master.name == "master"

if __name__ == "__main__":
    # Run basic smoke test
    print("Running basic functionality tests...")

    # Test imports
    try:
        from config.settings import config
        print("✓ Configuration import successful")
    except Exception as e:
        print(f"✗ Configuration import failed: {e}")

    try:
        from agents.master_agent import MasterAgent
        print("✓ Master Agent import successful")
    except Exception as e:
        print(f"✗ Master Agent import failed: {e}")

    try:
        from database.connection import init_database
        print("✓ Database connection import successful")
    except Exception as e:
        print(f"✗ Database connection import failed: {e}")

    print("Basic smoke test completed!")