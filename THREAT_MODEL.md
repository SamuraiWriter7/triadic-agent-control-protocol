# TACP Threat Model

**Baseline:** TACP v0.1.0-v0.6.0  
**Status:** architecture-review artifact / feature-freeze phase  
**Purpose:** identify structural failure and abuse modes that TACP is intended to constrain.  
**Non-claim:** this document does not certify production security, identity authenticity, evidence truth, or runtime enforcement.

## 1. Threat-model objective

TACP is not based on the assumption that malicious intent can always be identified correctly.

Instead, the protocol is designed around a narrower and more testable objective:

> Prevent error, ambiguity, misuse, or malicious intent from being amplified into broader authority, repeated execution, erased history, uncontrolled remediation, or false responsibility transfer.

The primary attack surface is therefore not only an individual model or user. It is the set of transitions where one stage could improperly manufacture the conditions needed to legitimize the next stage.

The central threat-model invariant is:

> **No stage may manufacture the authority, evidence, or responsibility transfer required to legitimize its own next stage.**

## 2. Threat classes

This review defines ten primary structural threat classes.

1. Authority forgery
2. Scope creep
3. Stale authorization
4. Evidence laundering
5. Hidden repetition
6. History rewriting
7. Remediation chaining
8. Self-acceptance
9. Silent abandonment
10. Privilege resurrection

These classes may arise from malicious behavior, implementation defects, race conditions, stale state, operator error, or model overreach.

## 3. Threat-model layers

Threat detection and prevention operate across five layers.

| Layer | Meaning | Example |
| --- | --- | --- |
| S | Schema | required fields, enums, structural shape |
| M | Semantic validation | cross-record identity, chronology, scope, deadline, closure rules |
| H | Harness / synthetic runtime | registered runtime-state scenarios that cannot be proven from a static document alone |
| R | External runtime enforcement | privilege isolation, immutable stores, authority registry, dispatch controls |
| T | Trust / provenance | evidence authenticity, identity authenticity, organizational authority, cryptographic provenance |

A threat may be partially detectable at S/M/H while still requiring R/T for actual prevention.

## 4. Threat 1 — Authority forgery

### Attack structure

An agent, controller, executor, or receiving process claims authority that was never independently granted.

Examples include:

- fabricating an authorization reference,
- inventing a receiver authority,
- reusing expired authorization,
- treating recommendation as permission,
- or self-signing the permission required to continue.

### Primary affected stages

v0.1, v0.2, v0.4, v0.5, v0.6.

### TACP defenses

- recommendation and authorization are structurally separate,
- remediation requires independent authorization,
- self-expansion of authority is prohibited,
- v0.6 receiver authority must be independently attributable,
- acceptance is not execution authorization.

### Detectable at

- S: presence and shape of authority references,
- M: consistency and forbidden self-issued patterns in registered fixtures,
- H: authority expansion runtime scenarios,
- R/T: actual authority provenance and authenticity.

### Residual risk

A syntactically valid authority reference may still point to a forged, compromised, stale, or incorrectly configured external authority source.

## 5. Threat 2 — Scope creep

### Attack structure

A validly admitted action expands beyond the approved target, receiver, resource, or capability boundary.

Examples include:

- widening an operation target,
- adding undeclared capabilities,
- accepting a broader handoff scope than requested,
- routing to an unapproved receiver,
- or allowing remediation to affect unrelated state.

### Primary affected stages

v0.1, v0.2, v0.4, v0.6.

### TACP defenses

- operation binding,
- execution-time scope checks,
- explicit remediation target/scope,
- `accepted_scope <= requested_scope`,
- permitted receiver sets,
- bounded resource and evidence limits.

### Detectable at

S/M for declared scope relationships; R for actual tool and resource access.

### Residual risk

A runtime tool may interpret a narrow declared scope more broadly than the protocol record indicates.

## 6. Threat 3 — Stale authorization

### Attack structure

An authorization or acceptance that was once valid is used after the relevant state, deadline, policy, or freshness condition has changed.

Examples include:

- dispatch after authorization expiry,
- execution after target state changes,
- remediation after human approval expiry,
- handoff acceptance after the deadline,
- or reliance on stale acceptance evidence.

### Primary affected stages

v0.2, v0.4, v0.5, v0.6.

### TACP defenses

- execution-time authorization checks,
- explicit deadlines,
- freshness windows,
- approval expiry,
- final verification deadlines,
- `max_acceptance_age_seconds`,
- no silent deadline extension.

