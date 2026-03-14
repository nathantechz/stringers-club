import streamlit as st
from datetime import date, timedelta, datetime, time
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, status_badge, is_coach_view
from utils.auth import login_gate, set_player_password
from utils.supabase_client import (
    fetch_all, fetch_view, insert_row, update_row, delete_row, bulk_update,
    confirm_request, reject_request, send_invite, bulk_confirm, upsert_row,
    VENUES,
)

st.set_page_config(page_title="Coach Dashboard | StringerS", page_icon="👨‍🏫", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

if not is_coach_view():
    st.warning("Coach access only.")
    st.stop()

st.title("👨‍🏫 Coach Dashboard")


def _slot_to_time(slot_val: str) -> time:
    """Parse saved slot text like '07:30 AM' into a time object for time_input."""
    if not slot_val:
        return time(7, 30)
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(str(slot_val).strip(), fmt).time()
        except ValueError:
            continue
    return time(7, 30)


def _format_slot(t: time) -> str:
    """Store slot in Playo-like format, e.g. '07:30 AM'."""
    return t.strftime("%I:%M %p")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Requests", "📩 Invites", "➕ Session", "💰 Session Fees", "⭐ Rate Players", "🔐 Passwords",
])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Manage Requests
# ═══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Pending Requests")

    # Join attendance with player name and session info
    pending = (
        st.session_state.get("_supa_client") or __import__("utils.supabase_client", fromlist=["get_client"]).get_client()
    ).table("attendance").select(
        "id, status, fee_charged, coach_note, "
        "player:players(id, name, avatar_emoji), "
        "session:sessions(id, date, slot)"
    ).eq("status", "pending").execute().data

    if not pending:
        st.info("No pending requests. 🎉")
    else:
        # Bulk accept
        if st.button("✅ Accept All Requests"):
            ids = [r["id"] for r in pending]
            bulk_confirm(ids)
            st.balloons()
            st.success(f"Accepted {len(ids)} requests!")
            st.rerun()

        for req in pending:
            player = req.get("player", {})
            session = req.get("session", {})
            emoji = player.get("avatar_emoji", "🏸")
            pname = player.get("name", "Unknown")
            sdate = session.get("date", "")
            sslot = session.get("slot", "")

            st.markdown(f"""
            <div class="game-card">
                <strong>{emoji} {pname}</strong><br>
                {sdate} • {sslot} &nbsp; {status_badge('pending')}
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            if c1.button("Accept", key=f"acc_{req['id']}"):
                confirm_request(req["id"])
                st.rerun()
            if c2.button("Reject", key=f"rej_{req['id']}"):
                reject_request(req["id"])
                st.rerun()

    st.divider()
    st.subheader("All Session Rosters")

    sessions = fetch_view("session_slots")
    if sessions:
        session_labels = {s["id"]: f"{s['date']} • {s['slot']}" for s in sessions}
        sel_sid = st.selectbox(
            "Pick a session",
            options=list(session_labels.keys()),
            format_func=lambda x: session_labels[x],
        )
        if sel_sid:
            roster = fetch_all("attendance", filters={"session_id": sel_sid})
            players_map = {p["id"]: p for p in fetch_all("players")}
            if roster:
                for r in roster:
                    p = players_map.get(r["player_id"], {})
                    badge = status_badge(r["status"])
                    st.markdown(
                        f"**{p.get('avatar_emoji', '🏸')} {p.get('name', '?')}** — {badge}"
                        + (f" &nbsp; 💬 _{r['coach_note']}_" if r.get("coach_note") else ""),
                        unsafe_allow_html=True,
                    )

                    # Coach note input
                    with st.expander(f"Add note for {p.get('name', '?')}", expanded=False):
                        note = st.text_input("Coach note", value=r.get("coach_note", "") or "", key=f"note_{r['id']}")
                        if st.button("Save Note", key=f"savenote_{r['id']}"):
                            update_row("attendance", r["id"], {"coach_note": note})
                            st.success("Note saved!")
                            st.rerun()
            else:
                st.info("No players in this session yet.")

# ═══════════════════════════════════════════════════════════
# TAB 2 — Send Invites
# ═══════════════════════════════════════════════════════════
with tab2:
    st.subheader("Send Private Invite")

    all_players = fetch_all("players", filters={"is_active": True}, order="name")
    sessions = fetch_view("session_slots")

    if not all_players or not sessions:
        st.info("Need at least one player and one session to send invites.")
    else:
        session_labels = {s["id"]: f"{s['date']} • {s['slot']} ({s.get('slots_left', '?')} left)" for s in sessions}

        selected_player = st.selectbox(
            "Select Player",
            options=all_players,
            format_func=lambda p: f"{p.get('avatar_emoji', '🏸')} {p['name']}",
            key="invite_player",
        )
        selected_session = st.selectbox(
            "Select Session",
            options=list(session_labels.keys()),
            format_func=lambda x: session_labels[x],
            key="invite_session",
        )

        if st.button("📩 Send Invite"):
            # Check if already exists
            existing = fetch_all("attendance", filters={
                "session_id": selected_session,
                "player_id": selected_player["id"],
            })
            if existing:
                st.warning(f"{selected_player['name']} already has a record for this session ({existing[0]['status']}).")
            else:
                sess_data = next((s for s in sessions if s["id"] == selected_session), {})
                send_invite(selected_session, selected_player["id"], float(sess_data.get("fee_per_player", 0)))
                st.success(f"Invite sent to {selected_player['name']}! 📩")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 3 — Create / Edit Session
# ═══════════════════════════════════════════════════════════
with tab3:
    sub1, sub2 = st.tabs(["🆕 New Session", "✏️ Edit Session"])

    # ── New Session ──
    with sub1:
        st.subheader("Create a New Session")
        with st.form("create_session", clear_on_submit=True):
            sess_date = st.date_input("Date", value=date.today() + timedelta(days=1))
            sess_time = st.time_input("Start Time", value=time(7, 30), step=timedelta(minutes=15))
            sess_slot = _format_slot(sess_time)
            venue = st.selectbox("Venue", list(VENUES.keys()))
            available_courts = VENUES[venue]["courts"]
            num_courts = st.number_input(
                "How many courts?", min_value=1,
                max_value=len(available_courts), value=1,
            )
            court_numbers = st.multiselect(
                "Which court number(s)?",
                options=available_courts,
                default=available_courts[:num_courts],
            )
            max_players = st.number_input("Max Players", min_value=2, max_value=30, value=num_courts * 4)

            if st.form_submit_button("🏟️ Create Session"):
                court_str = ",".join(str(c) for c in sorted(court_numbers))
                insert_row("sessions", {
                    "date": str(sess_date),
                    "slot": sess_slot,
                    "venue": venue,
                    "num_courts": len(court_numbers),
                    "court_numbers": court_str,
                    "max_players": max_players,
                    "fee_per_player": 0,
                })
                st.success(f"Session created for {sess_date} ({sess_slot}) at {venue}! 🎉")
                st.rerun()

    # ── Edit Session ──
    with sub2:
        st.subheader("Edit Existing Session")
        all_sessions = fetch_view("session_slots")
        if not all_sessions:
            st.info("No sessions to edit.")
        else:
            edit_labels = {
                s["id"]: f"{s['date']} • {s['slot']} — {s.get('venue', '?')} (Courts: {s.get('court_numbers', '?')})"
                for s in all_sessions
            }
            edit_sid = st.selectbox("Session", list(edit_labels.keys()),
                                    format_func=lambda x: edit_labels[x], key="edit_sess")
            sess = next(s for s in all_sessions if s["id"] == edit_sid)

            with st.form(f"edit_session_{edit_sid}"):
                e_time = st.time_input("Start Time", value=_slot_to_time(sess.get("slot", "")), step=timedelta(minutes=15))
                e_venue = st.selectbox("Venue", list(VENUES.keys()),
                                       index=list(VENUES.keys()).index(sess.get("venue", "Pro-Sports")))
                e_avail = VENUES[e_venue]["courts"]
                current_courts = [int(c) for c in str(sess.get("court_numbers", "1")).split(",") if c.strip().isdigit()]
                e_courts = st.multiselect("Court Number(s)", options=e_avail,
                                          default=[c for c in current_courts if c in e_avail])
                e_max = st.number_input("Max Players", min_value=2, max_value=30,
                                        value=sess.get("max_players", 8))

                if st.form_submit_button("💾 Save Changes"):
                    court_str = ",".join(str(c) for c in sorted(e_courts))
                    update_row("sessions", edit_sid, {
                        "slot": _format_slot(e_time),
                        "venue": e_venue,
                        "num_courts": len(e_courts),
                        "court_numbers": court_str,
                        "max_players": e_max,
                    })
                    st.success("Session updated!")
                    st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 4 — Session-level Fees (assign one fee to all players)
# ═══════════════════════════════════════════════════════════
with tab4:
    st.subheader("Set Fee For All Players In A Session")

    all_sessions = fetch_view("session_slots")
    if not all_sessions:
        st.info("No sessions yet.")
    else:
        fee_labels = {
            s["id"]: f"{s['date']} • {s['slot']} — {s.get('venue', '?')}"
            for s in all_sessions
        }
        fee_sid = st.selectbox("Session", list(fee_labels.keys()),
                               format_func=lambda x: fee_labels[x], key="fee_sess")
        roster = fetch_all("attendance", filters={"session_id": fee_sid})
        confirmed = [r for r in roster if r.get("status") == "confirmed"]

        if not confirmed:
            st.info("No confirmed players in this session yet.")
        else:
            st.caption(f"Confirmed players: {len(confirmed)}")
            all_fee = st.number_input("Fee for all confirmed players (₹)", min_value=0.0, value=100.0, step=10.0)
            if st.button("Apply Fee To All Confirmed Players"):
                for r in confirmed:
                    update_row("attendance", r["id"], {"fee_charged": float(all_fee)})
                st.success(f"Applied ₹{all_fee:.0f} to {len(confirmed)} confirmed players.")
                st.rerun()

    st.divider()
    st.subheader("📜 Fee Audit Log")
    try:
        audit = fetch_all("fee_audit_log", order="created_at")
    except Exception:
        audit = []
        st.info("Fee audit log table is not available yet. Run `migration_v5.sql` in Supabase SQL Editor.")
    if audit:
        players_map_all = {p["id"]: p for p in fetch_all("players")}
        for entry in reversed(audit[-50:]):
            p = players_map_all.get(entry.get("player_id"), {})
            action_label = {
                "fee_set": "💲 Fee Set",
                "fee_updated": "✏️ Fee Updated",
                "payment_recorded": "💰 Payment",
                "payment_reversed": "↩️ Reversed",
            }.get(entry["action"], entry["action"])

            st.markdown(f"""
            <div class="player-card">
                <div class="player-avatar">📝</div>
                <div class="player-info">
                    <div class="name">{action_label} — {p.get('name', '?')}</div>
                    <div class="sub">₹{entry.get('old_value', 0):.0f} → ₹{entry.get('new_value', 0):.0f}
                        &nbsp;•&nbsp; by {entry.get('changed_by', '?')}
                        &nbsp;•&nbsp; {str(entry.get('created_at', ''))[:16]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No audit entries yet.")

# ═══════════════════════════════════════════════════════════
# TAB 5 — Rate Players
# ═══════════════════════════════════════════════════════════
with tab5:
    st.subheader("⭐ Rate a Player")
    rate_players = fetch_all("players", filters={"is_active": True}, order="name")
    if not rate_players:
        st.info("No active players to rate.")
    else:
        sel_p = st.selectbox("Player", rate_players,
                             format_func=lambda p: f"{p.get('avatar_emoji', '🏸')} {p['name']}",
                             key="rate_player")
        with st.form("rate_form"):
            footwork = st.slider("Footwork", 1, 10, 5)
            stamina = st.slider("Stamina", 1, 10, 5)
            smash = st.slider("Smash Power", 1, 10, 5)
            net_play = st.slider("Net Play", 1, 10, 5)
            if st.form_submit_button("Save Rating"):
                upsert_row("ratings", {
                    "player_id": sel_p["id"],
                    "footwork": footwork,
                    "stamina": stamina,
                    "smash_power": smash,
                    "net_play": net_play,
                })
                st.success(f"Rating saved for {sel_p['name']}!")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 6 — Passwords
# ═══════════════════════════════════════════════════════════
with tab6:
    st.subheader("🔐 Set Player Password")
    pwd_players = fetch_all("players", filters={"is_active": True}, order="name")
    if not pwd_players:
        st.info("No active players.")
    else:
        sel_pwd_p = st.selectbox(
            "Select Player", pwd_players,
            format_func=lambda p: f"{p.get('avatar_emoji', '🏸')} {p['name']}",
            key="pwd_player",
        )
        has_pwd = bool(sel_pwd_p.get("password_hash"))
        st.caption(f"Password status: {'✅ Set' if has_pwd else '❌ Not set'}")
        with st.form("set_password_form"):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Set Password"):
                if not new_pwd or len(new_pwd) < 4:
                    st.error("Password must be at least 4 characters.")
                elif new_pwd != confirm_pwd:
                    st.error("Passwords do not match.")
                else:
                    set_player_password(sel_pwd_p["id"], new_pwd)
                    st.success(f"Password set for {sel_pwd_p['name']}!")
                    st.rerun()

bottom_nav("2_Coach_Dashboard.py")
