"""
Page 3 — Collect Payment  (revamped)

Three payment workflows:
  • ⚡ Quick Pay   — daily players pay for today's / recent session on the spot
  • 📅 Monthly     — monthly members pay a lump sum upfront for the month
  • 📋 Sessions    — pick any unpaid sessions and settle them (works for both)

Tab 2: History & edit / delete past payments.
"""

import streamlit as st
from datetime import date
import calendar
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.supabase_client import get_client
from utils.styles import inject_mobile_css
from utils.helpers import show_back_button

st.set_page_config(page_title="Collect Payment", page_icon="💳", layout="centered")
inject_mobile_css()
show_back_button()
st.markdown("## 💳 Collect Payment")
st.caption("Record money received from players — cash, UPI, or monthly lump sum.")

sb = get_client()

# ── Player selector ───────────────────────────────────────────────────────────
players_raw = sb.table("players").select("*").eq("is_active", True).order("name").execute().data
if not players_raw:
    st.info("No active players. Add some on the Manage Players page.")
    st.stop()

player_name = st.selectbox("Select player", [p["name"] for p in players_raw], key="player_select")
player     = next(p for p in players_raw if p["name"] == player_name)
p_id       = player["id"]
is_monthly = player.get("membership_type") == "monthly"

# ── Player status card ────────────────────────────────────────────────────────
all_att = (
    sb.table("attendance")
    .select("fee_charged, amount_paid")
    .eq("player_id", p_id)
    .execute()
    .data
)
total_due      = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in all_att)
total_charged  = sum(r["fee_charged"]  or 0 for r in all_att)
total_paid_all = sum(r["amount_paid"]  or 0 for r in all_att)

mem_color = "var(--accent3)" if is_monthly else "var(--accent2)"
mem_label = "📅 Monthly member" if is_monthly else "🏸 Daily / Regular"
st.markdown(
    f"<span style='background:rgba(2,132,199,0.08);border:1.5px solid {mem_color};"
    f"border-radius:50px;padding:4px 14px;font-size:0.82rem;font-weight:700;"
    f"color:{mem_color};'>{mem_label}</span>",
    unsafe_allow_html=True,
)
st.write("")

mc1, mc2, mc3 = st.columns(3)
mc1.metric("Balance Due",   f"₹{total_due:,.0f}")
mc2.metric("Total Charged", f"₹{total_charged:,.0f}")
mc3.metric("Total Paid",    f"₹{total_paid_all:,.0f}")

st.divider()

