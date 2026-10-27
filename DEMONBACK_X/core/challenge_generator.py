"""Challenge generator — rule-based daily missions + weekly challenges.

Rules use past performance to adjust difficulty, but never invent impossible
tasks and never auto-increase workout intensity: physical missions stay at the
user's configured level unless the user changes difficulty in Settings.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from database import db, repositories as repo
from core import scoring_engine

# Mission library: (title, description, category, difficulty, xp)
MISSION_LIBRARY = {
    "easy": [
        ("Focused study block", "One 25-minute distraction-free study session.", "Mental", 10),
        ("Read 10 pages", "Any book that feeds your goals.", "Mental", 10),
        ("Walk 20 minutes", "Outdoor walk at a comfortable pace.", "Physical", 10),
        ("Stretch for 10 minutes", "Loosen up — mobility counts as training.", "Physical", 8),
        ("Tidy your workspace", "Five minutes of reset beats hours of complaint.", "Discipline", 8),
        ("Plan tomorrow tonight", "Write the three priorities for the next day.", "Discipline", 10),
        ("Hydration target", "Reach your configured daily water goal.", "Physical", 8),
        ("Mindful break", "Ten minutes away from every screen.", "Mental", 8),
    ],
    "normal": [
        ("Deep work session", "45 focused minutes on your hardest task.", "Mental", 15),
        ("Workout session", "A complete workout suited to your level.", "Physical", 20),
        ("Priority task done", "Finish the most important task first.", "Discipline", 20),
        ("Skill practice", "30 deliberate minutes on one skill.", "Mental", 15),
        ("Journal reflection", "Write today's reflection honestly.", "Mental", 10),
        ("Cardio 25 minutes", "Run, cycle, rope — sustained effort.", "Physical", 18),
        ("Screen-time cut", "Halve your recreational screen time today.", "Discipline", 15),
        ("On-time start", "Begin your first task exactly when planned.", "Discipline", 12),
    ],
    "hard": [
        ("Double focus block", "Two 45-minute deep work sessions, one topic.", "Mental", 25),
        ("Full training day", "Strength + mobility, scaled to your ability.", "Physical", 30),
        ("Eat-the-frog day", "Complete your top three priorities before noon.", "Discipline", 30),
        ("Long cardio", "45+ minute sustained cardio effort.", "Physical", 28),
        ("Study marathon prep", "Prepare and run a 90-minute study plan.", "Mental", 25),
    ],
}

TEAM_MISSIONS = [
    ("Team mission: sync check-in", "Both players log their day before 21:00.", 15),
    ("Team mission: joint walk", "Take a 20-minute walk together.", 15),
    ("Team mission: no-excuses hour", "Both players do one hour of deep work simultaneously.", 20),
]

COMEBACK_MISSION = ("Comeback mission", "Yesterday was missed. Do any ONE small habit today to restart your streak.", 12)
RECOVERY_MISSION = ("Recovery mission", "Rest day is a valid day: stretch lightly, hydrate, sleep early.", 10)


def _difficulty_for(profile_id: int) -> str:
    """Adjust based on recent completion rate and user preference cap."""
    pref = db.get_setting("challenge_difficulty", "normal")
    rate = scoring_engine.daily_completion_rate(profile_id,
                                                date.today() - timedelta(days=1))
    if pref == "easy":
        return "easy"
    if pref == "hard":
        return "hard" if rate >= 0.4 else "normal"
    # normal preference: soften after bad days, sharpen after strong ones
    if rate < 0.25:
        return "easy"
    if rate > 0.75:
        return "normal"
    return "normal"


def generate_daily_missions(profile_id: int, day: date | None = None) -> list[int]:
    """Create 2-3 missions for `day` if none exist yet. Returns mission ids."""
    day = day or date.today()
    iso = day.isoformat()
    existing = repo.Missions.for_date(profile_id, iso)
    if [m for m in existing if m["source"] == "generated"]:
        return [m["id"] for m in existing if m["source"] == "generated"]

    rng = random.Random(f"{profile_id}-{iso}")       # deterministic per profile/day
    diff = _difficulty_for(profile_id)
    pool = MISSION_LIBRARY[diff]
    picks = rng.sample(pool, k=min(2, len(pool)))
    ids = []
    for title, desc, cat, xp in picks:
        ids.append(repo.Missions.add(profile_id, iso, title, desc, cat, diff, xp,
                                     source="generated"))
    # Comeback logic: yesterday had zero XP → add comeback/recovery mission
    y_iso = (day - timedelta(days=1)).isoformat()
    if repo.XP.on_day(profile_id, y_iso) <= 0 and repo.XP.between(profile_id, y_iso, y_iso) <= 0:
        t, d_, xp = COMEBACK_MISSION
        ids.append(repo.Missions.add(profile_id, iso, t, d_, "Discipline", "easy", xp,
                                     source="generated"))
    # Recovery guard: 3+ hard physical days in a row → recovery mission instead
    phys_days = 0
    for i in range(1, 4):
        d_iso = (day - timedelta(days=i)).isoformat()
        rows = db.query("SELECT 1 FROM workout_sessions WHERE profile_id=? AND session_date=?"
                        " AND kind IN ('strength','cardio') LIMIT 1", (profile_id, d_iso))
        if rows:
            phys_days += 1
    if phys_days >= 3:
        t, d_, xp = RECOVERY_MISSION
        ids.append(repo.Missions.add(profile_id, iso, t, d_, "Physical", "easy", xp,
                                     source="generated"))
    return ids


WEEKLY_TEMPLATES = [
    ("Consistency Week", "Both players earn XP on at least 5 different days.",
     "cooperative", "days_active", 10, 60),
    ("Focus Gauntlet", "Accumulate 300 total focus minutes as a team.",
     "cooperative", "focus_minutes", 300, 60),
    ("Movement Week", "Each player logs 4 workouts this week.",
     "competitive", "workouts", 4, 40),
    ("Habit Storm", "Collect 25 habit completions between both players.",
     "cooperative", "completions", 25, 50),
    ("XP Duel", "Highest weekly XP wins the round.",
     "competitive", "xp", 1, 50),
]


def ensure_weekly_challenge(active_profile_ids: list[int]) -> int | None:
    """Create this week's challenge if none is active. Deterministic per ISO week."""
    repo.Challenges.expire_overdue()
    if repo.Challenges.active():
        return repo.Challenges.active()[0]["id"]
    year, week, _ = date.today().isocalendar()
    rng = random.Random(f"weekly-{year}-{week}")
    title, desc, mode, metric, target, xp = rng.choice(WEEKLY_TEMPLATES)
    monday = date.today() - timedelta(days=date.today().weekday())
    sunday = monday + timedelta(days=6)
    return repo.Challenges.create(title, desc, mode, metric, float(target), xp,
                                  monday.isoformat(), sunday.isoformat(),
                                  profile_ids=active_profile_ids)


