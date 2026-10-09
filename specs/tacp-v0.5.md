# Triadic Agent Control Protocol v0.5

## Post-Remediation Verification and Escalation

**Protocol:** Triadic Agent Control Protocol  
**Protocol version:** 0.5.0  
**Status:** Draft — specification  
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

The central rule is:

> **A remediation attempt MUST NOT be treated as successful merely because it was admitted, dispatched, or reported as successful by the executor. Its external effect MUST be independently verified before the remediation can be closed as completed.**

If the remediation result is absent, partial, contradictory, uncertain, harmful, or unverifiable, v0.5 terminates the remediation path and records an escalation requirement rather than creating another autonomous remediation.

---

# 2. Scope

TACP v0.5 addresses the following condition:

1. a v0.4-compatible remediation has been admitted;
2. a remediation mission has been dispatched or reached a terminal non-dispatch state;
3. the system must determine the actual post-remediation condition;
4. the system must decide whether the remediation is complete, ineffective, partially effective, harmful, or unresolved;
5. no automatic remediation-of-remediation is permitted.

Examples include:

- a compensating transaction reports success but the target balance remains incorrect;
- a corrective configuration change applies only partially;
- a containment operation stops one effect but leaves another active;
- a notification operation is dispatched but delivery cannot be established;
- a remediation creates an unexpected secondary effect;
- a remediation outcome cannot be observed before the verification deadline.

---

# 3. Non-Goals

The following are outside the v0.5 profile:

- automatic second remediation;
- recursive compensation chains;
- autonomous policy expansion after remediation failure;
- assuming executor success equals external success;
- hiding partial or secondary effects behind a completed status;
- unlimited re-observation;
- indefinite waiting for evidence;
- automatic transfer to a more privileged executor;
- automatic human approval of a new corrective action;
- distributed transaction atomicity;
- proof of legal, financial, physical, or social restoration;
- proof that escalation was acted upon outside TACP.

A deployment MAY provide external incident response, human review, or a new independently authorized process after escalation, but that process is outside the v0.5 remediation chain.

---

# 4. Core Principles

## 4.1 Executor success is not remediation success

An executor may report:

```text
succeeded
```

without the intended external state actually being achieved.

Therefore, remediation completion MUST require independent post-remediation verification.

A tool response, API acknowledgement, transaction submission, or executor receipt alone MUST NOT establish remediation completion.

---

## 4.2 Post-remediation observation is required

After a remediation execution attempt, the scout MUST obtain fresh post-remediation observations within declared freshness and time limits.

The observations MUST distinguish:

- intended effect;
- observed target state;
- remaining source effect;
- newly introduced effect;
- unavailable evidence;
- contradictory evidence;
- unresolved uncertainty.

Repeated reading of the same stale evidence MUST NOT be treated as a fresh verification event.

---

## 4.3 Verification must classify effect, not intention

The analyst MUST classify the observed remediation outcome from evidence rather than from the remediation plan's intent.

A remediation result MUST be classified as exactly one of:

```text
confirmed_effective
confirmed_partially_effective
confirmed_ineffective
confirmed_harmful
unresolved
not_dispatched
```

These classifications describe the observed remediation result, not moral judgment or policy desirability.

---

## 4.4 No silent success from uncertainty

The following MUST NOT be converted to `confirmed_effective`:

- missing evidence;
- stale evidence;
- conflicting evidence;
- unknown target state;
- uncertain execution outcome;
- partial restoration;
- evidence that only proves dispatch;
- evidence that only proves tool-level acknowledgement.

Unknown remains unknown until bounded verification resolves it.

---

## 4.5 No autonomous remediation chain

A failed, partial, harmful, or unresolved remediation MUST NOT create another remediation operation under v0.5.

The path is:

```text
source effect
  -> remediation
      -> post-remediation verification
          -> completed
          OR
          -> escalated
```

not:

```text
source effect
  -> remediation A
      -> remediation B
          -> remediation C
```

