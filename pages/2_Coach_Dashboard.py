import streamlit as st
from datetime import date, timedelta
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button, status_badge
from utils.supabase_client import (
    fetch_all, fetch_view, insert_row, update_row, delete_row, bulk_update,
    confirm_request, reject_request, send_invite, bulk_confirm, upsert_row,
    set_player_fee, VENUES,
)

st.set_page_config(page_title="Coach Dashboard | StringerS", page_icon="👨‍🏫", layout="wide")
inject_mobile_css()
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { max-width: 500px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)
show_back_button()

st.title("👨‍🏫 Coach Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Requests", "📩 Invites", "➕ Session", "💰 Fees", "⭐ Rate Players",
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
                {sdate} • {sslot.title()} &nbsp; {status_badge('pending')}
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
        session_labels = {s["id"]: f"{s['date']} • {s['slot'].title()}" for s in sessions}
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
        session_labels = {s["id"]: f"{s['date']} • {s['slot'].title()} ({s.get('slots_left', '?')} left)" for s in sessions}

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
            sess_slot = st.selectbox("Slot", ["morning", "evening"])
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
            fee = st.number_input("Fee per Player (₹)", min_value=0.0, value=100.0, step=10.0)
            notes = st.text_input("Notes (optional)")

            if st.form_submit_button("🏟️ Create Session"):
                court_str = ",".join(str(c) for c in sorted(court_numbers))
                insert_row("sessions", {
                    "date": str(sess_date),
                    "slot": sess_slot,
                    "venue": venue,
                    "num_courts": len(court_numbers),
                    "court_numbers": court_str,
                    "max_players": max_players,
                    "fee_per_player": float(fee),
                    "notes": notes or None,
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
                s["id"]: f"{s['date']} • {s['slot'].title()} — {s.get('venue', '?')} (Courts: {s.get('court_numbers', '?')})"
                for s in all_sessions
            }
            edit_sid = st.selectbox("Session", list(edit_labels.keys()),
                                    format_func=lambda x: edit_labels[x], key="edit_sess")
            sess = next(s for s in all_sessions if s["id"] == edit_sid)

            with st.form(f"edit_session_{edit_sid}"):
                e_venue = st.selectbox("Venue", list(VENUES.keys()),
                                       index=list(VENUES.keys()).index(sess.get("venue", "Pro-Sports")))
                e_avail = VENUES[e_venue]["courts"]
                current_courts = [int(c) for c in str(sess.get("court_numbers", "1")).split(",") if c.strip().isdigit()]
                e_courts = st.multiselect("Court Number(s)", options=e_avail,
                                          default=[c for c in current_courts if c in e_avail])
                e_max = st.number_input("Max Players", min_value=2, max_value=30,
                                        value=sess.get("max_players", 8))
                e_fee = st.number_input("Fee per Player (₹)", min_value=0.0,
                                        value=float(sess.get("fee_per_player", 0)), step=10.0)
                e_notes = st.text_input("Notes", value=sess.get("notes", "") or "")

                if st.form_submit_button("💾 Save Changes"):
                    court_str = ",".join(str(c) for c in sorted(e_courts))
                    update_row("sessions", edit_sid, {
                        "venue": e_venue,
                        "num_courts": len(e_courts),
                        "court_numbers": court_str,
                        "max_players": e_max,
                        "fee_per_player": float(e_fee),
                        "notes": e_notes or None,
                    })
                    st.success("Session updated!")
                    st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 4 — Manage Per-Player Fees
# ═══════════════════════════════════════════════════════════
with tab4:
    st.subheader("Set / Update Player Fees")

    all_sessions = fetch_view("session_slots")
    if not all_sessions:
        st.info("No sessions yet.")
    else:
        fee_labels = {
            s["id"]: f"{s['date']} • {s['slot'].title()} — {s.get('venue', '?')}"
            for s in all_sessions
        }
        fee_sid = st.selectbox("Session", list(fee_labels.keys()),
                               format_func=lambda x: fee_labels[x], key="fee_sess")
        fee_sess = next(s for s in all_sessions if s["id"] == fee_sid)
        default_fee = float(fee_sess.get("fee_per_player", 0))

        roster = fetch_all("attendance", filters={"session_id": fee_sid})
        players_map = {p["id"]: p for p in fetch_all("players")}

        if not roster:
            st.info("No players in this session yet.")
        else:
            st.caption(f"Session default fee: ₹{default_fee:.0f}")
            for r in roster:
                p = players_map.get(r["player_id"], {})
                pname = p.get("name", "?")
                old_fee = float(r.get("fee_charged", 0))
                paid = float(r.get("amount_paid", 0))

                badge = status_badge(r["status"])
                paid_badge = ""
                if r["status"] == "confirmed":
                    if paid >= old_fee and old_fee > 0:
                        paid_badge = ' <span class="badge-confirmed">PAID</span>'
                    elif old_fee > 0:
                        paid_badge = f' <span class="badge-due">₹{old_fee - paid:.0f} due</span>'

                st.markdown(f"""
                <div class="game-card">
                    <strong>{p.get('avatar_emoji', '🏸')} {pname}</strong> {badge}{paid_badge}
                    <br>Fee: ₹{old_fee:.0f} &nbsp;|&nbsp; Paid: ₹{paid:.0f}
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Update fee for {pname}"):
                    new_fee = st.number_input(
                        f"Fee for {pname} (₹)", min_value=0.0,
                        value=old_fee if old_fee > 0 else default_fee,
                        step=10.0, key=f"fee_{r['id']}",
                    )
                    if st.button("Save Fee", key=f"savefee_{r['id']}"):
                        set_player_fee(
                            attendance_id=r["id"],
                            session_id=fee_sid,
                            player_id=r["player_id"],
                            old_fee=old_fee,
                            new_fee=float(new_fee),
                            changed_by="coach",
                        )
                        st.success(f"Fee updated to ₹{new_fee:.0f} for {pname}")
                        st.rerun()

    st.divider()
    st.subheader("📜 Fee Audit Log")
    audit = fetch_all("fee_audit_log", order="created_at")
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
