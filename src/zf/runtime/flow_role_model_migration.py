"""Explicit, evidence-bound authorization for model-only activation changes."""
from dataclasses import asdict
from typing import Any

from zf.core.events.model import ZfEvent
from zf.runtime.sidecar_refs import hydrate_sidecar_ref

MODEL_FIELDS = {"model", "model_reasoning_effort"}
EVENT = "flow.roles.model_migration.authorized"


def authorize_model_migration(orch: Any, previous: Any, *, reason: str) -> list[str]:
    """Validate the full old/new role configs before appending authorizations.

    Old configs must reproduce the immutable activation's exact role digests.
    No task, attempt or historic activation is rewritten.
    """
    from zf.runtime.flow_role_activation import _role_config_digest
    from zf.runtime.flow_roles import role_configs_for_flow
    from zf.runtime.workflow_operation import reduce_workflow_operations, TERMINAL_OPERATION_STATUSES

    if not reason.strip():
        raise ValueError("operator reason is required")
    events = orch.event_log.read_all()
    operations = reduce_workflow_operations(events)
    if any(op.get("status") not in TERMINAL_OPERATION_STATUSES for op in operations.values()):
        raise ValueError("stop or settle active workflow operations before model migration")
    pending = []
    known = {(e.payload.get("previous_activation_id"), tuple(sorted(e.payload.get("role_digests", {}).items())))
             for e in events if e.type == EVENT}
    for event in events:
        if event.type != "flow.roles.activation.applied":
            continue
        manifest = hydrate_sidecar_ref(
            orch.state_dir, event.payload["activation_manifest_ref"],
            purpose="model_migration", actor="kernel",
        ).payload
        old = {r.instance_id: r for r in role_configs_for_flow(previous, manifest["flow_kind"])}
        new = {r.instance_id: r for r in role_configs_for_flow(orch.config, manifest["flow_kind"])}
        entries = {r["instance_id"]: r for r in manifest["roles"]}
        if old.keys() != new.keys() or new.keys() != entries.keys():
            raise ValueError("non-model role membership change")
        digests = {key: _role_config_digest(role) for key, role in new.items()}
        if all(entries[key]["role_config_digest"] == digests[key] for key in entries):
            continue
        key = (manifest["activation_id"], tuple(sorted(digests.items())))
        if key in known:
            continue
        previous_entries = [{"instance_id": name, "role_config_digest": _role_config_digest(role)}
                            for name, role in old.items()]
        previous_authorized = migration_authorizes(events, manifest["activation_id"], previous_entries)
        changes = {}
        for name in old:
            before, after = asdict(old[name]), asdict(new[name])
            if not previous_authorized and _role_config_digest(old[name]) != entries[name]["role_config_digest"]:
                raise ValueError(f"previous config does not match activation: {name}")
            changed = {k for k in before if before[k] != after[k]}
            if changed - MODEL_FIELDS:
                raise ValueError(f"non-model config change: {name}: {sorted(changed - MODEL_FIELDS)}")
            changes[name] = {k: {"before": before[k], "after": after[k]} for k in sorted(changed)}
        pending.append((event, manifest, digests, changes))
        known.add(key)
    ids = []
    for event, manifest, digests, changes in pending:
        record = ZfEvent(type=EVENT, actor="zf-cli", origin="kernel", payload={
            "previous_activation_id": manifest["activation_id"],
            "workflow_run_id": manifest["workflow_run_id"],
            "role_digests": digests, "changes": changes, "reason": reason,
            "previous_manifest_ref": event.payload["activation_manifest_ref"],
        }, causation_id=event.id, correlation_id=manifest["workflow_run_id"])
        orch.event_writer.append(record)
        ids.append(record.id)
    return ids


def migration_authorizes(events: list, activation: str, entries: list[dict]) -> bool:
    digests = {entry["instance_id"]: entry["role_config_digest"] for entry in entries}
    return any(e.type == EVENT and e.origin == "kernel"
               and e.payload.get("previous_activation_id") == activation
               and e.payload.get("role_digests") == digests for e in events)
