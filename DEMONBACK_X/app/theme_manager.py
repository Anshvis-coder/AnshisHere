"""Centralized theme manager.

- Owns the active palette (dark / light / system).
- Persists the choice in the settings table.
- Notifies every registered widget/screen when the theme changes so the
  whole application updates immediately without a restart.
"""
from __future__ import annotations

import sys
import tkinter as tk

import customtkinter as ctk

from app.themes import PALETTES, DarkPalette, LightPalette
from database import db


def _windows_system_is_dark() -> bool:
    """Best-effort detection of the OS theme on Windows; False elsewhere."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return int(value) == 0
    except Exception:
        return False


class ThemeManager:
    def __init__(self):
        self._listeners: list = []          # callables(palette)
        self._mode_choice = "dark"          # user's stored choice
        self._palette = DarkPalette
        self._poll_job = None

    # ---------------------------------------------------------- palette ---
    @property
    def palette(self):
        return self._palette

    @property
    def mode(self) -> str:
        """Effective mode after resolving 'system'."""
        if self._mode_choice == "system":
            return "dark" if _windows_system_is_dark() else "light"
        return self._mode_choice

    def resolve_palette(self, choice: str | None = None):
        choice = choice or self._mode_choice
        if choice == "system":
            return DarkPalette if _windows_system_is_dark() else LightPalette
        return PALETTES.get(choice, DarkPalette)

    # ------------------------------------------------------------- setup ---
    def load_from_settings(self) -> None:
        self._mode_choice = db.get_setting("theme", "dark")
        if self._mode_choice not in ("dark", "light", "system"):
            self._mode_choice = "dark"
        self._apply(self.resolve_palette())

    def set_mode(self, choice: str, persist: bool = True) -> None:
        if choice not in ("dark", "light", "system"):
            raise ValueError(f"Unknown theme mode: {choice}")
        self._mode_choice = choice
        if persist:
            db.set_setting("theme", choice)
        self._apply(self.resolve_palette())
        if choice == "system":
            self._start_system_polling()
        else:
            self._stop_system_polling()

    def toggle(self) -> str:
        """Quick switch used by nav shortcut: dark <-> light."""
        new = "light" if self.mode == "dark" else "dark"
        self.set_mode(new)
        return new

    # ------------------------------------------------------------ apply ---
    def _apply(self, palette) -> None:
        self._palette = palette
        ctk.set_appearance_mode(palette.MODE)
        ctk.set_default_color_theme("blue")   # we override all colors anyway
        for cb in list(self._listeners):
            try:
                cb(palette)
            except Exception as e:            # never let one widget break theming
                print(f"[theme] listener error: {e}", file=sys.stderr)

    def register(self, callback) -> None:
        """callback(palette) is invoked now and on every theme change."""
        self._listeners.append(callback)
        try:
            callback(self._palette)
        except Exception as e:
            print(f"[theme] register error: {e}", file=sys.stderr)

    def unregister(self, callback) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ------------------------------------------- system-theme live poll ---
    def _start_system_polling(self) -> None:
        self._stop_system_polling()
        prev = self._palette

        def poll():
            cur = self.resolve_palette("system")
            if cur is not prev:
                prev = cur
                self._apply(cur)
            self._poll_job = tk._default_root.after(5000, poll) \
                if tk._default_root else None

        if tk._default_root is not None:
            self._poll_job = tk._default_root.after(5000, poll)

    def _stop_system_polling(self) -> None:
        if self._poll_job and tk._default_root is not None:
            try:
                tk._default_root.after_cancel(self._poll_job)
            except Exception:
                pass
        self._poll_job = None


# singleton shared across the app
theme_manager = ThemeManager()
