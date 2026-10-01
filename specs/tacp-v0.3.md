TACP v0.3 — Human-Reviewed Recovery and Mission Handoff
Protocol: Triadic Agent Control Protocol
Protocol version: 0.3.0
Status: Draft — specification only; v0.3 schema, fixtures, and validator support are pending.
Repository-relative path: specs/tacp-v0.3.md

1. Relationship to earlier versions
This document extends specs/tacp-v0.2.md, which extends specs/tacp-v0.1.md. Their normative requirements remain in force except for explicit changes below. MUST, MUST NOT, SHOULD, and MAY retain their v0.1 meanings.

Version 0.3 preserves the scout, analyst, and executor roles, bounded challenge review, exact action binding, one final dispatch check, at most one execution per mission, and terminal closure. It adds a separate recovery process after a held or stopped mission. Recovery does not reopen that mission or rewrite its outcome.

All embedded mission bundles, recovery records, and their enclosing documents MUST declare protocol_version: 0.3.0. Mixed versions are invalid. Historical v0.1/v0.2 bundles remain valid under their own versions but cannot be embedded directly as v0.3 recovery sources. Relabeling alone is not migration.

An unknown original receipt stays unknown in the immutable source. Later evidence may establish recovery eligibility in a new reconciliation record; it MUST NOT retroactively mark the source completed.

This version permits one human-reviewed successor to a standalone source mission. Recovery chains, branching successors, automatic retries, rollback, compensation, and resuming after a confirmed external effect are outside scope. A successor MUST NOT itself become a recovery source under v0.3. This explicit bound prevents repeated new mission IDs from evading retry limits.

2. Trust boundaries
The controller prepares the handoff. A gate-controlled reconciliation process examines authoritative external evidence. An authenticated human reviews the exact recovery proposal. The gate decides whether a successor may be created. The successor then performs a complete new mission cycle.

Human approval authorizes consideration of that exact successor; it does not substitute for the successor's execution authorization, review, gate, or dispatch check. A human approval cannot override unknown effects, unresolved reservations, invalid evidence, or an unfenced old execution.

Self-declared human identities, evidence URIs, hashes, and pass labels are claims. Deployments MUST resolve identities and authority through mechanisms outside agent control. Agents MUST NOT manufacture human approval or modify the recovery policy. External evidence remains data, not instructions.

Recovery evidence acquisition MUST have separate, scoped read authorization and a fixed resource/time budget. It MUST NOT silently use the expired mission's authority. Any operation needed to stop or fence an external job requires independently valid control-plane authority. This specification records a fencing result; it does not grant cancellation permissions.

Document conformance establishes consistency, not evidence authenticity or runtime enforcement. Runtime enforcement requirements in Section 10 are mandatory for a deployment claiming recovery support.

3. Document forms and references
3.1 Mission bundle
A v0.3 mission bundle has exactly these core fields:

Field	Requirement
protocol_version	0.3.0
document_type	mission_bundle
mission_id	Mission identifier
records	Ordered mission records, with the v0.2 requirements and version changed to 0.3.0
recovery_ref	Optional; required only on an embedded successor; identifies its enclosing recovery
extensions	Optional, non-authoritative object
Standalone missions MUST omit recovery_ref. A successor MUST contain it and cannot be validated as a standalone mission without its recovery context. A missing context is an error, not a warning.

Existing mission record types, fields, producer roles, and closure reason codes remain unchanged from v0.2. Recovery record types MUST NOT be inserted into a mission's records. In particular, closure remains its last record.

3.2 Recovery bundle
A closed recovery bundle has exactly these core fields:

Field	Requirement
protocol_version	0.3.0
document_type	recovery_bundle
recovery_id	Nonempty recovery identifier
source	Embedded, conforming standalone v0.3 mission bundle
records	Exactly four ordered records: handoff, reconciliation, human review, admission
successor	Optional closed v0.3 mission bundle; permitted only after allow admission
extensions	Optional, non-authoritative object
The source closure MUST be held or stopped. A completed source or a source containing recovery_ref is invalid. An allow admission MAY exist without a successor: admission is permission to create one, not proof that it was created. A deny admission MUST NOT have a successor.

