import streamlit as st
import pandas as pd
import math
import calendar
from datetime import date
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
st.caption(f"Pro Sports Arena, Kothanur · {date.today().strftime('%A, %d %b %Y')}")

try:
    from utils.supabase_client import get_client
    sb = get_client()

    today      = date.today()
    today_str  = str(today)
    today_dow  = today.strftime("%A")
    month_str  = today.strftime("%Y-%m")
    from_month = f"{month_str}-01"
    to_month   = f"{month_str}-{calendar.monthrange(today.year, today.month)[1]:02d}"

    # ── Single batch fetch ────────────────────────────────────────────────────
    players      = sb.table("players").select("*").eq("is_active", True).execute().data
    attendance   = sb.table("attendance").select("fee_charged, player_id, session_date, session_time").execute().data
    payments_all = sb.table("payments").select("player_id, amount, payment_date, notes").order("payment_date", desc=True).execute().data
    exp_month    = sb.table("expenditures").select("amount").gte("exp_date", from_month).lte("exp_date", to_month).execute().data

    pid_to_name = {p["id"]: p["name"] for p in players}

    # ── Derived totals ────────────────────────────────────────────────────────
    total_charged  = sum(r["fee_charged"] or 0 for r in attendance)
    total_paid     = sum(r["amount"]      or 0 for r in payments_all)

    # Per-player balance (positive = owes money, negative = overpaid/prepaid)
    due_by_pid: dict = {}
    for r in attendance:
        pid = r["player_id"]
        due_by_pid[pid] = due_by_pid.get(pid, 0.0) + (r["fee_charged"] or 0)
    for r in payments_all:
        pid = r["player_id"]
        due_by_pid[pid] = due_by_pid.get(pid, 0.0) - (r["amount"] or 0)
    # Only sum positive balances — overpaid players don't cancel others' debts
    total_due      = sum(v for v in due_by_pid.values() if v > 0.005)

    month_att      = [r for r in attendance if str(r["session_date"])[:7] == month_str]
    month_charged  = sum(r["fee_charged"] or 0 for r in month_att)
    month_paid     = sum(r["amount"] or 0 for r in payments_all if str(r["payment_date"])[:7] == month_str)
    month_exp      = sum(r["amount"] or 0 for r in exp_month)
    month_profit   = month_paid - month_exp

    today_att      = [r for r in attendance if r["session_date"] == today_str]
    today_morning  = sum(1 for r in today_att if r["session_time"] == "morning")
    today_evening  = sum(1 for r in today_att if r["session_time"] == "evening")

    # ── Section 1: 2×2 headline metrics ──────────────────────────────────────
    c1, c2 = st.columns(2)
    c1.metric("Active Players",  len(players))
    c2.metric("Today's Players", today_morning + today_evening,
              f"☀️ {today_morning}  🌙 {today_evening}")
    c3, c4 = st.columns(2)
    c3.metric("Month Collected", f"₹{month_paid:,.0f}")
    c4.metric("Outstanding Dues", f"₹{total_due:,.0f}")

    st.divider()

    # ── Section 2: Today live ─────────────────────────────────────────────────
    st.markdown(f"**📅 Today's Sessions — {today.strftime('%A, %d %b %Y')}**")
    def _session_line(label, count):
        if count:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 16px;border-radius:8px;"
                f"background:rgba(5,150,105,0.08);margin-bottom:6px;'>"
                f"<span style='font-size:0.9rem;font-weight:500;'>{label}</span>"
                f"<span style='font-weight:700;color:#059669;'>{count} player{'s' if count!=1 else ''}</span>"
                f"</div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 16px;border-radius:8px;"
                f"background:rgba(100,116,139,0.07);margin-bottom:6px;'>"
                f"<span style='font-size:0.9rem;font-weight:500;'>{label}</span>"
                f"<span style='color:#94a3b8;'>not marked yet</span>"
                f"</div>",
                unsafe_allow_html=True)
    _session_line("☀️ Morning (7–8 AM)", today_morning)
    _session_line("🌙 Evening (7–8 PM)", today_evening)

    st.divider()

    # ── Section 3 (was forecast): Forecast ───────────────────────────────────
    from datetime import timedelta
    tomorrow     = today + timedelta(days=1)
    tomorrow_dow = tomorrow.strftime("%A")
    st.markdown(f"**🔮 Tomorrow's Forecast — {tomorrow_dow}, {tomorrow.strftime('%d %b')}**")
    if attendance:
        adf = pd.DataFrame(attendance)
        adf["session_date"] = pd.to_datetime(adf["session_date"])
        adf["day_of_week"]  = adf["session_date"].dt.day_name()
        hist = adf[(adf["day_of_week"] == tomorrow_dow) & (adf["session_date"].dt.date < tomorrow)]

        def _pred(slot):
            s = hist[hist["session_time"] == slot]
            if s.empty:
                return None, None
            counts = s.groupby("session_date")["player_id"].nunique().tail(8)
            avg = counts.mean()
            hi  = math.ceil((avg + counts.std()) if len(counts) > 1 else avg)
            return max(1, math.ceil(avg)), f"{max(1, math.floor(avg))}–{hi}"

        m_pred, m_rng = _pred("morning")
        e_pred, e_rng = _pred("evening")

        def _fc_line(label, pred, rng):
            if pred:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;padding:8px 16px;border-radius:8px;"
                    f"background:rgba(217,119,6,0.08);margin-bottom:6px;'>"
                    f"<span style='font-size:0.9rem;font-weight:500;'>{label}</span>"
                    f"<span style='font-weight:700;color:#92400e;'>~{pred} players "
                    f"<span style='font-size:0.8rem;font-weight:400;'>(range {rng})</span></span>"
                    f"</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;padding:8px 16px;border-radius:8px;"
                    f"background:rgba(100,116,139,0.07);margin-bottom:6px;'>"
                    f"<span style='font-size:0.9rem;font-weight:500;'>{label}</span>"
                    f"<span style='color:#94a3b8;'>no history yet</span>"
                    f"</div>",
                    unsafe_allow_html=True)
        _fc_line("☀️ Morning (7–8 AM)", m_pred, m_rng)
        _fc_line("🌙 Evening (7–8 PM)", e_pred, e_rng)
        st.caption("Based on last 8 same-weekday sessions")

    st.divider()

    # ── Section 3: This month P&L snapshot ───────────────────────────────────
    st.markdown(f"**📆 {today.strftime('%B %Y')} — Financial Snapshot**")
    m1, m2 = st.columns(2)
    m1.metric("Fees Charged", f"₹{month_charged:,.0f}")
    m2.metric("Collected",    f"₹{month_paid:,.0f}")
    m3, m4 = st.columns(2)
    m3.metric("Expenditure",  f"₹{month_exp:,.0f}")
    profit_delta = f"{'▲' if month_profit >= 0 else '▼'} ₹{abs(month_profit):,.0f}"
    m4.metric("Net Profit",      f"₹{month_profit:,.0f}",
              delta=profit_delta,
              delta_color="normal" if month_profit >= 0 else "inverse")

    st.divider()

    # ── Section 4: All players with outstanding dues ──────────────────────────
    # Build last-payment-date lookup from payments_all (already ordered desc)
    last_pay_date: dict = {}
    for r in payments_all:
        pid = r["player_id"]
        if pid not in last_pay_date:
            last_pay_date[pid] = r["payment_date"]

    all_dues = sorted(
        [{"pid": pid, "name": pid_to_name.get(pid, "Unknown"), "due": round(v, 2)}
         for pid, v in due_by_pid.items() if v > 0.5],
        key=lambda x: x["due"], reverse=True
    )

    st.markdown(f"**🔴 Pending Dues — {len(all_dues)} player(s)**")
    if not all_dues:
        st.success("✅ All players are clear — no outstanding dues!")
    else:
        for row in all_dues:
            last_p = last_pay_date.get(row["pid"])
            sub    = f"Last paid: {last_p}" if last_p else "Never paid"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 16px;border-radius:8px;"
                f"background:rgba(220,38,38,0.06);margin-bottom:6px;'>"
                f"<span style='font-size:0.9rem;'>"
                f"<span style='font-weight:500;'>{row['name']}</span>"
                f"<br><span style='color:#94a3b8;font-size:0.78rem;'>{sub}</span></span>"
                f"<span style='color:#dc2626;font-weight:700;font-size:0.95rem;'>"
                f"₹{row['due']:,.0f}</span>"
                f"</div>",
                unsafe_allow_html=True)

    st.divider()

    # ── Section 5: Upcoming anniversaries ────────────────────────────────────
    upcoming_anns = []
    for p in players:
        dj = p.get("date_joined")
        if not dj:
            continue
        joined = date.fromisoformat(str(dj)[:10])
        try:
            ann = joined.replace(year=today.year)
        except ValueError:          # Feb 29 on non-leap year
            ann = joined.replace(year=today.year, day=28)
        if ann < today:
            try:
                ann = joined.replace(year=today.year + 1)
            except ValueError:
                ann = joined.replace(year=today.year + 1, day=28)
        days_away = (ann - today).days
        if days_away <= 30:
            years_completed = ann.year - joined.year
            upcoming_anns.append({
                "name":  p["name"],
                "date":  ann.strftime("%d %b"),
                "days":  days_away,
                "years": years_completed,
            })
    upcoming_anns.sort(key=lambda x: x["days"])

    if upcoming_anns:
        st.markdown(f"**🎂 Upcoming Club Anniversaries**")
        for a in upcoming_anns:
            label   = "Today! 🎉" if a["days"] == 0 else ("Tomorrow" if a["days"] == 1 else f"In {a['days']} days")
            yrs_txt = f"{a['years']} year{'s' if a['years'] != 1 else ''}"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 16px;border-radius:8px;"
                f"background:rgba(217,119,6,0.08);margin-bottom:6px;'>"
                f"<span style='font-size:0.9rem;'>"
                f"<span style='font-weight:500;'>{a['name']}</span>"
                f"<br><span style='color:#92400e;font-size:0.78rem;'>{a['date']} · {yrs_txt} with the club</span></span>"
                f"<span style='color:#d97706;font-weight:700;font-size:0.9rem;'>{label}</span>"
                f"</div>",
                unsafe_allow_html=True)
        st.divider()

    # ── Section 6: Recent payments ────────────────────────────────────────────
    st.markdown("**💚 Recent Payments**")
    if not payments_all:
        st.caption("No payments recorded yet.")
    else:
        for r in payments_all[:5]:
            name      = pid_to_name.get(r["player_id"], "Unknown")
            notes_txt = r["notes"] or ""
            method    = notes_txt.split(" — ")[0] if notes_txt else ""
            sub       = r["payment_date"] + (f" · {method}" if method else "")
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 16px;border-radius:8px;"
                f"background:rgba(5,150,105,0.06);margin-bottom:6px;'>"
                f"<span style='font-size:0.9rem;'>"
                f"<span style='font-weight:500;'>{name}</span>"
                f"<br><span style='color:#64748b;font-size:0.78rem;'>{sub}</span></span>"
                f"<span style='color:#059669;font-weight:700;font-size:0.95rem;'>"
                f"₹{r['amount']:,.0f}</span>"
                f"</div>",
                unsafe_allow_html=True)

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
    st.page_link("pages/3_Record_Payment.py",     label="💳 Collect\nPayment",        use_container_width=True)
with c4:
    st.page_link("pages/4_Manage_Players.py",     label="🧑‍🤝‍🧑 Manage\nPlayers",   use_container_width=True)

# Row 3
c5, c6 = st.columns(2)
with c5:
    st.page_link("pages/5_Monthly_Settlement.py", label="📅 Monthly\nDues",           use_container_width=True)
with c6:
    st.page_link("pages/6_Analytics.py",          label="📊 Analytics",               use_container_width=True)

# Row 4 centre
c7, c8 = st.columns(2)
with c7:
    st.page_link("pages/7_Expenditure.py",        label="💸 Expenditure",             use_container_width=True)

st.caption("Sessions: 7–8 AM & 7–8 PM · Pro Sports Arena, Kothanur")
