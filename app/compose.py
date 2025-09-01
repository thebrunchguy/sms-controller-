from typing import Sequence

def _fmt(value, max_len: int = 40):
    if value is None or value == "":
        return "—"
    if isinstance(value, (list, tuple)):
        value = ", ".join(map(str, value))
    s = str(value).strip()
    return (s[:max_len] + "…") if len(s) > max_len else s

def compose_snapshot(person_fields: dict, fields: Sequence[str] = ("Company","Role","City","Tags")) -> str:
    lines = [f"• {k}: {_fmt(person_fields.get(k))}" for k in fields]
    return "\n".join(lines)

def compose_outbound(name: str, snapshot: str, last_confirmed: str | None) -> str:
    last = last_confirmed or "last month"
    return (
        f"Hi {name}! Monthly check-in. Here’s what I have:\n"
        f"{snapshot}\n"
        f"Anything changed since {last}?\n"
        "Reply with updates or 'No change'. Reply STOP to opt out."
    )
