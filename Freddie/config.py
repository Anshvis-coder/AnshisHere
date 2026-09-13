"""
Freddie Configuration
=====================
Central configuration for the Freddie AI Assistant.
"""

# Assistant Identity
ASSISTANT_NAME = "Freddie"
ASSISTANT_VERSION = "1.0.0"

# Local AI Configuration (Ollama)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Default model - can be changed by user
OLLAMA_TIMEOUT = 60  # seconds

# Voice Configuration
VOICE_ENABLED = True
TTS_ENABLED = True
WAKE_WORD_ENABLED = False  # Set to True for wake word mode
WAKE_WORD = "hey freddie"

# Memory Configuration
MEMORY_ENABLED = True
DATABASE_PATH = "database/memory.db"

# Paths
DATA_DIR = "data"
NOTES_DIR = "data/notes"
EXPORTS_DIR = "data/exports"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"

# Application Paths (Windows defaults)
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "vscode": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "file_explorer": "explorer.exe",
    "task_manager": "taskmgr.exe",
    "settings": "ms-settings:",
}

# Speech Recognition Settings
SPEECH_RECOGNITION_LANGUAGE = "en-US"
SPEECH_TIMEOUT = 5  # seconds

# TTS Settings
TTS_RATE = 150  # words per minute (approximate)
TTS_VOLUME = 1.0

# GUI Settings
GUI_THEME = "dark-blue"  # customtkinter theme
GUI_COLOR_PRIMARY = "#2B579A"
GUI_COLOR_SECONDARY = "#1E3A5F"

# Security Settings
REQUIRE_CONFIRMATION_FOR = [
    "shutdown",
    "restart",
    "delete_file",
    "delete_folder",
    "bulk_delete",
]

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
