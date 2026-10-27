"""Repository layer — every function that reads/writes business data.

Screens and engines call these; they never execute SQL directly.
All dates are local calendar dates in ISO format YYYY-MM-DD.
"""
from __future__ import annotations

from datetime import date, datetime

from database import db

# ------------------------------------------------------------- profiles ----
class Profiles:
    @staticmethod
    def all(include_inactive: bool = True) -> list[db.sqlite3.Row]:
        if include_inactive:
            return db.query("SELECT * FROM profiles ORDER BY id")
        return db.query("SELECT * FROM profiles WHERE is_active=1 ORDER BY id")

    @staticmethod
    def get(profile_id: int):
        return db.query_one("SELECT * FROM profiles WHERE id=?", (profile_id,))

    @staticmethod
    def create(name: str, avatar_color: str = "#DC143C", goals: str = "",
               pin: str = "") -> int:
        name = name.strip()
        if not name:
            raise ValueError("Profile name cannot be empty.")
        if len(name) > 24:
            raise ValueError("Profile name too long (max 24 characters).")
        h = db.pin_hash(pin) if pin else ""
        cur = db.execute(
            "INSERT INTO profiles(name,avatar_color,goals,pin_hash) VALUES(?,?,?,?)",
            (name, avatar_color, goals.strip(), h))
        return cur.lastrowid

    @staticmethod
    def update(profile_id: int, name: str | None = None, avatar_color: str | None = None,
               goals: str | None = None, pin: str | None = None,
               is_active: bool | None = None) -> None:
        sets, params = [], []
        if name is not None:
            name = name.strip()
            if not name or len(name) > 24:
                raise ValueError("Invalid profile name.")
            sets.append("name=?"); params.append(name)
        if avatar_color is not None:
            sets.append("avatar_color=?"); params.append(avatar_color)
        if goals is not None:
            sets.append("goals=?"); params.append(goals.strip())
        if pin is not None:
            sets.append("pin_hash=?"); params.append(db.pin_hash(pin) if pin else "")
        if is_active is not None:
            sets.append("is_active=?"); params.append(1 if is_active else 0)
        if sets:
            params.append(profile_id)
            db.execute(f"UPDATE profiles SET {','.join(sets)} WHERE id=?", tuple(params))

    @staticmethod
    def check_pin(profile_id: int, pin: str) -> bool:
        row = Profiles.get(profile_id)
        if row is None or not row["pin_hash"]:
            return True
        return row["pin_hash"] == db.pin_hash(pin)

    @staticmethod
    def has_pin(profile_id: int) -> bool:
        row = Profiles.get(profile_id)
        return bool(row and row["pin_hash"])

    @staticmethod
    def delete(profile_id: int) -> None:
        db.execute("DELETE FROM profiles WHERE id=?", (profile_id,))


