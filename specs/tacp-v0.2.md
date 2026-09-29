TACP v0.2 — Dispatch Rechecking and Explicit Holds
Protocol: Triadic Agent Control Protocol
Protocol version: 0.2.0
Status: Draft — specification only; v0.2 schemas, examples, and validator support are pending.
Repository-relative path: specs/tacp-v0.2.md
1. Relationship to v0.1
This document extends specs/tacp-v0.1.md. Its requirements remain in force except where this document explicitly changes them. The normative terms MUST, MUST NOT, SHOULD, and MAY retain their v0.1 meanings.
All records and the bundle in a v0.2 mission MUST use protocol_version: 0.2.0. Mixed-version bundles are invalid. A v0.1 record MUST NOT be relabeled as v0.2 without satisfying the additional requirements.
Version 0.2 retains one mission, one logical operation, at most one dispatch attempt, bounded review, and terminal closure. Automatic retries, automatic rollback, parallel missions, and reopening a closed mission remain outside scope.
The change is to make the last execution check and reasons for holding a mission explicit and mechanically inspectable. Passing document validation still does not establish actual permissions, evidence authenticity, or runtime safety.
2. Changes at a glance
Area	v0.2 requirement
Mission	Declare a finite maximum age for the final dispatch check
Final dispatch check	Add a dispatch_check record between an allow gate and execution
Authorization	Record the checked authorization status, scope match, and evidence references
Target state	Record expected and current state and require renewed planning after a mismatch
Review issues	Give review issue updates an explicit execution-blocking flag
Execution	Bind the receipt to the exact passing dispatch check
Closure	Add machine-readable reason codes, including unknown outcome and exhausted limits
Validation	Distinguish a conforming blocked mission from a mission that ignored a blocker


3. Mission additions
The mission limits object adds the required field:
Field	Type	Constraint
max_dispatch_check_age_seconds	positive integer	Maximum permitted age of the final dispatch check at action dispatch


This limit is fixed before agent work begins. Agents MUST NOT extend it. It does not replace observation freshness, gate expiration, authorization expiration, or the mission deadline; all applicable limits must hold together.
There is at most one dispatch_check record per mission. A denied or expired final check cannot be replaced by another final check in the same mission. This keeps v0.2's recovery boundary explicit: close the mission and consider new work under a new mission and authorization evaluation.
4. Explicit review-issue tracking
Every object in review.issue_updates adds the required boolean blocks_execution.
- An update with status: resolved MUST have blocks_execution: false.
- An update with status: open may be blocking or nonblocking, according to fixed policy.
- If an issue appears in both the assessed revision's open_issues and a review update, the review MUST NOT waive or downgrade an assessment blocker.
- Resolving or downgrading a previously blocking issue requires a new assessment revision and an explicit update in the first review of that revision.
- A resolved issue MUST already exist in an earlier assessment or review. An unknown issue cannot be silently declared resolved.
- Issue IDs are stable across revisions and MUST NOT be changed to hide an unresolved issue.
The validator tracks the latest structured state of each issue across the mission. A passing review MUST have no remaining tracked execution-blocking issues and an empty remaining_blocking_issues list. Omitting an old issue from a new assessment or review does not resolve it.
For a resolution or downgrade, the review update MUST identify supporting observations through a nonempty evidence_refs array and explain the change in explanation. Reused evidence may support a logical correction; it MUST NOT be described as new independent corroboration.
The existing rules for reused_observation_refs and new_observation_refs remain unchanged. An additional observation already referenced by the revised assessment is reused evidence when its subsequent review begins.
Structured flags make issue continuity checkable. Whether an issue was correctly classified, or whether the evidence truly resolves it, still requires policy enforcement and substantive review.
5. Dispatch-check record
dispatch_check is a new record type produced by gate. It uses the common envelope defined in specs/tacp-v0.1.md, with version 0.2.0.
It MUST follow an allow gate decision and precede any execution receipt. No new assessment, review, or pre-execution observation may intervene between that gate, its dispatch check, and dispatch. If additional agent work is needed after the gate, the mission MUST be held; renewed planning belongs to a new mission in this version.
Required fields:
Field	Type	Meaning
gate_ref	nonempty string	The preceding allow gate
assessment_ref	nonempty string	Same latest assessment as the gate
review_ref	nonempty string	Same latest passing review as the gate
action	action object	Structurally identical to the gated action
authorization_ref	nonempty string	Same immutable authorization reference as the mission
policy_ref	nonempty string	Same immutable policy reference as the mission
checked_at	UTC timestamp	Time of the final runtime checks
authorization_check	object	Fields defined in Section 5.1
target_check	object	Fields defined in Section 5.2
checks	object	Required named results defined in Section 5.3
resource_usage	nonempty array	One {budget_id, used, reserved} per mission budget
decision	string	allow or deny
reasons	nonempty array of nonempty strings	Explanation of the final decision


