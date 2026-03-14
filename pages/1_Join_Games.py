import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, status_badge
from utils.auth import login_gate
from utils.supabase_client import fetch_all, fetch_view, insert_row, update_row, record_payment_with_audit

st.set_page_config(page_title="Join Games | StringerS", page_icon="🏸", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()
bottom_nav("1_Join_Games.py")  # Reserve space at top

st.title("🏸 Available Sessions")

# ── Fetch sessions with slot info ──
sessions = fetch_view("session_slots")

if not sessions:
    st.info("No sessions available right now. Check back later!")
    st.stop()

from datetime import date as dt_date, datetime

upcoming = [s for s in sessions if s["date"] >= str(dt_date.today())]
upcoming.sort(key=lambda s: (s["date"], s["slot"]))

if not upcoming:
    st.info("No upcoming sessions. Ask your coach to create one!")
    st.stop()

# ── Fetch current player's attendance records to know existing status ──
my_attendance = fetch_all("attendance", filters={"player_id": current["id"]})
my_session_map = {a["session_id"]: a for a in my_attendance}

for s in upcoming:
    slots_left = s.get("slots_left", "?")
    confirmed = s.get("confirmed_count", 0)
    slot_txt = str(s.get("slot", ""))
    try:
        slot_hour = datetime.strptime(slot_txt, "%I:%M %p").hour
        slot_emoji = "🌅" if slot_hour < 12 else "🌆"
    except ValueError:
        slot_emoji = "🌅" if "morning" in slot_txt.lower() else "🌆"

    venue = s.get('venue', 'Pro-Sports')
    courts = s.get('court_numbers', '1')

    st.markdown(f"""
    <div class="game-card">
            <h3>{slot_emoji} {s['date']}  •  {s['slot']}</h3>
        <p>📍 {venue} — Court {courts} &nbsp;|&nbsp;
           💰 ₹{s.get('fee_per_player', 0)} per player &nbsp;|&nbsp;
           🟢 {confirmed} confirmed &nbsp;|&nbsp;
           <strong>{slots_left} slots left</strong></p>
    </div>
    """, unsafe_allow_html=True)

    existing = my_session_map.get(s["id"])

    if existing:
        badge = status_badge(existing["status"])
        st.markdown(f"Your status: {badge}", unsafe_allow_html=True)

        # If invited, show accept / decline buttons
        if existing["status"] == "invited":
            c1, c2 = st.columns(2)
            if c1.button("✅ Accept Invite", key=f"accept_{s['id']}"):
                update_row("attendance", existing["id"], {
                    "status": "confirmed",
                    "fee_charged": float(s.get("fee_per_player", 0)),
                })
                st.success("You're in! See you on court! 🎉")
                st.rerun()
            if c2.button("❌ Decline", key=f"decline_{s['id']}"):
                update_row("attendance", existing["id"], {"status": "rejected"})
                st.info("Invite declined.")
                st.rerun()
        # If confirmed, show "Mark as Paid" option
        if existing["status"] == "confirmed":
            fee = float(existing.get("fee_charged", 0))
            paid = float(existing.get("amount_paid", 0))
            if fee > 0 and paid < fee:
                with st.expander(f"💳 Mark as Paid (₹{fee - paid:.0f} due)"):
                    from datetime import date as d_date
                    pay_amount = st.number_input(
                        "Amount (₹)", min_value=0.0, value=fee - paid,
                        step=10.0, key=f"payamt_{s['id']}",
                    )
                    pay_date = st.date_input("Payment Date", value=d_date.today(), key=f"paydt_{s['id']}")
                    pay_note = st.text_input("Note (optional)", key=f"paynote_{s['id']}")
                    if st.button("✅ Confirm Payment", key=f"paybtn_{s['id']}"):
                        record_payment_with_audit(
                            attendance_id=existing["id"],
                            session_id=s["id"],
                            player_id=current["id"],
                            amount=float(pay_amount),
                            payment_date=str(pay_date),
                            changed_by=current["name"],
                            notes=pay_note or None,
                        )
                        st.success("Payment recorded! 🎉")
                        st.rerun()
            elif fee > 0:
                st.markdown('<span class="badge-confirmed">✅ Fully Paid</span>', unsafe_allow_html=True)
    else:
        # No existing record — show "Request to Join"
        if slots_left and int(slots_left) > 0:
            if st.button(f"🙋 Request to Join", key=f"join_{s['id']}"):
                insert_row("attendance", {
                    "session_id": s["id"],
                    "player_id": current["id"],
                    "status": "pending",
                    "fee_charged": float(s.get("fee_per_player", 0)),
                })
                st.success("Request sent to coach! ⏳")
                st.rerun()
        else:
            st.warning("Session is full.")

    st.markdown("---")
