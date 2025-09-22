"""Voice Dialog Generator Sub-agent."""

import json
import re
import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from database.connection import get_db_session
from database.models import GeneratedContent

logger = logging.getLogger(__name__)

class VoiceDialogGenerator(BaseAgent):
    """Voice Dialog Generator agent for creating conversational voice scripts."""

    def __init__(self):
        super().__init__("voice_dialog", "voice_dialog")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a voice dialog script from research response."""

        self.validate_input(input_data, ["topic", "research_response"])

        topic = input_data["topic"]
        research_response = input_data["research_response"]

        # Generate voice dialog
        voice_dialog = await self._generate_voice_dialog(topic, research_response)

        # Analyze dialog quality
        quality_metrics = await self._analyze_dialog_quality(voice_dialog)

        # Add timing and pacing information
        enhanced_dialog = await self._add_timing_and_pacing(voice_dialog)

        # Store generated content
        await self._store_generated_content(enhanced_dialog, quality_metrics)

        return {
            "dialog": enhanced_dialog,
            "word_count": len(enhanced_dialog.split()),
            "estimated_duration": quality_metrics.get("estimated_duration_seconds", 0),
            "naturalness_score": quality_metrics.get("naturalness_score", 0.0),
            "engagement_score": quality_metrics.get("engagement_score", 0.0),
            "pacing_score": quality_metrics.get("pacing_score", 0.0),
            "clarity_score": quality_metrics.get("clarity_score", 0.0),
            "segments": self._extract_dialog_segments(enhanced_dialog)
        }

    async def _generate_voice_dialog(self, topic: str, research_response: str) -> str:
        """Generate a conversational voice dialog from LinkedIn post content."""

        system_prompt = """You are a professional voice content creator and scriptwriter. Transform the research into a natural, conversational podcast script that:

1. Sounds like a professional speaking naturally to an audience
2. Maintains the key insights and value from the research
3. Uses conversational language with contractions and personal touches
4. Includes natural pauses and emphasis indicators
5. Adds transitional phrases for smooth flow
6. Incorporates rhetorical questions and engagement elements
7. Uses vocal variety indicators (enthusiasm, emphasis, pauses)
8. Maintains the professional yet approachable tone
9. Includes calls-to-action that work well in audio format
10. Structures content for 2-3 minute delivery

Format the script with:
- [Opening music/intro]
- Natural speech patterns
- [Sound effects or music cues]
- [Emphasis] for key points
- (Pause) for natural breaks
- Clear paragraph breaks for breathing room"""

        user_content = f"""Topic: {topic}

Research from Perplexity AI:
{research_response}

Create a conversational podcast script that leverages this research. The script should sound natural when spoken aloud and be suitable for a 2-3 minute delivery."""

        messages = [
            self.create_system_message(system_prompt),
            self.create_user_message(user_content)
        ]

        response = await self.call_openrouter(messages)
        voice_dialog = self.openrouter.extract_response_content(response)

        # Clean and format the dialog
        voice_dialog = self._clean_dialog_content(voice_dialog)

        return voice_dialog

    def _clean_dialog_content(self, content: str) -> str:
        """Clean and format the generated voice dialog."""

        # Remove any markdown formatting that might interfere with voice
        content = re.sub(r'\*\*([^*]+)\*\*', r'[Emphasis: \1]', content)
        content = re.sub(r'\*([^*]+)\*', r'[Emphasis: \1]', content)

        # Ensure proper line breaks
        content = content.replace('\\n', '\n')

        # Clean up excessive whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n\n'.join(lines)

        # Remove any HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&', '&')
        content = content.replace('<', '<')
        content = content.replace('>', '>')

        return content.strip()

    async def _analyze_dialog_quality(self, dialog: str) -> Dict[str, Any]:
        """Analyze the quality of the generated voice dialog."""

        system_prompt = """Analyze this voice dialog script for audio content quality:

1. Naturalness (0-1): How conversational and authentic does it sound?
2. Engagement (0-1): How well does it maintain listener interest?
3. Pacing (0-1): How well does it flow with appropriate pauses and emphasis?
4. Clarity (0-1): How clear and easy to understand is the content?
5. Professional tone (0-1): How appropriate is the professional level?
6. Length appropriateness (0-1): Is it suitable for the intended duration?
7. Call-to-action effectiveness (0-1): How compelling are the CTAs for audio?

Also estimate:
- Total word count
- Estimated speaking time in seconds (150 words/minute average)
- Number of natural pause points
- Vocal variety indicators present

Return analysis in JSON format."""

        user_content = f"""Analyze this voice dialog script:

{dialog}

