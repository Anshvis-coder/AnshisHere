# Freddie - Personal AI Assistant

A complete desktop AI assistant powered by local LLM, designed to run on Windows without requiring paid API keys.

## Features

- **Local AI Brain**: Uses Ollama for offline AI inference (no API keys required)
- **Voice Input/Output**: Speech recognition and text-to-speech capabilities
- **Application Control**: Open and manage applications
- **Browser Commands**: Search the web, open websites
- **File Management**: Create, open, rename, and organize files
- **System Commands**: Check time, battery, CPU, RAM usage
- **Memory System**: Persistent storage for preferences and facts
- **Notes & Reminders**: Create notes and schedule reminders
- **Modern GUI**: Clean, dark-themed interface using CustomTkinter
- **Text Mode**: Full functionality without voice if preferred

## Requirements

### Python
- Python 3.12 or higher

### External Software
- **Ollama**: Local LLM runner (required for AI features)
  - Download from: https://ollama.ai
  - Install and run: `ollama serve`
  - Pull a model: `ollama pull llama3.2`

### Python Packages
Install using pip:
```bash
pip install -r requirements.txt
```

## Installation

### Step 1: Install Python
Download and install Python 3.12+ from https://python.org

### Step 2: Install Ollama
1. Download Ollama from https://ollama.ai
2. Run the installer
3. Open a terminal and pull a model:
   ```bash
   ollama pull llama3.2
   ```
4. Start Ollama service:
   ```bash
   ollama serve
   ```

### Step 3: Install Python Dependencies
```bash
cd Freddie
pip install -r requirements.txt
```

### Step 4: Run Freddie
```bash
python main.py
```

## Usage

### Voice Commands
Click the microphone button and speak commands like:
- "Open Chrome"
- "What time is it?"
- "Search Google for Python tutorials"
- "Create a folder called Projects"
- "Remember that I use Python"

### Text Commands
Type commands in the input field:
- `open notepad`
- `what is the battery level?`
- `open youtube`
- `make a note: Learn decorators`

### Common Commands

**Applications:**
- "Open Chrome/Firefox/Edge"
- "Open Notepad"
- "Open Calculator"
- "Open VS Code"
- "Open File Explorer"

**Browser:**
- "Open YouTube"
- "Open GitHub"
- "Search Google for [query]"
- "Go to https://example.com"

**System:**
- "What time is it?"
- "What's the date?"
- "Check battery"
- "Check CPU usage"
- "Check RAM usage"
- "Lock my PC"

**Memory & Notes:**
- "Remember that my favorite color is blue"
- "What is my favorite programming language?"
- "Make a note: Study Python tomorrow"
- "Show my notes"

**Files:**
- "Create a folder called Projects on Desktop"
- "Open my Downloads folder"

## Configuration

Edit `config.py` to customize:
- AI model name
- Voice settings
- Application paths
- Wake word
- And more

## Project Structure

```
Freddie/
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── README.md           # This file
│
├── core/               # Core logic
│   ├── assistant.py    # Main assistant controller
│   ├── command_router.py  # Command classification
│   └── security.py     # Security checks
│
├── brain/              # AI & Memory
│   ├── local_ai.py     # Ollama interface
│   └── memory.py       # SQLite database manager
│
├── voice/              # Voice processing
│   ├── listen.py       # Speech recognition
│   ├── speak.py        # Text-to-speech
│   └── wake_word.py    # Wake word detection
│
├── commands/           # Command handlers
│   ├── apps.py         # Application control
│   ├── browser.py      # Web browser commands
│   ├── files.py        # File operations
│   ├── system.py       # System commands
│   └── automation.py   # Scheduled tasks
│
├── database/           # Database utilities
│   └── db.py           # Database initialization
│
├── ui/                 # GUI components
│   ├── window.py       # Main window
│   ├── dashboard.py    # Conversation display
│   └── settings.py     # Settings dialog
│
├── data/               # User data storage
│   ├── notes/          # Saved notes
│   └── exports/        # Exported data
│
└── logs/               # Application logs
```

## Troubleshooting

### Ollama Not Running
- Error: "AI is offline"
- Solution: Start Ollama with `ollama serve`

### Microphone Not Working
- Check Windows microphone permissions
- Ensure microphone is selected as default input device
- Install SpeechRecognition: `pip install SpeechRecognition`

### TTS Not Working
- Install pyttsx3: `pip install pyttsx3`
- On Windows, ensure SAPI5 is available

### Application Won't Open
- Check application path in `config.py`
- Verify the application is installed
- Some apps may require administrator privileges

## Building Executable (Windows)

To create a standalone .exe file:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name Freddie main.py
```

The executable will be in the `dist/` folder.

## Adding New Commands

1. Create a new handler in `commands/` directory
2. Add pattern matching in `core/command_router.py`
3. Add routing logic in `core/assistant.py`

Example - Adding a weather command:
```python
# commands/weather.py
class WeatherController:
    def get_weather(self, location: str) -> str:
        # Implementation
        return f"Weather in {location}: Sunny, 75°F"
```

## Changing AI Model

1. Open Settings in the GUI
2. Change the model name (e.g., `mistral`, `codellama`)
3. Or edit `config.py`:
   ```python
   OLLAMA_MODEL = "mistral"
   ```
4. Pull the new model:
   ```bash
   ollama pull mistral
   ```

## Future Enhancements

Potential features for future versions:
- Advanced wake word detection (Porcupine)
- Screen understanding
- Smart home integration
- Calendar integration
- Email management
- Music control
- Plugin system
- Multiple AI model support
- Developer/coding mode

## License

This project is provided as-is for personal use.

## Support

For issues and questions:
1. Check the logs in the `logs/` folder
2. Ensure Ollama is running
3. Verify all dependencies are installed
4. Check microphone and speaker settings

---

**Freddie** - Your Personal AI Assistant 🤖
