from __future__ import annotations

from pathlib import Path

from zf.core.events import EventLog, EventWriter, ZfEvent
from zf.core.task.schema import Task, TaskContract
from zf.core.task.store import TaskStore
from zf.runtime.workflow_anchor import (
    bind_workflow_request_to_task,
    mark_workflow_managed_task,
)
from zf.runtime.workflow_task_request_rotation import (
    apply_task_request_binding,
)
from zf.runtime.workflow_origin import workflow_origin_digest


def test_terminal_task_is_reopened_for_proven_request_rotation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".zf"
    state_dir.mkdir()
    store = TaskStore(state_dir / "kanban.json")
    task = bind_workflow_request_to_task(
        mark_workflow_managed_task(Task(
            id="TASK-ROTATE-TERMINAL",
            title="Rotate a cancelled workflow Task",
            status="cancelled",
            completed_at="2026-08-31T00:00:00+00:00",
            contract=TaskContract(
                behavior="delivery",
                verification="pytest -q",
            ),
        )),
        request_id="REQ-OLD",
        request_revision=2,
        origin_binding_digest="sha256:" + "a" * 64,
    )
    store.add(task)
    archived = store.get(task.id)
    assert archived is not None and archived.status == "cancelled"

    origin_binding = {
        "schema_version": "workflow-origin-binding.v1",
        "surface": "cli",
        "source": "cli",
        "project_id": "demo",
        "channel_id": "",
        "thread_id": "",
        "conversation_id": "",
        "thread_key": "",
    }
    rotation = {
        "prior_request_id": "REQ-OLD",
        "prior_request_revision": 2,
        "prior_run_id": "RUN-OLD",
        "prior_terminal_event_id": "evt-old-terminal",
        "prior_terminal_type": "run.cancelled",
        "origin_binding": origin_binding,
        "origin_binding_digest": workflow_origin_digest(origin_binding),
    }
    monkeypatch.setattr(
        "zf.runtime.workflow_task_request_rotation."
        "terminal_task_request_rotation_context",
        lambda _state_dir, _task_request: rotation,
    )
    monkeypatch.setattr(
        "zf.runtime.workflow_task_request_rotation.request_admission_view",
        lambda _events, *, request_id, run_id: {},
    )

    log = EventLog(state_dir / "events.jsonl")
    writer = EventWriter(log)
    accepted = ZfEvent(
        type="workflow.submit.accepted",
        actor="operator:cli",
        task_id=task.id,
        correlation_id="REQ-NEW",
        payload={"request_id": "REQ-NEW", "request_revision": 1},
    )
    decision = apply_task_request_binding(
        state_dir,
        task_store=store,
        event_writer=writer,
        task=archived,
        request_projection={
            "request_id": "REQ-NEW",
            "revision": 1,
            "origin_binding": origin_binding,
            "run_id": "REQ-NEW",
        },
        requested_event=accepted,
        actor="operator:cli",
    )

    assert decision.should_bind is True
    reopened = store.get(task.id)
    assert reopened is not None
    assert reopened.status == "backlog"
    assert reopened.completed_at is None
    assert reopened.execution_binding.request_id == "REQ-NEW"
    assert reopened.execution_binding.request_revision == 1
