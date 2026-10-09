# Triadic Agent Control Protocol v0.5

## Post-Remediation Verification and Escalation

**Protocol:** Triadic Agent Control Protocol  
**Protocol version:** 0.5.0  
**Status:** Draft — final consistency candidate  
**Repository-relative path:** `specs/tacp-v0.5.md`

---

# 1. Relationship to Earlier Versions

This document extends `specs/tacp-v0.4.md`, which extends v0.3, v0.2, and v0.1.

All normative requirements from earlier versions remain in force unless this specification explicitly changes them.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

TACP v0.5 preserves:

- scout, analyst, gate, and executor separation;
- bounded challenge review;
- exact action binding;
- least-privilege authorization;
- final dispatch checking;
- immutable source history;
- v0.3 bounded recovery;
- v0.4 human-reviewed remediation;
- new operation identity for remediation;
- independent remediation authorization;
- prohibition on remediation-of-remediation chains.

Version 0.5 adds a bounded process for determining what happened **after a remediation operation was attempted**.

The central invariant is:

> **A remediation attempt MUST NOT be treated as successful merely because it was admitted, dispatched, or reported as successful by the executor. Its external effect MUST be independently verified before the remediation can be closed as completed.**

If the remediation result is absent, partial, contradictory, uncertain, harmful, or unverifiable, v0.5 terminates the remediation path and records an escalation requirement rather than creating another autonomous remediation.

---

# 2. Scope

TACP v0.5 addresses the following condition:

1. a v0.4-compatible remediation has been admitted;
2. a remediation mission has been dispatched or reached a terminal non-dispatch state;
3. the system must determine the actual post-remediation condition;
4. the system must classify the remediation result;
5. the system must close the path safely;
6. no automatic remediation-of-remediation is permitted.

Typical cases include partial correction, ineffective correction, secondary harm, uncertain delivery, missing evidence, contradictory evidence, and verification deadline exhaustion.

---

# 3. Non-Goals

The following are outside the v0.5 profile:

- automatic second remediation;
- recursive compensation chains;
- autonomous policy expansion after remediation failure;
- assuming executor success equals external success;
- hiding partial or secondary effects behind `completed`;
- unlimited re-observation;
- indefinite waiting for evidence;
- automatic transfer to a more privileged executor;
- automatic human approval of a new corrective action;
- distributed transaction atomicity;
- proof of legal, financial, physical, or social restoration;
- proof that escalation was acted upon outside TACP.

A deployment MAY provide external incident response, human review, or a separately authorized process after escalation. That later process is outside the v0.5 remediation chain.

---

# 4. Core Principles

## 4.1 Executor success is not remediation success

A tool response, API acknowledgement, transaction submission, execution receipt, or executor success claim alone MUST NOT establish remediation completion.

## 4.2 Post-remediation observation is required

After a remediation attempt, the scout MUST obtain fresh post-remediation observations within declared limits.

Observations SHOULD distinguish intended effect, observed target state, remaining source effect, newly introduced effect, unavailable evidence, contradictory evidence, and unresolved uncertainty.

## 4.3 Verification classifies effect, not intention

The analyst MUST classify the observed result from evidence rather than from the remediation plan's intent.

The result MUST be exactly one of:

```text
confirmed_effective
confirmed_partially_effective
confirmed_ineffective
confirmed_harmful
unresolved
not_dispatched
```

## 4.4 No silent success from uncertainty

Missing, stale, conflicting, out-of-scope, temporally impossible, or insufficient evidence MUST NOT be converted to `confirmed_effective`.

## 4.5 No autonomous remediation chain

A failed, partial, harmful, or unresolved remediation MUST NOT create another remediation operation under v0.5.

```text
source effect
  -> remediation
      -> post-remediation verification
          -> completed
          OR
          -> escalated
```

## 4.6 Escalation is terminal, not authority

Escalation records that the current remediation path has reached its boundary. It MUST NOT grant authority, imply human approval, or authorize another action.

---

# 5. Document Forms and Native Validation Scope

The broader TACP v0.5 profile may contain inherited:

1. `mission_bundle`
2. `remediation_bundle`
3. `remediation_outcome_bundle`

The **v0.5-native JSON Schema and semantic validator in this repository validate `remediation_outcome_bundle` only**.

`mission_bundle` and `remediation_bundle` remain governed by the inherited earlier-version profiles unless and until a separate v0.5-native representation is defined for them.

All v0.5-native records and bundles MUST declare:

```json
"protocol_version": "0.5.0"
```

A `remediation_outcome_bundle` MUST reference one terminal remediation attempt and MUST NOT contain a second remediation mission.

