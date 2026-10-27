"""Physical Performance Arena — workouts, cardio, hydration, recovery.

Rest and recovery are valid training days. The app never pushes intensity
beyond what the user configures, and it warns against training through pain.
"""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from app.charts import ChartFrame, style_axes
from app.components import (ActionButton, ProgressBar, SectionTitle, ThemedEntry,
                            ThemedFrame, ThemedLabel, ThemedOptionMenu, toast)
from app.theme_manager import theme_manager
from core import validation
from database import db, repositories as repo

KINDS = ["strength", "cardio", "walk", "mobility", "stretch", "recovery"]
KIND_LABEL = {"strength": "Strength", "cardio": "Cardio", "walk": "Walking",
              "mobility": "Mobility", "stretch": "Stretching", "recovery": "Rest / Recovery"}


class PhysicalPerformanceScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(fg_color="transparent")

        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=20, pady=(18, 4))
        SectionTitle(head, text="PHYSICAL PERFORMANCE ARENA").pack(anchor="w")
        ThemedLabel(head, text="Train smart. Recover harder than you train. "
                    "Never push through sharp pain.", level="secondary", size=12)\
            .pack(anchor="w")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(2, 12))

        # ---- log workout card ------------------------------------------------
        log_card = ThemedFrame(body, role="card")
        log_card.pack(fill="x", pady=4)
        ThemedLabel(log_card, text="LOG A SESSION", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 4))
        g = ctk.CTkFrame(log_card, fg_color="transparent")
        g.pack(padx=14, pady=(0, 12), anchor="w")
        ex_e = ThemedEntry(g, placeholder="Exercise (e.g. Push-ups, 5km run)", width=250)
        kind_m = ThemedOptionMenu(g, KINDS, width=130)
        dur_e = ThemedEntry(g, width=70); dur_e.insert(0, "30")
        sets_e = ThemedEntry(g, width=60); sets_e.insert(0, "0")
        reps_e = ThemedEntry(g, width=60); reps_e.insert(0, "0")
        dist_e = ThemedEntry(g, width=70); dist_e.insert(0, "0")
        for col, w in enumerate([ex_e, kind_m, dur_e, sets_e, reps_e, dist_e]):
            w.grid(row=1, column=col, padx=(0, 8), pady=2)
        for col, t in enumerate(["Exercise", "Type", "Minutes", "Sets", "Reps", "Km"]):
            ThemedLabel(g, text=t, level="muted", size=10).grid(row=0, column=col, sticky="w")
        ActionButton(g, text="Log Session", width=120, command=self._log_workout)\
            .grid(row=1, column=6)
        self.ex_e, self.kind_m = ex_e, kind_m
        self.dur_e, self.sets_e, self.reps_e, self.dist_e = dur_e, sets_e, reps_e, dist_e

        # ---- middle row: hydration | weekly chart -----------------------------
        mid = ctk.CTkFrame(body, fg_color="transparent")
        mid.pack(fill="x", pady=6)
        hyd_card = ThemedFrame(mid, role="card")
        hyd_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ThemedLabel(hyd_card, text="HYDRATION TRACKER", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.hyd_lbl = ThemedLabel(hyd_card, text="0 / 2000 ml", level="primary",
                                   size=22, bold=True)
        self.hyd_lbl.pack(anchor="w", padx=14)
        self.hyd_bar = ProgressBar(hyd_card, height=8)
        self.hyd_bar.pack(fill="x", padx=14, pady=(6, 8))
        hbtns = ctk.CTkFrame(hyd_card, fg_color="transparent")
        hbtns.pack(padx=14, pady=(0, 12), anchor="w")
        for amt in (200, 330, 500):
            ActionButton(hbtns, text=f"+{amt}ml", kind="secondary", width=80, height=30,
                         command=lambda a=amt: self._add_water(a)).pack(side="left", padx=3)
        ActionButton(hbtns, text="Reset", kind="ghost", width=60, height=30,
                     command=self._reset_water).pack(side="left", padx=3)

        chart_card = ThemedFrame(mid, role="card")
        chart_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.week_chart = ChartFrame(chart_card, self._draw_week_chart, figsize=(4.2, 2.6))
        self.week_chart.pack(fill="both", expand=True, padx=4, pady=4)

        # ---- goals + records ---------------------------------------------------
        low = ctk.CTkFrame(body, fg_color="transparent")
        low.pack(fill="x", pady=6)
        goal_card = ThemedFrame(low, role="card")
        goal_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ThemedLabel(goal_card, text="PERSONAL FITNESS GOALS", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.goal_t = ctk.CTkTextbox(goal_card, height=64, wrap="word", corner_radius=8)
        self.goal_t.pack(fill="x", padx=14, pady=(0, 4))
        ActionButton(goal_card, text="Save Goals", kind="secondary", width=110, height=28,
                     command=self._save_goals).pack(anchor="w", padx=14, pady=(0, 10))

        rec_card = ThemedFrame(low, role="card")
        rec_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ThemedLabel(rec_card, text="PERSONAL RECORDS", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.rec_holder = ctk.CTkFrame(rec_card, fg_color="transparent")
        self.rec_holder.pack(fill="x", padx=14, pady=(0, 10))

        # ---- history --------------------------------------------------------------
        hist_card = ThemedFrame(body, role="card")
        hist_card.pack(fill="both", expand=True, pady=6)
        ThemedLabel(hist_card, text="WORKOUT HISTORY", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 4))
        self.hist_holder = ctk.CTkScrollableFrame(hist_card, fg_color="transparent",
                                                  height=170)
        self.hist_holder.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    # ------------------------------------------------------------------ actions --
    def _log_workout(self):
        try:
            ex = validation.require_text(self.ex_e.get(), "Exercise", 80)
            mins = validation.parse_int(self.dur_e.get(), "Minutes", 0, 600)
            sets = validation.parse_int(self.sets_e.get(), "Sets", 0, 999, default=0)
            reps = validation.parse_int(self.reps_e.get(), "Reps", 0, 9999, default=0)
            dist = validation.parse_float(self.dist_e.get(), "Distance", 0, 500, default=0)
            kind = self.kind_m.get()
            pid = self.app.current_profile_id
            before = repo.XP.total(pid)
            repo.Workouts.log(pid, ex, kind, mins, sets, reps, "", dist)
            gained = repo.XP.total(pid) - before
            toast(self.app, f"Session logged (+{gained} XP).", "success")
            self.ex_e.delete(0, "end")
            self.app.after_activity(pid)
            self.refresh()
        except ValueError as e:
            toast(self.app, str(e), "error")

    def _add_water(self, ml):
        pid = self.app.current_profile_id
        try:
            total = repo.Hydration.add(pid, date.today().isoformat(), ml)
            goal = int(db.get_setting("daily_water_goal_ml", "2000"))
            if total >= goal:
                toast(self.app, "Daily water goal reached. Stay healthy.", "success")
            self.app.after_activity(pid)
            self.refresh()
        except ValueError as e:
            toast(self.app, str(e), "error")

    def _reset_water(self):
        repo.Hydration.set_amount(self.app.current_profile_id,
                                  date.today().isoformat(), 0)
        self.refresh()

    def _save_goals(self):
        prof = repo.Profiles.get(self.app.current_profile_id)
        repo.Profiles.update(prof["id"], goals=self.goal_t.get("1.0", "end").strip())
        toast(self.app, "Fitness goals saved.", "success")

    # -------------------------------------------------------------------- draw --
    def _draw_week_chart(self, fig, p):
        pid = self.app.current_profile_id
        ax = fig.add_subplot(111)
        days = [(date.today() - timedelta(days=i)) for i in range(6, -1, -1)]
        vals = []
        for d in days:
            iso = d.isoformat()
            rows = db.query("SELECT COALESCE(SUM(duration_minutes),0) m FROM workout_sessions"
                            " WHERE profile_id=? AND session_date=?", (pid, iso))
            vals.append(rows[0]["m"])
        ax.bar([d.strftime("%a") for d in days], vals, color=p.SUCCESS, width=0.6)
        style_axes(ax, p, title="Weekly Activity (minutes)", ylabel="min")
        ax.set_ylim(bottom=0)

    def refresh(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        today = date.today().isoformat()
        total = repo.Hydration.get(pid, today)
        goal = int(db.get_setting("daily_water_goal_ml", "2000"))
        self.hyd_lbl.configure(text=f"{total} / {goal} ml")
        self.hyd_bar.set(total / goal if goal else 0, color=theme_manager.palette.INFO)
        prof = repo.Profiles.get(pid)
        self.goal_t.delete("1.0", "end")
        self.goal_t.insert("1.0", prof["goals"] or "")

        for w in self.rec_holder.winfo_children():
            w.destroy()
        p = theme_manager.palette
        recs = repo.Workouts.personal_records(pid)
        if not recs:
            ThemedLabel(self.rec_holder, text="No records yet.", level="muted",
                        size=12).pack()
        for r in recs:
            txt = f"{KIND_LABEL.get(r['kind'], r['kind'])}: {r['best_minutes']} min max"
            if r["best_km"]:
                txt += f" · {r['best_km']:.1f} km best"
            ThemedLabel(self.rec_holder, text=txt, level="primary", size=12)\
                .pack(anchor="w", pady=1)

        for w in self.hist_holder.winfo_children():
            w.destroy()
        hist = repo.Workouts.history(pid, limit=30)
        if not hist:
            ThemedLabel(self.hist_holder, text="No sessions logged yet.", level="muted",
                        size=12).pack(pady=8)
        for r in hist:
            extra = ""
            if r["sets"] and r["reps"]:
                extra = f" · {r['sets']}x{r['reps']}"
            if r["distance_km"]:
                extra += f" · {r['distance_km']:.1f}km"
            lvl = "success" if r["kind"] != "recovery" else "info"
            txt = (f"{r['session_date']} · {r['exercise']} ({KIND_LABEL.get(r['kind'], r['kind'])})"
                   f" · {r['duration_minutes']}min{extra} · +{r['xp_awarded']} XP")
            ThemedLabel(self.hist_holder, text=txt, level=lvl, size=12)\
                .pack(anchor="w", padx=6, pady=1)
        self.week_chart.redraw()
