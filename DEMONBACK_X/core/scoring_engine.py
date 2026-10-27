"""Scoring engine — XP totals, ranks, category scores, completion rates.

NOTE ON "SCORES": Mental / Physical / Discipline scores are simple
descriptive metrics computed from tracked activities and user-defined goals.
They are NOT medical or psychological measurements of any kind.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from database import db, repositories as repo

# Rank thresholds stored in config.json under "ranks" (XP needed to reach).
DEFAULT_RANKS = [
    {"name": "Recruit", "min_xp": 0},
    {"name": "Disciplined", "min_xp": 250},
    {"name": "Relentless", "min_xp": 800},
    {"name": "Elite", "min_xp": 2000},
    {"name": "Apex", "min_xp": 4500},
]


def load_ranks() -> list[dict]:
    try:
        cfg_path = db.BASE_DIR / "config.json"
        if cfg_path.exists():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            ranks = data.get("ranks")
            if isinstance(ranks, list) and ranks and all(
                    isinstance(r, dict) and "name" in r and "min_xp" in r for r in ranks):
                return sorted(ranks, key=lambda r: int(r["min_xp"]))
    except (json.JSONDecodeError, OSError, ValueError):
        pass  # corrupted config → fall back to defaults, never crash
    return DEFAULT_RANKS


def rank_for_xp(total_xp: int, ranks: list[dict] | None = None) -> tuple[dict, dict | None]:
    """Return (current_rank, next_rank_or_None)."""
    ranks = ranks or load_ranks()
    current = ranks[0]
    nxt = None
    for r in ranks:
        if total_xp >= int(r["min_xp"]):
            current = r
        else:
            nxt = r
            break
    return current, nxt


def rank_progress(profile_id: int) -> dict:
    total = repo.XP.total(profile_id)
    cur, nxt = rank_for_xp(total)
    into = total - int(cur["min_xp"])
    needed = (int(nxt["min_xp"]) - int(cur["min_xp"])) if nxt else 0
    return {"total_xp": total, "rank": cur["name"], "next_rank": nxt["name"] if nxt else None,
            "into_rank": into, "needed_for_next": needed,
            "fraction": (into / needed) if needed else 1.0}


def _category_score(profile_id: int, category: str, days: int = 7) -> int:
    """Score 0..100 based on XP earned in a category over the window vs a target.

    Target = 1 active day per every 2 days at ~30 XP/day baseline; capped at 100.
    Transparent, deterministic, and identical rules for both profiles.
    """
    end = date.today()
    start = end - timedelta(days=days - 1)
    xp = repo.XP.by_category(profile_id, category, start.isoformat(), end.isoformat())
    active_days = 0
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        if repo.XP.by_category(profile_id, category, d, d) > 0:
            active_days += 1
    target_xp = days * 15                       # gentle weekly baseline
    score = min(100, round((xp / target_xp) * 60 + (active_days / days) * 40))
    return int(score)


def scores(profile_id: int) -> dict:
    mental = _category_score(profile_id, "Mental")
    physical = _category_score(profile_id, "Physical")
    discipline = _category_score(profile_id, "Discipline")
    combined = round((mental + physical + discipline) / 3)
    return {"mental": mental, "physical": physical, "discipline": discipline,
            "combined": combined}


def daily_completion_rate(profile_id: int, day: date | None = None) -> float:
    """Fraction (0..1) of scheduled habits+missions completed on `day`."""
    day = day or date.today()
    iso = day.isoformat()
    habits = [h for h in repo.Habits.active(profile_id) if repo.Habits.is_scheduled_on(h, day)]
    done_habits = repo.Completions.completed_habit_ids(profile_id, iso)
    missions = repo.Missions.for_date(profile_id, iso)
    relevant_missions = [m for m in missions if m["status"] in ("pending", "done")]
    done_missions = [m for m in relevant_missions if m["status"] == "done"]
    total = len(habits) + len(relevant_missions)
    if total == 0:
        return 0.0
    done = sum(1 for h in habits if h["id"] in done_habits) + len(done_missions)
    return done / total


def weekly_summary(profile_id: int, week_start: date | None = None) -> dict:
    ws = week_start or (date.today() - timedelta(days=date.today().weekday()))
    we = ws + timedelta(days=6)
    s, e = ws.isoformat(), we.isoformat()
    return {
        "week_start": s, "week_end": e,
        "xp": repo.XP.between(profile_id, s, e),
        "mental_xp": repo.XP.by_category(profile_id, "Mental", s, e),
        "physical_xp": repo.XP.by_category(profile_id, "Physical", s, e),
        "discipline_xp": repo.XP.by_category(profile_id, "Discipline", s, e),
        "completions": repo.Completions.count_between(profile_id, s, e),
        "focus_minutes": repo.FocusSessions.total_minutes(profile_id, s, e),
        "workout_minutes": repo.Workouts.weekly_minutes(profile_id, s, e),
    }


def monthly_summary(profile_id: int, month: date | None = None) -> dict:
    m = month or date.today()
    start = m.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    s, e = start.isoformat(), end.isoformat()
    return {
        "month": s[:7],
        "xp": repo.XP.between(profile_id, s, e),
        "completions": repo.Completions.count_between(profile_id, s, e),
        "focus_minutes": repo.FocusSessions.total_minutes(profile_id, s, e),
        "workout_minutes": repo.Workouts.weekly_minutes(profile_id, s, e),
    }


def check_and_unlock_achievements(profile_id: int) -> list[str]:
    """Evaluate all achievement rules; unlock newly earned ones. Returns titles."""
    unlocked_now: list[str] = []
    already = repo.Achievements.unlocked(profile_id)

    def try_key(key: str, cond: bool):
        if cond and key not in already:
            if repo.Achievements.unlock(profile_id, key):
                row = db.query_one("SELECT title FROM achievements WHERE key=?", (key,))
                unlocked_now.append(row["title"] if row else key)

    total_completions = db.query_one(
        "SELECT COUNT(*) c FROM completions WHERE profile_id=?", (profile_id,))["c"] \
        + db.query_one("SELECT COUNT(*) c FROM daily_missions WHERE profile_id=? AND "
                       "status='done'", (profile_id,))["c"]
    streaks_row = repo.Streaks.get_row(profile_id, "overall")
    longest = streaks_row["longest_streak"] if streaks_row else 0
    try_key("first_blood", total_completions >= 1)
    try_key("week_warrior", longest >= 7)
    try_key("iron_streak", longest >= 30)
    try_key("mental_monk", repo.FocusSessions.count(profile_id) >= 10)
    deep = db.query_one("SELECT COUNT(*) c FROM focus_sessions WHERE profile_id=? AND "
                        "completed=1 AND actual_minutes>=60", (profile_id,))["c"]
    try_key("deep_focus", deep >= 1)
    try_key("body_forge", repo.Workouts.count(profile_id) >= 10)
    goal = int(db.get_setting("daily_water_goal_ml", "2000"))
    hyd = db.query_one("SELECT COUNT(*) c FROM hydration_logs WHERE profile_id=? AND "
                       "amount_ml>=?", (profile_id, goal))["c"]
    try_key("hydrated", hyd >= 1)
    try_key("reflective", repo.Journal.count(profile_id) >= 7)
    total_xp = repo.XP.total(profile_id)
    cur_rank, _ = rank_for_xp(total_xp)
    for rank_name, key in (("Disciplined", "rank_disciplined"), ("Relentless", "rank_relentless"),
                           ("Elite", "rank_elite"), ("Apex", "rank_apex")):
        idx = [r["name"] for r in load_ranks()]
        if rank_name in idx and idx.index(rank_name) <= idx.index(cur_rank):
            try_key(key, True)
    wins = db.query_one("SELECT COUNT(*) c FROM rivalry_results WHERE winner_id=?",
                        (profile_id,))["c"]
    try_key("rival_slayer", wins >= 1)
    chal = db.query_one("SELECT COUNT(*) c FROM challenge_participants WHERE profile_id=? "
                        "AND completed=1", (profile_id,))["c"]
    try_key("challenge_done", chal >= 1)
    return unlocked_now
