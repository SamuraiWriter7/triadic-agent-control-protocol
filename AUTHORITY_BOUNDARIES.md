# TACP Authority Boundaries

**Baseline:** v0.1.0-v0.6.0  
**Status:** architecture-review artifact / feature-freeze phase  
**Purpose:** define who may propose, authorize, execute, verify, remediate, escalate, accept responsibility, and where each authority ends.

This document does not add new autonomous capability. It consolidates the authority model already implied by TACP v0.1-v0.6.

## 1. Core authority principle

TACP separates five things that must not be collapsed into one another:

1. recommendation,
2. authorization,
3. execution,
4. verification,
5. responsibility acceptance.

The architectural rule is:

> A role may request or describe a transition without thereby gaining the authority required to perform, validate, or legitimize that transition.

A convenient shorthand is:

```text
proposal != permission
permission != execution
execution != verified success
escalation != transfer
acceptance != execution authorization
```

## 2. Authority domains

TACP uses the following logical authority domains.

### 2.1 Observation authority

Observation authority permits bounded collection of evidence about declared targets and conditions.

It does not authorize state-changing action.

Typical holder:

- scout,
- bounded observer,
- transport observer,
- post-remediation observer.

### 2.2 Analytical authority

Analytical authority permits interpretation, challenge, classification, and recommendation.

It does not authorize execution.

Typical holder:

- analyst,
- reviewer,
- verifier acting in an analytical role.

### 2.3 Admission / authorization authority

Admission authority decides whether a specific operation may proceed under declared scope, identity, time, and constraints.

This authority must be independently attributable and must not be self-issued by the executor that benefits from it.

Typical holder:

- execution gate,
- remediation gate,
- human approver,
- external policy authority.

### 2.4 Execution authority

Execution authority permits one admitted operation to be dispatched within the exact authorized boundary.

It does not include authority to expand scope, renew expired permission, reinterpret denied states, or create successor authority.

Typical holder:

- executor.

### 2.5 Verification authority

Verification authority permits independent determination of whether the claimed external state actually holds based on bounded evidence.

It must remain distinct from the actor whose success claim is being evaluated when the protocol requires independent verification.

### 2.6 Escalation authority

Escalation authority permits a failed or unresolved autonomous path to be terminated and packaged for transfer.

It does not authorize the original path to continue acting after escalation.

### 2.7 Responsibility-acceptance authority

Responsibility-acceptance authority permits an external receiver to explicitly accept responsibility for an escalated case.

It does not automatically authorize any state-changing action.

## 3. Role capability matrix

| Role / boundary | May observe | May recommend | May authorize | May execute | May verify | May accept responsibility |
| --- | --- | --- | --- | --- | --- | --- |
| Scout | yes | limited factual recommendation | no | no | no | no |
| Analyst | yes | yes | no | no | analytical verification where specified | no |
| Executor | operational observation only as needed | may report | no self-grant | yes, admitted operation only | no independent self-certification | no |
| Execution gate | inspect declared state | no autonomous planning requirement | yes, bounded admission | no | no | no |
| Human reviewer / approver | yes | yes | yes within assigned authority | not implied | may review evidence | possibly, if separately acting as receiver |
| Post-remediation verifier | yes | classify outcome | no new execution grant | no | yes | no |
| TACP controller | coordinate records / state | may propose transitions | only where externally granted | no implicit execution | may enforce protocol-state consistency | no self-acceptance |
| External receiver | inspect escalated package | may decide next governance step | only under separate authority model | not implied | may perform later review | yes, if independently authorized |

This matrix is conceptual. A deployment may combine implementation components, but must preserve the logical separation of powers.

## 4. v0.1 boundary — planning and gated execution

v0.1 establishes that planning and recommendation do not equal permission.

### Scout may

- collect bounded evidence,
- report uncertainty,
- identify relevant state.

### Scout must not

- authorize execution,
- enlarge target scope,
- convert uncertainty into approval.

### Analyst may

- challenge assumptions,
- evaluate evidence,
- recommend an action or denial.

### Analyst must not

