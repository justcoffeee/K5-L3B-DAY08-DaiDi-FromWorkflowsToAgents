"""Cross-shape integration and evaluation checks.

Authored by: Pham Hoang Huy (MSSV: 2A202603836)

These tests are the group leader's integration checks. They run the same claim
through all three implemented shapes on fresh stores and verify that:

1. The core business outcome is identical: status, proposal, refunds and audit.
2. The trace satisfies Trace contract v1 and contains no canary/secret field.
3. A crash before the ledger effect still resumes to exactly one refund.

They are host-gate tests (not marked ``student``) so CI catches integration
regressions across shapes as well as the per-shape student suites.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.shapes import orchestrator, single, workflow
from tests.conftest import CLAIMS, WORLD

SHAPES = (
    ("workflow", workflow.run_claim),
    ("single", single.run_claim),
    ("orchestrator", orchestrator.run_claim),
)

PARITY_CLAIMS = (
    "C-001",  # resolved
    "C-002",  # ticket overstates delay -> denied
    "C-007",  # expired approval -> denied
    "C-008",  # per-order cap -> partial refund
    "C-013",  # superseded policy -> denied
    "C-014",  # per-order cap with damage -> partial refund
)


def _fresh_store(tmp_path: Path, name: str):
    path = tmp_path / f"{name}.sqlite"
    init_store(path, WORLD, CLAIMS).close()
    return path


@pytest.mark.parametrize("claim_id", PARITY_CLAIMS)
def test_all_shapes_agree_on_core_outcome(tmp_path: Path, claim_id: str) -> None:
    outcomes = {}
    for name, run in SHAPES:
        result = run(claim_id, seed=11, store_path=str(_fresh_store(tmp_path, name)))

        trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        assert trace["run_id"] == result.run_id
        assert trace["events"]
        trace_blob = json.dumps(trace, ensure_ascii=False)
        assert "CANARY_SECRET_" not in trace_blob
        assert "parent_secret" not in trace_blob
        assert "Bearer " not in trace_blob

        outcomes[name] = (
            result.status,
            result.proposal_amount,
            tuple(effect["amount_vnd"] for effect in result.refund_effects),
            result.committed_audit_count,
        )

    assert outcomes["single"] == outcomes["workflow"]
    assert outcomes["orchestrator"] == outcomes["workflow"]


@pytest.mark.parametrize("shape_name,run", SHAPES, ids=[name for name, _ in SHAPES])
def test_all_shapes_resume_after_crash_with_one_refund(tmp_path: Path, shape_name: str, run) -> None:
    store = _fresh_store(tmp_path, f"{shape_name}-crash")

    with pytest.raises(InjectedCrash):
        run("C-001", seed=11, store_path=str(store), crash_at="before_effect")

    result = run("C-001", seed=11, store_path=str(store))
    assert result.status == "resolved"
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 35000
    assert result.committed_audit_count == 1

    conn = connect(store)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 1
