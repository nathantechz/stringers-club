-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v3: Add date_joined to players table
-- Run this in Supabase Dashboard → SQL Editor
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS date_joined DATE DEFAULT CURRENT_DATE;
