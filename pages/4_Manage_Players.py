import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, skill_label, is_coach_view
from utils.auth import login_gate, set_player_password
from utils.supabase_client import fetch_all, insert_row, update_row

st.set_page_config(page_title="Manage Players | StringerS", page_icon="👥", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

if not is_coach_view():
    st.warning("Coach access only.")
    bottom_nav("4_Manage_Players.py")
    st.stop()

st.title("👥 Manage Players")

tab1, tab2 = st.tabs(["➕ Add Player", "📋 All Players"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Add Player
# ═══════════════════════════════════════════════════════════
with tab1:
    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        role = st.selectbox("Role", ["player", "coach", "admin"])
        skill = st.slider("Skill Level", 1, 10, 5)
        emoji = st.text_input("Avatar Emoji", value="🏸")
        password = st.text_input("Password (optional)", type="password")

        if st.form_submit_button("Add Player"):
            if not name or not phone:
                st.error("Name and phone are required.")
            else:
                row = insert_row("players", {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "role": role,
                    "skill_level": skill,
                    "avatar_emoji": emoji,
                })
                if password and len(password) >= 4 and row and row.data:
                    set_player_password(row.data[0]["id"], password)
                st.success(f"{name} added! 🎉")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 2 — View / Edit Players
# ═══════════════════════════════════════════════════════════
with tab2:
    players = fetch_all("players", order="name")
    if not players:
        st.info("No players yet. Add one above!")
    else:
        for p in players:
            active_dot = "🟢" if p.get("is_active") else "🔴"
            st.markdown(f"""
            <div class="player-card">
                <div class="player-avatar">{p.get('avatar_emoji', '🏸')}</div>
                <div class="player-info">
                    <div class="name">{active_dot} {p['name']}</div>
                    <div class="sub">{p.get('phone', '')} &nbsp;•&nbsp; {p.get('role', 'player').title()} &nbsp;•&nbsp; {skill_label(p.get('skill_level', 5))}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Edit {p['name']}", expanded=False):
                new_name = st.text_input("Name", value=p["name"], key=f"n_{p['id']}")
                new_phone = st.text_input("Phone", value=p.get("phone", ""), key=f"ph_{p['id']}")
                new_role = st.selectbox("Role", ["player", "coach", "admin"],
                                        index=["player", "coach", "admin"].index(p.get("role", "player")),
                                        key=f"r_{p['id']}")
                new_skill = st.slider("Skill", 1, 10, p.get("skill_level", 5), key=f"sk_{p['id']}")
                new_emoji = st.text_input("Emoji", value=p.get("avatar_emoji", "🏸"), key=f"em_{p['id']}")
                new_active = st.checkbox("Active", value=p.get("is_active", True), key=f"act_{p['id']}")
                new_pwd = st.text_input("New Password (leave blank to keep)", type="password", key=f"pwd_{p['id']}")

                if st.button("Save Changes", key=f"save_{p['id']}"):
                    update_row("players", p["id"], {
                        "name": new_name.strip(),
                        "phone": new_phone.strip(),
                        "role": new_role,
                        "skill_level": new_skill,
                        "avatar_emoji": new_emoji,
                        "is_active": new_active,
                    })
                    if new_pwd and len(new_pwd) >= 4:
                        set_player_password(p["id"], new_pwd)
                    st.success("Updated!")
                    st.rerun()

bottom_nav("4_Manage_Players.py")
