# Changelog

This changelog records specification and validation milestones. It does not imply production release certification.

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
