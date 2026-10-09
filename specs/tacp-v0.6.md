# Triadic Agent Control Protocol v0.6

## Escalation Handoff and Responsibility Transfer

**Protocol:** Triadic Agent Control Protocol  
**Protocol version:** 0.6.0  
**Status:** Draft — specification  
**Repository-relative path:** `specs/tacp-v0.6.md`

---

# 1. Relationship to Earlier Versions

This document extends `specs/tacp-v0.5.md`, which extends v0.4, v0.3, v0.2, and v0.1.

All normative requirements from earlier versions remain in force unless this specification explicitly changes them.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

TACP v0.6 preserves:

- scout, analyst, gate, and executor separation;
- least-privilege authorization;
- immutable source and remediation history;
- bounded recovery;
- human-reviewed remediation;
- independent post-remediation verification;
- explicit uncertainty;
- prohibition on autonomous remediation-of-remediation chains;
- the rule that escalation does not itself grant authority.

Version 0.6 adds a bounded handoff process for transferring responsibility after a v0.5 terminal escalation.

The central rule is:

> **An escalated TACP path MUST NOT be treated as safely transferred merely because a handoff message was emitted. Responsibility transfer requires an explicit, bound, and independently attributable acceptance receipt from the receiving process or authority.**

If no valid acceptance receipt exists, TACP retains the state `handoff_pending` or terminates as `handoff_unconfirmed`; it MUST NOT silently assume that a human or external system took responsibility.

---

# 2. Scope

TACP v0.6 addresses the condition where:

1. a v0.5 remediation outcome has closed as `escalated`;
2. autonomous remediation has stopped;
3. the case must be transferred to a separately governed human or external process;
4. the transfer itself must be traceable;
5. the receiving party must explicitly accept or reject responsibility;
6. TACP must record where its own autonomous responsibility ends.

Examples include handoff to:

- a human incident-response operator;
- a security operations center;
- a compliance or legal review process;
- an operations team;
- an external safety controller;
- a separately authorized orchestration system;
- a manual recovery procedure.

---

# 3. Non-Goals

The following are outside the v0.6 profile:

- automatic approval of a new corrective action;
- automatic privilege expansion after escalation;
- automatic restart of remediation;
- automatic creation of another remediation chain;
- proving that a human actually solved the incident;
- proving legal or organizational accountability outside recorded receipts;
- assigning moral blame;
- replacing organizational incident-management systems;
- granting authority merely because a receiver acknowledged a message;
- allowing the original TACP executor to self-accept the handoff without independently valid authority.

A receiving process MAY later create a new independently authorized action, but that action is outside the escalated TACP remediation chain unless a later protocol explicitly defines re-entry.

---

# 4. Core Principles

## 4.1 Escalation is not handoff completion

A v0.5 `escalated` closure means only that the current autonomous remediation path has stopped.

It does not prove that:

- a human saw the case;
- an external system accepted the case;
- responsibility moved elsewhere;
- another action is authorized.

---

## 4.2 Emission is not acceptance

A handoff request, notification, ticket creation, email, message, API submission, or queue insertion MUST NOT by itself establish responsibility transfer.

The receiving side MUST produce an explicit acceptance or rejection record bound to the exact handoff request.

---

## 4.3 Acceptance does not grant execution authority

A receiving party may accept responsibility for review without holding authority to execute a corrective action.

Therefore:

```text
handoff_acceptance != execution_authorization
```

Any later action MUST be authorized independently under the receiving process's authority model.

---

## 4.4 Responsibility transfer must be attributable

A handoff acceptance MUST identify:

- who or what accepted responsibility;
- which authority context applies;
- which escalation is being accepted;
- when acceptance occurred;
- the accepted scope;
- unresolved constraints or exclusions.

Anonymous or unbound acceptance MUST NOT complete the handoff.

---

## 4.5 No silent abandonment

If no valid receiver accepts responsibility before the handoff deadline, the system MUST NOT mark the case as transferred.

The result MUST remain explicit, such as:

```text
handoff_pending
handoff_rejected
handoff_unconfirmed
```

A timeout is not acceptance.

---

## 4.6 Transfer ends the current autonomous path

Once a valid handoff is accepted, TACP records that the escalated path has been transferred to an external responsibility domain.

The original autonomous TACP path MUST remain stopped.

A valid handoff receipt MUST NOT reactivate the executor, remediation, recovery, or source operation.

---

# 5. Native v0.6 Document Form

The v0.6-native document form is:

```text
escalation_handoff_bundle
```

Earlier `mission_bundle`, `recovery_bundle`, `remediation_bundle`, and `remediation_outcome_bundle` documents remain governed by their respective inherited profiles.

All v0.6-native records and bundles MUST declare:

```json
"protocol_version": "0.6.0"
```

The v0.6 native schema, when added, SHOULD validate `escalation_handoff_bundle` only rather than duplicating prior-version schemas.

---

# 6. Escalation Handoff Bundle

