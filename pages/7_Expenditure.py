import streamlit as st
import pandas as pd
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button
from utils.supabase_client import fetch_all, insert_row, delete_row

st.set_page_config(page_title="Expenditure | StringerS", page_icon="📒", layout="wide")
inject_mobile_css()
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { max-width: 500px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)
show_back_button()

st.title("📒 Expenditure Tracker")

tab1, tab2 = st.tabs(["➕ Add Expense", "📋 History"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Add
# ═══════════════════════════════════════════════════════════
with tab1:
    with st.form("add_expense", clear_on_submit=True):
        exp_date = st.date_input("Date")
        category = st.selectbox("Category", [
            "Shuttlecocks", "Court Rental", "Equipment",
            "Refreshments", "Transport", "Miscellaneous",
        ])
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        notes = st.text_input("Notes (optional)")

        if st.form_submit_button("💸 Add Expense"):
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                insert_row("expenditures", {
                    "date": str(exp_date),
                    "category": category,
                    "amount": float(amount),
                    "notes": notes or None,
                })
                st.success("Expense recorded!")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 2 — History
# ═══════════════════════════════════════════════════════════
with tab2:
    expenses = fetch_all("expenditures", order="date")
    if not expenses:
        st.info("No expenses recorded yet.")
    else:
        df = pd.DataFrame(expenses)
        total = df["amount"].sum()
        st.metric("Total Expenditure", f"₹{total:,.0f}")

        # By category
        st.subheader("By Category")
        cat_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        st.bar_chart(cat_totals)

        st.subheader("All Records")
        for exp in reversed(expenses):
            st.markdown(f"""
            <div class="player-card">
                <div class="player-avatar">🧾</div>
                <div class="player-info">
                    <div class="name">₹{exp['amount']:.0f} — {exp['category']}</div>
                    <div class="sub">{exp['date']}{' — ' + exp['notes'] if exp.get('notes') else ''}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🗑️ Delete", key=f"del_{exp['id']}"):
                delete_row("expenditures", exp["id"])
                st.rerun()
