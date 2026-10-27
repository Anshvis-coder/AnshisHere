"""Command Center dashboard — everything at a glance for the active profile."""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from app.charts import ChartFrame, style_axes
from app.components import (ActionButton, ProgressBar, SectionTitle, StatCard, ThemedFrame,
                            ThemedLabel, ToggleSwitch, XPBar, toast)
from app.theme_manager import theme_manager
from core import habit_engine, scoring_engine, streak_engine
from database import db, repositories as repo


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(fg_color="transparent")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=6, pady=6)

        # ---- header -------------------------------------------------------
        head = ThemedFrame(self.scroll, role="bg", border=False)
        head.pack(fill="x", padx=12, pady=(4, 10))
        self.welcome = SectionTitle(head, text="Welcome")
        self.welcome.pack(anchor="w")
        self.date_lbl = ThemedLabel(head, text="", level="secondary", size=13)
        self.date_lbl.pack(anchor="w", pady=(2, 0))
        topbtns = ctk.CTkFrame(head, fg_color="transparent")
        topbtns.pack(anchor="e", pady=(4, 0))
        ActionButton(topbtns, text="+ Quick Habit", kind="secondary", width=130,
                     command=self._quick_add_habit).pack(side="left", padx=4)
        ActionButton(topbtns, text="⏱ Focus Timer", width=130,
                     command=lambda: app.navigate("mental")).pack(side="left", padx=4)

        # ---- stat cards ---------------------------------------------------
        row1 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row1.pack(fill="x", padx=6, pady=4)
        self.cards = {}
        for key, caption, accent in (("completion", "Daily Completion", "accent"),
                                     ("xp_today", "XP Today", "accent"),
                                     ("streak", "Current Streak", "warning"),
                                     ("mental", "Mental Score", "info"),
                                     ("physical", "Physical Score", "success"),
                                     ("discipline", "Discipline Score", "accent")):
            card = StatCard(row1, caption, value="--", accent_role=accent)
            card.pack(side="left", expand=True, fill="x", padx=5)
            self.cards[key] = card

        # ---- rank + motivation -------------------------------------------
        row2 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row2.pack(fill="x", padx=6, pady=6)
        xp_card = ThemedFrame(row2, role="card")
        xp_card.pack(side="left", fill="x", expand=True, padx=5)
        ThemedLabel(xp_card, text="RANK PROGRESSION", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 0))
        self.xp_bar = XPBar(xp_card)
        self.xp_bar.pack(fill="x", padx=10, pady=(2, 8))
        mot_card = ThemedFrame(row2, role="accent_soft")
        mot_card.pack(side="left", fill="x", padx=5)
        ThemedLabel(mot_card, text="TODAY'S ORDERS", level="accent", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 0))
        self.mot_lbl = ThemedLabel(mot_card, text="", level="primary", size=13,
                                   wraplength=260, justify="left")
        self.mot_lbl.pack(anchor="w", padx=14, pady=(2, 12))

        # ---- middle: checklist | chart ------------------------------------
        row3 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row3.pack(fill="both", expand=True, padx=6, pady=6)
        mission_card = ThemedFrame(row3, role="card")
        mission_card.pack(side="left", fill="both", expand=True, padx=5)
        mh = ctk.CTkFrame(mission_card, fg_color="transparent")
        mh.pack(fill="x", padx=14, pady=(10, 2))
        ThemedLabel(mh, text="TODAY'S MISSION CHECKLIST", level="secondary", size=11,
                    bold=True).pack(side="left")
        ActionButton(mh, text="Mission Room ▸", kind="ghost", width=120, height=26,
                     command=lambda: app.navigate("missions")).pack(side="right")
        self.progress = ProgressBar(mission_card, height=6)
        self.progress.pack(fill="x", padx=14, pady=(2, 6))
        self.checklist = ctk.CTkScrollableFrame(mission_card, fg_color="transparent",
                                                height=220)
        self.checklist.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        right = ctk.CTkFrame(row3, fg_color="transparent", width=340)
        right.pack(side="left", fill="both", padx=5)
        right.pack_propagate(False)
        chart_card = ThemedFrame(right, role="card")
        chart_card.pack(fill="x")
        self.week_chart = ChartFrame(chart_card, self._draw_week_chart, figsize=(3.3, 2.4))
        self.week_chart.pack(fill="x")

        lb_card = ThemedFrame(right, role="card")
        lb_card.pack(fill="both", expand=True, pady=(8, 0))
        ThemedLabel(lb_card, text="LEADERBOARD · ARENA RANKING", level="secondary",
                    size=11, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.leaderboard = ctk.CTkFrame(lb_card, fg_color="transparent")
        self.leaderboard.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # ---- bottom: challenge + achievements ------------------------------
        row4 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row4.pack(fill="x", padx=6, pady=(4, 10))
        chal_card = ThemedFrame(row4, role="card")
        chal_card.pack(side="left", fill="x", expand=True, padx=5)
        ThemedLabel(chal_card, text="UPCOMING / ACTIVE CHALLENGE", level="secondary",
                    size=11, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
        self.chal_title = ThemedLabel(chal_card, text="—", level="primary", size=15, bold=True)
        self.chal_title.pack(anchor="w", padx=14)
        self.chal_desc = ThemedLabel(chal_card, text="", level="secondary", size=12,
                                     wraplength=420, justify="left")
        self.chal_desc.pack(anchor="w", padx=14, pady=(2, 4))
        self.chal_bar = ProgressBar(chal_card, height=6)
        self.chal_bar.pack(fill="x", padx=14, pady=(2, 4))
        self.chal_meta = ThemedLabel(chal_card, text="", level="muted", size=11)
        self.chal_meta.pack(anchor="w", padx=14, pady=(0, 10))

        ach_card = ThemedFrame(row4, role="card")
        ach_card.pack(side="left", fill="x", expand=True, padx=5)
        ThemedLabel(ach_card, text="RECENT ACHIEVEMENTS", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(10, 4))
        self.ach_holder = ctk.CTkFrame(ach_card, fg_color="transparent")
        self.ach_holder.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    # ------------------------------------------------------------------ draw --
    def _draw_week_chart(self, fig, p):
        pid = self.app.current_profile_id
        ax = fig.add_subplot(111)
        days = [(date.today() - timedelta(days=i)) for i in range(6, -1, -1)]
        vals = [max(0, repo.XP.on_day(pid, d.isoformat())) for d in days]
        ax.bar([d.strftime("%a") for d in days], vals, color=p.ACCENT, width=0.6)
        style_axes(ax, p, title="Weekly XP", ylabel="XP")
        ax.set_ylim(bottom=0)

    # ---------------------------------------------------------------- refresh --
    def refresh(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        prof = repo.Profiles.get(pid)
        today = date.today()
        self.welcome.configure(text=f"WELCOME BACK, {prof['name'].upper()}")
        self.date_lbl.configure(text=today.strftime("%A · %d %B %Y"))
        from app.notifications import daily_motivation
        self.mot_lbl.configure(text=daily_motivation(pid))

        rate = scoring_engine.daily_completion_rate(pid)
        self.cards["completion"].set_value(f"{round(rate * 100)}%")
        self.progress.set(rate)
        self.cards["xp_today"].set_value(str(max(0, repo.XP.on_day(pid, today.isoformat()))))
        st = streak_engine.refresh(pid)
        self.cards["streak"].set_value(f"{st['current']} 🔥")
        sc = scoring_engine.scores(pid)
        self.cards["mental"].set_value(str(sc["mental"]))
        self.cards["physical"].set_value(str(sc["physical"]))
        self.cards["discipline"].set_value(str(sc["discipline"]))

        rp = scoring_engine.rank_progress(pid)
        self.xp_bar.update_rank(rp["rank"], rp["total_xp"], rp["into_rank"],
                                rp["needed_for_next"])

        self._rebuild_checklist(pid, today)
        self._rebuild_leaderboard()
        self._rebuild_challenge()
        self._rebuild_achievements(pid)
        self.week_chart.redraw()

    def _rebuild_checklist(self, pid, today):
        for w in self.checklist.winfo_children():
            w.destroy()
        items = []
        for entry in habit_engine.todays_checklist(pid, today):
            h = entry["habit"]
            items.append(("habit", h["id"], h["name"], h["category"], h["xp_reward"],
                          entry["done"], entry["partial"]))
        for m in repo.Missions.for_date(pid, today.isoformat()):
            if m["status"] in ("pending", "done"):
                items.append(("mission", m["id"], m["title"], m["category"],
                              m["xp_reward"], m["status"] == "done", False))
        if not items:
            ThemedLabel(self.checklist, text="Nothing scheduled — add habits or missions.",
                        level="muted", size=12).pack(pady=16)
        for kind, oid, name, cat, xp, done, partial in items[:14]:
            row = ctk.CTkFrame(self.checklist, fg_color="transparent")
            row.pack(fill="x", pady=1)
            cb = ctk.CTkCheckBox(row, text=f"{name}  ·  {cat}  ·  {xp} XP"
                                 + (" (partial)" if partial else ""),
                                 font=ctk.CTkFont(size=13),
                                 fg_color=theme_manager.palette.ACCENT,
                                 hover_color=theme_manager.palette.ACCENT_HOVER,
                                 checkmark_color="#FFFFFF",
                                 text_color=theme_manager.palette.TEXT_PRIMARY,
                                 checkbox_color=theme_manager.palette.ACCENT)
            cb.select() if done else cb.deselect()
            cb.configure(command=lambda k=kind, i=oid, b=cb: self._toggle(k, i, b))
            cb.pack(side="left", padx=8, pady=3)

    def _toggle(self, kind, oid, checkbox):
        pid = self.app.current_profile_id
        iso = date.today().isoformat()
        try:
            if kind == "habit":
                if checkbox.instate(["selected"]):
                    res = repo.Completions.complete(pid, oid, iso)
                    if res["status"] == "ok" and res["xp_awarded"]:
                        toast(self.app, f"+{res['xp_awarded']} XP", "success")
                else:
                    removed = repo.Completions.undo(pid, oid, iso)
                    if removed:
                        toast(self.app, f"-{removed} XP (undone)", "warn")
            else:
                m = repo.Missions.get(oid)
                if checkbox.instate(["selected"]):
                    xp = repo.Missions.complete(oid)
                    if xp:
                        toast(self.app, f"+{xp} XP", "success")
                else:
                    repo.Missions.undo(oid)
            self.app.after_activity(pid)
            self.refresh()
        except ValueError as e:
            toast(self.app, str(e), "error")

    def _rebuild_leaderboard(self):
        for w in self.leaderboard.winfo_children():
            w.destroy()
        profiles = [p for p in repo.Profiles.all() if p["is_active"]]
        ranked = sorted(profiles, key=lambda p: repo.XP.total(p["id"]), reverse=True)
        p = theme_manager.palette
        for i, prof in enumerate(ranked):
            row = ctk.CTkFrame(self.leaderboard, fg_color=p.CARD_HOVER, corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"#{i + 1}", width=34, text_color=p.TEXT_MUTED,
                         font=ctk.CTkFont(size=14, bold=True)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=prof["name"], text_color=p.TEXT_PRIMARY,
                         font=ctk.CTkFont(size=14, bold=True)).pack(side="left")
            rp = scoring_engine.rank_progress(prof["id"])
            ctk.CTkLabel(row, text=f"{rp['rank']} · {rp['total_xp']} XP",
                         text_color=p.TEXT_SECONDARY).pack(side="right", padx=10)

    def _rebuild_challenge(self):
        active = repo.Challenges.active()
        if active:
            ch = active[0]
            self.chal_title.configure(text=f"{ch['title']}  ({ch['mode']})")
            self.chal_desc.configure(text=ch["description"])
            frac = min(1.0, (ch["progress_value"] or 0) / max(ch["target_value"], 1e-9))
            self.chal_bar.set(frac)
            self.chal_meta.configure(
                text=f"Deadline {ch['deadline']} · reward {ch['xp_reward']} XP · "
                     f"progress {ch['progress_value']:g}/{ch['target_value']:g}")
        else:
            self.chal_title.configure(text="No active challenge")
            self.chal_desc.configure(text="Visit the Mission Room to generate this week's challenge.")
            self.chal_bar.set(0)
            self.chal_meta.configure(text="")

    def _rebuild_achievements(self, pid):
        for w in self.ach_holder.winfo_children():
            w.destroy()
        rows = repo.Achievements.recent(pid, limit=4)
        p = theme_manager.palette
        if not rows:
            ThemedLabel(self.ach_holder, text="No achievements yet — earn your first one today.",
                        level="muted", size=12).pack(pady=10)
        for r in rows:
            row = ctk.CTkFrame(self.ach_holder, fg_color=p.ACCENT_SOFT, corner_radius=8)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=r["icon"], text_color=p.ACCENT, width=26,
                         font=ctk.CTkFont(size=15, bold=True)).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=r["title"], text_color=p.TEXT_PRIMARY,
                         font=ctk.CTkFont(size=13, bold=True)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=r["unlocked_at"][:10], text_color=p.TEXT_MUTED,
                         font=ctk.CTkFont(size=11)).pack(side="right", padx=8)

    # ------------------------------------------------------------ quick add --
    def _quick_add_habit(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Quick Add Habit")
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()
        frame = ThemedFrame(dlg, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        ThemedLabel(frame, text="Habit name", level="secondary", size=12).pack(
            anchor="w", pady=(12, 2), padx=16)
        name_e = ThemedEntry(frame, placeholder="e.g. Read 20 pages", width=280)
        name_e.pack(padx=16, anchor="w")
        ThemedLabel(frame, text="Category", level="secondary", size=12).pack(
            anchor="w", pady=(10, 2), padx=16)
        cat_m = ThemedOptionMenuCat(frame)
        cat_m.pack(padx=16, anchor="w")
        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(pady=14)

        def save():
            try:
                from core import validation
                nm = validation.require_text(name_e.get(), "Habit name", 60)
                repo.Habits.create(self.app.current_profile_id, nm, cat_m.get(),
                                   xp_reward=_DEFAULT_XP[cat_m.get()])
                toast(self.app, "Habit added — full details in Habit Manager.", "success")
                dlg.destroy()
                self.app.after_activity(self.app.current_profile_id)
                self.refresh()
            except ValueError as e:
                toast(self.app, str(e), "error")

        ActionButton(btns, text="Add", command=save).grid(row=0, column=0, padx=5)
        ActionButton(btns, text="Cancel", kind="secondary", command=dlg.destroy)\
            .grid(row=0, column=1, padx=5)
        name_e.focus_force()


_DEFAULT_XP = {"Mental": 15, "Physical": 20, "Discipline": 12}


def ThemedOptionMenuCat(master):
    from app.components import ThemedOptionMenu
    return ThemedOptionMenu(master, values=list(_DEFAULT_XP.keys()), width=200)
