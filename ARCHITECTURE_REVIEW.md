# TACP Architecture Review

**Review baseline:** v0.1.0-v0.6.0  
**Review status:** First Complete Cycle / feature freeze baseline  
**Validation baseline:** registered suites through v0.6.0 passed GitHub Actions on Python 3.10 and 3.12.  
**Interpretation:** this review evaluates the protocol architecture and encoded conformance model. It does not certify production deployment safety.

## 1. Purpose of this review

TACP reached a first complete control cycle at v0.6.0:

```text
Plan
→ Authorize
→ Execute
→ Verify
→ Recover
→ Remediate
→ Verify Remediation
→ Escalate
→ Handoff
```

The purpose of this document is not to add new autonomous capability. It freezes the current cycle long enough to examine whether the architecture remains coherent across versions.

The review therefore asks six questions:

1. Which invariants must remain true across every version?
2. Where does responsibility move from one stage to another?
3. Which authority boundaries are structural and must never be inferred from model reasoning alone?
4. Which properties can be checked from documents, and which require runtime enforcement?
5. Where has the specification accumulated duplication, ambiguity, or unnecessary complexity?
6. What conditions must be satisfied before considering a v1.0 candidate?

## 2. Cross-version invariants

The following invariants are architectural, not version-specific conveniences.

### 2.1 Authorization is separate from recommendation

An AI-generated plan, review, preference, confidence score, or execution proposal is not execution permission.

Authorization must remain attributable to an external or independently governed authority boundary.

### 2.2 Authority cannot be self-expanded

An agent may request authority, but it must not grant additional authority to itself merely because additional authority would make the task easier or faster.

This applies before execution, during recovery, during remediation, after failed remediation, and during handoff.

### 2.3 Execution must remain bound to the admitted operation

The executed action must remain bound to the authorized target, operation identity, scope, timing conditions, and relevant current-state checks.

A later change in circumstances must not be silently treated as if the old authorization still applies.

### 2.4 Verification is distinct from execution success

A successful tool response, executor response, transport acknowledgement, or delivery acknowledgement is not equivalent to verified external success.

Independent observation is required whenever the protocol claims that an external effect was achieved, corrected, or safely transferred.

### 2.5 Uncertainty must remain explicit

Unknown state must not be silently converted into:

- approval,
- non-dispatch,
- no effect,
- successful remediation,
- acceptance,
- or responsibility transfer.

### 2.6 History is append-only in meaning

Later recovery, remediation, verification, escalation, or handoff must not rewrite the historical fact that earlier actions or effects occurred.

A later corrective action may change the current state, but it does not erase the prior trace.

### 2.7 Recovery is not blind retry

A held, uncertain, or failed path must not simply restart the same operation under a new label.

Recovery requires fresh checks and a separately bounded successor path.

### 2.8 Remediation is a new operation

A remediation action must have a new operation identity and independently valid authority.

It must not reuse the original operation identity or treat corrective intent as permission to bypass normal controls.

### 2.9 Failed remediation terminates autonomous remediation chaining

Partial, ineffective, harmful, or unresolved remediation must not lead to automatic remediation-of-remediation.

Escalation exists specifically to terminate that autonomous chain.

### 2.10 Handoff requires attributable acceptance

Escalation output, message emission, transport delivery, and acknowledgement are insufficient to establish responsibility transfer.

A transferred handoff requires explicit acceptance bound to the intended receiver, scope, and independently attributable receiving authority.

### 2.11 Acceptance is not execution authorization

A receiver accepting responsibility for an escalated case does not automatically grant execution authority to either:

- the original TACP path, or
- the receiving process.

Any later state-changing action must be authorized under its own applicable authority model.

## 3. Version responsibility map

| Version | Primary responsibility | Entry condition | Exit condition |
| --- | --- | --- | --- |
| v0.1 | establish a bounded mission and gated execution path | mission exists | completed or safely held/stopped |
| v0.2 | preserve execution-time validity | v0.1-style mission approaches dispatch | execute only while authorization and conditions remain valid, otherwise hold |
| v0.3 | reconcile non-dispatch, no-effect, uncertainty, and blocked states | source mission is held/stopped and recovery-eligible | bounded successor or safe terminal recovery outcome |
| v0.4 | remediate a confirmed external effect | prior effect exists and remediation is justified | separately authorized remediation attempt or safe denial |
| v0.5 | verify remediation result and terminate unsafe chains | remediation attempt exists | completed only when independently verified effective; otherwise escalated |
| v0.6 | transfer responsibility after escalation | v0.5 escalation exists and autonomous remediation is stopped | explicit transferred handoff or explicit not-transferred state |

