"""Jev-first lead-routing prototype for Nativity Group.

Run: python jev_lead_harness.py --self-test
Live: TYPESAFE_API_KEY=... python jev_lead_harness.py --input lead.json --live
Does not send emails, write to a CRM, or modify the production website.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.typesafe.ai/v1/systemone"
CATEGORIES = {
    "ai_agents": "Wants AI agents, conversational assistants, or agent development",
    "workflow_automation": "Wants to automate business processes or integrations",
    "custom_ai_software": "Wants a custom AI software application or model integration",
    "other": "Does not clearly request one of the listed AI solutions",
}
QUESTIONS = {
    "service": {
        "type": "choice",
        "instructions": "Which SINGLE AI solution best matches the visitor's explicitly described request? Choose other if unclear.",
        "criteria": CATEGORIES,
    },
    "sales_intent": {
        "type": "noul",
        "instructions": "Does the visitor explicitly request a consultation, quotation, proposal, or a conversation about purchasing services?",
    },
    "human_review": {
        "type": "noul",
        "instructions": "Does the visitor explicitly ask for a person or mention urgent legal, safety, privacy, or security concerns?",
    },
}

def assess(lead, client=None):
    """Return recommendation only. Authorization and all side effects belong elsewhere."""
    if not isinstance(lead, dict):
        return {"route": "manual_review", "reason": "invalid_input"}
    message = lead.get("message", "")
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        return {"route": "manual_review", "reason": "missing_or_oversize_message"}
    if client is None:
        return {"route": "manual_review", "reason": "jev_unavailable"}
    try:
        response = client({"model": "jev-latest", "state": message.strip(), "questions": QUESTIONS})
        answers = response["answers"]
        choice = answers["service"]
        service = choice.get("choice")
        distribution = choice.get("probabilities", {})
        confidence = distribution.get(service, choice.get("confidence", 0))
        intent = answers["sales_intent"]["noul"]
        review = answers["human_review"]["noul"]
        if not isinstance(service, str) or service not in CATEGORIES:
            raise ValueError("invalid service")
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 1
                   for x in (confidence, intent, review)):
            raise ValueError("invalid probability")
        if review >= 0.6:
            route, reason = "manual_review", "sensitive_or_human_requested"
        elif confidence < 0.8 or service == "other":
            route, reason = "manual_review", "uncertain_or_out_of_scope"
        elif intent >= 0.8:
            route, reason = "sales_review", "explicit_sales_intent"
        else:
            route, reason = "service_information", "informational_request"
        return {"route": route, "reason": reason, "service": service,
                "service_probability": round(confidence, 4),
                "sales_intent_probability": round(intent, 4),
                "human_review_probability": round(review, 4),
                "model": response.get("model", "unreported"),
                "external_actions": 0}
    except (KeyError, TypeError, ValueError, TimeoutError, HTTPError, URLError, OSError):
        return {"route": "manual_review", "reason": "jev_error", "external_actions": 0}

def live_client(payload):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise ValueError("TYPESAFE_API_KEY is required")
    request = Request(API_URL, data=json.dumps(payload).encode("utf-8"),
                      headers={"Authorization": "Bearer " + key,
                               "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("non-200 response")
        return json.load(response)

def self_test():
    def mock(payload):
        assert payload["questions"].keys() == QUESTIONS.keys()
        return {"model": "mock", "answers": {
            "service": {"choice": "workflow_automation", "probabilities": {"workflow_automation": 0.93}},
            "sales_intent": {"noul": 0.98}, "human_review": {"noul": 0.01}}}
    assert assess({"message": "Please quote a workflow automation project"}, mock)["route"] == "sales_review"
    assert assess({"message": ""}, mock)["route"] == "manual_review"
    assert assess({"message": "hello"})["route"] == "manual_review"
    def sensitive(payload):
        out = mock(payload)
        out["answers"]["human_review"]["noul"] = 0.95
        return out
    assert assess({"message": "I need to speak to someone urgently"}, sensitive)["route"] == "manual_review"
    def uncertain(payload):
        out = mock(payload)
        out["answers"]["service"]["probabilities"]["workflow_automation"] = 0.4
        return out
    assert assess({"message": "Can you help with something?"}, uncertain)["route"] == "manual_review"
    def broken(payload):
        raise URLError("offline")
    assert assess({"message": "Hello"}, broken)["reason"] == "jev_error"
    print("PASS: six deterministic harness checks (mock only; no Jev API call)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.input:
        parser.error("use --self-test or --input lead.json")
    data = json.loads(args.input.read_text())
    result = assess(data, live_client if args.live else None)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
