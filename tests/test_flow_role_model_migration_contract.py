from __future__ import annotations

from zf.core.events.known_types import KNOWN_EVENT_TYPES
from zf.core.events.model import ZfEvent
from zf.core.verification.event_schema import (
    EventSchemaRegistry,
    flow_role_model_migration_event_schema_rules,
)


EVENT_TYPE = "flow.roles.model_migration.authorized"


def _payload() -> dict:
    return {
        "previous_activation_id": "activation-1",
        "workflow_run_id": "run-1",
        "role_digests": {"prd-dev": "a" * 64},
        "changes": {"prd-dev": {"model": {"before": "old", "after": "new"}}},
        "reason": "operator approved model update",
        "previous_manifest_ref": {
            "ref": "artifacts/flow-role-activations/prd/manifest.json",
            "sha256": "b" * 64,
        },
    }


def test_model_migration_event_is_a_known_type() -> None:
    assert EVENT_TYPE in KNOWN_EVENT_TYPES


def test_model_migration_event_schema_requires_auditable_payload() -> None:
    registry = EventSchemaRegistry.from_dict(
        flow_role_model_migration_event_schema_rules()
    )
    valid = ZfEvent(type=EVENT_TYPE, payload=_payload())
    assert registry.validate(valid) == []

    invalid = ZfEvent(
        type=EVENT_TYPE,
        payload={**_payload(), "reason": "", "previous_manifest_ref": {}},
    )
    violations = registry.validate(invalid)
    assert {v.field_path for v in violations} >= {
        "payload.reason",
        "payload.previous_manifest_ref.ref",
        "payload.previous_manifest_ref.sha256",
    }


def test_generic_workflow_profile_includes_model_migration_schema() -> None:
    from zf.core.config.schema_profiles import resolve_schema_profile

    profile = resolve_schema_profile("generic-workflow/v1")
    assert EVENT_TYPE in profile
    assert set(profile[EVENT_TYPE]["required"]) == set(_payload())
