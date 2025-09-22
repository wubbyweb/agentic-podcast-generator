"""Tests for main CLI application."""

import pytest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner

from main import main, display_results

class TestMainCLI:
    """Test main CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_main_help(self, runner):
        """Test main command help output."""
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'Process a topic through the agentic system' in result.output
        assert '--verbose' in result.output
        assert '--session-id' in result.output

    @patch('main.MasterAgent')
    @patch('main.init_database')
    @patch('main.setup_logging')
    @patch('main.config')
    def test_main_successful_execution(self, mock_config, mock_setup_logging, mock_init_db, mock_master_agent, runner):
        """Test successful main execution."""
        # Mock configuration
        mock_config.validate_config.return_value = True
        mock_config.openrouter_api_key = "test-key"

        # Mock MasterAgent
        mock_instance = AsyncMock()
        mock_instance.process_topic.return_value = {
            'session_id': 123,
            'topic': 'Test Topic',
            'linkedin_post': 'Test post',
            'voice_dialog': 'Test dialog',
            'keywords': ['test'],
            'hashtags': ['#test']
        }
        mock_master_agent.return_value = mock_instance

        result = runner.invoke(main, ['Test Topic'])

        assert result.exit_code == 0
        assert 'Processing complete' in result.output
        assert 'Session ID: 123' in result.output

    @patch('main.config')
    def test_main_missing_api_key(self, mock_config, runner):
        """Test main execution with missing API key."""
        mock_config.validate_config.side_effect = ValueError("API key required")

        result = runner.invoke(main, ['Test Topic'])

        assert result.exit_code == 1
        assert 'API key required' in result.output

    @patch('main.MasterAgent')
    @patch('main.init_database')
    @patch('main.setup_logging')
    @patch('main.config')
    def test_main_with_verbose_flag(self, mock_config, mock_setup_logging, mock_init_db, mock_master_agent, runner):
        """Test main execution with verbose flag."""
        mock_config.validate_config.return_value = True
        mock_config.openrouter_api_key = "test-key"

        mock_instance = AsyncMock()
        mock_instance.process_topic.return_value = {'session_id': 123}
        mock_master_agent.return_value = mock_instance

        result = runner.invoke(main, ['Test Topic', '--verbose'])

        assert result.exit_code == 0
        # Verify setup_logging was called with DEBUG level
        mock_setup_logging.assert_called_with(level='DEBUG')

    @patch('main.MasterAgent')
    @patch('main.init_database')
    @patch('main.setup_logging')
    @patch('main.config')
    def test_main_with_session_id(self, mock_config, mock_setup_logging, mock_init_db, mock_master_agent, runner):
        """Test main execution with session ID."""
        mock_config.validate_config.return_value = True
        mock_config.openrouter_api_key = "test-key"

        mock_instance = AsyncMock()
        mock_instance.process_topic.return_value = {'session_id': 456}
        mock_master_agent.return_value = mock_instance

        result = runner.invoke(main, ['Test Topic', '--session-id', '123'])

        assert result.exit_code == 0
        # Verify process_topic was called with session_id
        mock_instance.process_topic.assert_called_with('Test Topic', session_id=123)

    @patch('main.MasterAgent')
    @patch('main.init_database')
    @patch('main.setup_logging')
    @patch('main.config')
    def test_main_with_json_output(self, mock_config, mock_setup_logging, mock_init_db, mock_master_agent, runner):
        """Test main execution with JSON output format."""
        mock_config.validate_config.return_value = True
        mock_config.openrouter_api_key = "test-key"

        mock_result = {
            'session_id': 123,
            'topic': 'Test Topic',
            'linkedin_post': 'Test post'
        }
        mock_instance = AsyncMock()
        mock_instance.process_topic.return_value = mock_result
        mock_master_agent.return_value = mock_instance

        result = runner.invoke(main, ['Test Topic', '--output-format', 'json'])

        assert result.exit_code == 0
        # Should contain JSON output
        assert '"session_id": 123' in result.output
        assert '"topic": "Test Topic"' in result.output

    @patch('main.MasterAgent')
    @patch('main.init_database')
    @patch('main.setup_logging')
    @patch('main.config')
    def test_main_execution_error(self, mock_config, mock_setup_logging, mock_init_db, mock_master_agent, runner):
        """Test main execution with processing error."""
        mock_config.validate_config.return_value = True
        mock_config.openrouter_api_key = "test-key"

        mock_instance = AsyncMock()
        mock_instance.process_topic.side_effect = Exception("Processing failed")
        mock_master_agent.return_value = mock_instance

        result = runner.invoke(main, ['Test Topic'])

        assert result.exit_code == 1
        assert 'Processing failed' in result.output

class TestDisplayResults:
    """Test result display functionality."""

    def test_display_results_complete(self, capsys):
        """Test displaying complete results."""
        result = {
            'session_id': 123,
            'topic': 'Test Topic',
            'analysis': {
                'themes': ['AI', 'Healthcare'],
                'audience': 'professionals',
                'goals': ['inform'],
                'research_directions': ['web'],
                'style': 'professional'
            },
            'keywords': ['artificial intelligence', 'healthcare'],
            'hashtags': ['#AI', '#Healthcare'],
            'linkedin_post': 'Test LinkedIn post content',
            'voice_dialog': 'Test voice dialog content',
            'research_summary': 'Test research summary'
        }

        display_results(result)

        captured = capsys.readouterr()
        output = captured.out

        # Check main sections are present
        assert '🤖 AGENTIC SYSTEM RESULTS' in output
        assert 'Session ID: 123' in output
        assert '📝 Topic: Test Topic' in output
        assert '🔍 Topic Analysis:' in output
        assert '🏷️ Keywords:' in output
        assert '#️⃣ Hashtags:' in output
        assert '💼 LinkedIn Post:' in output
        assert '🎙️ Voice Dialog Script:' in output
        assert '📚 Research Summary:' in output
        assert '✅ Processing Complete!' in output

    def test_display_results_minimal(self, capsys):
        """Test displaying minimal results."""
        result = {
            'session_id': 456,
            'topic': 'Minimal Topic',
            'linkedin_post': 'Minimal post',
            'voice_dialog': 'Minimal dialog'
        }

        display_results(result)

        captured = capsys.readouterr()
        output = captured.out

        assert 'Session ID: 456' in output
        assert '📝 Topic: Minimal Topic' in output
        assert 'Minimal post' in output
        assert 'Minimal dialog' in output

    def test_display_results_missing_fields(self, capsys):
        """Test displaying results with missing optional fields."""
        result = {
            'session_id': 789,
            'topic': 'Incomplete Topic'
            # Missing analysis, keywords, etc.
        }

        display_results(result)

        captured = capsys.readouterr()
        output = captured.out

        assert 'Session ID: 789' in output
        assert '📝 Topic: Incomplete Topic' in output
        # Should not crash with missing fields