# --------------------------------------------------------------- habits ----
class Habits:
    @staticmethod
    def active(profile_id: int):
        return db.query("SELECT * FROM habits WHERE profile_id=? AND archived=0 "
                        "ORDER BY category, name", (profile_id,))

    @staticmethod
    def all_for_profile(profile_id: int):
        return db.query("SELECT * FROM habits WHERE profile_id=? ORDER BY archived, name",
                        (profile_id,))

    @staticmethod
    def get(habit_id: int):
        return db.query_one("SELECT * FROM habits WHERE id=?", (habit_id,))

    @staticmethod
    def create(profile_id: int, name: str, category: str, frequency: str = "daily",
               description: str = "", target_count: int = 1, target_quantity: float = 0,
               target_unit: str = "", xp_reward: int = 10, partial_allowed: bool = False,
               start_date: str | None = None, weekdays: list[int] | None = None) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Habit name cannot be empty.")
        if category not in ("Mental", "Physical", "Discipline"):
            raise ValueError("Unknown habit category.")
        if frequency not in ("daily", "weekly"):
            raise ValueError("Frequency must be daily or weekly.")
        if xp_reward < 0 or xp_reward > 500:
            raise ValueError("XP reward must be between 0 and 500.")
        if target_count < 1:
            target_count = 1
        start = start_date or date.today().isoformat()
        dup = db.query_one("SELECT id FROM habits WHERE profile_id=? AND name=? "
                           "AND archived=0 COLLATE NOCASE", (profile_id, name))
        if dup:
            raise ValueError(f"A habit named '{name}' already exists.")
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO habits(profile_id,name,description,category,frequency,"
                "target_count,target_quantity,target_unit,xp_reward,partial_allowed,"
                "start_date) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (profile_id, name, description.strip(), category, frequency,
                 target_count, target_quantity, target_unit, int(xp_reward),
                 1 if partial_allowed else 0, start))
            hid = cur.lastrowid
            days = weekdays if weekdays else list(range(7))
            for wd in sorted(set(days)):
                conn.execute("INSERT INTO habit_schedules(habit_id,weekday) VALUES(?,?)",
                             (hid, int(wd)))
            # ensure streak row exists
            conn.execute("INSERT OR IGNORE INTO streaks(profile_id,scope) VALUES(?,'overall')",
                         (profile_id,))
        return hid

    @staticmethod
    def schedule_weekdays(habit_id: int) -> list[int]:
        return [r["weekday"] for r in
                db.query("SELECT weekday FROM habit_schedules WHERE habit_id=?", (habit_id,))]

    @staticmethod
    def update(habit_id: int, **fields) -> None:
        allowed = {"name", "description", "category", "frequency", "target_count",
                   "target_quantity", "target_unit", "xp_reward", "partial_allowed",
                   "start_date", "archived"}
        sets, params = [], []
        for k, v in fields.items():
            if k in allowed:
                if k == "name" and not str(v).strip():
                    raise ValueError("Habit name cannot be empty.")
                if k == "partial_allowed":
                    v = 1 if v else 0
                sets.append(f"{k}=?"); params.append(v)
        if sets:
            params.append(habit_id)
            db.execute(f"UPDATE habits SET {','.join(sets)} WHERE id=?", tuple(params))
        if "weekdays" in fields:
            with db.transaction() as conn:
                conn.execute("DELETE FROM habit_schedules WHERE habit_id=?", (habit_id,))
                for wd in sorted(set(int(d) for d in fields["weekdays"])):
                    conn.execute("INSERT INTO habit_schedules(habit_id,weekday) VALUES(?,?)",
                                 (habit_id, wd))

    @staticmethod
    def set_archived(habit_id: int, archived: bool) -> None:
        db.execute("UPDATE habits SET archived=? WHERE id=?", (1 if archived else 0, habit_id))

    @staticmethod
    def is_scheduled_on(habit, day: date) -> bool:
        """Does this habit occur on the given local date?"""
        if habit["start_date"] and day.isoformat() < habit["start_date"]:
            return False
        wds = Habits.schedule_weekdays(habit["id"])
        return day.weekday() in wds


