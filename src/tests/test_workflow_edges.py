"""Workflow integration checks beyond the public claim matrix."""

import json

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.shapes.workflow import run_claim
from tests.conftest import CLAIMS, WORLD


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "workflow.sqlite"
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def test_unknown_claim_returns_failed_with_fresh_trace(store):
    result = run_claim("C-UNKNOWN", seed=11, store_path=store)
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    with open(result.trace_path, encoding="utf-8") as stream:
        trace = json.load(stream)
    assert trace["run_id"] == result.run_id
    assert trace["events"]


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_workflow_crash_and_repeated_resume(store, point):
    with pytest.raises(InjectedCrash):
        run_claim("C-001", seed=11, store_path=store, crash_at=point)
    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()[0]
        assert count == (0 if point == "before_effect" else 1)
    finally:
        conn.close()
    for _ in range(2):
        result = run_claim("C-001", seed=11, store_path=store)
        assert result.status == "resolved"
        assert len(result.refund_effects) == 1
        assert result.refund_effects[0]["amount_vnd"] == 35000
        assert result.committed_audit_count == 1


def test_changed_quote_on_retry_preserves_committed_amount(store):
    first = run_claim("C-001", seed=11, store_path=store)
    assert first.status == "resolved"
    conn = connect(store)
    try:
        conn.execute("UPDATE orders SET shipping_fee_vnd = 10000 WHERE order_id = 'O-107'")
        conn.commit()
    finally:
        conn.close()
    result = run_claim("C-001", seed=11, store_path=store)
    assert result.status == "failed"
    assert result.error_reason == "amount_conflict"
    assert result.proposal_amount == 10000
    assert result.refund_effects[0]["amount_vnd"] == 35000
    assert result.committed_audit_count == 1
