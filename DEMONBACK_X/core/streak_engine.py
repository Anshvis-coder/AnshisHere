"""Date-aware streak engine.

A day counts as "active" for a profile when any XP was earned that day
(habit completion, mission, focus session, workout, journal, bonus).
Streaks are recomputed from history — they never erase past achievements,
and missed days only reset the *current* counter, not stored records.
"""
from __future__ import annotations

from datetime import date, timedelta

from database import db, repositories as repo


def active_dates(profile_id: int, scope: str = "overall") -> set[str]:
    """ISO dates on which the profile earned positive XP in `scope`."""
    if scope == "overall":
        rows = db.query("SELECT DISTINCT created_date d FROM xp_transactions "
                        "WHERE profile_id=? AND amount>0", (profile_id,))
        return {r["d"] for r in rows}
    category_map = {"mental": "Mental", "physical": "Physical", "discipline": "Discipline"}
    cat = category_map.get(scope.lower())
    if cat is None:
        return set()
    rows = db.query("SELECT DISTINCT created_date d FROM xp_transactions WHERE profile_id=? "
                    "AND category=? AND amount>0", (profile_id, cat))
    return {r["d"] for r in rows}


def compute_streak(active: set[str], today: date | None = None) -> tuple[int, str]:
    """Current consecutive-day streak ending today or yesterday.

    Returns (streak_length, last_active_iso_or_empty). A miss *today* does not
    break the streak until the day ends; a gap of 2+ days resets it to 0.
    """
    today = today or date.today()
    if not active:
        return 0, ""
    # find the anchor: today if active, else yesterday, else no current streak
    if today.isoformat() in active:
        anchor = today
    elif (today - timedelta(days=1)).isoformat() in active:
        anchor = today - timedelta(days=1)
    else:
        latest = max(active)
        return 0, latest
    n = 0
    d = anchor
    while d.isoformat() in active:
        n += 1
        d -= timedelta(days=1)
    return n, anchor.isoformat()


def longest_streak(active: set[str]) -> int:
    if not active:
        return 0
    days = sorted(date.fromisoformat(x) for x in active)
    best = cur = 1
    for prev, nxt in zip(days, days[1:]):
        if (nxt - prev).days == 1:
            cur += 1
            best = max(best, cur)
        elif (nxt - prev).days > 1:
            cur = 1
    return best


def refresh(profile_id: int, scopes: list[str] | None = None) -> dict:
    """Recompute + persist streaks. Returns {'current':..,'longest':..} overall."""
    scopes = scopes or ["overall", "mental", "physical", "discipline"]
    result = {}
    for scope in scopes:
        act = active_dates(profile_id, scope)
        cur, last = compute_streak(act)
        longest = max(longest_streak(act), repo.Streaks.longest(profile_id, scope))
        repo.Streaks.save(profile_id, scope, cur, longest, last)
        if scope == "overall":
            result = {"current": cur, "longest": longest}
    return result


def current(profile_id: int, scope: str = "overall") -> int:
    """Fast read used by dashboard — refreshes first so date rollover works."""
    refresh(profile_id, [scope])
    return repo.Streaks.current(profile_id, scope)