# ---------------------------------------------------------- completions ----
class Completions:
    @staticmethod
    def get(profile_id: int, habit_id: int, day: str):
        return db.query_one("SELECT * FROM completions WHERE profile_id=? AND habit_id=? "
                            "AND completion_date=?", (profile_id, habit_id, day))

    @staticmethod
    def complete(profile_id: int, habit_id: int, day: str, quantity: float = 1,
                 note: str = "") -> dict:
        """Record a completion + award XP atomically. Duplicate-safe.

        Returns dict(status, xp_awarded, is_partial).
        """
        habit = Habits.get(habit_id)
        if habit is None or habit["profile_id"] != profile_id:
            raise ValueError("Habit not found for this profile.")
        full = habit["target_quantity"] if habit["target_quantity"] > 0 else habit["target_count"]
        is_partial = bool(habit["partial_allowed"]) and 0 < quantity < full
        xp = int(round(habit["xp_reward"] * (quantity / full))) if is_partial \
            else int(habit["xp_reward"])
        with db.transaction() as conn:
            exists = conn.execute(
                "SELECT id FROM completions WHERE profile_id=? AND habit_id=? "
                "AND completion_date=?", (profile_id, habit_id, day)).fetchone()
            if exists:
                return {"status": "duplicate", "xp_awarded": 0, "is_partial": False}
            conn.execute(
                "INSERT INTO completions(profile_id,habit_id,completion_date,quantity,"
                "is_partial,note,xp_awarded) VALUES(?,?,?,?,?,?,?)",
                (profile_id, habit_id, day, quantity, 1 if is_partial else 0, note, xp))
            if xp > 0:
                conn.execute(
                    "INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                    "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                    (profile_id, xp, f"Habit: {habit['name']}", habit["category"],
                     "completions", 0, day))
        return {"status": "ok", "xp_awarded": xp, "is_partial": is_partial}

    @staticmethod
    def undo(profile_id: int, habit_id: int, day: str) -> int:
        """Undo today's eligible completion; reverses its XP. Returns xp removed."""
        with db.transaction() as conn:
            row = conn.execute("SELECT * FROM completions WHERE profile_id=? AND habit_id=? "
                               "AND completion_date=?", (profile_id, habit_id, day)).fetchone()
            if row is None:
                return 0
            xp = row["xp_awarded"]
            conn.execute("DELETE FROM completions WHERE id=?", (row["id"],))
            if xp > 0:
                conn.execute(
                    "UPDATE xp_transactions SET amount=-amount, reason=reason||' (reversed)' "
                    "WHERE profile_id=? AND created_date=? AND amount=? AND ref_table='completions' "
                    "AND reason LIKE 'Habit:%' LIMIT 1", (profile_id, day, xp))
        return xp

    @staticmethod
    def for_date(profile_id: int, day: str):
        return db.query("SELECT * FROM completions WHERE profile_id=? AND completion_date=?",
                        (profile_id, day))

    @staticmethod
    def completed_habit_ids(profile_id: int, day: str) -> set[int]:
        rows = db.query("SELECT habit_id FROM completions WHERE profile_id=? "
                        "AND completion_date=?", (profile_id, day))
        return {r["habit_id"] for r in rows}

    @staticmethod
    def count_between(profile_id: int, start: str, end: str) -> int:
        row = db.query_one("SELECT COUNT(*) c FROM completions WHERE profile_id=? "
                           "AND completion_date BETWEEN ? AND ?", (profile_id, start, end))
        return row["c"] if row else 0


# --------------------------------------------------------- daily missions --
class Missions:
    @staticmethod
    def for_date(profile_id: int, day: str):
        return db.query("SELECT * FROM daily_missions WHERE profile_id=? AND mission_date=? "
                        "ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, id",
                        (profile_id, day))

    @staticmethod
    def add(profile_id: int, day: str, title: str, description: str = "",
            category: str = "Discipline", difficulty: str = "normal",
            xp_reward: int = 15, source: str = "manual",
            challenge_id: int | None = None) -> int:
        title = title.strip()
        if not title:
            raise ValueError("Mission title cannot be empty.")
        cur = db.execute(
            "INSERT OR IGNORE INTO daily_missions(profile_id,mission_date,title,"
            "description,category,difficulty,xp_reward,source,challenge_id) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (profile_id, day, title, description, category, difficulty,
             int(xp_reward), source, challenge_id))
        if cur.rowcount == 0:  # duplicate — fetch existing
            row = db.query_one("SELECT id FROM daily_missions WHERE profile_id=? AND "
                               "mission_date=? AND title=? AND source=?",
                               (profile_id, day, title, source))
            return row["id"]
        return cur.lastrowid

    @staticmethod
    def get(mission_id: int):
        return db.query_one("SELECT * FROM daily_missions WHERE id=?", (mission_id,))

    @staticmethod
    def complete(mission_id: int) -> int:
        m = Missions.get(mission_id)
        if m is None:
            raise ValueError("Mission not found.")
        if m["status"] == "done":
            return 0  # duplicate prevention
        with db.transaction() as conn:
            conn.execute("UPDATE daily_missions SET status='done' WHERE id=?", (mission_id,))
            xp = m["xp_reward"]
            if xp > 0:
                conn.execute(
                    "INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                    "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                    (m["profile_id"], xp, f"Mission: {m['title']}", m["category"],
                     "daily_missions", mission_id, m["mission_date"]))
        return xp

    @staticmethod
    def undo(mission_id: int) -> int:
        m = Missions.get(mission_id)
        if m is None or m["status"] != "done":
            return 0
        with db.transaction() as conn:
            conn.execute("UPDATE daily_missions SET status='pending' WHERE id=?", (mission_id,))
            row = conn.execute("SELECT SUM(amount) s FROM xp_transactions WHERE ref_table="
                               "'daily_missions' AND ref_id=? AND amount>0",
                               (mission_id,)).fetchone()
            xp = row["s"] or 0
            if xp:
                conn.execute(
                    "INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                    "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                    (m["profile_id"], -xp, f"Reversed mission: {m['title']}",
                     m["category"], "daily_missions", mission_id, m["mission_date"]))
        return xp

    @staticmethod
    def set_status(mission_id: int, status: str) -> None:
        if status not in ("pending", "skipped", "postponed"):
            raise ValueError("Invalid status.")
        db.execute("UPDATE daily_missions SET status=? WHERE id=?", (status, mission_id))

    @staticmethod
    def delete(mission_id: int) -> None:
        db.execute("DELETE FROM daily_missions WHERE id=?", (mission_id,))


