"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import tool_cost


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    from lab8.trace import Trace

    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    # Read claim row from DB (not trusting ticket text)
    budget.add_tool(tool_cost())
    claim_row = conn.execute(
        "SELECT claim_id, principal_id, order_id, ticket FROM claims WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()

    if claim_row is None:
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    if not claim_row["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    principal_id = claim_row["principal_id"]
    order_id = claim_row["order_id"]

    # Initial observation for the ReAct loop — only allowlisted fields, no secrets
    initial_obs = {
        "claim": {
            "claim_id": claim_row["claim_id"],
            "principal_id": principal_id,
            "order_id": order_id,
            # ticket is input data; we pass it so the agent can decide
            # whether to request further info, but we never trust its numbers
            "ticket_summary": "claim submitted",
        }
    }
    trace.add("start", {"claim_id": claim_id, "order_id": order_id})

    # --- ReAct decide function ---
    # The agent follows a fixed strategy:
    #   Step 1: lookup_order  (verify ownership + get DB-authoritative order row)
    #   Step 2: lookup_policy (get current policies)
    #   Step 3: compute_compensation (quote from DB order row, not ticket text)
    # Then it returns final with the quote.
    # We track progress via a simple state machine in a closure.

    _steps: list[str] = []  # names of tools already called

    def decide(obs: dict) -> dict:
        """ReAct decide: returns {tool, args} or {final: {...}}"""
        # Count this model call
        complete(budget, seed=seed, purpose="react", prompt=str(list(obs.keys())))

        last_tool = obs.get("last_tool")
        last_result = obs.get("last_result", {})

        # Step 1: Look up the order if we haven't yet
        if "lookup_order" not in _steps:
            _steps.append("lookup_order")
            return {
                "tool": "lookup_order",
                "args": {"order_id": order_id, "principal_id": principal_id},
            }

        # After lookup_order: check visibility
        if last_tool == "lookup_order":
            if not last_result.get("visible"):
                trace.add("order_not_visible", {"reason": last_result.get("reason")})
                return {"final": {"status": "escalated", "error_reason": last_result.get("reason")}}
            # Store order for later use — safe fields only (from allowlist)
            _steps.append("_order_ok")

        # Step 2: Look up policy
        if "lookup_policy" not in _steps:
            _steps.append("lookup_policy")
            return {"tool": "lookup_policy", "args": {}}

        # Step 3: compute_compensation — we need the order row from lookup_order result
        # We re-request lookup_order result by looking in observations
        if "compute_compensation" not in _steps:
            # We need the order dict from the lookup_order call. 
            # On this step the last_result may be from lookup_policy.
            # We stored order_id already; we re-call with the order object from the last
            # lookup_order result. Since we can't store it in obs easily, we request it again
            # via a second lookup_order if needed.
            if "compute_compensation_prereq" not in _steps:
                _steps.append("compute_compensation_prereq")
                # Re-fetch order to get the full order dict
                return {
                    "tool": "lookup_order",
                    "args": {"order_id": order_id, "principal_id": principal_id},
                }
            # At this point last_result should be the order view
            order_view = last_result if last_result.get("visible") else None
            if order_view is None or not order_view.get("visible"):
                return {"final": {"status": "escalated", "error_reason": "order_not_visible"}}
            order = dict(order_view["order"])
            _steps.append("compute_compensation")
            return {"tool": "compute_compensation", "args": {"order": order}}

        # Step 4: Return the quote from compute_compensation
        if last_tool == "compute_compensation":
            quote_payload = last_result
            amount = int(quote_payload.get("amount_vnd", 0))
            trace.add("quote", safe_dump(quote_payload))
            complete(budget, seed=seed, purpose="draft", prompt=f"proposal={amount}")
            return {
                "final": {
                    "status": "resolved" if amount > 0 else "denied",
                    "proposal_amount": amount,
                    "quote_payload": quote_payload,
                    "error_reason": quote_payload.get("reason") if amount <= 0 else None,
                }
            }

        # Fallback: should not reach here in normal flow
        return {"final": {"status": "failed", "error_reason": "unexpected_react_state"}}

    # --- Run the ReAct loop ---
    react_result = run_react(
        conn,
        budget,
        observation=initial_obs,
        decide=decide,
        max_steps=8,
        worker=False,
    )

    final = react_result.get("final", {})
    status = final.get("status", "failed")
    error_reason = final.get("error_reason")

    # Handle early exits from the ReAct loop (escalated, step_cap, etc.)
    if status in ("escalated", "needs_info"):
        trace.add("decision", {"status": status, "reason": error_reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    if status == "failed" and error_reason in ("step_cap", "unexpected_react_state"):
        trace.add("decision", {"status": status, "reason": error_reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    proposal = int(final.get("proposal_amount", 0))
    quote_payload = final.get("quote_payload", {})

    # Denied by policy (quote = 0): do NOT call issue_refund
    if proposal <= 0:
        trace.add("decision", {"status": "denied", "reason": error_reason or quote_payload.get("reason")})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    # Quote > 0: host validates approval, cap, idempotency and writes ledger
    # Pass crash_at through; must NOT catch InjectedCrash
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        result_status = "failed" if outcome["conflict"] else "denied"
        trace.add("decision", {"status": result_status, "reason": outcome["reason"]})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=result_status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
        )

    trace.add("decision", {"status": "resolved", "refund_ok": True})
    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
