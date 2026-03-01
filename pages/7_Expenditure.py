"""
Page 7 — Expenditure & Profit
Track court booking costs and shuttle purchases.
View monthly revenue vs expenditure vs profit.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import calendar
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Expenditure & Profit", page_icon="💰", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 💰 Expenditure & Profit")

sb = get_client()

CATEGORIES = ["Court booking", "Shuttles", "Equipment", "Other"]

CHART_BG   = "#ffffff"
ACCENT     = "#059669"
WARN       = "#d97706"
DANGER     = "#dc2626"
GRID_COLOR = "#e2e8f0"
TEXT_COLOR = "#475569"

def _style(fig):
    fig.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=TEXT_COLOR, size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        height=300,
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ── Add Expenditure ───────────────────────────────────────────────────────────
with st.expander("➕ Add expenditure", expanded=False):
    with st.form("add_exp_form", clear_on_submit=True):
        exp_date     = st.date_input("Date", value=date.today())
        exp_category = st.selectbox("Category", CATEGORIES)
        exp_amount   = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        exp_notes    = st.text_input("Notes", placeholder="e.g. 2 tubes Yonex Mavis 350")
        save_exp     = st.form_submit_button("💾 Save Expenditure")

        if save_exp:
            if exp_amount <= 0:
                st.error("Amount must be > ₹0")
            else:
                sb.table("expenditures").insert({
                    "exp_date":  str(exp_date),
                    "category":  exp_category,
                    "amount":    exp_amount,
                    "notes":     exp_notes.strip() or None,
                }).execute()
                st.success(f"✅ ₹{exp_amount:.2f} ({exp_category}) saved.")
                st.rerun()

st.divider()

# ── Month selector ────────────────────────────────────────────────────────────
today = date.today()
month_options = sorted(
    {f"{today.year}-{m:02d}" for m in range(1, today.month + 1)}
    | {f"{today.year - 1}-{m:02d}" for m in range(1, 13)},
    reverse=True,
)
selected_month = st.selectbox("View month", month_options)
year, mon = map(int, selected_month.split("-"))
from_date = f"{selected_month}-01"
to_date   = f"{selected_month}-{calendar.monthrange(year, mon)[1]:02d}"


# ── Fetch data for month ──────────────────────────────────────────────────────
exp_rows = (
    sb.table("expenditures")
    .select("*")
    .gte("exp_date", from_date)
    .lte("exp_date", to_date)
    .order("exp_date")
    .execute()
    .data
)

att_rows = (
    sb.table("attendance")
    .select("fee_charged")
    .gte("session_date", from_date)
    .lte("session_date", to_date)
    .execute()
    .data
)

pay_rows = (
    sb.table("payments")
    .select("amount")
    .gte("payment_date", from_date)
    .lte("payment_date", to_date)
    .execute()
    .data
)


# ── P&L Metrics ───────────────────────────────────────────────────────────────────────────────
total_revenue   = sum(r["fee_charged"] or 0 for r in att_rows)
total_collected = sum(r["amount"] or 0 for r in pay_rows)
total_exp      = sum(r["amount"] for r in exp_rows)
profit         = total_collected - total_exp

c1, c2 = st.columns(2)
c1.metric("Revenue (collected)", f"₹{total_collected:,.0f}")
c2.metric("Expenditure",         f"₹{total_exp:,.0f}")
c3, c4 = st.columns(2)
c3.metric("Fees charged (total)", f"₹{total_revenue:,.0f}")

profit_delta = f"{'▲' if profit >= 0 else '▼'} ₹{abs(profit):,.0f}"
c4.metric(
    "Net Profit",
    f"₹{profit:,.0f}",
    delta=profit_delta,
    delta_color="normal" if profit >= 0 else "inverse",
)

if profit >= 0:
    st.success(f"✅ Club is **in profit** by ₹{profit:,.0f} this month.")
else:
    st.error(f"⚠️ Club is **at a loss** of ₹{abs(profit):,.0f} this month.")

st.divider()


# ── Revenue vs Expenditure chart ──────────────────────────────────────────────
fig = go.Figure(data=[
    go.Bar(name="Collected", x=[selected_month], y=[total_collected], marker_color=ACCENT),
    go.Bar(name="Expenditure", x=[selected_month], y=[total_exp], marker_color=DANGER),
    go.Bar(name="Net Profit", x=[selected_month], y=[profit],
           marker_color=ACCENT if profit >= 0 else DANGER, opacity=0.6),
])
fig.update_layout(barmode="group", title=f"P&L — {selected_month}")
st.plotly_chart(_style(fig), use_container_width=True)


# ── Expenditure breakdown pie ──────────────────────────────────────────────────
if exp_rows:
    st.subheader("Expenditure breakdown")
    by_cat = pd.DataFrame(exp_rows).groupby("category")["amount"].sum().reset_index()
    fig2 = px.pie(
        by_cat, values="amount", names="category",
        color_discrete_sequence=[ACCENT, WARN, "#22d3ee", DANGER],
        title=f"Spend by category — {selected_month}",
        hole=0.4,
    )
    fig2.update_layout(paper_bgcolor=CHART_BG, font=dict(color=TEXT_COLOR),
                       margin=dict(l=8,r=8,t=36,b=8), height=280,
                       legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig2, use_container_width=True)

    # Detail table
    exp_df = pd.DataFrame(exp_rows)[["exp_date", "category", "amount", "notes"]]
    exp_df.columns = ["Date", "Category", "Amount (₹)", "Notes"]
    exp_df["Notes"] = exp_df["Notes"].fillna("—")
    st.dataframe(exp_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total expenditure: ₹{total_exp:,.2f}**")
else:
    st.info(f"No expenditure logged for {selected_month}.")

st.divider()

# ── Full expenditure log ──────────────────────────────────────────────────────
with st.expander("📋 All expenditure history", expanded=False):
    all_exp = sb.table("expenditures").select("*").order("exp_date", desc=True).execute().data
    if all_exp:
        all_df = pd.DataFrame(all_exp)[["id", "exp_date", "category", "amount", "notes"]]
        all_df.columns = ["id", "Date", "Category", "Amount (₹)", "Notes"]
        all_df["Notes"] = all_df["Notes"].fillna("—")
        st.dataframe(all_df.drop(columns=["id"]), use_container_width=True, hide_index=True)
        st.markdown(f"**Total all time: ₹{sum(r['amount'] for r in all_exp):,.2f}**")

        st.markdown("")
        st.subheader("🗑️ Delete an entry")
        del_options = [
            f"{r['exp_date']} | {r['category']} | ₹{r['amount']} | {r.get('notes') or ''}"
            for r in all_exp
        ]
        del_choice = st.selectbox("Select entry to delete", del_options, key="del_exp_sel")
        del_idx    = del_options.index(del_choice)
        del_id     = all_exp[del_idx]["id"]
        if st.button("🗑️ Delete this entry", type="primary", key="del_exp_btn"):
            try:
                sb.table("expenditures").delete().eq("id", del_id).execute()
                st.success("✅ Entry deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("No expenditure records yet.")
