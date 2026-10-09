# Changelog

This changelog records specification and validation milestones. It does not imply production release certification.

## 2026-10-09 — v0.6 first complete cycle milestone

- GitHub Actions run #179 succeeded on Python 3.10 and 3.12 at commit `e757fe98fdbef4d78292a38bb7b6e232c594267e`.
- Registered v0.6 suite contains 5 positive and 16 negative fixtures; 21/21 expected outcomes matched.
- Added native v0.6 schema and semantic validation for escalation handoff and responsibility transfer.
- Added explicit distinction between escalation, delivery, acceptance, responsibility transfer, and execution authorization.
- Require an explicit, attributable receiver disposition before responsibility can be transferred.
- Require accepted scope to remain within requested scope and acceptance to remain within declared deadlines and freshness limits.
- Require rejected, unconfirmed, and timed-out handoffs to close as `not_transferred` rather than silently assuming responsibility transfer.
- Added synthetic runtime negatives for second remediation after handoff, authority expansion during handoff, and post-closure handoff-history rewriting.
- Registered mandatory prohibitions against source restart, remediation restart, remediation-of-remediation, self-authority expansion, self-acceptance, and assuming acceptance from delivery.
- Marked v0.6 as the **First Complete Cycle Boundary**:
  `Plan → Authorize → Execute → Verify → Recover → Remediate → Verify Remediation → Escalate → Handoff`.
- Entered feature-freeze / architecture-review phase before any further capability expansion.

## v0.6.0 — Escalation Handoff and Responsibility Transfer

- Start from a v0.5 remediation outcome already closed as `escalated`.
- Treat handoff emission and transport acknowledgement as insufficient to establish responsibility transfer.
- Require exactly one `handoff_request`, one `handoff_disposition`, and one terminal `handoff_closure`, with zero or more bounded delivery observations.
- Support disposition results `accepted`, `rejected`, `unconfirmed`, and `timeout`.
- Permit `transferred` only after explicit acceptance by an independently attributable receiving authority.
- Preserve `not_transferred` as the terminal state for rejection, missing authoritative acceptance, or timeout.
- Require receiver and accepted-scope binding across request, disposition, and closure.
- Preserve source, recovery, remediation, v0.5 verification, and escalation history as immutable prior trace.
- Keep the original autonomous path stopped after handoff closure.
- Clarify that receiver acceptance transfers responsibility only; it does not grant TACP execution authorization.

## 2026-10-09 — v0.5 final consistency patch

- GitHub Actions run #147 succeeded on Python 3.10 and 3.12 at commit `2a9bd1cc7170dca99a2ccffce1aae2a636211667`.
- Registered v0.5 suite expanded to 5 positive and 18 negative fixtures; 23/23 expected outcomes matched.
- Added explicit `terminal_policy` binding for clean `not_dispatched` closure.
- Reject future-dated observations, out-of-scope observation targets, and unique evidence-budget overruns.
- Added four regression negatives and exercised extensible escalation prohibitions in a positive fixture.
- Clarified native v0.5 outcome-bundle schema scope and observation/verification/closure cardinality.

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
