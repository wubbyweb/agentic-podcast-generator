# Project Structure and Implementation Plan

## Directory Structure

```
agentic-podcast-generator/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
├── main.py                     # CLI entry point
├── config/
│   ├── __init__.py
│   ├── settings.py             # Configuration management
│   └── models.yaml             # OpenRouter model configurations
├── database/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models
│   ├── connection.py           # Database connection and setup
│   └── migrations/             # Database migrations
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base Agent class
│   ├── master_agent.py         # Master Agent implementation
│   └── sub_agents/
│       ├── __init__.py
│       ├── web_researcher.py   # Web research capabilities
│       ├── keyword_generator.py# Keyword/hashtag generation
│       ├── post_generator.py   # LinkedIn post creation
│       └── voice_dialog.py     # Voice dialog generation
├── services/
│   ├── __init__.py
│   ├── openrouter_client.py    # OpenRouter API client
│   ├── web_scraper.py          # Web scraping utilities
│   ├── search_api.py           # Search API integrations
│   └── logger.py               # Custom logging service
├── utils/
│   ├── __init__.py
│   ├── communication.py        # Agent communication protocol
│   ├── retry.py                # Retry mechanisms
│   └── validators.py           # Data validation utilities
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_services.py
│   └── fixtures/
└── docs/
    ├── api_reference.md
    ├── usage_examples.md
    └── troubleshooting.md
```

## Core Implementation Files

### 1. main.py - CLI Entry Point
```python
#!/usr/bin/env python3
"""
Agentic System CLI Entry Point
Handles user input and initiates the Master Agent workflow
"""

import asyncio
import click
from agents.master_agent import MasterAgent
from config.settings import Config
from database.connection import init_database
from services.logger import setup_logging

@click.command()
@click.argument('topic', required=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--session-id', help='Resume existing session')
async def main(topic: str, verbose: bool, session_id: str = None):
    """Process a topic through the agentic system pipeline."""
    
    # Initialize logging
    setup_logging(verbose=verbose)
    
    # Initialize database
    await init_database()
    
    # Create and run Master Agent
    master = MasterAgent(config=Config())
    result = await master.process_topic(topic, session_id=session_id)
    
    click.echo(f"Processing complete. Session ID: {result.session_id}")
    click.echo(f"LinkedIn Post: {result.linkedin_post}")
    click.echo(f"Voice Dialog: {result.voice_dialog}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. agents/base_agent.py - Base Agent Class
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from services.logger import get_agent_logger
from database.models import AgentLog, Session

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = get_agent_logger(name)
        self.session_id: Optional[str] = None
        
    async def log_action(self, action: str, input_data: Any, 
                        output_data: Any, duration_ms: int):
        """Log agent action to database and console."""
        # Implementation for logging
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary function."""
        pass
    
    async def handoff_to(self, target_agent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle communication with other agents."""
        # Implementation for agent communication
        pass
```

