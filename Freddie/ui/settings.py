"""
Settings Frame for Freddie GUI
===============================
Contains settings and configuration options.
"""

import customtkinter as ctk
from typing import Optional, Callable
from config import OLLAMA_MODEL, VOICE_ENABLED, TTS_ENABLED, MEMORY_ENABLED


class SettingsFrame(ctk.CTkToplevel):
    """Settings window for Freddie."""

    def __init__(self, parent, on_save: Callable = None):
        super().__init__(parent)

        self.title("Freddie Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        self.on_save_callback = on_save

        # Center the window
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the settings UI."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # AI Settings Section
        ai_section = ctk.CTkFrame(main_frame)
        ai_section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            ai_section,
            text="AI Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Model selection
        ctk.CTkLabel(
            ai_section,
            text="Ollama Model:",
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(5, 0))

        self.model_entry = ctk.CTkEntry(
            ai_section,
            width=300,
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.model_entry.insert(0, OLLAMA_MODEL)
        self.model_entry.pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            ai_section,
            text="Common models: llama3.2, mistral, codellama",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Voice Settings Section
        voice_section = ctk.CTkFrame(main_frame)
        voice_section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            voice_section,
            text="Voice Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Voice enabled toggle
        self.voice_switch = ctk.CTkSwitch(
            voice_section,
            text="Enable Voice Input",
            font=ctk.CTkFont(size=12),
        )
        self.voice_switch.select() if VOICE_ENABLED else self.voice_switch.deselect()
        self.voice_switch.pack(anchor="w", padx=15, pady=5)

        # TTS enabled toggle
        self.tts_switch = ctk.CTkSwitch(
            voice_section,
            text="Enable Text-to-Speech",
            font=ctk.CTkFont(size=12),
        )
        self.tts_switch.select() if TTS_ENABLED else self.tts_switch.deselect()
        self.tts_switch.pack(anchor="w", padx=15, pady=5)

        # Memory Settings Section
        memory_section = ctk.CTkFrame(main_frame)
        memory_section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            memory_section,
            text="Memory Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Memory enabled toggle
        self.memory_switch = ctk.CTkSwitch(
            memory_section,
            text="Enable Memory & Notes",
            font=ctk.CTkFont(size=12),
        )
        self.memory_switch.select() if MEMORY_ENABLED else self.memory_switch.deselect()
        self.memory_switch.pack(anchor="w", padx=15, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 10))

        self.save_button = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            height=40,
            command=self._on_save
        )
        self.save_button.pack(side="left", padx=(15, 10), pady=10)

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            height=40,
            fg_color="transparent",
            border_width=2,
            command=self.destroy
        )
        self.cancel_button.pack(side="right", padx=(10, 15), pady=10)

    def _on_save(self) -> None:
        """Handle save button click."""
        settings = {
            "ollama_model": self.model_entry.get().strip(),
            "voice_enabled": self.voice_switch.get(),
            "tts_enabled": self.tts_switch.get(),
            "memory_enabled": self.memory_switch.get(),
        }

        if self.on_save_callback:
            self.on_save_callback(settings)

        self.destroy()

    def get_settings(self) -> dict:
        """Get current settings values."""
        return {
            "ollama_model": self.model_entry.get().strip(),
            "voice_enabled": self.voice_switch.get(),
            "tts_enabled": self.tts_switch.get(),
            "memory_enabled": self.memory_switch.get(),
        }
