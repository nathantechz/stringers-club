"""
Page 2 — Player Profiles
View attendance history, dues and payment history for any player.
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import skill_label, show_back_button

st.set_page_config(page_title="Player Profiles", page_icon="👤", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 👤 Player Profiles")

sb = get_client()

players_raw = sb.table("players").select("*").order("name").execute().data
if not players_raw:
    st.info("No players found. Add some on the Manage Players page.")
    st.stop()

player_name = st.selectbox("Select player", [p["name"] for p in players_raw])
player = next(p for p in players_raw if p["name"] == player_name)
p_id = player["id"]
skill = int(player.get("skill_level") or 5)

# ── Profile header ───────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
col_a.metric("Membership", player["membership_type"].title())
col_a.markdown(
    f"<span class='skill-badge'>🎾 {skill_label(skill)}</span>",
    unsafe_allow_html=True,
)
profession  = player.get("profession") or "—"
work_timing = player.get("work_timing") or "—"
col_b.markdown(f"**Profession:** {profession}")
col_b.markdown(f"**Work timing:** {work_timing}")
# Date joined + years as member
_dj = player.get("date_joined")
if _dj:
    joined = date.fromisoformat(str(_dj)[:10])
    today  = date.today()
    years  = (today - joined).days // 365
    months = ((today - joined).days % 365) // 30
    duration = f"{years} yr{'s' if years != 1 else ''} {months} mo" if years else f"{months} month{'s' if months != 1 else ''}"
    # Anniversary this year
    ann_this_year = joined.replace(year=today.year)
    if ann_this_year < today:
        ann_this_year = joined.replace(year=today.year + 1)
    days_to_ann = (ann_this_year - today).days
    ann_str = f" · 🎂 Anniversary in {days_to_ann}d" if days_to_ann <= 30 else ""
    st.markdown(
        f"<div style='margin-top:6px;padding:6px 12px;border-radius:8px;"
        f"background:rgba(217,119,6,0.08);font-size:0.87rem;'>"
        f"📅 Joined <b>{joined.strftime('%d %b %Y')}</b> &nbsp;·&nbsp; "
        f"Member for <b>{duration}</b>{ann_str}</div>",
        unsafe_allow_html=True,
    )
# ── Summary metrics ───────────────────────────────────────────────────────────
att_rows = (
    sb.table("attendance")
    .select("*")
    .eq("player_id", p_id)
    .order("session_date", desc=True)
    .execute()
    .data
)

pay_rows_all  = sb.table("payments").select("amount").eq("player_id", p_id).execute().data
total_charged = sum(r["fee_charged"] or 0 for r in att_rows)
total_paid_all = sum(r["amount"] or 0 for r in pay_rows_all)
balance_due   = max(0.0, round(total_charged - total_paid_all, 2))

c1, c2 = st.columns(2)
c1.metric("Sessions", len(att_rows))
c2.metric("Balance Due", f"₹{balance_due:,.0f}")
c3, c4 = st.columns(2)
c3.metric("Charged", f"₹{total_charged:,.0f}")
c4.metric("Paid", f"₹{total_paid_all:,.0f}")

st.divider()

# ── Date range filter ─────────────────────────────────────────────────────────
st.subheader("Attendance & fee history")
col1, col2 = st.columns(2)
from_date = col1.date_input("From", value=date(date.today().year, 1, 1))
to_date   = col2.date_input("To",   value=date.today())

filtered = [
    r for r in att_rows
    if str(from_date) <= r["session_date"] <= str(to_date)
]

if filtered:
    df = pd.DataFrame([
        {
            "Date":     r["session_date"],
            "Session":  r["session_time"].title(),
            "Monthly?": "✅" if r["is_monthly_member"] else "—",
            "Fee (₹)":  r["fee_charged"],
            "Paid (₹)": r["amount_paid"],
            "Due (₹)":  (r["fee_charged"] or 0) - (r["amount_paid"] or 0),
            "Notes":    r["notes"] or "",
        }
        for r in filtered
    ])
    total_due_filtered = df["Due (₹)"].sum()
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total due in range: ₹{total_due_filtered:,.2f}**")
else:
    st.info("No attendance records in this range.")

st.divider()

# ── Payment history ───────────────────────────────────────────────────────────
st.subheader("Payment history")
pay_rows = (
    sb.table("payments")
    .select("*")
    .eq("player_id", p_id)
    .order("payment_date", desc=True)
    .execute()
    .data
)

if pay_rows:
    pay_df = pd.DataFrame([
        {
            "Date":          r["payment_date"],
            "Amount (₹)":    r["amount"],
            "Method / Notes": r["notes"] or "",
        }
        for r in pay_rows
    ])
    st.dataframe(pay_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total payments recorded: ₹{sum(r['amount'] for r in pay_rows):,.2f}**")
else:
    st.info("No payments recorded yet.")