The important architectural pattern is that each version narrows one ambiguity left by the previous stage instead of granting broader autonomy.

## 4. Authority boundaries

TACP depends on boundaries that must remain external to prompt-only reasoning.

### 4.1 Planning boundary

Scout and analyst roles may gather evidence, classify conditions, challenge assumptions, and propose actions.

They do not thereby create execution permission.

### 4.2 Execution gate boundary

The execution gate is an enforcement boundary. It must not be treated as another deliberating agent whose output can be socially persuaded by the executor.

The gate must evaluate explicit state and authorization conditions.

### 4.3 Recovery boundary

Recovery admission does not grant permission to repeat the source operation.

A successor must be independently bounded and re-evaluated.

### 4.4 Remediation boundary

Remediation intent does not imply remediation authority.

The corrective action must be admitted as its own operation with separate identity, review, authorization, limits, and trace.

### 4.5 Escalation boundary

Escalation is a stop-and-transfer boundary, not a hidden path to additional autonomous capability.

The original autonomous path remains constrained after escalation.

### 4.6 Handoff boundary

The receiving party must be independently attributable.

The original executor or controller must not manufacture a receiver identity, receiver authority, or acceptance receipt that makes its own transfer appear valid.

## 5. Document-verifiable versus runtime-verifiable properties

TACP intentionally separates what a static document can prove from what requires an external runtime or security boundary.

### 5.1 Document-verifiable properties

The current validators can reasonably check properties such as:

- record cardinality,
- record ordering,
- identifier binding,
- reference consistency,
- declared scope containment,
- timestamp relationships,
- deadline relationships,
- required evidence-reference presence,
- mandatory prohibitions,
- result-to-closure consistency,
- declared receiver membership in permitted receiver sets,
- declared acceptance freshness,
- and registered synthetic fixture expectations.

### 5.2 Runtime-verifiable properties

The following cannot be proven from one JSON bundle alone:

- whether evidence is authentic,
- whether a human identity is genuine,
- whether a receiver authority really exists,
- whether an external effect actually occurred,
- whether a hidden second execution occurred,
- whether authority was secretly expanded outside the recorded document,
- whether a transport notification was truly delivered,
- whether a receiver actually saw or understood the incident,
- whether distributed duplicate-prevention is race-free,
- whether privilege isolation is actually enforced,
- whether historical records were mutated in a backing store,
- whether the original executor remained technically fenced after handoff,
- or whether legal/organizational responsibility truly changed.

These require runtime enforcement, signed receipts, trusted registries, immutable storage, security controls, and integration testing.

## 6. Validation architecture assessment

The repository currently uses three validation layers:

1. JSON Schema for structural shape.
2. Semantic validators for cross-record and policy consistency.
3. Explicit synthetic runtime fixtures for properties that cannot be established from a static document alone.

This separation is architecturally sound and should be preserved.

A synthetic runtime negative must not be presented as proof that runtime enforcement exists in a deployment. It is a test of the intended invariant and harness behavior only.

## 7. Complexity and duplication review

The first complete cycle is coherent, but several areas should be reviewed before v1.0.

### 7.1 Repeated identity fields

Multiple versions repeat identity fields across bundle and records. This improves local validation but creates duplication.

Review question: should v1.0 retain explicit repetition for trace robustness, or define a shared envelope with inherited identity?

Default recommendation: keep explicit binding where it protects against record substitution, but document why each repeated field is security-relevant.

### 7.2 Repeated prohibition lists

v0.5 and v0.6 use explicit mandatory prohibition sets.

Review question: should common prohibitions become a shared invariant registry rather than being separately enumerated in each version?

Default recommendation: keep version-specific lists in normative documents, but add a cross-version invariant matrix for human readability.

### 7.3 Multiple time limits

The protocol uses freshness windows, operation deadlines, review deadlines, verification deadlines, handoff deadlines, and acceptance-age limits.

This is necessary but can become confusing.

Before v1.0, each time field should be classified as one of:

- validity window,
- freshness window,
- action deadline,
- observation deadline,
- or terminal transfer deadline.

No two fields should exist if they enforce the same boundary under different names.

### 7.4 Safe denial versus failure

A protocol path may safely deny execution while still being a conformant document.

This distinction is already present but should become more explicit in v1.0 documentation so that users do not equate `reject action` with `invalid protocol record`.

### 7.5 Runtime evidence namespaces