### 3. agents/master_agent.py - Master Agent
```python
import asyncio
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.sub_agents.web_researcher import WebResearcher
from agents.sub_agents.keyword_generator import KeywordGenerator
from agents.sub_agents.post_generator import PostGenerator
from agents.sub_agents.voice_dialog import VoiceDialogGenerator
from services.openrouter_client import OpenRouterClient

class MasterAgent(BaseAgent):
    """Master Agent that orchestrates all sub-agents."""
    
    def __init__(self, config):
        super().__init__("master", config)
        self.openrouter = OpenRouterClient(config.OPENROUTER_API_KEY)
        
    async def process_topic(self, topic: str, session_id: str = None) -> Dict[str, Any]:
        """Main workflow orchestration."""
        
        # 1. Analyze topic with GPT-5
        analysis = await self.analyze_topic(topic)
        
        # 2. Create sub-agents
        web_researcher = WebResearcher(self.config)
        keyword_generator = KeywordGenerator(self.config)
        
        # 3. Execute parallel tasks
        research_task = web_researcher.execute({"topic": topic, "analysis": analysis})
        keyword_task = keyword_generator.execute({"topic": topic, "analysis": analysis})
        
        research_results, keywords = await asyncio.gather(research_task, keyword_task)
        
        # 4. Generate LinkedIn post
        post_generator = PostGenerator(self.config)
        post_result = await post_generator.execute({
            "topic": topic,
            "research": research_results,
            "keywords": keywords
        })
        
        # 5. Generate voice dialog
        voice_generator = VoiceDialogGenerator(self.config)
        voice_result = await voice_generator.execute({
            "linkedin_post": post_result["content"]
        })
        
        return {
            "session_id": self.session_id,
            "linkedin_post": post_result["content"],
            "voice_dialog": voice_result["dialog"],
            "keywords": keywords["keywords"],
            "research_summary": research_results["summary"]
        }
    
    async def analyze_topic(self, topic: str) -> Dict[str, Any]:
        """Analyze topic using GPT-5."""
        # Implementation for topic analysis
        pass
```

### 4. services/openrouter_client.py - OpenRouter API Client
```python
import aiohttp
import json
from typing import Dict, Any, List, Optional
from utils.retry import retry_with_backoff

class OpenRouterClient:
    """Client for OpenRouter API with retry logic and model management."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry_with_backoff(max_retries=3)
    async def chat_completion(self, model: str, messages: List[Dict], 
                             tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Send chat completion request to OpenRouter."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        async with self.session.post(
            f"{self.base_url}/chat/completions", 
            headers=headers, 
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()
```

### 5. database/models.py - SQLAlchemy Models
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='active')
    
    # Relationships
    agent_logs = relationship("AgentLog", back_populates="session")
    research_results = relationship("ResearchResult", back_populates="session")
    keywords = relationship("Keyword", back_populates="session")
    generated_content = relationship("GeneratedContent", back_populates="session")

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    agent_name = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer)
    
    # Relationships
    session = relationship("Session", back_populates="agent_logs")

# Additional model classes...
```

## Implementation Workflow

### Phase 1: Foundation (Days 1-2)
1. Set up project structure and virtual environment
2. Install dependencies and configure development environment
3. Implement database models and connection handling
4. Create basic configuration management
5. Set up logging infrastructure

### Phase 2: Core Services (Days 3-4)
1. Implement OpenRouter API client with retry logic
2. Create base agent class with common functionality
3. Build agent communication protocol
4. Implement web scraping and search API services

### Phase 3: Agent Implementation (Days 5-7)
1. Implement Master Agent with orchestration logic
2. Create Web Researcher sub-agent with tool calling
3. Build Keyword Generator using Gemini 2.5 Flash
4. Implement Post Generator for LinkedIn content
5. Create Voice Dialog Generator

### Phase 4: Integration & Testing (Days 8-9)
1. Integrate all components and test end-to-end workflow
2. Implement comprehensive error handling
3. Add CLI interface and user experience improvements
4. Performance testing and optimization

### Phase 5: Documentation & Deployment (Day 10)
1. Write comprehensive documentation
2. Create usage examples and troubleshooting guides
3. Package for distribution
4. Final testing and quality assurance

## Key Implementation Considerations

### Concurrency Management
- Use asyncio for parallel execution of Web Researcher and Keyword Generator
- Implement proper async/await patterns throughout
- Handle rate limiting for OpenRouter API calls

### Error Handling
- Implement retry mechanisms with exponential backoff
- Graceful degradation when sub-agents fail
- Comprehensive error logging and recovery procedures

### Memory Management
- Efficient database connection pooling
- Proper cleanup of web scraping resources
- Memory-conscious handling of large research datasets

### Security
- Secure API key management
- Input validation and sanitization
- Rate limiting and abuse prevention

This structure provides a solid foundation for implementing the complete agentic system with clear separation of concerns and scalable architecture.