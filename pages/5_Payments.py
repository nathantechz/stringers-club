import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav
from utils.auth import login_gate
from utils.supabase_client import (
    fetch_all, get_client, record_payment_with_audit,
)

st.set_page_config(page_title="Payments | StringerS", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

current = login_gate()

st.title("💳 Record Payment")

tab1, tab2, tab3 = st.tabs(["➕ New Payment", "📜 History", "🔍 Audit Trail"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Record a payment
# ═══════════════════════════════════════════════════════════
with tab1:
    players = fetch_all("players", filters={"is_active": True}, order="name")
    if not players:
        st.info("No active players.")
        st.stop()

    selected = st.selectbox(
        "Player",
        options=players,
        format_func=lambda p: f"{p.get('avatar_emoji', '🏸')} {p['name']}",
    )

    # Show unpaid sessions for context
    unpaid = (
        get_client().table("attendance")
        .select("id, fee_charged, amount_paid, session_id, session:sessions(date, slot, venue, court_numbers)")
        .eq("player_id", selected["id"])
        .eq("status", "confirmed")
        .execute().data
    )
    unpaid = [u for u in unpaid if (u.get("fee_charged", 0) - u.get("amount_paid", 0)) > 0]

    if unpaid:
        st.markdown("**Unpaid sessions:**")
        total_due = 0.0
        for u in unpaid:
            s = u.get("session", {})
            due = u["fee_charged"] - u["amount_paid"]
            total_due += due
            venue = s.get("venue", "")
            courts = s.get("court_numbers", "")
            loc = f" — 📍 {venue} Court {courts}" if venue else ""
            st.markdown(
                f"- {s.get('date', '?')} {s.get('slot', '?').title()}{loc} — "
                f"₹{u['fee_charged']:.0f} charged, ₹{u['amount_paid']:.0f} paid, "
                f'<span class="badge-due">₹{due:.0f} due</span>',
                unsafe_allow_html=True,
            )
        st.markdown(f"**Total due: ₹{total_due:.0f}**")
    else:
        st.success(f"{selected['name']} has no unpaid sessions!")

    st.divider()

    with st.form("payment_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        pay_date = st.date_input("Payment Date")
        notes = st.text_input("Notes (optional)")

        if st.form_submit_button("💰 Record Payment"):
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                # Auto-distribute payment across unpaid sessions (FIFO by date)
                remaining = float(amount)
                for u in sorted(unpaid, key=lambda x: x.get("session", {}).get("date", "")):
                    if remaining <= 0:
                        break
                    due = u["fee_charged"] - u["amount_paid"]
                    apply_amt = min(remaining, due)
                    record_payment_with_audit(
                        attendance_id=u["id"],
                        session_id=u["session_id"],
                        player_id=selected["id"],
                        amount=apply_amt,
                        payment_date=str(pay_date),
                        changed_by="player",
                        notes=notes or None,
                    )
                    remaining -= apply_amt

                st.success(f"₹{amount:.0f} recorded for {selected['name']}! 🎉")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 2 — Payment History
# ═══════════════════════════════════════════════════════════
with tab2:
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

# ═══════════════════════════════════════════════════════════
# TAB 3 — Audit Trail
# ═══════════════════════════════════════════════════════════
with tab3:
    audit_logs = fetch_all("fee_audit_log", order="created_at")
    players_map2 = {p["id"]: p for p in fetch_all("players")}

    if not audit_logs:
        st.info("No audit entries yet.")
    else:
        ACTION_LABELS = {
            "fee_set": "🏷️ Fee Set",
            "fee_updated": "✏️ Fee Updated",
            "payment_recorded": "💰 Payment",
            "payment_reversed": "↩️ Reversal",
        }
        for entry in reversed(audit_logs):
            p = players_map2.get(entry["player_id"], {})
            label = ACTION_LABELS.get(entry["action"], entry["action"])
            ts = entry.get("created_at", "")[:16].replace("T", " ")
            note_txt = f" — {entry['notes']}" if entry.get("notes") else ""
            st.markdown(
                f'<div class="player-card">'
                f'<div class="player-avatar">{p.get("avatar_emoji", "📋")}</div>'
                f'<div class="player-info">'
                f'<div class="name">{label} — {p.get("name", "?")}</div>'
                f'<div class="sub">₹{entry.get("old_value", 0):.0f} → ₹{entry.get("new_value", 0):.0f}'
                f" | {ts} | by {entry.get('changed_by', '?')}{note_txt}</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

bottom_nav("5_Payments.py")
