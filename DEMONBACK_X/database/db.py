"""DEMONBACK X — SQLite access layer.

Handles: directory creation, schema init, migrations, backups, settings,
and a thread-safe connection helper.  All UI code talks to the database
through repositories in `database/repositories.py`, never raw SQL.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

APP_NAME = "DEMONBACK X"
VERSION = "1.0.0"

# ---------------------------------------------------------------- paths ----
def get_base_dir() -> Path:
    """Directory containing the project (or exe when frozen with PyInstaller)."""
    if getattr(os.sys, "frozen", False):  # pragma: no cover - frozen builds only
        return Path(os.sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "demonback_x.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_db_lock = threading.RLock()
_connection: sqlite3.Connection | None = None


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(("demonback::" + pin).encode("utf-8")).hexdigest()


def ensure_dirs() -> None:
    for d in (DATA_DIR, BACKUP_DIR, EXPORT_DIR,
              ASSETS_DIR / "icons", ASSETS_DIR / "backgrounds",
              ASSETS_DIR / "fonts", ASSETS_DIR / "sounds"):
        d.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    global _connection
    with _db_lock:
        if _connection is None:
            ensure_dirs()
            _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA foreign_keys = ON")
            _connection.execute("PRAGMA journal_mode = WAL")
        return _connection


class transaction:
    """Context manager giving atomic commit/rollback across repositories."""

    def __enter__(self):
        _db_lock.acquire()
        self.conn = get_conn()
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            _db_lock.release()
        return False


def execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
    with _db_lock:
        conn = get_conn()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur


def query(sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
    with _db_lock:
        return get_conn().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def init_database() -> None:
    """Create all tables from schema.sql, run migrations, seed defaults."""
    ensure_dirs()
    conn = get_conn()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with _db_lock:
            conn.executescript(schema)
            conn.commit()
        from database.migrations import run_migrations
        run_migrations(conn)
        _seed_defaults(conn)
    except sqlite3.DatabaseError as e:
        raise RuntimeError(f"Database initialisation failed: {e}") from e


def _seed_defaults(conn: sqlite3.Connection) -> None:
    # Achievements catalogue -------------------------------------------------
    achievements = [
        ("first_blood", "First Blood", "Complete your very first mission or habit.", "+", 10),
        ("week_warrior", "Week Warrior", "Reach a 7-day streak.", "*", 30),
        ("iron_streak", "Iron Streak", "Reach a 30-day streak.", "#", 75),
        ("mental_monk", "Mental Monk", "Log 10 focus sessions.", "M", 25),
        ("deep_focus", "Deep Focus", "Complete a focus session of 60 minutes or more.", "F", 20),
        ("body_forge", "Body Forge", "Log 10 workout sessions.", "B", 25),
        ("hydrated", "Hydration Hero", "Hit your daily water goal once.", "H", 10),
        ("reflective", "Reflective Mind", "Write 7 journal entries.", "J", 20),
        ("rank_disciplined", "Rank: Disciplined", "Reach the Disciplined rank.", "R", 20),
        ("rank_relentless", "Rank: Relentless", "Reach the Relentless rank.", "R", 40),
        ("rank_elite", "Rank: Elite", "Reach the Elite rank.", "R", 75),
        ("rank_apex", "Rank: Apex", "Reach the Apex rank.", "R", 150),
        ("rival_slayer", "Rival Slayer", "Win a weekly rivalry round.", "V", 25),
        ("challenge_done", "Challenger", "Complete a weekly challenge.", "C", 30),
    ]
    for key, title, desc, icon, bonus in achievements:
        conn.execute(
            "INSERT OR IGNORE INTO achievements(key,title,description,icon,xp_bonus) VALUES(?,?,?,?,?)",
            (key, title, desc, icon, bonus))
    # Default settings -------------------------------------------------------
    defaults = {
        "theme": "dark",                      # dark | light | system
        "sound_enabled": "1",
        "animations_enabled": "1",
        "notifications_enabled": "1",
        "quiet_hours": "22:00-07:00",
        "show_awakening": "1",
        "xp_focus_session": "20",
        "xp_reading_session": "15",
        "xp_workout": "25",
        "xp_mobility": "10",
        "xp_priority_task": "20",
        "xp_daily_reflection": "10",
        "daily_water_goal_ml": "2000",
        "challenge_difficulty": "normal",
        "last_profile_id": "0",
    }
    for k, v in defaults.items():
        conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    conn.commit()


# ------------------------------------------------------------ settings ----
DEFAULT_SETTINGS = {
    "theme": "dark", "sound_enabled": "1", "animations_enabled": "1",
    "notifications_enabled": "1", "quiet_hours": "22:00-07:00",
    "show_awakening": "1", "xp_focus_session": "20", "xp_reading_session": "15",
    "xp_workout": "25", "xp_mobility": "10", "xp_priority_task": "20",
    "xp_daily_reflection": "10", "daily_water_goal_ml": "2000",
    "challenge_difficulty": "normal", "last_profile_id": "0",
}


def get_setting(key: str, default: str | None = None) -> str:
    row = query_one("SELECT value FROM settings WHERE key=?", (key,))
    if row:
        return row["value"]
    return DEFAULT_SETTINGS.get(key, default if default is not None else "")


def set_setting(key: str, value: str) -> None:
    execute("INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


# ------------------------------------------------------------- backups ----
def create_backup(tag: str = "auto") -> Path:
    """Copy current DB into backups/ with timestamp. Keeps last 20."""
    ensure_dirs()
    if not DB_PATH.exists():
        raise FileNotFoundError("No database file to back up yet.")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"demonback_{tag}_{stamp}.db"
    with _db_lock:
        src = get_conn()
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)          # safe online backup API
        finally:
            dst.close()
    backups = sorted(BACKUP_DIR.glob("demonback_*.db"), key=lambda p: p.stat().st_mtime)
    for old in backups[:-20]:
        try:
            old.unlink()
        except OSError:
            pass
    return dest


def list_backups() -> list[Path]:
    ensure_dirs()
    return sorted(BACKUP_DIR.glob("demonback_*.db"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def restore_backup(path: Path) -> None:
    """Replace live DB with a backup file (live DB is backed up first)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Backup not found: {path}")
    create_backup("pre_restore")
    global _connection
    with _db_lock:
        if _connection is not None:
            _connection.close()
            _connection = None
        shutil.copyfile(path, DB_PATH)
    get_conn()  # reopen & validate
    with _db_lock:
        get_conn().execute("PRAGMA quick_check").fetchone()


def reset_all_data() -> None:
    """Delete every table's contents but keep schema (used by Settings > Reset)."""
    create_backup("pre_reset")
    tables = ["achievement_unlocks", "rivalry_results", "challenge_participants",
              "weekly_challenges", "journal_entries", "xp_transactions", "streaks",
              "hydration_logs", "workout_sessions", "focus_sessions", "completions",
              "daily_missions", "habit_schedules", "habits", "profiles"]
    with _db_lock:
        conn = get_conn()
        for t in tables:
            conn.execute(f"DELETE FROM {t}")
        conn.execute("DELETE FROM sqlite_sequence")
        conn.commit()


pin_hash = _hash_pin
