"""
Page 1 — Mark Attendance
Search for players who attended a session, set fee (for regular members).
Monthly members are marked with ₹0 fee until monthly settlement.
"""

import streamlit as st
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Mark Attendance", page_icon="📋", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 📋 Mark Attendance")

sb = get_client()

# ── Session selector ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
session_date = col1.date_input("Date", value=date.today())
session_time = col2.selectbox("Session", ["morning (7–8 AM)", "evening (7–8 PM)"])
session_key  = "morning" if "morning" in session_time else "evening"

st.divider()

# ── Load active players ───────────────────────────────────────────────────────
players_raw = sb.table("players").select("*").eq("is_active", True).order("name").execute().data
players = {p["name"]: p for p in players_raw}

# Show already-marked players for this session
existing = (
    sb.table("attendance")
    .select("player_id, fee_charged, amount_paid")
    .eq("session_date", str(session_date))
    .eq("session_time", session_key)
    .execute()
    .data
)
already_marked_ids = {r["player_id"] for r in existing}

# ── Player search & attendance form ──────────────────────────────────────────
st.subheader(f"Add player — {session_date.strftime('%A, %d %b %Y')} · {session_time}")

# Player selector lives outside the form so membership type can adapt the UI
player_name = st.selectbox(
    "Search player",
    options=["— Select —"] + list(players.keys()),
)
_sel = players.get(player_name)
_is_monthly_sel = _sel["membership_type"] == "monthly" if _sel else False

with st.form("mark_attendance_form", clear_on_submit=True):
    if _is_monthly_sel:
        st.info("🏷️ Monthly member — fee will be settled at month-end. No per-session charge.")
        fee = 0.0
    else:
        fee = st.number_input(
            "Fee for this session (₹)",
            min_value=0.0,
            step=10.0,
            value=0.0,
        )
    notes = st.text_input("Notes (optional)")
    submitted = st.form_submit_button("✅ Mark Attendance")

    if submitted:
        if player_name == "— Select —":
            st.error("Please select a player.")
        else:
            player = players[player_name]
            p_id = player["id"]

            if p_id in already_marked_ids:
                st.warning(f"{player_name} is already marked for this session.")
            else:
                is_monthly = player["membership_type"] == "monthly"
                row = {
                    "player_id":        p_id,
                    "session_date":     str(session_date),
                    "session_time":     session_key,
                    "fee_charged":      0.0 if is_monthly else float(fee),
                    "amount_paid":      0.0,
                    "is_monthly_member": is_monthly,
                    "notes":            notes or None,
                }
                sb.table("attendance").insert(row).execute()

                label = "Monthly Member — settle at end of month" if is_monthly else f"₹{fee:.2f} due"
                st.success(f"✅ {player_name} marked present. {label}")

st.divider()

# ── Already marked for this session ──────────────────────────────────────────
st.subheader(f"Already marked for this session ({len(already_marked_ids)} players)")

if existing:
    # Fetch full attendance rows (need the id to delete)
    existing_full = (
        sb.table("attendance")
        .select("id, player_id, fee_charged, amount_paid")
        .eq("session_date", str(session_date))
        .eq("session_time", session_key)
        .execute()
        .data
    )
    pid_to_name = {p["id"]: p["name"] for p in players_raw}
    for r in existing_full:
        pname   = pid_to_name.get(r["player_id"], "Unknown")
        fee_c   = r["fee_charged"] or 0
        paid    = r["amount_paid"] or 0
        due     = round(fee_c - paid, 2)
        status  = "✅ Cleared" if due <= 0 else f"⚠️ Due ₹{due:.0f}"

        with st.container(border=True):
            ca, cb = st.columns([4, 1])
            ca.markdown(f"**{pname}**")
            ca.caption(f"Fee ₹{fee_c:.0f}  ·  Paid ₹{paid:.0f}  ·  {status}")
            if cb.button("🗑️", key=f"del_att_{r['id']}", help="Remove this attendance record"):
                # Reverse amount_paid via linked payments before deleting
                linked = sb.table("payment_attendance") \
                    .select("payment_id, applied_amount") \
                    .eq("attendance_id", r["id"]).execute().data
                for lnk in linked:
                    pay = sb.table("payments").select("amount").eq("id", lnk["payment_id"]).execute().data
                    if pay:
                        new_amt = max(0.0, round((pay[0]["amount"] or 0) - (lnk["applied_amount"] or 0), 2))
                        sb.table("payments").update({"amount": new_amt}).eq("id", lnk["payment_id"]).execute()
                sb.table("payment_attendance").delete().eq("attendance_id", r["id"]).execute()
                sb.table("attendance").delete().eq("id", r["id"]).execute()
                st.success(f"🗑️ {pname} removed from this session.")
                st.rerun()
else:
    st.info("No players marked yet for this session.")
