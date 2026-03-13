-- ============================================================
-- Migration v5 — Run this in Supabase SQL Editor
-- ============================================================

-- 1. Create fee_audit_log table (was missing)
CREATE TABLE IF NOT EXISTS fee_audit_log (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    attendance_id  UUID REFERENCES attendance(id) ON DELETE CASCADE,
    player_id      UUID REFERENCES players(id) ON DELETE CASCADE,
    session_id     UUID REFERENCES sessions(id) ON DELETE CASCADE,
    action         TEXT NOT NULL
                       CHECK (action IN ('fee_set', 'fee_updated', 'payment_recorded', 'payment_reversed')),
    old_value      NUMERIC(10,2),
    new_value      NUMERIC(10,2),
    changed_by     TEXT,
    notes          TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS and allow all authenticated reads/writes (coach-controlled)
ALTER TABLE fee_audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all_fee_audit_log" ON fee_audit_log FOR ALL USING (true) WITH CHECK (true);

-- 2. Drop the slot CHECK constraint so any time string (e.g. "08:30 AM") is allowed
--    First find and drop the constraint
DO $$
BEGIN
    -- Drop the old CHECK constraint on slot
    ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_slot_check;
    -- Drop the UNIQUE(date, slot) constraint so multiple sessions can exist same day
    ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_date_slot_key;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Constraint drop skipped: %', SQLERRM;
END $$;

-- 3. Add password_hash column to players if missing
ALTER TABLE players ADD COLUMN IF NOT EXISTS password_hash TEXT;
