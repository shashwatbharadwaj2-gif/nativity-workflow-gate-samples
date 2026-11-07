"""Inspectable synthetic print-intake gates. No network, model, or external writes.

Run: python workflow_gate_demo.py --self-test
     python workflow_gate_demo.py --input /path/to/synthetic-input.json
This is a new standalone sample; it is not the production website's implementation.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def evaluate(data: object) -> dict:
    trace = []

    def result(status: str, **details: object) -> dict:
        return {"status": status, "external_actions": 0, "trace": trace.copy(), **details}

    if not isinstance(data, dict):
        return result("invalid-input", error="Expected a JSON object")
    if not isinstance(data.get("event_id"), str) or not data["event_id"].strip():
        return result("invalid-input", error="A non-empty event_id is required")
    trace.append("Envelope has a non-empty event identifier")
    # These supplied fields illustrate an access gate; they are not authentication.
    if data.get("actor_allowed") is not True:
        trace.append("Access not permitted by the supplied sample field")
        return result("access-denied")
    trace.append("Sample access gate passed")
    processed = data.get("processed_event_ids", [])
    if not isinstance(processed, list) or any(not isinstance(x, str) for x in processed):
        return result("invalid-input", error="processed_event_ids must be a list of strings")
    if data["event_id"] in processed:
        trace.append("Event already exists in the supplied processed-event list")
        return result("duplicate-held")
    trace.append("No duplicate found in the supplied list")
    if data.get("tool_available") is not True:
        trace.append("Required tool marked unavailable in the synthetic input")
        return result("tool-unavailable")
    trace.append("Synthetic tool-availability gate passed")
    brief = data.get("brief")
    if not isinstance(brief, dict):
        return result("invalid-input", error="brief must be a JSON object")
    required = ("job_id", "dimensions", "stock", "finish")
    missing = [key for key in required if not isinstance(brief.get(key), str) or not brief[key].strip()]
    quantity = brief.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        missing.append("quantity")
    if missing:
        trace.append("Required specifications are missing or invalid")
        return result("more-information-needed", missing_or_invalid=missing)
    trace.append("Required field types and values checked")
    approved = data.get("approved_job")
    if not isinstance(approved, dict):
        return result("invalid-input", error="approved_job must be the supplied reference object")
    conflicts = [key for key in required if key in approved and brief[key] != approved[key]]
    if conflicts:
        trace.append("Brief disagrees with the supplied reference")
        return result("conflict-held", conflicting_fields=conflicts)
    trace.append("No conflict in the compared reference fields")
    trace.append("Estimator or production owner must review before any real action")
    return result("ready-for-review", draft_ticket={key: brief[key] for key in (*required, "quantity")})


def scenarios() -> list[tuple[str, dict, str]]:
    base = {"event_id": "SYNTHETIC-PRINT-028", "actor_allowed": True,
            "tool_available": True, "processed_event_ids": [],
            "brief": {"job_id": "PRINT-028", "quantity": 2000, "dimensions": "A5",
                      "stock": "150 gsm silk", "finish": "Matt"},
            "approved_job": {"job_id": "PRINT-028", "dimensions": "A5",
                             "stock": "150 gsm silk", "finish": "Matt"}}
    cases = [("complete", copy.deepcopy(base), "ready-for-review")]
    missing = copy.deepcopy(base); missing["brief"].pop("finish")
    cases.append(("missing-finish", missing, "more-information-needed"))
    denied = copy.deepcopy(base); denied["actor_allowed"] = False
    cases.append(("access-denied", denied, "access-denied"))
    conflict = copy.deepcopy(base); conflict["brief"]["stock"] = "Unapproved stock"
    cases.append(("conflicting-stock", conflict, "conflict-held"))
    duplicate = copy.deepcopy(base); duplicate["processed_event_ids"] = [base["event_id"]]
    cases.append(("duplicate-event", duplicate, "duplicate-held"))
    unavailable = copy.deepcopy(base); unavailable["tool_available"] = False
    cases.append(("tool-unavailable", unavailable, "tool-unavailable"))
    return cases


def self_test() -> dict:
    checks = []
    for name, payload, expected in scenarios():
        before = copy.deepcopy(payload)
        actual = evaluate(payload)
        assert actual["status"] == expected, (name, actual)
        assert actual["external_actions"] == 0
        assert payload == before, "The evaluator must not mutate the input"
        if expected != "ready-for-review":
            assert "draft_ticket" not in actual
        checks.append({"case": name, "expected": expected, "result": actual, "passed": True})
    base = scenarios()[0][1]
    for name, value in (("boolean-quantity", True), ("fractional-quantity", 2.5), ("zero-quantity", 0)):
        payload = copy.deepcopy(base); payload["brief"]["quantity"] = value
        actual = evaluate(payload)
        assert actual["status"] == "more-information-needed"
        checks.append({"case": name, "passed": True})
    assert evaluate([])["status"] == "invalid-input"
    checks.append({"case": "non-object-input", "passed": True})
    return {"sample_version": "1.0", "checks_passed": len(checks), "checks_failed": 0,
            "limitations": ["Synthetic deterministic rules only; no AI-model or production-security evaluation",
                            "Supplied access and duplicate fields are not trusted authentication or durable idempotency",
                            "No artwork inspection, prepress validation, price, delivery promise, or client outcome"],
            "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.input and args.self_test:
        parser.error("Choose --input or --self-test")
    if args.input:
        try:
            output = evaluate(json.loads(args.input.read_text()))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
    else:
        output = self_test()
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