---

# 6. Remediation Outcome Bundle

A `remediation_outcome_bundle` contains:

| Field | Requirement |
|---|---|
| `protocol_version` | MUST equal `0.5.0` |
| `document_type` | MUST equal `remediation_outcome_bundle` |
| `outcome_id` | Unique outcome identifier |
| `remediation_ref` | Exact remediation being evaluated |
| `remediation_operation_id` | Exact remediation operation identity |
| `verification_limits` | Finite verification limits |
| `terminal_policy` | Optional explicit terminal policy; required semantically for completed `not_dispatched` |
| `records` | Ordered post-remediation records |
| `extensions` | Optional non-authoritative object |

The ordered `records` array MUST contain:

1. **one or more** `post_remediation_observation` records;
2. **exactly one** `remediation_verification` record;
3. **exactly one final** `remediation_closure` record.

All observations MUST precede the verification. The closure MUST be final.

---

# 7. Verification Limits

Every outcome bundle MUST declare finite:

- `max_observation_count`;
- `max_verification_age_seconds`;
- `final_verification_deadline`;
- `observation_scope`;
- `evidence_retrieval_budget`.

`observation_scope` is authoritative for the bounded v0.5 observation phase. Every `target_refs` entry in every post-remediation observation MUST be contained in that declared scope.

`evidence_retrieval_budget` bounds the number of unique evidence references consumed by the post-remediation observation phase in this repository profile.

The protocol MUST NOT extend these limits autonomously.

When a limit is exhausted before `confirmed_effective` can be established, the result MUST NOT be silently upgraded to success.

---

# 8. Post-Remediation Observation

A `post_remediation_observation` records externally observed state after the remediation attempt.

It MUST contain at least:

- `record_id`;
- `outcome_id`;
- `remediation_ref`;
- `remediation_operation_id`;
- `created_at`;
- `observed_at`;
- `producer_id`;
- `producer_role: scout`;
- `target_refs`;
- `evidence_refs`;
- `observed_effects`;
- `uncertainties`;
- `reason`.

The observation MUST NOT be produced solely from the executor's own success claim.

An observation used by a verification MUST NOT occur after that verification's `evaluated_at`.

---

# 9. Remediation Verification

A `remediation_verification` is produced by the analyst after reviewing fresh post-remediation observations.

It MUST contain:

- `record_id`;
- `outcome_id`;
- `remediation_ref`;
- `remediation_operation_id`;
- `observation_refs`;
- `evaluated_at`;
- `producer_id`;
- `producer_role: analyst`;
- `result`;
- `remaining_effects`;
- `new_effects`;
- `uncertainties`;
- `reason`.

Every referenced observation MUST exist in the same outcome bundle.

The verification MUST preserve any source effect that still exists and MUST separately identify newly introduced effects supported by evidence.

---

# 10. Result Semantics

## 10.1 `confirmed_effective`

Use only when fresh in-scope evidence supports all required remediation outcomes and no blocking remaining effect, new adverse effect, or unresolved uncertainty remains within the declared scope.

## 10.2 `confirmed_partially_effective`

Use when the remediation produced some intended benefit but did not satisfy all required outcomes. It MUST escalate.

## 10.3 `confirmed_ineffective`

Use when evidence establishes that the remediation did not achieve the required result. It MUST escalate.

## 10.4 `confirmed_harmful`

Use when evidence establishes a new adverse effect attributable to the remediation. It MUST escalate and MUST NOT automatically authorize another correction.

## 10.5 `unresolved`

Use when bounded verification cannot establish the result because of missing, conflicting, stale, inaccessible, or otherwise insufficient evidence, or because a verification limit is exhausted. It MUST escalate.

## 10.6 `not_dispatched`

Use only when authoritative evidence establishes that the remediation operation was never dispatched and produced no remediation execution effect.

Absence of a local execution receipt alone is insufficient.

---

# 11. Remediation Closure

A `remediation_closure` terminates the v0.5 outcome path.

Its `status` MUST be exactly one of:

```text
completed
escalated
```

`confirmed_effective` MUST close as `completed` with `escalation_required: false`.

`confirmed_partially_effective`, `confirmed_ineffective`, `confirmed_harmful`, and `unresolved` MUST close as `escalated` with `escalation_required: true`.

`not_dispatched` MAY close as `completed` **only when the bundle explicitly declares**:

```json
"terminal_policy": {
  "not_dispatched": "completed"
}
```

Otherwise `not_dispatched` MUST NOT be silently treated as completed and MAY be escalated according to deployment policy.