dispatch_before is a required UTC timestamp only when decision: allow; it MUST be absent for deny.
Time ordering is:
- The gate was issued no later than checked_at.
- checked_at is no later than this record's created_at.
- For allow, created_at < dispatch_before.
A denied dispatch check may be recorded after gate expiration or the mission deadline as control-plane bookkeeping. It authorizes no additional agent work or action.
5.1 Authorization check
authorization_check contains:
- status: active, expired, revoked, not_yet_valid, or unknown.
- scope_match: pass, fail, or unknown, for the exact proposed target, operation, parameters, and executor.
- evidence_refs: unique external evidence references; may be empty only for status: unknown.
- valid_from and valid_until: either both present or both absent. Both are required for active, expired, and not_yet_valid.
When validity bounds are present, valid_from < valid_until is required.
Declared status	Required time relationship at checked_at
active	valid_from <= checked_at < valid_until
expired	checked_at >= valid_until
not_yet_valid	checked_at < valid_from
revoked	Revocation evidence is required; time bounds alone do not override it
unknown	Authorization cannot be established; execution is denied


allow requires active and scope_match: pass. A nonempty evidence reference is not proof of valid authority. The deployment must resolve evidence through trusted authorization sources, validate its integrity, and establish applicable revocation status. A bundle-supplied fixture registry MUST NOT grant authority.
For an allow decision:
dispatch_before <= authorization_check.valid_until
An invalid scope or unknown, expired, revoked, or not-yet-valid authorization MUST produce deny.
5.2 Target check
target_check contains:
- target_ref: exactly the action target.
- basis_observation_ref: a pre-execution observation referenced by the assessment and reviewed as reused or new evidence by the gate-bound review.
- expected_state: {kind, value}, identical to that observation's target_state.
- current_state: {kind, value}, obtained by the enforcing runtime.
- result: match, changed, or unknown.
- evidence_refs: unique external evidence references; nonempty for match or changed.
For known states, compare both kind and value. match requires structural equality and neither state may have kind: unknown. changed requires two known, comparable states of the same kind with different values. Incomparable state kinds or an unknown state require result: unknown.
allow requires match. A changed or unknown target state requires deny and a held closure. This final runtime check does not constitute a new scout observation or a new deliberation cycle.
Deployments must choose a state token covering the mutable prerequisites that affect the action. Equality of an unrelated or incomplete token cannot establish that all prerequisites hold.
5.3 Named checks and resources
checks has exactly these required keys, each with pass, fail, or unknown:
- reference_integrity
- review_passed
- authorization_valid
- scope_match
- observation_fresh
- target_state_match
- budgets_available
- deadline_valid
- stop_conditions_clear
- operation_available
These use the same meanings as gate checks. The structured authorization and target results MUST agree with the corresponding named checks. For authorization status unknown, authorization_valid is unknown; it is fail for expired, revoked, or not-yet-valid status. Target result match, changed, or unknown maps to pass, fail, or unknown respectively. The scope_match values must be identical.
allow requires every named check to pass. A deny decision MUST identify at least one failed or unknown check. Each assessed prerequisite must remain enforced by the runtime; a generic pass label is not a substitute for executing its check.
Resource IDs must exactly cover the mission budgets. Cumulative used values MUST NOT decrease from the gate record. For allow, used + reserved <= limit is required for every budget, with enough resources reserved for execution, verification, and closure bookkeeping.
A deny record MAY report an already exceeded budget. This reports a violation or overrun instead of permitting more work. Closure still requires control-plane capacity and preserves the measured usage.
6. Execution binding and freshness
Each execution record adds required dispatch_check_ref, referring to the mission's preceding allow dispatch check.
The execution, dispatch check, gate, and assessment MUST bind the same exact action and mission operation ID. Gate and dispatch-check references cannot be substituted merely because two actions appear similar.
Dispatch must satisfy all of the following:
- It occurs no earlier than dispatch-check record creation.
- It occurs strictly before dispatch_before, gate valid_until, authorization valid_until, and the mission deadline.
- The dispatch-check age is nonnegative and at most max_dispatch_check_age_seconds.
- Every observation used by the assessment still meets max_observation_age_seconds at dispatch.
- The runtime has atomically reserved the logical operation and prevents duplicate dispatch.
For an allow dispatch check:
dispatch_before <= min(gate.valid_until, authorization.valid_until, mission.deadline_at, checked_at + max_dispatch_check_age_seconds)
Time comparisons use parsed instants, preserving fractional precision. Equality at an expiration boundary is too late to dispatch.
The runtime MUST also ensure that mutable prerequisites remain valid through dispatch using conditional execution, locking, or an equivalent mechanism. A fresh record alone does not close the gap between checking and acting. If that guarantee cannot be established, the action must be held.
If dispatch was authorized but its check expired before use, close as held without dispatch. Do not create a second check or reuse the old one. If reservation or dispatch status is uncertain, preserve the reservation and use execution_status: uncertain rather than guessing that nothing happened.
7. Closure reason codes
Every closure adds required reason_codes: a nonempty array of unique values from this table.
Code	Meaning
verified_result	A succeeded receipt and completed verification support completion
review_limit_reached	No further review is allowed and blocking issues remain
deadline_reached	Required work or dispatch cannot proceed within the deadline
resource_limit_reached	Required work cannot be admitted within the resource limits
authorization_expired	Authorization expired before permitted dispatch
authorization_revoked	Authorization was revoked
authorization_not_yet_valid	Authorization is not yet effective
authorization_unknown	Authorization could not be established
authorization_scope_mismatch	The exact action or executor is outside the grant
target_state_changed	Target state differs from the reviewed basis
target_state_unknown	Required target state cannot be established
dispatch_check_expired	A passing final check expired before dispatch
execution_outcome_unknown	The recorded execution attempt has no established outcome
reservation_unresolved	A reservation exists but dispatch status is uncertain
verification_incomplete	Outcome verification could not be completed
expected_result_not_met	Verification found that an expected result was not met
unresolved_blocking_issue	A blocking issue remains unresolved
gate_denied	The initial execution gate denied the action
dispatch_check_denied	The final execution check denied dispatch
stop_condition_triggered	A defined stop condition was confirmed
explicit_stop	The controller explicitly stopped the mission


