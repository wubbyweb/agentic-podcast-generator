"""Tests for agent classes."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.base_agent import BaseAgent
from agents.master_agent import MasterAgent
from config.settings import ModelConfig

class TestBaseAgent:
    """Test BaseAgent class."""

    @pytest.fixture
    def model_config(self):
        """Create a mock model configuration."""
        return ModelConfig(
            name="test-model",
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.fixture
    def base_agent(self, model_config):
        """Create a BaseAgent instance."""
        with patch('agents.base_agent.OpenRouterClient'):
            agent = BaseAgent("test_agent", "master")
            return agent

    def test_base_agent_initialization(self, base_agent):
        """Test BaseAgent initialization."""
        assert base_agent.name == "test_agent"
        assert base_agent.session_id is None
        assert hasattr(base_agent, 'openrouter')

    @pytest.mark.asyncio
    async def test_context_manager(self, base_agent):
        """Test BaseAgent async context manager."""
        async with base_agent:
            assert base_agent.openrouter is not None

        # After exiting context, openrouter should be cleaned up
        assert base_agent.openrouter is None

    def test_validate_input_success(self, base_agent):
        """Test successful input validation."""
        input_data = {"topic": "test", "analysis": "test"}
        # Should not raise an exception
        base_agent.validate_input(input_data, ["topic", "analysis"])

    def test_validate_input_missing_key(self, base_agent):
        """Test input validation with missing key."""
        input_data = {"topic": "test"}

        with pytest.raises(ValueError, match="Missing required input keys: \\['analysis'\\]"):
            base_agent.validate_input(input_data, ["topic", "analysis"])

    def test_create_system_message(self, base_agent):
        """Test creating system message."""
        message = base_agent.create_system_message("Test system prompt")

        assert message["role"] == "system"
        assert message["content"] == "Test system prompt"

    def test_create_user_message(self, base_agent):
        """Test creating user message."""
        message = base_agent.create_user_message("Test user content")

        assert message["role"] == "user"
        assert message["content"] == "Test user content"

    def test_create_assistant_message(self, base_agent):
        """Test creating assistant message."""
        message = base_agent.create_assistant_message("Test assistant content")

        assert message["role"] == "assistant"
        assert message["content"] == "Test assistant content"

    def test_create_tool_message(self, base_agent):
        """Test creating tool message."""
        message = base_agent.create_tool_message("call123", "Tool result")

        assert message["role"] == "tool"
        assert message["tool_call_id"] == "call123"
        assert message["content"] == "Tool result"

    @pytest.mark.asyncio
    async def test_call_openrouter_success(self, base_agent):
        """Test successful OpenRouter API call."""
        mock_response = {"choices": [{"message": {"content": "Test response"}}]}

        with patch.object(base_agent.openrouter, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            async with base_agent:
                result = await base_agent.call_openrouter([
                    {"role": "user", "content": "test"}
                ])

                assert result == mock_response
                mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_openrouter_with_tools(self, base_agent):
        """Test OpenRouter API call with tools."""
        mock_response = {"choices": [{"message": {"content": "Test response"}}]}
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        with patch.object(base_agent.openrouter, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            async with base_agent:
                result = await base_agent.call_openrouter(
                    [{"role": "user", "content": "test"}],
                    tools=tools
                )

                # Verify tools were passed
                call_args = mock_chat.call_args
                assert call_args[1]['tools'] == tools

    @pytest.mark.asyncio
    async def test_execute_with_logging_success(self, base_agent):
        """Test execute_with_logging with successful execution."""
        input_data = {"topic": "test"}
        expected_output = {"result": "success"}

        with patch.object(base_agent, 'execute', new_callable=AsyncMock) as mock_execute, \
             patch.object(base_agent, 'log_action', new_callable=AsyncMock) as mock_log:

            mock_execute.return_value = expected_output

            async with base_agent:
                result = await base_agent.execute_with_logging(input_data)

                assert result == expected_output
                # Verify logging calls
                assert mock_log.call_count >= 2  # start and complete logs

    @pytest.mark.asyncio
    async def test_execute_with_logging_error(self, base_agent):
        """Test execute_with_logging with execution error."""
        input_data = {"topic": "test"}

        with patch.object(base_agent, 'execute', new_callable=AsyncMock) as mock_execute, \
             patch.object(base_agent, 'log_action', new_callable=AsyncMock) as mock_log:

            mock_execute.side_effect = Exception("Test error")

            async with base_agent:
                with pytest.raises(Exception, match="Test error"):
                    await base_agent.execute_with_logging(input_data)

                # Verify error logging
                error_log_call = None
                for call in mock_log.call_args_list:
                    if call[1].get('success') is False:
                        error_log_call = call
                        break

                assert error_log_call is not None
                assert error_log_call[1]['error_message'] == "Test error"

    @pytest.mark.asyncio
    async def test_handoff_to(self, base_agent):
        """Test agent handoff logging."""
        base_agent.session_id = 123

        with patch('database.connection.log_agent_handoff', new_callable=AsyncMock) as mock_log_handoff:
            await base_agent.handoff_to("target_agent", "test_action", {"data": "test"})

            mock_log_handoff.assert_called_once_with(
                session_id=123,
                from_agent="test_agent",
                to_agent="target_agent",
                action="test_action",
                payload='{"data": "test"}'
            )

class TestMasterAgent:
    """Test MasterAgent class."""

    @pytest.fixture
    def master_agent(self):
        """Create a MasterAgent instance."""
        with patch('agents.master_agent.OpenRouterClient'):
            agent = MasterAgent()
            return agent

    def test_master_agent_initialization(self, master_agent):
        """Test MasterAgent initialization."""
        assert master_agent.name == "master"
        assert hasattr(master_agent, 'sub_agents')
        assert isinstance(master_agent.sub_agents, dict)

    @pytest.mark.asyncio
    async def test_analyze_topic_success(self, master_agent, mock_topic_analysis):
        """Test successful topic analysis."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"themes": ["test"], "audience": "general", "goals": ["inform"], "research_directions": ["web"], "style": "casual"}'
                }
            }],
            "usage": {"total_tokens": 100}
        }

        with patch.object(master_agent.openrouter, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            async with master_agent:
                result = await master_agent.analyze_topic("Test Topic")

                assert isinstance(result, dict)
                assert "themes" in result
                assert "audience" in result
                assert "goals" in result

    @pytest.mark.asyncio
    async def test_analyze_topic_json_error(self, master_agent):
        """Test topic analysis with JSON parsing error."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": "Invalid JSON response"
                }
            }],
            "usage": {"total_tokens": 100}
        }

        with patch.object(master_agent.openrouter, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            async with master_agent:
                result = await master_agent.analyze_topic("Test Topic")

                # Should return fallback analysis
                assert isinstance(result, dict)
                assert "themes" in result

    @pytest.mark.asyncio
    async def test_initialize_sub_agents(self, master_agent):
        """Test sub-agent initialization."""
        with patch('agents.master_agent.WebResearcher') as mock_web, \
             patch('agents.master_agent.KeywordGenerator') as mock_keyword, \
             patch('agents.master_agent.PostGenerator') as mock_post, \
             patch('agents.master_agent.VoiceDialogGenerator') as mock_voice:

            master_agent.session_id = 123
            await master_agent.initialize_sub_agents()

            # Verify all sub-agents were created
            assert 'web_researcher' in master_agent.sub_agents
            assert 'keyword_generator' in master_agent.sub_agents
            assert 'post_generator' in master_agent.sub_agents
            assert 'voice_dialog' in master_agent.sub_agents

            # Verify session IDs were set
            for agent in master_agent.sub_agents.values():
                assert agent.session_id == 123

    @pytest.mark.asyncio
    async def test_process_topic_full_workflow(self, master_agent, mock_topic_analysis, mock_research_results, mock_keywords_data, sample_linkedin_post, sample_voice_dialog):
        """Test the complete topic processing workflow."""
        # Mock all the components
        with patch.object(master_agent, 'analyze_topic', new_callable=AsyncMock) as mock_analyze, \
             patch.object(master_agent, 'initialize_sub_agents', new_callable=AsyncMock) as mock_init, \
             patch('database.connection.create_session_record', new_callable=AsyncMock) as mock_create_session, \
             patch('database.connection.update_session_status', new_callable=AsyncMock) as mock_update_status:

            # Set up mocks
            mock_analyze.return_value = mock_topic_analysis
            mock_create_session.return_value = 123

            # Mock sub-agents
            mock_web_agent = AsyncMock()
            mock_web_agent.execute_with_logging.return_value = mock_research_results

            mock_keyword_agent = AsyncMock()
            mock_keyword_agent.execute_with_logging.return_value = mock_keywords_data

            mock_post_agent = AsyncMock()
            mock_post_agent.execute_with_logging.return_value = {"content": sample_linkedin_post}

            mock_voice_agent = AsyncMock()
            mock_voice_agent.execute_with_logging.return_value = {"dialog": sample_voice_dialog}

            master_agent.sub_agents = {
                'web_researcher': mock_web_agent,
                'keyword_generator': mock_keyword_agent,
                'post_generator': mock_post_agent,
                'voice_dialog': mock_voice_agent
            }

            async with master_agent:
                result = await master_agent.process_topic("Test Topic")

                # Verify the result structure
                assert result['session_id'] == 123
                assert 'linkedin_post' in result
                assert 'voice_dialog' in result
                assert 'keywords' in result
                assert 'hashtags' in result

                # Verify session status was updated
                mock_update_status.assert_called_with(123, "completed")

    @pytest.mark.asyncio
    async def test_process_topic_with_error(self, master_agent):
        """Test topic processing with error handling."""
        with patch('database.connection.create_session_record', new_callable=AsyncMock) as mock_create_session, \
             patch('database.connection.update_session_status', new_callable=AsyncMock) as mock_update_status:

            mock_create_session.return_value = 123

            # Mock analyze_topic to raise an exception
            with patch.object(master_agent, 'analyze_topic', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.side_effect = Exception("Analysis failed")

                async with master_agent:
                    with pytest.raises(Exception, match="Analysis failed"):
                        await master_agent.process_topic("Test Topic")

                    # Verify error status was set
                    mock_update_status.assert_called_with(123, "failed", "Analysis failed")

    def test_abstract_execute_method(self, base_agent):
        """Test that execute method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            base_agent.execute({})