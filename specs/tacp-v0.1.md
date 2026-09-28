TACP v0.1 — Core Specification
Protocol: Triadic Agent Control Protocol
Protocol version: 0.1.0
Status: Draft
Repository-relative path: specs/tacp-v0.1.md
1. Purpose and scope
TACP coordinates scout, analyst, and executor roles around one mission while separating observation, recommendation, and execution authority. A non-agent-controlled gate enforces authorization and execution prerequisites.
Version 0.1 covers one proposed action, bounded assessment revisions and challenge reviews, at most one execution attempt, and post-execution verification. Automatic retries, rollback, parallel missions, and autonomous permission expansion are outside scope.
TACP constrains and records a control process. It does not guarantee correct evidence, independent reasoning, or safe outcomes.
In this specification, MUST, MUST NOT, SHOULD, and MAY express required, prohibited, recommended, and optional behavior respectively. These definitions apply within TACP without incorporating an external standard by reference.
2. Trust and enforcement boundaries
Component	Responsibility	Prohibited authority
Scout	Acquire scoped observations before and after execution	Mutating the action target or granting execution authority
Analyst	Assess evidence, challenge assumptions, verify results	Dispatching the action or issuing authorization
Executor	Dispatch the exact gated action and record its outcome	Broadening the action or retrying it within the mission
Gate	Validate authorization, prerequisites, resource limits, and operation reservation	Treating an agent recommendation as sufficient authorization
Mission controller	Enforce policy, track state and limits, close the mission	Allowing agents to alter governing policy


The controller and gate are runtime control mechanisms, not additional deliberating roles. One runtime may provide both functions.
A human operator or an authorized governing system supplies mission policy and authorization. Prompt instructions alone do not satisfy enforcement requirements. Model count and process count do not establish verification independence.
External content MUST be treated as evidence data, not as instructions that can alter mission policy, permissions, or gate behavior. Read-only observations MUST still obey data-access and communication restrictions.
3. Representation and common envelope
Records use JSON objects. JSON objects MUST NOT contain duplicate member names. Timestamps use UTC strings with a trailing Z, in YYYY-MM-DDTHH:mm:ss[.fraction]Z form. Runtime comparisons MUST use parsed instants, not lexical comparison.
Every record contains:
Field	Type	Requirement
protocol_version	string	Exactly 0.1.0
record_type	string	One of the types defined below
record_id	nonempty string	Unique across the mission
mission_id	nonempty string	Same mission identifier throughout
created_at	timestamp	Time the record was issued
producer_id	nonempty string	Identity resolved by the deployment
producer_role	string	controller, scout, analyst, gate, or executor


Records are immutable once issued. Corrections require new records and explicit references; silent replacement is prohibited. References MUST resolve to records in the same mission with the required type. A referenced record MUST precede the referencing record in bundle order. Bundle order, rather than timestamp equality, resolves ordering where clocks have limited precision.
Runtime identity, record integrity, and authorization authenticity MUST be checked by deployment mechanisms. Self-declared JSON fields are not proof of these properties. Signatures and a specific identity provider are outside this version's interchange format.
All fields listed for a record are required unless marked optional or conditional. Collections described as nonempty MUST contain at least one item. Reference arrays MUST NOT repeat identifiers. Extensions MAY be placed in an optional extensions object, but MUST NOT override core semantics.
4. Mission and immutable policy
The controller issues one mission record before observation begins. Its common envelope has producer_role: controller and record_id equal to mission_id.
Additional fields:
Field	Type	Meaning
objective	nonempty string	Intended result
operation_id	nonempty string	Stable identifier for the intended logical operation
observation_scope	nonempty array of strings	Allowed data sources and communication destinations
authorization_ref	nonempty string	Externally resolvable authorization reference
policy_ref	nonempty string	Externally resolvable, fixed policy version
limits	object	Limits below
expected_results	nonempty array of condition objects	Observable requirements for success
stop_conditions	nonempty array of condition objects	Conditions that require stopping


