"""Shared helper utilities for the Playo-style Badminton Pro Hub."""
import streamlit as st


def show_back_button():
    st.page_link("app.py", label="🏠 Home", use_container_width=False)
    st.divider()


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
    """Ensure a player is selected in session state; show picker if not."""
    if "current_player" in st.session_state and st.session_state.current_player:
        return st.session_state.current_player
    return None
