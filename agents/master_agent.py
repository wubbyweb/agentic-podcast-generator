"""Master Agent that orchestrates all sub-agents."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from .sub_agents.web_researcher import WebResearcher
from .sub_agents.keyword_generator import KeywordGenerator
from .sub_agents.post_generator import PostGenerator
from .sub_agents.voice_dialog import VoiceDialogGenerator
from database.connection import create_session_record, update_session_status
from services.openrouter_client import OpenRouterClient
from config.settings import config

logger = logging.getLogger(__name__)

class MasterAgent(BaseAgent):
    """Master Agent that orchestrates all sub-agents."""

    def __init__(self):
        super().__init__("master", "master")
        self.sub_agents = {}

    async def process_topic(self, topic: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        # Get research from Perplexity first
        research_response = await self.get_perplexity_research(topic)
        return await self.process_topic_with_research(topic, research_response, session_id)

    async def process_topic_with_research(self, topic: str, research_response: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        """Main workflow orchestration using provided research response.

        Args:
            topic: The topic to process
            research_response: Research response from Perplexity API
            session_id: Optional existing session ID to resume

        Returns:
            Dictionary containing all results
        """

        try:
            # Create or resume session
            if session_id is None:
                self.session_id = await create_session_record(topic)
                logger.info(f"Created new session {self.session_id} for topic: {topic}")
            else:
                self.session_id = session_id
                logger.info(f"Resuming session {self.session_id}")

            # Step 1: Initialize all sub-agents (post, voice, keyword)
            await self.initialize_all_agents()

            # Step 2: Prepare research data from Perplexity response
            research_results = {
                "topic": topic,
                "research_plan": {"search_queries": [topic], "source_types": ["perplexity"]},
                "results": [{
                    "title": f"Perplexity Research: {topic}",
                    "url": f"https://perplexity.ai/search?q={topic.replace(' ', '+')}",
                    "snippet": research_response[:500],
                    "content": research_response,
                    "source": "perplexity",
                    "relevance_score": 1.0,
                    "credibility_score": 0.9
                }],
                "summary": research_response,
                "total_sources": 1,
                "credibility_score": 0.9
            }

            # Step 3: Run sub-agents in parallel
            logger.info("Running sub-agents in parallel")

            # Prepare inputs for each sub-agent
            post_input = {
                "topic": topic,
                "research": research_results,
                "research_response": research_response
            }

            voice_input = {
                "topic": topic,
                "research_response": research_response
            }

            keyword_input = {
                "topic": topic,
                "research_response": research_response
            }

            # Execute all sub-agents concurrently
            post_task = self.sub_agents['post_generator'].execute_with_logging(post_input)
            voice_task = self.sub_agents['voice_dialog'].execute_with_logging(voice_input)
            keyword_task = self.sub_agents['keyword_generator'].execute_with_logging(keyword_input)

            post_result, voice_result, keyword_result = await asyncio.gather(
                post_task, voice_task, keyword_task, return_exceptions=True
            )

            # Handle any exceptions from parallel execution
            results = {}
            for name, result in [("post", post_result), ("voice", voice_result), ("keyword", keyword_result)]:
                if isinstance(result, Exception):
                    logger.error(f"Sub-agent {name} failed: {result}")
                    results[name] = None
                else:
                    results[name] = result

            # Step 4: Update session status
            await update_session_status(self.session_id, "completed")

            # Step 5: Return final results
            return {
                "session_id": self.session_id,
                "topic": topic,
                "research_response": research_response,
                "linkedin_post": results.get("post", {}).get("content", "") if results.get("post") else "",
                "voice_dialog": results.get("voice", {}).get("dialog", "") if results.get("voice") else "",
                "keywords": results.get("keyword", {}).get("keywords", []) if results.get("keyword") else [],
                "hashtags": results.get("keyword", {}).get("hashtags", []) if results.get("keyword") else [],
                "research_summary": research_response[:500]
            }

        except Exception as e:
            # Update session status on failure
            if self.session_id:
                await update_session_status(self.session_id, "failed", str(e))
            raise

    async def get_perplexity_research(self, topic: str) -> str:
        """Get comprehensive research from Perplexity API using sonar model."""
        async with OpenRouterClient(config.openrouter_api_key) as client:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert research assistant. Provide comprehensive, up-to-date research and analysis on the given topic. Include current facts, key insights, trends, and relevant data points."
                },
                {
                    "role": "user",
                    "content": f"Research and analyze this topic comprehensively: {topic}. Provide detailed findings, current developments, and key insights."
                }
            ]

            response = await client.chat_completion(
                model="perplexity/sonar",
                messages=messages,
                max_tokens=4000,
                temperature=0.3
            )

            return client.extract_response_content(response)

    async def analyze_topic(self, topic: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility - now uses Perplexity research."""
        research_response = await self.get_perplexity_research(topic)

        # Parse the research response into structured analysis
        analysis = {
            "themes": [topic],
            "audience": "general professional audience",
            "goals": ["inform and engage"],
            "research_findings": research_response,
            "keywords": [topic],
            "hashtags": [f"#{topic.replace(' ', '')}"],
            "style": "professional and conversational",
            "summary": research_response[:500]
        }

        # Log the analysis
        await self.log_action("topic_analysis", input_data={"topic": topic}, output_data=analysis)

        return analysis

    async def initialize_all_agents(self) -> None:
        """Initialize all sub-agents for parallel execution."""

        # Initialize Post Generator
        self.sub_agents['post_generator'] = PostGenerator()
        self.sub_agents['post_generator'].session_id = self.session_id
        await self.sub_agents['post_generator'].__aenter__()

        # Initialize Voice Dialog Generator
        self.sub_agents['voice_dialog'] = VoiceDialogGenerator()
        self.sub_agents['voice_dialog'].session_id = self.session_id
        await self.sub_agents['voice_dialog'].__aenter__()

        # Initialize Keyword Generator
        self.sub_agents['keyword_generator'] = KeywordGenerator()
        self.sub_agents['keyword_generator'].session_id = self.session_id
        await self.sub_agents['keyword_generator'].__aenter__()

        logger.info("All sub-agents initialized")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Exit sub-agents
        for sub_agent in self.sub_agents.values():
            if hasattr(sub_agent, '__aexit__'):
                await sub_agent.__aexit__(exc_type, exc_val, exc_tb)

        # Exit master
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with BaseAgent interface."""
        topic = input_data.get("topic", "")
        if not topic:
            raise ValueError("Topic is required for Master Agent execution")

        return await self.process_topic(topic)

    async def get_session_status(self, session_id: int) -> Dict[str, Any]:
        """Get the status of a session."""
        # This would query the database for session status
        # Implementation would go here
        pass

    async def resume_session(self, session_id: int) -> Dict[str, Any]:
        """Resume a previously interrupted session."""
        # Implementation for resuming sessions would go here
        # This would involve checking what steps were completed and continuing from there
        pass