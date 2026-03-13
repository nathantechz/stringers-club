"""Shared helper utilities for StringerS Badminton Academy."""
import streamlit as st

# ── Bottom navigation items ──────────────────────────────
# (label, material icon name, url path, page key)
_PLAYER_NAV = [
    ("Home", "home", "/", "app.py"),
    ("Games", "sports_tennis", "/1_Join_Games", "1_Join_Games.py"),
    ("Profile", "person", "/3_My_Profile", "3_My_Profile.py"),
    ("Payments", "payments", "/5_Payments", "5_Payments.py"),
    ("Stats", "analytics", "/6_Analytics", "6_Analytics.py"),
]

_COACH_NAV = [
    ("Home", "home", "/", "app.py"),
    ("Games", "sports_tennis", "/1_Join_Games", "1_Join_Games.py"),
    ("Dashboard", "shield_person", "/2_Coach_Dashboard", "2_Coach_Dashboard.py"),
    ("Players", "group", "/4_Manage_Players", "4_Manage_Players.py"),
    ("Stats", "analytics", "/6_Analytics", "6_Analytics.py"),
]


def bottom_nav(current_page: str = ""):
    """Render a fixed Playo-style bottom nav with icons across all pages."""
    player = st.session_state.get("authenticated_player") or st.session_state.get("current_player")
    is_coach = player and player.get("role") in ("coach", "admin")
    items = _COACH_NAV if is_coach else _PLAYER_NAV

    links = ""
    for label, icon, href, page_key in items:
        active = "active" if current_page == page_key else ""
        links += (
            f'<a href="{href}" target="_self" class="{active}">'
            f'<span class="material-symbols-rounded">{icon}</span>'
            f'<span class="nav-label">{label}</span>'
            f'</a>'
        )

    st.markdown(
        f'<div class="bottom-nav"><div class="bottom-nav-inner">{links}</div></div>',
        unsafe_allow_html=True,
    )


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