A condition object has a mission-unique condition_id and a nonempty description. Deployments MUST define how each condition is evaluated; a prose description alone does not implement an execution check. Condition identifiers remain fixed throughout the mission.
limits contains:
- max_review_rounds: positive integer; counts every challenge-review record, including inconclusive reviews.
- deadline_at: timestamp later than mission creation; bounds active mission work.
- max_observation_age_seconds: positive integer; maximum age of pre-execution evidence used by the authorized assessment.
- max_execution_attempts: integer fixed to 1.
- resource_budgets: nonempty array of {budget_id, unit, limit}, where IDs are unique, units are nonempty strings, and limits are finite positive numbers.
The controller MUST meter the resources named by policy, including observation, analysis, and verification work. It MUST admit work only when it can bound that work within the remaining budget and deadline. Unmeterable required resources block execution. Measurements use the same unit as their corresponding limit and are never negative.
Policy and authorization must resolve to immutable versions or snapshots. Revocation MUST still be checked at execution time. Agents MUST NOT extend limits, substitute a policy, or change the mission objective. Changes requiring any of these create a new mission, subject to reconciliation of prior effects.
5. Record definitions
5.1 Observation
An observation record is produced by scout and contains:
- phase: pre_execution or post_execution.
- observed_at: timestamp of observation, no later than created_at.
- target_ref: nonempty, deployment-resolvable target identifier.
- target_state: {kind, value}, with nonempty strings; for example, a revision token or snapshot identifier. If no reliable state is available, use kind: unknown and value: unknown.
- sources: nonempty array of {source_ref, retrieved_at}.
- facts: nonempty array of factual observations expressed as strings.
- uncertainties: array of strings, possibly empty.
- execution_ref: required only for post_execution; references the execution record.
An observation does not prove its own authenticity. Unknown state cannot satisfy a prerequisite that requires a known target state. Post-execution evidence MUST be collected after the action attempt; pre-execution records cannot be relabeled as outcome verification.
5.2 Assessment
An assessment record is produced by analyst and contains:
- revision: positive integer, starting at 1 and increasing by one.
- supersedes_ref: absent for revision 1; otherwise references the immediately preceding assessment.
- observation_refs: nonempty array of pre-execution observation references.
- action: object defined below.
- rationale: nonempty explanation grounded in the referenced observations.
- prerequisites: nonempty array of {prerequisite_id, description, check_ref}. IDs are unique within the assessment; check_ref identifies an executable check in deployment policy.
- open_issues: array of {issue_id, description, blocks_execution}.
- recommendation: ready, hold, or stop.
action contains operation_id, target_ref, operation, and parameters. The first three are nonempty strings; parameters is a JSON object. operation_id MUST equal the mission's operation identifier.
An assessment may refine the proposed action within the existing mission and authorization scope. Every new revision requires its own challenge review. A ready recommendation is not permission to execute and MUST NOT coexist with an open issue whose blocks_execution is true.
Issue classification MUST follow the fixed policy. An issue that could invalidate an execution prerequisite blocks execution; an agent cannot waive it merely by changing a label. Resolving or reclassifying a prior blocking issue requires an assessment revision and an explanation supported by the next review.
5.3 Challenge review
A review record is produced by analyst and contains:
- round: positive integer, starting at 1 and increasing by one across the whole mission, not per assessment revision.
- assessment_ref: exact assessment reviewed.
- previous_review_ref: absent for round 1; otherwise references the preceding review.
- questions: nonempty array of questions challenging assumptions, counterevidence, or missing information.
- checks_performed: nonempty array of {question, method, finding, evidence_refs}. evidence_refs may be empty only when the finding explicitly remains unverified.
- reused_observation_refs: array of previously considered observation references.
- new_observation_refs: array of additional pre-execution observations not referenced by any earlier assessment or review.
- issue_updates: array of {issue_id, status, explanation, evidence_refs}, where status is open or resolved.
- remaining_blocking_issues: array of nonempty descriptions.
- decision: pass, reobserve, hold, or stop.
- decision_change: initial, retained, or revised.
- change_reason: nonempty explanation of what changed or why the decision was retained.
The reused and new reference arrays MUST be disjoint. Together they MUST include every observation referenced by the review's checks and issue updates. A newly issued observation is not independent evidence merely because its identifier is new.
pass requires concrete checks, no remaining blocking issues, and a ready assessment. A review cannot bypass a blocking issue in the assessment by claiming it resolved without an assessment revision. If new evidence materially changes the action, rationale, or prerequisites, a new assessment and review are required.
The first review has decision_change: initial; later reviews explicitly compare against the prior review. No new observation is required when a meaningful logical challenge can be resolved from existing evidence. Such a review MUST NOT claim additional independent corroboration.
reobserve requests additional scoped observations within remaining limits. hold and stop terminate the active mission through a closure record. Passing reviews cannot be accumulated as votes to override a failed condition. A later non-passing review invalidates earlier readiness.
5.4 Gate decision
A gate record is produced by gate and contains:
- assessment_ref and review_ref: latest assessment and latest review; the review must address that assessment.
- action: exact copy of the assessed action.
- authorization_ref and policy_ref: same references as the mission.
- checked_at and valid_until: timestamps; checked_at < valid_until <= deadline_at.
- checks: object whose required keys are listed below; each value is pass, fail, or unknown.
- prerequisite_results: one {prerequisite_id, result, evidence_ref} per assessed prerequisite, with result pass, fail, or unknown.
- resource_usage: one {budget_id, used, reserved} per mission resource budget.
- enforcement_ref: reference to the runtime check-and-dispatch mechanism.
- decision: allow or deny.
- reasons: nonempty array of strings.
Required checks keys are reference_integrity, review_passed, authorization_valid, scope_match, observation_fresh, target_state_match, budgets_available, deadline_valid, stop_conditions_clear, and operation_available.
All checks and prerequisite results MUST be pass for allow. Every budget entry must satisfy used + reserved <= limit; reserved resources include bounded execution and outcome verification. At dispatch, all applicable observation ages MUST be nonnegative and no greater than the declared maximum. unknown MUST NOT be treated as pass.
Equality of action copies is structural JSON equality: object member order is ignored, array order and values are preserved, and no string-to-number coercion is allowed. Deployments MAY additionally bind actions using hashes, but hashing is not required by this version.
An allow record is not a portable or reusable permission token. The runtime MUST revalidate its authority and mutable conditions at dispatch. Conditional execution, locking, or an equivalent mechanism MUST protect any prerequisite that must remain true through dispatch. If the deployment cannot enforce that property, it must deny the action.
Gate denial leads to a held closure in v0.1. A new mission may reconsider the action after the cause has been addressed.
5.5 Execution receipt
An execution record is produced by executor and contains:
- gate_ref: reference to an allow decision.
- assessment_ref: same assessment as the gate.
- action: exact copy of the gated action.
- started_at and finished_at: timestamps with started_at <= finished_at; finished time means the attempt ended or outcome tracking was abandoned.
- attempt: integer fixed to 1.
- reservation_ref: reference to the runtime's durable operation reservation.
- outcome: succeeded, failed, or unknown.
- reported_effects: array of strings describing confirmed effects, possibly empty.
- uncertainties: array of strings; nonempty for an unknown outcome.
- result_refs: array of externally resolvable tool-result or receipt references.
The runtime MUST atomically reserve the logical operation before dispatch, and dispatch strictly before the gate's expiration and mission deadline. A reservation blocks duplicate dispatch across concurrent requests and process restarts. Where an operation spans missions, deployments MUST preserve its identity or maintain equivalent deduplication; renaming a mission cannot bypass this rule.
An unknown outcome is not a failed action eligible for retry. A crash after reservation but before a receipt also leaves an unresolved attempt. The controller MUST hold the mission and retain the reservation evidence; it MUST NOT infer that nothing happened. Automatic delivery retries that could repeat the side effect are prohibited.
Only one execution record and one dispatch attempt are permitted per mission. A failed receipt does not prove absence of side effects.
5.6 Outcome verification
A verification record is produced by analyst and contains:
- execution_ref: reference to the execution receipt.
- observation_refs: nonempty array of post-execution observations referring to that receipt.
- expected_result_checks: exactly one {condition_id, result, evidence_refs} for every mission expected result.
- stop_condition_checks: exactly one such entry for every mission stop condition.
- unexpected_changes: array of strings.
- remaining_issues: array of {description, blocks_completion}.
- decision: completed, held, or stopped.
- reason: nonempty explanation.
For expected results, result is met, not_met, or unknown. For stop conditions it is triggered, clear, or unknown. Each entry's evidence references must be nonempty and drawn from the verification's observations.
completed requires a succeeded receipt, every expected result met, every stop condition clear, and no issue blocking completion. Unexpected changes MUST be assessed against the mission's conditions and policy; they cannot be ignored merely because the primary result occurred.
Any confirmed triggered stop condition requires stopped. Uncertain outcomes, unknown required conditions, unmet expected results, or inability to finish verification within limits require held unless a stop condition or explicit stop requires stopped.
5.7 Mission closure
A closure record is produced by controller and is the final record in a closed mission bundle. It contains:
- disposition: completed, held, or stopped.
- basis_refs: nonempty array of records establishing the disposition.
- verification_ref: required when a verification record exists; otherwise absent.
- execution_status: not_dispatched, recorded, or uncertain.
- reservation_ref: required when an unresolved reservation exists; otherwise optional.
- reason: nonempty explanation, including any missing verification.
- resource_usage: exactly one {budget_id, used} entry per mission resource budget, using the declared unit and a finite nonnegative amount.
completed requires a completed verification and execution_status: recorded. If verification exists, closure MUST agree with it, unless a subsequent explicit controller stop changes the disposition to stopped and records its basis.
An unresolved reservation requires execution_status: uncertain and cannot yield completed. A closure without verification is permitted only for held or stopped. A timeout after dispatch must retain the possibility of later external effects. recorded requires an execution receipt, including when its outcome is unknown; not_dispatched requires runtime confirmation that no dispatch occurred and no unresolved reservation remains.
Closure recording is required even if a deadline or resource limit has been reached. Deployments MUST reserve minimal control-plane capacity for this bookkeeping; reaching a limit permits no further agent work or action dispatch. Resources already consumed by an in-flight operation remain reportable, including overruns.
6. State transitions
States are derived from the ordered records and runtime events. They are not agent-controlled flags.
Current state	Event or condition	Next state
created	First valid pre-execution observation	observing
observing	Assessment issued	assessing
assessing	Challenge review begins	reviewing
reviewing	Additional observations or assessment revision required; limits remain	observing or assessing
reviewing	Latest review passes latest ready assessment	ready
ready	New observation, assessment, or review requires reconsideration	observing, assessing, or reviewing
ready	Gate allows and runtime dispatch prerequisites hold	executing
executing	Receipt issued	verifying
verifying	Outcome checks meet completion requirements	completed
Any nonterminal state	Unresolved blocking issue, denial, or exhausted limit	held
Any nonterminal state	Confirmed stop condition or explicit controller stop	stopped


