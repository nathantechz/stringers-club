"""
Page 4 — Manage Players
Add / edit players: membership, skill level (1-10), profession, work timing.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import skill_label, WORK_TIMINGS

st.set_page_config(page_title="Manage Players", page_icon="🧑‍🤝‍🧑", layout="centered")
inject_mobile_css()
st.markdown("## 🧑‍🤝‍🧑 Manage Players")

sb = get_client()


# ── Add new player ────────────────────────────────────────────────────────────
with st.expander("➕ Add new player", expanded=False):
    with st.form("add_player_form", clear_on_submit=True):
        st.markdown("**Personal details**")
        name  = st.text_input("Full name *")
        phone = st.text_input("WhatsApp no. (with country code, e.g. 918220583450) *")

        st.markdown("**Membership**")
        membership_type = st.selectbox("Membership type", ["regular", "monthly"])
        monthly_fee     = st.number_input("Monthly fee (₹) — monthly members only",
                                          min_value=0.0, step=100.0, value=0.0)

        st.markdown("**Skill level**")
        skill_level = st.slider("1 = Complete beginner  →  10 = Pro", 1, 10, 5)
        st.caption(f"🎾 {skill_label(skill_level)}")

        st.markdown("**Research profile**")
        profession  = st.text_input("Profession / Job title", placeholder="e.g. Software Engineer, Doctor…")
        work_timing = st.selectbox("Typical work timing", WORK_TIMINGS)

        add_btn = st.form_submit_button("✅ Add Player")

        if add_btn:
            if not name.strip() or not phone.strip():
                st.error("Name and phone are required.")
            else:
                row = {
                    "name":            name.strip(),
                    "phone":           phone.strip(),
                    "membership_type": membership_type,
                    "monthly_fee":     monthly_fee if membership_type == "monthly" else None,
                    "skill_level":     skill_level,
                    "profession":      profession.strip() or None,
                    "work_timing":     work_timing,
                    "is_active":       True,
                }
                try:
                    sb.table("players").insert(row).execute()
                    st.success(f"✅ {name} added — Skill {skill_level}/10")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()

# ── Players table ─────────────────────────────────────────────────────────────
players = sb.table("players").select("*").order("name").execute().data

if not players:
    st.info('No players yet. Use "Add new player" above.')
    st.stop()

st.subheader("All players")

df = pd.DataFrame([
    {
        "Name":        p["name"],
        "Skill":       f"{p.get('skill_level') or '—'}/10",
        "Membership":  p["membership_type"].title(),
        "Profession":  p.get("profession") or "—",
        "Work Timing": p.get("work_timing") or "—",
        "Active":      "✅" if p["is_active"] else "❌",
    }
    for p in players
])
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ── Edit player ───────────────────────────────────────────────────────────────
st.subheader("✏️ Edit player profile")

player_names = [p["name"] for p in players]
edit_name    = st.selectbox("Select player to edit", player_names, key="edit_sel")
edit_player  = next(p for p in players if p["name"] == edit_name)

cur_skill  = int(edit_player.get("skill_level") or 5)
cur_timing = edit_player.get("work_timing") or WORK_TIMINGS[-1]
timing_idx = WORK_TIMINGS.index(cur_timing) if cur_timing in WORK_TIMINGS else len(WORK_TIMINGS) - 1

st.markdown(
    f"Current skill:&nbsp;<span class='skill-badge'>🎾 {cur_skill}/10 — {skill_label(cur_skill)}</span>",
    unsafe_allow_html=True,
)
st.markdown("")

with st.form("edit_player_form"):
    st.markdown("**Personal details**")
    new_name  = st.text_input("Name",  value=edit_player["name"])
    new_phone = st.text_input("Phone", value=edit_player["phone"])

    st.markdown("**Membership**")
    new_memtype = st.selectbox(
        "Membership", ["regular", "monthly"],
        index=0 if edit_player["membership_type"] == "regular" else 1,
    )
    new_monthly = st.number_input("Monthly fee (₹)", min_value=0.0, step=100.0,
                                  value=float(edit_player.get("monthly_fee") or 0))

    st.markdown("**Skill level**")
    new_skill = st.slider("1 = Beginner  →  10 = Pro", 1, 10, cur_skill)
    st.caption(f"🎾 {skill_label(new_skill)}")

    st.markdown("**Research profile**")
    new_profession  = st.text_input("Profession / Job title",
                                    value=edit_player.get("profession") or "",
                                    placeholder="e.g. Software Engineer, Doctor…")
    new_work_timing = st.selectbox("Typical work timing", WORK_TIMINGS, index=timing_idx)

    new_active = st.checkbox("Active", value=edit_player["is_active"])
    update_btn = st.form_submit_button("💾 Update Player")

    if update_btn:
        sb.table("players").update({
            "name":            new_name.strip(),
            "phone":           new_phone.strip(),
            "membership_type": new_memtype,
            "monthly_fee":     new_monthly if new_memtype == "monthly" else None,
            "skill_level":     new_skill,
            "profession":      new_profession.strip() or None,
            "work_timing":     new_work_timing,
            "is_active":       new_active,
        }).eq("id", edit_player["id"]).execute()
        st.success(f"✅ {new_name} updated — Skill {new_skill}/10")
        st.rerun()
