"""Mission Room — daily challenges, manual missions, weekly challenge control."""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from app.components import (ActionButton, ProgressBar, SectionTitle, ThemedEntry,
                            ThemedFrame, ThemedLabel, ThemedOptionMenu, ThemedTextbox,
                            toast)
from app.theme_manager import theme_manager
from core import challenge_generator, validation
from database import repositories as repo


class MissionRoomScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.day = date.today()
        self.configure(fg_color="transparent")

        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=20, pady=(18, 6))
        SectionTitle(head, text="MISSION ROOM").pack(anchor="w")
        nav = ctk.CTkFrame(head, fg_color="transparent")
        nav.pack(anchor="e")
        ActionButton(nav, text="◂", kind="ghost", width=40, height=28,
                     command=lambda: self._shift(-1)).grid(row=0, column=0)
        self.day_lbl = ThemedLabel(nav, text="", level="primary", size=13, bold=True)
        self.day_lbl.grid(row=0, column=1, padx=10)
        ActionButton(nav, text="▸", kind="ghost", width=40, height=28,
                     command=lambda: self._shift(1)).grid(row=0, column=2)
        ActionButton(nav, text="+ Custom Mission", kind="secondary", width=150, height=28,
                     command=self._add_custom).grid(row=0, column=3, padx=(14, 0))
        ActionButton(nav, text="Generate Daily", width=130, height=28,
                     command=self._generate).grid(row=0, column=4, padx=(6, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        left = ctk.CTkScrollableFrame(body, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.list_holder = left

        right = ctk.CTkFrame(body, fg_color="transparent", width=330)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        chal_card = ThemedFrame(right, role="card")
        chal_card.pack(fill="x")
        ThemedLabel(chal_card, text="WEEKLY CHALLENGE", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(12, 2))
        self.chal_title = ThemedLabel(chal_card, text="—", level="primary", size=15, bold=True)
        self.chal_title.pack(anchor="w", padx=14)
        self.chal_desc = ThemedLabel(chal_card, text="", level="secondary", size=12,
                                     wraplength=290, justify="left")
        self.chal_desc.pack(anchor="w", padx=14, pady=(2, 6))
        self.chal_bar = ProgressBar(chal_card, height=6)
        self.chal_bar.pack(fill="x", padx=14)
        self.chal_meta = ThemedLabel(chal_card, text="", level="muted", size=11)
        self.chal_meta.pack(anchor="w", padx=14, pady=(4, 8))
        crow = ctk.CTkFrame(chal_card, fg_color="transparent")
        crow.pack(padx=10, pady=(0, 12), anchor="w")
        self.complete_btn = ActionButton(crow, text="Mark Complete", width=120, height=30,
                                         command=self._complete_challenge)
        self.complete_btn.pack(side="left", padx=3)
        ActionButton(crow, text="New Challenge", kind="secondary", width=120, height=30,
                     command=self._new_challenge_dialog).pack(side="left", padx=3)

        hist_card = ThemedFrame(right, role="card")
        hist_card.pack(fill="both", expand=True, pady=(8, 0))
        ThemedLabel(hist_card, text="CHALLENGE HISTORY", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(12, 4))
        self.hist_holder = ctk.CTkScrollableFrame(hist_card, fg_color="transparent")
        self.hist_holder.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ------------------------------------------------------------------ data --
    def _shift(self, delta):
        self.day += timedelta(days=delta)
        self.refresh()

    def refresh(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        self.day_lbl.configure(text=self.day.strftime("%A · %d %b %Y"))
        for w in self.list_holder.winfo_children():
            w.destroy()
        missions = repo.Missions.for_date(pid, self.day.isoformat())
        if not missions:
            ThemedLabel(self.list_holder,
                        text="No missions for this day.\nUse 'Generate Daily' or add a custom mission.",
                        level="muted", size=13, justify="center").pack(pady=30)
        for m in missions:
            self._mission_row(m)
        self._refresh_challenge_panel(pid)
        self._refresh_history()

    def _mission_row(self, m):
        card = ThemedFrame(self.list_holder, role="card")
        card.pack(fill="x", pady=4)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)
        status_color = {"done": "success", "pending": "primary",
                        "skipped": "muted", "postponed": "warning"}[m["status"]]
        ThemedLabel(row, text=m["title"], level="primary", size=15, bold=True)\
            .pack(side="left")
        ThemedLabel(row, text=f"[{m['status'].upper()}]", level=status_color, size=11,
                    bold=True).pack(side="left", padx=8)
        ThemedLabel(row, text=f"{m['category']} · {m['difficulty']} · {m['xp_reward']} XP"
                    + (" · team" if m["source"] == "challenge" else ""),
                    level="secondary", size=12).pack(side="left", padx=6)
        if m["description"]:
            ThemedLabel(row, text=m["description"], level="muted", size=11)\
                .pack(side="left", padx=6)
        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.pack(side="right")
        if m["status"] == "pending":
            ActionButton(btns, text="Complete", width=90, height=28,
                         command=lambda: self._do(m["id"], "done")).grid(row=0, column=0, padx=2)
            ActionButton(btns, text="Skip", kind="ghost", width=60, height=28,
                         command=lambda: self._do(m["id"], "skipped")).grid(row=0, column=1, padx=2)
            ActionButton(btns, text="Postpone", kind="secondary", width=80, height=28,
                         command=lambda: self._do(m["id"], "postponed")).grid(row=0, column=2, padx=2)
        elif m["status"] == "done":
            ActionButton(btns, text="Undo", kind="secondary", width=70, height=28,
                         command=lambda: self._do(m["id"], "undo")).grid(row=0, column=0, padx=2)
        else:
            ActionButton(btns, text="Reactivate", kind="secondary", width=90, height=28,
                         command=lambda: self._do(m["id"], "pending")).grid(row=0, column=0, padx=2)
        ActionButton(btns, text="✕", kind="ghost", width=34, height=28,
                     command=lambda: self._delete(m["id"])).grid(row=0, column=3, padx=2)

    def _do(self, mid, action):
        pid = self.app.current_profile_id
        try:
            if action == "done":
                xp = repo.Missions.complete(mid)
                if xp:
                    toast(self.app, f"+{xp} XP — mission complete!", "success")
            elif action == "undo":
                repo.Missions.undo(mid)
                toast(self.app, "Mission reward reversed.", "warn")
            elif action == "postponed":
                repo.Missions.set_status(mid, "postponed")
                # move it to tomorrow so it actually re-appears
                m = repo.Missions.get(mid)
                tomorrow = (date.fromisoformat(m["mission_date"]) + timedelta(days=1)).isoformat()
                repo.db.execute("UPDATE daily_missions SET mission_date=?, status='pending' WHERE id=?",
                                (tomorrow, mid))
                toast(self.app, "Mission postponed to tomorrow.", "info")
            else:
                repo.Missions.set_status(mid, action)
            self.app.after_activity(pid)
            self.refresh()
        except ValueError as e:
            toast(self.app, str(e), "error")

    def _delete(self, mid):
        repo.Missions.delete(mid)
        self.refresh()

    def _generate(self):
        pid = self.app.current_profile_id
        ids = challenge_generator.generate_daily_missions(pid, self.day)
        challenge_generator.ensure_weekly_challenge(
            [p["id"] for p in repo.Profiles.all() if p["is_active"]])
        toast(self.app, f"{len(ids)} mission(s) ready for {self.day:%d %b}.", "success")
        self.refresh()

    def _add_custom(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Custom Mission"); dlg.transient(self.app); dlg.grab_set()
        frame = ThemedFrame(dlg, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        ThemedLabel(frame, text="Title", level="secondary", size=12).pack(anchor="w",
                                                                         padx=16, pady=(12, 2))
        t_e = ThemedEntry(frame, width=340); t_e.pack(padx=16, anchor="w")
        ThemedLabel(frame, text="Description", level="secondary", size=12).pack(anchor="w",
                                                                               padx=16, pady=(8, 2))
        d_t = ThemedTextbox(frame, width=340, height=60); d_t.pack(padx=16, anchor="w")
        g = ctk.CTkFrame(frame, fg_color="transparent"); g.pack(padx=16, pady=(8, 0), anchor="w")
        ThemedLabel(g, text="Category", level="secondary", size=12).grid(row=0, column=0, padx=(0, 10))
        ThemedLabel(g, text="Difficulty", level="secondary", size=12).grid(row=0, column=1, padx=(0, 10))
        ThemedLabel(g, text="XP", level="secondary", size=12).grid(row=0, column=2)
        cat_m = ThemedOptionMenu(g, ["Mental", "Physical", "Discipline"], width=120)
        cat_m.grid(row=1, column=0, padx=(0, 10))
        diff_m = ThemedOptionMenu(g, ["easy", "normal", "hard"], width=110)
        diff_m.grid(row=1, column=1, padx=(0, 10))
        xp_e = ThemedEntry(g, width=70); xp_e.grid(row=1, column=2); xp_e.insert(0, "15")
        btns = ctk.CTkFrame(frame, fg_color="transparent"); btns.pack(pady=14)

        def save():
            try:
                title = validation.require_text(t_e.get(), "Title", 80)
                xp = validation.parse_int(xp_e.get(), "XP", 0, 300)
                repo.Missions.add(self.app.current_profile_id, self.day.isoformat(),
                                  title, d_t.get("1.0", "end").strip(), cat_m.get(),
                                  diff_m.get(), xp, source="manual")
                toast(self.app, "Custom mission added.", "success")
                dlg.destroy(); self.refresh()
            except ValueError as e:
                toast(self.app, str(e), "error")

        ActionButton(btns, text="Add", command=save).grid(row=0, column=0, padx=5)
        ActionButton(btns, text="Cancel", kind="secondary", command=dlg.destroy)\
            .grid(row=0, column=1, padx=5)

    # ------------------------------------------------------------ challenge --
    def _refresh_challenge_panel(self, pid):
        active = repo.Challenges.active()
        if active:
            ch = active[0]
            self.chal_title.configure(text=f"{ch['title']} ({ch['mode']})")
            self.chal_desc.configure(text=ch["description"])
            parts = repo.Challenges.participants(ch["id"])
            self.chal_bar.set(min(1.0, (ch["progress_value"] or 0) / max(ch["target_value"], 1e-9)))
            contrib = " | ".join(f"{p['name']}: {p['contribution']:g}" for p in parts)
            self.chal_meta.configure(text=f"{ch['start_date']} → {ch['deadline']} · "
                                          f"{ch['progress_value']:g}/{ch['target_value']:g} "
                                          f"({ch['metric']}) · {contrib}")
            self.complete_btn.configure(state="normal")
            self._active_chal_id = ch["id"]
        else:
            self.chal_title.configure(text="No active challenge")
            self.chal_desc.configure(text="Create one below or generate from the dashboard.")
            self.chal_bar.set(0)
            self.chal_meta.configure(text="")
            self.complete_btn.configure(state="disabled")
            self._active_chal_id = None

    def _complete_challenge(self):
        if not self._active_chal_id:
            return
        ch = repo.Challenges.get(self._active_chal_id)
        winner = None
        if ch["mode"] == "competitive":
            parts = sorted(repo.Challenges.participants(self._active_chal_id),
                           key=lambda p: p["contribution"], reverse=True)
            winner = parts[0]["profile_id"] if parts else None
        awarded = repo.Challenges.complete(self._active_chal_id, winner)
        if awarded:
            toast(self.app, f"Challenge complete! +{ch['xp_reward']} XP awarded.", "success")
        self.app.after_activity(self.app.current_profile_id)
        self.refresh()

    def _new_challenge_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("New Weekly Challenge"); dlg.transient(self.app); dlg.grab_set()
        frame = ThemedFrame(dlg, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        rows = []

        def field(label, default="", values=None, width=300):
            ThemedLabel(frame, text=label, level="secondary", size=12).pack(anchor="w",
                                                                           padx=16, pady=(8, 2))
            if values:
                w = ThemedOptionMenu(frame, values, width=width)
            else:
                w = ThemedEntry(frame, width=width); w.insert(0, default)
            w.pack(padx=16, anchor="w")
            rows.append(w)
            return w

        field("Title", "Custom Challenge")
        field("Description", "Describe the shared goal.")
        mode_m = field("Mode", values=["cooperative", "competitive"], width=160)
        metric_m = field("Metric", values=["xp", "completions", "focus_minutes",
                                           "workouts", "days_active"], width=160)
        field("Target value", "10")
        field("XP reward", "50")
        btns = ctk.CTkFrame(frame, fg_color="transparent"); btns.pack(pady=12)

        def save():
            try:
                title = validation.require_text(rows[0].get(), "Title", 80)
                target = validation.parse_float(rows[4].get(), "Target", 0.01, 100000)
                xp = validation.parse_int(rows[5].get(), "XP reward", 0, 1000)
                monday = date.today() - timedelta(days=date.today().weekday())
                pids = [p["id"] for p in repo.Profiles.all() if p["is_active"]]
                repo.Challenges.create(title, rows[1].get(), mode_m.get(), metric_m.get(),
                                       target, xp, monday.isoformat(),
                                       (monday + timedelta(days=6)).isoformat(),
                                       profile_ids=pids)
                toast(self.app, "Challenge created for both players.", "success")
                dlg.destroy(); self.refresh()
            except ValueError as e:
                toast(self.app, str(e), "error")

        ActionButton(btns, text="Create", command=save).grid(row=0, column=0, padx=5)
        ActionButton(btns, text="Cancel", kind="secondary", command=dlg.destroy)\
            .grid(row=0, column=1, padx=5)

    def _refresh_history(self):
        for w in self.hist_holder.winfo_children():
            w.destroy()
        for ch in repo.Challenges.all(limit=8):
            txt = f"{ch['title']} · {ch['status']}"
            lvl = "success" if ch["status"] == "completed" else \
                  ("warning" if ch["status"] == "expired" else "info")
            ThemedLabel(self.hist_holder, text=txt, level=lvl, size=12).pack(anchor="w",
                                                                            padx=6, pady=1)