Recovery records use this common envelope: protocol_version, record_type, record_id, recovery_id, created_at, producer_id, and producer_role. The new types are handoff, reconciliation, human_review, and recovery_admission. They do not contain mission_id. Roles are controller, gate, human, and gate respectively. The human role is permitted only on human_review; it is not a new agent role.

All IDs for recovery records and records in the source and successor MUST be unique across the enclosing recovery document. Mission IDs MUST differ; operation identity continuity is specified in Section 5. Times are UTC instants with fractional precision preserved. Record creation times MUST be nondecreasing in order.

Ordinary mission references remain local to their mission. Cross-boundary references are permitted only in fields explicitly defined here. source_*_ref fields resolve in source.records; recovery record references resolve to preceding entries of recovery records; recovery_ref resolves to the enclosing recovery_id. External authority/evidence references MUST NOT alias any internal record ID. Reference arrays contain unique nonempty strings.

All fields listed below are required unless marked optional or conditional. Objects have only their listed core fields plus an optional extensions object. Integers and numeric resource values MUST be finite; duplicate JSON object members are invalid.

4. Handoff record
The controller issues handoff after source closure. Required fields:

Field	Type and meaning
source_mission_ref	Source mission record ID
source_closure_ref	Source closure record ID
source_operation_id	Exact source mission operation ID
source_reason_codes	Exact ordered copy of source closure reason codes
source_execution_ref	Required iff a source execution record exists
source_reservation_ref	Required iff source execution or closure records a reservation; must equal every such reference
issue_carryover	Array of objects defined below; may be empty
candidate	Exact proposed successor template, Section 5
recovery_policy_ref	Immutable external policy snapshot
read_authorization_ref	External authority for reconciliation evidence access
control_authorization_ref	External authority for any runtime fencing; optional when no fencing action is needed
limits	Fixed recovery limits defined below
reason	Nonempty explanation of the proposed recovery
An issue carryover object contains issue_id, source_record_ref, and blocks_execution. Include exactly all currently open tracked issues after replaying source assessments and review updates using v0.2 rules. The reference identifies the latest explicit record defining that issue's state. Omission from a later assessment is not resolution. Preserve IDs and flags, including nonblocking open issues. Natural-language closure reasons are preserved separately and MUST be reviewed even if they have no issue ID.

limits contains deadline_at, max_evidence_age_seconds, and resource_budgets. Deadline MUST follow handoff creation; maximum evidence age is a positive integer. Budgets use the v0.1 {budget_id, unit, limit} shape with positive finite limits and unique IDs. They are separate from the source and successor budgets. Recovery policy MUST also authorize the combined resource exposure; creating a new budget is not an implicit grant of more resources.

5. Exact successor candidate and operation identity
candidate has mission_id, operation_id, objective, observation_scope, authorization_ref, policy_ref, limits, expected_results, and stop_conditions. Apart from the identifier rule below, these fields have the same types and constraints as the corresponding v0.2 mission fields. This is a template, not a mission record; it has no record envelope or creation time.

The candidate mission ID is new and MUST differ from the source ID. The operation ID MUST equal the source operation ID. In v0.3 this operation ID remains the stable deduplication identity across the bounded recovery pair. A new mission ID MUST NOT hide a repeated logical operation under a new operation ID.

The candidate objective, observation scope, expected results, and stop conditions MUST be structurally equal to those of the source. Recovery here attempts the same objective. A different business objective belongs outside this recovery profile and MUST NOT be used to evade a pending operation's lock.

The candidate authorization reference MUST identify a new immutable authorization snapshot and MUST differ from the source authorization reference. The policy reference MAY remain the same if the policy explicitly permits this recovery. Candidate limits are fixed before human approval; any change requires a different proposal and new human review, never an in-place edit.

The action is not copied as permission. Fresh observations, assessment, and challenge review in the successor establish its action, which may need new state-dependent parameters. Its own authorization, gate, and final check must cover that exact action. Identity equivalence, policy adequacy, and authorization scope require runtime review as well as document comparisons.

