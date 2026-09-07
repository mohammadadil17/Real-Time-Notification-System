from collections import Counter

from app.models.event import Event

# Stub for the AI-powered digest feature: no LLM API key yet, so this groups
# events with a rule-based summary instead. The signature is the real
# integration point — a future LLM-backed version (build a prompt from
# `events`, call the model, return its text) can replace this function body
# without touching the digest worker or anything else that calls it.

_TYPE_LABELS = {
    "order": "order update",
    "payment": "payment update",
    "delivery": "delivery update",
}


def generate_digest(events: list[Event]) -> str:
    if len(events) == 1:
        event = events[0]
        return f"You have 1 new {_TYPE_LABELS.get(event.type, event.type)}."

    counts = Counter(event.type for event in events)
    parts = [
        f"{count} {_TYPE_LABELS.get(event_type, event_type)}{'s' if count > 1 else ''}"
        for event_type, count in counts.items()
    ]
    return "You have " + ", ".join(parts) + "."
