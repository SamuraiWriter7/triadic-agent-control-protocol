# TACP Conformance Matrix

**Baseline:** v0.1.0-v0.6.0  
**Purpose:** map architectural invariants to specification stages, validator coverage, fixtures, and external runtime requirements.  
**Status:** architecture-review artifact; this document does not expand protocol autonomy.

## 1. Interpretation

This matrix answers four questions for each major TACP invariant:

1. Where is the invariant introduced or relied upon?
2. What can the repository's current validators check?
3. Which registered fixtures exercise the invariant?
4. Which part still depends on external runtime, security, identity, or authority enforcement?

A validator PASS means only that the encoded schema, semantic rules, and registered synthetic runtime expectations behaved as expected. It is not proof that a deployment enforces the same property in reality.

## 2. Cross-version invariant matrix

| ID | Architectural invariant | Primary versions | Repository-verifiable rule | Representative fixtures / checks | External runtime requirement |
| --- | --- | --- | --- | --- | --- |
| I-01 | Recommendation is not authorization | v0.1-v0.6 | planning, review, acceptance, or escalation records cannot substitute for required authority references or gate decisions | v0.1 gate/authorization cases; v0.4 independent remediation authorization; v0.6 accepted handoff cases | authority source must be genuine, independent, current, and actually enforced outside model reasoning |
| I-02 | Authority cannot be self-expanded | v0.1-v0.6 | declared authority changes that contradict bounded scope can be rejected; registered runtime fixtures encode post-failure/handoff self-expansion as nonconformant | v0.5 `authority-expanded-after-failure.json`; v0.6 `authority-expanded-during-handoff.json` | runtime privilege system must prevent hidden capability gain even when no compliant record is emitted |
| I-03 | Execution remains bound to admitted operation | v0.1-v0.4 | operation identity, target, scope, authorization and timing references must remain consistent across records | v0.2 execution-time authorization cases; v0.4 reused-operation and source-authorization-reuse negatives | executor sandbox / tool layer must enforce actual target, scope, identity and permission at dispatch time |
| I-04 | Execution success is not outcome verification | v0.1, v0.5 | completion requires verification records and permitted result-to-closure mapping rather than executor success alone | v0.1 outcome-verification cases; v0.5 executor-success-without-independent-observation negative | observation source must be independent enough to establish actual external state |
| I-05 | Uncertainty must remain explicit | v0.1-v0.6 | unknown / unresolved states cannot silently map to approval, completed remediation, accepted handoff, or transfer | v0.3 uncertain recovery cases; v0.5 `unresolved` escalation cases; v0.6 unconfirmed handoff positive | external systems must not coerce unknown state into success outside recorded protocol logic |
| I-06 | History is append-only in meaning | v0.3-v0.6 | identifiers and references preserve prior source/remediation/escalation history; registered runtime rewrite attempts are nonconformant | v0.5 new-effect/history-related checks; v0.6 `handoff-history-rewritten.json` | immutable / tamper-evident backing storage is required to prove records were not rewritten after issuance |
| I-07 | Recovery is not blind retry | v0.3 | recovery paths require bounded successor handling and fresh conditions rather than silent repetition of the source operation | v0.3 recovery pass/fail suite, including held/no-effect/uncertain successor handling | distributed runtime must prevent an unrecorded duplicate source execution or race-condition retry |
| I-08 | Remediation is a new operation | v0.4-v0.5 | remediation requires a new operation identity, causal linkage, review, authorization and admission | v0.4 reused-operation-id, source-authorization-reuse, missing causal link, missing review negatives | actual remediation executor must enforce the separately authorized operation rather than reusing source privileges |
| I-09 | Failed remediation terminates autonomous remediation chaining | v0.5-v0.6 | partial, ineffective, harmful and unresolved outcomes must escalate; mandatory prohibitions block autonomous second remediation | v0.5 `second-remediation-created.json`; v0.6 `second-remediation-created-after-handoff.json` | runtime policy / executor isolation must actually fence the original autonomous path after escalation |
| I-10 | Escalation does not itself grant new authority | v0.5-v0.6 | escalated closure contains prohibitions and does not authorize new execution; v0.6 acceptance is separately modeled | v0.5 escalation closures; v0.6 accepted handoff positives | downstream incident-response or governance system must perform its own authorization for later state-changing action |
| I-11 | Delivery is not acceptance | v0.6 | delivery observation evidence cannot serve as sole acceptance receipt; unconfirmed delivery closes not-transferred | `delivery-treated-as-acceptance.json`; `delivery-unconfirmed-not-transferred.json` | receiving system must generate authoritative acceptance independently of transport acknowledgement |
| I-12 | Handoff requires attributable acceptance | v0.6 | `transferred` requires accepted disposition, bound receiver, scope, authority, fresh acceptance, and evidence refs | `accepted-human-handoff-transferred.json`; `accepted-external-process-transferred.json`; missing/wrong/stale acceptance negatives | receiver identity, authority and acceptance evidence must be genuine and externally verifiable |
| I-13 | Accepted scope cannot exceed requested scope | v0.6 | `accepted_scope` must be a subset of `requested_scope` | `accepted-scope-exceeds-request.json` | external receiver must also enforce the accepted scope when acting later |
| I-14 | Receiver must be within declared handoff boundary | v0.6 | request, delivery, disposition and closure receiver refs must remain within permitted receiver refs and bind consistently | `receiver-outside-declared-scope.json` | registry / routing layer must authenticate the actual endpoint and prevent receiver substitution |
| I-15 | Acceptance is not execution authorization | v0.6 | handoff acceptance/transfer records never create an execution authorization for either original or receiving path | accepted handoff positives; mandatory closure prohibitions | downstream execution must pass through a separate authority model before any state-changing action |
| I-16 | Deadlines and freshness cannot be silently ignored | v0.2-v0.6 | timestamp ordering, final deadlines, freshness/age limits, and expiry relationships are semantically checked where encoded | v0.2 expiry/deadline cases; v0.5 stale observation cases; v0.6 late/stale acceptance negatives | trusted time source and runtime enforcement are required to prevent backdating or clock manipulation |
| I-17 | Evidence references are not evidence authenticity | v0.1-v0.6 | validators can require presence, uniqueness, count and reference consistency, but not truth | v0.5 evidence-budget negative; v0.6 evidence-budget and acceptance-evidence checks | signed receipts, trusted provenance, tamper evidence, source authentication and content validation are external requirements |
| I-18 | Safe denial is distinct from protocol invalidity | v0.1-v0.6 | a conformant document may deny/hold execution without itself being invalid | registered positive safe-denial / held cases across versions | deployment reporting must preserve this distinction rather than treating every denial as system failure |

