"""Tests for configuration management system."""

import pytest
import os
from unittest.mock import patch, Mock

from config.settings import SystemConfig, ModelConfig, AgentConfig

class TestModelConfig:
    """Test ModelConfig class."""

    def test_model_config_creation(self):
        """Test creating a ModelConfig instance."""
        config = ModelConfig(
            name="openai/gpt-4",
            max_tokens=2000,
            temperature=0.7,
            top_p=1.0,
            timeout=30
        )

        assert config.name == "openai/gpt-4"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.top_p == 1.0
        assert config.timeout == 30

    def test_model_config_defaults(self):
        """Test ModelConfig with default values."""
        config = ModelConfig(name="test-model")

        assert config.name == "test-model"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.top_p == 1.0
        assert config.timeout == 30

class TestAgentConfig:
    """Test AgentConfig class."""

    def test_agent_config_creation(self):
        """Test creating an AgentConfig instance."""
        model_config = ModelConfig(name="test-model")
        agent_config = AgentConfig(
            name="test-agent",
            model=model_config,
            max_retries=5,
            tools=["tool1", "tool2"]
        )

        assert agent_config.name == "test-agent"
        assert agent_config.model == model_config
        assert agent_config.max_retries == 5
        assert agent_config.tools == ["tool1", "tool2"]

    def test_agent_config_defaults(self):
        """Test AgentConfig with default values."""
        model_config = ModelConfig(name="test-model")
        agent_config = AgentConfig(name="test-agent", model=model_config)

        assert agent_config.name == "test-agent"
        assert agent_config.model == model_config
        assert agent_config.max_retries == 3
        assert agent_config.tools is None

class TestSystemConfig:
    """Test SystemConfig class."""

    @patch.dict(os.environ, {
        "OPENROUTER_API_KEY": "test-api-key",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "LOG_LEVEL": "DEBUG",
        "MAX_RETRIES": "5",
        "TIMEOUT_SECONDS": "60",
        "MASTER_MODEL": "perplexity/sonar",
        "RESEARCH_MODEL": "perplexity/sonar"
    })
    def test_system_config_with_env_vars(self):
        """Test SystemConfig loading from environment variables."""
        config = SystemConfig()

        assert config.openrouter_api_key == "test-api-key"
        assert config.database_url == "sqlite+aiosqlite:///./test.db"
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
        assert config.timeout_seconds == 60

    def test_system_config_defaults(self):
        """Test SystemConfig with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = SystemConfig()

            assert config.database_url == "sqlite+aiosqlite:///./agentic_system.db"
            assert config.log_level == "INFO"
            assert config.max_retries == 3
            assert config.timeout_seconds == 30

    def test_system_config_model_setup(self):
        """Test that models are properly configured."""
        config = SystemConfig()

        assert "master" in config.models
        assert "research" in config.models
        assert "keyword" in config.models
        assert "post" in config.models
        assert "dialog" in config.models

        # Check master model configuration
        master_model = config.models["master"]
        assert master_model.name == "perplexity/sonar"
        assert master_model.max_tokens == 4000
        assert master_model.temperature == 0.7

    def test_system_config_agent_setup(self):
        """Test that agents are properly configured."""
        config = SystemConfig()

        assert "master" in config.agents
        assert "web_researcher" in config.agents
        assert "keyword_generator" in config.agents
        assert "post_generator" in config.agents
        assert "voice_dialog" in config.agents

        # Check master agent configuration
        master_agent = config.agents["master"]
        assert master_agent.name == "master"
        assert master_agent.max_retries == 3

    def test_get_model_config(self):
        """Test getting model configuration by agent name."""
        config = SystemConfig()

        model_config = config.get_model_config("master")
        assert isinstance(model_config, ModelConfig)
        assert model_config.name == "perplexity/sonar"

    def test_get_model_config_invalid_agent(self):
        """Test getting model config for invalid agent."""
        config = SystemConfig()

        with pytest.raises(ValueError, match="Unknown agent: invalid_agent"):
            config.get_model_config("invalid_agent")

    def test_get_agent_config(self):
        """Test getting agent configuration."""
        config = SystemConfig()

        agent_config = config.get_agent_config("master")
        assert isinstance(agent_config, AgentConfig)
        assert agent_config.name == "master"

    def test_get_agent_config_invalid_agent(self):
        """Test getting agent config for invalid agent."""
        config = SystemConfig()

        with pytest.raises(ValueError, match="Unknown agent: invalid_agent"):
            config.get_agent_config("invalid_agent")

    def test_config_validation_with_api_key(self):
        """Test config validation with API key."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            config = SystemConfig()
            # Should not raise an exception
            assert config.validate_config() is True

    def test_config_validation_without_api_key(self):
        """Test config validation without API key."""
        with patch.dict(os.environ, {}, clear=True):
            config = SystemConfig()

            with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
                config.validate_config()

    @patch.dict(os.environ, {
        "OPENROUTER_API_KEY": "test-key",
        "GOOGLE_API_KEY": "google-key",
        "GOOGLE_CSE_ID": "cse-id",
        "BING_API_KEY": "bing-key"
    })
    def test_optional_api_keys(self):
        """Test optional API key configuration."""
        config = SystemConfig()

        assert config.google_api_key == "google-key"
        assert config.google_cse_id == "cse-id"
        assert config.bing_api_key == "bing-key"

    def test_web_scraping_config(self):
        """Test web scraping configuration."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-key",
            "USER_AGENT": "CustomAgent/1.0",
            "MAX_CONCURRENT_REQUESTS": "20",
            "REQUEST_DELAY": "2.5"
        }):
            config = SystemConfig()

            assert config.user_agent == "CustomAgent/1.0"
            assert config.max_concurrent_requests == 20
            assert config.request_delay == 2.5