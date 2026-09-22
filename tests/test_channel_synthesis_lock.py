from __future__ import annotations

from zf.runtime.channel_synthesis_lock import synthesis_request_in_flight


def _channel(reply_status: str = "") -> dict:
    replies = {}
    if reply_status:
        replies["reply-synth-1"] = {
            "request_id": "reply-synth-1",
            "thread_id": "main",
            "message_id": "msg-synth-1",
            "status": reply_status,
        }
    return {
        "discussions": {"main": {"state": "phase3_synthesis"}},
        "synthesis_requests": [{
            "request_id": "synth-1",
            "thread_id": "main",
            "status": "requested",
        }],
        "reply_requests": replies,
    }


def test_terminal_synthesis_reply_releases_gate() -> None:
    channel = _channel("failed")
    channel["reply_requests"]["reply-synth-1"]["request_id"] = "synth-1"
    channel["reply_requests"]["reply-synth-1"]["message_id"] = "msg-synth-1"

    assert synthesis_request_in_flight(channel, "main") is None


def test_non_terminal_synthesis_reply_keeps_gate() -> None:
    channel = _channel("running")
    channel["reply_requests"]["reply-synth-1"]["request_id"] = "synth-1"

    assert synthesis_request_in_flight(channel, "main") == channel["synthesis_requests"][0]


def test_unrelated_failed_reply_does_not_release_gate() -> None:
    channel = _channel("failed")
    channel["reply_requests"]["reply-synth-1"]["request_id"] = "other-request"
    channel["reply_requests"]["reply-synth-1"]["message_id"] = "msg-other-request"

    assert synthesis_request_in_flight(channel, "main") == channel["synthesis_requests"][0]
