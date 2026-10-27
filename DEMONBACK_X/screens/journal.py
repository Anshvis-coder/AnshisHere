"""Journal — private per-profile daily reflections."""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from app.components import (ActionButton, SectionTitle, ThemedEntry, ThemedFrame,
                            ThemedLabel, ThemedTextbox, toast)
from app.theme_manager import theme_manager
from database import repositories as repo


class JournalScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.day = date.today()
        self.configure(fg_color="transparent")

        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=20, pady=(18, 6))
        SectionTitle(head, text="JOURNAL").pack(anchor="w")
        ThemedLabel(head, text="Private to this profile. Reflection is part of training.",
                    level="secondary", size=12).pack(anchor="w")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        left = ThemedFrame(body, role="card")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        nav = ctk.CTkFrame(left, fg_color="transparent")
        nav.pack(fill="x", padx=14, pady=(12, 2))
        ActionButton(nav, text="◂", kind="ghost", width=40, height=28,
                     command=lambda: self._shift(-1)).pack(side="left")
        self.day_lbl = ThemedLabel(nav, text="", level="primary", size=14, bold=True)
        self.day_lbl.pack(side="left", expand=True)
        ActionButton(nav, text="▸", kind="ghost", width=40, height=28,
                     command=lambda: self._shift(1)).pack(side="right")
        ActionButton(nav, text="Today", kind="secondary", width=70, height=28,
                     command=lambda: self._goto_today()).pack(side="right", padx=6)

        ThemedLabel(left, text="Mood (1 awful – 10 strong)", level="secondary", size=12)\
            .pack(anchor="w", padx=16, pady=(8, 2))
        mood_row = ctk.CTkFrame(left, fg_color="transparent")
        mood_row.pack(anchor="w", padx=16)
        self.mood_slider = ctk.CTkSlider(mood_row, from_=1, to=10, number_of_steps=9,
                                         width=280,
                                         progress_color=theme_manager.palette.ACCENT,
                                         button_color=theme_manager.palette.TEXT_PRIMARY)
        self.mood_slider.set(5)
        self.mood_slider.pack(side="left")
        self.mood_lbl = ThemedLabel(mood_row, text="5", level="primary", size=14, bold=True)
        self.mood_lbl.pack(side="left", padx=10)
        self.mood_slider.configure(command=lambda v: self.mood_lbl.configure(
            text=str(int(round(v)))))

        for label, attr in [("Wins today (what went right?)", "wins_t"),
                            ("Reflection", "refl_t"),
                            ("Distractions / obstacles", "dist_t")]:
            ThemedLabel(left, text=label, level="secondary", size=12).pack(
                anchor="w", padx=16, pady=(8, 2))
            t = ThemedTextbox(left, height=70 if attr != "refl_t" else 110, width=520)
            t.pack(fill="x", padx=16)
            setattr(self, attr, t)

        brow = ctk.CTkFrame(left, fg_color="transparent")
        brow.pack(padx=16, pady=12, anchor="w")
        ActionButton(brow, text="Save Entry", width=130, command=self._save).pack(side="left")
        ThemedLabel(brow, text="First saved reflection of the day earns XP.",
                    level="muted", size=11).pack(side="left", padx=10)

        right = ThemedFrame(body, role="card", width=300)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)
        ThemedLabel(right, text="PAST ENTRIES", level="secondary", size=11, bold=True)\
            .pack(anchor="w", padx=14, pady=(12, 4))
        self.hist = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.hist.pack(fill="both", expand=True, padx=6, pady=(0, 8))

    # -------------------------------------------------------------------- ops --
    def _shift(self, d):
        self.day += timedelta(days=d)
        self.refresh()

    def _goto_today(self):
        self.day = date.today()
        self.refresh()

    def _save(self):
        pid = self.app.current_profile_id
        awarded = repo.Journal.save(pid, self.day.isoformat(),
                                    reflection=self.refl_t.get("1.0", "end").strip(),
                                    mood=int(round(self.mood_slider.get())),
                                    distractions=self.dist_t.get("1.0", "end").strip(),
                                    wins=self.wins_t.get("1.0", "end").strip())
        toast(self.app, "Entry saved." + (" +reflection XP!" if awarded else ""),
              "success")
        self.app.after_activity(pid)
        self.refresh()

    def refresh(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        self.day_lbl.configure(text=self.day.strftime("%A · %d %b %Y"))
        e = repo.Journal.get_entry(pid, self.day.isoformat())
        for t in (self.wins_t, self.refl_t, self.dist_t):
            t.delete("1.0", "end")
        if e:
            self.wins_t.insert("1.0", e["wins"] or "")
            self.refl_t.insert("1.0", e["reflection"] or "")
            self.dist_t.insert("1.0", e["distractions"] or "")
            self.mood_slider.set(e["mood"])
            self.mood_lbl.configure(text=str(e["mood"]))
        for w in self.hist.winfo_children():
            w.destroy()
        p = theme_manager.palette
        rows = repo.Journal.entries(pid, limit=40)
        if not rows:
            ThemedLabel(self.hist, text="No entries yet.\nThis journal is only visible to "
                        "your profile.", level="muted", size=12, justify="center")\
                .pack(pady=20)
        for r in rows:
            card = ctk.CTkFrame(self.hist, fg_color=p.CARD_HOVER, corner_radius=8)
            card.pack(fill="x", pady=3)
            ctk.CTkLabel(card, text=f"{r['entry_date']} · mood {r['mood']}/10",
                         text_color=p.ACCENT, font=ctk.CTkFont(size=12, bold=True))\
                .pack(anchor="w", padx=10, pady=(6, 0))
            snippet = (r["reflection"] or "").strip().replace("\n", " ")
            if len(snippet) > 90:
                snippet = snippet[:90] + "…"
            if snippet:
                ctk.CTkLabel(card, text=snippet, text_color=p.TEXT_SECONDARY,
                             font=ctk.CTkFont(size=11), wraplength=250,
                             justify="left").pack(anchor="w", padx=10, pady=(0, 6))
