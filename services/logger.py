"""Logging service for the agentic system."""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """Set up logging configuration for the entire system."""

    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format string
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)-20s | "
            "%(message)s"
        )

    # Create formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set up specific loggers for different components
    _setup_component_loggers()

def _setup_component_loggers() -> None:
    """Set up specific loggers for different system components."""

    # Agent logger
    agent_logger = logging.getLogger("agent")
    agent_logger.setLevel(logging.DEBUG)

    # Database logger
    db_logger = logging.getLogger("database")
    db_logger.setLevel(logging.DEBUG)

    # API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.DEBUG)

    # Web scraping logger
    scrape_logger = logging.getLogger("scraper")
    scrape_logger.setLevel(logging.DEBUG)

def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger specifically configured for an agent."""

    logger = logging.getLogger(f"agent.{agent_name}")

    # Ensure it doesn't propagate to root to avoid duplicate messages
    logger.propagate = False

    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s | AGENT-{agent_name.upper()} | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def get_component_logger(component: str) -> logging.Logger:
    """Get a logger for a specific system component."""

    logger = logging.getLogger(f"system.{component}")

    # Ensure it doesn't propagate to root to avoid duplicate messages
    logger.propagate = False

    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s | {component.upper()} | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

class AgentLoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for agents with additional context."""

    def __init__(self, logger: logging.Logger, session_id: Optional[int] = None):
        super().__init__(logger, {})
        self.session_id = session_id

    def process(self, msg: str, kwargs):
        """Process the logging message to add context."""
        if self.session_id:
            msg = f"[Session {self.session_id}] {msg}"
        return msg, kwargs

    def log_handoff(self, from_agent: str, to_agent: str, action: str) -> None:
        """Log an agent-to-agent handoff."""
        self.info(f"HANDOFF → {to_agent}: {action}")

    def log_execution_start(self, action: str) -> None:
        """Log the start of an agent execution."""
        self.info(f"EXECUTION START: {action}")

    def log_execution_complete(self, action: str, duration_ms: Optional[int] = None) -> None:
        """Log the completion of an agent execution."""
        duration_str = f" ({duration_ms}ms)" if duration_ms else ""
        self.info(f"EXECUTION COMPLETE: {action}{duration_str}")

    def log_api_call(self, model: str, tokens: Optional[int] = None) -> None:
        """Log an API call."""
        token_str = f" ({tokens} tokens)" if tokens else ""
        self.debug(f"API CALL: {model}{token_str}")

    def log_error(self, action: str, error: str) -> None:
        """Log an error with context."""
        self.error(f"ERROR in {action}: {error}")

def create_session_logger(session_id: int) -> AgentLoggerAdapter:
    """Create a logger adapter for a specific session."""
    base_logger = logging.getLogger("session")
    return AgentLoggerAdapter(base_logger, session_id)