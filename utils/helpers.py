"""Shared helper utilities for StringerS Badminton Academy."""
import streamlit as st

# ── Bottom navigation items ──────────────────────────────
# (label, material icon name, page path)
_PLAYER_NAV = [
    ("Home",     "home",          "app.py"),
    ("Games",    "sports_tennis", "pages/1_Join_Games.py"),
    ("Profile",  "person",        "pages/3_My_Profile.py"),
    ("Payments", "payments",      "pages/5_Payments.py"),
    ("Stats",    "analytics",     "pages/6_Analytics.py"),
]

_COACH_NAV = [
    ("Home",      "home",          "app.py"),
    ("Games",     "sports_tennis", "pages/1_Join_Games.py"),
    ("Dashboard", "shield_person", "pages/2_Coach_Dashboard.py"),
    ("Players",   "group",         "pages/4_Manage_Players.py"),
    ("Stats",     "analytics",     "pages/6_Analytics.py"),
]


def bottom_nav(current_page: str = ""):
    """Render a fixed bottom navigation bar. `current_page` is the page filename to highlight."""
    player = st.session_state.get("authenticated_player") or st.session_state.get("current_player")
    is_coach = player and player.get("role") in ("coach", "admin")
    items = _COACH_NAV if is_coach else _PLAYER_NAV

    links = ""
    for label, icon, path in items:
        active = "active" if current_page and current_page in path else ""
        links += (
            f'<a href="/{path}" target="_self" class="{active}">'
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
