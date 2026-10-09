# Changelog

This changelog records specification and validation milestones. It does not imply production release certification.

## 2026-10-09 — v0.5 validation milestone

- GitHub Actions run #134 completed successfully on Python 3.10 and 3.12.
- Registered v0.1-v0.5 example suites passed their expected outcomes.
- v0.5 post-remediation semantic validation was added in `scripts/validate_v05.py`.
- v0.5 example-suite execution was added in `scripts/validate_v05_examples.py`.
- GitHub Actions now validates v0.1-v0.5 and summarizes all registered versions.
- v0.5 currently includes 5 positive and 14 negative examples, with 19/19 expected outcomes matched.
- 4 v0.5 negatives are explicitly classified as synthetic runtime-state checks: automatic second remediation creation, self-authority expansion after failure, execution evidence contradicting `not_dispatched`, and silent omission of a newly observed adverse effect.
- The v0.5 validator enforces post-remediation observation, record binding, evidence freshness, verification deadlines, result-to-closure consistency, and mandatory escalation prohibitions.
- README and conformance documentation were updated to distinguish successful registered validation from production runtime safety.

## v0.5.0 — Post-Remediation Verification and Escalation

- Require independent post-remediation observation rather than trusting executor success reports.
- Require analyst verification of the actual post-remediation state.
- Classify outcomes as `confirmed_effective`, `confirmed_partially_effective`, `confirmed_ineffective`, `confirmed_harmful`, `unresolved`, or `not_dispatched`.
- Permit `completed` only for verified effective outcomes and explicitly allowed clean non-dispatch outcomes.
- Require `escalated` for partial, ineffective, harmful, and unresolved outcomes.
- Require bounded evidence freshness and a final verification deadline.
- Preserve source and remediation history as immutable prior trace.
- Prohibit automatic source repetition, remediation repetition, remediation-of-remediation, and self-expansion of authority after escalation.
- Treat escalation as a terminal protocol outcome, not as new execution authority.

## 2026-10-09 — v0.4 validation milestone

- GitHub Actions run #106 completed successfully on Python 3.10 and 3.12.
- Registered v0.1-v0.4 example suites passed their expected outcomes.
- v0.4 remediation schema and semantic validation were integrated into `scripts/validate.py`.
- v0.1-v0.3 compatibility remains delegated to `scripts/validate_legacy.py`.
- v0.4 registered suite currently includes 3 positive and 9 negative examples.
- `duplicate-remediation.json` is treated as a synthetic runtime-state negative rather than a document-only failure.
- README and conformance documentation were updated to distinguish CI fixture success from production runtime safety.

## v0.4.0 — Human-Reviewed Remediation and Compensation

- Preserve the recorded source effect rather than rewriting history as if the effect never occurred.
- Require a new remediation operation identity.
- Require explicit causal linkage to the source operation.
- Require independent remediation authorization.
- Require human review before remediation admission.
- Bound remediation by timing, resources, and policy checks.
- Prevent duplicate remediation through external/runtime state checks.
- Prohibit remediation-of-remediation chains within the v0.4 model.

## v0.3.0 — Recovery

- Added bounded recovery semantics for non-dispatch, no-effect, uncertain, blocked, and related terminal states.
- Added successor handling with fresh review and execution controls.
- Added registered synthetic runtime negatives for conditions that cannot be proven from a single document.

## v0.2.0 — Execution-time control

- Added dispatch-time authorization and state checks.
- Added held, expired, revoked, deadline, resource-limit, target-change, and authorization-unknown behavior.

## v0.1.0 — Core mission model

- Established scout, analyst, and executor role separation.
- Established independent gate authorization.
- Added bounded review, traceable evidence, explicit uncertainty, duplicate prevention, and post-execution verification.
