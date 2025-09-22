"""Web Researcher Sub-agent with tool-calling capabilities."""

import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from ..base_agent import BaseAgent
from database.connection import get_db_session
from database.models import ResearchResult

logger = logging.getLogger(__name__)

class WebResearcher(BaseAgent):
    """Web Researcher agent with tool-calling capabilities for comprehensive research."""

    def __init__(self):
        super().__init__("web_researcher", "research")
        self.research_tools = self._define_research_tools()

    def _define_research_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available to the web researcher."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information on a specific topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to execute"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 20
                            },
                            "time_filter": {
                                "type": "string",
                                "description": "Time filter for search results",
                                "enum": ["day", "week", "month", "year", "all"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_webpage",
                    "description": "Extract content from a specific webpage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to scrape content from"
                            },
                            "extract_type": {
                                "type": "string",
                                "description": "Type of content to extract",
                                "enum": ["text", "links", "metadata", "full"],
                                "default": "text"
                            },
                            "max_length": {
                                "type": "integer",
                                "description": "Maximum content length to extract",
                                "default": 5000
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_content",
                    "description": "Analyze scraped content for relevance and key insights",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Content to analyze"
                            },
                            "topic": {
                                "type": "string",
                                "description": "Original topic for relevance scoring"
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis to perform",
                                "enum": ["relevance", "sentiment", "key_points", "credibility", "comprehensive"],
                                "default": "comprehensive"
                            }
                        },
                        "required": ["content", "topic"]
                    }
                }
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive web research on the given topic."""

        self.validate_input(input_data, ["topic"])

        topic = input_data["topic"]
        analysis = input_data.get("analysis", {})

        # Create research plan based on topic analysis
        research_plan = await self._create_research_plan(topic, analysis)

        # Execute research using tool-calling
        research_results = await self._perform_research(topic, research_plan)

        # Analyze and summarize findings
        summary = await self._analyze_findings(topic, research_results)

        # Store results in database
        await self._store_research_results(research_results)

        return {
            "topic": topic,
            "research_plan": research_plan,
            "results": research_results,
            "summary": summary,
            "total_sources": len(research_results),
            "credibility_score": self._calculate_overall_credibility(research_results)
        }

    async def _create_research_plan(self, topic: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive research plan based on topic analysis."""

        system_prompt = """You are an expert research strategist. Create a detailed research plan for the given topic.

Based on the topic analysis, identify:
1. Key search queries to execute
2. Types of sources to prioritize (academic, news, industry reports, etc.)
3. Specific websites or domains to target
4. Research questions to answer
5. Success criteria for the research

Return your plan in JSON format with these keys: search_queries, source_types, target_domains, research_questions, success_criteria."""

        user_content = f"""Topic: {topic}

Topic Analysis: {json.dumps(analysis, indent=2)}

Create a comprehensive research plan that will gather high-quality, relevant information for content creation."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        content = self.openrouter.extract_response_content(response)

        try:
            plan = json.loads(content)
        except json.JSONDecodeError:
            # Fallback plan
            plan = {
                "search_queries": [topic, f"{topic} latest developments", f"{topic} expert opinions"],
                "source_types": ["news", "academic", "industry"],
                "target_domains": ["edu", "org", "com"],
                "research_questions": [f"What are the key aspects of {topic}?", f"What are the latest developments in {topic}?"],
                "success_criteria": ["Gather information from at least 5 credible sources", "Cover multiple perspectives"]
            }

        return plan

    async def _perform_research(self, topic: str, research_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform the actual research using tool-calling capabilities."""

        results = []

        # Execute search queries
        for query in research_plan.get("search_queries", [topic]):
            search_results = await self._execute_web_search(query)
            results.extend(search_results)

        # Scrape specific high-value pages if identified
        for domain in research_plan.get("target_domains", []):
            domain_results = await self._scrape_domain_pages(topic, domain)
            results.extend(domain_results)

        # Remove duplicates and limit results
        unique_results = self._deduplicate_results(results)
        return unique_results[:15]  # Limit to top 15 results

    async def _execute_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Execute a web search using the tool-calling interface."""

        # This is a simplified implementation
        # In a real system, this would use actual search APIs or web scraping

        # For now, we'll simulate tool calling by directly calling a search function
        # In production, this would use the OpenRouter tool-calling feature

        search_results = await self._mock_web_search(query)

        # Analyze each result for relevance and credibility
        analyzed_results = []
        for result in search_results:
            analysis = await self._analyze_content_relevance(result, query)
            result.update(analysis)
            analyzed_results.append(result)

        return analyzed_results

    async def _mock_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Mock web search implementation (replace with real search API)."""

        # This is a placeholder - in production, you would integrate with:
        # - Google Custom Search API
        # - Bing Search API
        # - DuckDuckGo API
        # - Or use web scraping libraries

        return [
            {
                "title": f"Latest Developments in {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}",
                "snippet": f"Comprehensive overview of {query} with expert insights and analysis.",
                "source": "example.com",
                "content": f"Detailed content about {query}..."
            }
        ]

    async def _scrape_domain_pages(self, topic: str, domain: str) -> List[Dict[str, Any]]:
        """Scrape pages from a specific domain."""

        # This is a placeholder - in production, you would use:
        # - BeautifulSoup for HTML parsing
        # - Scrapy for comprehensive scraping
        # - Selenium for JavaScript-heavy sites

        return []

    async def _analyze_content_relevance(self, content: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Analyze content for relevance to the topic."""

        system_prompt = """Analyze the given content for relevance to the topic. Provide:
1. Relevance score (0-1)
2. Key insights extracted
3. Credibility assessment
4. Content type (news, academic, opinion, etc.)

Return analysis in JSON format."""

        user_content = f"""Topic: {topic}

Content: {content.get('content', content.get('snippet', ''))}

URL: {content.get('url', '')}
Title: {content.get('title', '')}"""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        analysis_content = self.openrouter.extract_response_content(response)

        try:
            analysis = json.loads(analysis_content)
        except json.JSONDecodeError:
            analysis = {
                "relevance_score": 0.7,
                "key_insights": ["Content appears relevant to the topic"],
                "credibility_score": 0.6,
                "content_type": "general"
            }

        return analysis

    async def _analyze_findings(self, topic: str, results: List[Dict[str, Any]]) -> str:
        """Analyze all research findings and create a comprehensive summary."""

        system_prompt = """You are a research analyst. Synthesize the research findings into a comprehensive summary that covers:
1. Key themes and patterns
2. Important facts and statistics
3. Expert opinions and perspectives
4. Current trends and developments
5. Areas of consensus and debate
6. Gaps in the research

Create a well-structured summary suitable for content creation."""

        # Compile research findings
        findings_text = ""
        for i, result in enumerate(results, 1):
            findings_text += f"\nSource {i}:\n"
            findings_text += f"Title: {result.get('title', 'N/A')}\n"
            findings_text += f"URL: {result.get('url', 'N/A')}\n"
            findings_text += f"Content: {result.get('content', result.get('snippet', 'N/A'))}\n"
            findings_text += f"Relevance: {result.get('relevance_score', 'N/A')}\n"
            findings_text += f"Key Insights: {', '.join(result.get('key_insights', []))}\n"

        user_content = f"""Topic: {topic}

Research Findings:
{findings_text}

Please provide a comprehensive summary of these findings."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        summary = self.openrouter.extract_response_content(response)

        return summary

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL and content similarity."""

        seen_urls = set()
        deduplicated = []

        for result in results:
            url = result.get('url', '').lower()
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)

        return deduplicated

    def _calculate_overall_credibility(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall credibility score for the research."""

        if not results:
            return 0.0

        credibility_scores = [
            result.get('credibility_score', 0.5) for result in results
        ]

        return sum(credibility_scores) / len(credibility_scores)

    async def _store_research_results(self, results: List[Dict[str, Any]]) -> None:
        """Store research results in the database."""

        if not self.session_id:
            return

        async with get_db_session() as session:
            for result in results:
                research_result = ResearchResult(
                    session_id=self.session_id,
                    source_url=result.get('url', ''),
                    title=result.get('title', ''),
                    content=result.get('content', result.get('snippet', '')),
                    relevance_score=result.get('relevance_score', 0.0),
                    credibility_score=result.get('credibility_score', 0.0),
                    metadata=json.dumps({
                        'key_insights': result.get('key_insights', []),
                        'content_type': result.get('content_type', 'unknown'),
                        'source': result.get('source', '')
                    })
                )
                session.add(research_result)
            await session.commit()