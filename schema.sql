-- ============================================================
-- StringerS Badminton Club — Supabase Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Players
CREATE TABLE IF NOT EXISTS players (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL UNIQUE,
    membership_type TEXT NOT NULL DEFAULT 'regular'
                    CHECK (membership_type IN ('regular', 'monthly')),
    monthly_fee NUMERIC(10,2),          -- only used for monthly members
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Monthly fee configuration (per player, per month)
CREATE TABLE IF NOT EXISTS monthly_fee_config (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id   UUID REFERENCES players(id) ON DELETE CASCADE,
    month       TEXT NOT NULL,           -- format: 'YYYY-MM'
    monthly_fee NUMERIC(10,2) NOT NULL,
    UNIQUE(player_id, month)
);

-- Attendance
CREATE TABLE IF NOT EXISTS attendance (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id     UUID REFERENCES players(id) ON DELETE CASCADE,
    session_date  DATE NOT NULL,
    session_time  TEXT NOT NULL CHECK (session_time IN ('morning', 'evening')),
    fee_charged   NUMERIC(10,2) DEFAULT 0,   -- 0 for monthly members until settlement
    amount_paid   NUMERIC(10,2) DEFAULT 0,
    is_monthly_member BOOLEAN DEFAULT FALSE, -- snapshot at time of attendance
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(player_id, session_date, session_time)
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id     UUID REFERENCES players(id) ON DELETE CASCADE,
    amount        NUMERIC(10,2) NOT NULL,
    payment_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Junction: which attendance rows does a payment cover
CREATE TABLE IF NOT EXISTS payment_attendance (
    payment_id    UUID REFERENCES payments(id) ON DELETE CASCADE,
    attendance_id UUID REFERENCES attendance(id) ON DELETE CASCADE,
    applied_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (payment_id, attendance_id)
);

-- ============================================================
-- Helpful views
-- ============================================================

-- Player balance summary
CREATE OR REPLACE VIEW player_balance AS
SELECT
    p.id,
    p.name,
    p.phone,
    p.membership_type,
    COALESCE(SUM(a.fee_charged), 0)  AS total_charged,
    COALESCE(SUM(a.amount_paid), 0)  AS total_paid,
    COALESCE(SUM(a.fee_charged - a.amount_paid), 0) AS balance_due
FROM players p
LEFT JOIN attendance a ON a.player_id = p.id
GROUP BY p.id, p.name, p.phone, p.membership_type;

-- Enable Row Level Security (optional — disable for local dev)
-- ALTER TABLE players ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