6. Reconciliation record
Required fields:

Field	Meaning
handoff_ref	Preceding handoff
checked_at	Time evidence was evaluated
status	One of the four values below
execution_finality	terminal or unknown
reservation_status	none, released, consumed, or unresolved
fence_status	enforced or unknown
evidence	Nonempty array of evidence objects
resource_usage	Cumulative recovery budget usage and reserved capacity
reason	Nonempty explanation, including conflicts or limitations
Each evidence object contains evidence_ref, issuer_ref, observed_at, and kind. Kinds are dispatch_ledger, operation_receipt, effect_audit, reservation_ledger, fence_receipt, target_snapshot, and lookup_failure. References are external and unique within this array. A lookup_failure records an unsuccessful lookup and can support only uncertainty, never a confirmed conclusion. Source closure time MUST be no later than each evidence observed_at, which MUST be no later than checked_at; checked_at <= created_at. Evidence age at admission MUST be within max_evidence_age_seconds.

Status	Required conclusion and evidence
confirmed_not_dispatched	No dispatch occurred and none can occur later; requires dispatch ledger, reservation ledger, and fence receipt
confirmed_no_effect	Dispatch occurred, is terminal, and produced no external effect; requires operation receipt, effect audit, reservation ledger, and fence receipt
confirmed_effect	An attributable external effect is established; requires operation receipt and effect audit; never permits a successor in v0.3
unresolved	Dispatch, effects, finality, reservations, or conflicts cannot be conclusively resolved; never permits a successor
The first two statuses require execution_finality: terminal, fence_status: enforced, and reservation status none or released. confirmed_no_effect requires released, because a dispatched attempt must have had an operation reservation. If a source reservation reference exists, none is invalid for any status; an eligible reconciliation must establish its release. consumed or unresolved reservations prevent recovery admission.

A source execution receipt, even a failed or unknown one, proves a recorded attempt: it prohibits confirmed_not_dispatched. A source succeeded receipt prohibits both eligibility statuses; use confirmed_effect when effect is established or unresolved when evidence conflicts. Missing execution records do not prove no dispatch when source closure reports uncertainty. Conversely, a source closure saying not_dispatched conflicts with evidence of dispatch; such conflict requires unresolved, not silent correction.

An unknown receipt may later support confirmed_no_effect only with authoritative finality and effect evidence. A failed receipt alone is insufficient: failure may follow a partial effect. A target snapshot showing the desired value or its original value does not establish causation, absence of transient effects, or termination. Target snapshots alone cannot support any confirmed status.

Fencing means that all old queued, in-flight, scheduled, or replayable work is durably prevented from producing a future effect. It is not merely a timeout, cancellation request, or lock expiration. An effective fence must survive until the old work is permanently unable to act. If that guarantee cannot be established, use unresolved. Absence of a receipt or failure to contact a service MUST NOT be interpreted as no effect.

These are requirements for evidence interpretation, not claims that JSON Schema can verify external truth. An evidence kind label alone does not satisfy the runtime requirement.

7. Human-review record
Required fields are handoff_ref, reconciliation_ref, reviewer_ref, reviewer_authority_ref, decision, reviewed_at, valid_until, evidence_refs, and reason.

Decision is approve, hold, or reject. Evidence references are a nonempty array of external human-review receipt references. The reviewer identity and authority MUST resolve to an authenticated human authorized under recovery policy. producer_id identifies that human; an agent or controller cannot substitute its own identity.

Reconciliation creation MUST be no later than reviewed_at, and reviewed_at <= created_at < valid_until. Human review MUST precede the recovery deadline. Review is bound to the exact immutable handoff and reconciliation, including candidate IDs, candidate fields, carryover issues, and evidence. Approval is single-use, revocable, and expires at valid_until.

approve is permitted only for confirmed_not_dispatched or confirmed_no_effect with all eligibility requirements satisfied. Other statuses require hold or reject. Approval does not resolve carried issues or authorize ignoring a stopped source. For a stopped source, the human reason MUST explicitly address why further work under a new mission is acceptable; runtime policy MUST independently permit it.

