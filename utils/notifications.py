# WhatsApp notifications removed — admin shares screenshots directly via WhatsApp.
# File kept as placeholder so existing imports don't crash during transition.


def format_due_message(player_name: str, balance_due: float) -> str:
    return (
        f"Hi {player_name}! 🏸\n"
        f"Your current due at StringerS Badminton Club is ₹{balance_due:.2f}.\n"
        f"Please clear your dues at the earliest. Thank you!\n"
        f"— StringerS Club"
    )


def format_payment_message(player_name: str, amount_paid: float, balance_due: float) -> str:
    return (
        f"Hi {player_name}! 🏸\n"
        f"Payment of ₹{amount_paid:.2f} received. Thank you!\n"
        f"Remaining balance: ₹{balance_due:.2f}.\n"
        f"— StringerS Club"
    )
