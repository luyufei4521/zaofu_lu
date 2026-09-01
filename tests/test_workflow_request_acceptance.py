from __future__ import annotations

from zf.core.task.schema import Task, TaskContract
from zf.runtime.workflow_request_acceptance import (
    build_task_workflow_input_contract,
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


def test_fresh_request_does_not_inherit_previous_plan_outputs() -> None:
    task = Task(
        id="TASK-ROTATE",
        title="rotate delivery",
        contract=TaskContract(
            plan_ref="artifacts/old-plan.json",
            source_index_ref="artifacts/old/source-index.json",
            product_contract_ref="artifacts/old/task-map.json",
            source_ref="workflow-previous/requirements.json",
            evidence_contract={
                "source_refs": {
                    "task_map_ref": "artifacts/old/task-map.json",
                    "source_index_ref": "artifacts/old/source-index.json",
                },
                "workflow_request_id": "workflow-previous",
            },
        ),
    )

    fresh = build_task_workflow_input_contract(
        task,
        task_contract_digest="sha256:task",
        fresh_request=True,
    )

    assert fresh["source_ref"] == "workflow-previous/requirements.json"
    assert fresh["source_index_ref"] == ""
    assert fresh["product_contract_ref"] == ""
    assert fresh["evidence_contract"]["source_refs"] == {}
    assert "workflow_request_id" not in fresh["evidence_contract"]
