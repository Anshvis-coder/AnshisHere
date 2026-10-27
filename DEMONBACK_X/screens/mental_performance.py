"""Mental Performance Arena — focus timer, Pomodoro, sessions, reading, PBs.

Scores here describe tracked activity only; they are not medical measures.
"""
from __future__ import annotations

import json
import time
from datetime import date

import customtkinter as ctk

from app.components import (ActionButton, SectionTitle, ThemedEntry, ThemedFrame,
                            ThemedLabel, ThemedOptionMenu, toast)
from app.notifications import play_beep
from app.theme_manager import theme_manager
from core import validation
from database import db, repositories as repo


class MentalPerformanceScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(fg_color="transparent")

        # timer state -------------------------------------------------------
        self.running = False
        self.paused = True
        self.end_ts: float | None = None      # unix ts when session ends
        self.remaining: int = 0               # seconds left while paused
        self.planned_min: int = 25
        self._tick_job = None
        self._start_iso: str | None = None

        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=20, pady=(18, 6))
        SectionTitle(head, text="MENTAL PERFORMANCE ARENA").pack(anchor="w")
        ThemedLabel(head, text="Focus is a muscle. Train it daily.", level="secondary",
                    size=12).pack(anchor="w")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        # ---- left: timer ---------------------------------------------------
        left = ThemedFrame(body, role="card")
        left.pack(side="left", fill="y", padx=(0, 8))
        inner = ctk.CTkFrame(left, fg_color="transparent")
        inner.pack(padx=24, pady=20)
        ThemedLabel(inner, text="FOCUS TIMER", level="secondary", size=11, bold=True)\
            .pack()
        self.time_lbl = ThemedLabel(inner, text="25:00", level="accent", size=64, bold=True)
        self.time_lbl.pack(pady=10)
        self.mode_lbl = ThemedLabel(inner, text="Idle", level="muted", size=12)
        self.mode_lbl.pack()

        row = ctk.CTkFrame(inner, fg_color="transparent"); row.pack(pady=(14, 4))
        ThemedLabel(row, text="Duration:", level="secondary", size=12).pack(side="left")
        self.dur_m = ThemedOptionMenu(row, ["15", "25", "30", "45", "60", "90"],
                                      width=90, command=self._set_duration)
        self.dur_m.set("25"); self.dur_m.pack(side="left", padx=6)
        kind_row = ctk.CTkFrame(inner, fg_color="transparent"); kind_row.pack(pady=4)
        ThemedLabel(kind_row, text="Type:", level="secondary", size=12).pack(side="left")
        self.kind_m = ThemedOptionMenu(kind_row, ["focus", "pomodoro", "study", "reading"],
                                       width=130)
        self.kind_m.set("focus"); self.kind_m.pack(side="left", padx=6)
        lbl_e = ThemedEntry(inner, placeholder="Session label (e.g. Maths chapter 4)",
                            width=280)
        lbl_e.pack(pady=6)
        self.label_entry = lbl_e

        btns = ctk.CTkFrame(inner, fg_color="transparent"); btns.pack(pady=10)
        self.start_btn = ActionButton(btns, text="▶ Start", width=100, command=self._start)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.pause_btn = ActionButton(btns, text="⏸ Pause", kind="secondary", width=100,
                                      command=self._pause, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=4)
        self.reset_btn = ActionButton(btns, text="⟲ Reset", kind="ghost", width=90,
                                      command=self._reset)
        self.reset_btn.grid(row=0, column=2, padx=4)
        self.stop_btn = ActionButton(btns, text="■ Stop", kind="danger", width=90,
                                     command=self._stop_early, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=4)

        pb_card = ThemedFrame(left, role="elevated")
        pb_card.pack(fill="x", padx=18, pady=(6, 16))
        ThemedLabel(pb_card, text="PERSONAL BESTS", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=12, pady=(8, 2))
        self.pb_lbl = ThemedLabel(pb_card, text="—", level="primary", size=12)
        self.pb_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # ---- right: log + history ------------------------------------------
        right = ctk.CTkScrollableFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        log_card = ThemedFrame(right, role="card")
        log_card.pack(fill="x")
        ThemedLabel(log_card, text="LOG PAST SESSION / READING", level="secondary",
                    size=11, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        lg = ctk.CTkFrame(log_card, fg_color="transparent"); lg.pack(padx=14, anchor="w",
                                                                    pady=(0, 10))
        self.log_min = ThemedEntry(lg, width=70); self.log_min.insert(0, "30")
        self.log_min.grid(row=1, column=0, padx=(0, 8))
        self.log_kind = ThemedOptionMenu(lg, ["focus", "pomodoro", "study", "reading"],
                                         width=110)
        self.log_kind.grid(row=1, column=1, padx=(0, 8))
        self.log_label = ThemedEntry(lg, placeholder="label", width=170)
        self.log_label.grid(row=1, column=2, padx=(0, 8))
        ActionButton(lg, text="Log", width=80, command=self._log_manual)\
            .grid(row=1, column=3)
        ThemedLabel(lg, text="Minutes", level="muted", size=10).grid(row=0, column=0, sticky="w")
        ThemedLabel(lg, text="Type", level="muted", size=10).grid(row=0, column=1, sticky="w")
        ThemedLabel(lg, text="Description", level="muted", size=10).grid(row=0, column=2, sticky="w")

        goals_card = ThemedFrame(right, role="card")
        goals_card.pack(fill="x", pady=(8, 0))
        ThemedLabel(goals_card, text="LEARNING GOALS", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.goals_t = ctk.CTkTextbox(goals_card, height=70, wrap="word",
                                      corner_radius=8)
        self.goals_t.pack(fill="x", padx=14, pady=(0, 6))
        row_g = ctk.CTkFrame(goals_card, fg_color="transparent")
        row_g.pack(padx=14, pady=(0, 10), anchor="w")
        ActionButton(row_g, text="Save Goals", kind="secondary", width=110, height=28,
                     command=self._save_goals).pack(side="left")
        ActionButton(row_g, text="Distraction note", kind="ghost", width=140, height=28,
                     command=self._distraction_note).pack(side="left", padx=6)

        hist_card = ThemedFrame(right, role="card")
        hist_card.pack(fill="both", expand=True, pady=(8, 0))
        ThemedLabel(hist_card, text="FOCUS SESSION HISTORY", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 4))
        self.hist_holder = ctk.CTkScrollableFrame(hist_card, fg_color="transparent",
                                                  height=180)
        self.hist_holder.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        self._restore_timer_state()
        self.refresh()

    # ------------------------------------------------------------ timer ops --
    def _set_duration(self, val):
        self.planned_min = int(val)
        if not self.running:
            self.remaining = self.planned_min * 60
            self._render_time(self.remaining)

    def _render_time(self, secs):
        m, s = divmod(max(0, int(secs)), 60)
        self.time_lbl.configure(text=f"{m:02d}:{s:02d}")

    def _start(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        if self.running and not self.paused:
            return
        if self.paused and self.end_ts is None and self.remaining <= 0:
            self.remaining = self.planned_min * 60
        if self.end_ts is None:
            if self.remaining <= 0:
                self.remaining = self.planned_min * 60
            self.end_ts = time.time() + self.remaining
        else:
            # resuming from pause: end_ts was kept
            pass
        self.running, self.paused = True, False
        self._start_iso = self._start_iso or time.strftime("%Y-%m-%dT%H:%M:%S")
        self.mode_lbl.configure(text=f"Locked in · {self.kind_m.get().upper()}")
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self._persist_state()
        self._tick()

    def _tick(self):
        if not self.running or self.paused or not self.winfo_exists():
            return
        left = self.end_ts - time.time()
        self.remaining = max(0, left)
        self._render_time(left)
        if left <= 0:
            self._complete()
            return
        self._tick_job = self.after(500, self._tick)

    def _pause(self):
        if not self.running:
            return
        self.paused = True
        self.remaining = max(0, self.end_ts - time.time())
        self.mode_lbl.configure(text="Paused — the arena waits.")
        self.start_btn.configure(state="normal", text="▶ Resume")
        self.pause_btn.configure(state="disabled")
        self._persist_state()

    def _reset(self):
        self._cancel_tick()
        self.running, self.paused = False, True
        self.end_ts = None
        self._start_iso = None
        self.remaining = self.planned_min * 60
        self._render_time(self.remaining)
        self.mode_lbl.configure(text="Idle")
        self.start_btn.configure(state="normal", text="▶ Start")
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self._clear_persisted()

    def _stop_early(self):
        """User aborts: record interrupted partial session, no completion XP."""
        if not self.running:
            return
        elapsed_min = self.planned_min - int(self.remaining // 60)
        self._cancel_tick()
        if elapsed_min >= 1:
            repo.FocusSessions.log(self.app.current_profile_id, self.planned_min,
                                   elapsed_min, self.kind_m.get(),
                                   self.label_entry.get().strip(), completed=False)
            toast(self.app, f"Session stopped early ({elapsed_min} min logged, "
                            "no XP for incomplete run).", "warn")
        else:
            toast(self.app, "Session discarded (<1 minute).", "warn")
        self._reset_after_stop()
        self.app.after_activity(self.app.current_profile_id)
        self.refresh()

    def _complete(self):
        self._cancel_tick()
        pid = self.app.current_profile_id
        xp_before = repo.XP.total(pid)
        repo.FocusSessions.log(pid, self.planned_min, self.planned_min,
                               self.kind_m.get(), self.label_entry.get().strip(),
                               completed=True)
        gained = repo.XP.total(pid) - xp_before
        play_beep("success")
        toast(self.app, f"Session complete! +{gained} XP", "success")
        self.label_entry.delete(0, "end")
        self._reset_after_stop()
        self.app.after_activity(pid)
        self.refresh()

    def _reset_after_stop(self):
        self.running, self.paused = False, True
        self.end_ts = None
        self._start_iso = None
        self.remaining = self.planned_min * 60
        self._render_time(self.remaining)
        self.mode_lbl.configure(text="Idle")
        self.start_btn.configure(state="normal", text="▶ Start")
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self._clear_persisted()

    def _cancel_tick(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

    # ----- persistence across restarts (safe handling of window switching) --
    def _timer_key(self):
        return f"active_timer_{self.app.current_profile_id}"

    def _persist_state(self):
        state = {"end_ts": self.end_ts, "remaining": self.remaining,
                 "paused": self.paused, "planned": self.planned_min,
                 "kind": self.kind_m.get(), "label": self.label_entry.get(),
                 "saved_at": time.time()}
        db.set_setting(self._timer_key(), json.dumps(state))

    def _clear_persisted(self):
        db.set_setting(self._timer_key(), "")

    def _restore_timer_state(self):
        raw = db.get_setting(self._timer_key(), "")
        if not raw:
            self.remaining = self.planned_min * 60
            self._render_time(self.remaining)
            return
        try:
            st = json.loads(raw)
            planned = int(st.get("planned", 25))
            self.dur_m.set(str(planned)); self.planned_min = planned
            self.kind_m.set(st.get("kind", "focus"))
            self.label_entry.delete(0, "end")
            self.label_entry.insert(0, st.get("label", ""))
            if st.get("paused"):
                self.remaining = float(st.get("remaining", 0))
                self.paused = True
                self.mode_lbl.configure(text="Paused — resume when ready.")
                self.start_btn.configure(state="normal", text="▶ Resume")
                self._render_time(self.remaining)
            else:
                left = float(st.get("end_ts", 0)) - time.time()
                if left > 0:
                    self.running = True
                    self.paused = False
                    self.end_ts = time.time() + left
                    self.mode_lbl.configure(text="Locked in (restored)")
                    self.start_btn.configure(state="disabled")
                    self.pause_btn.configure(state="normal")
                    self.stop_btn.configure(state="normal")
                    self._tick()
                else:
                    # finished while app was closed → award as completed
                    repo.FocusSessions.log(self.app.current_profile_id, planned, planned,
                                           st.get("kind", "focus"),
                                           st.get("label", ""), completed=True)
                    db.set_setting("pending_timer_complete", "1")
                    self._clear_persisted()
                    self.remaining = planned * 60
                    self._render_time(self.remaining)
        except (ValueError, KeyError):
            self._clear_persisted()
            self.remaining = self.planned_min * 60
            self._render_time(self.remaining)

    # ------------------------------------------------------------------ misc --
    def _log_manual(self):
        try:
            mins = validation.parse_int(self.log_min.get(), "Minutes", 1, 600)
            kind = self.log_kind.get()
            repo.FocusSessions.log(self.app.current_profile_id, mins, mins, kind,
                                   self.log_label.get().strip(), completed=True)
            toast(self.app, f"Logged {mins} min {kind}.", "success")
            self.log_label.delete(0, "end")
            self.app.after_activity(self.app.current_profile_id)
            self.refresh()
        except ValueError as e:
            toast(self.app, str(e), "error")

    def _save_goals(self):
        prof = repo.Profiles.get(self.app.current_profile_id)
        existing = prof["goals"] or ""
        new = self.goals_t.get("1.0", "end").strip()
        if existing and new and existing != new:
            new = existing + "\n" + new
        repo.Profiles.update(prof["id"], goals=new)
        self.goals_t.delete("1.0", "end")
        toast(self.app, "Learning goal saved.", "success")

    def _distraction_note(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Distraction Note"); dlg.transient(self.app); dlg.grab_set()
        frame = ThemedFrame(dlg, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        ThemedLabel(frame, text="What pulled your focus today? (stored with your journal)",
                    level="secondary", size=12).pack(padx=16, pady=(12, 4), anchor="w")
        t = ThemedTextbox(frame, width=340, height=90)
        t.pack(padx=16, anchor="w")
        iso = date.today().isoformat()
        cur = repo.Journal.get_entry(self.app.current_profile_id, iso)
        if cur:
            t.insert("1.0", cur["distractions"])

        def save():
            repo.Journal.save(self.app.current_profile_id, iso,
                              reflection=cur["reflection"] if cur else "",
                              mood=cur["mood"] if cur else 5,
                              distractions=t.get("1.0", "end").strip(),
                              wins=cur["wins"] if cur else "")
            toast(self.app, "Distraction note saved.", "success")
            dlg.destroy()
        btns = ctk.CTkFrame(frame, fg_color="transparent"); btns.pack(pady=12)
        ActionButton(btns, text="Save", command=save).grid(row=0, column=0, padx=4)
        ActionButton(btns, text="Cancel", kind="secondary", command=dlg.destroy)\
            .grid(row=0, column=1, padx=4)

    # ------------------------------------------------------------- refresh ---
    def refresh(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        rows = db.query("SELECT MAX(actual_minutes) best, SUM(actual_minutes) tot FROM "
                        "focus_sessions WHERE profile_id=? AND completed=1", (pid,))
        best = rows[0]["best"] or 0
        tot = rows[0]["tot"] or 0
        self.pb_lbl.configure(text=f"Longest session: {best} min · Total focus: {tot} min")
        prof = repo.Profiles.get(pid)
        self.goals_t.delete("1.0", "end")
        self.goals_t.insert("1.0", prof["goals"] or "")
        for w in self.hist_holder.winfo_children():
            w.destroy()
        hist = repo.FocusSessions.history(pid, limit=25)
        p = theme_manager.palette
        if not hist:
            ThemedLabel(self.hist_holder, text="No sessions yet.", level="muted",
                        size=12).pack(pady=8)
        for r in hist:
            status = "✓" if r["completed"] else "✗ interrupted"
            lvl = "success" if r["completed"] else "warning"
            txt = (f"{r['session_date']} · {r['actual_minutes']}min · {r['kind']} · "
                   f"{r['label'] or '—'} · {status} · +{r['xp_awarded']} XP")
            ThemedLabel(self.hist_holder, text=txt, level=lvl, size=12)\
                .pack(anchor="w", padx=6, pady=1)
