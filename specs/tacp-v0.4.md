# Triadic Agent Control Protocol v0.4

## Human-Reviewed Remediation and Compensation

**Protocol:** Triadic Agent Control Protocol  
**Protocol version:** 0.4.0  
**Status:** Draft — specification  
**Repository-relative path:** `specs/tacp-v0.4.md`

---

# 1. Relationship to Earlier Versions

This document extends `specs/tacp-v0.3.md`, which extends v0.2 and v0.1.

All normative requirements from earlier versions remain in force unless this specification explicitly changes them.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

TACP v0.4 preserves:

- scout, analyst, gate, and executor separation;
- bounded challenge review;
- exact action binding;
- least-privilege authorization;
- final dispatch checking;
- bounded execution;
- immutable mission closure;
- v0.3 recovery and successor protections.

Version 0.4 adds a separate remediation process for cases where an external effect has already been established and therefore the original logical operation MUST NOT simply be retried.

The central rule is:

> **A confirmed effect MUST NOT be erased from history, relabeled as no-effect, or treated as permission to repeat the original operation.**

Instead, any corrective action MUST be represented as a new, separately authorized remediation operation.

---

# 2. Scope

TACP v0.4 addresses the following condition:

1. a source mission has reached a terminal state;
2. an attributable external effect is confirmed or conservatively treated as present;
3. repeating the source operation would be unsafe, incorrect, or duplicative;
4. an additional action may be needed to reduce, reverse, contain, correct, or communicate the effect.

Examples include:

- compensating for a completed financial or logical transaction;
- correcting an unintended configuration change;
- containing an external process that has already begun producing effects;
- notifying affected parties where reversal is impossible;
- restoring a target toward a safe state through a new operation.

v0.4 does **not** claim that every external action is reversible.

A remediation may reduce harm without restoring the exact prior world state.

---

# 3. Non-Goals

The following are outside the v0.4 profile:

- automatic unlimited rollback;
- pretending that a compensating action deletes the original effect;
- autonomous agent approval of high-impact remediation;
- repeated remediation chains;
- remediation of a remediation;
- multiple parallel remediation missions for the same source effect;
- distributed transaction atomicity;
- guaranteed restoration of physical-world state;
- guaranteed reversal of financial, legal, social, or human consequences;
- silent reuse of the source mission's authority;
- unbounded retry of remediation execution.

A deployment MAY support stronger guarantees externally, but MUST NOT attribute those guarantees to document conformance alone.

---

# 4. Core Principles

## 4.1 Source immutability

The source mission and all of its records MUST remain unchanged.

A later remediation MUST NOT:

- change a source execution outcome;
- rewrite a source closure;
- remove recorded effects;
- alter timestamps;
- replace the original operation identity;
- retroactively declare an effect absent.

Historical correction MUST occur through new records and new operations.

---

## 4.2 Effect acknowledgement

A confirmed external effect MUST remain explicitly acknowledged.

A remediation record MUST identify the effect being addressed.

A deployment MUST NOT convert:

```text
confirmed_effect
```

into:

```text
confirmed_no_effect
```

merely because a later compensating action succeeded.

Compensation changes the world after the original effect. It does not erase the original event.

---

## 4.3 New operation identity

A remediation action is a new logical operation.

Therefore:

```text
source.operation_id != remediation.operation_id
```

MUST hold.

The remediation operation MUST instead contain an explicit causal relationship to the source operation.

---

## 4.4 Independent authorization

A remediation MUST have independently valid authorization.

The following MUST NOT automatically authorize remediation:

- the source mission authorization;
- a source execution receipt;
- a recovery authorization;
- an expired authorization;
- a human approval for another remediation candidate.

A source authorization MAY be cited as historical context but MUST NOT be treated as current execution authority.

---

## 4.5 Bounded remediation

One source effect may produce at most one remediation mission under the v0.4 profile.

The remediation mission MUST NOT itself become a remediation source.