An `escalation_handoff_bundle` binds exactly one terminal v0.5 escalation to one bounded handoff process.

It MUST contain:

| Field | Requirement |
|---|---|
| `protocol_version` | MUST equal `0.6.0` |
| `document_type` | MUST equal `escalation_handoff_bundle` |
| `handoff_id` | Unique handoff identifier |
| `escalation_ref` | Exact v0.5 escalated closure or outcome being transferred |
| `remediation_ref` | Exact remediation associated with the escalation |
| `remediation_operation_id` | Exact remediation operation identity |
| `handoff_limits` | Finite handoff limits |
| `records` | Ordered v0.6 handoff records |
| `extensions` | Optional non-authoritative object |

The bundle MUST NOT contain a new remediation mission or new execution authorization.

---

# 7. Record Cardinality and Ordering

A valid v0.6 handoff path contains:

```text
exactly 1 handoff_request
0..N handoff_delivery_observation
exactly 1 handoff_disposition
exactly 1 handoff_closure
```

All delivery observations MUST occur after the request and before the disposition.

The disposition MUST precede closure.

The closure MUST be the final v0.6 record.

---

# 8. Handoff Request

A `handoff_request` records the bounded request to transfer responsibility.

It MUST contain at least:

- `record_id`;
- `handoff_id`;
- `escalation_ref`;
- `remediation_ref`;
- `remediation_operation_id`;
- `created_at`;
- `producer_id`;
- `producer_role` equal to `controller`;
- `receiver_ref`;
- `requested_scope`;
- `reason_codes`;
- `basis_refs`;
- `requested_by_authority_ref`;
- `deadline`;
- `reason`.

The request MUST NOT include or imply automatic execution permission.

The request MUST identify only the scope being transferred for review or responsibility handling.

---

# 9. Handoff Delivery Observation

A `handoff_delivery_observation` records evidence concerning delivery or visibility of the handoff request.

It MAY record:

- queue insertion;
- ticket creation;
- message delivery;
- acknowledgement transport;
- receiver availability;
- delivery failure;
- conflicting delivery state.

It MUST NOT itself establish responsibility transfer.

A delivery observation MUST distinguish transport acknowledgement from responsibility acceptance.

---

# 10. Handoff Disposition

A `handoff_disposition` records the receiving side's explicit decision regarding responsibility transfer.

Its `result` MUST be exactly one of:

```text
accepted
rejected
unconfirmed
timeout
```

## 10.1 `accepted`

Use only when a receiver produces an explicit acceptance bound to the exact handoff request.

An accepted disposition MUST identify:

- `receiver_id`;
- `receiver_type`;
- `receiver_authority_ref`;
- `accepted_scope`;
- `accepted_at`;
- `acceptance_evidence_refs`;
- `remaining_constraints`;
- `reason`.

The accepted scope MUST NOT exceed the requested scope.

The receiving authority reference MUST be independently attributable and MUST NOT be self-created by the original TACP executor merely to satisfy the handoff.

## 10.2 `rejected`

Use when the intended receiver explicitly refuses responsibility.

A rejection MUST preserve the refusal reason and evidence.

Rejection MUST NOT trigger automatic reassignment to a more privileged receiver.

## 10.3 `unconfirmed`

Use when delivery may have occurred but no authoritative acceptance or rejection can be established.

Transport-level acknowledgements alone belong here rather than under `accepted`.

## 10.4 `timeout`

Use when the handoff deadline expires without valid acceptance or rejection.

Timeout MUST NOT be interpreted as implicit acceptance.

---

# 11. Handoff Closure

A `handoff_closure` terminates the v0.6 handoff path.

Its `status` MUST be exactly one of:

```text
transferred
not_transferred
```

`transferred` is permitted only when the disposition result is:

```text
accepted
```

All of the following MUST close as `not_transferred`:

```text
rejected
unconfirmed
timeout
```

A transferred closure MUST record:

- `responsibility_transferred: true`;
- `receiver_ref`;
- `receiver_authority_ref`;
- `accepted_scope`;
- `basis_refs`;
- `prohibited_automatic_actions`;
- `reason`.

A non-transferred closure MUST record:

- `responsibility_transferred: false`;
- `basis_refs`;
- `remaining_responsibility_state`;
- `prohibited_automatic_actions`;
- `reason`.

---

# 12. Mandatory Prohibitions

Every v0.6 closure MUST preserve at least these automatic-action prohibitions:

```text
restart_source_operation
restart_remediation_operation
create_remediation_of_remediation
self_expand_authority
self_accept_handoff
assume_acceptance_from_delivery
```

An implementation MAY add stricter prohibitions.

These prohibitions remain in force whether the handoff is transferred or not transferred.

---

# 13. Handoff Limits

Every handoff process MUST declare finite limits for:

- final handoff deadline;
- permitted receiver set or receiver scope;
- maximum delivery-observation count;
- evidence retrieval budget;
- maximum acceptance age if acceptance evidence is time-sensitive.

