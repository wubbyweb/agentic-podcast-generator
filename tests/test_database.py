"""Tests for database models and connection."""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from database.models import Session, AgentLog, ResearchResult, Keyword, GeneratedContent, AgentHandoff
from database.connection import create_session_record, update_session_status, log_agent_action

class TestDatabaseModels:
    """Test database model classes."""

    def test_session_model_creation(self):
        """Test creating a Session model instance."""
        session = Session(
            topic="Test Topic",
            analysis='{"test": "analysis"}',
            status="active"
        )

        assert session.topic == "Test Topic"
        assert session.analysis == '{"test": "analysis"}'
        assert session.status == "active"
        assert session.completed_at is None
        assert isinstance(session.created_at, datetime)

    def test_agent_log_model_creation(self):
        """Test creating an AgentLog model instance."""
        agent_log = AgentLog(
            session_id=1,
            agent_name="test_agent",
            action="test_action",
            input_data='{"input": "test"}',
            output_data='{"output": "test"}',
            duration_ms=100,
            success=True
        )

        assert agent_log.session_id == 1
        assert agent_log.agent_name == "test_agent"
        assert agent_log.action == "test_action"
        assert agent_log.input_data == '{"input": "test"}'
        assert agent_log.output_data == '{"output": "test"}'
        assert agent_log.duration_ms == 100
        assert agent_log.success is True

    def test_research_result_model_creation(self):
        """Test creating a ResearchResult model instance."""
        research_result = ResearchResult(
            session_id=1,
            source_url="https://example.com",
            title="Test Article",
            content="Test content",
            relevance_score=0.85,
            credibility_score=0.8,
            source="example.com"
        )

        assert research_result.session_id == 1
        assert research_result.source_url == "https://example.com"
        assert research_result.title == "Test Article"
        assert research_result.content == "Test content"
        assert research_result.relevance_score == 0.85
        assert research_result.credibility_score == 0.8

    def test_keyword_model_creation(self):
        """Test creating a Keyword model instance."""
        keyword = Keyword(
            session_id=1,
            keyword="test keyword",
            keyword_type="keyword",
            relevance_score=0.9,
            category="primary"
        )

        assert keyword.session_id == 1
        assert keyword.keyword == "test keyword"
        assert keyword.keyword_type == "keyword"
        assert keyword.relevance_score == 0.9
        assert keyword.category == "primary"

    def test_generated_content_model_creation(self):
        """Test creating a GeneratedContent model instance."""
        content = GeneratedContent(
            session_id=1,
            content_type="linkedin_post",
            content="Test post content",
            quality_score=0.85
        )

        assert content.session_id == 1
        assert content.content_type == "linkedin_post"
        assert content.content == "Test post content"
        assert content.quality_score == 0.85

    def test_agent_handoff_model_creation(self):
        """Test creating an AgentHandoff model instance."""
        handoff = AgentHandoff(
            session_id=1,
            from_agent="master",
            to_agent="web_researcher",
            action="research_topic",
            payload='{"topic": "test"}',
            response_time_ms=500
        )

        assert handoff.session_id == 1
        assert handoff.from_agent == "master"
        assert handoff.to_agent == "web_researcher"
        assert handoff.action == "research_topic"
        assert handoff.payload == '{"topic": "test"}'
        assert handoff.response_time_ms == 500

class TestDatabaseConnection:
    """Test database connection functions."""

    @pytest.mark.asyncio
    async def test_create_session_record(self):
        """Test creating a session record."""
        with patch('database.connection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock the session creation and commit
            mock_db_session = Mock()
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            mock_db_session.id = 123

            session_id = await create_session_record("Test Topic", '{"analysis": "test"}')

            # Verify the function was called correctly
            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_update_session_status(self):
        """Test updating session status."""
        with patch('database.connection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_db_session = Mock()
            mock_get_session.return_value = mock_session
            mock_session.get.return_value = mock_db_session

            await update_session_status(1, "completed")

            # Verify the session was retrieved and updated
            mock_session.get.assert_called_with(Session, 1)
            assert mock_db_session.status == "completed"
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_update_session_status_with_error(self):
        """Test updating session status with error message."""
        with patch('database.connection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_db_session = Mock()
            mock_get_session.return_value = mock_session
            mock_session.get.return_value = mock_db_session

            await update_session_status(1, "failed", "Test error")

            assert mock_db_session.status == "failed"
            assert mock_db_session.error_message == "Test error"
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_log_agent_action(self):
        """Test logging agent action."""
        with patch('database.connection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            await log_agent_action(
                session_id=1,
                agent_name="test_agent",
                action="test_action",
                input_data='{"input": "test"}',
                output_data='{"output": "test"}',
                duration_ms=100,
                success=True
            )

            # Verify the log entry was added and committed
            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_log_agent_action_with_error(self):
        """Test logging agent action with error."""
        with patch('database.connection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            await log_agent_action(
                session_id=1,
                agent_name="test_agent",
                action="test_action",
                success=False,
                error_message="Test error"
            )

            # Verify error was logged
            assert mock_session.add.called
            assert mock_session.commit.called

    def test_session_relationships(self):
        """Test that Session model relationships are properly configured."""
        session = Session(topic="Test")

        # Check that relationship attributes exist
        assert hasattr(session, 'agent_logs')
        assert hasattr(session, 'research_results')
        assert hasattr(session, 'keywords')
        assert hasattr(session, 'generated_content')
        assert hasattr(session, 'agent_handoffs')

    def test_agent_log_relationships(self):
        """Test that AgentLog model relationships are properly configured."""
        agent_log = AgentLog(
            session_id=1,
            agent_name="test",
            action="test"
        )

        # Check that relationship attributes exist
        assert hasattr(agent_log, 'session')

    def test_research_result_relationships(self):
        """Test that ResearchResult model relationships are properly configured."""
        research_result = ResearchResult(
            session_id=1,
            content="test content"
        )

        assert hasattr(research_result, 'session')

    def test_keyword_relationships(self):
        """Test that Keyword model relationships are properly configured."""
        keyword = Keyword(
            session_id=1,
            keyword="test"
        )

        assert hasattr(keyword, 'session')

    def test_generated_content_relationships(self):
        """Test that GeneratedContent model relationships are properly configured."""
        content = GeneratedContent(
            session_id=1,
            content_type="test",
            content="test content"
        )

        assert hasattr(content, 'session')

    def test_agent_handoff_relationships(self):
        """Test that AgentHandoff model relationships are properly configured."""
        handoff = AgentHandoff(
            session_id=1,
            from_agent="test1",
            to_agent="test2",
            action="test"
        )

        assert hasattr(handoff, 'session')