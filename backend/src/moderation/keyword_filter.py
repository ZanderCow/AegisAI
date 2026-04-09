"""Keyword-based pre-send content filter.

Checks user messages against a list of harmful keywords before the message
is forwarded to any AI provider. Matching is case-insensitive.
"""
import re

from src.moderation.keywords import HARMFUL_KEYWORDS

MODERATION_RESPONSE = "That's Dangerous"


def is_harmful(text: str) -> bool:
    """Returns True if the text contains any harmful keyword on a word boundary.

    Uses word-boundary matching to avoid false positives from words that contain
    a keyword as a substring (e.g. 'skill' matching 'kill').

    Args:
        text (str): The user message to check.

    Returns:
        bool: True if a harmful keyword is found, False otherwise.
    """
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in HARMFUL_KEYWORDS)
