Triadic Agent Control Protocol (TACP)
A protocol for coordinating scout, analysis, and execution agents with separated permissions, iterative verification, and bounded control loops.
Target version: v0.1.0
Status: Draft — scope and core requirements. Schemas, examples, validation scripts, and conformance tests are not yet included.
Purpose
TACP describes how three agent roles share a mission while retaining separate authority boundaries:
- Scout: observes the environment and records evidence and uncertainty.
- Analyst: evaluates the evidence, proposes an action, and challenges its assumptions.
- Executor: performs only the action permitted by an external execution gate.
The roles form a feedback loop: observe, assess, challenge, check, execute, and verify the outcome.
TACP aims to constrain deviations and make stopping, rechecking, and tracing decisions possible. It does not guarantee safe behavior or correct judgments.
v0.1 scope
The initial version covers one mission, one proposed action, bounded pre-execution review, and post-execution verification. Additional observations may revise the proposal before execution. At most one execution attempt is allowed within the mission.
The version excludes parallel missions, autonomous permission changes, automatic retries, automatic rollback, and cross-organization coordination. Recovery or another action requires a new mission and a new authorization evaluation.
Roles and authority
Component	Produces	Authority boundary
Scout	Observations, sources, timestamps, target state, unresolved facts	Read-only access within an externally allowed scope
Analyst	Assessment, proposed action, prerequisites, stop conditions, review records	Cannot execute actions or grant permissions
Executor	Execution receipt and reported outcome	Can use only externally permitted operations and targets
Execution gate	Allow or deny decision with reasons	Checks authorization and conditions outside agent-generated judgments


The gate is an enforcement mechanism, not a fourth deliberating agent. Deployment policy is set by the human operator or authorized governing system. An agent cannot approve its own request for expanded authority.
Roles are logical responsibilities; three models or processes alone do not establish independent verification. Deployments must enforce the stated access boundaries outside prompts.
Core requirements
In this draft, MUST denotes a required property and MUST NOT denotes a prohibited behavior.
1. Shared mission: Every record MUST identify its mission and record type. Record identifiers MUST be unique within the mission.
2. Traceable basis: Each assessment MUST reference its observations; each review MUST reference the assessment version reviewed; each gate decision and execution receipt MUST identify the exact action and assessment version used.
3. Separated authorization: An analyst recommendation MUST NOT be treated as authorization. The gate MUST independently validate the applicable externally issued authorization.
4. Required challenge: Before execution, at least one review MUST examine assumptions, counterevidence, or missing information. Any unresolved issue that could invalidate an execution prerequisite MUST block execution.
5. No evidence inflation: Reassessing the same evidence MUST NOT be counted as new independent evidence. Reviews MUST distinguish reused evidence, newly acquired evidence, and unresolved questions. New evidence is not automatically independent.
6. Fresh conditions: The gate MUST check the target, operation, assessment version, observation freshness, authorization validity, and remaining mission budget at execution time. Material changes MUST invalidate prior readiness and require renewed assessment and review.
7. Bounded review: Mission policy MUST declare finite review limits, a deadline, and resource limits before work begins. Agents MUST NOT extend these limits. Exhaustion with unresolved issues MUST result in a hold.
8. Duplicate prevention: An operation identifier MUST be reserved by the execution enforcement layer before dispatch. A duplicate or uncertain prior attempt MUST NOT cause another dispatch in v0.1.
9. Outcome verification: A successful tool response alone MUST NOT establish mission completion. The scout MUST record post-execution observations, and the analyst MUST compare them with the declared expected result and stop conditions.
10. Uncertainty is explicit: Missing evidence, inaccessible references, or an unknown execution outcome MUST NOT be silently converted into approval or success.
Verification cycle
Stage	Required question	Result
Initial observation	What is known, when was it observed, and what remains unknown?	Observation record
Assessment	Does the evidence support this action within the mission?	Versioned assessment
Challenge review	What could invalidate the assessment, and what was actually checked?	Review record and unresolved issues
Pre-execution gate	Are the exact action, authority, state, and limits still valid?	Allow or deny record
Outcome verification	Did the expected result occur, and were unexpected changes observed?	Verification record and final disposition


When a review requires additional facts, the analyst requests scoped observations from the scout. The next review records what changed and why the prior decision was retained or revised. Passing by repetition or majority vote is not an authorization mechanism.
Execution and stopping
An allow decision MUST be bound to the exact action and relevant target state. Implementations MUST use conditional execution, locking, or an equivalent mechanism when a mutable prerequisite must remain true through dispatch. If they cannot enforce that prerequisite, they MUST hold the action instead of claiming that a prior check guarantees it.
The pre-execution review loop may return to observation within its declared limits. After dispatch, v0.1 permits observation and verification, but no further action attempt.
Final dispositions are:
- completed: post-execution verification supports the declared expected result and identifies no unresolved stop-condition violation.
- held: evidence, authority, state, or outcome remains unresolved, or a required check could not finish within limits. No further execution is allowed in this mission.
- stopped: an explicit stop decision or a confirmed stop-condition violation ended the mission. No further execution is allowed in this mission.
A held or stopped disposition does not imply that no side effects occurred. Execution receipts must preserve confirmed effects and uncertainties. A new mission does not make an uncertain prior operation safe to repeat; reconciliation is required before reauthorizing that operation.
Planned v0.1 conformance cases
The next specification and validation files will define a valid mission and rejection cases for:
- Missing challenge review or unresolved execution-blocking issues.
- Stale observations, changed target state, or an expired authorization.
- Missing evidence references or mismatched mission/assessment identifiers.
- An action outside the authorized target or operation scope.
- A duplicate execution request or an uncertain prior attempt.
- Exceeded review, time, or resource limits.
- Completion claimed without post-execution verification.
Document validation can check record structure and cross-record consistency. Runtime enforcement, evidence authenticity, and actual access isolation require separate implementation checks. A schema pass is not a safety certification.
Design principle
Unify purpose and traceability. Separate authority and responsibility. Recheck assumptions within explicit limits.