Completed closure MUST use exactly ["verified_result"]. Held closure MUST NOT include verified_result, stop_condition_triggered, or explicit_stop. Stopped closure MUST include stop_condition_triggered or explicit_stop, and MUST NOT include verified_result.
Multiple blocking reasons may coexist. Reason codes do not waive the underlying checks; basis_refs must reference records supporting the disposition and reasons. Timestamp-based expiry may be established by the closure timestamp together with the referenced gate, authorization bounds, or dispatch check.
For denied dispatch checks, include dispatch_check_denied and every applicable specific authorization or target-state reason evident from that check. If review exhaustion and an unresolved blocker coincide, include both review_limit_reached and unresolved_blocking_issue.
An unknown execution outcome requires execution_outcome_unknown; a stopped disposition may additionally record an explicit stop or triggered stop condition. An unresolved reservation requires reservation_unresolved and the reservation reference. If no execution occurred, verification need not exist; absence of unnecessary verification is not verification_incomplete.
An execution receipt reporting unknown remains unknown even if a later snapshot shows the desired state. In v0.2, preserve the attempt record and close as held, or stopped when independently required. Reconciliation and further action require a new mission; this specification does not authorize automatic retry.
8. State-flow changes
The transition from readiness to execution now includes a final checkpoint:
Current stage	Condition	Next stage
Reviewed readiness	Gate denies	Held closure
Gate allows	Dispatch check denies	Held closure, or stopped if independently required
Gate allows	Dispatch check allows and remains valid through dispatch	One execution attempt
Dispatch check allows	It expires before use	Held closure without dispatch
Execution attempted	Outcome cannot be established	Held verification/closure, or stopped if independently required
Outcome verification	All completion requirements hold	Completed closure


The final permitted review may pass and proceed to the gate. Reaching the review count alone is not a failure; reaching it with unresolved execution-blocking issues prevents further progress.
No deny, hold, or stop can be overridden by another agent vote. No terminal mission may reopen. A valid hold or stop is a conforming outcome.
9. Required v0.2 fixtures
New fixture files will be placed under examples/v0.2/pass/ and examples/v0.2/fail/. These directories do not exist yet as part of this specification step.
Positive scenarios must include completed execution with a final check, resolution after additional observation, a hold at the review limit, denied dispatch for changed target state, expired/revoked/unknown authorization, expired final check, a held unknown outcome, and a held mission when deadline or resource limits prevent required work.
Negative scenarios must include missing final check, execution after a denied check, action substitution, contradictory active/expired authorization times, dispatch after expiry, false target-state match, unresolved issue silently dropped during revision, duplicate dispatch/check records, and unknown outcome declared completed.
For each blocked positive scenario, provide a paired negative case that ignores the same blocker. This distinguishes the protocol's ability to record a correct stop from its ability to reject an invalid continuation.
10. Delivery and compatibility
The planned additions are:
1. specs/tacp-v0.2.md — this document.
2. schemas/tacp-v0.2.schema.json — version-specific structural rules.
3. Individual fixture files under examples/v0.2/pass/ and examples/v0.2/fail/.
4. An update to scripts/validate.py that explicitly selects the matching version's schema and semantic rules.
5. An update to .github/workflows/validate.yml that exercises both versions.
The existing schemas/tacp-v0.1.schema.json, examples/pass/, and examples/fail/ remain the v0.1 baseline. Existing v0.1 test results do not imply v0.2 support. The current validator must continue to reject unsupported version declarations until support is implemented.
Version 0.2 is ready for a release decision only after its schema, fixtures, and semantic checks are implemented, both version suites pass, and the human maintainer reviews the results. No release tag or GitHub publication is performed by this document.
A correct hold is a successful control outcome. A recorded permission is still a claim that the runtime must enforce.