- grant execution permission merely because the recommendation is strong,
- overwrite gate state.

### Execution gate may

- admit or deny an operation under declared policy and current conditions.

### Execution gate must not

- become a deliberating substitute for the analyst,
- accept executor self-authorization as equivalent to independent permission.

### Executor may

- execute the admitted operation.

### Executor must not

- mutate the authorized target or scope,
- create additional authority,
- certify its own external success where independent verification is required.

## 5. v0.2 boundary — execution-time validity

v0.2 makes authority time- and state-sensitive.

An authorization that was valid earlier does not remain valid merely because the executor still possesses a record of it.

Before dispatch, the gate or equivalent enforcement layer must check relevant conditions such as:

- authorization still active,
- deadline not expired,
- target unchanged,
- resource limits respected,
- state not revoked or held,
- required runtime facts known.

The executor may not reinterpret an expired, revoked, held, or authorization-unknown state as permission to continue.

## 6. v0.3 boundary — recovery without authority resurrection

Recovery is not an authority reset.

A failed, uncertain, blocked, or non-dispatched path may produce a recovery review, but recovery does not restore the original operation's authority by default.

A successor path must be separately bounded.

The recovery mechanism must not:

- silently repeat the original operation,
- reuse stale admission without re-evaluation,
- broaden scope because the first attempt failed,
- self-expand privileges to overcome a blocker.

## 7. v0.4 boundary — remediation as a separate authority context

A confirmed external effect may justify remediation, but corrective intent does not create corrective authority.

A remediation action requires:

- explicit causal linkage,
- a new operation identity,
- independent authorization,
- human review where required,
- bounded scope and limits,
- explicit admission.

The original operation's authorization must not be reused as remediation authority.

The original executor must not claim that because it caused the effect, it is automatically authorized to correct it.

## 8. v0.5 boundary — verification and escalation

A remediation success claim is not sufficient to close the incident.

Independent post-remediation verification determines whether the remediation is:

- confirmed effective,
- partially effective,
- ineffective,
- harmful,
- unresolved,
- or not dispatched.

When the result is partial, ineffective, harmful, or unresolved, the autonomous remediation path must terminate as escalated.

Escalation does not grant:

- another remediation,
- a remediation-of-remediation,
- expanded authority,
- renewed source-operation authority.

## 9. v0.6 boundary — escalation handoff

v0.6 separates transport from responsibility transfer.

The following are insufficient to establish transfer:

- escalation created,
- handoff message emitted,
- transport submitted,
- delivery recorded,
- acknowledgement received.

A transfer requires an explicit disposition of `accepted` from the intended receiver under independently attributable receiving authority.

### Originating TACP path may

- prepare the handoff request,
- identify the permitted receiver,
- transmit the package,
- record delivery observations,
- record the receiver's authoritative disposition.

### Originating TACP path must not

- self-accept the handoff,
- invent receiver authority,
- treat delivery as acceptance,
- expand accepted scope beyond the requested scope,
- restart the source or remediation operation after handoff,
- assume silence means acceptance.

### Receiver may

- accept,
- reject,
- remain unconfirmed,
- or time out.

### Receiver acceptance means

Responsibility for the escalated case is transferred within the accepted scope.

### Receiver acceptance does not mean

- the original executor may resume,
- the receiving process may execute arbitrary corrective actions,
- the receiving process inherits TACP source-operation authority.

Any later state-changing action requires a separate applicable authority model.

## 10. Authority termination points

TACP must be explicit about where a role's authority ends.

| Authority | Terminates when |
| --- | --- |
| Observation authority | declared observation scope, deadline, or resource limit ends |
| Analytical authority | review decision is recorded; no implicit execution power follows |
| Execution admission | expires, is revoked/held, conditions change, operation completes, or one-time use is consumed |
| Execution authority | admitted operation completes or becomes invalid |
| Recovery authority | recovery outcome closes or successor is separately admitted |
| Remediation authority | remediation attempt closes or is no longer valid |
| Verification authority | verification record is completed; it does not become remediation authority |
| Escalation authority | handoff request is emitted and autonomous corrective authority remains stopped |
| Responsibility acceptance | limited to the accepted scope; does not imply downstream execution authority |

