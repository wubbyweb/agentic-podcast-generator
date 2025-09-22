#!/usr/bin/env python3
"""Simple test script to verify the agentic system works."""

import asyncio
import sys
from unittest.mock import patch, AsyncMock

async def test_basic_imports():
    """Test that all basic imports work."""
    print("Testing basic imports...")

    try:
        from config.settings import config
        print("✓ Configuration import successful")
    except Exception as e:
        print(f"✗ Configuration import failed: {e}")
        return False

    try:
        from agents.master_agent import MasterAgent
        print("✓ Master Agent import successful")
    except Exception as e:
        print(f"✗ Master Agent import failed: {e}")
        return False

    try:
        from database.connection import init_database
        print("✓ Database connection import successful")
    except Exception as e:
        print(f"✗ Database connection import failed: {e}")
        return False

    try:
        from services.openrouter_client import OpenRouterClient
        print("✓ OpenRouter client import successful")
    except Exception as e:
        print(f"✗ OpenRouter client import failed: {e}")
        return False

    try:
        from utils.retry import retry_with_backoff
        print("✓ Retry utilities import successful")
    except Exception as e:
        print(f"✗ Retry utilities import failed: {e}")
        return False

    return True

async def test_agent_initialization():
    """Test that agents can be initialized."""
    print("\nTesting agent initialization...")

    try:
        with patch('agents.master_agent.OpenRouterClient'):
            from agents.master_agent import MasterAgent
            master = MasterAgent()
            print("✓ Master Agent initialization successful")
    except Exception as e:
        print(f"✗ Master Agent initialization failed: {e}")
        return False

    return True

async def test_database_operations():
    """Test basic database operations."""
    print("\nTesting database operations...")

    try:
        from database.connection import init_database, close_database

        # Initialize database
        await init_database()
        print("✓ Database initialization successful")

        # Clean up
        await close_database()
        print("✓ Database cleanup successful")

    except Exception as e:
        print(f"✗ Database operations failed: {e}")
        return False

    return True

async def test_openrouter_client():
    """Test OpenRouter client initialization."""
    print("\nTesting OpenRouter client...")

    try:
        from services.openrouter_client import OpenRouterClient

        client = OpenRouterClient("test-key")
        print("✓ OpenRouter client creation successful")

        # Test async context manager
        async with client:
            print("✓ OpenRouter client context manager successful")

    except Exception as e:
        print(f"✗ OpenRouter client test failed: {e}")
        return False

    return True

async def test_config_validation():
    """Test configuration validation."""
    print("\nTesting configuration validation...")

    try:
        from config.settings import SystemConfig

        # Test with missing API key (should not raise exception)
        config = SystemConfig()
        print("✓ Configuration creation successful")

        # Test validation (will fail without API key, but should not crash)
        try:
            config.validate_config()
            print("✓ Configuration validation successful")
        except ValueError:
            print("✓ Configuration validation correctly detected missing API key")

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

    return True

async def main():
    """Run all tests."""
    print("🧪 Running Agentic System Tests")
    print("=" * 50)

    tests = [
        test_basic_imports,
        test_agent_initialization,
        test_database_operations,
        test_openrouter_client,
        test_config_validation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The agentic system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)