If remediation fails, becomes uncertain, or creates a further unresolved effect, the process MUST terminate in a held or stopped state and require escalation outside this profile.

This prevents:

```text
source
  -> remediation A
      -> remediation B
          -> remediation C
              -> ...
```

from becoming an unbounded compensation loop.

---

# 5. Document Forms

v0.4 defines two primary document forms:

1. `mission_bundle`
2. `remediation_bundle`

A normal v0.4 mission continues to follow the mission requirements inherited from earlier versions.

A remediation action is represented by a `remediation_bundle`.

All embedded v0.4 records and bundles MUST declare:

```json
"protocol_version": "0.4.0"
```

Mixed protocol versions inside one remediation bundle are invalid.

Historical bundles MAY remain stored under their original versions but MUST NOT be relabeled to `0.4.0` without explicit migration.

---

# 6. Remediation Bundle

A closed remediation bundle has these core fields:

| Field | Requirement |
|---|---|
| `protocol_version` | MUST equal `0.4.0` |
| `document_type` | MUST equal `remediation_bundle` |
| `remediation_id` | Unique remediation identifier |
| `source` | Embedded closed v0.4 source mission |
| `records` | Ordered remediation control records |
| `remediation_mission` | Optional closed remediation mission |
| `extensions` | Optional non-authoritative object |

The ordered `records` array contains exactly:

1. `impact_assessment`
2. `remediation_plan`
3. `human_review`
4. `remediation_admission`

A permitted remediation mission MAY follow an allow admission.

A denied admission MUST NOT contain a remediation mission.

---

# 7. Source Eligibility

The source mission MUST be terminal.

Its final closure MUST be one of the states permitted by the remediation policy.

The source MUST contain evidence that an external effect:

- occurred;
- probably occurred and cannot safely be treated as absent; or
- remains sufficiently uncertain that conservative containment is required.

A source known to be:

```text
confirmed_not_dispatched
```

or:

```text
confirmed_no_effect
```

belongs to the v0.3 recovery profile rather than v0.4 remediation.

A deployment MUST NOT use remediation merely to bypass v0.3 successor restrictions.

---

# 8. Remediation Types

`remediation_type` MUST be one of:

```text
compensate
contain
correct
notify
```

## 8.1 compensate

A new action whose intended effect offsets or counterbalances the source effect.

Example:

```text
source:
  debit account A

remediation:
  issue authorized compensating credit
```

Compensation MUST NOT be represented as deletion of the original debit.

---

## 8.2 contain

An action intended to stop expansion, propagation, or continuation of an already established effect.

Examples:

- disable a compromised credential;
- fence a background job;
- isolate a resource;
- stop downstream propagation.

Containment does not prove reversal.

---

## 8.3 correct

An action that moves a target from an incorrect state toward a known valid state.

Correction requires authoritative evidence of the current target state.

The desired corrective state MUST NOT be inferred solely from the source agent's earlier intention.

---

## 8.4 notify

A non-reversal remediation that communicates the established effect to an authorized recipient or affected party.

Notification may be appropriate when:

- the effect cannot be undone;
- correction requires external human action;
- legal or operational policy requires disclosure.

Notification itself is an external effect and MUST use normal TACP controls.

---

# 9. Impact Assessment Record

The first remediation record has:

```text
record_type = impact_assessment
producer_role = analyst
```

Required fields:

| Field | Meaning |
|---|---|
| `source_mission_ref` | Source mission |
| `source_closure_ref` | Source closure |
| `source_operation_id` | Original logical operation |
| `source_execution_refs` | Source executions relevant to the effect |
| `effect_status` | Effect classification |
| `effect_scope` | Bounded impact scope |
| `evidence` | Supporting evidence |
| `uncertainties` | Remaining uncertainties |
| `assessed_at` | Assessment time |
| `reason` | Human-readable reasoning |

`effect_status` MUST be one of:

```text
confirmed
probable
unresolved
```

`effect_scope` MUST be one of:

```text
bounded
partially_bounded
unresolved
```

A remediation that changes external state MUST NOT be admitted when:

```text
effect_scope = unresolved
```

except a narrowly scoped `contain` action explicitly permitted by policy.

---

# 10. Effect Evidence

Each impact evidence object contains:

| Field | Requirement |
|---|---|
| `evidence_ref` | External immutable reference |
| `issuer_ref` | Evidence issuer |
| `observed_at` | Observation time |
| `kind` | Evidence type |

Allowed initial evidence kinds are:

```text
operation_receipt
effect_audit
target_snapshot
downstream_receipt
reservation_ledger
fence_receipt
human_report
lookup_failure
```

A `lookup_failure` establishes uncertainty only.

It MUST NOT establish:

- absence of effect;
- successful reversal;
- finality;
- safe remediation eligibility.

A target snapshot alone MUST NOT establish causation.

---

# 11. Remediation Plan Record

The second record has:

```text
record_type = remediation_plan
producer_role = controller
```

Required fields:

| Field | Meaning |
|---|---|
| `impact_assessment_ref` | Preceding impact assessment |
| `remediation_type` | compensate / contain / correct / notify |
| `source_operation_id` | Original operation |
| `remediation_operation_id` | New operation |
| `objective` | Exact remediation objective |
| `target_scope` | Bounded remediation scope |
| `proposed_action` | Exact proposed action |
| `authorization_ref` | New immutable authority |
| `policy_ref` | Remediation policy |
| `expected_results` | Expected remediation results |
| `stop_conditions` | Mandatory stop conditions |
| `limits` | Deadline, review and resource limits |
| `reason` | Explanation |

The following MUST hold:

```text
remediation_operation_id != source_operation_id
```

The plan MUST contain:

```text
compensates_operation_ref
```

or equivalent causal reference identifying the exact source operation.

---

# 12. Exact Action Binding

The proposed remediation action MUST be structurally fixed before human approval.

The human review, admission, dispatch check, and execution MUST refer to the same exact action.

Changes to any of the following require a new remediation proposal:

- target;
- operation;
- operation ID;
- parameters;
- authorization;
- policy;
- limits;
- expected results;
- stop conditions.

Agents MUST NOT broaden scope after approval.

---

# 13. Human Review

The third record has:

```text
record_type = human_review
producer_role = human
```

Required fields:

| Field | Meaning |
|---|---|
| `impact_assessment_ref` | Exact assessment reviewed |
| `remediation_plan_ref` | Exact plan reviewed |
| `reviewer_ref` | Human reviewer |
| `reviewer_authority_ref` | Reviewer authority |
| `decision` | approve / hold / reject |
| `reviewed_at` | Review time |
| `valid_until` | Approval expiry |
| `evidence_refs` | Authentication/review evidence |
| `reason` | Human rationale |

The human review MUST bind to the exact immutable remediation plan.

Approval MUST NOT:

- change evidence;
- broaden authorization;
- resolve unknown effects by declaration;
- override policy;
- waive normal mission review;
- bypass the final dispatch check.

Self-declared agent claims of human approval are invalid.

---

# 14. Remediation Admission

The fourth record has:

```text
record_type = remediation_admission
producer_role = gate
```

Required fields:

| Field | Meaning |
|---|---|
| `impact_assessment_ref` | Impact record |
| `remediation_plan_ref` | Plan |
| `human_review_ref` | Human review |
| `checked_at` | Admission check time |
| `checks` | Deterministic admission checks |
| `decision` | allow / deny |
| `claim_ref` | Required on allow |
| `start_before` | Required on allow |
| `reason_codes` | Machine-readable reasons |
| `reason` | Explanation |

---

# 15. Admission Checks

The `checks` object MUST contain exactly:

```text
reference_integrity
source_terminal
effect_established
effect_scope_bounded
remediation_policy_valid
remediation_authorization_valid
human_approval_valid
action_identity_new
causal_link_valid
target_scope_valid
budgets_available
deadline_valid
duplicate_remediation_absent
```