# -------------------------------------------------------- focus sessions ---
class FocusSessions:
    @staticmethod
    def log(profile_id: int, planned_min: int, actual_min: int, kind: str,
            label: str = "", completed: bool = True, day: str | None = None) -> int:
        day = day or date.today().isoformat()
        xp = 0
        cat = "Mental"
        if completed:
            setting = "xp_reading_session" if kind == "reading" else "xp_focus_session"
            base = int(db.get_setting(setting, "20"))
            # scale by duration vs default 25-min session, cap at 2x
            xp = max(1, int(round(base * min(2.0, max(actual_min, 1) / 25.0)))) \
                if actual_min >= 1 else 0
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO focus_sessions(profile_id,session_date,started_at,ended_at,"
                "planned_minutes,actual_minutes,completed,interrupted,kind,label,xp_awarded)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (profile_id, day, datetime.now().isoformat(timespec="seconds"),
                 datetime.now().isoformat(timespec="seconds"), planned_min, actual_min,
                 1 if completed else 0, 0 if completed else 1, kind, label, xp))
            if xp > 0:
                conn.execute(
                    "INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                    "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                    (profile_id, xp, f"Focus session ({kind}): {label or 'untitled'}",
                     cat, "focus_sessions", cur.lastrowid, day))
            return_val = cur.lastrowid
        return return_val

    @staticmethod
    def history(profile_id: int, limit: int = 50):
        return db.query("SELECT * FROM focus_sessions WHERE profile_id=? "
                        "ORDER BY id DESC LIMIT ?", (profile_id, limit))

    @staticmethod
    def total_minutes(profile_id: int, start: str, end: str) -> int:
        row = db.query_one("SELECT COALESCE(SUM(actual_minutes),0) m FROM focus_sessions "
                           "WHERE profile_id=? AND session_date BETWEEN ? AND ? AND completed=1",
                           (profile_id, start, end))
        return row["m"]

    @staticmethod
    def count(profile_id: int) -> int:
        row = db.query_one("SELECT COUNT(*) c FROM focus_sessions WHERE profile_id=? "
                           "AND completed=1", (profile_id,))
        return row["c"]


