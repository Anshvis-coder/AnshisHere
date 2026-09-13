"""
Speech Recognition Module for Freddie
======================================
Handles microphone input and speech-to-text conversion.
Uses local speech recognition when possible.
"""

import logging
from typing import Optional
import threading
import queue

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

from config import SPEECH_RECOGNITION_LANGUAGE, SPEECH_TIMEOUT

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Handles speech recognition from microphone input."""

    def __init__(self, language: str = None, timeout: int = None):
        self.language = language or SPEECH_RECOGNITION_LANGUAGE
        self.timeout = timeout or SPEECH_TIMEOUT
        self.recognizer: Optional[sr.Recognizer] = None
        self.microphone: Optional[sr.Microphone] = None
        self._available: bool = False
        self._listening = False
        self._stop_flag = False

        if SPEECH_RECOGNITION_AVAILABLE:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize the speech recognizer and microphone."""
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

            # Test microphone availability
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            self._available = True
            logger.info("Speech recognizer initialized")
        except Exception as e:
            logger.warning(f"Speech recognizer initialization failed: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if speech recognition is available."""
        return self._available and SPEECH_RECOGNITION_AVAILABLE

    def listen(self, timeout: int = None) -> Optional[str]:
        """
        Listen for speech and convert to text.

        Args:
            timeout: Maximum time to wait for speech (seconds)

        Returns:
            Recognized text or None if recognition failed
        """
        if not self.is_available():
            logger.warning("Speech recognition not available")
            return None

        if self._listening:
            logger.warning("Already listening")
            return None

        timeout = timeout or self.timeout
        self._listening = True
        self._stop_flag = False

        try:
            with self.microphone as source:
                logger.debug("Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=15
                )

            if self._stop_flag:
                logger.debug("Listen cancelled")
                return None

            # Try Google's free speech recognition API first
            # This works offline for some languages but generally needs internet
            # For truly offline, you would need Vosk or Whisper installed locally
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                logger.info(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.debug("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                # Try fallback to Sphinx if available (offline)
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Recognized (Sphinx): {text}")
                    return text
                except:
                    return None

        except sr.WaitTimeoutError:
            logger.debug("No speech detected within timeout")
            return None
        except Exception as e:
            logger.error(f"Error during listening: {e}")
            return None
        finally:
            self._listening = False

    def listen_in_background(self, callback) -> None:
        """
        Start listening in a background thread.

        Args:
            callback: Function to call with recognized text
        """
        if not self.is_available():
            return

        def listen_thread():
            while not self._stop_flag:
                text = self.listen()
                if text:
                    callback(text)

        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    def stop_listening(self) -> None:
        """Stop any ongoing listening operation."""
        self._stop_flag = True
        self._listening = False

    def set_language(self, language: str) -> None:
        """Change the recognition language."""
        self.language = language
        logger.info(f"Recognition language set to: {language}")

    def test_microphone(self) -> bool:
        """Test if microphone is working."""
        if not self.is_available():
            return False

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            return True
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False


# Singleton instance
_recognizer_instance: Optional[SpeechRecognizer] = None


def get_speech_recognizer() -> SpeechRecognizer:
    """Get the singleton SpeechRecognizer instance."""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = SpeechRecognizer()
    return _recognizer_instance
