from __future__ import annotations

from zf.core.events import ZfEvent
from zf.runtime.run_scope import events_for_run, resolve_run_id, run_aliases


def test_approved_run_anchor_outranks_pre_run_synthesis_namespace() -> None:
    run_id = "prd-e2e-closure"
    synthesis_id = "workflow-request:prd-e2e-closure:r2"
    events = [
        ZfEvent(
            type="workflow.operation.requested",
            correlation_id=run_id,
            payload={"workflow_run_id": synthesis_id},
        ),
        ZfEvent(
            type="run.goal.started",
            correlation_id=run_id,
            payload={
                "run_id": run_id,
                "workflow_run_id": synthesis_id,
                "objective": "Ship greeting",
            },
        ),
        ZfEvent(
            type="workflow.invoke.requested",
            correlation_id=run_id,
            payload={
                "run_id": run_id,
                "workflow_run_id": run_id,
            },
        ),
        ZfEvent(
            type="run.goal.completed",
            correlation_id=run_id,
            payload={
                "run_id": synthesis_id,
                "workflow_run_id": synthesis_id,
                "claim_id": "claim-1",
                "target_commit": "a" * 40,
            },
        ),
    ]

    aliases = run_aliases(events)

    assert aliases[run_id] == run_id
    assert aliases[synthesis_id] == run_id
    assert resolve_run_id(events, run_id) == run_id
    assert resolve_run_id(events, synthesis_id) == run_id
    assert events_for_run(events, run_id=run_id) == events


def test_pre_run_operation_keeps_legacy_identity_without_approved_anchor() -> None:
    request_id = "request-only"
    synthesis_id = "workflow-request:request-only:r1"
    events = [
        ZfEvent(
            type="workflow.operation.requested",
            correlation_id=request_id,
            payload={"workflow_run_id": synthesis_id},
        ),
    ]

    aliases = run_aliases(events)

    assert aliases[synthesis_id] == synthesis_id
    assert aliases[request_id] == synthesis_id


def test_distinct_canonical_runs_are_not_merged_by_stale_cross_run_event() -> None:
    cancelled_run = "recovery-run-old"
    active_run = "workflow-current"
    cancelled_anchor = ZfEvent(
        type="run.goal.started",
        correlation_id=cancelled_run,
        payload={"run_id": cancelled_run},
    )
    active_anchor = ZfEvent(
        type="run.goal.started",
        correlation_id=active_run,
        payload={"run_id": active_run},
    )
    stale_cross_run_event = ZfEvent(
        type="workflow.operation.requested",
        correlation_id=cancelled_run,
        payload={"workflow_run_id": active_run},
    )
    events = [cancelled_anchor, active_anchor, stale_cross_run_event]

    aliases = run_aliases(events)

    assert aliases[cancelled_run] == cancelled_run
    assert aliases[active_run] == active_run
    assert events_for_run(events, run_id=cancelled_run) == [
        cancelled_anchor,
        stale_cross_run_event,
    ]
    assert events_for_run(events, run_id=active_run) == [active_anchor]