# ------------------------------------------------------- workout sessions --
class Workouts:
    KIND_XP_SETTING = {
        "strength": "xp_workout", "cardio": "xp_workout", "walk": "xp_mobility",
        "mobility": "xp_mobility", "stretch": "xp_mobility", "recovery": "xp_mobility",
    }

    @staticmethod
    def log(profile_id: int, exercise: str, kind: str, duration_min: int,
            sets: int = 0, reps: int = 0, load_note: str = "", distance_km: float = 0,
            notes: str = "", day: str | None = None) -> int:
        exercise = exercise.strip()
        if not exercise:
            raise ValueError("Exercise name required.")
        if duration_min < 0 or duration_min > 600:
            raise ValueError("Duration must be between 0 and 600 minutes.")
        if kind not in ("strength", "cardio", "walk", "mobility", "stretch", "recovery"):
            raise ValueError("Unknown workout kind.")
        base = int(db.get_setting(Workouts.KIND_XP_SETTING[kind], "10"))
        xp = base if duration_min >= 5 or kind == "recovery" else max(0, base // 2)
        day = day or date.today().isoformat()
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO workout_sessions(profile_id,session_date,exercise,kind,"
                "duration_minutes,sets,reps,load_note,distance_km,notes,xp_awarded) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (profile_id, day, exercise, kind, duration_min, sets, reps,
                 load_note, distance_km, notes, xp))
            if xp > 0:
                conn.execute(
                    "INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                    "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                    (profile_id, xp, f"Workout: {exercise}", "Physical",
                     "workout_sessions", cur.lastrowid, day))
            wid = cur.lastrowid
        return wid

    @staticmethod
    def history(profile_id: int, limit: int = 50):
        return db.query("SELECT * FROM workout_sessions WHERE profile_id=? "
                        "ORDER BY id DESC LIMIT ?", (profile_id, limit))

    @staticmethod
    def count(profile_id: int) -> int:
        row = db.query_one("SELECT COUNT(*) c FROM workout_sessions WHERE profile_id=?",
                           (profile_id,))
        return row["c"]

    @staticmethod
    def weekly_minutes(profile_id: int, start: str, end: str) -> int:
        row = db.query_one("SELECT COALESCE(SUM(duration_minutes),0) m FROM workout_sessions "
                           "WHERE profile_id=? AND session_date BETWEEN ? AND ?",
                           (profile_id, start, end))
        return row["m"]

    @staticmethod
    def personal_records(profile_id: int):
        return db.query(
            "SELECT kind, MAX(duration_minutes) best_minutes, MAX(distance_km) best_km, "
            "MAX(reps*sets) best_volume FROM workout_sessions WHERE profile_id=? "
            "GROUP BY kind ORDER BY kind", (profile_id,))


# ------------------------------------------------------------ hydration ----
class Hydration:
    @staticmethod
    def get(profile_id: int, day: str) -> int:
        row = db.query_one("SELECT amount_ml FROM hydration_logs WHERE profile_id=? "
                           "AND log_date=?", (profile_id, day))
        return row["amount_ml"] if row else 0

    @staticmethod
    def add(profile_id: int, day: str, ml: int) -> int:
        if ml <= 0 or ml > 5000:
            raise ValueError("Amount must be between 1 and 5000 ml per entry.")
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO hydration_logs(profile_id,log_date,amount_ml) VALUES(?,?,?) "
                "ON CONFLICT(profile_id,log_date) DO UPDATE SET amount_ml=amount_ml+excluded.amount_ml",
                (profile_id, day, ml))
        goal = int(db.get_setting("daily_water_goal_ml", "2000"))
        total = Hydration.get(profile_id, day)
        if goal and total >= ml + (total - ml) and total - ml < goal <= total:
            core_award_bonus(profile_id, "Hydration goal reached", "Physical", 5, day)
        return total

    @staticmethod
    def set_amount(profile_id: int, day: str, ml: int) -> None:
        ml = max(0, min(ml, 20000))
        db.execute("INSERT INTO hydration_logs(profile_id,log_date,amount_ml) VALUES(?,?,?) "
                   "ON CONFLICT(profile_id,log_date) DO UPDATE SET amount_ml=?",
                   (profile_id, day, ml, ml))


def core_award_bonus(profile_id: int, reason: str, category: str, xp: int, day: str) -> None:
    """Small internal helper to grant bonus XP transactionally."""
    if xp <= 0:
        return
    db.execute("INSERT INTO xp_transactions(profile_id,amount,reason,category,ref_table,"
               "ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
               (profile_id, xp, reason, category, "bonus", 0, day))


