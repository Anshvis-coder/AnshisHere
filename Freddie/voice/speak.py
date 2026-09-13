"""
Text-to-Speech Module for Freddie
==================================
Handles text-to-speech conversion using local TTS engines.
No paid API required.
"""

import logging
from typing import Optional
import threading
import queue

try:
    # Try pyttsx3 first (offline, cross-platform)
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

from config import TTS_ENABLED, TTS_RATE, TTS_VOLUME

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Handles text-to-speech synthesis."""

    def __init__(self, rate: int = None, volume: float = None):
        self.rate = rate or TTS_RATE
        self.volume = volume or TTS_VOLUME
        self.engine: Optional[pyttsx3.Engine] = None
        self._available: bool = False
        self._speaking = False
        self._stop_flag = False
        self._speech_queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None

        if PYTTSX3_AVAILABLE and TTS_ENABLED:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize the TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

            # Set up event handlers
            self.engine.connect('started-words', self._on_start)
            self.engine.connect('finished-words', self._on_finish)

            self._available = True
            logger.info("TTS engine initialized")

            # Start worker thread
            self._start_worker()

        except Exception as e:
            logger.warning(f"TTS initialization failed: {e}")
            self._available = False

    def _start_worker(self) -> None:
        """Start the speech worker thread."""
        def worker():
            while not self._stop_flag:
                try:
                    text = self._speech_queue.get(timeout=0.5)
                    if text:
                        self._speak_internal(text)
                    self._speech_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Speech worker error: {e}")

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def _speak_internal(self, text: str) -> None:
        """Internal method to speak text (blocking)."""
        if not self.engine:
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error speaking text: {e}")

    def _on_start(self, name, location, length) -> None:
        """Callback when speech starts."""
        self._speaking = True
        logger.debug("Speech started")

    def _on_finish(self, name, completed) -> None:
        """Callback when speech finishes."""
        self._speaking = False
        logger.debug("Speech finished")

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self._available and PYTTSX3_AVAILABLE

    def speak(self, text: str, block: bool = False) -> None:
        """
        Add text to the speech queue.

        Args:
            text: Text to speak
            block: If True, wait until speech completes
        """
        if not self.is_available():
            logger.debug("TTS not available")
            return

        if not text.strip():
            return

        if block:
            self._speak_internal(text)
        else:
            self._speech_queue.put(text)

    def speak_now(self, text: str) -> None:
        """Speak text immediately, interrupting current speech."""
        if not self.is_available():
            return

        self.stop()
        self._speech_queue.queue.clear()
        self.speak(text, block=True)

    def stop(self) -> None:
        """Stop current speech."""
        if self.engine and self._speaking:
            try:
                self.engine.stop()
                self._speaking = False
                logger.debug("Speech stopped")
            except Exception as e:
                logger.error(f"Error stopping speech: {e}")

    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._speaking

    def set_rate(self, rate: int) -> None:
        """Set speech rate (words per minute)."""
        self.rate = rate
        if self.engine:
            self.engine.setProperty('rate', rate)
            logger.info(f"TTS rate set to: {rate}")

    def set_volume(self, volume: float) -> None:
        """Set speech volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.engine:
            self.engine.setProperty('volume', self.volume)
            logger.info(f"TTS volume set to: {self.volume}")

    def set_voice(self, voice_name: str) -> bool:
        """
        Set the voice to use.

        Args:
            voice_name: Name of the voice to use

        Returns:
            True if voice was found and set, False otherwise
        """
        if not self.engine:
            return False

        voices = self.engine.getProperty('voices')
        for voice in voices:
            if voice_name.lower() in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                logger.info(f"Voice set to: {voice.name}")
                return True

        logger.warning(f"Voice '{voice_name}' not found")
        return False

    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if not self.engine:
            return []

        voices = self.engine.getProperty('voices')
        return [voice.name for voice in voices]

    def shutdown(self) -> None:
        """Shutdown the TTS engine."""
        self._stop_flag = True
        self.stop()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        logger.info("TTS engine shut down")


# Singleton instance
_tts_instance: Optional[TextToSpeech] = None


def get_tts() -> TextToSpeech:
    """Get the singleton TextToSpeech instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance
