-- ============================================================
-- StringerS Badminton Club — Playo-Style Schema (v4)
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Drop old objects (careful: destroys existing data)
DROP VIEW  IF EXISTS player_balance CASCADE;
DROP TABLE IF EXISTS payment_attendance CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS monthly_fee_config CASCADE;
DROP TABLE IF EXISTS expenditures CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

-- ============================================================
-- Players
-- ============================================================
CREATE TABLE players (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name          TEXT NOT NULL,
    phone         TEXT NOT NULL UNIQUE,
    password_hash TEXT,                     -- PBKDF2 hash set by coach
    role          TEXT NOT NULL DEFAULT 'player'
                      CHECK (role IN ('player', 'coach', 'admin')),
    skill_level   INTEGER DEFAULT 5 CHECK (skill_level BETWEEN 1 AND 10),
    avatar_emoji  TEXT DEFAULT '🏸',
    is_active     BOOLEAN DEFAULT TRUE,
    date_joined   DATE DEFAULT CURRENT_DATE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Sessions  (a coach/admin creates upcoming game slots)
-- ============================================================
CREATE TABLE sessions (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date           DATE NOT NULL,
    slot           TEXT NOT NULL CHECK (slot IN ('morning', 'evening')),
    venue          TEXT NOT NULL DEFAULT 'Pro-Sports'
                       CHECK (venue IN ('Pro-Sports', 'Hermes')),
    num_courts     INTEGER NOT NULL DEFAULT 1 CHECK (num_courts >= 1),
    court_numbers  TEXT NOT NULL DEFAULT '1',   -- e.g. '1' or '2,3' or '1,5'
    max_players    INTEGER DEFAULT 8,
    fee_per_player NUMERIC(10,2) DEFAULT 0,
    notes          TEXT,
    created_by     UUID REFERENCES players(id),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, slot)
);

-- ============================================================
-- Attendance (the request / invite / confirm flow)
-- ============================================================
CREATE TABLE attendance (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id    UUID REFERENCES sessions(id) ON DELETE CASCADE,
    player_id     UUID REFERENCES players(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'confirmed', 'rejected', 'invited')),
    fee_charged   NUMERIC(10,2) DEFAULT 0,
    amount_paid   NUMERIC(10,2) DEFAULT 0,
    coach_note    TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, player_id)
);

-- ============================================================
-- Payments
-- ============================================================
CREATE TABLE payments (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id     UUID REFERENCES players(id) ON DELETE CASCADE,
    amount        NUMERIC(10,2) NOT NULL,
    payment_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Expenditures
-- ============================================================
CREATE TABLE expenditures (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date          DATE NOT NULL DEFAULT CURRENT_DATE,
    category      TEXT NOT NULL,
    amount        NUMERIC(10,2) NOT NULL,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Fee / Payment Audit Log  (perfect trail of every change)
-- ============================================================
CREATE TABLE fee_audit_log (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    attendance_id  UUID REFERENCES attendance(id) ON DELETE CASCADE,
    player_id      UUID REFERENCES players(id) ON DELETE CASCADE,
    session_id     UUID REFERENCES sessions(id) ON DELETE CASCADE,
    action         TEXT NOT NULL
                       CHECK (action IN ('fee_set', 'fee_updated', 'payment_recorded', 'payment_reversed')),
    old_value      NUMERIC(10,2),
    new_value      NUMERIC(10,2),
    changed_by     TEXT,           -- name or role of who made the change
    notes          TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Player Ratings (coach rates players per skill dimension)
-- ============================================================
CREATE TABLE ratings (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id     UUID REFERENCES players(id) ON DELETE CASCADE,
    rated_by      UUID REFERENCES players(id),
    footwork      INTEGER NOT NULL CHECK (footwork   BETWEEN 1 AND 10),
    stamina       INTEGER NOT NULL CHECK (stamina    BETWEEN 1 AND 10),
    smash_power   INTEGER NOT NULL CHECK (smash_power BETWEEN 1 AND 10),
    net_play      INTEGER NOT NULL CHECK (net_play   BETWEEN 1 AND 10),
    rated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(player_id, rated_by)
);

-- ============================================================
-- Helpful views
-- ============================================================

-- Slots left per session (includes venue + court info)
CREATE OR REPLACE VIEW session_slots AS
SELECT
    s.*,
    s.max_players - COUNT(a.id) FILTER (WHERE a.status = 'confirmed') AS slots_left,
    COUNT(a.id) FILTER (WHERE a.status = 'confirmed') AS confirmed_count,
    COUNT(a.id) FILTER (WHERE a.status = 'pending')   AS pending_count
FROM sessions s
LEFT JOIN attendance a ON a.session_id = s.id
GROUP BY s.id;

-- Player balance summary
-- Balance = (confirmed sessions × fee_per_player) − sum of payments
CREATE OR REPLACE VIEW player_balance AS
SELECT
    p.id,
    p.name,
    p.phone,
    p.skill_level,
    COUNT(a.id) FILTER (WHERE a.status = 'confirmed')                   AS games_played,
    COALESCE(SUM(s.fee_per_player) FILTER (WHERE a.status = 'confirmed'), 0) AS total_charged,
    COALESCE(pay.total_paid, 0)                                          AS total_paid,
    COALESCE(SUM(s.fee_per_player) FILTER (WHERE a.status = 'confirmed'), 0)
        - COALESCE(pay.total_paid, 0)                                    AS balance_due
FROM players p
LEFT JOIN attendance a ON a.player_id = p.id
LEFT JOIN sessions   s ON s.id = a.session_id
LEFT JOIN (
    SELECT player_id, SUM(amount) AS total_paid
    FROM payments
    GROUP BY player_id
) pay ON pay.player_id = p.id
GROUP BY p.id, p.name, p.phone, p.skill_level, pay.total_paid;