def update_challenge_progress(profile_id: int) -> None:
    """Sync active challenge progress from real data (called after activity)."""
    today = date.today()
    monday = (today - timedelta(days=today.weekday())).isoformat()
    today_iso = today.isoformat()
    for ch in repo.Challenges.active():
        cid = ch["id"]
        metric = ch["metric"]
        if metric == "xp":
            val = repo.XP.between(profile_id, monday, today_iso)
        elif metric == "focus_minutes":
            val = repo.FocusSessions.total_minutes(profile_id, monday, today_iso)
        elif metric == "workouts":
            rows = db.query("SELECT COUNT(*) c FROM workout_sessions WHERE profile_id=? "
                            "AND session_date BETWEEN ? AND ?", (profile_id, monday, today_iso))
            val = rows[0]["c"]
        elif metric == "completions":
            val = repo.Completions.count_between(profile_id, monday, today_iso)
        elif metric == "days_active":
            rows = db.query("SELECT DISTINCT created_date d FROM xp_transactions WHERE "
                            "profile_id=? AND amount>0 AND created_date BETWEEN ? AND ?",
                            (profile_id, monday, today_iso))
            val = len(rows)
        else:
            continue
        prev = db.query_one("SELECT contribution FROM challenge_participants WHERE "
                            "challenge_id=? AND profile_id=?", (cid, profile_id))
        prev_val = prev["contribution"] if prev else 0
        delta = max(0, val - prev_val)
        if delta:
            repo.Challenges.contribute(cid, profile_id, delta)
        # cooperative auto-complete
        if ch["mode"] == "cooperative":
            fresh = repo.Challenges.get(cid)
            if fresh and fresh["progress_value"] >= fresh["target_value"] \
                    and fresh["status"] == "active":
                awarded = repo.Challenges.complete(cid)
                if awarded:
                    db.set_setting(f"chal_done_{cid}", "1")   # UI polls this to toast
