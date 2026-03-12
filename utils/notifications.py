# Notifications placeholder — admin shares updates via WhatsApp screenshots.


def format_invite_message(player_name: str, session_date: str, slot: str) -> str:
    return (
        f"Hi {player_name}! 🏸\n"
        f"You've been invited to play on {session_date} ({slot}).\n"
        f"Open the app to accept!\n"
        f"— Badminton Pro Hub"
    )


def format_confirmation_message(player_name: str, session_date: str, slot: str) -> str:
    return (
        f"Hi {player_name}! 🏸\n"
        f"Your spot is confirmed for {session_date} ({slot}).\n"
        f"See you on court! 💪\n"
        f"— Badminton Pro Hub"
    )
