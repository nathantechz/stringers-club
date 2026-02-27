-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: Add skill_level, profession, work_timing to players
--            Create expenditures table
-- Run this in Supabase Dashboard → SQL Editor
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. New columns on players table
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS skill_level   INTEGER DEFAULT 5 CHECK (skill_level BETWEEN 1 AND 10),
    ADD COLUMN IF NOT EXISTS profession    TEXT,
    ADD COLUMN IF NOT EXISTS work_timing   TEXT;

-- 2. Expenditures table
CREATE TABLE IF NOT EXISTS expenditures (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exp_date    DATE NOT NULL,
    category    TEXT NOT NULL,          -- 'Court booking' | 'Shuttles' | 'Equipment' | 'Other'
    amount      NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast monthly queries
CREATE INDEX IF NOT EXISTS idx_expenditures_date ON expenditures (exp_date);
