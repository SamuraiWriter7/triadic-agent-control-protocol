# TACP v1.0 Readiness Gate

**Baseline:** v0.1.0-v0.6.0  
**Current state:** First Complete Cycle completed; feature freeze active  
**Purpose:** determine whether the architecture is mature enough to enter a v1.0 candidate phase without weakening the authority model or overstating conformance.

## 1. Readiness principle

TACP should not move to v1.0 because the version count is large enough, because the first cycle is complete, or because the registered fixtures pass.

A v1.0 candidate is justified only when the existing architecture is internally coherent, the authority boundaries are stable, the conformance model is auditable, and all runtime-only guarantees are clearly separated from document-level guarantees.

The primary compatibility boundary is:

> No stage may manufacture the authority, evidence, or responsibility transfer required to legitimize its own next stage.

Any proposed v1.0 change that weakens this invariant is a HOLD condition.

## 2. Inputs to this readiness gate

This gate consolidates the following review artifacts:

- `ARCHITECTURE_REVIEW.md`
- `CONFORMANCE_MATRIX.md`
- `THREAT_MODEL.md`
- `AUTHORITY_BOUNDARIES.md`
- `CONFORMANCE_INDEX.md`
- `CHANGELOG.md`
- registered schemas, validators, fixtures, and GitHub Actions results through v0.6.0

The readiness decision must be based on agreement across these artifacts, not on one document in isolation.

## 3. Readiness states

TACP uses three architecture-readiness states.

### 3.1 GO

A v1.0 candidate may be prepared when all mandatory readiness gates pass and no unresolved issue requires changing the core authority model.

GO does not mean production-safe. It means the protocol specification is mature enough to stabilize a compatibility contract.

### 3.2 CONDITIONAL GO

A candidate may be prepared only for review when remaining items are limited to non-breaking consolidation work, such as:

- terminology normalization,
- documentation consistency,
- validator refactoring that preserves semantics,
- conformance report normalization,
- fixture naming cleanup,
- or explicit runtime-integration guidance.

A CONDITIONAL GO must list all remaining items and none may alter normative authority transitions.

### 3.3 HOLD

v1.0 must not be declared when any unresolved issue could:

- permit self-expanded authority,
- merge recommendation with authorization,
- merge executor success with verified success,
- permit blind retries,
- permit source authorization reuse for remediation,
- permit autonomous remediation chaining,
- treat escalation as new execution authority,
- treat delivery as acceptance,
- treat acceptance as execution authorization,
- rewrite prior history,
- or materially change cross-version identity and responsibility semantics.

## 4. Mandatory readiness gates

### Gate A — Cross-version invariant stability

**Requirement:** the invariants documented in `ARCHITECTURE_REVIEW.md` must be non-contradictory across v0.1-v0.6.

Minimum checks:

- recommendation remains distinct from authorization,
- authority cannot be self-expanded,
- execution remains bound to an admitted operation,
- external success requires independent verification,
- uncertainty remains explicit,
- history remains append-only in meaning,
- recovery is not blind retry,
- remediation is a separately authorized operation,
- failed remediation terminates autonomous chaining,
- handoff requires attributable acceptance,
- acceptance does not imply execution authorization.

**GO condition:** no version-specific rule contradicts these invariants.  
**HOLD condition:** resolving a contradiction requires weakening an invariant.

### Gate B — Authority boundary stability

**Requirement:** `AUTHORITY_BOUNDARIES.md` must define stable transitions between observation, analysis, authorization, execution, verification, escalation, and responsibility acceptance.

The following implicit conversions must remain prohibited:

```text
recommendation -> execution permission
executor success -> verified success
held state -> retry permission
source authorization -> remediation authorization
remediation failure -> second remediation authority
escalation -> execution authority
transport delivery -> responsibility acceptance
responsibility acceptance -> execution authority
```

**GO condition:** all normative authority transitions require independently attributable authority where applicable.  
**HOLD condition:** any actor can manufacture the authority required for its own next transition.

### Gate C — Conformance traceability

**Requirement:** every normative invariant must map to at least one of:

