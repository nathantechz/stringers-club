import streamlit as st
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav, skill_label, status_badge
from utils.auth import login_gate
from utils.supabase_client import fetch_all, fetch_view

st.set_page_config(page_title="My Profile | StringerS", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

show_back_button()

st.title("📈 My Profile")

current = require_login()
if not current:
    st.warning("Select your profile from the sidebar on the Home page first.")
    st.stop()

# ── Profile header ──
emoji = current.get("avatar_emoji", "🏸")
st.markdown(f"""
<div class="game-card" style="text-align:center;">
    <div style="font-size:3rem;">{emoji}</div>
    <h2 style="margin:4px 0;">{current['name']}</h2>
    <p style="margin:0;">📞 {current.get('phone', '—')} &nbsp;|&nbsp;
       🎯 {skill_label(current.get('skill_level', 5))}</p>
    <p style="margin:0;">Joined: {current.get('date_joined', '—')}</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Key Metrics ──
balances = fetch_view("player_balance")
my_bal = next((b for b in balances if b["id"] == current["id"]), None)

if my_bal:
    c1, c2, c3 = st.columns(3)
    c1.metric("🏸 Games Played", my_bal.get("games_played", 0))
    c2.metric("💰 Total Paid", f"₹{my_bal.get('total_paid', 0):.0f}")
    due = my_bal.get("balance_due", 0)
    c3.metric("📊 Balance Due", f"₹{due:.0f}")
    if due > 0:
        st.markdown('<span class="badge-due">💳 Payment Due</span>', unsafe_allow_html=True)

# ── Skill Radar Chart ──
import plotly.graph_objects as go

st.divider()
st.subheader("🎯 Skill Analysis")

ratings_data = fetch_all("ratings", filters={"player_id": current["id"]})
if not ratings_data:
    st.info("Coach hasn't rated your skills yet. Keep playing!")
else:
    latest = ratings_data[-1]
    categories = ["Footwork", "Stamina", "Smash Power", "Net Play"]
    values = [
        latest.get("footwork", 5),
        latest.get("stamina", 5),
        latest.get("smash_power", 5),
        latest.get("net_play", 5),
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(0, 200, 83, 0.3)",
        line=dict(color="#00c853", width=2),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], tickfont_size=10),
            angularaxis=dict(tickfont_size=12, rotation=90, direction="clockwise"),
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ── Session History ──
st.subheader("📋 Session History")

my_attendance = (
    __import__("utils.supabase_client", fromlist=["get_client"]).get_client()
    .table("attendance")
    .select("id, status, fee_charged, amount_paid, coach_note, session:sessions(date, slot, venue, court_numbers)")
    .eq("player_id", current["id"])
    .order("created_at", desc=True)
    .execute().data
)

if not my_attendance:
    st.info("No session history yet. Join a game to get started!")
else:
    for a in my_attendance:
        session = a.get("session", {})
        sdate = session.get("date", "?")
        sslot = session.get("slot", "?")
        venue = session.get("venue", "")
        courts = session.get("court_numbers", "")
        badge = status_badge(a["status"])
        fee = a.get("fee_charged", 0)
        paid = a.get("amount_paid", 0)
        note = a.get("coach_note")

        note_html = f"<br>💬 <em>{note}</em>" if note else ""
        due_html = ""
        if a["status"] == "confirmed" and fee > paid:
            due_html = f' &nbsp; <span class="badge-due">₹{fee - paid:.0f} due</span>'
        elif a["status"] == "confirmed" and fee > 0 and paid >= fee:
            due_html = ' &nbsp; <span class="badge-confirmed">✅ Paid</span>'

        venue_str = f"📍 {venue} Court {courts} &nbsp;|&nbsp; " if venue else ""

        st.markdown(f"""
        <div class="game-card">
              <strong>{sdate} • {sslot}</strong> &nbsp; {badge}{due_html}
            <br>{venue_str}Fee: ₹{fee:.0f} &nbsp;|&nbsp; Paid: ₹{paid:.0f}{note_html}
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Payment History ──
st.subheader("💳 Payment History")
payments = fetch_all("payments", filters={"player_id": current["id"]}, order="payment_date")
if not payments:
    st.info("No payments recorded yet.")
else:
    for pay in reversed(payments):
        st.markdown(f"""
        <div class="player-card">
            <div class="player-avatar">💵</div>
            <div class="player-info">
                <div class="name">₹{pay['amount']:.0f}</div>
                <div class="sub">{pay['payment_date']}{' — ' + pay['notes'] if pay.get('notes') else ''}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Audit Trail ──
st.subheader("📝 Fee & Payment Audit Trail")
audit = fetch_all("fee_audit_log", filters={"player_id": current["id"]}, order="created_at")
if not audit:
    st.info("No audit entries for your account.")
else:
    for entry in reversed(audit):
        action_label = {
            "fee_set": "💲 Fee Set",
            "fee_updated": "✏️ Fee Changed",
            "payment_recorded": "💰 Payment",
            "payment_reversed": "↩️ Reversed",
        }.get(entry["action"], entry["action"])

        st.markdown(f"""
        <div class="player-card">
            <div class="player-avatar">📝</div>
            <div class="player-info">
                <div class="name">{action_label}</div>
                <div class="sub">₹{entry.get('old_value', 0):.0f} → ₹{entry.get('new_value', 0):.0f}
                    &nbsp;•&nbsp; by {entry.get('changed_by', '?')}
                    &nbsp;•&nbsp; {str(entry.get('created_at', ''))[:16]}
                    {' — ' + entry['notes'] if entry.get('notes') else ''}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

bottom_nav("3_My_Profile.py")