The closure MUST reference the exact verification record that determines its status.

---

# 12. Escalation Requirements

An escalated closure MUST include:

- `reason_codes`;
- `basis_refs`;
- `escalation_required: true`;
- nonempty `escalation_scope`;
- `prohibited_automatic_actions`;
- `reason`.

`prohibited_automatic_actions` MUST include at least:

```text
repeat_source_operation
repeat_remediation_operation
create_remediation_of_remediation
self_expand_authority
```

Implementations MAY add stricter prohibition strings beyond this mandatory subset.

---

# 13. Record Ordering and Time

The minimum successful path is:

```text
post_remediation_observation
  -> remediation_verification
      -> remediation_closure(completed)
```

The minimum escalation path is:

```text
post_remediation_observation
  -> remediation_verification
      -> remediation_closure(escalated)
```

All post-remediation observations MUST precede verification in record order and in evidence time. A verification MUST NOT rely on an observation whose `observed_at` is later than `evaluated_at`.

A verification MUST NOT be finalized after `final_verification_deadline`.

---

# 14. Identity and Binding

Every v0.5 post-remediation record MUST bind the same:

```text
outcome_id
remediation_ref
remediation_operation_id
```

A mismatch is invalid.

`remediation_operation_id` MUST equal the operation identity of the remediation being verified and MUST NOT be a newly invented identity for another corrective action.

---

# 15. Source and Remediation Immutability

v0.5 MUST NOT rewrite source mission records, source execution receipts, source closure, v0.4 impact assessment, v0.4 remediation plan, human review, remediation admission, or remediation execution history.

Post-remediation observations, verification, and closure are additive records.

---

# 16. Required Negative Cases

A v0.5 conformance suite SHOULD include at least:

1. `executor-success-without-verification`
2. `completed-with-partial-effect`
3. `completed-with-ineffective-result`
4. `completed-with-harmful-result`
5. `completed-with-unresolved-result`
6. `stale-post-remediation-evidence`
7. `missing-post-remediation-observation`
8. `verification-operation-id-mismatch`
9. `closure-verification-ref-mismatch`
10. `second-remediation-created`
11. `authority-expanded-after-failure`
12. `verification-after-deadline`
13. `not-dispatched-with-execution-evidence`
14. `new-effect-silently-omitted`
15. `not-dispatched-without-terminal-policy`
16. `observation-after-verification`
17. `observation-outside-scope`
18. `evidence-budget-exceeded`

The suite SHOULD include positive examples for effective completion, partial escalation, harmful escalation, unresolved escalation, and authoritative non-dispatch completion under explicit terminal policy.

---

# 17. Runtime Boundary

Document validation can establish recorded structure and semantic consistency only.

It cannot independently prove:

- external target truth;
- evidence authenticity;
- scout operational independence;
- globally unique remediation;
- absence of out-of-band second remediation;
- actual privilege revocation or fencing;
- successful delivery of escalation to a human operator;
- containment of real harmful effects.

Those properties require independent runtime enforcement and evidence systems.

---

# 18. Core Invariants

```text
executor_success != remediation_success

confirmed_effective
    requires independent, fresh, in-scope post-remediation evidence

partial | ineffective | harmful | unresolved
    -> escalated

not_dispatched + completed
    requires explicit terminal policy

observation_after_verification
    -> invalid

out_of_scope_observation
    -> invalid

evidence_budget_exceeded
    -> invalid

escalated
    != authorization

failed_remediation
    != permission_for_second_remediation

source_history
    remains immutable

remediation_history
    remains immutable
```

---

# 19. Minimal State Transition

```text
REMEDIATION_ADMITTED
    |
    v
REMEDIATION_ATTEMPT
    |
    v
POST_REMEDIATION_OBSERVATION
    |
    v
REMEDIATION_VERIFICATION
    |
    +--> confirmed_effective ------> COMPLETED
    |
    +--> not_dispatched ----------> COMPLETED only by explicit policy
    |                               or ESCALATED by policy
    |
    +--> partially_effective -----+
    +--> ineffective -------------+
    +--> harmful -----------------+--> ESCALATED
    +--> unresolved --------------+

ESCALATED
    |
    +--> no automatic successor remediation
```

---

# 20. Summary

TACP v0.4 answers:

> **How may a system authorize a bounded corrective action after an external effect has already occurred?**

TACP v0.5 answers:

> **How does the system determine whether that remediation actually worked, and how does it stop safely when it did not?**

The design objective is not recursive autonomy. It is bounded verification, explicit uncertainty, immutable history, and a terminal escalation boundary.