# -------------------------------------------------------------- journal ----
class Journal:
    @staticmethod
    def get_entry(profile_id: int, day: str):
        return db.query_one("SELECT * FROM journal_entries WHERE profile_id=? AND entry_date=?",
                            (profile_id, day))

    @staticmethod
    def save(profile_id: int, day: str, reflection: str, mood: int = 5,
             distractions: str = "", wins: str = "") -> bool:
        """Save/update the day's entry. Awards reflection XP only on first save."""
        mood = max(1, min(10, int(mood)))
        existing = Journal.get_entry(profile_id, day)
        xp_setting = int(db.get_setting("xp_daily_reflection", "10"))
        awarded = False
        with db.transaction() as conn:
            if existing:
                conn.execute("UPDATE journal_entries SET reflection=?,mood=?,distractions=?,"
                             "wins=?,updated_at=datetime('now') WHERE id=?",
                             (reflection, mood, distractions, wins, existing["id"]))
            else:
                conn.execute("INSERT INTO journal_entries(profile_id,entry_date,mood,"
                             "reflection,distractions,wins) VALUES(?,?,?,?,?,?)",
                             (profile_id, day, mood, reflection, distractions, wins))
                if xp_setting > 0 and reflection.strip():
                    conn.execute("INSERT INTO xp_transactions(profile_id,amount,reason,"
                                 "category,ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                                 (profile_id, xp_setting, "Daily reflection", "Mental",
                                  "journal_entries", 0, day))
                    awarded = True
        return awarded

    @staticmethod
    def entries(profile_id: int, limit: int = 60):
        return db.query("SELECT * FROM journal_entries WHERE profile_id=? "
                        "ORDER BY entry_date DESC LIMIT ?", (profile_id, limit))

    @staticmethod
    def count(profile_id: int) -> int:
        row = db.query_one("SELECT COUNT(*) c FROM journal_entries WHERE profile_id=?",
                           (profile_id,))
        return row["c"]


# ------------------------------------------------------------------ XP -----
class XP:
    @staticmethod
    def total(profile_id: int) -> int:
        row = db.query_one("SELECT COALESCE(SUM(amount),0) t FROM xp_transactions "
                           "WHERE profile_id=?", (profile_id,))
        return max(0, row["t"])          # never negative (anti-exploit clamp)

    @staticmethod
    def on_day(profile_id: int, day: str) -> int:
        row = db.query_one("SELECT COALESCE(SUM(amount),0) t FROM xp_transactions "
                           "WHERE profile_id=? AND created_date=?", (profile_id, day))
        return row["t"]

    @staticmethod
    def between(profile_id: int, start: str, end: str) -> int:
        row = db.query_one("SELECT COALESCE(SUM(amount),0) t FROM xp_transactions "
                           "WHERE profile_id=? AND created_date BETWEEN ? AND ?",
                           (profile_id, start, end))
        return row["t"]

    @staticmethod
    def by_category(profile_id: int, category: str, start: str, end: str) -> int:
        row = db.query_one("SELECT COALESCE(SUM(amount),0) t FROM xp_transactions "
                           "WHERE profile_id=? AND category=? AND created_date BETWEEN ? AND ?",
                           (profile_id, category, start, end))
        return row["t"]

    @staticmethod
    def history(profile_id: int, limit: int = 40):
        return db.query("SELECT * FROM xp_transactions WHERE profile_id=? "
                        "ORDER BY id DESC LIMIT ?", (profile_id, limit))

    @staticmethod
    def daily_series(profile_id: int, days: int, end_day: date | None = None):
        end_day = end_day or date.today()
        out = []
        for i in range(days - 1, -1, -1):
            d = end_day.fromordinal(end_day.toordinal() - i)
            out.append((d.isoformat(), XP.on_day(profile_id, d.isoformat())))
        return out