Provide quality metrics and timing estimates."""

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
            analysis = self._fallback_dialog_analysis(dialog)

        return analysis

    def _fallback_dialog_analysis(self, dialog: str) -> Dict[str, Any]:
        """Fallback analysis if JSON parsing fails."""

        word_count = len(dialog.split())
        estimated_duration = (word_count / 150) * 60  # 150 words per minute

        has_emphasis = '[Emphasis:' in dialog or '[emphasis:' in dialog
        has_pauses = '(Pause)' in dialog or '(pause)' in dialog
        has_questions = '?' in dialog
        has_transitions = any(word in dialog.lower() for word in [
            'now', 'also', 'but', 'however', 'let me', 'you know', 'actually'
        ])

        return {
            'naturalness_score': 0.8 if has_transitions else 0.6,
            'engagement_score': 0.8 if has_questions else 0.6,
            'pacing_score': 0.8 if has_pauses else 0.6,
            'clarity_score': 0.8 if word_count > 100 else 0.6,
            'professional_tone': 0.8,
            'length_appropriateness': 0.8 if 200 <= word_count <= 400 else 0.6,
            'cta_effectiveness': 0.7 if has_questions else 0.5,
            'word_count': word_count,
            'estimated_duration_seconds': int(estimated_duration),
            'has_emphasis_indicators': has_emphasis,
            'has_pause_indicators': has_pauses,
            'has_engagement_elements': has_questions,
            'vocal_variety_score': 0.8 if (has_emphasis and has_pauses) else 0.6
        }

    async def _add_timing_and_pacing(self, dialog: str) -> str:
        """Add timing and pacing information to the dialog."""

        # This is a simplified implementation
        # In a production system, you might use more sophisticated timing analysis

        # Add basic timing estimates
        word_count = len(dialog.split())
        estimated_duration = (word_count / 150) * 60  # 150 words per minute

        # Add timing header
        timing_info = f"[Estimated Duration: {int(estimated_duration)} seconds | {word_count} words]\n\n"

        enhanced_dialog = timing_info + dialog

        # Add more detailed pacing if needed
        if '(Pause)' not in enhanced_dialog and '(pause)' not in enhanced_dialog:
            # Add some basic pause indicators
            enhanced_dialog = self._add_basic_pauses(enhanced_dialog)

        return enhanced_dialog

    def _add_basic_pauses(self, dialog: str) -> str:
        """Add basic pause indicators to improve pacing."""

        # Add pauses after questions
        dialog = re.sub(r'(\?)\s+', r'\1\n\n(Pause for engagement)\n\n', dialog)

        # Add pauses after key transitions
        transitions = [
            r'(\bNow\b)',
            r'(\bBut\b)',
            r'(\bHowever\b)',
            r'(\bAlso\b)',
            r'(\bLet me\b)',
            r'(\bYou know\b)'
        ]

        for transition in transitions:
            dialog = re.sub(
                transition + r'\s+',
                r'\1... (brief pause)\n',
                dialog,
                flags=re.IGNORECASE
            )

        return dialog

    def _extract_dialog_segments(self, dialog: str) -> List[Dict[str, str]]:
        """Extract dialog segments for analysis."""

        segments = []
        lines = dialog.split('\n')

        current_segment = ""
        segment_type = "content"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for segment markers
            if line.startswith('[') and line.endswith(']'):
                # Save previous segment if it exists
                if current_segment:
                    segments.append({
                        "type": segment_type,
                        "content": current_segment.strip(),
                        "word_count": len(current_segment.split())
                    })

                # Start new segment
                if 'music' in line.lower() or 'intro' in line.lower():
                    segment_type = "music_cue"
                elif 'emphasis' in line.lower():
                    segment_type = "emphasis"
                elif 'pause' in line.lower():
                    segment_type = "pause"
                else:
                    segment_type = "cue"

                current_segment = line

            else:
                current_segment += " " + line

        # Add final segment
        if current_segment:
            segments.append({
                "type": segment_type,
                "content": current_segment.strip(),
                "word_count": len(current_segment.split())
            })

        return segments

    async def _store_generated_content(self, content: str, quality_metrics: Dict[str, Any]) -> None:
        """Store the generated voice dialog in the database."""

        if not self.session_id:
            return

        async with get_db_session() as session:
            generated_content = GeneratedContent(
                session_id=self.session_id,
                content_type="voice_dialog",
                content=content,
                metadata=json.dumps({
                    'quality_metrics': quality_metrics,
                    'word_count': len(content.split()),
                    'estimated_duration': quality_metrics.get('estimated_duration_seconds', 0),
                    'segments': self._extract_dialog_segments(content),
                    'naturalness_score': quality_metrics.get('naturalness_score', 0.0),
                    'engagement_score': quality_metrics.get('engagement_score', 0.0)
                }),
                quality_score=quality_metrics.get('naturalness_score', 0.0)
            )
            session.add(generated_content)
            await session.commit()

    def _optimize_for_voice(self, content: str) -> str:
        """Apply voice-specific optimizations."""

        # Voice content best practices:
        # - Use contractions (I'm, you're, it's)
        # - Avoid complex sentences
        # - Include natural pauses
        # - Use vocal emphasis indicators
        # - Keep sentences conversational

        # Convert formal language to conversational
        content = re.sub(r'\bI am\b', "I'm", content)
        content = re.sub(r'\bYou are\b', "You're", content)
        content = re.sub(r'\bIt is\b', "It's", content)
        content = re.sub(r'\bWe are\b', "We're", content)
        content = re.sub(r'\bThey are\b', "They're", content)
        content = re.sub(r'\bDo not\b', "Don't", content)
        content = re.sub(r'\bCannot\b', "Can't", content)

        return content