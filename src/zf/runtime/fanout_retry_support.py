"""Sidecar preparation and failure reporting for fanout retries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from zf.core.events.model import ZfEvent
from zf.core.events.writer import EventWriter
from zf.runtime.artifact_read_ledger import source_manifest_from_payload
from zf.runtime.failure_kind import classify_dispatch_exception


def prepare_reader_retry_source_payload(
    state_dir: Path,
    project_root: Path,
    event_writer: EventWriter,
    manifest: dict[str, Any],
    child: dict[str, Any],
    role_instance: str,
    run_id: str,
    attempt: int,
    previous_dispatch: ZfEvent,
) -> dict[str, Any] | None:
    """Materialize the immutable source manifest for a new reader attempt."""
    task_id = str(child.get("task_id") or "")
    try:
        child_payload = child.get("payload")
        manifest_payload = (
            dict(child_payload) if isinstance(child_payload, dict) else {}
        )
        manifest_payload.update({
            "task_id": task_id,
            "workflow_run_id": str(
                manifest_payload.get("workflow_run_id")
                or manifest.get("trace_id")
                or ""
            ),
            "target_ref": str(
                child.get("target_ref") or manifest.get("target_ref") or ""
            ),
        })
        source_manifest, descriptor = source_manifest_from_payload(
            state_dir=state_dir,
            project_root=project_root,
            payload=manifest_payload,
            workflow_run_id=str(manifest_payload.get("workflow_run_id") or ""),
            task_id=task_id,
            attempt_id=run_id,
            dispatch_id=run_id,
            source_event_id=previous_dispatch.id,
            manifest_metadata={
                "retry_of_run_id": str(
                    previous_dispatch.payload.get("run_id") or ""
                ),
                "retry_attempt": attempt,
            },
        )
    except Exception as exc:
        event_writer.append(ZfEvent(
            type="fanout.child.failed",
            actor="zf-cli",
            payload={
                **_retry_identity_payload(
                    manifest, child, role_instance, run_id, attempt,
                    previous_dispatch,
                ),
                "reason": f"retry source manifest preparation failed: {exc}",
                "failure_kind": "artifact_read",
            },
            causation_id=previous_dispatch.id,
            correlation_id=str(manifest.get("trace_id") or ""),
        ))
        return None

    payload: dict[str, Any] = {
        "attempt_source_manifest_ref": str(descriptor.get("ref") or ""),
        "attempt_source_manifest_digest": str(descriptor.get("sha256") or ""),
        "attempt_source_manifest": dict(descriptor),
    }
    for key in (
        "required_reads",
        "input_consumption_policy",
        "input_consumption_policy_ref",
        "input_consumption_policy_digest",
    ):
        if key in source_manifest:
            payload[key] = source_manifest[key]
    return payload


def emit_fanout_retry_dispatch_failure(
    event_writer: EventWriter,
    manifest: dict[str, Any],
    child: dict[str, Any],
    role_instance: str,
    run_id: str,
    attempt: int,
    previous_dispatch: ZfEvent,
    exc: Exception,
) -> None:
    """Convert a retry transport exception into the canonical failure event."""
    payload = _retry_identity_payload(
        manifest, child, role_instance, run_id, attempt, previous_dispatch,
    )
    payload["reason"] = str(exc)
    failure_kind = classify_dispatch_exception(exc)
    if failure_kind:
        payload["failure_kind"] = failure_kind
    event_writer.append(ZfEvent(
        type="fanout.child.failed",
        actor="zf-cli",
        payload=payload,
        causation_id=previous_dispatch.id,
        correlation_id=str(manifest.get("trace_id") or ""),
    ))


def _retry_identity_payload(
    manifest: dict[str, Any],
    child: dict[str, Any],
    role_instance: str,
    run_id: str,
    attempt: int,
    previous_dispatch: ZfEvent,
) -> dict[str, Any]:
    return {
        "fanout_id": str(manifest.get("fanout_id") or ""),
        "trace_id": str(manifest.get("trace_id") or ""),
        "stage_id": str(manifest.get("stage_id") or ""),
        "child_id": str(child.get("child_id") or ""),
        "run_id": run_id,
        "role_instance": role_instance,
        "task_id": str(child.get("task_id") or ""),
        "retry_of_run_id": str(previous_dispatch.payload.get("run_id") or ""),
        "attempt": attempt + 1,
    }