### Detectable at

M for recorded timestamps and declared windows; R/T for trustworthy clocks and authoritative revocation state.

### Residual risk

Clock skew, delayed revocation propagation, or a compromised time source can produce apparently valid but operationally stale records.

## 7. Threat 4 — Evidence laundering

### Attack structure

A non-independent signal is presented as if it independently proved success, safety, acceptance, or external effect.

Examples include:

- executor success treated as external verification,
- delivery receipt treated as receiver acceptance,
- transport acknowledgement treated as responsibility transfer,
- reused evidence counted as independent evidence,
- or self-generated statements presented as external observation.

### Primary affected stages

v0.1, v0.5, v0.6.

### TACP defenses

- outcome verification is distinct from execution success,
- post-remediation observation is independent,
- delivery evidence cannot serve as the sole acceptance receipt,
- evidence budgets and uniqueness rules,
- explicit uncertainty when evidence is insufficient.

### Detectable at

M for reference reuse and prohibited evidence relationships; T for actual evidence-source independence.

### Residual risk

Two apparently distinct evidence references may still originate from the same compromised underlying source.

## 8. Threat 5 — Hidden repetition

### Attack structure

An operation that failed, produced uncertain effects, or was intentionally stopped is silently retried under the same or slightly changed identity.

Examples include:

- automatic retry after uncertain execution,
- duplicate remediation,
- second remediation after escalation or handoff,
- or replay of a prior source action.

### Primary affected stages

v0.3, v0.4, v0.5, v0.6.

### TACP defenses

- recovery is not blind retry,
- successor paths require fresh checks,
- remediation receives a new identity,
- duplicate remediation protection,
- escalation prohibits source/remediation repetition,
- handoff keeps the original autonomous path stopped.

### Detectable at

M for visible identity reuse; H/R for hidden runtime retries and distributed duplicates.

### Residual risk

Concurrent or distributed executors may repeat effects outside the local trace unless runtime claim consumption and deduplication are atomic.

## 9. Threat 6 — History rewriting

### Attack structure

A later stage mutates prior records to make the current state appear cleaner, safer, or more authorized than it really was.

Examples include:

- deleting a harmful source effect,
- changing a prior remediation result,
- rewriting a handoff disposition after closure,
- or altering timestamps to fit a deadline.

### Primary affected stages

v0.4, v0.5, v0.6.

### TACP defenses

- prior effects remain part of source history,
- remediation does not erase the source action,
- later stages bind to immutable prior references,
- registered synthetic history-rewrite negative.

### Detectable at

H for modeled rewrite attempts; R/T for immutable storage, append-only logs, signatures, or hash-linked records.

### Residual risk

A single static bundle cannot prove that a backing store was never mutated before the bundle was exported.

## 10. Threat 7 — Remediation chaining

### Attack structure

A corrective action fails and automatically creates another corrective action, which may fail again, creating an unbounded autonomous chain.

### Primary affected stages

v0.4, v0.5, v0.6.

### TACP defenses

- remediation is a separately authorized operation,
- remediation-of-remediation is prohibited,
- partial/ineffective/harmful/unresolved results escalate,
- v0.6 transfers responsibility instead of restarting autonomous correction.

### Detectable at

M/H for declared or synthetic chained remediation; R for hidden runtime creation of corrective operations.

### Residual risk

An external orchestration layer outside TACP may create a new corrective operation unless the deployment enforces the same authority boundary.

## 11. Threat 8 — Self-acceptance

### Attack structure

The originating TACP path pretends to be the external receiver or manufactures the acceptance needed to claim that responsibility was transferred.

### Primary affected stage

v0.6.

### TACP defenses

- receiver identity and authority are explicit,
- acceptance evidence is required,
- original executor self-acceptance is forbidden,
- receiver authority must be independently attributable,
- delivery does not imply acceptance.

### Detectable at

M for registered self-acceptance patterns; R/T for real identity and authority separation.

### Residual risk

A compromised identity provider or shared administrative account may make a self-acceptance event appear externally attributable.

## 12. Threat 9 — Silent abandonment

### Attack structure

An escalation is emitted and the system behaves as if someone else took responsibility even though no authoritative receiver accepted it.

### Primary affected stage

v0.6.

### TACP defenses

- `delivery != acceptance`,
- `acceptance != execution_authorization`,
- rejected/unconfirmed/timeout close as `not_transferred`,
- remaining responsibility state must remain explicit,
- timeout never becomes implicit acceptance.

### Detectable at