The protocol MUST NOT autonomously extend these limits.

Exhaustion MUST result in an explicit non-transfer state rather than silent continuation.

---

# 14. Identity and Binding

Every v0.6 record MUST bind the same:

```text
handoff_id
escalation_ref
remediation_ref
remediation_operation_id
```

The handoff request, disposition, and closure MUST reference each other exactly.

An acceptance for another incident, another escalation, or another remediation MUST NOT satisfy the current handoff.

---

# 15. Authority Boundary

The receiving authority domain is separate from the escalated TACP remediation path.

Therefore:

```text
receiver_acceptance
    != TACP execution authorization

responsibility_transfer
    != permission to resume autonomous remediation
```

The original TACP executor MUST NOT manufacture the receiving authority reference.

The controller MUST NOT treat identity alone as sufficient proof of authority.

A deployment MUST validate receiver authority outside prompt-only reasoning.

---

# 16. Immutability

v0.6 MUST NOT rewrite:

- source mission history;
- source execution history;
- recovery history;
- remediation history;
- v0.5 post-remediation observations;
- v0.5 verification result;
- v0.5 escalated closure.

The handoff process is additive.

Acceptance does not erase the fact that escalation occurred.

---

# 17. Required Positive Cases

A v0.6 conformance suite SHOULD include at least:

1. `accepted-human-handoff-transferred`
2. `accepted-external-process-transferred`
3. `receiver-rejected-not-transferred`
4. `delivery-unconfirmed-not-transferred`
5. `handoff-timeout-not-transferred`

---

# 18. Required Negative Cases

A v0.6 conformance suite SHOULD reject at least:

1. `delivery-treated-as-acceptance`
2. `missing-acceptance-receipt`
3. `acceptance-wrong-escalation-ref`
4. `acceptance-wrong-remediation-operation-id`
5. `accepted-scope-exceeds-request`
6. `self-issued-receiver-authority`
7. `executor-self-accepts-handoff`
8. `transferred-after-rejection`
9. `transferred-after-timeout`
10. `closure-before-disposition`
11. `second-remediation-created-after-handoff`
12. `authority-expanded-during-handoff`
13. `receiver-outside-declared-scope`
14. `handoff-after-deadline-marked-accepted`
15. `acceptance-evidence-stale`
16. `handoff-history-rewritten`

---

# 19. Runtime Boundary

Document validation can establish only recorded structure and semantic consistency.

It cannot independently prove:

- that the receiver is a real human or external system;
- that the receiver actually saw the incident;
- that the receiver identity is authentic;
- that the receiver truly has the claimed authority;
- that the external organization accepted legal responsibility;
- that no hidden remediation was restarted elsewhere;
- that runtime permissions remained fenced;
- that the accepted case was later resolved;
- that notification infrastructure is trustworthy.

Those properties require external identity, authorization, messaging, incident-management, and runtime enforcement systems.

---

# 20. v0.6 Core Invariants

A conforming v0.6 implementation MUST preserve:

```text
escalation != handoff_completion

delivery != acceptance

acceptance != execution_authorization

accepted_scope <= requested_scope

handoff_timeout != implicit_acceptance

transferred
    requires explicit attributable acceptance

handoff
    MUST NOT restart autonomous remediation

source_history
    remains immutable

remediation_history
    remains immutable

v0.5 escalation_history
    remains immutable
```

---

# 21. Minimal State Transition

```text
V0_5_ESCALATED
    |
    v
HANDOFF_REQUESTED
    |
    +--> delivery observations (bounded)
    |
    v
HANDOFF_DISPOSITION
    |
    +--> accepted -----> TRANSFERRED
    |
    +--> rejected -----+
    +--> unconfirmed --+--> NOT_TRANSFERRED
    +--> timeout ------+

TRANSFERRED
    |
    +--> TACP autonomous remediation remains stopped

NOT_TRANSFERRED
    |
    +--> no silent abandonment
    +--> no autonomous privilege escalation
    +--> no automatic remediation restart
```

---

# 22. First Complete Cycle Boundary

v0.6 is intended to close the first complete TACP control cycle:

```text
Plan
-> Authorize
-> Execute
-> Verify
-> Recover
-> Remediate
-> Verify remediation
-> Escalate
-> Handoff
```

After v0.6, the protocol SHOULD enter a feature-freeze and architecture-review phase before adding further capabilities.

That review SHOULD focus on:

- cross-version invariants;
- conformance matrices;
- threat modeling;
- authority boundary consistency;
- implementation guidance;
- external protocol mappings;
- conditions required for a future v1.0 candidate.

---

# 23. Summary

TACP v0.5 answers:

> **How does the system verify whether remediation worked, and how does it stop safely when it did not?**

TACP v0.6 answers:

> **After the autonomous path stops, how is responsibility transferred without pretending that sending a message means someone actually accepted the case?**

The core design rule is simple:

> **Stop first. Transfer explicitly. Require acceptance. Never confuse acknowledgement with authority.**
