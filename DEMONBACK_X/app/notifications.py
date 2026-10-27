"""Local notification + motivation system.

- In-app toasts always work offline.
- Native Windows desktop notifications use the built-in PowerShell
  BurntToast-less approach (Windows.UI.Notifications via powershell) and
  silently fall back to toasts when unavailable.
- Honours quiet hours, enable/disable flags and sound preference.
"""
from __future__ import annotations

import random
import subprocess
import sys
import tkinter as tk
from datetime import datetime, time as dtime

from database import db

MOTIVATION_MESSAGES = [
    "Your first mission is waiting.",
    "Focus on the next action.",
    "Progress is built through repeated effort.",
    "Your next milestone is within reach.",
    "Review your plan and begin again.",
    "Small consistent steps beat rare heroic leaps.",
    "Discipline is choosing what you want most over what you want now.",
    "The arena rewards those who show up.",
    "Recovery is training. Rest with intent.",
    "One focused hour is worth a distracted day.",
]


def daily_motivation(profile_id: int | None = None) -> str:
    """Deterministic per-day message so both players see variety daily."""
    seed = datetime.now().strftime("%Y%m%d") + str(profile_id or 0)
    rng = random.Random(seed)
    return rng.choice(MOTIVATION_MESSAGES)


def random_motivation() -> str:
    return random.choice(MOTIVATION_MESSAGES)


def _parse_hhmm(s: str) -> dtime | None:
    try:
        h, m = s.split(":")
        return dtime(int(h), int(m))
    except Exception:
        return None


def in_quiet_hours() -> bool:
    spec = db.get_setting("quiet_hours", "22:00-07:00")
    if "-" not in spec:
        return False
    start_s, end_s = spec.split("-", 1)
    start, end = _parse_hhmm(start_s.strip()), _parse_hhmm(end_s.strip())
    if not start or not end:
        return False
    now = datetime.now().time()
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end      # wraps past midnight


def notifications_enabled() -> bool:
    return db.get_setting("notifications_enabled", "1") == "1"


def sounds_enabled() -> bool:
    return db.get_setting("sound_enabled", "1") == "1"


def play_beep(kind: str = "info") -> None:
    """Short non-intrusive tone; fails silently on systems without audio."""
    if not sounds_enabled():
        return
    try:
        if sys.platform == "win32":
            import winsound
            freq = {"info": 880, "success": 1046, "warn": 660, "error": 440}[kind]
            winsound.Beep(freq, 120)
        else:
            print("\a", end="", file=sys.stderr)   # terminal bell fallback
    except Exception:
        pass


def native_notify(title: str, message: str) -> bool:
    """Try a real Windows toast notification. Returns True on success."""
    if sys.platform != "win32":
        return False
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
        " ContentType=WindowsRuntime] | Out-Null;"
        "$u=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(2);"
        f"$u.GetXml().Replace('placeholder','{title} - {message}') | Out-Null;"
        "$n=[Windows.UI.Notifications.ToastNotification]::new($u);"
        "[Windows.UI.Notifications.ToastNotificationManager]"
        "::CreateToastNotifier('DEMONBACK X').Show($n);"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except OSError:
        return False


class NotificationService:
    """Coordinates reminders + motivational nudges inside the app."""

    def __init__(self, app):
        self.app = app
        self._jobs: list[str] = []

    def notify(self, title: str, message: str, kind: str = "info") -> None:
        if not notifications_enabled() or in_quiet_hours():
            return
        shown_native = native_notify(title, message)
        if not shown_native:
            from app.components import toast
            toast(self.app, f"{title}: {message}", kind)
        play_beep(kind)

    def schedule_daily_reminders(self) -> None:
        """Check every 5 min whether an evening review reminder is due."""
        def tick():
            try:
                now = datetime.now()
                if now.hour == 20 and now.minute < 5:
                    key = f"reminder_evening_{now:%Y%m%d}"
                    if db.get_setting(key, "0") != "1":
                        db.set_setting(key, "1")
                        self.notify("DEMONBACK X",
                                    "Evening check-in: finish today's missions or "
                                    "write your reflection.")
            finally:
                self._jobs.append(self.app.after(5 * 60 * 1000, tick))

        tick()

    def greet_motivation(self) -> None:
        msg = daily_motivation(self.app.current_profile_id or None)
        self.notify("Motivation", msg, "info")

    def shutdown(self) -> None:
        for job in self._jobs:
            try:
                self.app.after_cancel(job)
            except Exception:
                pass
        self._jobs.clear()