# ------------------------------------------------------------ challenges ---
class Challenges:
    @staticmethod
    def active():
        return db.query("SELECT * FROM weekly_challenges WHERE status='active' "
                        "ORDER BY deadline")

    @staticmethod
    def all(limit: int = 20):
        return db.query("SELECT * FROM weekly_challenges ORDER BY id DESC LIMIT ?", (limit,))

    @staticmethod
    def create(title: str, description: str, mode: str, metric: str, target: float,
               xp_reward: int, start: str, deadline: str, difficulty: str = "normal",
               category: str = "Team", profile_ids: list[int] | None = None) -> int:
        if mode not in ("cooperative", "competitive"):
            raise ValueError("Challenge mode invalid.")
        if target <= 0:
            raise ValueError("Challenge target must be positive.")
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO weekly_challenges(title,description,mode,category,difficulty,"
                "xp_reward,target_value,start_date,deadline) VALUES(?,?,?,?,?,?,?,?,?)",
                (title.strip(), description, mode, category, difficulty, int(xp_reward),
                 float(target), start, deadline))
            cid = cur.lastrowid
            for pid in (profile_ids or []):
                conn.execute("INSERT OR IGNORE INTO challenge_participants(challenge_id,"
                             "profile_id) VALUES(?,?)", (cid, pid))
        return cid

    @staticmethod
    def get(cid: int):
        return db.query_one("SELECT * FROM weekly_challenges WHERE id=?", (cid,))

    @staticmethod
    def participants(cid: int):
        return db.query("SELECT cp.*, p.name FROM challenge_participants cp "
                        "JOIN profiles p ON p.id=cp.profile_id WHERE cp.challenge_id=?", (cid,))

    @staticmethod
    def contribute(cid: int, profile_id: int, amount: float) -> None:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO challenge_participants(challenge_id,profile_id,contribution) "
                "VALUES(?,?,?) ON CONFLICT(challenge_id,profile_id) "
                "DO UPDATE SET contribution=contribution+?",
                (cid, profile_id, max(0, amount), max(0, amount)))
            conn.execute("UPDATE weekly_challenges SET progress_value=progress_value+? "
                         "WHERE id=?", (max(0, amount), cid))

    @staticmethod
    def complete(cid: int, winner_id: int | None = None) -> list[int]:
        """Mark done, award XP to participants, return awarded profile ids."""
        ch = Challenges.get(cid)
        if ch is None or ch["status"] != "active":
            return []
        awarded = []
        with db.transaction() as conn:
            conn.execute("UPDATE weekly_challenges SET status='completed', winner_profile_id=? "
                         "WHERE id=?", (winner_id, cid))
            parts = conn.execute("SELECT profile_id FROM challenge_participants WHERE "
                                 "challenge_id=?", (cid,)).fetchall()
            today = date.today().isoformat()
            for p in parts:
                conn.execute("UPDATE challenge_participants SET completed=1 WHERE "
                             "challenge_id=? AND profile_id=?", (cid, p["profile_id"]))
                if ch["mode"] == "competitive" and winner_id and p["profile_id"] != winner_id:
                    continue
                conn.execute("INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                             "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                             (p["profile_id"], ch["xp_reward"],
                              f"Challenge: {ch['title']}", "Bonus", "weekly_challenges",
                              cid, today))
                awarded.append(p["profile_id"])
        return awarded

    @staticmethod
    def cancel(cid: int) -> None:
        db.execute("UPDATE weekly_challenges SET status='expired' WHERE id=?", (cid,))

    @staticmethod
    def expire_overdue() -> None:
        today = date.today().isoformat()
        db.execute("UPDATE weekly_challenges SET status='expired' WHERE status='active' "
                   "AND deadline < ?", (today,))


