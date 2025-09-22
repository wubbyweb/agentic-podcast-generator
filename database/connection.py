"""Database connection and initialization utilities."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from typing import Optional
import logging

from .models import Base
from config.settings import config

logger = logging.getLogger(__name__)

# Global database engine and session factory
_engine = None
_async_session_maker = None

async def init_database() -> None:
    """Initialize the database engine and create all tables."""
    global _engine, _async_session_maker

    if _engine is None:
        # Create async engine
        _engine = create_async_engine(
            config.database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            pool_recycle=300,
        )

        # Create session factory
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create all tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")

def get_db_session() -> AsyncSession:
    """Get a database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return _async_session_maker()

async def close_database() -> None:
    """Close the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connection closed")

async def check_database_health() -> bool:
    """Check if database is accessible and healthy."""
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def create_session_record(topic: str, analysis: Optional[str] = None) -> int:
    """Create a new session record and return its ID."""
    from .models import Session

    async with get_db_session() as session:
        new_session = Session(topic=topic, analysis=analysis)
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        return new_session.id

async def update_session_status(session_id: int, status: str, error_message: Optional[str] = None) -> None:
    """Update session status."""
    from .models import Session
    from datetime import datetime

    async with get_db_session() as session:
        db_session = await session.get(Session, session_id)
        if db_session:
            db_session.status = status
            if status == 'completed':
                db_session.completed_at = datetime.utcnow()
            if error_message:
                db_session.error_message = error_message
            await session.commit()

async def log_agent_action(
    session_id: int,
    agent_name: str,
    action: str,
    input_data: Optional[str] = None,
    output_data: Optional[str] = None,
    duration_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """Log an agent action to the database."""
    from .models import AgentLog

    async with get_db_session() as session:
        log_entry = AgentLog(
            session_id=session_id,
            agent_name=agent_name,
            action=action,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        session.add(log_entry)
        await session.commit()

async def log_agent_handoff(
    session_id: int,
    from_agent: str,
    to_agent: str,
    action: str,
    payload: Optional[str] = None,
    response_time_ms: Optional[int] = None
) -> None:
    """Log an agent-to-agent handoff."""
    from .models import AgentHandoff

    async with get_db_session() as session:
        handoff = AgentHandoff(
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload=payload,
            response_time_ms=response_time_ms
        )
        session.add(handoff)
        await session.commit()