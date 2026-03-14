import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, is_coach_view
from utils.supabase_client import fetch_all, fetch_view, confirm_request, update_row
from utils.auth import login_gate, logout

st.set_page_config(
    page_title="StringerS Badminton Academy",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_mobile_css()

# ── Auth gate ──
current = login_gate()

# ── Header row (Playo-style: greeting + logout) ──
col_g, col_out = st.columns([4, 1])
with col_g:
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"<span style='font-size:2rem;'>{current.get('avatar_emoji', '🏸')}</span>"
        f"<div><strong style='font-size:1.1rem;'>Hey {current['name']}!</strong>"
        f"<br><span style='color:#5f6368;font-size:0.82rem;'>"
        f"{current.get('role', 'player').title()}</span></div></div>",
        unsafe_allow_html=True,
    )
with col_out:
    if st.button("🚪", help="Logout"):
        logout()

# ── Action Required Alerts ──
if current.get("role") in ["coach", "admin"]:
    _pending_count = len(fetch_all("attendance", filters={"status": "pending"}))
    if _pending_count > 0:
        st.warning(f"🔔 **{_pending_count}** new join request(s) to review!")
        if st.button("Manage Requests"):
            st.switch_page("pages/2_Coach_Dashboard.py")
else:
    _invite_count = len(fetch_all(
        "attendance", filters={"player_id": current["id"], "status": "invited"}
    ))
    if _invite_count > 0:
        st.info(f"📩 **{_invite_count}** game invitation(s)!")
        if st.button("View Invites"):
            st.switch_page("pages/1_Join_Games.py")

    _balances = fetch_view("player_balance")
    _my_bal = next((b for b in _balances if b["id"] == current["id"]), None)
    if _my_bal and _my_bal.get("balance_due", 0) > 0:
        st.error(f"💳 Payment Due: ₹{_my_bal['balance_due']:.0f}")

st.divider()

# ── What's Coming Up ──
st.markdown(
    "<h3 style='margin-bottom:8px;'>"
    "<span class='material-symbols-rounded' style='vertical-align:middle;font-size:22px;color:#34a853;'>calendar_today</span>"
    " WHAT'S COMING UP</h3>",
    unsafe_allow_html=True,
)

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
                <p>
                    <span class="material-symbols-rounded" style="font-size:16px;vertical-align:middle;">location_on</span>
                    {venue} — Court {courts} &nbsp;|&nbsp;
                    💰 ₹{s.get('fee_per_player', 0)} per player
                </p>
                <p>🟢 {confirmed} confirmed &nbsp;|&nbsp;
                   ⏳ {pending} pending &nbsp;|&nbsp;
                   <strong>{slots_left} slots left</strong></p>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Quick Stats ──
st.markdown(
    "<h3><span class='material-symbols-rounded' style='vertical-align:middle;font-size:22px;color:#34a853;'>analytics</span>"
    " YOUR STATS</h3>",
    unsafe_allow_html=True,
)
balances = fetch_view("player_balance")
my_bal = next((b for b in balances if b["id"] == current["id"]), None)

if my_bal:
    c1, c2, c3 = st.columns(3)
    c1.metric("Games", my_bal.get("games_played", 0))
    c2.metric("Paid", f"₹{my_bal.get('total_paid', 0):.0f}")
    c3.metric("Due", f"₹{my_bal.get('balance_due', 0):.0f}")

st.divider()

# ── Activity Center ──
players = fetch_all("players", filters={"is_active": True}, order="name")
is_coach = is_coach_view()

if is_coach:
    st.markdown(
        "<h3><span class='material-symbols-rounded' style='vertical-align:middle;font-size:22px;color:#34a853;'>notifications</span>"
        " PENDING REQUESTS</h3>",
        unsafe_allow_html=True,
    )
    pending_requests = fetch_all("attendance", filters={"status": "pending"})

    if not pending_requests:
        st.success("All caught up! No pending requests.")
    else:
        for req in pending_requests:
            player_name = next(
                (p["name"] for p in players if p["id"] == req["player_id"]),
                "Unknown",
            )
            sess = next(
                (s for s in sessions if s["id"] == req.get("session_id")),
                {},
            ) if sessions else {}
            sess_label = f"{sess.get('date', '?')} {sess.get('slot', '').title()}" if sess else "upcoming session"

            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{player_name}** wants to join **{sess_label}**")
            if col2.button("✅ Accept", key=f"coach_acc_{req['id']}"):
                confirm_request(req["id"])
                st.success(f"Accepted {player_name}!")
                st.rerun()
else:
    my_invites = fetch_all(
        "attendance",
        filters={"player_id": current["id"], "status": "invited"},
    )

    if my_invites:
        st.markdown(
            "<h3><span class='material-symbols-rounded' style='vertical-align:middle;font-size:22px;color:#34a853;'>mail</span>"
            " INVITATIONS</h3>",
            unsafe_allow_html=True,
        )
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
                f'<div class="game-card" style="border-left:4px solid #00c853;">'
                f"<strong>Coach has invited you!</strong><br>"
                f"Session: {sess_label}</div>",
                unsafe_allow_html=True,
            )
            if st.button("Accept Invite", key=f"inv_acc_{invite['id']}"):
                update_row("attendance", invite["id"], {"status": "confirmed"})
                st.success("You're in! 🎉")
                st.rerun()

# ── Bottom Nav ──
bottom_nav("app.py")
