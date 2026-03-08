import streamlit as st
import pandas as pd
import math
import calendar
import numpy as np
from datetime import date
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils.styles import inject_mobile_css


# Court capacity caps
# Morning: 1 court on weekdays (Mon–Fri) → max 7 players
# Evening: 2 courts every day → max 14 players
_CAPACITY = {
    "morning_weekday": 7,
    "morning_weekend": 7,  # same single court; adjust if weekends differ
    "evening": 14,
}


def _slot_cap(slot: str, dow: int) -> int:
    """Return the hard player cap for a given slot and day-of-week (0=Mon)."""
    if slot == "evening":
        return _CAPACITY["evening"]
    return _CAPACITY["morning_weekday"] if dow < 5 else _CAPACITY["morning_weekend"]


@st.cache_data(ttl="1d", show_spinner=False)
def _train_forecast_models(attendance_json: str, target_date_str: str):
    """Train per-slot Ridge Regression models.
    Cache expires daily so the model always incorporates yesterday's sessions.
    `attendance_json` and `target_date_str` are the cache-key inputs.
    """
    import json
    from datetime import date as _date, timedelta

    attendance_rows = json.loads(attendance_json)
    tomorrow = _date.fromisoformat(target_date_str)
    tomorrow_dow = pd.Timestamp(tomorrow).dayofweek   # 0=Mon

    if not attendance_rows:
        return {"morning": (None, None), "evening": (None, None)}

    adf = pd.DataFrame(attendance_rows)
    adf["session_date"] = pd.to_datetime(adf["session_date"])

    all_counts = (
        adf[adf["session_date"].dt.date < tomorrow]
        .groupby(["session_date", "session_time"])["player_id"]
        .nunique()
        .reset_index()
        .rename(columns={"player_id": "count"})
    )
    all_counts["session_date"] = pd.to_datetime(all_counts["session_date"])
    all_counts = all_counts.sort_values("session_date")

    if all_counts.empty:
        return {"morning": (None, None), "evening": (None, None)}

    epoch = all_counts["session_date"].min()

    def _make_features(df):
        df = df.copy().reset_index(drop=True)
        df["trend"]   = (df["session_date"] - epoch).dt.days
        df["month"]   = df["session_date"].dt.month
        df["week"]    = df["session_date"].dt.isocalendar().week.astype(int)
        df["dow_enc"] = df["session_date"].dt.dayofweek
        df["lag1"]    = df["count"].shift(1).fillna(df["count"].mean())
        df["roll4"]   = df["count"].shift(1).rolling(4, min_periods=1).mean().fillna(df["count"].mean())
        return df[["trend", "month", "week", "dow_enc", "lag1", "roll4"]].values, df["count"].values

    def _fit_slot(slot):
        cap = _slot_cap(slot, tomorrow_dow)
        s = all_counts[all_counts["session_time"] == slot].copy()
        if s.empty:
            return None, None
        if len(s) < 5:          # not enough history — simple mean fallback
            avg = s["count"].mean()
            std = s["count"].std() if len(s) > 1 else 0
            pred = min(cap, max(1, math.ceil(avg)))
            lo   = max(1, math.floor(avg))
            hi   = min(cap, math.ceil(avg + std))
            return pred, f"{lo}–{hi}"

        X, y = _make_features(s)
        scaler = StandardScaler()
        X_sc   = scaler.fit_transform(X)
        model  = Ridge(alpha=1.0)
        model.fit(X_sc, y)

        last_count = s["count"].iloc[-1]
        roll4_val  = s["count"].tail(4).mean()
        x_tom = np.array([[
            (pd.Timestamp(tomorrow) - epoch).days,
            tomorrow.month,
            int(pd.Timestamp(tomorrow).isocalendar()[1]),
            tomorrow_dow,
            last_count,
            roll4_val,
        ]])
        pred_val = model.predict(scaler.transform(x_tom))[0]
        pred_int = min(cap, max(1, math.ceil(pred_val)))

        res_std = (y - model.predict(X_sc)).std() if len(y) > 1 else 0
        lo = max(1, math.floor(pred_val - res_std))
        hi = min(cap, math.ceil(pred_val + res_std))
        return pred_int, f"{lo}–{hi}"

    return {
        "morning": _fit_slot("morning"),
        "evening": _fit_slot("evening"),
    }

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
    # Monthly members: fee for THIS month only (mirrors Monthly Settlement tab view)
    fee_configs  = sb.table("monthly_fee_config").select("player_id, monthly_fee").eq("month", month_str).execute().data

    pid_to_name  = {p["id"]: p["name"] for p in players}
    monthly_pids = {p["id"] for p in players if (p.get("membership_type") or "") == "monthly"}

    # ── Derived totals ────────────────────────────────────────────────────────
    total_charged  = sum(r["fee_charged"] or 0 for r in attendance)
    total_paid     = sum(r["amount"]      or 0 for r in payments_all)

    # Payments made in the current month (used for monthly member dues)
    month_pay_by_pid: dict = {}
    for r in payments_all:
        if str(r["payment_date"])[:7] == month_str:
            pid = r["player_id"]
            month_pay_by_pid[pid] = month_pay_by_pid.get(pid, 0.0) + (r["amount"] or 0)

    # Per-player balance (positive = owes money, negative = overpaid/prepaid)
    # Monthly members: THIS month's fee_config minus THIS month's payments
    # Regular members:  all-time fee_charged minus all-time payments
    due_by_pid: dict = {}
    for r in fee_configs:
        pid = r["player_id"]
        if pid in monthly_pids:
            fee  = r["monthly_fee"] or 0
            paid = month_pay_by_pid.get(pid, 0.0)
            due_by_pid[pid] = fee - paid
    for r in attendance:
        pid = r["player_id"]
        if pid not in monthly_pids:
            due_by_pid[pid] = due_by_pid.get(pid, 0.0) + (r["fee_charged"] or 0)
    for r in payments_all:
        pid = r["player_id"]
        if pid not in monthly_pids:
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

    # ── Section 3 (was forecast): Forecast (Ridge Regression ML) ────────────
    from datetime import timedelta
    import json

    tomorrow     = today + timedelta(days=1)
    tomorrow_dow = tomorrow.strftime("%A")
    st.markdown(f"**🔮 Tomorrow's Forecast — {tomorrow_dow}, {tomorrow.strftime('%d %b')}**")
    if attendance:
        # Pass attendance as JSON so the cache key is stable and hashable.
        # Cache TTL = 1 day → model retrained automatically each day with fresh data.
        preds = _train_forecast_models(
            json.dumps([{"player_id": r["player_id"],
                         "session_date": str(r["session_date"]),
                         "session_time": r["session_time"]} for r in attendance]),
            str(tomorrow),
        )
        m_pred, m_rng = preds["morning"]
        e_pred, e_rng = preds["evening"]

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
        st.caption("Ridge Regression · retrained daily · features: trend, month, week, lag-1, 4-session rolling mean")

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
