import streamlit as st
import pandas as pd
from utils.styles import inject_mobile_css
from utils.helpers import bottom_nav
from utils.auth import login_gate
from utils.supabase_client import fetch_all, fetch_view

st.set_page_config(page_title="Analytics | StringerS", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
inject_mobile_css()

current = login_gate()

st.title("📊 Analytics")

tab1, tab2, tab3 = st.tabs(["📈 Attendance", "💰 Revenue", "👥 Leaderboard"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Attendance Trends
# ═══════════════════════════════════════════════════════════
with tab1:
    attendance = fetch_all("attendance", filters={"status": "confirmed"})
    if not attendance:
        st.info("No confirmed attendance data yet.")
    else:
        # Join with session dates
        from utils.supabase_client import get_client
        data = (
            get_client().table("attendance")
            .select("id, session:sessions(date, slot)")
            .eq("status", "confirmed")
            .execute().data
        )
        if data:
            rows = [{"date": d["session"]["date"], "slot": d["session"]["slot"]} for d in data if d.get("session")]
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])

            daily = df.groupby("date").size().reset_index(name="players")
            st.subheader("Daily Attendance")
            st.line_chart(daily.set_index("date")["players"])

            st.subheader("Morning vs Evening Split")
            slot_counts = df["slot"].value_counts()
            st.bar_chart(slot_counts)

# ═══════════════════════════════════════════════════════════
# TAB 2 — Revenue
# ═══════════════════════════════════════════════════════════
with tab2:
    payments = fetch_all("payments", order="payment_date")
    if not payments:
        st.info("No payment data yet.")
    else:
        df_pay = pd.DataFrame(payments)
        df_pay["payment_date"] = pd.to_datetime(df_pay["payment_date"])
        df_pay["month"] = df_pay["payment_date"].dt.to_period("M").astype(str)

        total_collected = df_pay["amount"].sum()
        st.metric("Total Collected", f"₹{total_collected:,.0f}")

        monthly = df_pay.groupby("month")["amount"].sum().reset_index()
        st.subheader("Monthly Collections")
        st.bar_chart(monthly.set_index("month")["amount"])

    # Expenditures
    expenditures = fetch_all("expenditures", order="date")
    if expenditures:
        df_exp = pd.DataFrame(expenditures)
        total_exp = df_exp["amount"].sum()
        st.metric("Total Expenditure", f"₹{total_exp:,.0f}")

        if payments:
            st.metric("Net Profit", f"₹{total_collected - total_exp:,.0f}")

# ═══════════════════════════════════════════════════════════
# TAB 3 — Leaderboard
# ═══════════════════════════════════════════════════════════
with tab3:
    st.subheader("🏆 Most Active Players")
    balances = fetch_view("player_balance")
    if balances:
        sorted_b = sorted(balances, key=lambda b: b.get("games_played", 0), reverse=True)
        for i, b in enumerate(sorted_b[:10], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            st.markdown(f"""
            <div class="player-card">
                <div class="player-avatar">{medal}</div>
                <div class="player-info">
                    <div class="name">{b['name']}</div>
                    <div class="sub">{b.get('games_played', 0)} games &nbsp;•&nbsp; Skill {b.get('skill_level', '?')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No data yet.")

    st.divider()

    st.subheader("📊 Outstanding Dues")
    if balances:
        with_dues = [b for b in balances if b.get("balance_due", 0) > 0]
        with_dues.sort(key=lambda b: b["balance_due"], reverse=True)
        if with_dues:
            for b in with_dues:
                st.markdown(f"""
                <div class="player-card">
                    <div class="player-avatar">💳</div>
                    <div class="player-info">
                        <div class="name">{b['name']}</div>
                        <div class="sub">Due: <span class="badge-due">₹{b['balance_due']:.0f}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("All dues cleared! 🎉")

bottom_nav("6_Analytics.py")
