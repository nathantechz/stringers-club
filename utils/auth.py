"""
Authentication module for StringerS Badminton Academy.
Phone (10-digit) + password login with persistent "Keep me logged in" via localStorage.
Coach/admin phones auto-login without a password prompt.
"""
import hashlib
import hmac
import os
import secrets

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

from utils.supabase_client import get_client, update_row

# ── Constants ──────────────────────────────────────────────
_LS_KEY = "stringers_auth"


def _sign_secret() -> str:
    try:
        raw = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    except Exception:
        raw = os.environ.get("SUPABASE_KEY", "")
    return (raw or "stringers-default-secret")[:32]


def _coach_phones() -> list[str]:
    """Return list of phone numbers that get auto-login as coach/admin."""
    try:
        val = st.secrets.get("COACH_PHONES", "") or os.environ.get("COACH_PHONES", "")
    except Exception:
        val = os.environ.get("COACH_PHONES", "")
    if not val:
        return []
    return [p.strip() for p in str(val).split(",") if p.strip()]


# ── Password hashing (PBKDF2-SHA256) ──────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, h = stored_hash.split(":", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(check.hex(), h)


# ── Token helpers (HMAC-SHA256 signed player id) ──────────

def _make_token(player_id: str) -> str:
    return hmac.new(
        _sign_secret().encode(), str(player_id).encode(), hashlib.sha256
    ).hexdigest()


def _verify_token(player_id: str, token: str) -> bool:
    return hmac.compare_digest(_make_token(player_id), token)


# ── localStorage persistence ──────────────────────────────

def _read_ls():
    return streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{_LS_KEY}')",
        key="auth_read",
    )


def _write_ls(player_id: str):
    token = _make_token(player_id)
    val = f"{player_id}:{token}"
    streamlit_js_eval(
        js_expressions=f"localStorage.setItem('{_LS_KEY}', '{val}')",
        key="auth_write",
    )


def _clear_ls():
    streamlit_js_eval(
        js_expressions=f"localStorage.removeItem('{_LS_KEY}')",
        key="auth_clear",
    )


# ── Coach helper: set / reset a player's password ────────

def set_player_password(player_id: str, new_password: str):
    update_row("players", player_id, {"password_hash": hash_password(new_password)})


# ── Main auth gate ────────────────────────────────────────

def login_gate():
    """
    Call at the top of every page.
    • Coach/admin phones (in COACH_PHONES env/secret) auto-login with no prompt.
    • Players see a phone + password login form.
    Returns the authenticated player dict or calls st.stop().
    """
    # 1. Fast path: already authenticated this Streamlit session
    if st.session_state.get("authenticated_player"):
        return st.session_state["authenticated_player"]

    # 2. Try localStorage (persistent across browser restarts)
    if not st.session_state.get("_auth_ls_checked"):
        stored = _read_ls()
        if stored == 0:
            st.stop()
        st.session_state["_auth_ls_checked"] = True
        if stored and isinstance(stored, str) and ":" in stored:
            pid, token = stored.rsplit(":", 1)
            if _verify_token(pid, token):
                player = (
                    get_client()
                    .table("players")
                    .select("*")
                    .eq("id", pid)
                    .eq("is_active", True)
                    .maybe_single()
                    .execute()
                    .data
                )
                if player:
                    st.session_state["authenticated_player"] = player
                    st.session_state["current_player"] = player
                    return player

    # 3. Auto-login for configured coach phones
    coach_phones = _coach_phones()
    if coach_phones:
        for cp in coach_phones:
            player = (
                get_client()
                .table("players")
                .select("*")
                .eq("phone", cp)
                .eq("is_active", True)
                .maybe_single()
                .execute()
                .data
            )
            if player and player.get("role") in ("coach", "admin"):
                st.session_state["authenticated_player"] = player
                st.session_state["current_player"] = player
                _write_ls(player["id"])
                return player

    # 4. No valid session — show login form
    _show_login_form()
    st.stop()


def _show_login_form():
    from utils.styles import inject_mobile_css
    inject_mobile_css()

    st.markdown(
        "<div style='text-align:center;font-size:3.5rem;margin-top:3rem;'>🏸</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='text-align:center;margin-bottom:0;'>StringerS</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#5f6368;margin-top:4px;'>Badminton Academy</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    with st.form("login_form"):
        phone = st.text_input("📱 Phone Number (10 digits)", max_chars=10)
        password = st.text_input("🔒 Password", type="password")
        remember = st.checkbox("Keep me logged in", value=True)

        if st.form_submit_button("Sign In"):
            if not phone or not password:
                st.error("Enter your phone number and password.")
                return

            phone = phone.strip()
            if not phone.isdigit() or len(phone) != 10:
                st.error("Phone must be exactly 10 digits.")
                return

            player = (
                get_client()
                .table("players")
                .select("*")
                .eq("phone", phone)
                .eq("is_active", True)
                .maybe_single()
                .execute()
                .data
            )

            if not player:
                st.error("No account found for this phone number.")
                return

            if not player.get("password_hash"):
                st.error("Password not set yet. Ask your coach to set it.")
                return

            if not verify_password(password, player["password_hash"]):
                st.error("Incorrect password.")
                return

            st.session_state["authenticated_player"] = player
            st.session_state["current_player"] = player
            if remember:
                _write_ls(player["id"])
            st.rerun()


def logout():
    """Clear auth from session + localStorage and rerun."""
    _clear_ls()
    for k in ["authenticated_player", "current_player", "_auth_ls_checked"]:
        st.session_state.pop(k, None)
    st.rerun()
