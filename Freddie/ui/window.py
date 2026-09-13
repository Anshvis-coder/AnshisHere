"""
Main Window for Freddie GUI
============================
Creates the main application window using CustomTkinter.
"""

import logging
import customtkinter as ctk
from typing import Optional, Callable
from config import ASSISTANT_NAME, ASSISTANT_VERSION, GUI_THEME

logger = logging.getLogger(__name__)


class FreddieWindow(ctk.CTk):
    """Main application window for Freddie."""

    def __init__(self):
        super().__init__()

        self.title(f"{ASSISTANT_NAME} - Personal AI Assistant")
        self.geometry("800x700")
        self.minsize(600, 500)

        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(GUI_THEME if GUI_THEME != "dark-blue" else "blue")

        # State
        self.status = "idle"
        self.callbacks = {}

        # Build UI
        self._build_ui()

        logger.info("Freddie window initialized")

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=ASSISTANT_NAME.upper(),
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Personal AI Assistant v{ASSISTANT_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            self.header_frame,
            text="● Online",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.status_indicator.grid(row=2, column=0, padx=20, pady=(0, 5))

        # Main content area (dashboard)
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Placeholder for dashboard content
        self.dashboard_content = None

        # Input area
        self.input_frame = ctk.CTkFrame(self, height=80)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Text input
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a message or command...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        self.input_entry.bind("<Return>", lambda e: self._on_enter_pressed())

        # Send button
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=80,
            height=40,
            command=self._on_send_clicked
        )
        self.send_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Bottom toolbar
        self.toolbar_frame = ctk.CTkFrame(self, height=50)
        self.toolbar_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.toolbar_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Mic button
        self.mic_button = ctk.CTkButton(
            self.toolbar_frame,
            text="🎤 Listen",
            height=35,
            command=self._on_mic_clicked
        )
        self.mic_button.grid(row=0, column=0, padx=10, pady=5)

        # Settings button
        self.settings_button = ctk.CTkButton(
            self.toolbar_frame,
            text="⚙ Settings",
            height=35,
            command=self._on_settings_clicked
        )
        self.settings_button.grid(row=0, column=2, padx=10, pady=5)

    def set_dashboard_content(self, content: ctk.CTkFrame) -> None:
        """Set the dashboard content frame."""
        if self.dashboard_content:
            self.dashboard_content.destroy()

        self.dashboard_content = content
        content.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def update_status(self, status: str) -> None:
        """Update the status indicator."""
        self.status = status

        status_colors = {
            "idle": "green",
            "listening": "yellow",
            "speaking": "blue",
            "processing": "orange",
            "error": "red",
        }

        color = status_colors.get(status, "gray")
        self.status_indicator.configure(text=f"● {status.capitalize()}", text_color=color)

    def append_message(self, role: str, message: str) -> None:
        """Append a message to the conversation display."""
        if self.dashboard_content and hasattr(self.dashboard_content, 'append_message'):
            self.dashboard_content.append_message(role, message)

    def clear_messages(self) -> None:
        """Clear all messages from the conversation display."""
        if self.dashboard_content and hasattr(self.dashboard_content, 'clear_messages'):
            self.dashboard_content.clear_messages()

    def get_input_text(self) -> str:
        """Get text from the input field."""
        return self.input_entry.get()

    def clear_input(self) -> None:
        """Clear the input field."""
        self.input_entry.delete(0, 'end')

    def set_input_focus(self) -> None:
        """Set focus to the input field."""
        self.input_entry.focus()

    def _on_enter_pressed(self) -> None:
        """Handle Enter key press in input field."""
        self._on_send_clicked()

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        text = self.get_input_text().strip()
        if text and 'on_send' in self.callbacks:
            self.callbacks['on_send'](text)
            self.clear_input()

    def _on_mic_clicked(self) -> None:
        """Handle mic button click."""
        if 'on_mic' in self.callbacks:
            self.callbacks['on_mic']()

    def _on_settings_clicked(self) -> None:
        """Handle settings button click."""
        if 'on_settings' in self.callbacks:
            self.callbacks['on_settings']()

    def register_callback(self, name: str, callback: Callable) -> None:
        """Register a callback function."""
        self.callbacks[name] = callback

    def on_close(self) -> None:
        """Handle window close event."""
        logger.info("Freddie window closing")
        if 'on_close' in self.callbacks:
            self.callbacks['on_close']()
        self.destroy()


# Make the window accessible
if __name__ == "__main__":
    app = FreddieWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
