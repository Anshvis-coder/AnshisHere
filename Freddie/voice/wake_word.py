"""
Wake Word Detection Module for Freddie
=======================================
Handles wake word detection ("Hey Freddie").
Modular design allows replacement with better offline engines.
"""

import logging
from typing import Optional, Callable
import threading
import time

from config import WAKE_WORD, WAKE_WORD_ENABLED

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Detects wake words to activate the assistant.
    
    This is a simple implementation that can be replaced with
    more sophisticated solutions like Porcupine, Snowboy, or Vosk.
    """

    def __init__(self, wake_word: str = None):
        self.wake_word = (wake_word or WAKE_WORD).lower()
        self.enabled = WAKE_WORD_ENABLED
        self._listening = False
        self._stop_flag = False
        self._callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None

        logger.info(f"Wake word detector initialized with: '{self.wake_word}'")

    def is_enabled(self) -> bool:
        """Check if wake word detection is enabled."""
        return self.enabled

    def set_wake_word(self, wake_word: str) -> None:
        """Set a new wake word."""
        self.wake_word = wake_word.lower()
        logger.info(f"Wake word changed to: '{self.wake_word}'")

    def start_listening(self, callback: Callable) -> None:
        """
        Start listening for wake word in background.

        Args:
            callback: Function to call when wake word is detected
        """
        if not self.enabled:
            logger.warning("Wake word detection is disabled")
            return

        if self._listening:
            logger.warning("Already listening for wake word")
            return

        self._callback = callback
        self._listening = True
        self._stop_flag = False

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Wake word detection started")

    def _listen_loop(self) -> None:
        """Main listening loop for wake word detection."""
        # This is a placeholder implementation
        # A real implementation would use:
        # - Porcupine (Picovoice) for offline wake word detection
        # - Snowboy (deprecated but still usable)
        # - Vosk with keyword spotting
        # - Custom audio analysis

        logger.debug("Wake word listening loop started")

        while not self._stop_flag:
            # In a real implementation, this would analyze audio
            # and detect the wake word pattern
            time.sleep(0.1)

        logger.debug("Wake word listening loop stopped")

    def stop_listening(self) -> None:
        """Stop wake word detection."""
        self._stop_flag = True
        self._listening = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("Wake word detection stopped")

    def detect_manual(self, text: str) -> bool:
        """
        Manually check if text contains the wake word.
        Useful for text-based activation.

        Args:
            text: Text to check

        Returns:
            True if wake word detected, False otherwise
        """
        text_lower = text.lower().strip()
        return self.wake_word in text_lower

    def simulate_wake_word(self) -> None:
        """Simulate wake word detection (for testing)."""
        if self._callback:
            logger.info("Simulated wake word detection")
            self._callback()


# Alternative: Simple pattern matching for wake word
class SimpleWakeWordDetector(WakeWordDetector):
    """
    Simple wake word detector using text pattern matching.
    Can be used when audio-based detection is not available.
    """

    def __init__(self, wake_word: str = None):
        super().__init__(wake_word)
        self.variations = [
            self.wake_word,
            self.wake_word.replace(" ", ""),
            f"hello {self.wake_word.split()[-1]}",
            f"hey {self.wake_word.split()[-1]}",
            f"ok {self.wake_word.split()[-1]}",
        ]

    def check_text(self, text: str) -> bool:
        """Check if text contains wake word or variations."""
        text_lower = text.lower().strip()

        for variation in self.variations:
            if text_lower.startswith(variation):
                return True

        return False


# Singleton instance
_detector_instance: Optional[WakeWordDetector] = None


def get_wake_word_detector() -> WakeWordDetector:
    """Get the singleton WakeWordDetector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SimpleWakeWordDetector()
    return _detector_instance
