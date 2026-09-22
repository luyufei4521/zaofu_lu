from __future__ import annotations

from zf.core.task.schema import Task, TaskContract
from zf.runtime.workflow_request_acceptance import (
    bind_task_workflow_inputs,
    inherit_task_acceptance,
)


def test_inherits_canonical_task_acceptance_when_request_omits_it() -> None:
    task = Task(
        id="TASK-1",
        title="delivery",
        contract=TaskContract(acceptance_criteria=[{
            "id": "AC-1",
            "statement": "The regression command passes.",
        }]),
    )

    parameters = inherit_task_acceptance({"target_ref": "HEAD"}, task)

    assert parameters["acceptance"] == ["The regression command passes."]


def test_explicit_request_acceptance_is_not_overwritten() -> None:
    task = Task(
        id="TASK-1",
        title="delivery",
        contract=TaskContract(acceptance_criteria=["canonical acceptance"]),
    )

    parameters = inherit_task_acceptance(
        {"acceptance": ["approved revision"]},
        task,
    )

    assert parameters["acceptance"] == ["approved revision"]


def test_channel_prd_lineage_is_inherited_into_workflow_source_refs() -> None:
    task = Task(
        id="TASK-CHANNEL-PRD",
        title="Deliver confirmed Channel PRD",
        contract=TaskContract(
            source_ref="channels/ch-prd/prd/r3.json",
            evidence_contract={
                "channel_id": "ch-prd",
                "thread_id": "main",
                "prd_revision": 3,
                "channel_prd_digest": "canonical-prd-sha",
                "readiness_ref": "channels/ch-prd/prd/r3-readiness.json",
                "readiness_digest": "readiness-sha",
            },
        ),
    )

    parameters, _binding, _contract, _overrides = bind_task_workflow_inputs(
        {"target_root": "."},
        task,
        task_contract_digest="task-contract-sha",
    )

    source_refs = parameters["source_refs"]
    assert source_refs["task_evidence_contract_digest"]
    assert {
        key: value
        for key, value in source_refs.items()
        if key != "task_evidence_contract_digest"
    } == {
        "task_source_ref": "channels/ch-prd/prd/r3.json",
        "task_contract_digest": "task-contract-sha",
        "channel_id": "ch-prd",
        "channel_thread_id": "main",
        "channel_prd_ref": "channels/ch-prd/prd/r3.json",
        "channel_prd_digest": "canonical-prd-sha",
        "channel_prd_revision": "3",
        "channel_prd_readiness_ref": "channels/ch-prd/prd/r3-readiness.json",
        "channel_prd_readiness_digest": "readiness-sha",
    }