Some synthetic runtime fixtures rely on conventionally named event fields.

Before v1.0, runtime fixture event vocabulary should be normalized so the harness does not depend on loosely interpreted field names.

### 7.6 Validator fragmentation

The current repository has legacy validation plus dedicated v0.5 and v0.6 validators.

This is acceptable during specification evolution, but v1.0 should define a stable validator architecture:

- shared primitives,
- version adapters,
- version-native semantic rules,
- and a common conformance report format.

## 8. Threat model review

TACP is designed primarily against structural amplification of error, ambiguity, misuse, or malicious intent.

The threat model should explicitly include at least these classes before v1.0:

1. **Authority forgery** — an agent invents or misrepresents permission.
2. **Scope creep** — an admitted action expands target or capability.
3. **Stale authorization** — previously valid permission is reused after conditions change.
4. **Evidence laundering** — transport, executor, or self-generated signals are presented as independent proof.
5. **Hidden repetition** — an uncertain or failed operation is retried without reconciliation.
6. **History rewriting** — prior adverse effects are removed or altered to simplify later state.
7. **Remediation chaining** — failed corrective actions recursively generate more autonomous corrective actions.
8. **Self-acceptance** — the originating path impersonates or substitutes for an external receiving authority.
9. **Silent abandonment** — escalation is emitted but no receiver accepts responsibility.
10. **Privilege resurrection** — a stopped path regains authority during recovery, remediation, escalation, or handoff.

## 9. First Complete Cycle assessment

The v0.1-v0.6 sequence forms a coherent first control cycle because it covers both forward action and failure handling:

```text
intent
→ bounded planning
→ authorization
→ execution
→ outcome verification
→ recovery when uncertain
→ remediation after confirmed effect
→ independent remediation verification
→ escalation when autonomous correction must stop
→ explicit responsibility handoff
```

The cycle intentionally stops at the handoff boundary.

TACP does not define what the external receiver must do next. That is a separate governance or incident-response domain and should not be folded back into the original autonomous chain without a new authority context.

## 10. Feature freeze policy

Until the architecture review is completed, the default policy is:

- do not add broader autonomous execution capability,
- do not add remediation-of-remediation paths,
- do not add automatic post-handoff action authority,
- do not weaken existing cross-version invariants,
- do not treat synthetic runtime tests as production guarantees,
- and do not add new version numbers merely to accumulate features.

Permitted work during the freeze includes:

- documentation clarification,
- validator bug fixes,
- fixture corrections,
- invariant matrices,
- threat-model documentation,
- terminology normalization,
- compatibility review,
- implementation guidance,
- and v1.0 readiness criteria.

## 11. v1.0 candidate conditions

A v1.0 candidate should not be declared merely because the version sequence is long enough.

The following conditions should be satisfied first:

1. Cross-version invariants are explicitly documented and non-contradictory.
2. Authority boundaries are consistently named and mapped across all stages.
3. Safe denial, document nonconformance, and runtime-state nonconformance are clearly separated.
4. Runtime-only guarantees are explicitly identified and not overclaimed.
5. The threat model covers the major structural failure modes.
6. Shared terminology for identity, scope, authority, evidence, deadlines, and closure is normalized.
7. Validator architecture is stable enough that adding conformance cases does not require ad hoc semantics.
8. A conformance matrix maps every normative invariant to at least one validator rule, fixture, or explicitly external runtime requirement.
9. Backward compatibility expectations for v0.1-v0.6 are documented.
10. The full registered suite passes on all supported Python versions after the final architecture-only changes.
11. README, specification documents, conformance index, and changelog agree on the protocol boundary.
12. No unresolved architecture-review issue would require breaking the core authority model.

## 12. Recommended next review artifacts

The architecture review should be followed by a small set of consolidation documents rather than a new protocol version:

```text
ARCHITECTURE_REVIEW.md
CONFORMANCE_MATRIX.md
THREAT_MODEL.md
AUTHORITY_BOUNDARIES.md
V1_READINESS.md
```

These documents should describe the existing v0.1-v0.6 system without expanding its autonomy.

## 13. Review conclusion

TACP v0.1-v0.6 forms a coherent first complete cycle whose dominant design direction is not increasing agent autonomy, but constraining transitions between planning, authority, execution, correction, escalation, and responsibility transfer.

The most important architecture invariant is:

> No stage may manufacture the authority, evidence, or responsibility transfer required to legitimize its own next stage.

That invariant should be treated as a primary v1.0 compatibility boundary.
