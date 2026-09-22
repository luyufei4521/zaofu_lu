"""Stable lock and in-flight lookup for Channel synthesis requests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def channel_synthesis_lock_path(
    state_dir: Path,
    channel_id: str,
    thread_id: str,
) -> Path:
    digest = hashlib.sha1(
        f"channel-synthesis:{channel_id}:{thread_id}".encode("utf-8")
    ).hexdigest()[:16]
    return Path(state_dir) / "locks" / f"channel-synthesis-{digest}"


def synthesis_request_in_flight(
    channel: dict[str, Any],
    thread_id: str,
) -> dict[str, Any] | None:
    """Return the active request for this discussion generation, if present.

    A synthesis request is recorded before its provider reply is dispatched.
    If that reply later reaches a terminal failure, the request must no longer
    reserve the synthesis gate; otherwise an operator retry is reported as
    ``already_requested`` forever.
    """
    sessions = channel.get("discussions")
    session = sessions.get(thread_id) if isinstance(sessions, dict) else {}
    if not isinstance(session, dict):
        session = {}
    if (
        str(session.get("state") or "") == "phase2_relay"
        and str(session.get("phase_reason") or "")
        in {"synthesis_questions_opened", "consensus_blocked"}
    ):
        return None
    for item in reversed(channel.get("synthesis_requests") or []):
        if not isinstance(item, dict):
            continue
        if str(item.get("thread_id") or "main") != thread_id:
            continue
        if str(item.get("status") or "requested") in {"blocked", "stale_ignored"}:
            continue
        request_id = str(item.get("request_id") or "")
        failed_reply = _failed_synthesis_reply(
            channel,
            thread_id=thread_id,
            request_id=request_id,
        )
        if failed_reply:
            continue
        return item
    return None


def _failed_synthesis_reply(
    channel: dict[str, Any],
    *,
    thread_id: str,
    request_id: str,
) -> bool:
    """Whether the provider reply linked to ``request_id`` terminally failed."""

    if not request_id:
        return False
    replies = channel.get("reply_requests") or {}
    values = replies.values() if isinstance(replies, dict) else replies
    expected_message_id = f"msg-{request_id}"
    terminal_failures = {"failed", "cancelled", "rejected", "escalated"}
    return any(
        isinstance(reply, dict)
        and str(reply.get("thread_id") or "main") == thread_id
        and (
            str(reply.get("message_id") or "") == expected_message_id
            or str(reply.get("request_id") or "") == request_id
        )
        and str(reply.get("status") or "") in terminal_failures
        for reply in values
    )