## 11. Forbidden authority conversions

The following conversions are structurally forbidden unless a separate independent authority step exists:

```text
recommendation -> execution permission
executor success -> verified success
held state -> retry permission
recovery need -> privilege expansion
source authorization -> remediation authorization
remediation failure -> second remediation authority
escalation -> execution authority
transport delivery -> responsibility acceptance
responsibility acceptance -> execution authority
```

These are not merely implementation preferences. They are TACP compatibility boundaries.

## 12. Authority provenance

A declared authority reference is not automatically trustworthy merely because it appears in a valid JSON document.

Production deployments need an external mechanism to establish authority provenance, such as:

- signed authorization receipts,
- trusted authority registries,
- organizational role bindings,
- hardware- or service-backed identities,
- policy-engine decisions,
- immutable audit records.

The document validator may verify that an authority reference is structurally present and consistently bound. It cannot prove that the external authority is genuine.

## 13. Self-authorization and self-acceptance

Two especially important forbidden patterns are:

### 13.1 Self-authorization

An actor that benefits from expanded authority must not be able to create that authority unilaterally.

Example:

```text
executor needs broader file access
-> executor writes new authority record
-> executor treats it as valid
```

This is invalid even if the resulting document is internally well-formed.

### 13.2 Self-acceptance

An originating TACP path must not impersonate the independent receiver required to close a handoff.

Example:

```text
controller sends handoff
-> same control domain manufactures receiver identity
-> same control domain records acceptance
-> case marked transferred
```

This violates the handoff authority boundary.

## 14. Authority and evidence separation

Authority and evidence are distinct.

Evidence may support an authorization decision, but evidence does not grant permission by itself.

Similarly, an authorization receipt proves permission was granted under some authority model; it does not prove the external effect succeeded.

Therefore:

```text
evidence != authority
authority != effect
effect claim != verified effect
```

## 15. Authority and responsibility separation

Authority answers:

> Who may cause a state transition?

Responsibility acceptance answers:

> Who now owns the obligation to decide what happens next?

These are related but different.

A receiver may accept responsibility while having no execution permission at all.

This distinction is intentional and prevents v0.6 handoff from becoming a hidden post-handoff execution channel.

## 16. Runtime enforcement requirements

The following properties require more than schema or semantic validation:

- executor cannot bypass the gate,
- expired/revoked authority is actually denied at dispatch,
- authority records cannot be forged,
- operation identity cannot be reused concurrently,
- hidden retries are prevented,
- remediation fencing is enforced,
- escalated paths cannot regain privilege,
- receiving identity is genuine,
- acceptance is actually attributable to the receiver,
- backing history cannot be rewritten,
- accepted scope is enforced downstream.

These require runtime controls, not prompt instructions alone.

## 17. Minimum production authority architecture

A deployment claiming meaningful TACP-style authority enforcement should have at least:

1. an external authority source,
2. a gate independent from the executor's reasoning path,
3. operation-scoped authorization,
4. dispatch-time validity checks,
5. immutable or tamper-evident trace records,
6. independent remediation authorization,
7. post-remediation verification separated from executor success reporting,
8. explicit escalation fencing,
9. independently attributable handoff acceptance,
10. a separate authority decision for any post-handoff state-changing action.

## 18. Cross-version authority invariant

The authority model across v0.1-v0.6 can be summarized as:

> No actor may convert its need, recommendation, success claim, recovery state, remediation intent, escalation state, or delivery evidence into additional authority without an independently attributable authority transition.

This is the main authority compatibility boundary for any future v1.0 candidate.

## 19. Review conclusion

TACP does not try to solve control by asking one intelligent agent to behave perfectly.

Instead, it separates powers so that planning, authorization, execution, verification, remediation, escalation, and responsibility transfer cannot all be legitimized by the same actor's assertion.

The practical rule is simple:

> An agent may ask for more authority. It must not be the entity that grants that authority to itself.
