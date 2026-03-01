"""
Page 3 — Record / Edit Payment
• Tab 1: Apply a new payment to one or more attendance sessions.
• Tab 2: Edit or delete an existing payment record, or directly
         adjust the amount_paid on individual session rows.
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
st.markdown("## 💳 Record / Edit Payment")

sb = get_client()

players_raw = sb.table("players").select("*").eq("is_active", True).order("name").execute().data
if not players_raw:
    st.info("No active players. Add some on the Manage Players page.")
    st.stop()

# Player selection lives ABOVE the tabs so changing it doesn't fight with tab state
player_name = st.selectbox("Select player", [p["name"] for p in players_raw], key="player_select")
player = next(p for p in players_raw if p["name"] == player_name)
p_id = player["id"]

tab_new, tab_edit = st.tabs(["➕ Record New", "✏️ Edit Existing"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Record New Payment
# ══════════════════════════════════════════════════════════════════════════════
with tab_new:

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
    else:
        st.subheader("Select sessions to settle")

        qc1, qc2 = st.columns(2)
        select_all  = qc1.button("☑️ Select All",      use_container_width=True, key="sel_all")
        pay_all_btn = qc2.button("⚡ Pay All Due Now",  use_container_width=True, type="primary", key="pay_all")

        if pay_all_btn:
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

        selected_ids     = []
        selected_amounts = []

        for r in pending:
            due = (r["fee_charged"] or 0) - (r["amount_paid"] or 0)
            label = f"{r['session_date']}  {r['session_time'].title()}  — Due: ₹{due:.2f}"
            col1, col2 = st.columns([3, 1])
            checked = col1.checkbox(label, key=f"chk_{r['id']}", value=select_all)
            pay_amt = col2.number_input("Pay (₹)", min_value=0.0, max_value=float(due),
                                        value=float(due), step=10.0, key=f"amt_{r['id']}")
            if checked:
                selected_ids.append(r["id"])
                selected_amounts.append(pay_amt)

        selected_total = sum(selected_amounts)
        st.markdown(f"**Selected total: ₹{selected_total:,.2f}**")
        st.divider()

        with st.form("record_payment_form"):
            pay_date  = st.date_input("Payment date", value=date.today())
            pay_notes = st.text_input("Notes (e.g. UPI, Cash)")
            save_btn  = st.form_submit_button("💾 Save Payment")

            if save_btn:
                if not selected_ids:
                    st.error("Please select at least one session.")
                elif selected_total <= 0:
                    st.error("Total payment must be > ₹0.")
                else:
                    pay_row = {
                        "player_id":    p_id,
                        "amount":       selected_total,
                        "payment_date": str(pay_date),
                        "notes":        pay_notes or None,
                    }
                    pay_result = sb.table("payments").insert(pay_row).execute()
                    pay_id = pay_result.data[0]["id"]

                    for att_id, amt in zip(selected_ids, selected_amounts):
                        att = next(r for r in pending if r["id"] == att_id)
                        new_paid = (att["amount_paid"] or 0) + amt
                        sb.table("attendance").update({"amount_paid": new_paid}).eq("id", att_id).execute()
                        sb.table("payment_attendance").insert({
                            "payment_id":    pay_id,
                            "attendance_id": att_id,
                            "applied_amount": amt,
                        }).execute()

                    updated_att = sb.table("attendance").select("fee_charged, amount_paid").eq("player_id", p_id).execute().data
                    new_balance = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in updated_att)
                    st.success(f"✅ Payment of ₹{selected_total:.2f} recorded. Remaining due: ₹{new_balance:.2f}")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Edit Existing Payment
# ══════════════════════════════════════════════════════════════════════════════
with tab_edit:
    # Reuse the player selected above the tabs
    ep_id      = p_id
    is_monthly = player.get("membership_type") == "monthly"
    edit_player_name = player_name

    badge_color = "var(--accent3)" if is_monthly else "var(--accent2)"
    badge_label = "Monthly member" if is_monthly else "Daily / Regular"
    st.markdown(
        f"<span style='background:rgba(167,139,250,0.15);border:1px solid {badge_color};"
        f"border-radius:50px;padding:3px 12px;font-size:0.78rem;font-weight:700;"
        f"color:{badge_color};'>{badge_label}</span>",
        unsafe_allow_html=True,
    )
    st.write("")

    edit_mode = st.radio(
        "What to edit",
        ["💰 Payment records", "📋 Session amounts"],
        horizontal=True,
        key="edit_mode_radio",
    )

    st.divider()

    # ──────────────────────────────────────────────────────────────────────
    # MODE A — Edit / delete a payment record from the payments table
    # ──────────────────────────────────────────────────────────────────────
    if edit_mode == "💰 Payment records":
        pay_records = (
            sb.table("payments")
            .select("*")
            .eq("player_id", ep_id)
            .order("payment_date", desc=True)
            .execute()
            .data
        )

        if not pay_records:
            st.info(f"No payment records found for {edit_player_name}.")
        else:
            pay_labels = [
                f"{r['payment_date']}  ·  ₹{r['amount']:.2f}"
                + (f"  · {r['notes']}" if r.get("notes") else "")
                for r in pay_records
            ]
            selected_label = st.selectbox("Choose a payment to edit", pay_labels, key="pay_sel")
            chosen_pay = pay_records[pay_labels.index(selected_label)]

            # Show linked sessions
            linked_junc = (
                sb.table("payment_attendance")
                .select("attendance_id, applied_amount")
                .eq("payment_id", chosen_pay["id"])
                .execute()
                .data
            )
            if linked_junc:
                linked_ids = [l["attendance_id"] for l in linked_junc]
                linked_att = (
                    sb.table("attendance")
                    .select("session_date, session_time")
                    .in_("id", linked_ids)
                    .execute()
                    .data
                )
                lrows = [
                    {
                        "Session date": la.get("session_date", "—"),
                        "Time":         la.get("session_time", "—").title(),
                        "Applied (₹)":  lj["applied_amount"],
                    }
                    for lj, la in zip(linked_junc, linked_att)
                ]
                with st.expander(f"🔗 {len(lrows)} linked session(s)", expanded=False):
                    st.dataframe(lrows, use_container_width=True, hide_index=True)

            with st.form("edit_payment_form"):
                st.markdown(
                    f"<span style='color:var(--accent2);font-size:0.78rem;'>"
                    f"Payment ID: {chosen_pay['id'][:8]}…</span>",
                    unsafe_allow_html=True,
                )
                new_amount = st.number_input(
                    "Amount (₹)", min_value=0.0, step=10.0, value=float(chosen_pay["amount"])
                )
                new_date = st.date_input(
                    "Payment date",
                    value=date.fromisoformat(str(chosen_pay["payment_date"])[:10]),
                )
                new_notes = st.text_input("Notes", value=chosen_pay.get("notes") or "")

                col_save, col_del = st.columns(2)
                save_edit = col_save.form_submit_button("💾 Update", use_container_width=True)
                del_btn   = col_del.form_submit_button("🗑️ Delete",  use_container_width=True)

                if save_edit:
                    diff = round(new_amount - float(chosen_pay["amount"]), 2)
                    sb.table("payments").update({
                        "amount":       new_amount,
                        "payment_date": str(new_date),
                        "notes":        new_notes or None,
                    }).eq("id", chosen_pay["id"]).execute()

                    # Spread the difference across linked attendance rows
                    if diff != 0 and linked_junc:
                        share = round(diff / len(linked_junc), 2)
                        for lnk in linked_junc:
                            att = sb.table("attendance").select("amount_paid").eq("id", lnk["attendance_id"]).execute().data
                            if att:
                                new_ap = max(0.0, round((att[0]["amount_paid"] or 0) + share, 2))
                                sb.table("attendance").update({"amount_paid": new_ap}).eq("id", lnk["attendance_id"]).execute()
                            sb.table("payment_attendance").update({
                                "applied_amount": round((lnk["applied_amount"] or 0) + share, 2)
                            }).eq("payment_id", chosen_pay["id"]).eq("attendance_id", lnk["attendance_id"]).execute()

                    st.success("✅ Payment updated.")
                    st.rerun()

                if del_btn:
                    # Reverse amount_paid on linked attendance rows before deleting
                    for lnk in linked_junc:
                        att = sb.table("attendance").select("amount_paid").eq("id", lnk["attendance_id"]).execute().data
                        if att:
                            reversed_amt = max(0.0, round((att[0]["amount_paid"] or 0) - (lnk["applied_amount"] or 0), 2))
                            sb.table("attendance").update({"amount_paid": reversed_amt}).eq("id", lnk["attendance_id"]).execute()
                    sb.table("payments").delete().eq("id", chosen_pay["id"]).execute()
                    st.success("🗑️ Payment deleted and session amounts reversed.")
                    st.rerun()

    # ──────────────────────────────────────────────────────────────────────
    # MODE B — Edit amount_paid directly on individual session rows
    # ──────────────────────────────────────────────────────────────────────
    else:
        import calendar as cal_mod

        today2 = date.today()

        if is_monthly:
            st.caption("Pick a month to edit each session's paid amount, or use the bulk-fill shortcut.")
            month_opts = sorted(
                {f"{today2.year}-{m:02d}" for m in range(1, today2.month + 1)}
                | {f"{today2.year - 1}-{m:02d}" for m in range(1, 13)},
                reverse=True,
            )
            sel_month  = st.selectbox("Month", month_opts, key="edit_month")
            yr, mo     = map(int, sel_month.split("-"))
            from_dt    = f"{sel_month}-01"
            last_d     = cal_mod.monthrange(yr, mo)[1]
            to_dt      = f"{sel_month}-{last_d:02d}"
            session_rows = (
                sb.table("attendance")
                .select("*")
                .eq("player_id", ep_id)
                .gte("session_date", from_dt)
                .lte("session_date", to_dt)
                .order("session_date")
                .execute()
                .data
            )
            if not session_rows:
                st.info(f"No sessions recorded for {edit_player_name} in {sel_month}.")
                st.stop()

            total_paid_m = sum(r["amount_paid"] or 0 for r in session_rows)
            total_fee_m  = sum(r["fee_charged"]  or 0 for r in session_rows)
            m1, m2 = st.columns(2)
            m1.metric("Month total paid", f"₹{total_paid_m:.2f}")
            m2.metric("Month total fee",  f"₹{total_fee_m:.2f}")

            # Quick bulk-fill: distribute a lump sum equally across all sessions
            st.markdown("**Quick fill — distribute a lump sum equally:**")
            bf1, bf2, bf3 = st.columns([3, 2, 1])
            bulk_total = bf1.number_input("Total amount (₹)", min_value=0.0, step=100.0, key="bulk_total")
            per_sess   = round(bulk_total / len(session_rows), 2) if session_rows else 0
            bf2.metric("Per session", f"₹{per_sess:.2f}")
            if bf3.button("Apply", use_container_width=True, key="apply_bulk"):
                for r in session_rows:
                    sb.table("attendance").update({"amount_paid": per_sess}).eq("id", r["id"]).execute()
                st.success(f"✅ ₹{bulk_total:.2f} distributed across {len(session_rows)} sessions (₹{per_sess:.2f} each).")
                st.rerun()

        else:
            st.caption("Pick a date range to edit each session's paid amount individually.")
            dr1, dr2 = st.columns(2)
            from_dt_d = dr1.date_input("From", value=date(today2.year, today2.month, 1), key="from_d")
            to_dt_d   = dr2.date_input("To",   value=today2, key="to_d")
            session_rows = (
                sb.table("attendance")
                .select("*")
                .eq("player_id", ep_id)
                .gte("session_date", str(from_dt_d))
                .lte("session_date", str(to_dt_d))
                .order("session_date")
                .execute()
                .data
            )
            if not session_rows:
                st.info("No sessions found in this date range.")
                st.stop()

        st.divider()
        st.subheader(f"📋 {edit_player_name} — {len(session_rows)} session(s)")

        with st.form("edit_sessions_form"):
            new_vals = {}
            for r in session_rows:
                charged = r["fee_charged"] or 0
                paid    = r["amount_paid"] or 0
                due     = round(charged - paid, 2)
                status_color = "var(--accent)" if due <= 0 else "var(--warn)" if due < charged else "var(--danger)"
                status_icon  = "✅" if due <= 0 else "⚠️" if due < charged else "🔴"
                col_l, col_r = st.columns([3, 2])
                col_l.markdown(
                    f"**{r['session_date']}** · {r['session_time'].title()}  \n"
                    f"<span style='color:{status_color};font-size:0.78rem;'>"
                    f"{status_icon} fee ₹{charged:.2f} · due ₹{due:.2f}</span>",
                    unsafe_allow_html=True,
                )
                new_vals[r["id"]] = col_r.number_input(
                    "Paid (₹)",
                    min_value=0.0,
                    step=10.0,
                    value=float(paid),
                    key=f"sess_{r['id']}",
                )

            save_sessions = st.form_submit_button("💾 Save All Changes", type="primary")

            if save_sessions:
                changes = 0
                for row_id, new_paid in new_vals.items():
                    orig = next(r for r in session_rows if r["id"] == row_id)
                    if round(new_paid, 2) != round((orig["amount_paid"] or 0), 2):
                        sb.table("attendance").update({"amount_paid": round(new_paid, 2)}).eq("id", row_id).execute()
                        changes += 1
                if changes:
                    st.success(f"✅ {changes} session(s) updated successfully.")
                    st.rerun()
                else:
                    st.info("No changes detected.")
