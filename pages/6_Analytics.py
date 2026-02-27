"""
Page 6 — Analytics
Attendance charts: Day view, Week view, Month view.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Analytics", page_icon="📊", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 📊 Analytics")

sb = get_client()

# ── Load all attendance ───────────────────────────────────────────────────────
att_raw = sb.table("attendance").select("session_date, session_time, player_id").execute().data
players_raw = sb.table("players").select("id, name").execute().data
pid_to_name = {p["id"]: p["name"] for p in players_raw}

if not att_raw:
    st.info("No attendance data yet.")
    st.stop()

df = pd.DataFrame(att_raw)
df["session_date"] = pd.to_datetime(df["session_date"])
df["player_name"]  = df["player_id"].map(pid_to_name)
df["week_start"]   = df["session_date"].dt.to_period("W").apply(lambda p: p.start_time)
df["month"]        = df["session_date"].dt.to_period("M").astype(str)
df["day_of_week"]  = df["session_date"].dt.day_name()

CHART_BG   = "#1a1d27"
ACCENT     = "#4ade80"
ACCENT2    = "#22d3ee"
GRID_COLOR = "#2e3352"
TEXT_COLOR = "#8b92b3"

def _style(fig):
    fig.update_layout(
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=TEXT_COLOR, size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        height=300,
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
    )
    return fig


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_day, tab_week, tab_month, tab_players, tab_dues = st.tabs(
    ["📅 Day", "📆 Week", "🗓 Month", "👤 Players", "💳 Dues"]
)

# ════════════════════════════════════════════════════════════
# DAY VIEW — pick a specific date
# ════════════════════════════════════════════════════════════
with tab_day:
    sel_date = st.date_input("Select date", value=date.today(), key="day_picker")
    day_df   = df[df["session_date"].dt.date == sel_date]

    if day_df.empty:
        st.info(f"No attendance on {sel_date.strftime('%d %b %Y')}.")
    else:
        st.metric("Players attended", len(day_df))
        session_counts = day_df.groupby("session_time").size().reset_index(name="count")
        fig = px.bar(
            session_counts, x="session_time", y="count",
            color="session_time",
            color_discrete_sequence=[ACCENT, ACCENT2],
            labels={"session_time": "Session", "count": "Players"},
            title=f"Attendance on {sel_date.strftime('%d %b %Y')}",
        )
        st.plotly_chart(_style(fig), use_container_width=True)

        # Player list
        st.markdown("**Players present:**")
        st.dataframe(
            day_df[["session_time", "player_name"]].rename(
                columns={"session_time": "Session", "player_name": "Player"}
            ).sort_values("Session"),
            use_container_width=True, hide_index=True,
        )

# ════════════════════════════════════════════════════════════
# WEEK VIEW — last N weeks of total daily attendance
# ════════════════════════════════════════════════════════════
with tab_week:
    n_weeks = st.select_slider("Show last N weeks", options=[2, 4, 8, 12], value=4)
    cutoff  = pd.Timestamp(date.today() - timedelta(weeks=n_weeks))
    week_df = df[df["session_date"] >= cutoff]

    if week_df.empty:
        st.info("No data in this range.")
    else:
        daily = (
            week_df.groupby(["session_date", "session_time"])
            .size().reset_index(name="count")
        )
        fig = px.bar(
            daily, x="session_date", y="count",
            color="session_time",
            color_discrete_sequence=[ACCENT, ACCENT2],
            barmode="stack",
            labels={"session_date": "Date", "count": "Players", "session_time": "Session"},
            title=f"Daily attendance — last {n_weeks} weeks",
        )
        fig.update_xaxes(tickformat="%d %b", tickangle=-30)
        st.plotly_chart(_style(fig), use_container_width=True)

        # Day-of-week heatmap style
        dow_counts = week_df.groupby("day_of_week").size().reindex(
            ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        ).fillna(0).reset_index(name="count")
        dow_counts.columns = ["Day", "Total Sessions"]
        fig2 = px.bar(
            dow_counts, x="Day", y="Total Sessions",
            color="Total Sessions",
            color_continuous_scale=["#1a1d27", ACCENT],
            title="Which days have most attendance?",
        )
        fig2.update_coloraxes(showscale=False)
        st.plotly_chart(_style(fig2), use_container_width=True)

# ════════════════════════════════════════════════════════════
# MONTH VIEW — aggregate per calendar month
# ════════════════════════════════════════════════════════════
with tab_month:
    monthly = df.groupby("month").size().reset_index(name="sessions_attended")
    monthly = monthly.sort_values("month")

    fig = px.line(
        monthly, x="month", y="sessions_attended",
        markers=True,
        color_discrete_sequence=[ACCENT],
        labels={"month": "Month", "sessions_attended": "Total attendance"},
        title="Monthly attendance trend",
    )
    fig.update_traces(line_width=2.5, marker_size=8)
    st.plotly_chart(_style(fig), use_container_width=True)

    # Unique players per month
    monthly_unique = df.groupby("month")["player_id"].nunique().reset_index(name="unique_players")
    monthly_unique = monthly_unique.sort_values("month")
    fig2 = px.bar(
        monthly_unique, x="month", y="unique_players",
        color_discrete_sequence=[ACCENT2],
        labels={"month": "Month", "unique_players": "Unique players"},
        title="Unique players per month",
    )
    st.plotly_chart(_style(fig2), use_container_width=True)

    # Show breakdown table
    merged = monthly.merge(monthly_unique, on="month")
    merged.columns = ["Month", "Total Attendance", "Unique Players"]
    st.dataframe(merged, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════
# PLAYERS — attendance frequency per player
# ════════════════════════════════════════════════════════════
with tab_players:
    # Date range filter
    col1, col2 = st.columns(2)
    from_d = col1.date_input("From", value=date(date.today().year, 1, 1), key="p_from")
    to_d   = col2.date_input("To",   value=date.today(), key="p_to")

    p_df = df[(df["session_date"].dt.date >= from_d) & (df["session_date"].dt.date <= to_d)]

    if p_df.empty:
        st.info("No data in range.")
    else:
        player_freq = (
            p_df.groupby("player_name").size()
            .reset_index(name="sessions")
            .sort_values("sessions", ascending=True)
        )
        fig = px.bar(
            player_freq, x="sessions", y="player_name",
            orientation="h",
            color="sessions",
            color_continuous_scale=["#1a1d27", ACCENT],
            labels={"sessions": "Sessions attended", "player_name": "Player"},
            title="Attendance frequency by player",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=max(250, len(player_freq) * 32))
        st.plotly_chart(_style(fig), use_container_width=True)

        # Morning vs evening split per player
        split = (
            p_df.groupby(["player_name", "session_time"]).size()
            .reset_index(name="count")
        )
        fig2 = px.bar(
            split, x="player_name", y="count",
            color="session_time",
            color_discrete_sequence=[ACCENT, ACCENT2],
            barmode="stack",
            labels={"player_name": "Player", "count": "Sessions", "session_time": "Session"},
            title="Morning vs Evening split",
        )
        fig2.update_xaxes(tickangle=-40)
        st.plotly_chart(_style(fig2), use_container_width=True)

# ════════════════════════════════════════════════════════════
# DUES — who owes what right now
# ════════════════════════════════════════════════════════════
with tab_dues:
    # Load all attendance with fee/paid info
    dues_att = sb.table("attendance").select("player_id, fee_charged, amount_paid").execute().data
    dues_by_player: dict = {}
    for r in dues_att:
        pid = r["player_id"]
        due = (r["fee_charged"] or 0) - (r["amount_paid"] or 0)
        dues_by_player[pid] = dues_by_player.get(pid, 0) + due

    dues_rows = [
        {"Player": pid_to_name.get(pid, pid), "Balance Due (₹)": round(due, 2)}
        for pid, due in dues_by_player.items()
        if due > 0.005  # ignore floating point near-zero
    ]
    dues_rows.sort(key=lambda x: x["Balance Due (₹)"], reverse=True)

    if not dues_rows:
        st.success("✅ All players are clear — no outstanding dues!")
    else:
        total_outstanding = sum(r["Balance Due (₹)"] for r in dues_rows)
        st.metric("Total outstanding", f"₹{total_outstanding:,.0f}")
        st.markdown(f"**{len(dues_rows)} player(s) have pending dues:**")

        dues_df = pd.DataFrame(dues_rows)
        fig = px.bar(
            dues_df.sort_values("Balance Due (₹)"),
            x="Balance Due (₹)", y="Player",
            orientation="h",
            color="Balance Due (₹)",
            color_continuous_scale=[ACCENT, DANGER],
            title="Outstanding dues by player",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=max(250, len(dues_df) * 36))
        st.plotly_chart(_style(fig), use_container_width=True)
        st.dataframe(dues_df, use_container_width=True, hide_index=True)