- schema rule,
- semantic validator rule,
- registered fixture,
- synthetic runtime harness assertion,
- or explicit external runtime/trust requirement.

The `CONFORMANCE_MATRIX.md` classification remains:

- `S` — Schema
- `M` — Semantic
- `H` — Harness / synthetic runtime
- `R` — External runtime
- `T` — Trust / provenance

**GO condition:** no normative rule exists without a declared verification layer.  
**HOLD condition:** an important safety claim has no validator, fixture, or explicit external requirement.

### Gate D — Runtime boundary honesty

**Requirement:** the specification must not claim that static validation proves properties that require external enforcement.

Runtime/trust-only properties include at least:

- authenticity of evidence,
- identity of human reviewers or receivers,
- validity of organizational authority,
- actual external effects,
- hidden duplicate execution,
- privilege isolation,
- backing-store immutability,
- real notification delivery,
- real acceptance by an external party,
- and legal or organizational responsibility transfer.

**GO condition:** these are explicitly marked `R` and/or `T` where relevant.  
**HOLD condition:** README, specs, or conformance documents imply that registered fixture PASS certifies these properties.

### Gate E — Threat-model coverage

**Requirement:** `THREAT_MODEL.md` must cover the structural failure modes that the protocol claims to resist.

Minimum classes:

1. authority forgery,
2. scope creep,
3. stale authorization,
4. evidence laundering,
5. hidden repetition,
6. history rewriting,
7. remediation chaining,
8. self-acceptance,
9. silent abandonment,
10. privilege resurrection.

**GO condition:** each threat maps to a defensive boundary and residual risk.  
**HOLD condition:** a major known threat can bypass the authority model without an explicit external control requirement.

### Gate F — Terminology normalization

**Requirement:** core terms must have one stable meaning across specifications and validators.

Terms requiring normalization before v1.0 include:

- operation identity,
- authority reference,
- scope,
- target,
- evidence reference,
- observation,
- verification,
- admission,
- authorization,
- closure,
- escalation,
- handoff,
- receiver,
- acceptance,
- responsibility transfer,
- deadline,
- freshness window,
- validity window.

**GO condition:** the same term is not used for materially different authority semantics.  
**CONDITIONAL GO condition:** remaining changes are editorial and non-breaking.  
**HOLD condition:** normalization would change normative behavior.

### Gate G — Time-model normalization

**Requirement:** time constraints must be classified by purpose rather than accumulated ad hoc.

Every normative time field should be categorized as one of:

- validity window,
- freshness window,
- action deadline,
- observation deadline,
- terminal transfer deadline.

**GO condition:** no two time fields enforce the same boundary under incompatible names or semantics.  
**CONDITIONAL GO condition:** only naming or documentation remains.  
**HOLD condition:** temporal ambiguity can change accept/reject outcomes.

### Gate H — Validator architecture stability

**Requirement:** validator organization must be understandable and maintainable without changing semantics.

A v1.0 candidate should have a stable architecture consisting conceptually of:

```text
shared primitives
+ version adapters
+ version-native semantic rules
+ synthetic runtime harness
+ common conformance report
```

The existing legacy / v0.5 / v0.6 split may remain temporarily if behavior is stable and documented.

**GO condition:** adding or reviewing a conformance case does not require ambiguous ad hoc logic.  
**CONDITIONAL GO condition:** refactoring remains, but current behavior is fully covered by regression suites.  
**HOLD condition:** validator fragmentation obscures normative behavior or causes version-dependent contradictions.

### Gate I — Backward compatibility contract

**Requirement:** the treatment of v0.1-v0.6 after v1.0 must be explicit.

Before v1.0, document whether prior versions are:

- immutable historical specifications,
- still-valid compatibility profiles,
- migration inputs,
- or deprecated experimental profiles.

A v1.0 validator must not silently reinterpret historical fixtures under new semantics.

**GO condition:** compatibility and migration expectations are documented.  
**HOLD condition:** v1.0 would silently change the meaning of already registered records.

### Gate J — Documentation agreement

**Requirement:** the following must describe the same protocol boundary:

