# Writer contract handoff

Writer results are adopted only after their immutable task-contract snapshot,
target commit, and implementation self-check agree with the canonical task
identity. The self-check authority fields (`contract_authority_revision`,
`execution_owner`, workflow request identity, and origin binding digest) are
part of that identity; handoff may fill omitted fields from the snapshot for
older workers, while an explicitly supplied mismatching value remains a hard
contract failure.

The handoff persists the normalized self-check as an `impl-self-check.v1`
sidecar and publishes its reference on `fanout.child.completed`. Regression
coverage is in `tests/test_writer_contract_handoff.py`.
