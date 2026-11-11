from typing import Tuple


def get_score_color(score: float) -> Tuple[str, str]:
    """Return (text_color, background_color) for a 0–100 score."""
    if score >= 80:
        return "#137567", "#e5f2ed"  # green
    if score >= 60:
        return "#a96914", "#fff1d8"  # amber
    return "#b63b48", "#fcecef"      # red


def get_score_emoji(score: float) -> str:
    """Emoji that matches the score band — used in headlines."""
    if score >= 90:
        return "🌟"
    if score >= 80:
        return "✅"
    if score >= 70:
        return "👍"
    if score >= 60:
        return "⚠️"
    return "🔴"


def get_severity_style(severity: str) -> Tuple[str, str, str]:
    """
    Return (icon, text_color, background_color) for an IssueDetail severity.
    Matches the values the backend emits in `detailed_feedback[].severity_level`.
    """
    level = (severity or "").lower()
    if level in ("critical", "high"):
        return "🔴", "#b63b48", "#fcecef"
    if level == "medium":
        return "🟡", "#a96914", "#fff1d8"
    return "🟢", "#137567", "#e5f2ed"
