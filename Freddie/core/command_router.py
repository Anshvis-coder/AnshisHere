"""
Command Router for Freddie
===========================
Routes user input to appropriate handlers (AI, commands, memory, etc.)
"""

import logging
import re
from typing import Optional, Tuple
from config import ASSISTANT_NAME

logger = logging.getLogger(__name__)


class CommandRouter:
    """Routes user commands to appropriate handlers."""

    def __init__(self):
        # Patterns for command detection
        self.command_patterns = {
            "open_app": [
                r"open\s+(\w+)",
                r"launch\s+(\w+)",
                r"start\s+(\w+)",
            ],
            "close_app": [
                r"close\s+(\w+)",
                r"exit\s+(\w+)",
                r"quit\s+(\w+)",
            ],
            "browser": [
                r"(?:go to|open|visit)\s+(https?://\S+)",
                r"(?:search|google)\s+(?:for\s+)?(.+)",
                r"open\s+(youtube|github|google|reddit|twitter)",
            ],
            "file_operation": [
                r"(?:create|make)\s+(?:a\s+)?(folder|directory)\s+(?:called|named)?\s*(.+)",
                r"(?:create|make)\s+(?:a\s+)?(file)\s+(?:called|named)?\s*(.+)",
                r"(?:delete|remove)\s+(file|folder)\s+(.+)",
                r"(?:rename|move|copy)\s+(.+)",
                r"open\s+(folder|directory|file)\s+(.+)",
            ],
            "system_command": [
                r"what(?:'s| is)\s+(?:the\s+)?(?:current\s+)?(time|date)",
                r"(?:lock|shutdown|restart)\s+(?:pc|computer|system)?",
                r"(?:mute|unmute|volume)\s*(\d+)?",
                r"(?:battery|cpu|ram)\s+(?:level|usage|status)?",
            ],
            "memory": [
                r"remember\s+(?:that\s+)?(.+)",
                r"(?:what is|what's)\s+my\s+(.+)",
                r"save\s+(?:this|note)\s*[:\-]?\s*(.+)",
            ],
            "note": [
                r"(?:make|create|add)\s+a\s+note\s*[:\-]?\s*(.+)",
                r"note\s*[:\-]?\s*(.+)",
                r"(?:show|list|read)\s+(?:my\s+)?notes",
            ],
            "reminder": [
                r"remind\s+me\s+(?:to\s+)?(.+)\s+(?:at|on)\s+(.+)",
                r"set\s+a\s+reminder\s+(?:for\s+)?(.+)",
            ],
        }

    def classify_input(self, user_input: str) -> Tuple[str, Optional[dict]]:
        """
        Classify user input and extract parameters.
        Returns (category, params) tuple.
        """
        user_input_lower = user_input.lower().strip()

        # Remove assistant name prefix if present
        assistant_name = ASSISTANT_NAME.lower()
        if user_input_lower.startswith(assistant_name):
            user_input_lower = user_input_lower[len(assistant_name) :].strip()
            user_input_lower = user_input_lower.lstrip(",.:")

        # Check each pattern category
        for category, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_input_lower, re.IGNORECASE)
                if match:
                    logger.debug(f"Matched '{category}' pattern: {pattern}")
                    return category, {"match": match, "original": user_input}

        # Default to AI question
        logger.debug("No command pattern matched, treating as AI question")
        return "ai_question", {"question": user_input}

    def is_greeting(self, user_input: str) -> bool:
        """Check if input is a greeting."""
        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
        ]
        return any(user_input.lower().strip().startswith(g) for g in greetings)

    def is_thanks(self, user_input: str) -> bool:
        """Check if input is an expression of thanks."""
        thanks = ["thank", "thanks", "appreciate"]
        return any(t in user_input.lower() for t in thanks)

    def is_yes(self, user_input: str) -> bool:
        """Check if input is affirmative."""
        yes_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "confirm"]
        return user_input.lower().strip() in yes_words

    def is_no(self, user_input: str) -> bool:
        """Check if input is negative."""
        no_words = ["no", "nope", "nah", "cancel", "never mind"]
        return user_input.lower().strip() in no_words


# Singleton instance
_router: Optional[CommandRouter] = None


def get_router() -> CommandRouter:
    """Get the singleton CommandRouter instance."""
    global _router
    if _router is None:
        _router = CommandRouter()
    return _router