A hold or reject cannot be overridden by a later gate decision. v0.3 permits one review per recovery bundle. A changed proposal needs a new recovery identifier and an independently validated approval, while retaining the same source and operation deduplication protection.

8. Recovery-admission record
Required fields are handoff_ref, reconciliation_ref, human_review_ref, checked_at, decision, checks, resource_usage, reason_codes, and reason.

checks has exactly these keys, each pass, fail, or unknown:

reference_integrity
source_terminal
reconciliation_eligible
evidence_fresh
human_approval_valid
recovery_policy_valid
read_authorization_valid
old_operation_fenced
reservation_resolved
successor_unique
budgets_available
deadline_valid
Human review creation MUST be no later than checked_at <= created_at. Decision is allow or deny. Allow requires all checks pass and all substantive requirements in this document. Deny requires at least one failed or unknown check.

For allow only, require start_before and claim_ref. The latter references an external atomic single-use claim for this source closure, recovery, operation, and candidate mission. Time must satisfy:

created_at < start_before <= min(human_review.valid_until, handoff.limits.deadline_at, candidate.limits.deadline_at, each evidence.observed_at + max_evidence_age_seconds)

For deny, both fields MUST be absent and no successor may exist. Admission may record denial after expiration as control-plane bookkeeping. It cannot authorize more evidence acquisition or agent work after the deadline.

Reason codes are unique and nonempty. Allow uses exactly ["successor_admitted"]. Deny excludes that code and includes every applicable code mapped from a non-pass check:

Check	Denial code
reference_integrity	reference_invalid
source_terminal	source_ineligible
reconciliation_eligible	reconciliation_ineligible
evidence_fresh	evidence_stale_or_unknown
human_approval_valid	human_approval_invalid
recovery_policy_valid	recovery_policy_invalid
read_authorization_valid	read_authorization_invalid
old_operation_fenced	old_operation_unfenced
reservation_resolved	reservation_unresolved
successor_unique	successor_conflict
budgets_available	resource_limit_reached
deadline_valid	deadline_reached
These are recovery-admission codes, not additions to mission closure codes. Fail/unknown claims may be conservative; a pass MUST NOT contradict structured facts. In particular, non-approved or expired human review, an ineligible reconciliation, or nonterminal source cannot be labeled pass.

Recovery resource_usage uses {budget_id, used, reserved}, exactly covering handoff budgets. Usage is cumulative from recovery initiation and MUST NOT decrease from reconciliation to admission. Reserved capacity covers required remaining control-plane work. An allow requires used + reserved <= limit. A deny may report an overrun but MUST preserve actual usage and must not claim capacity for successor work. The admission is terminal bookkeeping for this recovery; later mission accounting belongs to the successor's fixed budgets.

9. Successor mission requirements
An embedded successor requires an allow admission and matching recovery_ref. Its mission record MUST copy every candidate field exactly, with a normal v0.3 mission envelope. Admission creation MUST be no later than successor mission creation, which MUST be strictly before start_before. Runtime claim consumption, approval revocation, fencing, and policy MUST be rechecked atomically at creation; a previously valid admission alone is insufficient.

The successor MUST acquire fresh scoped observations after its creation. Source records and reconciliation evidence cannot substitute for the successor's required observation records. Old evidence may be cited as historical context only when permitted by scope and policy; reuse is not independent corroboration.

The successor's first assessment MUST include every issue_carryover ID with its carried blocking flag in open_issues. These issues initialize its tracked issue state. They cannot be resolved by omission or by initial human approval. A blocking carried issue requires a later assessment revision and an explicit evidenced resolution in that revision's first review, following v0.2 rules. New issues may also be added.

The successor must independently pass challenge review, initial gate, and its one final dispatch check. Its action and execution bindings follow v0.2. It may itself close held or stopped; approval does not promise completion. Source records, limits, and closure remain unchanged.

If the source had an operation reservation, the successor execution MUST use a new reservation reference. No consumed or unresolved old reservation can be reused. A new reservation remains bound to the stable operation ID and the successor mission ID in the runtime ledger.

