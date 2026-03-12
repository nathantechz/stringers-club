# 🏸 Badminton Pro Hub

A **Playo-style** badminton club management app built with **Streamlit** + **Supabase**.

## Features

- **Join Games** — Players browse upcoming sessions and request to join
- **Coach Dashboard** — Accept/reject requests, send private invites, add coach notes, create sessions
- **My Profile** — Player stats, session history, payment history, balance due
- **Manage Players** — Add/edit players with roles, skill levels, and avatar emojis
- **Payments** — Record payments with auto-distribution to unpaid sessions (FIFO)
- **Analytics** — Attendance trends, revenue charts, leaderboard, outstanding dues
- **Expenditure** — Track club expenses by category

## The Playo Workflow

1. **Coaches** create upcoming sessions (date, slot, courts, fee, max players)
2. **Players** browse sessions and click "Request to Join" — status becomes `pending`
3. **Coaches** see pending requests and can "Accept All" or individually accept/reject
4. **Coaches** can also send **private invites** to specific players — status becomes `invited`
5. **Players** see invites and can accept or decline

## Setup

1. Create a Supabase project and run `schema_v4.sql` in the SQL Editor
2. Add your credentials to `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   streamlit run app.py
   ```

## Database Schema

- `players` — name, phone, role (player/coach/admin), skill_level, avatar_emoji
- `sessions` — date, slot (morning/evening), court_nos, max_players, fee_per_player
- `attendance` — session_id, player_id, status (pending/confirmed/rejected/invited), coach_note
- `payments` — player_id, amount, payment_date, notes
- `expenditures` — date, category, amount, notes
- `session_slots` (view) — sessions with slots_left, confirmed_count, pending_count
- `player_balance` (view) — per-player totals: charged, paid, balance_due, games_played