Each value is:

```text
pass
fail
unknown
```

An `allow` decision requires every check to be `pass`.

Any `fail` or `unknown` requires `deny`.

---

# 16. Admission Reason Codes

Allow uses exactly:

```text
remediation_admitted
```

Deny MAY include:

```text
reference_invalid
source_ineligible
effect_unconfirmed
effect_scope_unresolved
remediation_policy_invalid
remediation_authorization_invalid
human_approval_invalid
operation_identity_reused
causal_link_invalid
target_scope_invalid
resource_limit_reached
deadline_reached
duplicate_remediation
```

All mechanically established denial reasons SHOULD be retained.

---

# 17. Remediation Claim

An allow admission MUST contain a unique `claim_ref`.

The runtime MUST atomically bind the claim to:

- source mission;
- source closure;
- source operation;
- remediation ID;
- remediation operation ID;
- approved plan.

The claim MUST be single-use.

Two remediation missions MUST NOT consume the same source effect claim.

The runtime MUST reject duplicate claim consumption across:

- processes;
- restarts;
- machines;
- documents;
- concurrent requests.

Document validation alone cannot prove this property.

---

# 18. Remediation Mission

A remediation mission is a normal TACP mission.

It MUST complete the full control sequence:

```text
mission
↓
observation
↓
assessment
↓
challenge review
↓
gate
↓
dispatch check
↓
execution
↓
outcome verification
↓
closure
```

Human approval of the remediation plan MUST NOT substitute for any of these stages.

The remediation mission MUST use:

```text
remediation_operation_id
```

as its operation identity.

It MUST NOT use the source operation ID.

---

# 19. Fresh Observation Requirement

The remediation mission MUST acquire fresh observations after creation.

Source observations MAY be used as historical context but MUST NOT substitute for fresh target-state verification.

A correction or compensation based solely on stale source state MUST NOT be dispatched.

The final dispatch check MUST independently verify that the current target state still permits the exact remediation action.

---

# 20. Authorization Requirements

The remediation mission requires new execution authority.

The runtime MUST verify:

- current authorization validity;
- exact action scope;
- target scope;
- executor identity;
- expiration;
- revocation;
- policy compatibility.

An authorization reference copied from the source without explicit remediation authority MUST fail admission.

---

# 21. Remediation Outcome

The remediation execution outcome MUST be recorded separately from the source outcome.

Possible success of the remediation means only:

> the remediation action produced its expected result.

It MUST NOT mean:

> the original source action never happened.

For example:

```text
source_effect = confirmed
remediation = compensated
```

is valid.

The system MUST NOT rewrite this as:

```text
source_effect = none
```

---

# 22. Verification

Successful execution MUST be followed by independent outcome verification.

Verification SHOULD determine:

- whether the remediation action occurred;
- whether the intended corrective state was reached;
- whether unexpected secondary effects occurred;
- whether containment remains effective;
- whether further human escalation is required.

A remediation MUST NOT close as completed solely because an executor reports success.

---

# 23. Closure

A remediation mission uses normal mission closure semantics.

A completed remediation MUST preserve a causal relationship to the source.

A held or stopped remediation MUST NOT automatically generate another remediation.

Instead:

```text
remediation held/stopped
        ↓
human escalation
```

is required outside the v0.4 automatic profile.

---

# 24. No Remediation of Remediation

A remediation mission MUST NOT become the source of another v0.4 remediation bundle.

This is a hard v0.4 bound.

A validator MUST reject any remediation bundle whose source mission itself declares a remediation relationship.

This prevents cascading autonomous repair loops.

---

# 25. Duplicate Remediation Protection

A source effect MUST have at most one admitted remediation under this profile.

The runtime MUST maintain an authoritative registry keyed by at least:

```text
source mission
source closure
source operation
effect identity
```

The registry MUST prevent:

- parallel remediation admissions;
- duplicate remediation claims;
- multiple compensating operations;
- replay after restart;
- alternate document creation for the same effect.

A different `remediation_id` MUST NOT bypass this rule.

---

# 26. Resource Bounds

Remediation has independent resource limits.

Limits MUST include:

```text
deadline_at
max_review_rounds
max_observation_age_seconds
max_dispatch_check_age_seconds
max_execution_attempts
resource_budgets
```

Creating a remediation MUST NOT restore or increase exhausted source budgets unless explicitly authorized by remediation policy.

A new budget is not automatically a new permission.

---

# 27. Deadline and Expiration

Human approval and remediation admission MUST expire.

Execution MUST begin strictly before all relevant deadlines.

At minimum:

```text
execution_start
<
min(
    human_review.valid_until,
    remediation_plan.limits.deadline_at,
    admission.start_before
)
```

Expired approval MUST NOT be revived.

A new approval requires a new plan review.

---

# 28. Compensation Safety

A `compensate` remediation MUST NOT assume that inverse syntax implies inverse real-world effect.

For example:

```text
A = send payment
B = send opposite payment
```

does not prove that B fully restores A.

The system MUST preserve:

- both transactions;
- both identities;
- both timestamps;
- both effects.

Compensation may itself have fees, delays, downstream consequences, or irreversible side effects.

---

# 29. Correction Safety

A `correct` remediation requires an authoritative desired state.

The desired state MUST NOT be invented by an agent merely because it differs from the current state.

The plan MUST establish why the proposed corrective state is valid through:

- policy;
- authoritative configuration;
- approved human instruction;
- trusted system-of-record evidence.

---

# 30. Containment Safety

Containment MUST be explicitly bounded.

A containment action MUST identify:

- what is being contained;
- why;
- scope;
- duration where applicable;
- authority;
- release conditions if relevant.

Containment MUST NOT silently become permanent authority escalation.

---

# 31. Notification Safety

Notification actions MUST respect:

- recipient scope;
- data minimization;
- disclosure authorization;
- confidentiality;
- duplicate-send protection.

An irreversible message send MUST itself pass the normal dispatch controls.

---

# 32. Runtime Enforcement

A deployment claiming v0.4 remediation support MUST maintain runtime enforcement outside agent control.

The enforcement layer MUST:

1. preserve immutable source records;
2. preserve confirmed effects;
3. prevent reuse of the source operation identity;
4. enforce unique remediation claims;
5. prevent concurrent remediations;
6. verify remediation authorization independently;
7. atomically consume admission claims;
8. enforce dispatch count;
9. enforce resource limits;
10. enforce deadlines and revocation;
11. prevent remediation chains;
12. retain complete causal audit history.

An agent's own statement that these properties hold is insufficient.

---

# 33. Trust Boundaries

The agent MAY:

- observe;
- analyze;
- propose remediation;
- request authority;
- generate evidence references;
- prepare a candidate action.

The agent MUST NOT independently:

- authenticate its own human reviewer;
- increase its own authority;
- alter remediation policy;
- declare external evidence authoritative;
- consume its own remediation claim without runtime enforcement;
- erase source effects;
- authorize remediation execution.

---

# 34. Validation Scope

A v0.4 document validator MAY establish:

- JSON validity;
- schema conformance;
- reference consistency;
- record ordering;
- operation ID inequality;
- causal reference presence;
- decision consistency;
- deadline relationships;
- duplicate internal identifiers;
- presence of human review;
- bounded document structure.

Document validation alone cannot establish:

- real human identity;
- external evidence authenticity;
- authorization validity;
- revocation state;
- actual external effect;
- actual compensation;
- target-state truth;
- durable fencing;
- atomic claim uniqueness;
- cross-process replay prevention.

These require external enforcement and evidence systems.

---

# 35. Minimum Conformance Invariants

A conforming v0.4 remediation bundle MUST satisfy at least:

### R1 — Source Immutability

The original mission remains unchanged.

### R2 — Effect Acknowledgement

