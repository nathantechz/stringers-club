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
st.markdown("### Quick Navigation")

# Row 1
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/1_Mark_Attendance.py",    label="📋 Mark\nAttendance",      use_container_width=True)
with c2:
    st.page_link("pages/2_Player_Profiles.py",    label="👤 Player\nProfiles",        use_container_width=True)

# Row 2
c3, c4 = st.columns(2)
with c3:
    st.page_link("pages/3_Record_Payment.py",     label="💳 Record\nPayment",         use_container_width=True)
with c4:
    st.page_link("pages/4_Manage_Players.py",     label="🧑‍🤝‍🧑 Manage\nPlayers",   use_container_width=True)

# Row 3
c5, c6 = st.columns(2)
with c5:
    st.page_link("pages/5_Monthly_Settlement.py", label="📅 Monthly\nSettlement",     use_container_width=True)
with c6:
    st.page_link("pages/6_Analytics.py",          label="📊 Analytics",               use_container_width=True)

# Row 4 centre
c7, c8 = st.columns(2)
with c7:
    st.page_link("pages/7_Expenditure.py",        label="💸 Expenditure",             use_container_width=True)

st.caption("Sessions: 7–8 AM & 7–8 PM · Pro Sports Arena, Kothanur")
