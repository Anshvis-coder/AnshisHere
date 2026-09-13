"""
Main Assistant Controller for Freddie
======================================
Coordinates all subsystems and manages the assistant lifecycle.
"""

import logging
from typing import Optional, Callable
from datetime import datetime

from config import ASSISTANT_NAME, OLLAMA_MODEL, VOICE_ENABLED, TTS_ENABLED, MEMORY_ENABLED
from core.command_router import get_router, CommandRouter
from core.security import get_security_manager, SecurityManager
from brain.local_ai import LocalAI
from brain.memory import MemoryManager
from voice.listen import SpeechRecognizer
from voice.speak import TextToSpeech
from commands.apps import AppController
from commands.browser import BrowserController
from commands.files import FileController
from commands.system import SystemController
from commands.automation import AutomationController

logger = logging.getLogger(__name__)


class Assistant:
    """Main assistant controller that coordinates all subsystems."""

    def __init__(self):
        self.name = ASSISTANT_NAME
        self.router: Optional[CommandRouter] = None
        self.security: Optional[SecurityManager] = None
        self.ai: Optional[LocalAI] = None
        self.memory: Optional[MemoryManager] = None
        self.speech_recognizer: Optional[SpeechRecognizer] = None
        self.tts: Optional[TextToSpeech] = None
        self.app_controller: Optional[AppController] = None
        self.browser_controller: Optional[BrowserController] = None
        self.file_controller: Optional[FileController] = None
        self.system_controller: Optional[SystemController] = None
        self.automation_controller: Optional[AutomationController] = None

        # State
        self.is_listening = False
        self.is_speaking = False
        self.pending_confirmation: Optional[dict] = None

        # Callbacks
        self.on_response_callback: Optional[Callable[[str], None]] = None
        self.on_status_change_callback: Optional[Callable[[str], None]] = None

    def initialize(self) -> dict:
        """
        Initialize all subsystems.
        Returns status dictionary.
        """
        logger.info("Initializing Freddie...")
        status = {
            "assistant": "ready",
            "ai": "unknown",
            "voice": "unknown",
            "memory": "unknown",
            "commands": "unknown",
        }

        try:
            # Initialize router and security
            self.router = get_router()
            self.security = get_security_manager()
            logger.info("Command router and security initialized")

            # Initialize AI
            try:
                self.ai = LocalAI()
                if self.ai.is_available():
                    status["ai"] = "connected"
                    logger.info(f"AI connected using model: {OLLAMA_MODEL}")
                else:
                    status["ai"] = "offline"
                    logger.warning("AI is offline - Ollama may not be running")
            except Exception as e:
                logger.error(f"AI initialization failed: {e}")
                status["ai"] = "error"

            # Initialize Memory
            try:
                if MEMORY_ENABLED:
                    self.memory = MemoryManager()
                    status["memory"] = "ready"
                    logger.info("Memory system initialized")
                else:
                    status["memory"] = "disabled"
            except Exception as e:
                logger.error(f"Memory initialization failed: {e}")
                status["memory"] = "error"

            # Initialize Voice
            try:
                if VOICE_ENABLED:
                    self.speech_recognizer = SpeechRecognizer()
                    status["voice"] = "ready" if self.speech_recognizer.is_available() else "unavailable"
                    
                    if TTS_ENABLED:
                        self.tts = TextToSpeech()
                        logger.info("TTS initialized")
                else:
                    status["voice"] = "disabled"
            except Exception as e:
                logger.error(f"Voice initialization failed: {e}")
                status["voice"] = "error"

            # Initialize Command Controllers
            try:
                self.app_controller = AppController()
                self.browser_controller = BrowserController()
                self.file_controller = FileController()
                self.system_controller = SystemController()
                self.automation_controller = AutomationController()
                status["commands"] = "ready"
                logger.info("Command controllers initialized")
            except Exception as e:
                logger.error(f"Command controller initialization failed: {e}")
                status["commands"] = "error"

            logger.info("Freddie initialization complete")

        except Exception as e:
            logger.error(f"Critical initialization error: {e}")
            status["assistant"] = "error"

        return status

    def process_input(self, user_input: str) -> str:
        """
        Process user input and return response.
        This is the main entry point for user commands.
        """
        if not user_input.strip():
            return "I didn't hear anything. Could you please repeat?"

        logger.info(f"Processing input: {user_input}")

        # Check for pending confirmation
        if self.pending_confirmation:
            return self._handle_confirmation(user_input)

        # Handle greetings
        if self.router and self.router.is_greeting(user_input):
            response = self._get_greeting_response()
            self._notify_response(response)
            return response

        # Handle thanks
        if self.router and self.router.is_thanks(user_input):
            response = "You're welcome! Happy to help."
            self._notify_response(response)
            return response

        # Classify the input
        category, params = self.router.classify_input(user_input)
        logger.debug(f"Input classified as: {category}")

        # Route to appropriate handler
        response = self._route_command(category, params, user_input)

        self._notify_response(response)
        return response

    def _route_command(self, category: str, params: dict, original_input: str) -> str:
        """Route command to appropriate handler."""
        try:
            if category == "open_app":
                return self._handle_open_app(params)
            elif category == "close_app":
                return self._handle_close_app(params)
            elif category == "browser":
                return self._handle_browser_command(params)
            elif category == "file_operation":
                return self._handle_file_operation(params)
            elif category == "system_command":
                return self._handle_system_command(params)
            elif category == "memory":
                return self._handle_memory_command(params)
            elif category == "note":
                return self._handle_note_command(params)
            elif category == "reminder":
                return self._handle_reminder_command(params)
            elif category == "ai_question":
                return self._handle_ai_question(original_input)
            else:
                return self._handle_ai_question(original_input)
        except Exception as e:
            logger.error(f"Error routing command: {e}")
            return f"I encountered an error processing that command: {str(e)}"

    def _handle_open_app(self, params: dict) -> str:
        """Handle application opening command."""
        match = params.get("match")
        if not match or not self.app_controller:
            return "I couldn't understand which app to open."

        app_name = match.group(1)
        success, message = self.app_controller.open_application(app_name)

        if success:
            return f"Opening {app_name}."
        else:
            return f"Sorry, I couldn't open {app_name}. {message}"

    def _handle_close_app(self, params: dict) -> str:
        """Handle application closing command."""
        match = params.get("match")
        if not match or not self.app_controller:
            return "I couldn't understand which app to close."

        app_name = match.group(1)
        success, message = self.app_controller.close_application(app_name)

        if success:
            return f"Closing {app_name}."
        else:
            return f"Sorry, I couldn't close {app_name}. {message}"

    def _handle_browser_command(self, params: dict) -> str:
        """Handle browser-related command."""
        if not self.browser_controller:
            return "Browser control is not available."

        match = params.get("match")
        if not match:
            return "I couldn't understand the browser command."

        # Check for URL
        url_pattern = r"(?:go to|open|visit)\s+(https?://\S+)"
        url_match = re.search(url_pattern, params.get("original", ""), re.IGNORECASE)
        if url_match:
            url = url_match.group(1)
            success = self.browser_controller.open_url(url)
            if success:
                return f"Opening {url}."
            else:
                return "Failed to open the URL."

        # Check for site name
        site_pattern = r"open\s+(youtube|github|google|reddit|twitter)"
        site_match = re.search(site_pattern, params.get("original", ""), re.IGNORECASE)
        if site_match:
            site = site_match.group(1)
            success = self.browser_controller.open_site(site)
            if success:
                return f"Opening {site.capitalize()}."
            else:
                return f"Failed to open {site}."

        # Search query
        search_pattern = r"(?:search|google)\s+(?:for\s+)?(.+)"
        search_match = re.search(search_pattern, params.get("original", ""), re.IGNORECASE)
        if search_match:
            query = search_match.group(1)
            success = self.browser_controller.search_google(query)
            if success:
                return f"Searching Google for '{query}'."
            else:
                return "Failed to perform the search."

        return "I couldn't understand the browser command."

    def _handle_file_operation(self, params: dict) -> str:
        """Handle file operation command."""
        if not self.file_controller:
            return "File operations are not available."

        # Implementation would parse the specific operation
        return "File operations are supported. Please be more specific."

    def _handle_system_command(self, params: dict) -> str:
        """Handle system command."""
        if not self.system_controller:
            return "System commands are not available."

        original = params.get("original", "").lower()

        # Time
        if "time" in original:
            return self.system_controller.get_time()

        # Date
        if "date" in original:
            return self.system_controller.get_date()

        # Battery
        if "battery" in original:
            return self.system_controller.get_battery_status()

        # CPU
        if "cpu" in original:
            return self.system_controller.get_cpu_usage()

        # RAM
        if "ram" in original:
            return self.system_controller.get_ram_usage()

        # Lock
        if "lock" in original:
            return self.system_controller.lock_pc()

        # Shutdown
        if "shutdown" in original:
            action_id = "shutdown_" + datetime.now().strftime("%Y%m%d%H%M%S")
            self.pending_confirmation = {
                "action": "shutdown",
                "action_id": action_id,
            }
            return self.security.get_confirmation_message("shutdown")

        # Restart
        if "restart" in original:
            action_id = "restart_" + datetime.now().strftime("%Y%m%d%H%M%S")
            self.pending_confirmation = {
                "action": "restart",
                "action_id": action_id,
            }
            return self.security.get_confirmation_message("restart")

        return "I can help with system commands like time, date, battery, CPU, RAM, lock, shutdown, or restart."

    def _handle_memory_command(self, params: dict) -> str:
        """Handle memory-related command."""
        if not self.memory:
            return "Memory system is not available."

        # Remember something
        if "remember" in params.get("original", "").lower():
            match = params.get("match")
            if match:
                content = match.group(1)
                self.memory.add_memory(content)
                return "I've remembered that for you."

        # Recall something
        if "what is my" in params.get("original", "").lower():
            match = params.get("match")
            if match:
                query = match.group(1)
                result = self.memory.search_memories(query)
                if result:
                    return f"You told me that {result[0]['content']}"
                else:
                    return "I don't have any information about that."

        return "Memory commands are supported. Try 'Remember that...' or 'What is my...'."

    def _handle_note_command(self, params: dict) -> str:
        """Handle note-related command."""
        if not self.memory:
            return "Notes system is not available."

        original = params.get("original", "").lower()

        # Create note
        if any(word in original for word in ["make", "create", "add", "note"]):
            # Extract note content (simplified)
            note_content = original.split("note")[-1].strip(" :.-")
            if note_content:
                self.memory.add_note(note_content)
                return "Note created successfully."

        # List notes
        if any(word in original for word in ["show", "list", "read"]):
            notes = self.memory.get_recent_notes(limit=5)
            if notes:
                note_list = "\n".join([f"- {n['content']}" for n in notes])
                return f"Your recent notes:\n{note_list}"
            else:
                return "You don't have any notes yet."

        return "Note commands are supported. Try 'Make a note: ...' or 'Show my notes'."

    def _handle_reminder_command(self, params: dict) -> str:
        """Handle reminder command."""
        if not self.memory:
            return "Reminder system is not available."

        # Simplified reminder handling
        return "Reminders are supported. I'll store this reminder for you."

    def _handle_ai_question(self, question: str) -> str:
        """Handle general AI question using local LLM."""
        if not self.ai:
            return "I'm sorry, but my AI brain is not connected. Please make sure Ollama is running."

        try:
            response = self.ai.generate_response(question)
            return response
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "I had trouble generating a response. Please try again."

    def _handle_confirmation(self, user_input: str) -> str:
        """Handle user confirmation for dangerous actions."""
        if not self.pending_confirmation or not self.security:
            self.pending_confirmation = None
            return "There's no pending action to confirm."

        action = self.pending_confirmation.get("action")
        action_id = self.pending_confirmation.get("action_id")

        if self.router and self.router.is_yes(user_input):
            # Execute the confirmed action
            self.security.mark_confirmed(action_id)
            response = self._execute_confirmed_action(action)
            self.pending_confirmation = None
            return response
        elif self.router and self.router.is_no(user_input):
            self.pending_confirmation = None
            return "Action cancelled."
        else:
            return "Please say 'yes' to confirm or 'no' to cancel."

    def _execute_confirmed_action(self, action: str) -> str:
        """Execute a confirmed dangerous action."""
        if not self.system_controller:
            return "System controller is not available."

        if action == "shutdown":
            return self.system_controller.shutdown_pc(confirmed=True)
        elif action == "restart":
            return self.system_controller.restart_pc(confirmed=True)
        else:
            return "Unknown action."

    def _get_greeting_response(self) -> str:
        """Get an appropriate greeting response."""
        hour = datetime.now().hour
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 18:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        return f"{time_greeting}! I'm {self.name}. How can I assist you today?"

    def _notify_response(self, response: str) -> None:
        """Notify callbacks of response."""
        if self.on_response_callback:
            self.on_response_callback(response)

        # Speak if TTS is enabled
        if self.tts and TTS_ENABLED:
            self.speak(response)

    def speak(self, text: str) -> None:
        """Speak text using TTS."""
        if not self.tts:
            return

        try:
            self.is_speaking = True
            if self.on_status_change_callback:
                self.on_status_change_callback("speaking")
            self.tts.speak(text)
        finally:
            self.is_speaking = False
            if self.on_status_change_callback:
                self.on_status_change_callback("idle")

    def listen(self) -> Optional[str]:
        """Listen for voice input."""
        if not self.speech_recognizer:
            return None

        try:
            self.is_listening = True
            if self.on_status_change_callback:
                self.on_status_change_callback("listening")
            return self.speech_recognizer.listen()
        except Exception as e:
            logger.error(f"Listening error: {e}")
            return None
        finally:
            self.is_listening = False
            if self.on_status_change_callback:
                self.on_status_change_callback("idle")

    def stop_speaking(self) -> None:
        """Stop current speech."""
        if self.tts:
            self.tts.stop()
            self.is_speaking = False

    def set_response_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for responses."""
        self.on_response_callback = callback

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for status changes."""
        self.on_status_change_callback = callback


# Import re at module level (needed for regex patterns)
import re