10. Cross-mission enforcement
The runtime MUST maintain a durable authoritative registry keyed by stable operation identity and source closure. It MUST:

Preserve the original dispatch count, reservation state, receipts, and fences.
Prevent concurrent live recovery claims and admit at most one successor mission for a source closure, including across separate documents or processes.
Atomically consume the human-approved claim at successor creation, rejecting duplicate creation even after process restart.
Permit a successor reservation only after the old attempt is conclusively non-dispatched or terminal without effect and unable to act later.
Bind a successor reservation to its mission and permit at most one dispatch from that reservation.
Keep total dispatches within this profile at two: at most one source attempt and at most one approved successor attempt. A source with no dispatch allows only the successor attempt.
A claim may expire unused and a new proposal may be reviewed only after the registry conclusively establishes that no successor was created. Unknown claim consumption blocks another claim. Creation permanently consumes the source's successor allowance even if the successor never dispatches. Renaming IDs or repackaging a successor as a standalone source MUST NOT bypass this lineage rule.

Runtime revocation or a broken fence after admission must block successor creation or dispatch. Recovery permission does not supersede normal dispatch-time authorization. Conditions that cannot be kept valid atomically through action must cause a hold.

A single JSON document cannot demonstrate global uniqueness. Offline validation MUST report its scope as document consistency; it MUST NOT claim that cross-document deduplication, human identity, fencing, or authorization were enforced.

11. Conformance and required fixtures
Validation has three distinct layers: structural schema validation; deterministic semantic checks over records and embedded bundles; and deployment enforcement of external truth and authority. A v0.3 validator MUST validate both embedded missions, reference order, temporal boundaries, exact candidate copying, issue carryover, reconciliation compatibility, admission conditions, and local uniqueness. It MUST reject unsupported versions rather than falling back to an earlier schema.

Required positive scenarios under examples/v0.3/pass/:

Ordinary completed mission without recovery.
Held source confirmed not dispatched, approved successor, verified completion.
Unknown source outcome conclusively terminal without effect, old reservation released and fenced, approved successor with a new reservation.
Unresolved reconciliation followed by human hold and denied admission, without successor.
Confirmed effect followed by denied admission, without successor.
Human rejection, expired approval, stale evidence, and exhausted recovery resources, each correctly denying admission.
Carried blocker explicitly resolved through a successor assessment revision and evidenced review.
Approved successor correctly held by its own authorization or target-state check.
Required negative scenarios under examples/v0.3/fail/:

Source reopened, edited, completed, or already a successor.
Unknown outcome or target snapshot alone treated as no effect.
Claimed no dispatch despite a source execution receipt.
Missing fence, unresolved reservation, or reuse of an old reservation.
Approval claimed by an agent, missing human review, or approval of ineligible reconciliation.
Successor after deny, at the exclusive start deadline, or with expired approval.
Changed candidate fields, changed operation ID, or missing recovery context.
Carried blocker omitted, renamed, downgraded, or silently resolved.
Missing fresh successor observation, review, gate, or final check.
Duplicate successor creation, duplicate claim consumption, or hidden recovery chain.
External identity, evidence authenticity, revocation, and cross-document races require runtime integration tests with a controlled registry and authority service; static fixtures alone cannot prove those properties. For mechanically detectable blockers, include paired accept/reject fixtures and assert the intended diagnostic rather than accepting any failure.

12. Delivery and release boundary
Deliverables are created individually, in this order:

specs/tacp-v0.3.md — this draft.
schemas/tacp-v0.3.schema.json — version-specific document forms and structural constraints.
Individual fixtures under examples/v0.3/pass/ and examples/v0.3/fail/.
scripts/validate.py — explicit v0.3 semantic support and diagnostic expectations while retaining v0.1/v0.2 behavior.
.github/workflows/validate.yml — exercise every supported version and required validation checks.
This specification does not claim that those later deliverables exist or pass. Existing v0.1/v0.2 results do not establish v0.3 support. Earlier-version fixture coverage gaps remain separate release-review items; adding this draft does not waive them. Human maintainer review and implemented conformance checks are required before a v0.3 release decision. No release tag, repository publication, or real external action is pe
