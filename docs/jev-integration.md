# Jev lead-routing harness (prototype, not production site)

This is an **additive**, isolated Jev example for Nativity Group. It does **not** modify the production website or automatically accept/reject customers.

## Intended workflow
1. Perform deterministic input validation and verified authentication outside the model.
2. Send minimal, consented textual context to TypeSafe using a **server-side** key.
3. Ask three narrow, independent questions in **one Jev request**: service choice, sales intent (Noul), and human handoff (Noul).
4. Apply **deterministic** thresholds; ambiguous, sensitive, invalid, or failed requests route to human review.
5. Allow only a separate authorized service to trigger external side effects. This prototype never sends email, updates a CRM, or rejects a lead.

## Try it
```bash
python jev_lead_harness.py --self-test
printf '{"message":"Please quote AI workflow automation for our CRM"}' > lead.json
TYPESAFE_API_KEY="your-key-in-a-local-secret-store" python jev_lead_harness.py --input lead.json --live
```
Never commit lead.json with customer data or any API key. The self-test mocks the API and proves control-flow behavior, not real-world classifier accuracy. Thresholds (0.8/0.6) are **initial heuristics**, not calibrated cutoffs. Pilot with labeled, consented examples, measure false negatives / false positives, tune thresholds, and monitor drift before any deployment. Consider PII minimization and retention requirements.

## When NOT to use Jev
Do not use Jev to generate copy or code, count, perform arithmetic/date calculations, authenticate, enforce permissions, validate compliance, execute payments, make irreversible decisions, or process adversarial content as authority. Jev returns probabilistic estimates, not truth or authorization.

## Next integration
The production AI Solutions site code is **not** in this GitHub repository. To integrate into the site, add a protected backend route that calls `assess` with the server-side key, enforces request identity/rate/budget controls, stores only appropriate audit fields, and never directly exposes the secret. Do not route browser traffic to the ChatGPT MCP secret URL.

Guide source: https://mezcorp.notion.site/Jev-by-TypeSafe-The-Complete-Builder-s-Guide-Setup-Harnesses-Repos-When-NOT-to-Use-It-3ea7e41bed0b8148a8e4c6e8df030c51
