import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button, skill_label
from utils.supabase_client import fetch_all, insert_row, update_row

st.set_page_config(page_title="Manage Players | StringerS", page_icon="👥", layout="wide")
inject_mobile_css()
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { max-width: 500px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)
show_back_button()

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

        if st.form_submit_button("Add Player"):
            if not name or not phone:
                st.error("Name and phone are required.")
            else:
                insert_row("players", {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "role": role,
                    "skill_level": skill,
                    "avatar_emoji": emoji,
                })
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

                if st.button("Save Changes", key=f"save_{p['id']}"):
                    update_row("players", p["id"], {
                        "name": new_name.strip(),
                        "phone": new_phone.strip(),
                        "role": new_role,
                        "skill_level": new_skill,
                        "avatar_emoji": new_emoji,
                        "is_active": new_active,
                    })
                    st.success("Updated!")
                    st.rerun()
