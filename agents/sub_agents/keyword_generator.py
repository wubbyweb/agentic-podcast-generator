"""Keyword Generator Sub-agent using Gemini 2.5 Flash."""

import json
import re
import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from database.connection import get_db_session
from database.models import Keyword

logger = logging.getLogger(__name__)

class KeywordGenerator(BaseAgent):
    """Keyword Generator agent using Gemini 2.5 Flash for SEO-optimized content."""

    def __init__(self):
        super().__init__("keyword_generator", "keyword")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate keywords and hashtags for the given topic."""

        self.validate_input(input_data, ["topic"])

        topic = input_data["topic"]
        analysis = input_data.get("analysis", {})

        # Generate keywords using Gemini 2.5 Flash
        keyword_data = await self._generate_keywords(topic, analysis)

        # Extract and categorize keywords
        keywords = keyword_data.get("keywords", [])
        hashtags = keyword_data.get("hashtags", [])

        # Validate and clean keywords
        keywords = self._clean_keywords(keywords)
        hashtags = self._clean_hashtags(hashtags)

        # Calculate relevance scores
        keyword_scores = await self._calculate_relevance_scores(topic, keywords)

        # Store results in database
        await self._store_keywords(keywords, hashtags, keyword_scores)

        return {
            "topic": topic,
            "keywords": keywords,
            "hashtags": hashtags,
            "keyword_scores": keyword_scores,
            "total_keywords": len(keywords),
            "total_hashtags": len(hashtags),
            "categories": keyword_data.get("categories", [])
        }

    async def _generate_keywords(self, topic: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive keywords and hashtags using Gemini 2.5 Flash."""

        system_prompt = """You are an expert SEO strategist and content marketer specializing in keyword research and social media optimization.

Generate comprehensive keyword and hashtag suggestions that include:
1. Primary keywords (exact match and close variations)
2. Long-tail keywords (2-4 word phrases)
3. Related keywords and synonyms
4. Trending and emerging terms
5. Question-based keywords
6. Hashtags for social media platforms (LinkedIn, Twitter, Instagram)
7. Industry-specific terminology
8. Geographic variations if applicable

Categorize keywords by:
- Search intent (informational, commercial, transactional)
- Competition level (high, medium, low)
- Content type suitability

Return results in JSON format with these keys: keywords, hashtags, categories, search_intent_breakdown."""

        # Build context from topic analysis
        context_info = ""
        if analysis:
            themes = analysis.get("themes", [])
            audience = analysis.get("audience", "")
            context_info = f"""
Topic Analysis Context:
- Key Themes: {', '.join(themes) if isinstance(themes, list) else themes}
- Target Audience: {audience}
- Content Goals: {analysis.get('goals', '')}
- Style Requirements: {analysis.get('style', '')}"""

        user_content = f"""Topic: {topic}{context_info}

Generate comprehensive keyword and hashtag suggestions for content creation, social media posts, and SEO optimization.

Focus on:
- Current trends and emerging topics
- Professional and industry-specific terminology
- Social media friendly hashtags
- Search engine optimization potential
- Content marketing effectiveness"""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        content = self.openrouter.extract_response_content(response)

        try:
            keyword_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback keyword generation
            keyword_data = self._generate_fallback_keywords(topic)

        return keyword_data

    def _generate_fallback_keywords(self, topic: str) -> Dict[str, Any]:
        """Generate basic keywords if JSON parsing fails."""

        # Clean and normalize topic
        clean_topic = re.sub(r'[^\w\s]', '', topic.lower())

        # Generate basic keywords
        keywords = [
            topic,
            f"{clean_topic} guide",
            f"{clean_topic} tips",
            f"best {clean_topic}",
            f"{clean_topic} trends",
            f"{clean_topic} news",
            f"how to {clean_topic}",
            f"{clean_topic} for beginners",
            f"latest {clean_topic}",
            f"{clean_topic} insights"
        ]

        # Generate hashtags
        hashtag_base = re.sub(r'\s+', '', clean_topic.title())
        hashtags = [
            f"#{hashtag_base}",
            f"#{clean_topic.replace(' ', '')}",
            "#ContentCreation",
            "#DigitalMarketing",
            "#SEO",
            "#SocialMedia"
        ]

        return {
            "keywords": keywords,
            "hashtags": hashtags,
            "categories": ["primary", "long_tail", "questions"],
            "search_intent_breakdown": {
                "informational": keywords[:5],
                "commercial": keywords[5:8],
                "transactional": keywords[8:]
            }
        }

    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """Clean and validate keyword list."""

        cleaned = []
        seen = set()

        for keyword in keywords:
            if isinstance(keyword, str):
                # Clean the keyword
                cleaned_keyword = self._clean_single_keyword(keyword)

                # Skip if too short, too long, or duplicate
                if (len(cleaned_keyword) >= 3 and
                    len(cleaned_keyword) <= 80 and
                    cleaned_keyword.lower() not in seen):

                    cleaned.append(cleaned_keyword)
                    seen.add(cleaned_keyword.lower())

        return cleaned[:30]  # Limit to top 30 keywords

    def _clean_hashtags(self, hashtags: List[str]) -> List[str]:
        """Clean and validate hashtag list."""

        cleaned = []
        seen = set()

        for hashtag in hashtags:
            if isinstance(hashtag, str):
                # Ensure hashtag starts with #
                if not hashtag.startswith('#'):
                    hashtag = f"#{hashtag}"

                # Clean the hashtag (remove spaces, special chars except #)
                cleaned_hashtag = re.sub(r'[^\w#]', '', hashtag)

                # Skip if too short, too long, or duplicate
                hashtag_text = cleaned_hashtag.lower()
                if (len(cleaned_hashtag) >= 2 and
                    len(cleaned_hashtag) <= 100 and
                    hashtag_text not in seen):

                    cleaned.append(cleaned_hashtag)
                    seen.add(hashtag_text)

        return cleaned[:20]  # Limit to top 20 hashtags

    def _clean_single_keyword(self, keyword: str) -> str:
        """Clean a single keyword string."""

        # Remove extra whitespace
        cleaned = ' '.join(keyword.split())

        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s\-&\']', '', cleaned)

        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())

        return cleaned.strip()

    async def _calculate_relevance_scores(self, topic: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate relevance scores for keywords based on topic match."""

        scores = {}

        # Simple relevance scoring based on word overlap
        topic_words = set(re.findall(r'\b\w+\b', topic.lower()))

        for keyword in keywords:
            keyword_words = set(re.findall(r'\b\w+\b', keyword.lower()))

            # Calculate Jaccard similarity
            intersection = len(topic_words.intersection(keyword_words))
            union = len(topic_words.union(keyword_words))

            if union > 0:
                relevance_score = intersection / union
            else:
                relevance_score = 0.0

            # Boost score for exact matches
            if keyword.lower() in topic.lower() or topic.lower() in keyword.lower():
                relevance_score = min(1.0, relevance_score + 0.3)

            # Boost score for longer, more specific keywords
            word_count = len(keyword_words)
            if word_count > 1:
                relevance_score = min(1.0, relevance_score + (word_count - 1) * 0.1)

            scores[keyword] = round(relevance_score, 3)

        return scores

    async def _store_keywords(
        self,
        keywords: List[str],
        hashtags: List[str],
        keyword_scores: Dict[str, float]
    ) -> None:
        """Store keywords and hashtags in the database."""

        if not self.session_id:
            return

        async with get_db_session() as session:
            # Store keywords
            for keyword in keywords:
                keyword_type = "hashtag" if keyword.startswith('#') else "keyword"
                actual_keyword = keyword[1:] if keyword.startswith('#') else keyword

                db_keyword = Keyword(
                    session_id=self.session_id,
                    keyword=actual_keyword,
                    keyword_type=keyword_type,
                    relevance_score=keyword_scores.get(keyword, 0.0),
                    category="generated"
                )
                session.add(db_keyword)

            # Store hashtags separately if not already included
            for hashtag in hashtags:
                if hashtag not in keywords:
                    db_hashtag = Keyword(
                        session_id=self.session_id,
                        keyword=hashtag[1:] if hashtag.startswith('#') else hashtag,
                        keyword_type="hashtag",
                        relevance_score=0.8,  # Default high score for curated hashtags
                        category="social_media"
                    )
                    session.add(db_hashtag)

            await session.commit()

    def _categorize_keywords(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Categorize keywords by type and intent."""

        categories = {
            "primary": [],
            "long_tail": [],
            "questions": [],
            "commercial": [],
            "informational": []
        }

        for keyword in keywords:
            word_count = len(keyword.split())

            # Categorize by length
            if word_count == 1:
                categories["primary"].append(keyword)
            elif word_count <= 3:
                categories["long_tail"].append(keyword)
            else:
                categories["long_tail"].append(keyword)

            # Categorize by intent
            lower_keyword = keyword.lower()
            if any(q in lower_keyword for q in ['how', 'what', 'why', 'when', 'where', 'who']):
                categories["questions"].append(keyword)
            elif any(c in lower_keyword for c in ['buy', 'price', 'cost', 'best', 'top', 'review']):
                categories["commercial"].append(keyword)
            else:
                categories["informational"].append(keyword)

        return categories