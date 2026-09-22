"""Reader restart regression; see docs/impl/reader-restart-result-priority.md."""

from pathlib import Path

from zf.core.events.model import ZfEvent
from tests.test_reader_fanout_runtime import _manifest, _start_fanout, _state


def test_restart_admits_pending_result_before_recovering_replaced_session(
    tmp_path: Path,
) -> None:
    state_dir, log, transport, orch = _state(tmp_path)
    _start_fanout(orch)
    started = next(e for e in log.read_all() if e.type == "fanout.started")
    fanout_id = started.payload["fanout_id"]
    result = ZfEvent(
        type="review.approved",
        actor="review-a",
        correlation_id="trace-1",
        payload={
            "fanout_id": fanout_id,
            "child_id": "review-a",
            "run_id": f"run-{fanout_id}-review-a",
            "status": "approved",
        },
    )
    log.append(result)
    log.append(ZfEvent(
        type="worker.launch_artifact.written",
        actor="zf-cli",
        payload={
            "instance_id": "review-a",
            "role": "review-a",
            "backend": "mock",
            "launch_attempt": 2,
            "is_resume": False,
        },
    ))
    sends_before = len(transport.sent)

    orch._recover_unrecorded_reader_fanout_results()

    events = log.read_all()
    assert not any(
        e.type == "fanout.child.dispatch_lost"
        and e.payload.get("child_id") == "review-a"
        for e in events
    )
    child = next(
        c for c in _manifest(state_dir, fanout_id)["children"]
        if c["child_id"] == "review-a"
    )
    assert child["status"] == "completed"
    assert len(transport.sent) == sends_before
    assert any(
        e.type == "fanout.child.completed" and e.causation_id == result.id
        for e in events
    )
