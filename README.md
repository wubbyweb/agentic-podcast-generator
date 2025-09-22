# 🤖 Agentic Podcast Generator

An intelligent multi-agent system that processes topics through a coordinated workflow to generate LinkedIn posts and voice dialog scripts using AI research and content generation.

## 🚀 Features

- **Research-First Approach**: Uses Perplexity AI (sonar model) for comprehensive topic research
- **Master Agent**: Orchestrates the entire workflow and manages sub-agent execution
- **Keyword Generator**: Generates SEO-optimized keywords and hashtags using Gemini 2.0 Flash
- **Post Generator**: Creates engaging LinkedIn posts in casual language using Grok-3
- **Voice Dialog Generator**: Converts posts into conversational voice scripts using Grok-3
- **SQLite Database**: Persistent storage of agent memory and session logs
- **Parallel Processing**: Keyword, post, and voice generation run simultaneously after research
- **Comprehensive Logging**: All agent interactions logged to console and database

## 📋 Requirements

- Python 3.9+
- OpenRouter API key (for AI model access)
- Internet connection for research

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentic-podcast-generator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

## ⚙️ Configuration

Edit the `.env` file with your configuration:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional - customize models (defaults shown)
MASTER_MODEL=sonar  # Perplexity AI research model
KEYWORD_MODEL=google/gemini-2.0-flash-001
POST_MODEL=xai/grok-3-mini
DIALOG_MODEL=xai/grok-3-mini

# Optional - system settings
LOG_LEVEL=INFO
DATABASE_URL=sqlite+aiosqlite:///./agentic_system.db
MAX_RETRIES=3
TIMEOUT_SECONDS=120
```

## 🎯 Usage

### Basic Usage

Run the system with a simple topic:

```bash
python main.py "Artificial Intelligence in Healthcare"
```

### Advanced Options

```bash
# Verbose logging
python main.py "Machine Learning Trends" --verbose

# Resume existing session
python main.py "AI Ethics" --session-id 123

# JSON output format
python main.py "Blockchain Technology" --output-format json
```

### Example Output

```
============================================================
🤖 AGENTIC SYSTEM RESULTS
============================================================

📋 Session ID: 1
📝 Topic: Artificial Intelligence in Healthcare

🏷️ Keywords:
  • artificial intelligence
  • healthcare technology
  • medical diagnostics
  • AI in medicine

#️⃣ Hashtags:
  #AIHealthcare #MedicalAI #DigitalHealth #HealthcareInnovation

💼 LinkedIn Post:
----------------------------------------
Excited to share some insights on how AI is revolutionizing healthcare! 🤖🏥

From diagnostic imaging that catches diseases earlier to personalized treatment plans that save lives, artificial intelligence is transforming patient care in ways we couldn't imagine just a few years ago.

Key trends I'm seeing:
• AI-powered diagnostic tools with 95%+ accuracy
• Predictive analytics for patient outcomes
• Drug discovery accelerated by machine learning
• Robotic surgery with unprecedented precision

The future of healthcare is here, and it's intelligent! What are your thoughts on AI's role in medicine?

#AIHealthcare #MedicalInnovation #DigitalTransformation
----------------------------------------

🎙️ Voice Dialog Script:
----------------------------------------
[Opening music fades in]

Host: Welcome to today's episode on the transformative power of artificial intelligence in healthcare!

You know, I'm really excited to dive into this topic because AI isn't just a buzzword anymore - it's actively saving lives and revolutionizing patient care.

Let me walk you through what I'm seeing in the industry right now...

[Content continues with natural, conversational delivery]
----------------------------------------

📚 Research Summary:
Comprehensive research gathered from Perplexity AI covering current developments, key insights, trends, and relevant data points in AI healthcare applications.

============================================================
✅ Processing Complete!
============================================================
```

## 🏗️ System Architecture

The system follows a streamlined agent architecture:

1. **Research Phase** (Sequential)
   - Perplexity AI (sonar model) performs comprehensive research on the topic
   - Provides detailed analysis, current facts, trends, and insights

2. **Master Agent** (Coordinator)
   - Receives research from Perplexity
   - Orchestrates sub-agent execution
   - Manages parallel processing of content generation
   - Handles session management and logging

3. **Content Generation** (Parallel)
   - **Keyword Generator** (Gemini 2.0 Flash): Creates SEO keywords and hashtags
   - **Post Generator** (Grok-3): Generates LinkedIn posts
   - **Voice Dialog Generator** (Grok-3): Creates podcast scripts

4. **Output & Storage**
   - Results displayed in formatted output
   - All interactions logged to SQLite database
   - Session tracking for resumability

### Data Flow Diagram
```
User Input (Topic)
    ↓
Perplexity AI Research (Sequential)
    ↓
Master Agent Coordination
    ↓
Parallel Content Generation:
├── Keyword Generation (Gemini)
├── Post Generation (Grok-3)
└── Voice Script Generation (Grok-3)
    ↓
Formatted Output + Database Logging
```

## 📊 Database Schema

The system uses SQLite for persistent storage:

- **Sessions**: Complete workflow instances with status tracking
- **Agent Logs**: All agent actions, inputs, outputs, and timing
- **Keywords**: Generated keywords and hashtags with relevance scores
- **Generated Content**: Posts and voice scripts with metadata

## 🔧 Development

### Running Tests

```bash
pytest tests/
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

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement the `execute()` method
3. Add to `agents/sub_agents/` directory
4. Update `MasterAgent.initialize_sub_agents()`
5. Add configuration in `config/settings.py`

## 📝 API Reference

### MasterAgent

```python
from agents.master_agent import MasterAgent

async with MasterAgent() as master:
    result = await master.process_topic("Your Topic Here")
```

### Configuration

```python
from config.settings import config

# Access configuration
api_key = config.openrouter_api_key
model_config = config.get_model_config("keyword")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This system generates content using AI models. Always review and fact-check generated content before publishing. The system is designed for research and content creation assistance, not as a replacement for professional expertise.

## 🆘 Troubleshooting

### Common Issues

1. **OpenRouter API Key Error**
   - Ensure your API key is correctly set in `.env`
   - Check your OpenRouter account has sufficient credits

2. **Database Connection Error**
   - Ensure write permissions in the project directory
   - Check SQLite installation

3. **Research Failures**
   - Check internet connection
   - Verify OpenRouter API access

4. **Agent Timeouts**
   - Increase timeout settings in config
   - Check API rate limits

### Debug Mode

Run with verbose logging to see detailed execution information:

```bash
python main.py "Your Topic" --verbose
```

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the logs in `agentic_system.log`
- Open an issue on GitHub

---

**Built with ❤️ using Python, OpenRouter API, and modern AI orchestration patterns.**