A confirmed source effect remains recorded.

### R3 — New Operation Identity

The remediation uses a new operation ID.

### R4 — Explicit Causal Link

The remediation explicitly identifies the source operation/effect.

### R5 — Bounded Impact Scope

State-changing remediation requires a bounded effect scope.

### R6 — Human-Reviewed Remediation

The exact remediation proposal receives valid human review.

### R7 — Independent Authorization

Remediation has independent current authority.

### R8 — No Remediation Loop

A remediation mission cannot recursively become another remediation source.

---

# 36. Initial Positive Conformance Fixtures

The initial v0.4 positive fixture set SHOULD include:

```text
examples/v0.4/pass/remediation-compensated.json
examples/v0.4/pass/remediation-contained.json
examples/v0.4/pass/remediation-corrected.json
examples/v0.4/pass/remediation-notified.json
examples/v0.4/pass/remediation-held-impact-unresolved.json
```

---

# 37. Initial Negative Conformance Fixtures

The initial negative set SHOULD include at least:

```text
examples/v0.4/fail/source-rewritten.json
examples/v0.4/fail/same-operation-id.json
examples/v0.4/fail/missing-causal-link.json
examples/v0.4/fail/impact-unresolved-but-executed.json
examples/v0.4/fail/missing-human-review.json
examples/v0.4/fail/expired-human-approval.json
examples/v0.4/fail/source-authorization-reused.json
examples/v0.4/fail/remediation-without-admission.json
examples/v0.4/fail/duplicate-remediation.json
examples/v0.4/fail/remediation-of-remediation.json
```

Additional negative fixtures SHOULD be added whenever a new invariant becomes mechanically testable.

---

# 38. Relationship Between v0.3 and v0.4

The profiles intentionally divide two different post-execution situations.

## v0.3

Use when authoritative reconciliation establishes:

```text
not dispatched
```

or:

```text
dispatched but terminal with no external effect
```

The same logical operation may then receive one bounded successor.

---

## v0.4

Use when:

```text
external effect confirmed
```

or an effect must conservatively be treated as present.

The source operation MUST NOT be retried as though nothing happened.

A new remediation operation is required.

Therefore:

```text
v0.3
unknown/failed
→ prove no effect
→ successor

v0.4
effect exists
→ assess impact
→ remediation
```

The boundary between the two profiles MUST remain explicit.

---

# 39. Safety Property

The principal v0.4 safety property is:

> **A system MUST NOT convert evidence of an already-caused external effect into permission to repeat the original operation.**

The secondary property is:

> **Any corrective action after a confirmed effect is itself a new external action and therefore receives the same bounded control, authorization, review, dispatch, verification, and audit treatment as any other mission.**

---

# 40. Version Boundary

TACP v0.4 intentionally stops after one bounded remediation mission.

Future versions may consider:

- multi-party remediation;
- authorized rollback profiles;
- distributed compensation graphs;
- staged containment and release;
- remediation arbitration;
- cross-system effect attribution;
- financial compensation ledgers;
- remediation handoff between organizations;
- limited remediation chaining under external human governance.

None of those behaviors are implied by v0.4.

---

# 41. Summary

TACP v0.4 extends the protocol from:

```text
Can this action safely execute?
```

and:

```text
Can this unresolved action safely be tried once more?
```

to a third question:

```text
An effect has already happened.
What bounded, independently authorized action may safely be taken next?
```

The answer is not to rewrite history.

The answer is:

```text
Observe the effect
        ↓
Bound its scope
        ↓
Design a new remediation operation
        ↓
Obtain human review
        ↓
Recheck authority and policy
        ↓
Admit exactly one remediation
        ↓
Run a complete TACP mission
        ↓
Verify the new outcome
        ↓
Preserve both histories
```

This preserves the protocol's central principle:

> **Safety does not require pretending that failure or unintended effects never happened. Safety requires making what happened traceable, bounded, reviewable, and recoverable without silently granting new power.**
