"""Configuration management system."""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModelConfig:
    """Configuration for OpenRouter models"""
    name: str
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: int = 30

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    model: ModelConfig
    max_retries: int = 3
    tools: Optional[list] = None

class SystemConfig:
    """Main system configuration"""

    def __init__(self):
        self.load_from_env()
        self.setup_models()
        self.setup_agents()

    def load_from_env(self):
        """Load configuration from environment variables"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agentic_system.db")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "120"))

        # Optional API keys (not currently used)
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.bing_api_key = os.getenv("BING_API_KEY")

        # Web scraping config (legacy - not currently used)
        self.user_agent = os.getenv("USER_AGENT", "AgenticSystem/1.0.0")
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.request_delay = float(os.getenv("REQUEST_DELAY", "1.0"))

    def setup_models(self):
        """Configure OpenRouter models - matches actual usage in the system"""
        self.models = {
            "master": ModelConfig(
                name=os.getenv("MASTER_MODEL", "perplexity/sonar"),  # Perplexity AI for research
                max_tokens=4000,
                temperature=0.3  # Lower temperature for research accuracy
            ),
            "research": ModelConfig(
                name=os.getenv("RESEARCH_MODEL", "perplexity/sonar"),  # Perplexity AI for research
                max_tokens=8000,
                temperature=0.3
            ),
            "keyword": ModelConfig(
                name=os.getenv("KEYWORD_MODEL", "google/gemini-2.0-flash-001"),  # Actual model used
                max_tokens=2000,
                temperature=0.5
            ),
            "post": ModelConfig(
                name=os.getenv("POST_MODEL", "xai/grok-3-mini"),  # Actual model used
                max_tokens=1000,
                temperature=0.8  # Higher temperature for creative content
            ),
            "dialog": ModelConfig(
                name=os.getenv("DIALOG_MODEL", "xai/grok-3-mini"),  # Actual model used
                max_tokens=3000,
                temperature=0.9  # Higher temperature for conversational content
            )
        }

    def setup_agents(self):
        """Configure agent-specific settings - matches actual system architecture"""
        self.agents = {
            "master": AgentConfig(
                name="master",
                model=self.models["master"],
                max_retries=self.max_retries
            ),
            # Note: Web researcher agent exists but is not used in current workflow
            "web_researcher": AgentConfig(
                name="web_researcher",
                model=self.models["research"],
                max_retries=self.max_retries,
                tools=["web_search", "scrape_webpage", "analyze_content"]
            ),
            "keyword_generator": AgentConfig(
                name="keyword_generator",
                model=self.models["keyword"],
                max_retries=self.max_retries
            ),
            "post_generator": AgentConfig(
                name="post_generator",
                model=self.models["post"],
                max_retries=self.max_retries
            ),
            "voice_dialog": AgentConfig(
                name="voice_dialog",
                model=self.models["dialog"],
                max_retries=self.max_retries
            )
        }

    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        return True

    def get_model_config(self, agent_name: str) -> ModelConfig:
        """Get model configuration for a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        return self.agents[agent_name].model

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get full agent configuration"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        return self.agents[agent_name]

# Global configuration instance
config = SystemConfig()