"""Bounded active-event queries for short-lived provider hooks."""

from __future__ import annotations

from zf.core.events.log import EventLog
from zf.core.events.model import ZfEvent


def read_active_event_tail(
    event_log: EventLog,
    *,
    max_bytes: int = 8 * 1024 * 1024,
) -> list[ZfEvent]:
    """Decode complete events from a bounded tail of the active segment."""
    path = event_log.path
    size = path.stat().st_size
    start = max(0, size - max(int(max_bytes), 64 * 1024))
    with path.open("rb") as handle:
        handle.seek(start)
        raw = handle.read()
    if start:
        newline = raw.find(b"\n")
        if newline < 0:
            return []
        raw = raw[newline + 1 :]
    events: list[ZfEvent] = []
    for line in raw.splitlines():
        event = event_log.decode_line(line.decode("utf-8", "replace"))
        if event is not None:
            events.append(event)
    return events


def orphan_already_recorded(event_log: EventLog, *, session_id: str) -> bool:
    """Best-effort orphan de-duplication within the bounded active tail."""
    if not session_id:
        return False
    try:
        for event in reversed(read_active_event_tail(event_log)):
            if event.type != "hook.orphan_event":
                continue
            payload = event.payload if isinstance(event.payload, dict) else {}
            if str(payload.get("session_id") or "") == session_id:
                return True
    except Exception:
        return False
    return False


def completed_tail_quiesced(event_log: EventLog) -> bool:
    """Evaluate completed-run quiescence without replaying event archives."""
    try:
        from zf.autoresearch.failure_signals import completed_run_quiesced

        return completed_run_quiesced(read_active_event_tail(event_log))
    except Exception:
        return False