## 3. Version-to-validator matrix

| Version | Primary validator path | Main conformance focus | Runtime-only or synthetic boundary |
| --- | --- | --- | --- |
| v0.1.0 | `scripts/validate_legacy.py` via `scripts/validate.py` | mission structure, observation, challenge review, independent gate, execution, outcome verification | real authority, real execution isolation, evidence authenticity |
| v0.2.0 | `scripts/validate_legacy.py` via `scripts/validate.py` | execution-time authorization, held/expired/revoked states, deadlines, resource limits | real-time authority registry, actual revocation enforcement, trusted clock |
| v0.3.0 | `scripts/validate_legacy.py` via `scripts/validate.py` | bounded recovery, fresh successor handling, non-dispatch/no-effect/uncertain paths | hidden duplicate execution, distributed state races, authoritative external state |
| v0.4.0 | v0.4 semantic path through `scripts/validate.py` | separately identified, reviewed, authorized remediation after confirmed effect | real reviewer identity, real authorization, cross-process duplicate remediation prevention |
| v0.5.0 | `scripts/validate_v05.py` + `scripts/validate_v05_examples.py` | independent post-remediation observation, result classification, escalation, anti-chaining | hidden second remediation, hidden authority expansion, contradictory external execution, omitted real effects |
| v0.6.0 | `scripts/validate_v06.py` + `scripts/validate_v06_examples.py` | responsibility handoff, acceptance binding, scope containment, transfer closure, anti-restart | hidden authority expansion, post-handoff second remediation, backing-store history rewrite, genuine receiver identity/authority |

## 4. v0.6 registered fixture coverage

The v0.6 suite contains 5 positive and 16 negative fixtures, with 3 negatives explicitly treated as synthetic runtime cases.

### Positive cases

