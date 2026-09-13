"""
Dashboard Frame for Freddie GUI
================================
Contains the main conversation display area.
"""

import customtkinter as ctk
from typing import List, Tuple
from datetime import datetime


class DashboardFrame(ctk.CTkScrollableFrame):
    """Main dashboard with conversation history and status."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.messages: List[Tuple[str, str, str]] = []  # (role, message, timestamp)
        self.message_widgets = []

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dashboard UI."""
        # Welcome message
        self.welcome_frame = ctk.CTkFrame(self)
        self.welcome_frame.pack(fill="x", padx=10, pady=20)

        welcome_text = (
            f"Welcome to Freddie!\n\n"
            f"I'm your personal AI assistant. You can:\n\n"
            f"• Ask me questions\n"
            f"• Open applications (Chrome, Notepad, etc.)\n"
            f"• Search the web\n"
            f"• Manage files and folders\n"
            f"• Check system status\n"
            f"• Create notes and reminders\n\n"
            f"Try saying \"Hello\" or \"Open Chrome\"!"
        )

        self.welcome_label = ctk.CTkLabel(
            self.welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        self.welcome_label.pack(anchor="w", padx=15, pady=15)

        # Conversation area
        self.conversation_container = ctk.CTkFrame(self)
        self.conversation_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.conversation_container.grid_columnconfigure(0, weight=1)

        self.row_num = 0

    def append_message(self, role: str, message: str) -> None:
        """
        Append a message to the conversation display.

        Args:
            role: 'user' or 'freddie'
            message: The message text
        """
        timestamp = datetime.now().strftime("%H:%M")
        self.messages.append((role, message, timestamp))

        # Create message frame
        msg_frame = ctk.CTkFrame(self.conversation_container)
        msg_frame.grid(row=self.row_num, column=0, sticky="ew", padx=5, pady=5)
        msg_frame.grid_columnconfigure(0, weight=1)

        # Role label
        role_color = "#3B8ED0" if role == "freddie" else "#2CC985"
        role_name = "Freddie" if role == "freddie" else "You"

        role_label = ctk.CTkLabel(
            msg_frame,
            text=role_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=role_color
        )
        role_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        # Time label
        time_label = ctk.CTkLabel(
            msg_frame,
            text=timestamp,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        time_label.grid(row=0, column=0, sticky="e", padx=10, pady=(5, 0))

        # Message content
        msg_label = ctk.CTkLabel(
            msg_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=650
        )
        msg_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        self.message_widgets.append(msg_frame)
        self.row_num += 1

        # Scroll to bottom
        self._scroll_to_bottom()

        # Hide welcome after first message
        if len(self.messages) == 1 and hasattr(self, 'welcome_frame'):
            self.welcome_frame.pack_forget()

    def clear_messages(self) -> None:
        """Clear all messages from the display."""
        for widget in self.message_widgets:
            widget.destroy()
        self.message_widgets = []
        self.messages = []
        self.row_num = 0

        # Show welcome again
        if not hasattr(self, 'welcome_frame') or not self.welcome_frame.winfo_ismounted():
            self._rebuild_welcome()

    def _rebuild_welcome(self) -> None:
        """Rebuild the welcome message."""
        self.welcome_frame = ctk.CTkFrame(self)
        self.welcome_frame.pack(fill="x", padx=10, pady=20, before=self.conversation_container)

        welcome_text = (
            f"Welcome to Freddie!\n\n"
            f"I'm your personal AI assistant. How can I help you today?"
        )

        self.welcome_label = ctk.CTkLabel(
            self.welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        self.welcome_label.pack(anchor="w", padx=15, pady=15)

    def _scroll_to_bottom(self) -> None:
        """Scroll the view to the bottom."""
        try:
            self._scrollbar.set(1.0, 0)
        except:
            pass

    def get_message_count(self) -> int:
        """Get the number of messages."""
        return len(self.messages)

    def get_recent_messages(self, limit: int = 10) -> List[Tuple[str, str]]:
        """Get recent messages as (role, message) tuples."""
        return self.messages[-limit:]
