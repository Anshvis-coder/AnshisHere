"""
Security Module for Freddie
============================
Handles security checks, confirmations, and safe command execution.
"""

import logging
from typing import Optional, List
from config import REQUIRE_CONFIRMATION_FOR

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manages security checks and confirmations for dangerous operations."""

    def __init__(self):
        self.dangerous_actions = REQUIRE_CONFIRMATION_FOR.copy()
        self.confirmed_actions: set = set()

    def is_dangerous_action(self, action: str) -> bool:
        """Check if an action requires confirmation."""
        return action.lower() in self.dangerous_actions

    def add_dangerous_action(self, action: str) -> None:
        """Add an action to the dangerous actions list."""
        if action not in self.dangerous_actions:
            self.dangerous_actions.append(action.lower())
            logger.info(f"Added '{action}' to dangerous actions list")

    def remove_dangerous_action(self, action: str) -> None:
        """Remove an action from the dangerous actions list."""
        if action in self.dangerous_actions:
            self.dangerous_actions.remove(action.lower())
            logger.info(f"Removed '{action}' from dangerous actions list")

    def require_confirmation(self, action: str) -> bool:
        """
        Check if an action requires user confirmation.
        Returns True if confirmation is needed, False otherwise.
        """
        return self.is_dangerous_action(action)

    def mark_confirmed(self, action_id: str) -> None:
        """Mark an action as confirmed by the user."""
        self.confirmed_actions.add(action_id)
        logger.debug(f"Action '{action_id}' marked as confirmed")

    def is_confirmed(self, action_id: str) -> bool:
        """Check if an action has been confirmed."""
        return action_id in self.confirmed_actions

    def clear_confirmation(self, action_id: str) -> None:
        """Clear a confirmation status."""
        self.confirmed_actions.discard(action_id)
        logger.debug(f"Confirmation cleared for '{action_id}'")

    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Validate a command for safety.
        Returns (is_safe, reason) tuple.
        """
        # Block potentially dangerous patterns
        dangerous_patterns = [
            "rm -rf",
            "del /s /q",
            "format",
            "diskpart",
            "reg delete",
            "powershell -enc",
            "cmd /c del",
        ]

        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                logger.warning(f"Dangerous command pattern detected: {pattern}")
                return False, f"Command contains potentially dangerous operation: {pattern}"

        return True, None

    def get_confirmation_message(self, action: str) -> str:
        """Get a confirmation message for a dangerous action."""
        messages = {
            "shutdown": "Are you sure you want to shut down the computer?",
            "restart": "Are you sure you want to restart the computer?",
            "delete_file": "Are you sure you want to delete this file?",
            "delete_folder": "Are you sure you want to delete this folder?",
            "bulk_delete": "This will delete multiple files. Are you sure?",
        }
        return messages.get(
            action.lower(),
            f"This action ({action}) may be dangerous. Are you sure you want to proceed?",
        )


# Singleton instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the singleton SecurityManager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
