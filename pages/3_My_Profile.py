import streamlit as st
from datetime import date as dt_date

from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, status_badge
from utils.auth import login_gate
from utils.supabase_client import fetch_all, get_client

st.set_page_config(page_title="My Activities | StringerS", page_icon="🗓️", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

st.title("🗓️ My Activities")

player_id = current["id"]

try:
    attendance = (
        get_client()
        .table("attendance")
        .select("id, status, fee_charged, amount_paid, coach_note, session:sessions(id, date, slot, venue, court_numbers)")
        .eq("player_id", player_id)
        .execute().data
    )
except Exception:
    # Fallback for projects where embedded relation metadata is unavailable.
    try:
        attendance_rows = (
            get_client()
            .table("attendance")
            .select("id, status, fee_charged, amount_paid, coach_note, session_id")
            .eq("player_id", player_id)
            .execute().data
        )
    except Exception:
        attendance_rows = []
    session_ids = [r.get("session_id") for r in attendance_rows if r.get("session_id")]
    sessions_map = {}
    if session_ids:
        sessions = (
            get_client()
            .table("sessions")
            .select("id, date, slot, venue, court_numbers")
            .in_("id", session_ids)
            .execute().data
        )
        sessions_map = {s["id"]: s for s in sessions}

    attendance = []
    for r in attendance_rows:
        row = dict(r)
        row["session"] = sessions_map.get(r.get("session_id"), {})
        attendance.append(row)

# Sort consistently by session date (latest first) without relying on DB order columns.
attendance.sort(key=lambda a: str((a.get("session", {}) or {}).get("date", "")), reverse=True)

if not attendance:
    st.info("No activities yet. Go to Games and join a hosted activity.")
    bottom_nav("3_My_Profile.py")
    st.stop()

today = str(dt_date.today())
future_rows, past_rows = [], []
for row in attendance:
    sess = row.get("session", {}) or {}
    sdate = str(sess.get("date", ""))
    if sdate and sdate >= today:
        future_rows.append(row)
    else:
        past_rows.append(row)

c1, c2, c3 = st.columns(3)
c1.metric("Future", len(future_rows))
c2.metric("Past", len(past_rows))
c3.metric("Activities", len(attendance))

st.divider()

f_tab, p_tab, pay_tab = st.tabs(["⏭️ Future Activities", "🕘 Past Activities", "💳 My Payments"])

with f_tab:
    if not future_rows:
        st.info("No upcoming activities yet.")
    else:
        for a in future_rows:
            sess = a.get("session", {}) or {}
            due = float(a.get("fee_charged", 0)) - float(a.get("amount_paid", 0))
            due_html = f' &nbsp; <span class="badge-due">₹{due:.0f} due</span>' if due > 0 else ""
            st.markdown(
                f"""
                <div class="game-card">
                    <strong>{sess.get('date', '?')} • {sess.get('slot', '?')}</strong>
                    &nbsp; {status_badge(a.get('status', 'pending'))}{due_html}
                    <br>📍 {sess.get('venue', '?')} Court {sess.get('court_numbers', '?')}
                </div>
                """,
                unsafe_allow_html=True,
            )

with p_tab:
    if not past_rows:
        st.info("No past activities yet.")
    else:
        for a in past_rows:
            sess = a.get("session", {}) or {}
            fee = float(a.get("fee_charged", 0))
            paid = float(a.get("amount_paid", 0))
            note = a.get("coach_note")
            note_html = f"<br>💬 <em>{note}</em>" if note else ""
            st.markdown(
                f"""
                <div class="game-card">
                    <strong>{sess.get('date', '?')} • {sess.get('slot', '?')}</strong>
                    &nbsp; {status_badge(a.get('status', 'pending'))}
                    <br>📍 {sess.get('venue', '?')} Court {sess.get('court_numbers', '?')}
                    <br>Fee: ₹{fee:.0f} &nbsp;|&nbsp; Paid: ₹{paid:.0f}{note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

with pay_tab:
    my_payments = fetch_all("payments", filters={"player_id": player_id}, order="payment_date")
    if not my_payments:
        st.info("No payments recorded yet.")
    else:
        for pay in reversed(my_payments):
            st.markdown(
                f"""
                <div class="player-card">
                    <div class="player-avatar">💵</div>
                    <div class="player-info">
                        <div class="name">₹{pay['amount']:.0f}</div>
                        <div class="sub">{pay['payment_date']}{' — ' + pay['notes'] if pay.get('notes') else ''}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

bottom_nav("3_My_Profile.py")
