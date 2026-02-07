import re
from html import escape


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection and XSS attacks.
    """
    if not text:
        return text

    # HTML escape to prevent XSS
    text = escape(text)

    # Remove common prompt injection patterns
    injection_patterns = [
        r"ignore\s+(previous|above|all)\s+instructions?",
        r"disregard\s+(previous|above|all)\s+instructions?",
        r"forget\s+(previous|above|all)\s+instructions?",
        r"new\s+instructions?:",
        r"system\s*:",
        r"assistant\s*:",
        r"\[system\]",
        r"\[assistant\]",
        r"<\|.*?\|>",
        r"```system",
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

    return text.strip()


def sanitize_for_ai(text: str) -> str:
    """
    Sanitize input specifically for AI prompts.
    More aggressive filtering for AI context.
    """
    text = sanitize_input(text)

    # Additional AI-specific sanitization
    ai_patterns = [
        r"you\s+are\s+(now|actually)",
        r"pretend\s+(to\s+be|you\s+are)",
        r"roleplay\s+as",
        r"act\s+as\s+if",
        r"your\s+(new\s+)?role\s+is",
    ]

    for pattern in ai_patterns:
        text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

    return text