- `README.md`
- version specifications
- `ARCHITECTURE_REVIEW.md`
- `CONFORMANCE_MATRIX.md`
- `THREAT_MODEL.md`
- `AUTHORITY_BOUNDARIES.md`
- `CONFORMANCE_INDEX.md`
- `CHANGELOG.md`
- this readiness gate

**GO condition:** no document claims broader autonomy, authority, or guarantees than the normative specs and validators support.  
**HOLD condition:** material contradictions remain.

### Gate K — Full regression pass

**Requirement:** after final architecture-only changes, all registered suites must pass on all supported Python versions.

At the current baseline, GitHub Actions validates through v0.6 on Python 3.10 and 3.12.

**GO condition:** final candidate baseline is green after all consolidation changes.  
**HOLD condition:** any registered expected outcome changes unexpectedly.

### Gate L — No unresolved core architecture issue

**Requirement:** there must be no known unresolved issue whose correct fix would require breaking the authority model.

Examples of core architecture issues include:

- uncertainty about who may authorize a transition,
- incompatible meanings of responsibility transfer,
- inability to distinguish acceptance from execution permission,
- inability to preserve immutable causal history,
- or inability to prevent autonomous corrective loops.

**GO condition:** remaining issues are implementation guidance, editorial consolidation, or explicitly external runtime requirements.  
**HOLD condition:** a core transition still lacks a coherent authority boundary.

## 5. Current readiness assessment

Based on the completed first-cycle review artifacts, the current architecture is best classified as:

> **CONDITIONAL GO for v1.0 preparation; HOLD on declaring v1.0 final.**

The reason is structural rather than functional. The first control cycle is complete and the current registered suites pass, but v1.0 should wait until consolidation work is finished.

The principal remaining readiness work is:

1. normalize shared terminology across v0.1-v0.6,
2. normalize the time-field taxonomy,
3. define the stable validator architecture and common report shape,
4. document backward compatibility / migration expectations,
5. perform a cross-document contradiction review,
6. re-run the full registered suite after those architecture-only changes,
7. record the final v1.0 candidate baseline in README, Conformance Index, and Changelog.

None of these items should add new autonomous capability.

## 6. Explicit non-blockers

The following do not by themselves block a v1.0 specification candidate, provided they remain clearly external requirements:

- lack of a production identity provider,
- lack of a universal signed-receipt infrastructure,
- lack of a deployment-specific authorization service,
- lack of a globally immutable storage layer,
- lack of proof that every external system enforces TACP correctly,
- or lack of certification for a specific production environment.

TACP is a protocol specification. v1.0 readiness requires a stable contract and honest boundary definitions, not universal deployment proof.

## 7. Automatic HOLD triggers

The v1.0 process must immediately return to HOLD if any proposed change does one of the following:

- lets an executor authorize itself,
- lets an agent infer permission from urgency or utility,
- lets transport evidence substitute for acceptance,
- lets acceptance substitute for action authorization,
- lets remediation reuse source authority without a new admission boundary,
- lets failed remediation spawn autonomous corrective recursion,
- lets historical adverse effects disappear from trace,
- lets escalation implicitly reactivate the original autonomous path,
- lets runtime-only properties be presented as schema-level guarantees,
- or changes registered semantics without an explicit compatibility decision.

## 8. v1.0 candidate preparation sequence

When all mandatory gates are satisfied, prepare v1.0 in this order:

```text
1. Freeze normative terminology
2. Freeze authority transition vocabulary
3. Freeze time-field taxonomy
4. Freeze validator architecture
5. Publish backward-compatibility policy
6. Run cross-document consistency review
7. Run complete regression suite
8. Record candidate conformance baseline
9. Only then draft v1.0 normative consolidation
```

The v1.0 draft should consolidate the existing architecture, not introduce a new autonomous stage after handoff.

## 9. Final readiness rule

TACP is ready for v1.0 only when the question changes from:

> "What capability should we add next?"

into:

> "Can we freeze the current authority, evidence, verification, recovery, remediation, escalation, and handoff semantics without creating contradictions?"

If the answer is yes, and Gates A-L pass, v1.0 may move to GO.

Until then, the correct state is feature freeze and consolidation.