| Fixture | Main invariant exercised |
| --- | --- |
| `accepted-human-handoff-transferred.json` | explicit human acceptance can establish transfer when receiver, scope, authority and evidence are bound |
| `accepted-external-process-transferred.json` | independently governed external process may accept responsibility without granting execution authority |
| `receiver-rejected-not-transferred.json` | explicit rejection remains not-transferred |
| `delivery-unconfirmed-not-transferred.json` | delivery without authoritative acceptance remains not-transferred |
| `handoff-timeout-not-transferred.json` | silence / timeout never becomes implicit acceptance |

### Negative cases

| Fixture | Expected invariant / diagnostic |
| --- | --- |
| `delivery-treated-as-acceptance.json` | `delivery_as_acceptance` |
| `missing-acceptance-receipt.json` | `acceptance_receipt_missing` |
| `acceptance-wrong-escalation-ref.json` | `escalation_ref_mismatch` |
| `acceptance-wrong-remediation-operation-id.json` | `remediation_operation_id_mismatch` |
| `accepted-scope-exceeds-request.json` | `accepted_scope_exceeds_request` |
| `self-issued-receiver-authority.json` | `receiver_authority_self_issued` |
| `executor-self-accepts-handoff.json` | `executor_self_acceptance` |
| `transferred-after-rejection.json` | `transferred_after_rejection` |
| `transferred-after-timeout.json` | `transferred_after_timeout` |
| `closure-before-disposition.json` | `closure_before_disposition` |
| `second-remediation-created-after-handoff.json` | `second_remediation_created_after_handoff` — synthetic runtime |
| `authority-expanded-during-handoff.json` | `authority_expanded_during_handoff` — synthetic runtime |
| `receiver-outside-declared-scope.json` | `receiver_outside_declared_scope` |
| `handoff-after-deadline-marked-accepted.json` | `handoff_after_deadline_marked_accepted` |
| `acceptance-evidence-stale.json` | `acceptance_evidence_stale` |
| `handoff-history-rewritten.json` | `handoff_history_rewritten` — synthetic runtime |

## 5. Assurance classes

To avoid overstating conformance, every important rule should be understood as belonging to one or more assurance classes.

| Class | Meaning | Typical examples |
| --- | --- | --- |
| S — Schema | structural shape can be validated from one document | required fields, enums, timestamp format, array cardinality bounds |
| M — Semantic | relationships within the supplied record set can be checked | identity binding, chronology, scope containment, result-to-closure mapping |
| H — Harness / synthetic runtime | the repository can encode and test an intended runtime invariant using synthetic events | hidden second remediation, authority expansion, history rewrite attempt |
| R — External runtime | only deployment infrastructure can establish the property | actual privilege isolation, real authority, real delivery, race-free duplicate prevention |
| T — Trust / provenance | requires trusted identity, signing, attestation or provenance infrastructure | evidence authenticity, human identity, authority registry validity, signed acceptance receipt |

A v1.0 conformance claim should state which assurance classes are covered instead of using a single undifferentiated word such as “safe”.

## 6. Coverage gaps that must remain explicit

The current matrix deliberately leaves the following as external rather than pretending that a JSON validator can prove them:

- genuine human or organization identity,
- cryptographic authenticity of evidence,
- actual external side effects,
- real execution-gate isolation,
- atomic and race-free distributed claim consumption,
- hidden duplicate actions outside the trace,
- truthful delivery to a receiver,
- genuine receiver understanding or organizational assumption of responsibility,
- enforcement of downstream accepted scope,
- immutable persistence of prior records,
- and legal or organizational transfer of responsibility.

These are not necessarily defects in TACP. They define the point at which the protocol must connect to external security, identity, authorization, storage, transport, and governance systems.

## 7. v1.0 use of this matrix

Before a v1.0 candidate, every normative invariant should satisfy at least one of the following:

1. it is machine-checked by schema or semantic validation;
2. it has a registered synthetic harness case when only a runtime scenario can express the intended violation; or
3. it is explicitly marked as an external runtime / trust requirement with no claim that repository validation proves it.

No normative invariant should remain in an ambiguous state where the specification implies enforcement but the repository neither validates it nor declares it external.

## 8. Matrix conclusion

The first complete TACP cycle is strongest when its claims are layered rather than absolute:

```text
Document shape
→ Semantic consistency
→ Synthetic runtime invariant
→ External runtime enforcement
→ Trusted identity / provenance
```

The architecture should therefore preserve the following rule through v1.0:

> A conformance document may prove that a claimed transition is internally well-formed, but it must not pretend to prove external authority, evidence truth, or responsibility transfer unless those properties are independently established by the systems that own them.
