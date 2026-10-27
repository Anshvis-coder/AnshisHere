"""Cinematic startup / awakening screen — theme aware, skippable."""
from __future__ import annotations

import math

import customtkinter as ctk

from app.components import ActionButton, ThemedLabel, animations_on
from app.theme_manager import theme_manager
from database import db


class AwakeningScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._alpha_step = 0.0
        self._job = None
        p = theme_manager.palette
        self.configure(fg_color=p.BG)
        self._apply_fn = lambda pal: self.configure(fg_color=pal.BG) \
            if self.winfo_exists() else None
        theme_manager.register(self._apply_fn)

        self.center = ctk.CTkFrame(self, fg_color="transparent")
        self.center.place(relx=0.5, rely=0.46, anchor="center")

        self.logo = ThemedLabel(self.center, text="DEMONBACK X", size=52, bold=True,
                                level="accent")
        self.logo.pack()
        self.sub = ThemedLabel(self.center, text="TWO MINDS. ONE ARENA. ZERO EXCUSES.",
                               size=15, level="secondary")
        self.sub.pack(pady=(10, 30))

        # animated underline
        self.pulse = ctk.CTkFrame(self.center, height=3, width=280, corner_radius=2,
                                  fg_color=p.ACCENT)
        self.pulse.pack(pady=(0, 34))

        btns = ctk.CTkFrame(self.center, fg_color="transparent")
        btns.pack()
        self.continue_btn = ActionButton(btns, text="CONTINUE ▸", width=200, height=42,
                                         command=self._continue)
        self.continue_btn.pack(side="left", padx=6)
        self.profiles_btn = ActionButton(btns, text="PROFILES", width=150, kind="secondary",
                                         command=lambda: self.app.show_profile_select())
        self.profiles_btn.pack(side="left", padx=6)
        self.settings_btn = ActionButton(btns, text="⚙ Settings", width=110, kind="ghost",
                                         command=lambda: self.app.open_settings_from_boot())
        self.settings_btn.pack(side="left", padx=6)

        hint = ThemedLabel(self, text="Press Enter to continue · animation & sound can be "
                                      "disabled in Settings", size=11, level="muted")
        hint.pack(side="bottom", pady=12)

        if db.get_setting("sound_enabled", "1") == "1":
            try:
                from app.notifications import play_beep
                play_beep("info")
            except Exception:
                pass
        if animations_on() and db.get_setting("show_awakening", "1") == "1":
            self._fade_in()
        self.bind("<Return>", lambda e: self._continue())

    def _fade_in(self):
        """Logo fade/scale-in using incremental font size (safe, no alpha issues)."""
        self._alpha_step = 0
        base = 8
        target = 52

        def step():
            if not self.winfo_exists():
                return
            self._alpha_step += 1
            t = min(1.0, self._alpha_step / 22)
            ease = 1 - (1 - t) ** 3
            size = int(base + (target - base) * ease)
            self.logo.configure(font=ctk.CTkFont(size=size, weight="bold"))
            w = int(280 * ease)
            self.pulse.configure(width=max(4, w))
            if t < 1.0:
                self._job = self.after(28, step)

        step()

    def _continue(self):
        if db.get_setting("show_awakening", "1") == "1":
            self.app.navigate("dashboard" if self.app.current_profile_id else "profile_select")
        else:
            self.app.navigate("dashboard" if self.app.current_profile_id else "profile_select")

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        theme_manager.unregister(self._apply_fn)
        super().destroy()
