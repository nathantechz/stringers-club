"""
Page 3 — Record Payment
Apply a payment to one or more attendance sessions for a player.
"""

import streamlit as st
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Record Payment", page_icon="💳", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 💳 Record Payment")

sb = get_client()

players_raw = sb.table("players").select("*").eq("is_active", True).order("name").execute().data
if not players_raw:
    st.info("No active players. Add some on the Manage Players page.")
    st.stop()

# ── Player selector & pending sessions ───────────────────────────────────────
player_name = st.selectbox("Select player", [p["name"] for p in players_raw])
player = next(p for p in players_raw if p["name"] == player_name)
p_id = player["id"]

# Fetch unpaid / partially paid attendance rows
att_rows = (
    sb.table("attendance")
    .select("*")
    .eq("player_id", p_id)
    .order("session_date")
    .execute()
    .data
)

pending = [r for r in att_rows if (r["fee_charged"] or 0) - (r["amount_paid"] or 0) > 0]
total_due = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in pending)

st.metric("Total balance due", f"₹{total_due:,.2f}")
st.divider()

if not pending:
    st.success("✅ No pending dues for this player.")
    st.stop()

# ── Show pending rows with checkboxes ─────────────────────────────────────────
st.subheader("Select sessions to settle")

# Quick-select helpers
qc1, qc2 = st.columns(2)
select_all = qc1.button("☑️ Select All", use_container_width=True)
pay_all_btn = qc2.button("⚡ Pay All Due Now", use_container_width=True, type="primary")

if pay_all_btn:
    # Immediately create one payment for total_due
    with st.spinner("Recording payment…"):
        try:
            pay_row = {
                "player_id":    p_id,
                "amount":       total_due,
                "payment_date": str(date.today()),
                "notes":        "Paid in full",
            }
            pay_result = sb.table("payments").insert(pay_row).execute()
            pay_id = pay_result.data[0]["id"]
            for r in pending:
                due = (r["fee_charged"] or 0) - (r["amount_paid"] or 0)
                sb.table("attendance").update({"amount_paid": r["fee_charged"]}).eq("id", r["id"]).execute()
                sb.table("payment_attendance").insert({
                    "payment_id":    pay_id,
                    "attendance_id": r["id"],
                    "applied_amount": due,
                }).execute()
            st.success(f"✅ All dues cleared — ₹{total_due:.2f} recorded.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

selected_ids = []
selected_amounts = []

for r in pending:
    due = (r["fee_charged"] or 0) - (r["amount_paid"] or 0)
    label = f"{r['session_date']}  {r['session_time'].title()}  — Due: ₹{due:.2f}"
    col1, col2 = st.columns([3, 1])
    # Pre-check all if select_all was clicked
    checked = col1.checkbox(label, key=r["id"], value=select_all)
    pay_amt = col2.number_input("Pay (₹)", min_value=0.0, max_value=float(due),
                                value=float(due), step=10.0, key=f"amt_{r['id']}")
    if checked:
        selected_ids.append(r["id"])
        selected_amounts.append(pay_amt)

selected_total = sum(selected_amounts)
st.markdown(f"**Selected total: ₹{selected_total:,.2f}**")
st.divider()

# ── Payment form ──────────────────────────────────────────────────────────────
with st.form("record_payment_form"):
    pay_date   = st.date_input("Payment date", value=date.today())
    pay_notes  = st.text_input("Notes (e.g. UPI, Cash)")
    save_btn   = st.form_submit_button("💾 Save Payment")

    if save_btn:
        if not selected_ids:
            st.error("Please select at least one session.")
        elif selected_total <= 0:
            st.error("Total payment must be > ₹0.")
        else:
            # Insert payment record
            pay_row = {
                "player_id":    p_id,
                "amount":       selected_total,
                "payment_date": str(pay_date),
                "notes":        pay_notes or None,
            }
            pay_result = sb.table("payments").insert(pay_row).execute()
            pay_id = pay_result.data[0]["id"]

            # Update each attendance row and create junction
            for att_id, amt in zip(selected_ids, selected_amounts):
                att = next(r for r in pending if r["id"] == att_id)
                new_paid = (att["amount_paid"] or 0) + amt
                sb.table("attendance").update({"amount_paid": new_paid}).eq("id", att_id).execute()
                sb.table("payment_attendance").insert({
                    "payment_id":    pay_id,
                    "attendance_id": att_id,
                    "applied_amount": amt,
                }).execute()

            # Recalculate remaining balance
            updated_att = sb.table("attendance").select("fee_charged, amount_paid").eq("player_id", p_id).execute().data
            new_balance = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in updated_att)
            st.success(f"✅ Payment of ₹{selected_total:.2f} recorded. Remaining due: ₹{new_balance:.2f}")
            st.rerun()
