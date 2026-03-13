"""Shared helper utilities for StringerS Badminton Academy."""
import streamlit as st

# ── Bottom navigation items ──────────────────────────────
# (label, material icon, script path)
_PLAYER_NAV = [
    ("Home", ":material/home:", "app.py"),
    ("Games", ":material/sports_tennis:", "pages/1_Join_Games.py"),
    ("Profile", ":material/person:", "pages/3_My_Profile.py"),
    ("Payments", ":material/payments:", "pages/5_Payments.py"),
    ("Stats", ":material/analytics:", "pages/6_Analytics.py"),
]

_COACH_NAV = [
    ("Home", ":material/home:", "app.py"),
    ("Games", ":material/sports_tennis:", "pages/1_Join_Games.py"),
    ("Dashboard", ":material/shield_person:", "pages/2_Coach_Dashboard.py"),
    ("Players", ":material/group:", "pages/4_Manage_Players.py"),
    ("Stats", ":material/analytics:", "pages/6_Analytics.py"),
]


def bottom_nav(current_page: str = ""):
    """Render bottom nav with Streamlit-native links (cloud-safe routing)."""
    player = st.session_state.get("authenticated_player") or st.session_state.get("current_player")
    is_coach = player and player.get("role") in ("coach", "admin")
    items = _COACH_NAV if is_coach else _PLAYER_NAV

    st.markdown('<div style="height:74px;"></div>', unsafe_allow_html=True)
    cols = st.columns(len(items), vertical_alignment="center")
    for col, (label, icon, path) in zip(cols, items):
        with col:
            st.page_link(path, label=label, icon=icon, use_container_width=True)


def show_back_button():
    """Kept for backward compat — now renders the bottom nav instead."""
    bottom_nav()


def skill_label(v: int) -> str:
    v = int(v or 5)
    if v <= 2:  return f"{v} — Beginner"
    if v <= 4:  return f"{v} — Casual"
    if v <= 6:  return f"{v} — Intermediate"
    if v <= 8:  return f"{v} — Advanced"
    if v == 9:  return f"{v} — Expert"
    return              f"{v} — Pro 🏆"


STATUS_BADGE = {
    "pending":   '<span class="badge-pending">⏳ Pending</span>',
    "confirmed": '<span class="badge-confirmed">✅ Confirmed</span>',
    "invited":   '<span class="badge-invited">📩 Invited</span>',
    "rejected":  '<span class="badge-rejected">✖ Rejected</span>',
}


def status_badge(status: str) -> str:
    return STATUS_BADGE.get(status, status)


def require_login():
    """Return the authenticated player or None. Prefer auth module's login_gate for gating."""
    return (
        st.session_state.get("authenticated_player")
        or st.session_state.get("current_player")
    )
