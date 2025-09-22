"""Data validation utilities."""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse

def validate_topic(topic: str) -> bool:
    """Validate that a topic string is acceptable."""
    if not topic or not isinstance(topic, str):
        return False

    # Check length
    if len(topic.strip()) < 3:
        return False

    if len(topic.strip()) > 200:
        return False

    # Check for basic content
    if not re.search(r'[a-zA-Z]', topic):
        return False

    return True

def validate_content(content: str, content_type: str = "general") -> Dict[str, Any]:
    """Validate content and return validation results."""
    results = {
        "is_valid": True,
        "issues": [],
        "warnings": [],
        "stats": {
            "length": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n'))
        }
    }

    # Basic validation
    if not content or not isinstance(content, str):
        results["is_valid"] = False
        results["issues"].append("Content is empty or not a string")
        return results

    # Content type specific validation
    if content_type == "linkedin_post":
        results.update(_validate_linkedin_post(content))
    elif content_type == "voice_dialog":
        results.update(_validate_voice_dialog(content))
    elif content_type == "topic":
        results.update(_validate_topic_content(content))

    # General content checks
    if len(content.strip()) < 10:
        results["warnings"].append("Content is very short")

    if len(content.split()) > 1000:
        results["warnings"].append("Content is very long")

    return results

def _validate_linkedin_post(content: str) -> Dict[str, Any]:
    """Validate LinkedIn post content."""
    results = {"linkedin_checks": {}}

    # Check for hashtags
    hashtag_count = len(re.findall(r'#\w+', content))
    results["linkedin_checks"]["hashtag_count"] = hashtag_count

    if hashtag_count == 0:
        results["warnings"] = results.get("warnings", []) + ["No hashtags found"]
    elif hashtag_count > 5:
        results["warnings"] = results.get("warnings", []) + ["Too many hashtags"]

    # Check length
    word_count = len(content.split())
    if word_count < 50:
        results["warnings"] = results.get("warnings", []) + ["Post is quite short"]
    elif word_count > 300:
        results["warnings"] = results.get("warnings", []) + ["Post is quite long"]

    # Check for questions (engagement)
    question_count = len(re.findall(r'\?', content))
    results["linkedin_checks"]["question_count"] = question_count

    if question_count == 0:
        results["warnings"] = results.get("warnings", []) + ["No questions found (may reduce engagement)"]

    return results

def _validate_voice_dialog(content: str) -> Dict[str, Any]:
    """Validate voice dialog content."""
    results = {"voice_checks": {}}

    # Check for timing indicators
    has_timing = bool(re.search(r'\[.*?\]', content))
    results["voice_checks"]["has_timing_indicators"] = has_timing

    # Check for pauses
    pause_count = len(re.findall(r'\(Pause\)', content, re.IGNORECASE))
    results["voice_checks"]["pause_count"] = pause_count

    # Check for emphasis indicators
    emphasis_count = len(re.findall(r'\[Emphasis:.*?\]', content, re.IGNORECASE))
    results["voice_checks"]["emphasis_count"] = emphasis_count

    # Estimate duration (rough calculation: 150 words per minute)
    word_count = len(content.split())
    estimated_minutes = word_count / 150
    results["voice_checks"]["estimated_duration_minutes"] = round(estimated_minutes, 1)

    if estimated_minutes < 1:
        results["warnings"] = results.get("warnings", []) + ["Content is very short for audio"]
    elif estimated_minutes > 5:
        results["warnings"] = results.get("warnings", []) + ["Content is very long for audio"]

    return results

def _validate_topic_content(content: str) -> Dict[str, Any]:
    """Validate topic content."""
    results = {"topic_checks": {}}

    # Check for keywords
    word_count = len(content.split())
    results["topic_checks"]["word_count"] = word_count

    # Check for diversity of vocabulary
    words = re.findall(r'\b\w+\b', content.lower())
    unique_words = set(words)
    vocabulary_diversity = len(unique_words) / len(words) if words else 0
    results["topic_checks"]["vocabulary_diversity"] = round(vocabulary_diversity, 3)

    return results

def validate_url(url: str) -> bool:
    """Validate that a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def validate_json_string(json_str: str) -> tuple[bool, str]:
    """Validate that a string is valid JSON."""
    try:
        import json
        json.loads(json_str)
        return True, ""
    except json.JSONDecodeError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"

def validate_agent_name(name: str) -> bool:
    """Validate that an agent name is acceptable."""
    if not name or not isinstance(name, str):
        return False

    # Check length
    if len(name.strip()) < 2 or len(name.strip()) > 50:
        return False

    # Check for valid characters (alphanumeric, underscore, dash)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False

    # Check for reserved names
    reserved_names = ['system', 'admin', 'root', 'master', 'agent']
    if name.lower() in reserved_names:
        return False

    return True

def sanitize_content(content: str, max_length: int = 10000) -> str:
    """Sanitize content by removing potentially harmful elements."""
    if not content:
        return ""

    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "..."

    # Remove null bytes
    content = content.replace('\x00', '')

    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    return content.strip()