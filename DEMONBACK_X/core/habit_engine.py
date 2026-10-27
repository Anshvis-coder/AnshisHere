"""Habit engine — daily checklist building, calendar data, history stats."""
from __future__ import annotations

from datetime import date, timedelta

from database import db, repositories as repo


def todays_checklist(profile_id: int, day: date | None = None) -> list[dict]:
    """Active habits scheduled on `day` + whether already completed."""
    day = day or date.today()
    iso = day.isoformat()
    done = repo.Completions.completed_habit_ids(profile_id, iso)
    out = []
    for h in repo.Habits.active(profile_id):
        if repo.Habits.is_scheduled_on(h, day):
            comp = repo.Completions.get(profile_id, h["id"], iso)
            out.append({
                "habit": h,
                "done": h["id"] in done,
                "partial": bool(comp["is_partial"]) if comp else False,
                "quantity": comp["quantity"] if comp else 0,
            })
    return sorted(out, key=lambda e: (e["done"], e["habit"]["category"], e["habit"]["name"]))


def completion_percentage(profile_id: int, days: int = 30, end_day: date | None = None) -> float:
    """Scheduled-vs-completed ratio over the last N days (only counts days from
    habit start_date onward; never fabricates data before a habit existed)."""
    end_day = end_day or date.today()
    scheduled = completed = 0
    for i in range(days):
        d = end_day - timedelta(days=i)
        if d > end_day:
            continue
        for h in repo.Habits.active(profile_id):
            if repo.Habits.is_scheduled_on(h, d):
                scheduled += 1
                if repo.Completions.get(profile_id, h["id"], d.isoformat()):
                    completed += 1
    return (completed / scheduled * 100.0) if scheduled else 0.0


def calendar_month(profile_id: int, year: int, month: int) -> dict[str, dict]:
    """Per-day info for a month calendar view: {iso: {scheduled, done}}."""
    start = date(year, month, 1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    out = {}
    habits = repo.Habits.active(profile_id)
    d = start
    while d <= end:
        sched = [h for h in habits if repo.Habits.is_scheduled_on(h, d)]
        done_ids = repo.Completions.completed_habit_ids(profile_id, d.isoformat())
        out[d.isoformat()] = {"scheduled": len(sched),
                              "done": sum(1 for h in sched if h["id"] in done_ids)}
        d += timedelta(days=1)
    return out


def habit_history_stats(profile_id: int, habit_id: int, days: int = 90) -> dict:
    """Completion count and rate for one habit over recent window."""
    habit = repo.Habits.get(habit_id)
    if habit is None or habit["profile_id"] != profile_id:
        raise ValueError("Habit not found.")
    end = date.today()
    start = max(end - timedelta(days=days - 1),
                date.fromisoformat(habit["start_date"]))
    scheduled = completed = 0
    d = start
    while d <= end:
        if repo.Habits.is_scheduled_on(habit, d):
            scheduled += 1
            if repo.Completions.get(profile_id, habit_id, d.isoformat()):
                completed += 1
        d += timedelta(days=1)
    return {"habit": habit, "scheduled": scheduled, "completed": completed,
            "rate": (completed / scheduled * 100) if scheduled else 0.0}


def best_habit(profile_id: int, days: int = 30) -> dict | None:
    """Most consistent active habit (min 3 scheduled occurrences)."""
    best = None
    for h in repo.Habits.active(profile_id):
        st = habit_history_stats(profile_id, h["id"], days)
        if st["scheduled"] >= 3 and (best is None or st["rate"] > best["rate"]):
            best = st
    return best


def worst_habit(profile_id: int, days: int = 30) -> dict | None:
    worst = None
    for h in repo.Habits.active(profile_id):
        st = habit_history_stats(profile_id, h["id"], days)
        if st["scheduled"] >= 3 and (worst is None or st["rate"] < worst["rate"]):
            worst = st
    return worst