completed, held, and stopped are terminal and require closure. An explicit controller stop may use the mission record as its basis and explain the stop decision in the closure reason. Completion cannot be established without the records required in Section 5.6.
Reaching the maximum review count prohibits another review, but does not invalidate the last permitted passing review. Reaching the deadline prohibits dispatch or further agent work. A material change after the last available review therefore requires a hold.
No terminal state can return to execution. New work requires a new mission; any earlier uncertain operation must first be reconciled. Closing a mission does not cancel an already dispatched external operation or prove that it has stopped.
7. Mission bundle and validation boundaries
A closed mission bundle is a JSON object with:
- protocol_version: 0.1.0.
- mission_id: identifier of the included mission.
- records: ordered, nonempty array containing one mission first, zero or more intermediate records, and exactly one closure last.
All references to TACP records MUST resolve inside the bundle. External references such as authorization, policy, source, and reservation references are resolved by the deployment. Their presence in JSON alone cannot establish runtime validity.
Conformance has three separate levels:
1. Structural validation: field presence, types, allowed values, and object shape.
2. Semantic validation: references, order, versions, review counts, action equality, state transitions, and completion requirements.
3. Runtime enforcement: authentic identity and evidence, actual permissions, live revocation, atomic reservations, conditional dispatch, and resource metering.
Passing structural and semantic checks does not prove runtime enforcement. Implementations MUST state which levels they validate. This draft supplies requirements; schemas and executable checks will be added separately.
8. Required conformance scenarios
Future fixtures and validators MUST include:
Scenario	Required interpretation
Valid assessment, meaningful review, gated execution, verified result	Completed bundle accepted
Review requests more evidence; revised assessment passes within limits	Valid bounded review path
Missing challenge review followed by execution	Invalid bundle
Same evidence reused without claiming independence	Permitted if actual challenge checks are recorded
Claimed readiness with unresolved blocking issue	Invalid readiness or execution
Gate allows stale observations or expired authorization	Invalid gate decision
Runtime detects changed target before dispatch	Deny and hold; no dispatch
Missing record reference or mismatched assessment revision	Invalid bundle
Execution action differs from gated action	Invalid bundle
Duplicate operation or unresolved prior attempt	No new dispatch; hold
Review loop exceeds its declared count	Invalid loop; runtime must hold before excess work
Last allowed review passes with sufficient time and resources	May proceed to gate
Unknown execution outcome followed by completed closure	Invalid completion
No post-execution verification followed by completed closure	Invalid completion
Deadline prevents verification after execution	Valid held closure preserving effects and uncertainty
Confirmed stop condition	Stopped closure; no further dispatch


A correctly recorded denial or hold can be a conforming mission. Rejection fixtures MUST distinguish malformed protocol records from valid records documenting a blocked action.
9. Limitations and integration
Several agents may share the same mistaken assumptions or contaminated sources. Iteration does not establish independence, and a recorded review is not proof that its reasoning was sound. Authorization and runtime controls remain necessary even when all agents agree.
TACP does not expose or require private model reasoning. Records capture observable evidence, decision summaries, checks, and action receipts sufficient for the declared control process.
Existing authorization, handoff, trace, and audit protocols may supply external references. This draft does not claim verified interoperability with any particular protocol. Adapters must define identifier mapping, policy ownership, and validation boundaries before making such claims.
Unify purpose and traceability. Separate authority and responsibility. Recheck assumptions within explicit limits.
