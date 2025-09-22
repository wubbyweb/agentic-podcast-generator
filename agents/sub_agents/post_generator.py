"""LinkedIn Post Generator Sub-agent."""

import json
import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from database.connection import get_db_session
from database.models import GeneratedContent

logger = logging.getLogger(__name__)

class PostGenerator(BaseAgent):
    """LinkedIn Post Generator agent for creating engaging professional content."""

    def __init__(self):
        super().__init__("post_generator", "post")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a LinkedIn post based on research and keywords."""

        self.validate_input(input_data, ["topic", "research", "keywords"])

        topic = input_data["topic"]
        research = input_data["research"]
        keywords = input_data["keywords"]

        # Generate LinkedIn post
        post_content = await self._generate_linkedin_post(topic, research, keywords)

        # Analyze post quality
        quality_metrics = await self._analyze_post_quality(post_content, topic)

        # Store generated content
        await self._store_generated_content(post_content, quality_metrics)

        return {
            "content": post_content,
            "word_count": len(post_content.split()),
            "quality_score": quality_metrics.get("overall_score", 0.0),
            "engagement_potential": quality_metrics.get("engagement_score", 0.0),
            "readability_score": quality_metrics.get("readability_score", 0.0),
            "seo_optimization": quality_metrics.get("seo_score", 0.0),
            "hashtags_included": self._extract_hashtags(post_content),
            "call_to_action": quality_metrics.get("has_cta", False)
        }

    async def _generate_linkedin_post(
        self,
        topic: str,
        research: Dict[str, Any],
        keywords: Dict[str, Any]
    ) -> str:
        """Generate an engaging LinkedIn post using research and keywords."""

        system_prompt = """You are a professional content creator specializing in LinkedIn posts. Create engaging, professional content that:

1. Hooks the reader in the first 2-3 lines
2. Provides valuable insights from the research
3. Uses conversational, authentic language
4. Includes relevant hashtags naturally
5. Ends with a question or call-to-action
6. Stays between 150-250 words
7. Incorporates 3-5 relevant keywords naturally
8. Uses emojis sparingly and appropriately
9. Maintains professional yet approachable tone
10. Includes specific examples or data points from research

Structure the post with:
- Attention-grabbing opening
- 2-3 key insights with context
- Personal/professional perspective
- Call-to-action question
- Relevant hashtags"""

        # Extract key information from research
        research_summary = research.get("summary", "")
        key_findings = research.get("results", [])

        # Extract keywords and hashtags
        keyword_list = keywords.get("keywords", [])[:8]  # Top 8 keywords
        hashtag_list = keywords.get("hashtags", [])[:5]  # Top 5 hashtags

        # Build research context
        research_context = f"""
Research Summary: {research_summary}

Key Findings:
{self._format_key_findings(key_findings)}

Available Keywords: {', '.join(keyword_list)}
Available Hashtags: {', '.join(hashtag_list)}"""

        user_content = f"""Topic: {topic}

{research_context}

Create an engaging LinkedIn post that leverages this research and incorporates relevant keywords naturally. The post should drive professional discussion and engagement."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        post_content = self.openrouter.extract_response_content(response)

        # Clean and format the post
        post_content = self._clean_post_content(post_content)

        return post_content

    def _format_key_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format key findings for the prompt."""

        formatted = ""
        for i, finding in enumerate(findings[:5], 1):  # Top 5 findings
            title = finding.get('title', f'Finding {i}')
            content = finding.get('content', finding.get('snippet', ''))
            relevance = finding.get('relevance_score', 0.0)

            if relevance > 0.6:  # Only include highly relevant findings
                formatted += f"{i}. {title}: {content[:100]}...\n"

        return formatted

    def _clean_post_content(self, content: str) -> str:
        """Clean and format the generated post content."""

        # Remove any markdown formatting
        content = content.replace('**', '').replace('*', '')

        # Ensure proper line breaks
        content = content.replace('\\n', '\n')

        # Remove excessive whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n\n'.join(lines)

        # Ensure the content doesn't start or end with hashtags
        # (they should be integrated naturally)

        return content.strip()

    async def _analyze_post_quality(self, post_content: str, topic: str) -> Dict[str, Any]:
        """Analyze the quality of the generated post."""

        system_prompt = """Analyze the quality of this LinkedIn post based on:

