# Project Structure and Implementation Plan

## Directory Structure

```
agentic-podcast-generator/
├── README.md                          # Project overview and usage
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── main.py                            # CLI entry point
├── agentic_podcast_generator_tutorial.ipynb  # Interactive tutorial
├── sequence.md                        # Workflow diagram
├── system_architecture.md            # Architecture documentation
├── technical_specifications.md       # Technical details
├── test_system.py                     # System testing script
├── config/
│   ├── __init__.py
│   └── settings.py                   # Configuration management
├── database/
│   ├── __init__.py
│   ├── models.py                     # SQLAlchemy models
│   └── connection.py                 # Database setup
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                 # Base Agent class
│   ├── master_agent.py               # Master Agent implementation
│   └── sub_agents/
│       ├── __init__.py
│       ├── web_researcher.py         # Web research (legacy/not used)
│       ├── keyword_generator.py      # Keyword/hashtag generation
│       ├── post_generator.py         # LinkedIn post creation
│       └── voice_dialog.py           # Voice dialog generation
├── services/
│   ├── __init__.py
│   ├── openrouter_client.py          # OpenRouter API client
│   ├── search_api.py                 # Search API integrations (legacy)
│   ├── web_scraper.py                # Web scraping (legacy)
│   └── logger.py                     # Logging service
├── utils/
│   ├── __init__.py
│   ├── communication.py              # Agent communication protocol
│   ├── retry.py                      # Retry mechanisms
│   └── validators.py                 # Data validation utilities
└── tests/
    ├── __init__.py
    ├── conftest.py                   # Test configuration
    ├── test_agents.py                # Agent tests
    ├── test_basic.py                 # Basic functionality tests
    ├── test_config.py                # Configuration tests
    ├── test_database.py              # Database tests
    ├── test_main.py                  # Main CLI tests
    ├── test_services.py              # Service tests
    └── test_utils.py                 # Utility tests
```

## Actual Implementation Overview

### Current Workflow (As Implemented)

1. **CLI Entry** (`main.py`)
   - Parse command line arguments
   - Call Perplexity AI (sonar model) for research
   - Initialize Master Agent with research results
   - Display formatted output

2. **Research Phase** (Sequential)
   - Perplexity AI performs comprehensive research
   - Returns detailed analysis and insights

3. **Content Generation** (Parallel)
   - Master Agent coordinates 3 sub-agents simultaneously:
     - **Keyword Generator** (Gemini 2.0 Flash)
     - **Post Generator** (Grok-3 Mini)
     - **Voice Dialog Generator** (Grok-3 Mini)

4. **Output & Logging**
   - Formatted results displayed
   - All interactions logged to SQLite database

### Key Implementation Details

#### Models Actually Used
- **Research**: `perplexity/sonar` (Perplexity AI) - NOT GPT-5
- **Keywords**: `google/gemini-2.0-flash-001` - NOT Gemini 2.5 Flash
- **Posts**: `xai/grok-3-mini` - NOT GPT-4
- **Voice**: `xai/grok-3-mini` - NOT Claude-3 Sonnet

#### Important Notes
- **GPT-5 is NOT used** anywhere in the running application
- **Web Researcher agent exists** but is not used in main workflow
- **Perplexity AI integration** is done directly in `main.py`, not through an agent

## Component Details

### Core Components

#### main.py - CLI Entry Point
```python
# Actual implementation structure
async def async_main(topic, verbose, session_id, output_format):
    # 1. Get research from Perplexity AI
    research_response = await get_perplexity_research(topic)

    # 2. Process with Master Agent
    async with MasterAgent() as master:
        result = await master.process_topic_with_research(
            topic, research_response, session_id=session_id
        )

    # 3. Display results
    display_results(result)
```

