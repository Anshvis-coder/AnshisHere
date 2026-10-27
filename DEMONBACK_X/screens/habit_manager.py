"""Habit Manager — create/edit/archive habits, calendar view, history."""
from __future__ import annotations

import calendar
from datetime import date

import customtkinter as ctk

from app.components import (ActionButton, SectionTitle, ThemedEntry, ThemedFrame,
                            ThemedLabel, ThemedOptionMenu, ThemedTextbox, ToggleSwitch,
                            toast)
from app.theme_manager import theme_manager
from core import habit_engine, validation
from database import repositories as repo

CATEGORIES = ["Mental", "Physical", "Discipline"]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class HabitManagerScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(fg_color="transparent")
        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=20, pady=(18, 8))
        SectionTitle(head, text="HABIT MANAGER").pack(anchor="w")
        ActionButton(head, text="+ New Habit", width=140, command=self._edit_new)\
            .pack(anchor="e", pady=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        left = ctk.CTkScrollableFrame(body, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.list_holder = left

        right = ThemedFrame(body, role="card", width=320)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        ThemedLabel(right, text="MONTH CALENDAR", level="secondary", size=11,
                    bold=True).pack(anchor="w", padx=14, pady=(12, 2))
        nav = ctk.CTkFrame(right, fg_color="transparent")
        nav.pack(fill="x", padx=10)
        self.cal_month = date.today().replace(day=1)
        ActionButton(nav, text="◂", kind="ghost", width=40, height=28,
                     command=lambda: self._shift_month(-1)).pack(side="left")
        self.cal_lbl = ThemedLabel(nav, text="", level="primary", size=13, bold=True)
        self.cal_lbl.pack(side="left", expand=True)
        ActionButton(nav, text="▸", kind="ghost", width=40, height=28,
                     command=lambda: self._shift_month(1)).pack(side="right")
        self.cal_grid = ctk.CTkFrame(right, fg_color="transparent")
        self.cal_grid.pack(padx=10, pady=8)
        ThemedLabel(right, text="Legend: green=full · amber=partial · grey=none",
                    level="muted", size=10).pack(pady=(0, 10))

        self.refresh()

    # ------------------------------------------------------------------ list --
    def refresh(self):
        for w in self.list_holder.winfo_children():
            w.destroy()
        pid = self.app.current_profile_id
        if pid is None:
            return
        habits = repo.Habits.all_for_profile(pid)
        if not habits:
            ThemedLabel(self.list_holder,
                        text="No habits yet. Create your first habit to start building streaks.",
                        level="muted", size=13).pack(pady=30)
        for h in habits:
            self._habit_row(h)
        self._draw_calendar()

    def _habit_row(self, h):
        p = theme_manager.palette
        card = ThemedFrame(self.list_holder, role="card")
        card.pack(fill="x", pady=4)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)
        name = ThemedLabel(row, text=h["name"], level="primary", size=15, bold=True)
        name.pack(side="left")
        tags = f"{h['category']} · {h['frequency']} · {h['xp_reward']} XP"
        if h["target_quantity"] > 0:
            tags += f" · target {h['target_quantity']:g}{(' ' + h['target_unit']) if h['target_unit'] else ''}"
        ThemedLabel(row, text=tags, level="secondary", size=12).pack(side="left", padx=12)
        if h["archived"]:
            ThemedLabel(row, text="ARCHIVED", level="warning", size=11, bold=True)\
                .pack(side="left", padx=6)
        st = habit_engine.habit_history_stats(h["profile_id"], h["id"], 30)
        ThemedLabel(row, text=f"{st['rate']:.0f}% (30d)", level="info", size=12)\
            .pack(side="right", padx=8)
        ActionButton(row, text="Edit", kind="secondary", width=70, height=28,
                     command=lambda: self._edit_existing(h["id"])).pack(side="right", padx=3)
        ActionButton(row, text="Archive" if not h["archived"] else "Restore",
                     kind="ghost", width=80, height=28,
                     command=lambda: self._archive(h["id"], not bool(h["archived"])))\
            .pack(side="right", padx=3)

    def _archive(self, hid, flag):
        repo.Habits.set_archived(hid, flag)
        toast(self.app, "Habit archived." if flag else "Habit restored.",
              "warn" if flag else "success")
        self.app.after_activity(self.app.current_profile_id)
        self.refresh()

    # --------------------------------------------------------------- editor --
    def _edit_new(self):
        self._editor(None)

    def _edit_existing(self, hid):
        self._editor(repo.Habits.get(hid))

    def _editor(self, habit):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Edit Habit" if habit else "New Habit")
        dlg.transient(self.app)
        dlg.grab_set()
        scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent", width=420, height=520)
        scroll.pack(fill="both", expand=True, padx=6, pady=6)
        frame = ThemedFrame(scroll, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        def lbl(t):
            ThemedLabel(frame, text=t, level="secondary", size=12).pack(anchor="w",
                                                                        pady=(10, 2), padx=14)

        name_e = None
        lbl("Name")
        name_e = ThemedEntry(frame, width=360)
        name_e.pack(padx=14, anchor="w")
        lbl("Description")
        desc_t = ThemedTextbox(frame, width=360, height=60)
        desc_t.pack(padx=14, anchor="w")
        lbl("Category")
        cat_m = ThemedOptionMenu(frame, CATEGORIES, width=160)
        cat_m.pack(padx=14, anchor="w")
        lbl("Frequency")
        freq_m = ThemedOptionMenu(frame, ["daily", "weekly"], width=160)
        freq_m.pack(padx=14, anchor="w")
        lbl("Weekdays active (click to toggle)")
        wrow = ctk.CTkFrame(frame, fg_color="transparent")
        wrow.pack(padx=14, anchor="w")
        wbtns = {}
        for i, dn in enumerate(DAY_NAMES):
            b = ctk.CTkButton(wrow, text=dn, width=40, height=28)
            b.grid(row=0, column=i, padx=2)
            wbtns[i] = {"on": True, "b": b}
            b.configure(command=lambda ii=i: _toggle_day(ii))

        def _toggle_day(ii):
            wbtns[ii]["on"] = not wbtns[ii]["on"]
            _paint_days()

        def _paint_days():
            p = theme_manager.palette
            for i, d in wbtns.items():
                d["b"].configure(fg_color=p.ACCENT if d["on"] else p.ELEVATED,
                                 text_color="#FFFFFF" if d["on"] else p.TEXT_MUTED)
        _paint_days()

        grid2 = ctk.CTkFrame(frame, fg_color="transparent")
        grid2.pack(padx=14, pady=(10, 0), anchor="w")
        ThemedLabel(grid2, text="Target count", level="secondary", size=12).grid(row=0, column=0, padx=(0, 12))
        ThemedLabel(grid2, text="XP reward", level="secondary", size=12).grid(row=0, column=1, padx=(0, 12))
        ThemedLabel(grid2, text="Quantity target", level="secondary", size=12).grid(row=0, column=2, padx=(0, 12))
        ThemedLabel(grid2, text="Unit", level="secondary", size=12).grid(row=0, column=3)
        tc_e = ThemedEntry(grid2, width=70); tc_e.grid(row=1, column=0, padx=(0, 12)); tc_e.insert(0, "1")
        xp_e = ThemedEntry(grid2, width=70); xp_e.grid(row=1, column=1, padx=(0, 12)); xp_e.insert(0, "15")
        tq_e = ThemedEntry(grid2, width=70); tq_e.grid(row=1, column=2, padx=(0, 12)); tq_e.insert(0, "0")
        tu_e = ThemedEntry(grid2, width=70); tu_e.grid(row=1, column=3); tu_e.insert(0, "min")
        partial_sw = ToggleSwitch(frame, text="Allow partial completion")
        partial_sw.pack(padx=14, anchor="w", pady=(10, 0))
        lbl("Start date (YYYY-MM-DD)")
        sd_e = ThemedEntry(frame, width=140)
        sd_e.pack(padx=14, anchor="w")
        sd_e.insert(0, date.today().isoformat())

        if habit:
            name_e.delete(0, "end"); name_e.insert(0, habit["name"])
            desc_t.insert("1.0", habit["description"] or "")
            cat_m.set(habit["category"]); freq_m.set(habit["frequency"])
            tc_e.delete(0, "end"); tc_e.insert(0, str(habit["target_count"]))
            xp_e.delete(0, "end"); xp_e.insert(0, str(habit["xp_reward"]))
            tq_e.delete(0, "end"); tq_e.insert(0, f"{habit['target_quantity']:g}")
            tu_e.delete(0, "end"); tu_e.insert(0, habit["target_unit"] or "")
            sd_e.delete(0, "end"); sd_e.insert(0, habit["start_date"])
            if habit["partial_allowed"]:
                partial_sw.select()
            wds = repo.Habits.schedule_weekdays(habit["id"])
            for i in wbtns:
                wbtns[i]["on"] = i in wds
            _paint_days()

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(pady=16)

        def save():
            try:
                nm = validation.require_text(name_e.get(), "Habit name", 60)
                pid = self.app.current_profile_id
                xp = validation.parse_int(xp_e.get(), "XP reward", 0, 500)
                tc = validation.parse_int(tc_e.get(), "Target count", 1, 99)
                tq = validation.parse_float(tq_e.get(), "Quantity target", 0, 100000, default=0)
                sd = validation.valid_iso_date(sd_e.get(), "Start date")
                days = [i for i, d in wbtns.items() if d["on"]]
                if not days:
                    raise ValueError("Select at least one weekday.")
                fields = dict(name=nm, description=desc_t.get("1.0", "end").strip(),
                              category=cat_m.get(), frequency=freq_m.get(),
                              target_count=tc, target_quantity=tq,
                              target_unit=tu_e.get().strip(), xp_reward=xp,
                              partial_allowed=partial_sw.instate(["selected"]),
                              start_date=sd, weekdays=days)
                if habit:
                    repo.Habits.update(habit["id"], **fields)
                    toast(self.app, "Habit updated.", "success")
                else:
                    repo.Habits.create(pid, nm, fields["category"], fields["frequency"],
                                       fields["description"], tc, tq,
                                       fields["target_unit"], xp,
                                       fields["partial_allowed"], sd, days)
                    toast(self.app, "Habit created.", "success")
                dlg.destroy()
                self.app.after_activity(pid)
                self.refresh()
            except ValueError as e:
                toast(self.app, str(e), "error")

        ActionButton(btns, text="Save", command=save).grid(row=0, column=0, padx=6)
        ActionButton(btns, text="Cancel", kind="secondary", command=dlg.destroy)\
            .grid(row=0, column=1, padx=6)

    # ------------------------------------------------------------- calendar --
    def _shift_month(self, delta):
        m = self.cal_month.month - 1 + delta
        y = self.cal_month.year + m // 12
        m = m % 12 + 1
        self.cal_month = date(y, m, 1)
        self._draw_calendar()

    def _draw_calendar(self):
        pid = self.app.current_profile_id
        if pid is None:
            return
        for w in self.cal_grid.winfo_children():
            w.destroy()
        p = theme_manager.palette
        y, mo = self.cal_month.year, self.cal_month.month
        self.cal_lbl.configure(text=f"{calendar.month_name[mo]} {y}")
        data = habit_engine.calendar_month(pid, y, mo)
        for ci, dn in enumerate(DAY_NAMES):
            ThemedLabel(self.cal_grid, text=dn, level="muted", size=10, bold=True)\
                .grid(row=0, column=ci, padx=3, pady=2)
        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(y, mo)
        today_iso = date.today().isoformat()
        for ri, week in enumerate(weeks):
            for ci, dnum in enumerate(week):
                if dnum == 0:
                    continue
                iso = date(y, mo, dnum).isoformat()
                info = data.get(iso, {"scheduled": 0, "done": 0})
                if info["scheduled"] == 0:
                    color, tc = p.BG_SECONDARY, p.TEXT_MUTED
                elif info["done"] >= info["scheduled"]:
                    color, tc = p.SUCCESS, "#FFFFFF"
                elif info["done"] > 0:
                    color, tc = p.WARNING, "#111111"
                else:
                    color, tc = p.PROGRESS_TRACK, p.TEXT_SECONDARY
                cell = ctk.CTkLabel(self.cal_grid, text=str(dnum), width=34, height=30,
                                    corner_radius=6, fg_color=color, text_color=tc,
                                    font=ctk.CTkFont(size=12,
                                                     bold=(iso == today_iso)))
                cell.grid(row=ri + 1, column=ci, padx=3, pady=3)
