"""Report engine — data series for charts, CSV export, printable summaries."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from database import db, repositories as repo


def daily_completion_series(profile_id: int, days: int = 30):
    from core import habit_engine
    out = []
    end = date.today()
    for i in range(days - 1, -1, -1):
        d = end - timedelta(days=i)
        pct = habit_engine.completion_percentage(profile_id, days=1, end_day=d) \
            if _any_habit_on(profile_id, d) else 0.0
        out.append((d.isoformat(), round(pct, 1)))
    return out


def _any_habit_on(profile_id: int, d: date) -> bool:
    return any(repo.Habits.is_scheduled_on(h, d) for h in repo.Habits.active(profile_id))


def xp_growth_series(profile_id: int, days: int = 30):
    """Cumulative XP over the window (only real transactions)."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = db.query("SELECT created_date d, SUM(amount) s FROM xp_transactions WHERE "
                    "profile_id=? AND created_date BETWEEN ? AND ? GROUP BY created_date",
                    (profile_id, start.isoformat(), end.isoformat()))
    by_day = {r["d"]: r["s"] for r in rows}
    out, cum = [], 0
    base = db.query_one("SELECT COALESCE(SUM(amount),0) s FROM xp_transactions WHERE "
                        "profile_id=? AND created_date<?", (profile_id, start.isoformat()))["s"]
    cum = base
    d = start
    while d <= end:
        cum += by_day.get(d.isoformat(), 0)
        out.append((d.isoformat(), max(0, cum)))
        d += timedelta(days=1)
    return out


def mental_vs_physical_series(profile_id: int, weeks: int = 8):
    out = []
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    for w in range(weeks - 1, -1, -1):
        ws = monday - timedelta(weeks=w)
        we = ws + timedelta(days=6)
        m = repo.XP.by_category(profile_id, "Mental", ws.isoformat(), we.isoformat())
        p = repo.XP.by_category(profile_id, "Physical", ws.isoformat(), we.isoformat())
        out.append((f"W{w + 1}", max(0, m), max(0, p)))
    return out


def streak_history_series(profile_id: int, days: int = 30):
    """Daily XP bar used to visualise streak rhythm."""
    return [(d, max(0, v)) for d, v in repo.XP.daily_series(profile_id, days)]


def heatmap_data(profile_id: int, days: int = 84) -> dict[str, float]:
    """Completion fraction per day for the consistency heatmap (real data only)."""
    from core import habit_engine
    out = {}
    end = date.today()
    start = end - timedelta(days=days - 1)
    d = start
    while d <= end:
        if _any_habit_on(profile_id, d):
            out[d.isoformat()] = habit_engine.completion_percentage(
                profile_id, days=1, end_day=d) / 100.0
        d += timedelta(days=1)
    return out


def best_and_missed_habits(profile_id: int, days: int = 30):
    from core import habit_engine
    stats = []
    for h in repo.Habits.active(profile_id):
        st = habit_engine.habit_history_stats(profile_id, h["id"], days)
        if st["scheduled"] >= 2:
            stats.append(st)
    stats.sort(key=lambda s: s["rate"], reverse=True)
    best = stats[:5]
    missed = [s for s in stats if s["rate"] < 70][-5:] or stats[-5:]
    return best, missed


# ------------------------------------------------------------------ CSV ----
def _write_csv(path: Path, header: list[str], rows: list[list]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


def export_completions_csv(profile_id: int) -> Path:
    rows = db.query("SELECT c.completion_date, h.name, h.category, c.quantity,"
                    " c.is_partial, c.xp_awarded, c.note FROM completions c "
                    "JOIN habits h ON h.id=c.habit_id WHERE c.profile_id=? "
                    "ORDER BY c.completion_date", (profile_id,))
    name = repo.Profiles.get(profile_id)["name"]
    return _write_csv(db.EXPORT_DIR / f"completions_{name}_{date.today():%Y%m%d}.csv",
                      ["date", "habit", "category", "quantity", "partial", "xp", "note"],
                      [[r[k] for k in r.keys()] for r in rows])


def export_xp_csv(profile_id: int) -> Path:
    rows = db.query("SELECT created_date, amount, reason, category FROM xp_transactions "
                    "WHERE profile_id=? ORDER BY created_date", (profile_id,))
    name = repo.Profiles.get(profile_id)["name"]
    return _write_csv(db.EXPORT_DIR / f"xp_{name}_{date.today():%Y%m%d}.csv",
                      ["date", "amount", "reason", "category"],
                      [[r[k] for k in r.keys()] for r in rows])


def export_workouts_csv(profile_id: int) -> Path:
    rows = db.query("SELECT session_date, exercise, kind, duration_minutes, sets, reps,"
                    " distance_km, notes FROM workout_sessions WHERE profile_id=? "
                    "ORDER BY session_date", (profile_id,))
    name = repo.Profiles.get(profile_id)["name"]
    return _write_csv(db.EXPORT_DIR / f"workouts_{name}_{date.today():%Y%m%d}.csv",
                      ["date", "exercise", "kind", "minutes", "sets", "reps",
                       "distance_km", "notes"],
                      [[r[k] for k in r.keys()] for r in rows])


def export_focus_csv(profile_id: int) -> Path:
    rows = db.query("SELECT session_date, kind, label, planned_minutes, actual_minutes,"
                    " completed, xp_awarded FROM focus_sessions WHERE profile_id=? "
                    "ORDER BY session_date", (profile_id,))
    name = repo.Profiles.get(profile_id)["name"]
    return _write_csv(db.EXPORT_DIR / f"focus_{name}_{date.today():%Y%m%d}.csv",
                      ["date", "kind", "label", "planned_min", "actual_min",
                       "completed", "xp"],
                      [[r[k] for k in r.keys()] for r in rows])


def weekly_report_text(profile_id: int) -> str:
    """Plain-text summary suitable for printing / clipboard."""
    from core import scoring_engine
    pid = profile_id
    prof = repo.Profiles.get(pid)
    wk = scoring_engine.weekly_summary(pid)
    sc = scoring_engine.scores(pid)
    rp = scoring_engine.rank_progress(pid)
    cur = repo.Streaks.current(pid)
    longest = repo.Streaks.longest(pid)
    lines = [
        "=" * 52,
        f"DEMONBACK X — WEEKLY REPORT :: {prof['name']}",
        f"Week of {wk['week_start']}   Generated {date.today():%Y-%m-%d}",
        "=" * 52,
        f"Rank: {rp['rank']} ({rp['total_xp']} total XP)",
        f"Weekly XP: {wk['xp']}   |   Completions: {wk['completions']}",
        f"Focus minutes: {wk['focus_minutes']}   |   Workout minutes: {wk['workout_minutes']}",
        f"Streak: {cur} current / {longest} longest",
        f"Scores — Mental {sc['mental']} · Physical {sc['physical']} "
        f"· Discipline {sc['discipline']} · Combined {sc['combined']}",
        "-" * 52,
        "(Scores reflect tracked activity against your own goals; they are not",
        " medical or psychological measurements.)",
        "=" * 52,
    ]
    return "\n".join(lines)
