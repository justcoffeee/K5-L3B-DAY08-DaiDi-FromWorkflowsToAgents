"""Edge-case tests for Shape C orchestrator (student self-check).

These tests are supplementary to tests/test_public_matrix.py and are NOT part of
the official grading matrix. They verify additional behaviours the orchestrator
must handle correctly.
"""

from __future__ import annotations

import time

import pytest

from lab8.config_loader import repo_path
from lab8.db import init_store, load_json, load_jsonl
from lab8.durability import InjectedCrash
from lab8.metrics import trial_pass
from lab8.shapes import SHAPES

WORLD = load_json(repo_path("data", "public_world_state.json"))
CLAIMS = load_jsonl(repo_path("data", "public_claims.jsonl"))
BY_ID = {row["claim_id"]: row for row in CLAIMS}


def _store(tmp_path, name: str):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


@pytest.mark.student
def test_orchestrator_unknown_claim(tmp_path):
    """Claim khong ton tra -> status failed, proposal 0, khong ghi ledger."""
    store = _store(tmp_path, "orch-edge-unknown.sqlite")
    started_at = time.time()
    result = SHAPES["orchestrator"]("C-999", seed=11, store_path=str(store))
    conn = __import__("lab8.db", fromlist=["connect"]).connect(store)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-999'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    assert count == 0


@pytest.mark.student
def test_orchestrator_missing_order_id(tmp_path):
    """Claim thieu order_id -> status needs_info, proposal 0, khong ghi ledger."""
    store = _store(tmp_path, "orch-edge-missing-order.sqlite")
    started_at = time.time()
    result = SHAPES["orchestrator"]("C-004", seed=11, store_path=str(store))
    conn = __import__("lab8.db", fromlist=["connect"]).connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(), BY_ID["C-004"]["expected"], conn, started_at=started_at
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-004'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    assert count == 0
    assert passed, reason


@pytest.mark.student
def test_orchestrator_outside_principal(tmp_path):
    """Principal khong 소유 đơn -> status escalated, proposal 0."""
    store = _store(tmp_path, "orch-edge-outside.sqlite")
    started_at = time.time()
    result = SHAPES["orchestrator"]("C-005", seed=11, store_path=str(store))
    conn = __import__("lab8.db", fromlist=["connect"]).connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(), BY_ID["C-005"]["expected"], conn, started_at=started_at
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-005'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "escalated"
    assert result.proposal_amount == 0
    assert count == 0
    assert passed, reason


@pytest.mark.student
def test_orchestrator_crash_recovery_idempotent(tmp_path):
    """Crash sau effect truoc checkpoint, resume lai van chi 1 refund (T12)."""
    store = _store(tmp_path, "orch-edge-crash.sqlite")
    try:
        SHAPES["orchestrator"](
            "C-012", seed=11, store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )
    except InjectedCrash:
        pass  # expected: crash propagates
    started_at = time.time()
    result = SHAPES["orchestrator"]("C-012", seed=11, store_path=str(store))
    conn = __import__("lab8.db", fromlist=["connect"]).connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started_at
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert count == 1
    assert passed, reason


@pytest.mark.student
def test_orchestrator_retry_same_amount_no_double_pay(tmp_path):
    """Goi lai cung claim cung so tien -> van chi 1 refund (T11)."""
    store = _store(tmp_path, "orch-edge-retry.sqlite")
    first = SHAPES["orchestrator"]("C-001", seed=11, store_path=str(store))
    started_at = time.time()
    second = SHAPES["orchestrator"]("C-001", seed=11, store_path=str(store))
    conn = __import__("lab8.db", fromlist=["connect"]).connect(store)
    try:
        passed, reason = trial_pass(
            second.as_dict(), BY_ID["C-001"]["expected"], conn, started_at=started_at
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert first.status == "resolved"
    assert second.status == "resolved"
    assert count == 1
    assert passed, reason