# ----------------------------------------------------------- achievements --
class Achievements:
    @staticmethod
    def catalogue():
        return db.query("SELECT * FROM achievements ORDER BY id")

    @staticmethod
    def unlocked(profile_id: int) -> set[str]:
        rows = db.query("SELECT achievement_key FROM achievement_unlocks WHERE profile_id=?",
                        (profile_id,))
        return {r["achievement_key"] for r in rows}

    @staticmethod
    def unlock(profile_id: int, key: str) -> bool:
        """Unlock once per profile; awards bonus XP. Returns True if newly unlocked."""
        with db.transaction() as conn:
            ach = conn.execute("SELECT * FROM achievements WHERE key=?", (key,)).fetchone()
            if ach is None:
                return False
            dup = conn.execute("SELECT id FROM achievement_unlocks WHERE achievement_key=? "
                               "AND profile_id=?", (key, profile_id)).fetchone()
            if dup:
                return False
            conn.execute("INSERT INTO achievement_unlocks(achievement_key,profile_id) "
                         "VALUES(?,?)", (key, profile_id))
            if ach["xp_bonus"] > 0:
                conn.execute("INSERT INTO xp_transactions(profile_id,amount,reason,category,"
                             "ref_table,ref_id,created_date) VALUES(?,?,?,?,?,?,?)",
                             (profile_id, ach["xp_bonus"],
                              f"Achievement: {ach['title']}", "Bonus",
                              "achievement_unlocks", 0, date.today().isoformat()))
        return True

    @staticmethod
    def recent(profile_id: int, limit: int = 5):
        return db.query(
            "SELECT a.title, a.description, a.icon, au.unlocked_at FROM achievement_unlocks "
            "au JOIN achievements a ON a.key=au.achievement_key WHERE au.profile_id=? "
            "ORDER BY au.id DESC LIMIT ?", (profile_id, limit))


# ------------------------------------------------------------- streaks -----
class Streaks:
    @staticmethod
    def get_row(profile_id: int, scope: str = "overall"):
        return db.query_one("SELECT * FROM streaks WHERE profile_id=? AND scope=?",
                            (profile_id, scope))

    @staticmethod
    def current(profile_id: int, scope: str = "overall") -> int:
        row = Streaks.get_row(profile_id, scope)
        return row["current_streak"] if row else 0

    @staticmethod
    def longest(profile_id: int, scope: str = "overall") -> int:
        row = Streaks.get_row(profile_id, scope)
        return row["longest_streak"] if row else 0

    @staticmethod
    def save(profile_id: int, scope: str, current: int, longest: int,
             last_active: str) -> None:
        db.execute(
            "INSERT INTO streaks(profile_id,scope,current_streak,longest_streak,"
            "last_active_date,updated_at) VALUES(?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(profile_id,scope) DO UPDATE SET current_streak=excluded.current_streak,"
            "longest_streak=excluded.longest_streak, last_active_date=excluded.last_active_date,"
            "updated_at=datetime('now')",
            (profile_id, scope, current, longest, last_active))


# ------------------------------------------------------------- rivalry -----
class Rivalry:
    @staticmethod
    def record_result(week_start: str, a_id: int, b_id: int, a_xp: int, b_xp: int) -> int | None:
        winner = a_id if a_xp > b_xp else (b_id if b_xp > a_xp else None)
        db.execute("INSERT INTO rivalry_results(week_start,player_a_id,player_b_id,a_xp,b_xp,"
                   "winner_id) VALUES(?,?,?,?,?,?) ON CONFLICT(week_start,player_a_id,"
                   "player_b_id) DO UPDATE SET a_xp=excluded.a_xp, b_xp=excluded.b_xp, "
                   "winner_id=excluded.winner_id", (week_start, a_id, b_id, a_xp, b_xp, winner))
        return winner

    @staticmethod
    def history(a_id: int, b_id: int, limit: int = 12):
        return db.query("SELECT * FROM rivalry_results WHERE (player_a_id=? AND player_b_id=?) "
                        "OR (player_a_id=? AND player_b_id=?) ORDER BY week_start DESC LIMIT ?",
                        (a_id, b_id, b_id, a_id, limit))

    @staticmethod
    def win_counts(a_id: int, b_id: int) -> tuple[int, int]:
        rows = db.query("SELECT winner_id FROM rivalry_results WHERE player_a_id IN (?,?) "
                        "AND player_b_id IN (?,?)", (a_id, b_id, a_id, b_id))
        aw = sum(1 for r in rows if r["winner_id"] == a_id)
        bw = sum(1 for r in rows if r["winner_id"] == b_id)
        return aw, bw
