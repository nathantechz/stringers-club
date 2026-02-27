"""Shared helper utilities used across multiple pages."""


def skill_label(v: int) -> str:
    """Human-readable label for a skill level 1-10."""
    v = int(v or 5)
    if v <= 2:  return f"{v} — Beginner"
    if v <= 4:  return f"{v} — Casual"
    if v <= 6:  return f"{v} — Intermediate"
    if v <= 8:  return f"{v} — Advanced"
    if v == 9:  return f"{v} — Expert"
    return              f"{v} — Pro 🏆"


WORK_TIMINGS = [
    "9 AM – 6 PM (Office)",
    "10 AM – 7 PM (Office)",
    "8 AM – 5 PM (Office)",
    "Night shift",
    "Flexible / WFH",
    "Student",
    "Business owner",
    "Other / Not specified",
]