---

## 4.6 Escalation is a terminal protocol outcome

Escalation records that the current TACP remediation path has reached its boundary.

Escalation MUST NOT itself grant authority.

Escalation MUST NOT imply that a human has reviewed the case.

Escalation MUST NOT imply that another action is permitted.

Any later action requires a separately defined process and independently valid authorization.

---

# 5. Document Forms

v0.5 defines three primary forms:

1. `mission_bundle`
2. `remediation_bundle`
3. `remediation_outcome_bundle`

The new v0.5 form is `remediation_outcome_bundle`.

All v0.5-native records and bundles MUST declare:

```json
"protocol_version": "0.5.0"
```

A `remediation_outcome_bundle` MUST reference one completed or terminal remediation attempt and MUST NOT contain a second remediation mission.

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
| `records` | Ordered post-remediation records |
| `extensions` | Optional non-authoritative object |

The ordered `records` array contains exactly:

1. `post_remediation_observation`
2. `remediation_verification`
3. `remediation_closure`

Additional observations MAY be included before the final verification only when permitted by the declared verification limits.

---

# 7. Post-Remediation Observation

A `post_remediation_observation` records externally observed state after the remediation attempt.

It MUST contain at least:

- `record_id`;
- `outcome_id`;
- `remediation_ref`;
- `remediation_operation_id`;
- `observed_at`;
- `producer_id`;
- `producer_role` equal to `scout`;
- `target_refs`;
- `evidence_refs`;
- `observed_effects`;
- `uncertainties`;
- `reason`.

The observation MUST NOT be produced solely from the executor's own success claim.

The observation MAY cite the executor receipt as one evidence source but MUST distinguish that receipt from independent target-state evidence.

---

# 8. Remediation Verification

A `remediation_verification` is produced by the analyst after reviewing fresh post-remediation observations.

It MUST contain:

- `record_id`;
- `outcome_id`;
- `remediation_ref`;
- `remediation_operation_id`;
- `observation_refs`;
- `evaluated_at`;
- `producer_id`;
- `producer_role` equal to `analyst`;
- `result`;
- `remaining_effects`;
- `new_effects`;
- `uncertainties`;
- `reason`.

`result` MUST be exactly one of:

```text
confirmed_effective
confirmed_partially_effective
confirmed_ineffective
confirmed_harmful
unresolved
not_dispatched
```

The verification MUST preserve any source effect that still exists.

The verification MUST separately identify newly introduced effects when evidence supports them.

---

# 9. Result Semantics

## 9.1 `confirmed_effective`

Use only when fresh evidence supports all required remediation outcomes and no unresolved blocking effect remains within the remediation scope.

This classification does not erase the original source effect from history.

---

## 9.2 `confirmed_partially_effective`

Use when the remediation produced a beneficial or intended effect but did not satisfy all required remediation outcomes.

A partial result MUST NOT close as `completed`.

It requires escalation.

---

## 9.3 `confirmed_ineffective`

Use when fresh evidence establishes that the remediation did not achieve the required result.

It requires escalation.

---

## 9.4 `confirmed_harmful`

Use when fresh evidence establishes a new adverse effect attributable to the remediation operation.

It requires escalation.

A `confirmed_harmful` result MUST NOT automatically authorize containment or correction.

---

## 9.5 `unresolved`

Use when bounded verification cannot establish the remediation result.

Examples include:

- missing evidence;
- conflicting evidence;
- stale evidence;
- inaccessible target;
- unknown execution outcome;
- verification deadline exhaustion.

It requires escalation.

---

## 9.6 `not_dispatched`

Use only when authoritative evidence establishes that the remediation operation was never dispatched and produced no remediation execution effect.

A local absence of an execution receipt alone is insufficient.

---

# 10. Remediation Closure

A `remediation_closure` terminates the v0.5 outcome path.

Its `status` MUST be exactly one of:

```text
completed
escalated
```

