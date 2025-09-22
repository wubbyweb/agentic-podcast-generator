# 🤖 Agentic Podcast Generator

An intelligent multi-agent system that processes topics through a coordinated workflow of specialized agents to generate LinkedIn posts and voice dialog scripts.

## 🚀 Features

- **Master Agent**: Orchestrates the entire workflow using GPT-5 analysis
- **Web Researcher**: Comprehensive research using tool-calling capabilities
- **Keyword Generator**: Generates relevant keywords and hashtags using Gemini 2.5 Flash
- **Post Generator**: Creates engaging LinkedIn posts in casual language
- **Voice Dialog Generator**: Converts posts into conversational voice scripts
- **SQLite Database**: Persistent storage of agent memory and session logs
- **Parallel Processing**: Research and keyword generation run simultaneously
- **Comprehensive Logging**: All agent interactions logged to console and database

## 📋 Requirements

- Python 3.9+
- OpenRouter API key
- Internet connection for web research

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

# Optional - customize models
MASTER_MODEL=openai/gpt-5
RESEARCH_MODEL=anthropic/claude-3-opus
KEYWORD_MODEL=google/gemini-2.5-flash
POST_MODEL=openai/gpt-4
DIALOG_MODEL=anthropic/claude-3-sonnet
```

## 🎯 Usage

### Basic Usage

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

🔍 Topic Analysis:
  • Themes: ['AI diagnostics', 'treatment optimization', 'patient care']
  • Audience: healthcare professionals, tech enthusiasts
  • Goals: ['inform about AI applications', 'discuss benefits and challenges']
  • Research_directions: ['current implementations', 'case studies', 'regulatory landscape']
  • Style: professional yet accessible

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
Comprehensive research gathered from 15+ sources including recent studies, industry reports, and expert analyses covering AI applications in diagnostics, treatment optimization, drug discovery, and telemedicine.

============================================================
✅ Processing Complete!
============================================================
```

## 🏗️ System Architecture

The system follows a hierarchical agent architecture:

1. **Master Agent** (GPT-5)
   - Analyzes input topics
   - Orchestrates sub-agent execution
   - Manages parallel processing

2. **Web Researcher** (Claude-3 Opus)
   - Performs comprehensive web research
   - Uses tool-calling for web scraping and search
   - Validates source credibility

3. **Keyword Generator** (Gemini 2.5 Flash)
   - Generates SEO-optimized keywords
   - Creates relevant hashtags
   - Analyzes content trends

4. **Post Generator** (GPT-4)
   - Creates engaging LinkedIn content
   - Maintains casual, professional tone
   - Incorporates research insights

5. **Voice Dialog Generator** (Claude-3 Sonnet)
   - Converts posts to conversational scripts
   - Adds natural speech patterns
   - Includes pacing and emphasis cues

## 📊 Database Schema

The system uses SQLite for persistent storage:

- **Sessions**: Complete workflow instances
- **Agent Logs**: All agent actions and executions
- **Research Results**: Web research findings
- **Keywords**: Generated keywords and hashtags
- **Generated Content**: Posts and voice scripts
- **Agent Handoffs**: Inter-agent communications

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
2. Implement `execute()` method
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
model_config = config.get_model_config("master")
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

3. **Web Research Failures**
   - Check internet connection
   - Some websites may block automated requests

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