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

logger = logging.getLogger(__name__)

class MasterAgent(BaseAgent):
    """Master Agent that orchestrates all sub-agents."""

    def __init__(self):
        super().__init__("master", "master")
        self.sub_agents = {}

    async def process_topic(self, topic: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        """Main workflow orchestration.

        Args:
            topic: The topic to process
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

            # Step 1: Analyze topic with GPT-5
            analysis = await self.analyze_topic(topic)

            # Step 2: Initialize sub-agents
            await self.initialize_sub_agents()

            # Step 3: Execute parallel tasks (Web Research + Keyword Generation)
            research_task = self.sub_agents['web_researcher'].execute_with_logging({
                "topic": topic,
                "analysis": analysis
            })
            keyword_task = self.sub_agents['keyword_generator'].execute_with_logging({
                "topic": topic,
                "analysis": analysis
            })

            # Run parallel tasks
            research_results, keywords = await asyncio.gather(research_task, keyword_task)

            # Step 4: Generate LinkedIn post
            post_result = await self.sub_agents['post_generator'].execute_with_logging({
                "topic": topic,
                "research": research_results,
                "keywords": keywords
            })

            # Step 5: Generate voice dialog
            voice_result = await self.sub_agents['voice_dialog'].execute_with_logging({
                "linkedin_post": post_result["content"]
            })

            # Step 6: Update session status
            await update_session_status(self.session_id, "completed")

            # Step 7: Return final results
            return {
                "session_id": self.session_id,
                "topic": topic,
                "analysis": analysis,
                "linkedin_post": post_result["content"],
                "voice_dialog": voice_result["dialog"],
                "keywords": keywords.get("keywords", []),
                "hashtags": keywords.get("hashtags", []),
                "research_summary": research_results.get("summary", "")
            }

        except Exception as e:
            # Update session status on failure
            if self.session_id:
                await update_session_status(self.session_id, "failed", str(e))
            raise

    async def analyze_topic(self, topic: str) -> Dict[str, Any]:
        """Analyze topic using GPT-5 to understand requirements."""

        system_prompt = """You are an expert content strategist. Analyze the given topic and provide:
1. Key themes and angles to explore
2. Target audience characteristics
3. Content goals and objectives
4. Research directions needed
5. Content style recommendations

Provide your analysis in JSON format with these keys: themes, audience, goals, research_directions, style."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(f"Analyze this topic for content creation: {topic}")
        ]

        response = await self.call_openrouter(messages)
        content = self.openrouter.extract_response_content(response)

        try:
            analysis = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "themes": [topic],
                "audience": "general professional audience",
                "goals": ["inform and engage"],
                "research_directions": ["general information gathering"],
                "style": "professional and conversational"
            }

        # Log the analysis
        await self.log_action("topic_analysis", input_data={"topic": topic}, output_data=analysis)

        return analysis

    async def initialize_sub_agents(self) -> None:
        """Initialize all sub-agents with proper context."""

        # Initialize Web Researcher
        self.sub_agents['web_researcher'] = WebResearcher()
        self.sub_agents['web_researcher'].session_id = self.session_id
        await self.sub_agents['web_researcher'].__aenter__()

        # Initialize Keyword Generator
        self.sub_agents['keyword_generator'] = KeywordGenerator()
        self.sub_agents['keyword_generator'].session_id = self.session_id
        await self.sub_agents['keyword_generator'].__aenter__()

        # Initialize Post Generator
        self.sub_agents['post_generator'] = PostGenerator()
        self.sub_agents['post_generator'].session_id = self.session_id
        await self.sub_agents['post_generator'].__aenter__()

        # Initialize Voice Dialog Generator
        self.sub_agents['voice_dialog'] = VoiceDialogGenerator()
        self.sub_agents['voice_dialog'].session_id = self.session_id
        await self.sub_agents['voice_dialog'].__aenter__()

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