M for missing or inconsistent acceptance; R for whether the intended external process actually received, acknowledged, and assumed operational responsibility.

### Residual risk

A valid acceptance record cannot by itself prove that the receiver is operationally capable of acting on the incident.

## 13. Threat 10 — Privilege resurrection

### Attack structure

A path that was stopped, constrained, escalated, or transferred silently regains authority later.

Examples include:

- recovery reactivating original privileges,
- failed remediation expanding authority,
- handoff causing the original controller to regain remediation permission,
- or a receiver acceptance being interpreted as permission for the original executor to resume.

### Primary affected stages

v0.3-v0.6.

### TACP defenses

- explicit prohibition of self-expansion,
- fresh authorization for successors,
- mandatory post-escalation prohibitions,
- acceptance is not execution authorization,
- handoff does not restart source/remediation operations.

### Detectable at

H for modeled authority expansion; R for actual privilege-state enforcement.

### Residual risk

A deployment may record the correct prohibition while still failing to revoke credentials or runtime capabilities.

## 14. Cross-threat interaction patterns

The most dangerous failures are combinations rather than isolated violations.

### 14.1 Forgery + scope creep

A forged authority token is used to approve a broader scope than originally intended.

### 14.2 Stale authorization + hidden repetition

An expired authorization is replayed to retry an uncertain action.

### 14.3 Evidence laundering + silent abandonment

A transport receipt is treated as acceptance so responsibility appears transferred when nobody actually accepted it.

### 14.4 History rewriting + remediation chaining

A failed remediation is rewritten as clean enough to justify another autonomous corrective action.

### 14.5 Privilege resurrection + self-acceptance

The original path creates a fake receiving authority and uses that handoff as a reason to restore its own privileges.

TACP's strongest protection comes from making these transitions independently attributable and explicitly bound rather than relying on intent classification.

## 15. What TACP does not attempt to solve alone

TACP does not by itself provide:

- cryptographic identity infrastructure,
- authoritative human identity proof,
- trusted timestamping,
- immutable database guarantees,
- network delivery guarantees,
- legal assignment of responsibility,
- secure credential revocation,
- race-free distributed locks,
- complete provenance attestation,
- or proof that an external system truthfully reported its state.

Those belong to surrounding runtime, security, organizational, or legal systems.

## 16. Required external controls for serious deployment

A deployment that relies on TACP for meaningful external actions should consider pairing the protocol with:

1. independently governed authorization services,
2. signed or otherwise attributable receipts,
3. immutable or append-only audit storage,
4. trusted clock and revocation sources,
5. least-privilege execution credentials,
6. atomic duplicate-prevention or idempotency controls,
7. explicit credential revocation after escalation/handoff,
8. receiver identity and authority registries,
9. monitoring for unrecorded tool execution,
10. and integration tests that verify real enforcement rather than document consistency alone.

## 17. Threat-to-version summary

| Threat | v0.1 | v0.2 | v0.3 | v0.4 | v0.5 | v0.6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Authority forgery | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Scope creep | ✓ | ✓ |  | ✓ |  | ✓ |
| Stale authorization |  | ✓ |  | ✓ | ✓ | ✓ |
| Evidence laundering | ✓ |  |  |  | ✓ | ✓ |
| Hidden repetition |  |  | ✓ | ✓ | ✓ | ✓ |
| History rewriting |  |  |  | ✓ | ✓ | ✓ |
| Remediation chaining |  |  |  | ✓ | ✓ | ✓ |
| Self-acceptance |  |  |  |  |  | ✓ |
| Silent abandonment |  |  |  |  |  | ✓ |
| Privilege resurrection |  |  | ✓ | ✓ | ✓ | ✓ |

## 18. Residual-risk rule

A TACP PASS should always be interpreted as:

> The registered document, semantic, and synthetic checks behaved as expected for the tested cases.

It should never be interpreted as:

> The deployment is secure, the evidence is true, the authority is genuine, or the external world behaved as recorded.

The latter claims require runtime and trust-layer evidence.

## 19. Review conclusion

TACP's threat model is intentionally structural.

It does not depend on perfectly identifying whether a human or AI is malicious. Instead, it attempts to make high-impact transitions difficult to legitimize without independent authority, fresh evidence, bounded scope, preserved history, and attributable responsibility transfer.

The defining security principle is therefore:

> **Do not try to prove that every actor is good. Prevent any one actor or stage from unilaterally creating the authority, evidence, or transfer state needed to amplify its own power.**
