import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        try:
            import streamlit as st
            url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
        except Exception:
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")

        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_KEY. "
                "Add them to .streamlit/secrets.toml or your .env file."
            )
        _client = create_client(url, key)
    return _client


# ── Convenience query helpers ──────────────────────────────


def fetch_all(table: str, *, order: str | None = None, filters: dict | None = None):
    """Return rows from *table*."""
    q = get_client().table(table).select("*")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    if order:
        q = q.order(order)
    return q.execute().data


def fetch_view(view: str):
    return get_client().table(view).select("*").execute().data


def insert_row(table: str, data: dict):
    return get_client().table(table).insert(data).execute()


def update_row(table: str, row_id: str, data: dict):
    return get_client().table(table).update(data).eq("id", row_id).execute()


def delete_row(table: str, row_id: str):
    return get_client().table(table).delete().eq("id", row_id).execute()


def upsert_row(table: str, data: dict):
    return get_client().table(table).upsert(data).execute()


def bulk_update(table: str, ids: list[str], data: dict):
    return get_client().table(table).update(data).in_("id", ids).execute()


# ── Status transition helpers (the "app" feel) ─────────────


def request_to_join(session_id: str, player_id: str, fee: float):
    """Player requests to join a session → status='pending'."""
    return insert_row("attendance", {
        "session_id": session_id,
        "player_id": player_id,
        "status": "pending",
        "fee_charged": fee,
    })


def confirm_request(attendance_id: str):
    """Coach confirms a pending request → status='confirmed'."""
    return update_row("attendance", attendance_id, {"status": "confirmed"})


def reject_request(attendance_id: str):
    """Coach rejects a pending request → status='rejected'."""
    return update_row("attendance", attendance_id, {"status": "rejected"})


def send_invite(session_id: str, player_id: str, fee: float):
    """Coach invites a player → status='invited'."""
    return insert_row("attendance", {
        "session_id": session_id,
        "player_id": player_id,
        "status": "invited",
        "fee_charged": fee,
    })


def bulk_confirm(ids: list[str]):
    """Coach bulk-confirms a list of pending attendance IDs."""
    return bulk_update("attendance", ids, {"status": "confirmed"})


# ── Fee & Payment helpers with audit trail ──────────────────


def set_player_fee(attendance_id: str, session_id: str, player_id: str,
                   old_fee: float, new_fee: float, changed_by: str = "coach"):
    """Set or update a player's fee for a session and log it."""
    action = "fee_set" if old_fee == 0 else "fee_updated"
    update_row("attendance", attendance_id, {"fee_charged": new_fee})
    insert_row("fee_audit_log", {
        "attendance_id": attendance_id,
        "player_id": player_id,
        "session_id": session_id,
        "action": action,
        "old_value": float(old_fee),
        "new_value": float(new_fee),
        "changed_by": changed_by,
    })


def record_payment_with_audit(attendance_id: str, session_id: str,
                              player_id: str, amount: float,
                              payment_date: str, changed_by: str = "player",
                              notes: str | None = None):
    """Player marks a session as paid. Records payment + audit log entry.
    Also inserts into the payments table for the global ledger."""
    # Get current state
    row = get_client().table("attendance").select("amount_paid, fee_charged").eq(
        "id", attendance_id
    ).single().execute().data
    old_paid = float(row["amount_paid"])
    new_paid = old_paid + amount

    # Update attendance
    update_row("attendance", attendance_id, {"amount_paid": new_paid})

    # Global payments ledger
    insert_row("payments", {
        "player_id": player_id,
        "amount": float(amount),
        "payment_date": payment_date,
        "notes": notes,
    })

    # Audit log
    insert_row("fee_audit_log", {
        "attendance_id": attendance_id,
        "player_id": player_id,
        "session_id": session_id,
        "action": "payment_recorded",
        "old_value": old_paid,
        "new_value": new_paid,
        "changed_by": changed_by,
        "notes": notes,
    })


# ── Venue / Court constants ─────────────────────────────────

VENUES = {
    "Pro-Sports": {"courts": [1, 2, 3]},
    "Hermes":     {"courts": [1, 2, 3, 4, 5, 6, 7]},
}


def accept_invite(attendance_id: str, fee: float):
    """Player accepts an invite → status='confirmed'."""
    return update_row("attendance", attendance_id, {
        "status": "confirmed",
        "fee_charged": fee,
    })


def decline_invite(attendance_id: str):
    """Player declines an invite → status='rejected'."""
    return update_row("attendance", attendance_id, {"status": "rejected"})


def bulk_confirm(attendance_ids: list[str]):
    """Coach bulk-confirms all pending requests."""
    return bulk_update("attendance", attendance_ids, {"status": "confirmed"})
