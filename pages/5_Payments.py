import streamlit as st

from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, is_coach_view
from utils.auth import login_gate
from utils.supabase_client import fetch_all, get_client, record_payment_with_audit

st.set_page_config(page_title="Payments | StringerS", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()
is_coach = is_coach_view()

if is_coach:
    st.title("💳 Player Payments")
    players = fetch_all("players", filters={"is_active": True}, order="name")
    if not players:
        st.info("No active players.")
        bottom_nav("5_Payments.py")
        st.stop()

    selected = st.selectbox(
        "Player",
        options=players,
        format_func=lambda p: f"{p.get('avatar_emoji', '🏸')} {p['name']}",
    )
    selected_player_id = selected["id"]
else:
    st.title("💳 Submit Payment Proof")
    selected_player_id = current["id"]

try:
    unpaid = (
        get_client().table("attendance")
        .select("id, fee_charged, amount_paid, session_id, session:sessions(date, slot, venue, court_numbers)")
        .eq("player_id", selected_player_id)
        .eq("status", "confirmed")
        .execute().data
    )
except Exception:
    # Fallback: some Supabase projects may not have embedded relation metadata cached.
    attendance_rows = (
        get_client().table("attendance")
        .select("id, fee_charged, amount_paid, session_id")
        .eq("player_id", selected_player_id)
        .eq("status", "confirmed")
        .execute().data
    )
    session_ids = [r.get("session_id") for r in attendance_rows if r.get("session_id")]
    sessions_map = {}
    if session_ids:
        sessions = (
            get_client().table("sessions")
            .select("id, date, slot, venue, court_numbers")
            .in_("id", session_ids)
            .execute().data
        )
        sessions_map = {s["id"]: s for s in sessions}
    unpaid = []
    for r in attendance_rows:
        row = dict(r)
        row["session"] = sessions_map.get(r.get("session_id"), {})
        unpaid.append(row)
unpaid = [u for u in unpaid if (u.get("fee_charged", 0) - u.get("amount_paid", 0)) > 0]

if unpaid:
    st.markdown("**Unpaid activities:**")
    total_due = 0.0
    for u in unpaid:
        s = u.get("session", {})
        due = u["fee_charged"] - u["amount_paid"]
        total_due += due
        venue = s.get("venue", "")
        courts = s.get("court_numbers", "")
        loc = f" — 📍 {venue} Court {courts}" if venue else ""
        st.markdown(
            f"- {s.get('date', '?')} {s.get('slot', '?')}{loc} — "
            f"₹{u['fee_charged']:.0f} charged, ₹{u['amount_paid']:.0f} paid, "
            f'<span class="badge-due">₹{due:.0f} due</span>',
            unsafe_allow_html=True,
        )
    st.markdown(f"**Total due: ₹{total_due:.0f}**")
else:
    if is_coach:
        st.success(f"{selected['name']} has no unpaid sessions!")
    else:
        st.success("You have no unpaid activities.")

st.divider()

with st.form("payment_form", clear_on_submit=True):
    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    pay_date = st.date_input("Payment Date")
    notes = st.text_input("Payment Proof / UTR / Note")

    if st.form_submit_button("💰 Submit Payment"):
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        elif not unpaid:
            st.warning("No unpaid activities found.")
        else:
            remaining = float(amount)
            for u in sorted(unpaid, key=lambda x: (x.get("session", {}) or {}).get("date", "")):
                if remaining <= 0:
                    break
                due = u["fee_charged"] - u["amount_paid"]
                apply_amt = min(remaining, due)
                record_payment_with_audit(
                    attendance_id=u["id"],
                    session_id=u["session_id"],
                    player_id=selected_player_id,
                    amount=apply_amt,
                    payment_date=str(pay_date),
                    changed_by=current.get("name", "player"),
                    notes=notes or None,
                )
                remaining -= apply_amt

            st.success("Payment submitted successfully! ✅")
            st.rerun()

if is_coach:
    st.divider()
    st.subheader("📜 Payment History")
    all_payments = fetch_all("payments", order="payment_date")
    players_map = {p["id"]: p for p in fetch_all("players")}

    if not all_payments:
        st.info("No payment records yet.")
    else:
        for pay in reversed(all_payments):
            p = players_map.get(pay["player_id"], {})
            st.markdown(f"""
            <div class="player-card">
                <div class="player-avatar">{p.get('avatar_emoji', '💵')}</div>
                <div class="player-info">
                    <div class="name">₹{pay['amount']:.0f} — {p.get('name', '?')}</div>
                    <div class="sub">{pay['payment_date']}{' — ' + pay['notes'] if pay.get('notes') else ''}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

bottom_nav("5_Payments.py")
