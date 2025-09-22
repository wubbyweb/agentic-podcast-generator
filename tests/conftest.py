"""Pytest configuration and fixtures."""

import asyncio
import pytest
import os
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from config.settings import config
from database.connection import init_database, close_database
from services.logger import setup_logging

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """Set up test environment before running tests."""
    # Set up test logging
    setup_logging(level="WARNING")  # Reduce log noise during tests

    # Initialize test database
    await init_database()

    yield

    # Clean up
    await close_database()

@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Test response content",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@pytest.fixture
def mock_topic_analysis():
    """Mock topic analysis data."""
    return {
        "themes": ["artificial intelligence", "healthcare technology"],
        "audience": "healthcare professionals and tech enthusiasts",
        "goals": ["inform about AI applications", "discuss benefits and challenges"],
        "research_directions": ["current implementations", "case studies", "regulatory landscape"],
        "style": "professional yet accessible"
    }

@pytest.fixture
def mock_research_results():
    """Mock research results data."""
    return {
        "topic": "AI in Healthcare",
        "research_plan": {
            "search_queries": ["AI healthcare applications", "medical AI trends"],
            "source_types": ["academic", "industry"],
            "target_domains": ["edu", "org", "com"]
        },
        "results": [
            {
                "title": "AI Revolution in Healthcare",
                "url": "https://example.com/ai-healthcare",
                "content": "Artificial intelligence is transforming healthcare delivery...",
                "relevance_score": 0.85,
                "credibility_score": 0.8,
                "source": "example.com"
            }
        ],
        "summary": "AI is making significant impacts in healthcare diagnostics and treatment.",
        "total_sources": 1,
        "credibility_score": 0.8
    }

@pytest.fixture
def mock_keywords_data():
    """Mock keywords and hashtags data."""
    return {
        "topic": "AI in Healthcare",
        "keywords": [
            "artificial intelligence",
            "healthcare technology",
            "medical diagnostics",
            "AI in medicine",
            "digital health"
        ],
        "hashtags": [
            "#AIHealthcare",
            "#MedicalAI",
            "#DigitalHealth",
            "#HealthcareInnovation",
            "#AIinMedicine"
        ],
        "keyword_scores": {
            "artificial intelligence": 0.9,
            "healthcare technology": 0.8,
            "medical diagnostics": 0.7
        },
        "total_keywords": 5,
        "total_hashtags": 5,
        "categories": ["primary", "long_tail", "technical"]
    }

@pytest.fixture
def sample_linkedin_post():
    """Sample LinkedIn post content."""
    return """Excited to share some insights on how AI is revolutionizing healthcare! 🤖🏥

From diagnostic imaging that catches diseases earlier to personalized treatment plans that save lives, artificial intelligence is transforming patient care in ways we couldn't imagine just a few years ago.

Key trends I'm seeing:
• AI-powered diagnostic tools with 95%+ accuracy
• Predictive analytics for patient outcomes
• Drug discovery accelerated by machine learning
• Robotic surgery with unprecedented precision

The future of healthcare is here, and it's intelligent! What are your thoughts on AI's role in medicine?

#AIHealthcare #MedicalInnovation #DigitalTransformation"""

@pytest.fixture
def sample_voice_dialog():
    """Sample voice dialog script."""
    return """[Opening music fades in]

Host: Welcome to today's episode on the transformative power of artificial intelligence in healthcare!

You know, I'm really excited to dive into this topic because AI isn't just a buzzword anymore - it's actively saving lives and revolutionizing patient care.

Let me walk you through what I'm seeing in the industry right now...

[Content continues with natural, conversational delivery]"""

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    mock_config = Mock()
    mock_config.openrouter_api_key = "test-api-key"
    mock_config.database_url = "sqlite+aiosqlite:///./test.db"
    mock_config.log_level = "INFO"
    mock_config.max_retries = 3
    mock_config.timeout_seconds = 30
    mock_config.models = {
        "master": Mock(name="perplexity/sonar", max_tokens=4000, temperature=0.7),
        "research": Mock(name="perplexity/sonar", max_tokens=4000, temperature=0.3),
        "keyword": Mock(name="google/gemini-2.0-flash-001", max_tokens=2000, temperature=0.5),
        "post": Mock(name="xai/grok-3-mini", max_tokens=1000, temperature=0.8),
        "dialog": Mock(name="xai/grok-3-mini", max_tokens=3000, temperature=0.9)
    }
    return mock_config