1. Engagement potential (0-1): How likely is it to generate comments/shares?
2. Readability (0-1): How easy is it to read and understand?
3. SEO optimization (0-1): How well does it incorporate keywords?
4. Content value (0-1): How valuable are the insights provided?
5. Call-to-action effectiveness (0-1): How compelling is the CTA?
6. Professional tone (0-1): How appropriate is the professional level?
7. Hashtag integration (0-1): How naturally are hashtags incorporated?

Return analysis in JSON format with scores and boolean flags."""

        user_content = f"""Topic: {topic}

Post Content:
{post_content}

Analyze this LinkedIn post for quality metrics."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        analysis_content = self.openrouter.extract_response_content(response)

        try:
            analysis = json.loads(analysis_content)
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = self._fallback_quality_analysis(post_content)

        # Calculate overall score
        score_components = [
            analysis.get('engagement_potential', 0.7),
            analysis.get('readability', 0.7),
            analysis.get('seo_optimization', 0.7),
            analysis.get('content_value', 0.7),
            analysis.get('call_to_action_effectiveness', 0.7),
            analysis.get('professional_tone', 0.7),
            analysis.get('hashtag_integration', 0.7)
        ]

        analysis['overall_score'] = sum(score_components) / len(score_components)

        return analysis

    def _fallback_quality_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback quality analysis if JSON parsing fails."""

        word_count = len(content.split())
        has_question = '?' in content
        has_hashtags = '#' in content
        has_emojis = any(char in content for char in ['🤖', '💼', '📈', '🚀', '💡', '🔍', '📊'])

        return {
            'engagement_potential': 0.8 if has_question else 0.6,
            'readability': 0.8 if 150 <= word_count <= 250 else 0.6,
            'seo_optimization': 0.7,
            'content_value': 0.7,
            'call_to_action_effectiveness': 0.8 if has_question else 0.5,
            'professional_tone': 0.8,
            'hashtag_integration': 0.9 if has_hashtags else 0.5,
            'has_emojis': has_emojis,
            'word_count': word_count,
            'has_cta': has_question
        }

    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from the post content."""

        import re
        hashtags = re.findall(r'#\w+', content)
        return list(set(hashtags))  # Remove duplicates

    async def _store_generated_content(self, content: str, quality_metrics: Dict[str, Any]) -> None:
        """Store the generated content in the database."""

        if not self.session_id:
            return

        async with get_db_session() as session:
            generated_content = GeneratedContent(
                session_id=self.session_id,
                content_type="linkedin_post",
                content=content,
                metadata=json.dumps({
                    'quality_metrics': quality_metrics,
                    'word_count': len(content.split()),
                    'hashtags': self._extract_hashtags(content),
                    'has_cta': quality_metrics.get('has_cta', False),
                    'engagement_score': quality_metrics.get('engagement_potential', 0.0)
                }),
                quality_score=quality_metrics.get('overall_score', 0.0)
            )
            session.add(generated_content)
            await session.commit()

    def _optimize_for_linkedin(self, content: str) -> str:
        """Apply LinkedIn-specific optimizations to the content."""

        # LinkedIn best practices:
        # - Start with a hook
        # - Use line breaks for readability
        # - Include 3-5 hashtags
        # - End with a question
        # - Keep under 250 words

        # Ensure line breaks for mobile readability
        if '\n' not in content:
            # Add line breaks every 80-100 characters for readability
            words = content.split()
            lines = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 80:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            content = '\n'.join(lines)

        return content