#### Master Agent (agents/master_agent.py)
```python
class MasterAgent(BaseAgent):
    async def process_topic_with_research(self, topic, research_response, session_id=None):
        # 1. Create session
        self.session_id = await create_session_record(topic)

        # 2. Initialize sub-agents
        await self.initialize_all_agents()

        # 3. Run parallel execution
        post_task = self.sub_agents['post_generator'].execute_with_logging(post_input)
        voice_task = self.sub_agents['voice_dialog'].execute_with_logging(voice_input)
        keyword_task = self.sub_agents['keyword_generator'].execute_with_logging(keyword_input)

        # 4. Gather results
        results = await asyncio.gather(post_task, voice_task, keyword_task, return_exceptions=True)

        # 5. Return formatted results
        return {
            "session_id": self.session_id,
            "topic": topic,
            "linkedin_post": results[0]["content"] if not isinstance(results[0], Exception) else "",
            "voice_dialog": results[1]["dialog"] if not isinstance(results[1], Exception) else "",
            "keywords": results[2]["keywords"] if not isinstance(results[2], Exception) else [],
            "hashtags": results[2]["hashtags"] if not isinstance(results[2], Exception) else [],
            "research_summary": research_response[:500]
        }
```

### Sub-Agent Implementations

#### Keyword Generator (agents/sub_agents/keyword_generator.py)
- **Model**: `google/gemini-2.0-flash-001`
- **Purpose**: Generate SEO keywords and hashtags
- **Key Features**:
  - Analyzes research content
  - Categorizes keywords by intent
  - Calculates relevance scores
  - Cleans and validates output

#### Post Generator (agents/sub_agents/post_generator.py)
- **Model**: `xai/grok-3-mini`
- **Purpose**: Create LinkedIn posts
- **Input**: Topic, research, keywords
- **Output**: Formatted professional content

#### Voice Dialog Generator (agents/sub_agents/voice_dialog.py)
- **Model**: `xai/grok-3-mini`
- **Purpose**: Convert posts to podcast scripts
- **Features**: Natural conversation patterns, pacing cues

#### Web Researcher (agents/sub_agents/web_researcher.py) - LEGACY
- **Status**: Implemented but NOT USED in current workflow
- **Purpose**: Web research with tool-calling capabilities
- **Note**: System currently uses Perplexity AI instead

### Configuration System (config/settings.py)

```python
class SystemConfig:
    def setup_models(self):
        # Actual models used in production
        self.models = {
            "master": ModelConfig(name="sonar"),  # Perplexity AI
            "research": ModelConfig(name="sonar"),  # Perplexity AI
            "keyword": ModelConfig(name="google/gemini-2.0-flash-001"),  # Gemini 2.0
            "post": ModelConfig(name="xai/grok-3-mini"),  # Grok-3 Mini
            "dialog": ModelConfig(name="xai/grok-3-mini")  # Grok-3 Mini
        }
```

### Database Models (database/models.py)

```python
# Key tables
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer)

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    keyword = Column(String, nullable=False)
    keyword_type = Column(String)  # "keyword" or "hashtag"
    relevance_score = Column(Float)
    category = Column(String)

class GeneratedContent(Base):
    __tablename__ = "generated_content"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    content_type = Column(String, nullable=False)  # "linkedin_post" or "voice_dialog"
    content = Column(Text, nullable=False)
    metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Development Workflow

### Running the System
```bash
# Basic usage
python main.py "Artificial Intelligence in Healthcare"

# With verbose logging
python main.py "Machine Learning Trends" --verbose

# Resume session
python main.py "AI Ethics" --session-id 123

# JSON output
python main.py "Blockchain Technology" --output-format json
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest --cov=agents --cov-report=html
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Important Clarifications

### GPT-5 References (OUTDATED)
**GPT-5 is NOT used in the actual application.** References exist in:
- Some documentation (being updated)
- Test files (expecting old defaults)
- Example code (speculative)

### Web Research Status
- **WebResearcher agent**: Exists but not used
- **Current research**: Direct Perplexity AI integration
- **Future potential**: Web research capabilities available if needed

### Model Accuracy
Always verify actual models by checking:
- `config/settings.py` for current configurations
- `main.py` for research implementation
- Agent source code for model usage

This documentation reflects the actual implemented system as of the current codebase.