"""
Freddie - Personal AI Assistant
================================
Main entry point for the Freddie application.
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import (
    ASSISTANT_NAME, LOG_LEVEL, LOG_FORMAT, LOGS_DIR,
    DATA_DIR, NOTES_DIR, EXPORTS_DIR
)


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Create log file with timestamp
    log_file = os.path.join(
        LOGS_DIR,
        f"freddie_{datetime.now().strftime('%Y%m%d')}.log"
    )

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info(f"{ASSISTANT_NAME} starting...")
    logger.info("=" * 50)

    return logger


def create_directories():
    """Create required directories."""
    directories = [DATA_DIR, NOTES_DIR, EXPORTS_DIR, LOGS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def check_ollama():
    """Check if Ollama is running."""
    try:
        import requests
        from config import OLLAMA_BASE_URL

        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def main():
    """Main entry point for Freddie."""
    # Setup
    logger = setup_logging()
    create_directories()

    # Check Ollama status
    ollama_running = check_ollama()
    if not ollama_running:
        logger.warning("Ollama is not running. AI features will be limited.")

    # Import GUI components
    try:
        import customtkinter as ctk
        from ui.window import FreddieWindow
        from ui.dashboard import DashboardFrame
        from ui.settings import SettingsFrame
        from core.assistant import Assistant
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        print("\nError: Missing required packages.")
        print("Please install dependencies: pip install -r requirements.txt\n")
        sys.exit(1)

    # Create application
    app = FreddieWindow()

    # Initialize assistant
    assistant = Assistant()
    status = assistant.initialize()

    # Log initialization status
    logger.info(f"Assistant initialized: {status}")

    # Create dashboard
    dashboard = DashboardFrame(app.content_frame)
    app.set_dashboard_content(dashboard)

    # Show welcome message
    dashboard.append_message("freddie", f"Hello! I'm {ASSISTANT_NAME}, your personal AI assistant. How can I help you today?")

    # Update status indicators
    ai_status = "AI Connected" if status["ai"] == "connected" else "⚠ AI Offline"
    voice_status = "Voice Ready" if status["voice"] == "ready" else "⚠ Voice Unavailable"
    memory_status = "Memory Ready" if status["memory"] == "ready" else "⚠ Memory Disabled"

    logger.info(f"Status - {ai_status}, {voice_status}, {memory_status}")

    # Handle send action
    def on_send(text):
        """Process user input."""
        app.update_status("processing")
        dashboard.append_message("user", text)

        # Process in thread to keep UI responsive
        def process():
            try:
                response = assistant.process_input(text)
                app.after(0, lambda: dashboard.append_message("freddie", response))
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                app.after(0, lambda: dashboard.append_message("freddie", f"Sorry, I encountered an error: {str(e)}"))
            finally:
                app.after(0, lambda: app.update_status("idle"))

        import threading
        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    # Handle mic action
    def on_mic():
        """Start voice listening."""
        if not assistant.speech_recognizer or not assistant.speech_recognizer.is_available():
            dashboard.append_message("freddie", "Microphone is not available. Please check your audio settings.")
            return

        app.update_status("listening")

        def listen_thread():
            try:
                text = assistant.listen()
                if text:
                    app.after(0, lambda: on_send(text))
            except Exception as e:
                logger.error(f"Listening error: {e}")
                app.after(0, lambda: dashboard.append_message("freddie", "Sorry, I couldn't hear you clearly."))
            finally:
                app.after(0, lambda: app.update_status("idle"))

        import threading
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    # Handle settings action
    settings_window = None

    def on_settings():
        """Open settings window."""
        nonlocal settings_window

        def on_save(settings):
            """Handle settings save."""
            logger.info(f"Settings saved: {settings}")
            # Apply settings
            if "ollama_model" in settings and assistant.ai:
                assistant.ai.set_model(settings["ollama_model"])

        if settings_window is None or not settings_window.winfo_exists():
            settings_window = SettingsFrame(app, on_save=on_save)

    # Handle close action
    def on_close():
        """Handle application close."""
        logger.info("Shutting down Freddie...")
        if assistant.tts:
            assistant.tts.shutdown()
        if assistant.memory:
            assistant.memory.close()
        app.destroy()
        sys.exit(0)

    # Register callbacks
    app.register_callback("on_send", on_send)
    app.register_callback("on_mic", on_mic)
    app.register_callback("on_settings", on_settings)
    app.register_callback("on_close", on_close)

    # Set up response callback for automatic speaking
    def on_response(response):
        """Handle assistant responses."""
        # Log conversation to database
        if assistant.memory:
            # Get last user input
            recent = dashboard.get_recent_messages(1)
            if recent and recent[0][0] == "user":
                assistant.memory.add_conversation(recent[0][1], response)

    assistant.set_response_callback(on_response)

    def on_status_change(status):
        """Handle status changes."""
        app.update_status(status)

    assistant.set_status_callback(on_status_change)

    # Start reminder scheduler
    if assistant.automation_controller:
        assistant.automation_controller.start_scheduler()

    # Run application
    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
