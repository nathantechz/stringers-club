"""
Page 5 — Monthly Dues
• Top section: Set / review monthly fees for ALL monthly members for a chosen month
  (pre-filled from each player's default fee, editable per player).
• Bottom section: Distribute a player's monthly fee across their attended sessions.
"""

import streamlit as st
import pandas as pd
from datetime import date
import calendar
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Monthly Dues", page_icon="📅", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 📅 Monthly Dues")
st.caption("Configure what each monthly member owes, and distribute fees across attended sessions.")

sb = get_client()

# ── Month selector (shared for both sections) ─────────────────────────────────
today = date.today()
month_options = sorted(
    {f"{today.year}-{m:02d}" for m in range(1, today.month + 1)}
    | {f"{today.year - 1}-{m:02d}" for m in range(1, 13)},
    reverse=True,
)
selected_month = st.selectbox("Month", month_options)
year, mon      = map(int, selected_month.split("-"))
from_date      = f"{selected_month}-01"
last_day       = calendar.monthrange(year, mon)[1]
to_date        = f"{selected_month}-{last_day:02d}"

st.divider()

# ── All monthly members ───────────────────────────────────────────────────────
monthly_players = (
    sb.table("players")
    .select("*")
    .eq("membership_type", "monthly")
    .eq("is_active", True)
    .order("name")
    .execute()
    .data
)

if not monthly_players:
    st.warning("No active monthly members found. Add them on the Manage Players page.")
    st.stop()

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — Set monthly dues for all members (start of month)
# ════════════════════════════════════════════════════════════════════
st.subheader(f"📌 Monthly dues — {selected_month}")
st.caption("Set each player's fee for this month. Pre-filled from their default fee. Edit as needed, then save.")

# Fetch existing fee configs for this month for all players
existing_configs = (
    sb.table("monthly_fee_config")
    .select("*")
    .eq("month", selected_month)
    .execute()
    .data
)
config_by_pid = {r["player_id"]: r["monthly_fee"] for r in existing_configs}

with st.form("set_monthly_dues_form"):
    fee_inputs = {}
    for p in monthly_players:
        pid = p["id"]
        default = config_by_pid.get(pid, p.get("monthly_fee") or 0.0)
        fee_inputs[pid] = st.number_input(
            f"{p['name']}",
            min_value=0.0,
            step=100.0,
            value=float(default),
            key=f"mfee_{pid}",
        )

    save_dues = st.form_submit_button("💾 Save Monthly Dues", type="primary")

    if save_dues:
        for p in monthly_players:
            pid  = p["id"]
            fval = fee_inputs[pid]
            row  = {"player_id": pid, "month": selected_month, "monthly_fee": fval}
            if pid in config_by_pid:
                sb.table("monthly_fee_config").update(row).eq("player_id", pid).eq("month", selected_month).execute()
            else:
                sb.table("monthly_fee_config").insert(row).execute()
        st.success(f"✅ Monthly dues saved for {selected_month}.")
        st.rerun()

# Summary table
st.markdown("**Current dues for this month:**")
# Fetch all attendance for this month in one query, then aggregate per player
all_att_month = (
    sb.table("attendance")
    .select("player_id, fee_charged, amount_paid")
    .gte("session_date", from_date)
    .lte("session_date", to_date)
    .execute()
    .data
)
att_count_by_pid = {}
att_paid_by_pid  = {}
for r in all_att_month:
    pid = r["player_id"]
    att_count_by_pid[pid] = att_count_by_pid.get(pid, 0) + 1
    att_paid_by_pid[pid]  = att_paid_by_pid.get(pid, 0) + (r["amount_paid"] or 0)

summary_rows = []
for p in monthly_players:
    pid           = p["id"]
    monthly_fee   = config_by_pid.get(pid, p.get("monthly_fee") or 0.0)
    att_count     = att_count_by_pid.get(pid, 0)
    paid          = att_paid_by_pid.get(pid, 0.0)
    summary_rows.append({
        "Player":          p["name"],
        "Monthly Fee (₹)": monthly_fee,
        "Sessions":        att_count,
        "Paid (₹)":        paid,
        "Due (₹)":         round(monthly_fee - paid, 2),
        "Configured":      "✅" if pid in config_by_pid else "⚠️ Not set",
    })

st.dataframe(summary_rows, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — Distribute fee across attended sessions (end of month)
# ════════════════════════════════════════════════════════════════════
st.subheader("⚡ Distribute fee across sessions")
st.caption("Run at end of month. Splits the monthly fee equally across all sessions the player attended.")

player_name = st.selectbox("Player", [p["name"] for p in monthly_players], key="dist_player")
player      = next(p for p in monthly_players if p["name"] == player_name)
p_id        = player["id"]

att_rows = (
    sb.table("attendance")
    .select("*")
    .eq("player_id", p_id)
    .gte("session_date", from_date)
    .lte("session_date", to_date)
    .order("session_date")
    .execute()
    .data
)

if not att_rows:
    st.info(f"{player_name} has no attendance recorded in {selected_month}.")
else:
    df_preview = pd.DataFrame([
        {
            "Date":              r["session_date"],
            "Session":           r["session_time"].title(),
            "Fee charged (₹)":   r["fee_charged"],
            "Paid (₹)":          r["amount_paid"],
        }
        for r in att_rows
    ])
    st.dataframe(df_preview, use_container_width=True, hide_index=True)

    # Use this month's saved fee config (or player default)
    fee_conf = (
        sb.table("monthly_fee_config")
        .select("*")
        .eq("player_id", p_id)
        .eq("month", selected_month)
        .execute()
        .data
    )
    existing_fee   = fee_conf[0]["monthly_fee"] if fee_conf else (player.get("monthly_fee") or 0.0)
    monthly_fee_amount = st.number_input(
        f"Monthly fee for {player_name} in {selected_month} (₹)",
        min_value=0.0, step=100.0, value=float(existing_fee),
        key="dist_fee",
    )
    per_session = monthly_fee_amount / len(att_rows) if att_rows else 0
    st.markdown(f"**Per-session share: ₹{per_session:.2f}** (÷ {len(att_rows)} sessions)")

    if st.button("⚡ Apply Distribution", type="primary"):
        if monthly_fee_amount <= 0:
            st.error("Monthly fee must be > ₹0.")
        else:
            # Upsert fee config
            cfg_row = {"player_id": p_id, "month": selected_month, "monthly_fee": monthly_fee_amount}
            if fee_conf:
                sb.table("monthly_fee_config").update(cfg_row).eq("player_id", p_id).eq("month", selected_month).execute()
            else:
                sb.table("monthly_fee_config").insert(cfg_row).execute()

            per_session_rounded = round(per_session, 2)
            for r in att_rows:
                sb.table("attendance").update({"fee_charged": per_session_rounded}).eq("id", r["id"]).execute()

            all_att = sb.table("attendance").select("fee_charged, amount_paid").eq("player_id", p_id).execute().data
            balance = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in all_att)

            st.success(
                f"✅ Done. {len(att_rows)} sessions × ₹{per_session_rounded:.2f} = "
                f"₹{monthly_fee_amount:.2f}. Overall balance due: ₹{balance:.2f}"
            )
            st.rerun()

