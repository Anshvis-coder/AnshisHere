-- DEMONBACK X — SQLite schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    avatar_color TEXT DEFAULT '#DC143C',
    goals TEXT DEFAULT '',
    pin_hash TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Mental',   -- Mental | Physical | Discipline
    frequency TEXT NOT NULL DEFAULT 'daily',   -- daily | weekly
    target_count INTEGER NOT NULL DEFAULT 1,   -- completions needed per period
    target_quantity REAL DEFAULT 0,            -- optional measurable target (min/ml/reps)
    target_unit TEXT DEFAULT '',
    xp_reward INTEGER NOT NULL DEFAULT 10,
    partial_allowed INTEGER NOT NULL DEFAULT 0,
    start_date TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_habits_profile ON habits(profile_id, archived);

CREATE TABLE IF NOT EXISTS habit_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    weekday INTEGER NOT NULL                 -- 0=Mon .. 6=Sun (for daily habits on chosen days)
);
CREATE INDEX IF NOT EXISTS idx_sched_habit ON habit_schedules(habit_id);

CREATE TABLE IF NOT EXISTS daily_missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    mission_date TEXT NOT NULL,              -- YYYY-MM-DD local calendar date
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'Discipline',
    difficulty TEXT DEFAULT 'normal',        -- easy | normal | hard
    xp_reward INTEGER NOT NULL DEFAULT 15,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | done | skipped | postponed
    deadline TEXT DEFAULT '',
    source TEXT DEFAULT 'generated',         -- generated | manual | challenge
    challenge_id INTEGER DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(profile_id, mission_date, title, source)
);
CREATE INDEX IF NOT EXISTS idx_missions_profile_date ON daily_missions(profile_id, mission_date);

CREATE TABLE IF NOT EXISTS completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
    completion_date TEXT NOT NULL,           -- scheduled local date
    quantity REAL DEFAULT 1,
    is_partial INTEGER NOT NULL DEFAULT 0,
    note TEXT DEFAULT '',
    xp_awarded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(profile_id, habit_id, completion_date)  -- prevents duplicate rewards per day
);
CREATE INDEX IF NOT EXISTS idx_completions_lookup ON completions(profile_id, completion_date);

CREATE TABLE IF NOT EXISTS focus_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    session_date TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    planned_minutes INTEGER NOT NULL,
    actual_minutes INTEGER NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0,    -- finished normally
    interrupted INTEGER NOT NULL DEFAULT 0,  -- stopped early / app restart
    kind TEXT NOT NULL DEFAULT 'focus',      -- focus | pomodoro | study | reading
    label TEXT DEFAULT '',
    xp_awarded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_focus_profile ON focus_sessions(profile_id, session_date);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    session_date TEXT NOT NULL,
    exercise TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'strength',   -- strength | cardio | walk | mobility | stretch | recovery
    duration_minutes INTEGER NOT NULL DEFAULT 0,
    sets INTEGER DEFAULT 0,
    reps INTEGER DEFAULT 0,
    load_note TEXT DEFAULT '',
    distance_km REAL DEFAULT 0,
    notes TEXT DEFAULT '',
    xp_awarded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_workout_profile ON workout_sessions(profile_id, session_date);

CREATE TABLE IF NOT EXISTS hydration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    amount_ml INTEGER NOT NULL,
    UNIQUE(profile_id, log_date)
);

CREATE TABLE IF NOT EXISTS streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    scope TEXT NOT NULL DEFAULT 'overall',   -- overall | mental | physical | discipline
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_active_date TEXT DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(profile_id, scope)
);

CREATE TABLE IF NOT EXISTS weekly_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    mode TEXT NOT NULL DEFAULT 'cooperative',-- cooperative | competitive
    category TEXT DEFAULT 'Team',
    difficulty TEXT DEFAULT 'normal',
    xp_reward INTEGER NOT NULL DEFAULT 50,
    target_value REAL NOT NULL DEFAULT 1,    -- shared goal or per-player target
    progress_value REAL NOT NULL DEFAULT 0,
    metric TEXT NOT NULL DEFAULT 'xp',       -- xp | sessions | workouts | completions
    start_date TEXT NOT NULL,
    deadline TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',   -- active | completed | expired
    winner_profile_id INTEGER DEFAULT NULL REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS challenge_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id INTEGER NOT NULL REFERENCES weekly_challenges(id) ON DELETE CASCADE,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    contribution REAL NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(challenge_id, profile_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    icon TEXT DEFAULT '*',
    xp_bonus INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS achievement_unlocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_key TEXT NOT NULL REFERENCES achievements(key) ON DELETE CASCADE,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(achievement_key, profile_id)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    entry_date TEXT NOT NULL,
    mood INTEGER DEFAULT 5,                  -- 1..10 self-reported
    reflection TEXT NOT NULL DEFAULT '',
    distractions TEXT DEFAULT '',
    wins TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(profile_id, entry_date)
);

CREATE TABLE IF NOT EXISTS xp_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Mental', -- Mental | Physical | Discipline | Bonus
    ref_table TEXT DEFAULT '',
    ref_id INTEGER DEFAULT 0,
    created_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_xp_profile_date ON xp_transactions(profile_id, created_date);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rivalry_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,                -- Monday date YYYY-MM-DD
    player_a_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    player_b_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    a_xp INTEGER NOT NULL DEFAULT 0,
    b_xp INTEGER NOT NULL DEFAULT 0,
    winner_id INTEGER DEFAULT NULL REFERENCES profiles(id) ON DELETE SET NULL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(week_start, player_a_id, player_b_id)
);
