---
title: Trace a print-intake decision
description: Run a synthetic print job through six workflow outcomes and reproduce three cases where two checks fail together.
---

# Trace a print-intake decision

Use a synthetic A5 print job to see where an intake workflow stops and what an operator can do next. The Python sample returns a decision and an ordered trace. It runs locally with Python 3.9 or later and the standard library.

## Run a job

Get the [workflow gate sample](https://github.com/shashwatbharadwaj2-gif/nativity-workflow-gate-samples) and run its self-test from the repository folder.

```sh
python workflow_gate_demo.py --self-test
```

Save this example as `print-job.json` in the same folder. The `brief` holds the incoming specifications. The `approved_job` object is the reference against which the sample checks job ID, dimensions, stock and finish.

```json
{
  "event_id": "SYNTHETIC-PRINT-028",
  "actor_allowed": true,
  "tool_available": true,
  "processed_event_ids": [],
  "brief": {
    "job_id": "PRINT-028",
    "quantity": 2000,
    "dimensions": "A5",
    "stock": "150 gsm silk",
    "finish": "Matt"
  },
  "approved_job": {
    "job_id": "PRINT-028",
    "dimensions": "A5",
    "stock": "150 gsm silk",
    "finish": "Matt"
  }
}
```

```sh
python workflow_gate_demo.py --input print-job.json
```

The supplied job returns `ready-for-review` and a draft ticket with five fields. Every outcome has `external_actions: 0`. The person responsible for estimating or production decides what happens after review.

## Compare outcomes

Make one change to the example at a time. The last trace entry identifies the decision the operator should investigate.

| Change to the fixture | Decision | Suggested operator action |
| --- | --- | --- |
| Leave the fixture as supplied | `ready-for-review` | Compare the draft ticket with the job brief before releasing it. |
| Remove `brief.finish` | `more-information-needed` | Request the finish and record the confirmed value. |
| Set `actor_allowed` to `false` | `access-denied` | Route the request to the person responsible for access. |
| Change `brief.stock` to `Unapproved stock` | `conflict-held` | Reconcile the requested stock with the approved reference. |
| Put `SYNTHETIC-PRINT-028` in `processed_event_ids` | `duplicate-held` | Check the earlier event before deciding whether to retry. |
| Set `tool_available` to `false` | `tool-unavailable` | Record the dependency failure for retry or manual handling. |

## When two checks fail

The sample evaluates access, duplicate status and tool availability before it checks the brief and compares it with the reference. This matters when two issues arrive together. The first failing gate determines the decision, and the trace ends at that gate.

| Combined input changes | Observed decision | What the trace shows |
| --- | --- | --- |
| Access denied and finish missing | `access-denied` | The access decision ends processing before the brief is examined. |
| Event already processed and tool unavailable | `duplicate-held` | The event is held before the dependency check. |
| Finish missing and stock conflicts | `more-information-needed` | The incomplete brief is held before the reference comparison. |

Run these three cases from the repository folder after saving `print-job.json`.

```python
from copy import deepcopy
from json import loads
from pathlib import Path

from workflow_gate_demo import evaluate

fixture = loads(Path("print-job.json").read_text(encoding="utf-8"))

denied = deepcopy(fixture)
denied["actor_allowed"] = False
del denied["brief"]["finish"]

duplicate = deepcopy(fixture)
duplicate["processed_event_ids"] = [duplicate["event_id"]]
duplicate["tool_available"] = False

incomplete = deepcopy(fixture)
del incomplete["brief"]["finish"]
incomplete["brief"]["stock"] = "Unapproved stock"

cases = (
    (denied, "access-denied"),
    (duplicate, "duplicate-held"),
    (incomplete, "more-information-needed"),
)
for payload, expected in cases:
    outcome = evaluate(payload)
    assert outcome["status"] == expected
    assert outcome["external_actions"] == 0
    assert "draft_ticket" not in outcome
    print(outcome["status"], outcome["trace"][-1])
```

## Adapt the checks

Keep the event ID, approved specifications and review owner explicit when designing your own intake. In this example, permissions, event history and tool availability come from the supplied fixture. A production workflow needs trusted sources for those inputs, a persistent record of handled events and an assigned owner for held work. Use test inputs to exercise gate order before connecting any external system.

The sample accompanies the workflow planning resources from [Nativity Group](https://nativity-group.chawla78.chatgpt.site/).
