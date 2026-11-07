# Workflow gate samples

This small Python sample shows how a workflow can stop when information, permission or a required tool is missing. It uses synthetic print-intake data and deterministic rules. It makes no network requests, calls no AI model and writes to no external system.

The example is prepared for Nativity Group's workflow resources: https://nativity-group.chawla78.chatgpt.site/. It is a new standalone sample rather than the production website's source code.

## Run

Python 3.9 or later; standard library only.

```sh
python workflow_gate_demo.py --self-test
python workflow_gate_demo.py --input /path/to/synthetic-input.json
```

The built-in checks cover a complete brief, missing finish, access denial, conflicting stock, duplicate event and unavailable tool. Boundary checks cover invalid quantities and a non-object input. The self-test reports 10 checks and exposes the computed output and trace for the six scenarios.

## Read the result

Every outcome includes `external_actions: 0`. A complete brief produces `ready-for-review`, not a sent estimate or a production commitment. Held cases return their status without a draft ticket.

The supplied `actor_allowed`, processed-event list and availability flag are controlled test inputs. They do not implement trusted authentication, a production authorisation system, durable idempotency or a real tool health check.

The compared reference fields are job ID, dimensions, stock and finish. Quantity is checked as a positive whole number; it is not compared with an authoritative quantity record in this sample.

## Limits

This sample does not evaluate a model, read PDFs, inspect artwork, validate prepress settings, integrate a printing MIS, establish price/delivery, certify security or demonstrate customer savings. Real deployments need their own permissions, persistence, tests, monitoring and acceptance evidence.

Inspect the source and modify only synthetic inputs. Keep business secrets, personal records and customer artwork out of this demonstration.
