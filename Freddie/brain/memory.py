"""
Memory Manager for Freddie
===========================
Handles SQLite database operations for memory, notes, and reminders.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages persistent storage using SQLite."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_tables(self) -> None:
        """Create necessary database tables."""
        cursor = self.conn.cursor()

        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                reminder_time TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        logger.debug("Database tables created/verified")

    # Memory Operations
    def add_memory(self, content: str, category: str = "general") -> int:
        """Add a new memory entry."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memories (content, category) VALUES (?, ?)",
                (content, category)
            )
            self.conn.commit()
            memory_id = cursor.lastrowid
            logger.debug(f"Memory added with ID: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return -1

    def get_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories by content."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    def clear_memories(self) -> bool:
        """Clear all memories."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM memories")
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False

    # Note Operations
    def add_note(self, content: str, title: str = None) -> int:
        """Add a new note."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO notes (content, title) VALUES (?, ?)",
                (content, title)
            )
            self.conn.commit()
            note_id = cursor.lastrowid
            logger.debug(f"Note added with ID: {note_id}")
            return note_id
        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            return -1

    def get_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent notes."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM notes ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get notes: {e}")
            return []

    def get_recent_notes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent notes (alias for get_notes)."""
        return self.get_notes(limit)

    def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search notes by content."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM notes WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return []

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete note: {e}")
            return False

    # Reminder Operations
    def add_reminder(self, content: str, reminder_time: datetime) -> int:
        """Add a new reminder."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (content, reminder_time) VALUES (?, ?)",
                (content, reminder_time.isoformat())
            )
            self.conn.commit()
            reminder_id = cursor.lastrowid
            logger.debug(f"Reminder added with ID: {reminder_id}")
            return reminder_id
        except Exception as e:
            logger.error(f"Failed to add reminder: {e}")
            return -1

    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Get all active reminders."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM reminders WHERE is_active = 1 ORDER BY reminder_time ASC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get active reminders: {e}")
            return []

    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders that are due now."""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                """SELECT * FROM reminders 
                   WHERE is_active = 1 AND reminder_time <= ? 
                   ORDER BY reminder_time ASC""",
                (now,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get due reminders: {e}")
            return []

    def mark_reminder_done(self, reminder_id: int) -> bool:
        """Mark a reminder as completed."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE reminders SET is_active = 0 WHERE id = ?",
                (reminder_id,)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark reminder done: {e}")
            return False

    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            return False

    # Preference Operations
    def set_preference(self, key: str, value: str) -> bool:
        """Set a user preference."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO preferences (key, value, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, value)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to set preference: {e}")
            return False

    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a user preference."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default
        except Exception as e:
            logger.error(f"Failed to get preference: {e}")
            return default

    def delete_preference(self, key: str) -> bool:
        """Delete a preference."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM preferences WHERE key = ?", (key,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete preference: {e}")
            return False

    # Conversation History Operations
    def add_conversation(self, user_input: str, assistant_response: str) -> int:
        """Add a conversation entry."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_input, assistant_response) VALUES (?, ?)",
                (user_input, assistant_response)
            )
            self.conn.commit()
            conv_id = cursor.lastrowid
            return conv_id
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            return -1

    def get_recent_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversations."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the singleton MemoryManager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
