import streamlit as st
from utils.styles import inject_mobile_css
from utils.supabase_client import fetch_all, fetch_view, confirm_request, update_row

st.set_page_config(
    page_title="StringerS Badminton Academy",
    page_icon="🏸",
    layout="wide",
)
inject_mobile_css()

# Force a narrow layout for mobile feel
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        max-width: 500px;
        margin: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Sidebar: Player Selector (acts as lightweight login) ──
players = fetch_all("players", filters={"is_active": True}, order="name")
player_names = ["— Select your profile —"] + [p["name"] for p in players]

chosen = st.sidebar.selectbox("👤  Who are you?", player_names, key="player_picker")
if chosen != "— Select your profile —":
    st.session_state.current_player = next(p for p in players if p["name"] == chosen)
else:
    st.session_state.current_player = None

# ── Home page ──
st.title("🏸 StringerS Badminton Academy")

current = st.session_state.get("current_player")
if current:
    st.markdown(f"Welcome back, **{current['name']}** {current.get('avatar_emoji', '🏸')}")
else:
    st.info("Select your profile from the sidebar to join games & view your stats.")

st.divider()

# ── Upcoming sessions — card view ──
st.subheader("📅 Upcoming Sessions")

sessions = fetch_view("session_slots")
if not sessions:
    st.info("No upcoming sessions. Ask your coach to create one!")
else:
    from datetime import date as dt_date

    upcoming = [s for s in sessions if s["date"] >= str(dt_date.today())]
    upcoming.sort(key=lambda s: (s["date"], s["slot"]))

    if not upcoming:
        st.info("No upcoming sessions. Check back soon!")
    else:
        for s in upcoming:
            slots_left = s.get("slots_left", "?")
            confirmed = s.get("confirmed_count", 0)
            pending = s.get("pending_count", 0)
            slot_emoji = "🌅" if s["slot"] == "morning" else "🌆"

            venue = s.get('venue', 'Pro-Sports')
            courts = s.get('court_numbers', '1')

            st.markdown(f"""
            <div class="game-card">
                <h3>{slot_emoji} {s['date']}  &bull;  {s['slot'].title()}</h3>
                <p>📍 {venue} — Court {courts} &nbsp;|&nbsp;
                   💰 ₹{s.get('fee_per_player', 0)} per player &nbsp;|&nbsp;
                   🟢 {confirmed} confirmed &nbsp;|&nbsp;
                   ⏳ {pending} pending</p>
                <p><strong>{slots_left} slots left</strong></p>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Quick Stats ──
if current:
    st.subheader("📊 Your Quick Stats")
    balances = fetch_view("player_balance")
    my_bal = next((b for b in balances if b["id"] == current["id"]), None)

    if my_bal:
        c1, c2, c3 = st.columns(3)
        c1.metric("Games Played", my_bal.get("games_played", 0))
        c2.metric("Total Paid", f"₹{my_bal.get('total_paid', 0):.0f}")
        c3.metric("Balance Due", f"₹{my_bal.get('balance_due', 0):.0f}")

# ── 🔔 Activity Center ──
if current:
    st.divider()
    st.subheader("🔔 Activity Center")

    is_coach = current.get("role") == "coach"

    if is_coach:
        # COACH VIEW: pending join requests
        st.markdown("##### 📥 Pending Player Requests")
        pending_requests = fetch_all("attendance", filters={"status": "pending"})

        if not pending_requests:
            st.success("All caught up! No pending requests.")
        else:
            for req in pending_requests:
                player_name = next(
                    (p["name"] for p in players if p["id"] == req["player_id"]),
                    "Unknown",
                )
                # Fetch session info for display
                sess = next(
                    (s for s in sessions if s["id"] == req.get("session_id")),
                    {},
                ) if sessions else {}
                sess_label = f"{sess.get('date', '?')} {sess.get('slot', '').title()}" if sess else "upcoming session"

                col1, col2 = st.columns([3, 1])
                col1.markdown(
                    f"**{player_name}** wants to join **{sess_label}**"
                )
                if col2.button("✅ Accept", key=f"coach_acc_{req['id']}"):
                    confirm_request(req["id"])
                    st.success(f"Accepted {player_name}!")
                    st.rerun()

    else:
        # PLAYER VIEW: invites from coach
        st.markdown("##### 📩 New Invitations")
        my_invites = fetch_all(
            "attendance",
            filters={"player_id": current["id"], "status": "invited"},
        )

        if not my_invites:
            st.info("No active invites. Join a game below!")
        else:
            for invite in my_invites:
                sess = next(
                    (s for s in sessions if s["id"] == invite.get("session_id")),
                    {},
                ) if sessions else {}
                sess_label = (
                    f"{sess.get('date', 'Upcoming')} {sess.get('slot', '').title()}"
                    f" — 📍 {sess.get('venue', '')} Court {sess.get('court_numbers', '')}"
                    if sess
                    else "Upcoming Match"
                )
                st.markdown(
                    f'<div style="background:#f0f2f6;padding:15px;border-radius:10px;'
                    f'border-left:5px solid #00c853;margin-bottom:10px;">'
                    f"<strong>Coach has invited you!</strong><br>"
                    f"Session: {sess_label}</div>",
                    unsafe_allow_html=True,
                )
                if st.button("Accept Invite", key=f"inv_acc_{invite['id']}"):
                    update_row("attendance", invite["id"], {"status": "confirmed"})
                    st.success("You're in! 🎉")
                    st.rerun()
