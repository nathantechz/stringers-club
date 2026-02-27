import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils.styles import inject_mobile_css

st.set_page_config(
    page_title="StringerS Club",
    page_icon="🏸",
    layout="centered",
)
inject_mobile_css()

st.markdown("## 🏸 StringerS Club")
st.caption("Admin · Pro Sports Arena (Behind BYG Brewski), Kothanur")

# ── Quick overview metrics ────────────────────────────────────────────────────
try:
    from utils.supabase_client import get_client
    sb = get_client()
    players    = sb.table("players").select("id").eq("is_active", True).execute().data
    attendance = sb.table("attendance").select("fee_charged, amount_paid").execute().data

    total_charged = sum(r["fee_charged"] or 0 for r in attendance)
    total_paid    = sum(r["amount_paid"]  or 0 for r in attendance)
    total_due     = total_charged - total_paid

    c1, c2 = st.columns(2)
    c1.metric("Active Players", len(players))
    c2.metric("Total Due", f"₹{total_due:,.0f}")
    c3, c4 = st.columns(2)
    c3.metric("Charged", f"₹{total_charged:,.0f}")
    c4.metric("Collected", f"₹{total_paid:,.0f}")

except Exception as e:
    st.warning(f"⚠️ Cannot connect to Supabase — check `.env`.\n\n`{e}`")

st.divider()

st.markdown("""
**Use the sidebar (☰) to navigate:**

| Page | Purpose |
|---|---|
| 📋 Mark Attendance | Mark players present + set fees |
| 👤 Player Profiles | Full history & dues per player |
| 💳 Record Payment | Apply payment to sessions |
| 🧑‍🤝‍🧑 Manage Players | Add / edit all players |
| 📅 Monthly Settlement | Spread monthly fee across days |

**Sessions:** 7–8 AM & 7–8 PM · Mon–Fri · Court 1 & Court 2
""")