`completed` is permitted only when verification result is:

```text
confirmed_effective
```

or, when no remediation dispatch occurred and the enclosing policy explicitly treats that as a clean terminal outcome:

```text
not_dispatched
```

All other verification results MUST close as:

```text
escalated
```

The closure MUST reference the exact verification record that determines its status.

---

# 11. Escalation Record Requirements

When closure status is `escalated`, the closure MUST contain:

- `reason_codes`;
- `basis_refs`;
- `escalation_required: true`;
- `escalation_scope`;
- `prohibited_automatic_actions`;
- `reason`.

`reason_codes` MAY include:

```text
partial_remediation
ineffective_remediation
harmful_remediation
unresolved_remediation_outcome
verification_deadline_reached
evidence_stale
evidence_conflict
target_unavailable
execution_outcome_unknown
```

`prohibited_automatic_actions` MUST include at least:

```text
repeat_source_operation
repeat_remediation_operation
create_remediation_of_remediation
self_expand_authority
```

An implementation MAY add stricter prohibitions.

---

# 12. Bounded Verification

Every remediation outcome process MUST declare finite limits for:

- maximum observation count;
- maximum verification age;
- final verification deadline;
- observation scope;
- evidence retrieval budget.

The protocol MUST NOT extend these limits autonomously.

When a limit is exhausted before `confirmed_effective` can be established, the result MUST become `unresolved` and the closure MUST become `escalated`.

---

# 13. Record Ordering

The minimum valid successful path is:

```text
post_remediation_observation
  -> remediation_verification
      -> remediation_closure(completed)
```

The minimum valid escalation path is:

```text
post_remediation_observation
  -> remediation_verification
      -> remediation_closure(escalated)
```

A closure MUST be the final v0.5 record in the bundle.

No execution or remediation-plan record may appear after closure.

---

# 14. Identity and Binding

Every v0.5 post-remediation record MUST bind the same:

```text
outcome_id
remediation_ref
remediation_operation_id
```

A mismatch is invalid.

The `remediation_operation_id` MUST equal the operation identity of the remediation that is being verified.

It MUST NOT equal a newly invented operation identity intended for another corrective action.

---

# 15. Source and Remediation Immutability

v0.5 MUST NOT rewrite:

- source mission records;
- source execution receipts;
- source closure;
- v0.4 impact assessment;
- v0.4 remediation plan;
- human review;
- remediation admission;
- remediation execution history.

Post-remediation observations and verification are additive records.

Historical facts remain historical facts even if later state changes.

---

# 16. Required Negative Cases

A v0.5 conformance suite SHOULD include at least these rejection cases:

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

The suite SHOULD also include positive examples for:

- effective remediation completed;
- partial remediation escalated;
- harmful remediation escalated;
- unresolved remediation escalated;
- authoritative non-dispatch closure.

---

# 17. Runtime Boundary

Document validation can establish only recorded structure and semantic consistency.

It cannot independently prove:

- that the external target actually changed;
- that evidence is authentic;
- that the scout is operationally independent from the executor;
- that a remediation was globally unique;
- that no external process launched a second remediation;
- that escalation reached a human operator;
- that runtime permissions were actually revoked or fenced;
- that a harmful effect was fully contained.

Those properties require independent runtime enforcement and evidence systems.

---

# 18. v0.5 Core Invariants

A conforming v0.5 implementation MUST preserve the following invariants:

```text
executor_success != remediation_success

confirmed_effective
    requires independent post-remediation evidence

partial | ineffective | harmful | unresolved
    -> escalated

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
    +--> not_dispatched ----------> COMPLETED or ESCALATED by policy
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

TACP v0.5 answers the next question:

> **How does the system prove whether that remediation actually worked, and how does it stop safely when it did not?**

The v0.5 answer is intentionally conservative:

> **Verify the external result independently. Complete only on confirmed effectiveness. Otherwise terminate the remediation chain and escalate without granting new authority.**