tab_pay, tab_history = st.tabs(["💳 Record Payment", "📜 History & Edit"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Record Payment
# ══════════════════════════════════════════════════════════════════════════════
with tab_pay:

    default_mode = "📅 Monthly Lump Sum" if is_monthly else "⚡ Quick Pay (today's session)"
    MODE_OPTS = [
        "⚡ Quick Pay (today's session)",
        "📅 Monthly Lump Sum",
        "📋 Settle Pending Sessions",
    ]
    pay_mode = st.radio(
        "Payment type",
        MODE_OPTS,
        index=MODE_OPTS.index(default_mode),
        horizontal=False,
        key="pay_mode_radio",
    )
    st.divider()

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 1 — Quick Pay: today's or most recent unpaid session(s)
    # ──────────────────────────────────────────────────────────────────────────
    if pay_mode == "⚡ Quick Pay (today's session)":
        today_str = str(date.today())

        today_att = (
            sb.table("attendance")
            .select("*")
            .eq("player_id", p_id)
            .eq("session_date", today_str)
            .order("session_time")
            .execute()
            .data
        )

        recent_unpaid = []
        if not today_att:
            recent_unpaid = (
                sb.table("attendance")
                .select("*")
                .eq("player_id", p_id)
                .lt("session_date", today_str)
                .order("session_date", desc=True)
                .limit(6)
                .execute()
                .data
            )
            recent_unpaid = [r for r in recent_unpaid
                             if round((r["fee_charged"] or 0) - (r["amount_paid"] or 0), 2) > 0]

        sessions_to_show = today_att if today_att else recent_unpaid

        if not sessions_to_show:
            st.info(f"No sessions found for {player_name} today and no recent unpaid sessions.")
        else:
            if today_att:
                st.subheader(f"Today — {date.today().strftime('%A, %d %b %Y')}")
            else:
                st.subheader("Recent unpaid sessions")

            qp_date = st.date_input(
                "Payment date",
                value=date.today(),
                key="qp_pay_date",
                help="Date the money was actually received",
            )

            for r in sessions_to_show:
                charged = r["fee_charged"] or 0
                paid    = r["amount_paid"] or 0
                due     = round(charged - paid, 2)

                with st.container(border=True):
                    ca, cb = st.columns([3, 2])
                    ca.markdown(f"**{r['session_date']}** · {r['session_time'].title()}")
                    ca.caption(f"Fee ₹{charged:.2f}  ·  Paid ₹{paid:.2f}  ·  Due ₹{due:.2f}")

                    if due > 0:
                        qp_amt = cb.number_input(
                            "Amount (₹)",
                            min_value=0.0,
                            max_value=float(charged),
                            value=float(due),
                            step=10.0,
                            key=f"qp_amt_{r['id']}",
                            label_visibility="collapsed",
                        )
                        pay_method = cb.selectbox(
                            "Method",
                            ["Cash", "UPI", "Bank Transfer", "Other"],
                            key=f"qp_method_{r['id']}",
                            label_visibility="collapsed",
                        )
                        if cb.button(
                            f"💰 Pay ₹{qp_amt:.0f}",
                            key=f"qp_btn_{r['id']}",
                            use_container_width=True,
                            type="primary",
                        ):
                            new_paid = round(paid + qp_amt, 2)
                            pr = sb.table("payments").insert({
                                "player_id":    p_id,
                                "amount":       qp_amt,
                                "payment_date": str(qp_date),
                                "notes":        pay_method,
                            }).execute()
                            pay_id = pr.data[0]["id"]
                            sb.table("attendance").update({"amount_paid": new_paid}).eq("id", r["id"]).execute()
                            sb.table("payment_attendance").insert({
                                "payment_id":    pay_id,
                                "attendance_id": r["id"],
                                "applied_amount": qp_amt,
                            }).execute()
                            st.success(f"✅ ₹{qp_amt:.2f} recorded via {pay_method}.")
                            st.rerun()
                    else:
                        cb.success("Cleared ✅")

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 2 — Monthly Lump Sum
    # ──────────────────────────────────────────────────────────────────────────
    elif pay_mode == "📅 Monthly Lump Sum":
        today2 = date.today()
        month_opts = sorted(
            {f"{today2.year}-{m:02d}" for m in range(1, today2.month + 1)}
            | {f"{today2.year - 1}-{m:02d}" for m in range(1, 13)},
            reverse=True,
        )
        sel_month = st.selectbox("Month", month_opts, key="lump_month")
        yr, mo    = map(int, sel_month.split("-"))
        from_dt   = f"{sel_month}-01"
        last_d    = calendar.monthrange(yr, mo)[1]
        to_dt     = f"{sel_month}-{last_d:02d}"

        fee_conf = (
            sb.table("monthly_fee_config")
            .select("monthly_fee")
            .eq("player_id", p_id)
            .eq("month", sel_month)
            .execute()
            .data
        )
        default_fee = fee_conf[0]["monthly_fee"] if fee_conf else (player.get("monthly_fee") or 0.0)

        month_att = (
            sb.table("attendance")
            .select("fee_charged, amount_paid")
            .eq("player_id", p_id)
            .gte("session_date", from_dt)
            .lte("session_date", to_dt)
            .execute()
            .data
        )
        month_sessions = len(month_att)
        month_paid     = sum(r["amount_paid"] or 0 for r in month_att)

        mm1, mm2, mm3 = st.columns(3)
        mm1.metric("Sessions this month", month_sessions)
        mm2.metric("Already paid",        f"₹{month_paid:.0f}")
        mm3.metric("Monthly fee",         f"₹{default_fee:.0f}")
        st.write("")

        with st.form("lump_sum_form"):
            lump_amount = st.number_input(
                "Amount received (₹)",
                min_value=0.0,
                step=100.0,
                value=float(max(0.0, default_fee - month_paid)),
            )
            ls1, ls2    = st.columns(2)
            lump_date   = ls1.date_input("Payment date", value=date.today())
            lump_method = ls2.selectbox("Method", ["Cash", "UPI", "Bank Transfer", "Other"])
            lump_notes  = st.text_input("Additional notes (optional)")
            distribute  = st.checkbox(
                "Distribute equally across this month's sessions",
                value=(month_sessions > 0),
                help="Splits the amount across all sessions attended this month",
            )
            lump_save = st.form_submit_button("💾 Record Payment", type="primary", use_container_width=True)

            if lump_save:
                if lump_amount <= 0:
                    st.error("Amount must be > ₹0.")
                else:
                    note_parts = [f"{sel_month} monthly", lump_method]
                    if lump_notes:
                        note_parts.append(lump_notes)
                    pr = sb.table("payments").insert({
                        "player_id":    p_id,
                        "amount":       lump_amount,
                        "payment_date": str(lump_date),
                        "notes":        " — ".join(note_parts),
                    }).execute()
                    pay_id = pr.data[0]["id"]

                    if distribute and month_sessions > 0:
                        month_att_full = (
                            sb.table("attendance")
                            .select("id, amount_paid")
                            .eq("player_id", p_id)
                            .gte("session_date", from_dt)
                            .lte("session_date", to_dt)
                            .execute()
                            .data
                        )
                        per_sess = round(lump_amount / len(month_att_full), 2)
                        for r in month_att_full:
                            new_paid = round((r["amount_paid"] or 0) + per_sess, 2)
                            sb.table("attendance").update({"amount_paid": new_paid}).eq("id", r["id"]).execute()
                            sb.table("payment_attendance").insert({
                                "payment_id":    pay_id,
                                "attendance_id": r["id"],
                                "applied_amount": per_sess,
                            }).execute()
                        st.success(
                            f"✅ ₹{lump_amount:.2f} recorded and split across "
                            f"{len(month_att_full)} sessions (₹{per_sess:.2f} each)."
                        )
                    else:
                        st.success(f"✅ ₹{lump_amount:.2f} recorded for {sel_month}.")
                    st.rerun()

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 3 — Settle Pending Sessions (any date range)
    # ──────────────────────────────────────────────────────────────────────────
    else:
        today3   = date.today()
        fc1, fc2 = st.columns(2)
        from_d3  = fc1.date_input("From", value=date(today3.year, today3.month, 1), key="sp_from")
        to_d3    = fc2.date_input("To",   value=today3, key="sp_to")

        all_sess = (
            sb.table("attendance")
            .select("*")
            .eq("player_id", p_id)
            .gte("session_date", str(from_d3))
            .lte("session_date", str(to_d3))
            .order("session_date", desc=True)
            .execute()
            .data
        )
        pending = [r for r in all_sess
                   if round((r["fee_charged"] or 0) - (r["amount_paid"] or 0), 2) > 0]

        if not pending:
            st.success(f"✅ No pending dues for {player_name} in this date range.")
        else:
            st.caption(f"{len(pending)} session(s) with outstanding balance")

            sa1, sa2   = st.columns(2)
            select_all = sa1.button("☑️ Select All", use_container_width=True, key="sp_sel_all")
            clear_all  = sa2.button("🔲 Clear All",  use_container_width=True, key="sp_clr_all")

            selected_ids     = []
            selected_amounts = []

            for r in pending:
                due = round((r["fee_charged"] or 0) - (r["amount_paid"] or 0), 2)
                with st.container(border=True):
                    cl, cr  = st.columns([3, 2])
                    default_checked = select_all and not clear_all
                    checked = cl.checkbox(
                        f"**{r['session_date']}** · {r['session_time'].title()}",
                        key=f"sp_chk_{r['id']}",
                        value=default_checked,
                    )
                    cl.caption(
                        f"Fee ₹{r['fee_charged'] or 0:.2f}  ·  "
                        f"Paid ₹{r['amount_paid'] or 0:.2f}  ·  Due ₹{due:.2f}"
                    )
                    pay_amt = cr.number_input(
                        "Pay (₹)",
                        min_value=0.0,
                        max_value=float(r["fee_charged"] or due),
                        value=float(due),
                        step=10.0,
                        key=f"sp_amt_{r['id']}",
                    )
                    if checked:
                        selected_ids.append(r["id"])
                        selected_amounts.append(pay_amt)

            selected_total = sum(selected_amounts)
            if selected_ids:
                st.markdown(f"### Total to collect: ₹{selected_total:,.2f}")
            st.divider()

            with st.form("settle_sessions_form"):
                sf1, sf2   = st.columns(2)
                pay_date   = sf1.date_input("Payment date", value=date.today())
                pay_method = sf2.selectbox("Method", ["Cash", "UPI", "Bank Transfer", "Other"])
                pay_notes  = st.text_input("Additional notes (optional)")
                save_btn   = st.form_submit_button("💾 Record Payment", type="primary", use_container_width=True)

                if save_btn:
                    if not selected_ids:
                        st.error("Please select at least one session.")
                    elif selected_total <= 0:
                        st.error("Total must be > ₹0.")
                    else:
                        note_str = pay_method + (f" — {pay_notes}" if pay_notes else "")
                        pr = sb.table("payments").insert({
                            "player_id":    p_id,
                            "amount":       selected_total,
                            "payment_date": str(pay_date),
                            "notes":        note_str,
                        }).execute()
                        pay_id = pr.data[0]["id"]

                        for att_id, amt in zip(selected_ids, selected_amounts):
                            att = next(r for r in pending if r["id"] == att_id)
                            new_paid = round((att["amount_paid"] or 0) + amt, 2)
                            sb.table("attendance").update({"amount_paid": new_paid}).eq("id", att_id).execute()
                            sb.table("payment_attendance").insert({
                                "payment_id":    pay_id,
                                "attendance_id": att_id,
                                "applied_amount": amt,
                            }).execute()

                        updated = (
                            sb.table("attendance")
                            .select("fee_charged, amount_paid")
                            .eq("player_id", p_id)
                            .execute()
                            .data
                        )
                        new_bal = sum((r["fee_charged"] or 0) - (r["amount_paid"] or 0) for r in updated)
                        st.success(
                            f"✅ ₹{selected_total:.2f} recorded via {pay_method}. "
                            f"Overall balance remaining: ₹{new_bal:.2f}"
                        )
                        st.rerun()



# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — History & Edit
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    pay_records = (
        sb.table("payments")
        .select("*")
        .eq("player_id", p_id)
        .order("payment_date", desc=True)
        .execute()
        .data
    )

    if not pay_records:
        st.info(f"No payment history for {player_name} yet.")
    else:
        total_ever = sum(r["amount"] for r in pay_records)
        st.metric("Total ever paid", f"₹{total_ever:,.2f}")
        st.write("")

        for r in pay_records:
            with st.container(border=True):
                h1, h2 = st.columns([5, 1])
                h1.markdown(
                    f"**{r['payment_date']}** &nbsp;·&nbsp; ₹{r['amount']:.2f}"
                    + (f"  \n_{r['notes']}_" if r.get("notes") else "")
                )

                linked = (
                    sb.table("payment_attendance")
                    .select("attendance_id, applied_amount")
                    .eq("payment_id", r["id"])
                    .execute()
                    .data
                )
                if linked:
                    linked_ids = [l["attendance_id"] for l in linked]
                    linked_att = (
                        sb.table("attendance")
                        .select("session_date, session_time")
                        .in_("id", linked_ids)
                        .execute()
                        .data
                    )
                    h1.caption(
                        "Sessions: " + ", ".join(
                            f"{a.get('session_date', '?')} {a.get('session_time', '').title()}"
                            for a in linked_att
                        )
                    )

                if h2.button("🗑️", key=f"del_pay_{r['id']}", help="Delete this payment"):
                    for lnk in linked:
                        att = sb.table("attendance").select("amount_paid").eq("id", lnk["attendance_id"]).execute().data
                        if att:
                            rev = max(0.0, round((att[0]["amount_paid"] or 0) - (lnk["applied_amount"] or 0), 2))
                            sb.table("attendance").update({"amount_paid": rev}).eq("id", lnk["attendance_id"]).execute()
                    sb.table("payments").delete().eq("id", r["id"]).execute()
                    st.success("🗑️ Payment deleted and session balances reversed.")
                    st.rerun()

        st.divider()
        with st.expander("✏️ Edit a payment", expanded=False):
            pay_labels = [
                f"{r['payment_date']}  ·  ₹{r['amount']:.2f}"
                + (f"  · {r['notes']}" if r.get("notes") else "")
                for r in pay_records
            ]
            sel_label = st.selectbox("Choose payment", pay_labels, key="edit_pay_sel")
            chosen    = pay_records[pay_labels.index(sel_label)]

            with st.form("edit_payment_form"):
                e1, e2     = st.columns(2)
                new_amount = e1.number_input("Amount (₹)", min_value=0.0, step=10.0, value=float(chosen["amount"]))
                new_date   = e2.date_input("Date", value=date.fromisoformat(str(chosen["payment_date"])[:10]))
                new_notes  = st.text_input("Notes", value=chosen.get("notes") or "")
                update_btn = st.form_submit_button("💾 Update Payment")

                if update_btn:
                    sb.table("payments").update({
                        "amount":       new_amount,
                        "payment_date": str(new_date),
                        "notes":        new_notes or None,
                    }).eq("id", chosen["id"]).execute()
                    st.success("✅ Payment updated.")
                    st.rerun()


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
            .eq("player_id", p_id)
            .order("payment_date", desc=True)
            .execute()
            .data
        )

        if not pay_records:
            st.info(f"No payment records found for {player_name}.")
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
                .eq("player_id", p_id)
                .gte("session_date", from_dt)
                .lte("session_date", to_dt)
                .order("session_date")
                .execute()
                .data
            )
            if not session_rows:
                st.info(f"No sessions recorded for {player_name} in {sel_month}.")
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
                .eq("player_id", p_id)
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
        st.subheader(f"📋 {player_name} — {len(session_rows)} session(s)")

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
