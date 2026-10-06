#!/usr/bin/env python3
"""Validate TACP v0.1/v0.2 missions and v0.3 mission/recovery bundles (Python 3.10+).

Dependency: python -m pip install "jsonschema>=4.18,<5"

From the repository root:
  python scripts/validate.py
  python scripts/validate.py --examples --json
  python scripts/validate.py --version 0.3.0
  python scripts/validate.py examples/pass/mission-completed.json
  python scripts/validate.py examples/fail/stale-observation.json --json

No positional paths runs all three version suites, including examples/v0.3.
The three external-state negatives run as explicitly labeled synthetic tests
with repaired positive controls; their documents alone are consistent. Pass
fixtures must be accepted and negative tests must detect their intended error.
Use --version 0.3.0 for one suite. Direct file mode checks document consistency
only and requires acceptance, even for files in a directory named fail.
Exit codes: 0 = all expectations met; 1 = validation/expectation failure;
2 = dependency, schema, file-reading, or command configuration error.

The schema is resolved relative to this script, not the working directory.
All schema references must be local fragments; no network requests are made.
JSON duplicate keys, non-finite numbers, and invalid UTC dates are rejected.
Decimal numbers and timestamp fractions are compared without float rounding.

Scope: structural and mechanically checkable record-consistency requirements in
specs/tacp-v0.1.md through specs/tacp-v0.3.md. Natural-language evidence quality, materiality, independence,
issue classification, explicit stop rationale, actual external authorization,
live target state, and actual runtime enforcement require separate assessment.
External references are opaque; extensions (including fixture registries and
expected_validation) never grant authority or influence document validation.
Only repository example mode reads mock state for the three named runtime tests.
No human identity, archive authenticity, permanent fence, revocation, or atomic
cross-document claim/lineage enforcement is established by this offline tool.
This program neither dispatches actions nor certifies that a deployment is safe.
"""

from __future__ import annotations

import argparse
import calendar
import copy
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any
from urllib.parse import unquote

try:
    from jsonschema import Draft202012Validator, FormatChecker, validators
    from jsonschema.exceptions import SchemaError
except ImportError:
    print('Missing dependency: run python -m pip install "jsonschema>=4.18,<5"', file=sys.stderr)
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {v: ROOT / f"schemas/tacp-v{v[:3]}.schema.json" for v in ("0.1.0", "0.2.0", "0.3.0")}
DEFAULT_SCHEMA = SCHEMAS["0.1.0"]
UTC_PATTERN = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]+))?Z$")
LIMITATIONS = (
    "Record consistency only; no runtime enforcement or external authorization verification. "
    "Natural-language evidence, independence, issue classification, material changes, and "
    "controller stop rationale require separate assessment. Human identity, source archives, "
    "permanent fences, revocation, and atomic cross-document deduplication are not verified. "
    "Extensions are not trusted evidence; example-mode runtime fixtures are synthetic tests only."
)
# These expectations are test-harness data, not supplied by the bundle under test.
KNOWN_FAILURES = {
    "missing-challenge-review.json": "missing_challenge_review",
    "stale-observation.json": "stale_observation",
    "action-mismatch.json": "action_mismatch",
    "duplicate-execution.json": "duplicate_execution",
    "completed-without-verification.json": "completed_without_verification",
    "unknown-outcome-completed.json": "unknown_outcome_completed",
}

KNOWN_FAILURES_V02 = {
    "action-mismatch.json": "action_mismatch",
    "authorization-active-outside-validity.json": "authorization_time",
    "authorization-unknown-but-executed.json": "execution_dispatch_denied",
    "duplicate-dispatch-check.json": "duplicate_dispatch_check",
    "duplicate-execution.json": "duplicate_execution",
    "false-target-state-match.json": "target_state_result_mismatch",
    "missing-dispatch-check.json": "missing_dispatch_check",
    "expired-dispatch-check.json": "expired_dispatch_check",
    "authorization-expired-at-dispatch.json": "authorization_expired_at_dispatch",
    "target-state-changed-but-executed.json": "execution_dispatch_denied",
    "unresolved-blocking-issue-but-executed.json": "unresolved_blocking_issue",
    "unknown-outcome-completed.json": "unknown_outcome_completed",
}


class InputError(ValueError):
    """Invalid JSON representation, rather than a schema/configuration error."""


def strict_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise InputError(f"Duplicate JSON member: {key!r}")
        result[key] = value
    return result


def forbidden_constant(value: str) -> Any:
    raise InputError(f"Non-finite JSON number: {value}")


def read_json(path: Path) -> Any:
    # Decimal prevents distinct action parameters from collapsing to one float.
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs,
                      parse_float=Decimal, parse_constant=forbidden_constant)


def instant(value: str) -> Fraction:
    match = UTC_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("Expected a UTC timestamp ending in Z")
    whole = datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%S")
    fraction = Fraction("0." + match[2]) if match[2] else Fraction(0)
    return Fraction(calendar.timegm(whole.timetuple())) + fraction


FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=(ValueError, OverflowError))
def valid_utc(value: Any) -> bool:
    if not isinstance(value, str):
        return True  # The schema's type check handles non-strings.
    instant(value)
    return True


def is_number(_checker: Any, value: Any) -> bool:
    return (type(value) is int or isinstance(value, Decimal) and value.is_finite())


def is_integer(checker: Any, value: Any) -> bool:
    return is_number(checker, value) and value == int(value)


JSONValidator = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine_many(
        {"number": is_number, "integer": is_integer}),
)


def json_equal(left: Any, right: Any) -> bool:
    """Structural JSON equality; booleans are not numbers, and strings are not coerced."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is bool and type(right) is bool and left == right
    if is_number(None, left) and is_number(None, right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    return left == right


def pointer(parts: Any) -> str:
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)


@dataclass(frozen=True)
class Diagnostic:
    layer: str
    code: str
    path: str
    message: str


class SemanticValidator:
    """Only called after full structural validation succeeds."""

    def __init__(self, bundle: dict[str, Any]):
        self.v02 = bundle["protocol_version"] in {"0.2.0", "0.3.0"}
        self.bundle = bundle
        self.records = bundle["records"]
        self.mission = self.records[0]
        self.deadline = instant(self.mission["limits"]["deadline_at"])
        self.index: dict[str, int] = {}
        self.errors: list[Diagnostic] = []
        self.budgets = {x["budget_id"]: x["limit"] for x in self.mission["limits"]["resource_budgets"]}
        self.last_usage: dict[str, Any] = {}

    def error(self, code: str, i: int, field: str, message: str) -> None:
        path = f"/records/{i}" + ("/" + field if field else "")
        item = Diagnostic("semantic", code, path, message)
        if item not in self.errors:
            self.errors.append(item)

    def require(self, ok: bool, code: str, i: int, field: str, message: str) -> None:
        if not ok:
            self.error(code, i, field, message)

    def resolve(self, rid: str, i: int, field: str,
                kinds: tuple[str, ...] | None = None, phase: str | None = None) -> dict[str, Any] | None:
        j = self.index.get(rid)
        if j is None:
            self.error("missing_reference", i, field, f"No record resolves {rid!r}.")
            return None
        row = self.records[j]
        self.require(j < i, "reference_order", i, field, f"Reference {rid!r} must precede this record.")
        if kinds and row["record_type"] not in kinds:
            self.error("reference_type", i, field, f"Reference {rid!r} must have type in {kinds}.")
            return None
        if phase and row.get("phase") != phase:
            self.error("observation_phase", i, field, f"Reference {rid!r} must be {phase}.")
            return None
        self.require(instant(row["created_at"]) <= instant(self.records[i]["created_at"]),
                     "reference_time", i, field, "A referenced record cannot have been issued later.")
        return row

    def unique(self, rows: list[dict[str, Any]], key: str, i: int, field: str) -> set[str]:
        ids = [x[key] for x in rows]
        self.require(len(ids) == len(set(ids)), "duplicate_identifier", i, field,
                     f"{key} values must be unique within this collection.")
        return set(ids)

    def coverage(self, rows: list[dict[str, Any]], key: str, wanted: set[str],
                 i: int, field: str) -> None:
        actual = self.unique(rows, key, i, field)
        self.require(actual == wanted, "identifier_coverage", i, field,
                     f"Expected identifiers {sorted(wanted)!r}; found {sorted(actual)!r}.")

    def usage(self, row: dict[str, Any], i: int, final: bool = False) -> None:
        entries = row["resource_usage"]
        self.coverage(entries, "budget_id", set(self.budgets), i, "resource_usage")
        for entry in entries:
            bid = entry["budget_id"]
            if bid not in self.budgets:
                continue
            used = Fraction(entry["used"])
            self.require(used >= Fraction(self.last_usage.get(bid, 0)), "resource_usage_decreased",
                         i, "resource_usage", f"Cumulative use for {bid!r} decreased.")
            self.last_usage[bid] = entry["used"]
            # Held/stopped closure may truthfully report in-flight overruns.
            if (not final and not (self.v02 and row.get("decision") == "deny")) or (final and row["disposition"] == "completed"):
                total = used + (Fraction(0) if final else Fraction(entry["reserved"]))
                self.require(total <= Fraction(self.budgets[bid]), "resource_limit_exceeded",
                             i, "resource_usage", f"Declared limit for {bid!r} is exceeded.")

    def freshness(self, assessment: dict[str, Any], at: str, i: int) -> None:
        limit = self.mission["limits"]["max_observation_age_seconds"]
        for rid in assessment["observation_refs"]:
            observation = self.resolve(rid, i, "assessment_ref", ("observation",), "pre_execution")
            if observation:
                age = instant(at) - instant(observation["observed_at"])
                self.require(0 <= age <= limit, "stale_observation", i, "assessment_ref",
                             f"Observation {rid!r} age is {age} seconds; allowed range is 0..{limit}.")

    def changed_state(self, assessment: dict[str, Any], after: int, until: int) -> None:
        baselines: dict[str, Any] = {}
        for rid in sorted(assessment["observation_refs"], key=lambda x: self.index.get(x, -1)):
            if rid in self.index:
                obs = self.records[self.index[rid]]
                if obs["record_type"] == "observation":
                    baselines[obs["target_ref"]] = obs["target_state"]
        for newer in self.records[after + 1:until]:
            if newer["record_type"] == "observation" and newer["phase"] == "pre_execution":
                baseline = baselines.get(newer["target_ref"])
                if baseline is not None:
                    self.require(json_equal(baseline, newer["target_state"]), "target_state_changed", until,
                                 "assessment_ref", "A later observation changed target state; renewed assessment and review are required.")

    def run(self) -> list[Diagnostic]:
        for i, row in enumerate(self.records):
            rid = row["record_id"]
            self.require(rid not in self.index, "duplicate_record_id", i, "record_id", "Record ID already exists.")
            self.index.setdefault(rid, i)
            self.require(row["mission_id"] == self.bundle["mission_id"], "mission_mismatch", i,
                         "mission_id", "Record mission differs from bundle mission.")
            self.require(instant(row["created_at"]) >= instant(self.mission["created_at"]),
                         "record_before_mission", i, "created_at", "Record was issued before the mission.")
        self.require(self.mission["record_id"] == self.bundle["mission_id"], "mission_mismatch", 0,
                     "record_id", "Mission record ID must equal the bundle mission ID.")
        self.require(self.records[-1]["record_type"] == "closure", "closure_not_last",
                     len(self.records) - 1, "record_type", "Closure must be the last record.")
        self.require(self.deadline > instant(self.mission["created_at"]), "invalid_deadline", 0,
                     "limits/deadline_at", "Deadline must follow mission creation.")
        self.unique(self.mission["limits"]["resource_budgets"], "budget_id", 0, "limits/resource_budgets")
        expected_ids = self.unique(self.mission["expected_results"], "condition_id", 0, "expected_results")
        stop_ids = self.unique(self.mission["stop_conditions"], "condition_id", 0, "stop_conditions")
        self.require(not expected_ids & stop_ids, "duplicate_identifier", 0, "stop_conditions",
                     "Expected-result and stop-condition IDs must be distinct.")

        latest_assessment = latest_review = latest_gate = execution = verification = None
        assessment_count = review_count = 0
        considered: set[str] = set()
        issues: dict[str, str] = {}
        previous_blockers: set[str] = set()
        pending_resolutions: set[str] = set()
        last_review_assessment: str | None = None
        terminal: str | None = None
        last_review_index = -1

        for i, row in enumerate(self.records):
            kind = row["record_type"]
            if kind == "mission":
                continue
            if terminal and kind != "closure":
                self.error("work_after_terminal_decision", i, "record_type",
                           f"Only closure is allowed after a {terminal} decision.")
            if execution and kind in {"assessment", "review", "gate"}:
                self.error("work_after_execution", i, "record_type", "No pre-execution planning is allowed after dispatch.")

            # Receipt and closure bookkeeping can report an attempt after the deadline.
            if kind in {"observation", "assessment", "review", "verification"}:
                self.require(instant(row["created_at"]) < self.deadline, "work_after_deadline", i,
                             "created_at", "Further agent work is prohibited at or after the deadline.")

            if kind == "observation":
                self.require(instant(row["observed_at"]) <= instant(row["created_at"]),
                             "observation_time", i, "observed_at", "Observation time follows record creation.")
                for source in row["sources"]:
                    self.require(instant(source["retrieved_at"]) <= instant(row["created_at"]),
                                 "source_time", i, "sources", "Source retrieval follows record creation.")
                if row["phase"] == "pre_execution":
                    self.require(execution is None, "work_after_execution", i, "phase",
                                 "Pre-execution observation cannot follow execution.")
                else:
                    receipt = self.resolve(row["execution_ref"], i, "execution_ref", ("execution",))
                    if receipt:
                        self.require(instant(row["observed_at"]) >= instant(receipt["finished_at"]),
                                     "post_observation_time", i, "observed_at", "Outcome observation predates the end of the attempt.")

            elif kind == "assessment":
                assessment_count += 1
                self.require(row["revision"] == assessment_count, "assessment_sequence", i, "revision",
                             "Assessment revisions must start at 1 and advance by one.")
                if latest_assessment:
                    self.require(last_review_assessment == latest_assessment["record_id"],
                                 "unreviewed_assessment_revision", i, "supersedes_ref",
                                 "Review the preceding assessment before advancing to another revision.")
                    self.require(row.get("supersedes_ref") == latest_assessment["record_id"],
                                 "assessment_predecessor", i, "supersedes_ref", "Must supersede the preceding assessment.")
                if "supersedes_ref" in row:
                    self.resolve(row["supersedes_ref"], i, "supersedes_ref", ("assessment",))
                for rid in row["observation_refs"]:
                    self.resolve(rid, i, "observation_refs", ("observation",), "pre_execution")
                considered.update(row["observation_refs"])
                self.require(row["action"]["operation_id"] == self.mission["operation_id"],
                             "operation_mismatch", i, "action/operation_id", "Action must retain the mission operation ID.")
                self.unique(row["prerequisites"], "prerequisite_id", i, "prerequisites")
                self.unique(row["open_issues"], "issue_id", i, "open_issues")
                blockers = {x["issue_id"] for x in row["open_issues"] if x["blocks_execution"]}
                pending_resolutions.update(previous_blockers - blockers)
                pending_resolutions.difference_update(blockers)
                previous_blockers = blockers
                for issue in row["open_issues"]:
                    issues[issue["issue_id"]] = "open"
                latest_assessment = row

            elif kind == "review":
                review_count += 1
                self.require(row["round"] == review_count, "review_sequence", i, "round",
                             "Review rounds must start at 1 and advance across the whole mission.")
                self.require(review_count <= self.mission["limits"]["max_review_rounds"],
                             "review_limit_exceeded", i, "round", "Review count exceeds the immutable mission limit.")
                assessment = self.resolve(row["assessment_ref"], i, "assessment_ref", ("assessment",))
                self.require(latest_assessment is not None and row["assessment_ref"] == latest_assessment["record_id"],
                             "review_assessment_mismatch", i, "assessment_ref", "Review must address the current assessment revision.")
                if latest_review:
                    self.require(row.get("previous_review_ref") == latest_review["record_id"],
                                 "review_predecessor", i, "previous_review_ref", "Must reference the preceding review.")
                    if row["decision_change"] == "retained":
                        self.require(row["decision"] == latest_review["decision"], "review_decision_change", i,
                                     "decision_change", "A retained decision cannot change its decision value.")
                    if row["decision"] == "pass" and latest_review["remaining_blocking_issues"]:
                        self.require(row["assessment_ref"] != latest_review["assessment_ref"],
                                     "issue_resolution_without_revision", i, "assessment_ref",
                                     "Resolving prior blocking issues requires an assessment revision.")
                if "previous_review_ref" in row:
                    self.resolve(row["previous_review_ref"], i, "previous_review_ref", ("review",))
                old, new = set(row["reused_observation_refs"]), set(row["new_observation_refs"])
                self.require(not old & new, "review_evidence_overlap", i, "new_observation_refs",
                             "Reused and new observations must be disjoint.")
                self.require(old <= considered and not new & considered, "review_evidence_classification", i,
                             "new_observation_refs", "Evidence classification differs from preceding assessments and reviews.")
                for rid in old | new:
                    self.resolve(rid, i, "observation_refs", ("observation",), "pre_execution")
                for check in row["checks_performed"] + row["issue_updates"]:
                    self.require(set(check["evidence_refs"]) <= old | new, "review_evidence_coverage", i,
                                 "checks_performed", "Review evidence must occur in its declared observation lists.")
                    for rid in check["evidence_refs"]:
                        self.resolve(rid, i, "evidence_refs", ("observation",), "pre_execution")
                self.unique(row["issue_updates"], "issue_id", i, "issue_updates")
                resolved = set()
                for update in row["issue_updates"]:
                    iid = update["issue_id"]
                    if update["status"] == "resolved":
                        self.require(iid in issues, "unknown_issue_resolution", i, "issue_updates",
                                     f"Issue {iid!r} has no earlier issue record.")
                        resolved.add(iid)
                    issues[iid] = update["status"]
                if assessment:
                    blockers = {x["issue_id"] for x in assessment["open_issues"] if x["blocks_execution"]}
                    self.require(not blockers & resolved, "issue_resolution_without_revision", i, "issue_updates",
                                 "A blocking issue in the assessed revision cannot be resolved only in the review.")
                    if not self.v02 and last_review_assessment != row["assessment_ref"]:
                        self.require(pending_resolutions <= resolved, "missing_issue_resolution", i, "issue_updates",
                                     "The next review must explain removed or reclassified blocking issues.")
                    if row["decision"] == "pass":
                        self.require(assessment["recommendation"] == "ready" and not blockers,
                                     "review_not_ready", i, "decision", "A passing review requires a ready assessment without blockers.")
                pending_resolutions.difference_update(resolved)
                considered.update(old | new)
                latest_review, last_review_assessment, last_review_index = row, row["assessment_ref"], i
                if row["decision"] in {"hold", "stop"}:
                    terminal = "held" if row["decision"] == "hold" else "stopped"

            elif kind == "gate":
                assessment = self.resolve(row["assessment_ref"], i, "assessment_ref", ("assessment",))
                review = self.resolve(row["review_ref"], i, "review_ref", ("review",))
                if latest_review is None:
                    self.error("missing_challenge_review", i, "review_ref", "No preceding challenge review exists.")
                self.require(latest_assessment is not None and row["assessment_ref"] == latest_assessment["record_id"],
                             "gate_assessment_mismatch", i, "assessment_ref", "Gate must bind the latest assessment.")
                self.require(latest_review is not None and row["review_ref"] == latest_review["record_id"],
                             "gate_review_mismatch", i, "review_ref", "Gate must bind the latest review.")
                if review:
                    self.require(review["assessment_ref"] == row["assessment_ref"], "gate_review_mismatch", i,
                                 "review_ref", "Review and gate must reference the same assessment.")
                for key in ("authorization_ref", "policy_ref"):
                    self.require(row[key] == self.mission[key], "authority_reference_mismatch", i, key,
                                 "Gate must retain the mission's immutable authority references.")
                self.require(instant(row["checked_at"]) < instant(row["valid_until"]) <= self.deadline,
                             "gate_time", i, "valid_until", "Gate validity must end after checking and no later than the deadline.")
                self.require(instant(row["checked_at"]) <= instant(row["created_at"]), "gate_time", i,
                             "checked_at", "Gate check cannot occur after its decision was issued.")
                self.usage(row, i)
                if assessment:
                    self.require(json_equal(row["action"], assessment["action"]), "action_mismatch", i,
                                 "action", "Gate action differs from the assessed action.")
                    self.coverage(row["prerequisite_results"], "prerequisite_id",
                                  {x["prerequisite_id"] for x in assessment["prerequisites"]}, i, "prerequisite_results")
                    for result in row["prerequisite_results"]:
                        # evidence_ref may be an external deployment reference.
                        if result["evidence_ref"] in self.index:
                            self.resolve(result["evidence_ref"], i, "prerequisite_results/evidence_ref")
                    if row["decision"] == "allow":
                        self.freshness(assessment, row["checked_at"], i)
                        self.require(assessment["recommendation"] == "ready" and review is not None
                                     and review["decision"] == "pass" and (self.v02 or not pending_resolutions),
                                     "gate_not_ready", i, "decision", "Allow requires current ready assessment and passing review.")
                        if review:
                            self.require(instant(row["checked_at"]) >= instant(review["created_at"]),
                                         "gate_time", i, "checked_at", "Gate check predates its review.")
                        self.changed_state(assessment, last_review_index, i)
                latest_gate = row
                if row["decision"] == "deny":
                    terminal = "held"

            elif kind == "dispatch_check":
                self.usage(row, i)
                if row["decision"] == "deny":
                    terminal = "held"

            elif kind == "execution":
                gate = self.resolve(row["gate_ref"], i, "gate_ref", ("gate",))
                assessment = self.resolve(row["assessment_ref"], i, "assessment_ref", ("assessment",))
                self.require(execution is None, "duplicate_execution", i, "record_type", "Only one execution attempt is allowed.")
                if gate:
                    self.require(gate["decision"] == "allow" and latest_gate is gate, "execution_gate_invalid", i,
                                 "gate_ref", "Execution requires the current allow decision.")
                    self.require(row["assessment_ref"] == gate["assessment_ref"], "execution_assessment_mismatch", i,
                                 "assessment_ref", "Execution assessment differs from gate assessment.")
                    self.require(latest_assessment is not None and gate["assessment_ref"] == latest_assessment["record_id"]
                                 and latest_review is not None and gate["review_ref"] == latest_review["record_id"],
                                 "execution_readiness_changed", i, "gate_ref", "Assessment or review changed after the gate decision.")
                    self.require(json_equal(row["action"], gate["action"]), "action_mismatch", i,
                                 "action", "Executed action differs from the exact gated action.")
                    self.require(instant(gate["created_at"]) <= instant(row["started_at"]) < instant(gate["valid_until"]),
                                 "execution_gate_expired", i, "started_at", "Dispatch must follow gate issuance and precede expiration.")
                self.require(instant(row["started_at"]) <= instant(row["finished_at"]) <= instant(row["created_at"]),
                             "execution_time", i, "finished_at", "Attempt and receipt times are inconsistent.")
                self.require(instant(row["started_at"]) < self.deadline, "dispatch_after_deadline", i,
                             "started_at", "Dispatch must precede the mission deadline.")
                if assessment:
                    self.freshness(assessment, row["started_at"], i)
                    self.changed_state(assessment, last_review_index, i)
                    self.require(json_equal(row["action"], assessment["action"]), "action_mismatch", i,
                                 "action", "Executed action differs from the assessed action.")
                execution = row

            elif kind == "verification":
                receipt = self.resolve(row["execution_ref"], i, "execution_ref", ("execution",))
                observations = set(row["observation_refs"])
                for rid in observations:
                    obs = self.resolve(rid, i, "observation_refs", ("observation",), "post_execution")
                    if obs:
                        self.require(obs["execution_ref"] == row["execution_ref"], "verification_execution_mismatch", i,
                                     "observation_refs", "Outcome observations must belong to the verified execution.")
                self.coverage(row["expected_result_checks"], "condition_id", expected_ids, i, "expected_result_checks")
                self.coverage(row["stop_condition_checks"], "condition_id", stop_ids, i, "stop_condition_checks")
                for check in row["expected_result_checks"] + row["stop_condition_checks"]:
                    self.require(set(check["evidence_refs"]) <= observations, "verification_evidence_coverage", i,
                                 "observation_refs", "Each condition check must use the declared outcome observations.")
                    for rid in check["evidence_refs"]:
                        self.resolve(rid, i, "evidence_refs", ("observation",), "post_execution")
                if row["decision"] == "completed":
                    self.require(receipt is not None and receipt["outcome"] == "succeeded",
                                 "unknown_outcome_completed" if receipt and receipt["outcome"] == "unknown" else "completion_without_success",
                                 i, "decision", "Completed verification requires a succeeded execution receipt.")
                verification = row
                terminal = row["decision"]

            elif kind == "closure":
                for rid in row["basis_refs"]:
                    self.resolve(rid, i, "basis_refs")
                self.usage(row, i, final=True)
                status = row["execution_status"]
                self.require(status != "not_dispatched" or execution is None, "closure_execution_status", i,
                             "execution_status", "An execution receipt contradicts not_dispatched.")
                self.require(status != "recorded" or execution is not None, "closure_execution_status", i,
                             "execution_status", "Recorded status requires an execution receipt.")
                if status == "uncertain" and execution and "reservation_ref" in row:
                    self.require(row["reservation_ref"] == execution["reservation_ref"], "reservation_mismatch", i,
                                 "reservation_ref", "Closure must retain the operation's reservation identity.")
                if verification:
                    self.require(row.get("verification_ref") == verification["record_id"], "closure_verification_mismatch", i,
                                 "verification_ref", "Closure must reference the latest outcome verification.")
                    self.require(row["disposition"] == verification["decision"] or row["disposition"] == "stopped",
                                 "closure_disposition_mismatch", i, "disposition", "Closure contradicts outcome verification.")
                else:
                    self.require("verification_ref" not in row and row["disposition"] != "completed",
                                 "completed_without_verification", i, "disposition", "No outcome verification supports completion.")
                if "verification_ref" in row:
                    self.resolve(row["verification_ref"], i, "verification_ref", ("verification",))
                if terminal == "stopped":
                    self.require(row["disposition"] == "stopped", "closure_disposition_mismatch", i,
                                 "disposition", "A stop decision requires a stopped closure.")
                elif terminal == "held":
                    self.require(row["disposition"] in {"held", "stopped"}, "closure_disposition_mismatch", i,
                                 "disposition", "A held mission cannot be declared complete.")
                if execution and execution["outcome"] == "unknown":
                    self.require(row["disposition"] != "completed", "unknown_outcome_completed", i,
                                 "disposition", "An unknown attempt outcome cannot yield completion.")
                terminal = row["disposition"]
        return self.errors


class SemanticValidatorV02(SemanticValidator):
    """v0.2 cross-record checks; external evidence remains an opaque claim."""

    def run(self) -> list[Diagnostic]:
        super().run()
        tracked: dict[str, bool] = {}
        blocking_revision: dict[str, str | None] = {}
        assessment = review = gate = dispatch = execution = verification = None
        reviewed_revisions: set[str] = set()
        for i, row in enumerate(self.records):
            kind = row['record_type']
            if gate and (kind in {'assessment', 'review'} or
                         kind == 'observation' and row['phase'] == 'pre_execution'):
                self.error('planning_after_gate', i, 'record_type',
                           'Renewed planning after gate issuance requires a new mission.')
            if kind == 'assessment':
                assessment = row
                for issue in row['open_issues']:
                    iid = issue['issue_id']
                    # Omission/downgrade in an assessment cannot clear tracked state.
                    if issue['blocks_execution']:
                        tracked[iid] = True
                        blocking_revision[iid] = row['record_id']
                    else:
                        tracked.setdefault(iid, False)
            elif kind == 'review':
                assessed = self.resolve(row['assessment_ref'], i, 'assessment_ref', ('assessment',))
                current = {x['issue_id'] for x in assessed['open_issues'] if x['blocks_execution']} if assessed else set()
                first_review = row['assessment_ref'] not in reviewed_revisions
                for update in row['issue_updates']:
                    iid = update['issue_id']
                    blocking = update['status'] == 'open' and update['blocks_execution']
                    if update['status'] == 'resolved':
                        self.require(iid in tracked, 'unknown_issue_resolution', i, 'issue_updates',
                                     'A resolved issue must already exist.')
                    if tracked.get(iid) and not blocking:
                        allowed = (row['assessment_ref'] != blocking_revision.get(iid)
                                   and first_review and iid not in current and bool(update['evidence_refs']))
                        self.require(allowed, 'issue_resolution_without_revision', i, 'issue_updates',
                                     'Clearing a blocker requires a new assessment and an evidenced update in its first review.')
                        if not allowed:
                            continue
                    self.require(iid not in current or blocking, 'assessment_blocker_waived', i,
                                 'issue_updates', 'A review cannot waive a blocker in its assessed revision.')
                    tracked[iid] = blocking
                    if blocking:
                        blocking_revision[iid] = row['assessment_ref']
                if row['decision'] == 'pass':
                    self.require(not any(tracked.values()), 'unresolved_blocking_issue', i, 'decision',
                                 'A passing review cannot omit or ignore a tracked execution blocker.')
                reviewed_revisions.add(row['assessment_ref'])
                review = row
            elif kind == 'gate':
                gate = row
                if row['decision'] == 'allow':
                    self.require(not any(tracked.values()), 'unresolved_blocking_issue', i, 'decision',
                                 'An unresolved tracked issue prevents gate admission.')
            elif kind == 'dispatch_check':
                dispatch = row
                bound_gate = self.resolve(row['gate_ref'], i, 'gate_ref', ('gate',))
                assessed = self.resolve(row['assessment_ref'], i, 'assessment_ref', ('assessment',))
                checked_review = self.resolve(row['review_ref'], i, 'review_ref', ('review',))
                if bound_gate:
                    self.require(bound_gate is gate and bound_gate['decision'] == 'allow',
                                 'dispatch_gate_invalid', i, 'gate_ref', 'Final check requires the current allow gate.')
                    for key in ('assessment_ref', 'review_ref', 'authorization_ref', 'policy_ref'):
                        self.require(row[key] == bound_gate[key], 'dispatch_binding_mismatch', i, key,
                                     'Final check must retain the exact gate binding.')
                    self.require(json_equal(row['action'], bound_gate['action']), 'action_mismatch', i,
                                 'action', 'Final-check action differs from the gated action.')
                    self.require(instant(bound_gate['created_at']) <= instant(row['checked_at']),
                                 'dispatch_check_time', i, 'checked_at', 'Final check predates gate issuance.')
                for key in ('authorization_ref', 'policy_ref'):
                    self.require(row[key] == self.mission[key], 'authority_reference_mismatch', i, key,
                                 'Authority references must retain the mission binding.')
                if assessed:
                    self.require(json_equal(row['action'], assessed['action']), 'action_mismatch', i,
                                 'action', 'Final-check action differs from assessment.')
                if checked_review:
                    self.require(checked_review['assessment_ref'] == row['assessment_ref'],
                                 'dispatch_binding_mismatch', i, 'review_ref', 'Review must bind the same assessment.')
                checked = instant(row['checked_at'])
                self.require(checked <= instant(row['created_at']), 'dispatch_check_time', i,
                             'checked_at', 'Check time follows record issuance.')
                auth = row['authorization_check']
                if 'valid_from' in auth:
                    start, end = instant(auth['valid_from']), instant(auth['valid_until'])
                    self.require(start < end, 'authorization_time', i, 'authorization_check',
                                 'Authorization validity interval must be nonempty.')
                    correct = {'active': start <= checked < end, 'expired': checked >= end,
                               'not_yet_valid': checked < start}.get(auth['status'], True)
                    self.require(correct, 'authorization_time', i, 'authorization_check/status',
                                 'Authorization status contradicts its declared validity interval.')
                for group in ('authorization_check', 'target_check'):
                    for ref in row[group]['evidence_refs']:
                        self.require(ref not in self.index, 'external_evidence_required', i,
                                     group + '/evidence_refs', 'Final-check evidence references must be external.')
                target = row['target_check']
                obs = self.resolve(target['basis_observation_ref'], i, 'target_check/basis_observation_ref',
                                   ('observation',), 'pre_execution')
                self.require(target['target_ref'] == row['action']['target_ref'], 'target_binding_mismatch', i,
                             'target_check/target_ref', 'Target check must cover the action target.')
                if obs:
                    self.require(obs['target_ref'] == target['target_ref'] and
                                 json_equal(obs['target_state'], target['expected_state']),
                                 'target_basis_mismatch', i, 'target_check', 'Expected state must match the basis observation.')
                if assessed:
                    self.require(target['basis_observation_ref'] in assessed['observation_refs'],
                                 'target_basis_mismatch', i, 'target_check', 'Basis must occur in assessment evidence.')
                if checked_review:
                    self.require(target['basis_observation_ref'] in checked_review['reused_observation_refs'] +
                                 checked_review['new_observation_refs'], 'target_basis_mismatch', i,
                                 'target_check', 'Basis must occur in the bound review evidence.')
                expected, current = target['expected_state'], target['current_state']
                comparable = expected['kind'] != 'unknown' and current['kind'] != 'unknown' and expected['kind'] == current['kind']
                result = ('match' if json_equal(expected, current) else 'changed') if comparable else 'unknown'
                self.require(target['result'] == result, 'target_state_result_mismatch', i, 'target_check/result',
                             'Declared target result contradicts the compared state tokens.')
                if row['decision'] == 'allow':
                    self.require(not any(tracked.values()), 'unresolved_blocking_issue', i, 'decision',
                                 'Final admission cannot override an unresolved blocker.')
                    before = instant(row['dispatch_before'])
                    bounds = [self.deadline, checked + self.mission['limits']['max_dispatch_check_age_seconds'],
                              instant(auth['valid_until'])]
                    if bound_gate:
                        bounds.append(instant(bound_gate['valid_until']))
                    self.require(instant(row['created_at']) < before <= min(bounds), 'dispatch_window_invalid', i,
                                 'dispatch_before', 'Dispatch window must follow issuance and fit all expiry bounds.')
                    if assessed:
                        self.freshness(assessed, row['checked_at'], i)
            elif kind == 'execution':
                execution = row
                dc = self.resolve(row['dispatch_check_ref'], i, 'dispatch_check_ref', ('dispatch_check',))
                self.require(not any(tracked.values()), 'unresolved_blocking_issue', i, 'record_type',
                             'Execution cannot ignore an unresolved tracked issue.')
                if dc:
                    self.require(dc is dispatch and dc['decision'] == 'allow', 'execution_dispatch_denied', i,
                                 'dispatch_check_ref', 'Execution requires the preceding allow final check.')
                    self.require(row['gate_ref'] == dc['gate_ref'] and row['assessment_ref'] == dc['assessment_ref'],
                                 'dispatch_binding_mismatch', i, 'dispatch_check_ref', 'Execution must retain final-check bindings.')
                    self.require(json_equal(row['action'], dc['action']), 'action_mismatch', i,
                                 'action', 'Execution differs from the final checked action.')
                    at = instant(row['started_at'])
                    self.require(at >= instant(dc['created_at']), 'dispatch_check_time', i,
                                 'started_at', 'Dispatch predates final-check issuance.')
                    if 'dispatch_before' in dc:
                        self.require(at < instant(dc['dispatch_before']), 'expired_dispatch_check', i,
                                     'started_at', 'Dispatch reached the exclusive final-check deadline.')
                    age = at - instant(dc['checked_at'])
                    self.require(0 <= age <= self.mission['limits']['max_dispatch_check_age_seconds'],
                                 'expired_dispatch_check', i, 'started_at', 'Final check is not fresh at dispatch.')
                    auth = dc['authorization_check']
                    if 'valid_until' in auth:
                        self.require(at < instant(auth['valid_until']), 'authorization_expired_at_dispatch', i,
                                     'started_at', 'Dispatch reached authorization expiration.')
                        self.require(at >= instant(auth['valid_from']), 'authorization_not_yet_valid', i,
                                     'started_at', 'Dispatch precedes authorization validity.')
            elif kind == 'verification':
                verification = row
            elif kind == 'closure':
                codes = set(row['reason_codes'])
                required: set[str] = set()
                evidence: set[str] = set()
                if gate and gate['decision'] == 'deny':
                    required.add('gate_denied'); evidence.add(gate['record_id'])
                if dispatch and dispatch['decision'] == 'deny':
                    required.add('dispatch_check_denied'); evidence.add(dispatch['record_id'])
                    auth = dispatch['authorization_check']
                    code = {'expired': 'authorization_expired', 'revoked': 'authorization_revoked',
                            'not_yet_valid': 'authorization_not_yet_valid', 'unknown': 'authorization_unknown'}.get(auth['status'])
                    if code:
                        required.add(code)
                    if auth['scope_match'] != 'pass':
                        required.add('authorization_scope_mismatch' if auth['scope_match'] == 'fail' else 'authorization_unknown')
                    code = {'changed': 'target_state_changed', 'unknown': 'target_state_unknown'}.get(dispatch['target_check']['result'])
                    if code:
                        required.add(code)
                if any(tracked.values()):
                    required.add('unresolved_blocking_issue')
                    if review:
                        evidence.add(review['record_id'])
                        if review['round'] >= self.mission['limits']['max_review_rounds']:
                            required.add('review_limit_reached')
                if execution and execution['outcome'] == 'unknown':
                    required.add('execution_outcome_unknown'); evidence.add(execution['record_id'])
                if row['execution_status'] == 'uncertain' or 'reservation_unresolved' in codes:
                    required.add('reservation_unresolved')
                    self.require(row['execution_status'] == 'uncertain' and 'reservation_ref' in row,
                                 'reservation_unresolved', i, 'execution_status', 'Unresolved reservation requires uncertain status and its reference.')
                if 'reservation_ref' in row and execution:
                    self.require(row['reservation_ref'] == execution['reservation_ref'], 'reservation_mismatch', i,
                                 'reservation_ref', 'Closure must retain the execution reservation identity.')
                if dispatch and dispatch['decision'] == 'allow' and not execution and row['execution_status'] == 'not_dispatched':
                    if instant(row['created_at']) >= instant(dispatch['dispatch_before']):
                        required.add('dispatch_check_expired'); evidence.add(dispatch['record_id'])
                if 'dispatch_check_expired' in codes:
                    self.require(dispatch is not None and dispatch['decision'] == 'allow' and execution is None and
                                 instant(row['created_at']) >= instant(dispatch.get('dispatch_before', row['created_at'])),
                                 'closure_reason_unsupported', i, 'reason_codes', 'Expired-check reason needs an unused expired allow check.')
                if 'review_limit_reached' in codes:
                    self.require(review is not None and review['round'] >= self.mission['limits']['max_review_rounds'] and
                                 any(tracked.values()), 'closure_reason_unsupported', i, 'reason_codes',
                                 'Review-limit reason requires exhaustion with unresolved blockers.')
                self.require(required <= codes, 'closure_reason_missing', i, 'reason_codes',
                             f'Missing mechanically evident reasons: {sorted(required - codes)}.')
                self.require(evidence <= set(row['basis_refs']), 'closure_basis_missing', i, 'basis_refs',
                             'Closure must cite the records establishing its blocking reasons.')
        return self.errors


# Expectations belong to the repository harness, never to extensions.expected_error.
KNOWN_FAILURES_V03 = {
    'agent-claimed-human-approval.json': 'agent_claimed_human_approval',
    'approval-for-ineligible-reconciliation.json': 'approval_for_ineligible_reconciliation',
    'carried-blocker-downgraded.json': 'carried_blocker_downgraded',
    'carried-blocker-omitted.json': 'carried_blocker_omitted',
    'carried-blocker-renamed.json': 'carried_blocker_renamed',
    'carried-blocker-silently-resolved.json': 'unresolved_blocking_issue',
    'changed-candidate-fields.json': 'changed_candidate_fields',
    'changed-operation-id.json': 'changed_operation_id',
    'completed-source-recovery.json': 'completed_source_recovery',
    'duplicate-claim-consumption.json': 'duplicate_claim_consumption',
    'duplicate-successor.json': 'duplicate_successor',
    'hidden-recovery-chain.json': 'hidden_recovery_chain',
    'missing-fence.json': 'old_operation_unfenced',
    'missing-fresh-successor-observation.json': 'missing_fresh_successor_observation',
    'missing-human-review.json': 'missing_human_review',
    'missing-recovery-context.json': 'missing_recovery_context',
    'missing-successor-dispatch-check.json': 'missing_successor_dispatch_check',
    'missing-successor-gate.json': 'missing_successor_gate',
    'missing-successor-review.json': 'missing_successor_review',
    'not-dispatched-with-source-execution.json': 'not_dispatched_with_source_execution',
    'reused-source-reservation.json': 'reused_source_reservation',
    'source-already-successor.json': 'source_already_successor',
    'source-edited.json': 'source_edited',
    'source-reopened.json': 'source_reopened',
    'successor-after-deny.json': 'successor_after_deny',
    'successor-at-start-deadline.json': 'successor_at_start_deadline',
    'successor-with-expired-approval.json': 'successor_with_expired_approval',
    'target-snapshot-only-no-effect.json': 'target_snapshot_only_no_effect',
    'unknown-outcome-treated-as-no-effect.json': 'unknown_outcome_treated_as_no_effect',
    'unresolved-reservation.json': 'reservation_unresolved',
}
RUNTIME_FIXTURES = {
    'source-edited.json', 'hidden-recovery-chain.json', 'duplicate-claim-consumption.json',
}
RECOVERY_CODES = dict(zip(
    ('reference_integrity', 'source_terminal', 'reconciliation_eligible', 'evidence_fresh',
     'human_approval_valid', 'recovery_policy_valid', 'read_authorization_valid',
     'old_operation_fenced', 'reservation_resolved', 'successor_unique',
     'budgets_available', 'deadline_valid'),
    ('reference_invalid', 'source_ineligible', 'reconciliation_ineligible',
     'evidence_stale_or_unknown', 'human_approval_invalid', 'recovery_policy_invalid',
     'read_authorization_invalid', 'old_operation_unfenced', 'reservation_unresolved',
     'successor_conflict', 'resource_limit_reached', 'deadline_reached')))
ELIGIBLE = {'confirmed_not_dispatched', 'confirmed_no_effect'}


def object_rows(value: Any) -> list[dict[str, Any]]:
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def v03_shape_codes(bundle: dict[str, Any]) -> list[Diagnostic]:
    """Safe diagnostic labels for schema-invalid input; never trust fixture metadata."""
    out: list[Diagnostic] = []
    def add(code: str, path: str, message: str) -> None:
        out.append(Diagnostic('schema', code, path, message))
    if bundle.get('document_type') == 'mission_bundle':
        if 'recovery_ref' in bundle:
            add('missing_recovery_context', '/recovery_ref', 'A successor requires its enclosing recovery bundle.')
        return out
    if bundle.get('document_type') != 'recovery_bundle':
        return out
    records = object_rows(bundle.get('records'))
    source = bundle.get('source')
    source = source if isinstance(source, dict) else {}
    sr = object_rows(source.get('records'))
    if 'recovery_ref' in source:
        add('source_already_successor', '/source/recovery_ref', 'A successor cannot be a recovery source.')
    if any(r.get('record_type') == 'closure' and r.get('disposition') == 'completed' for r in sr):
        add('completed_source_recovery', '/source', 'Recovery requires a held or stopped source.')
    reviews = [r for r in records if r.get('record_type') == 'human_review']
    if not reviews:
        add('missing_human_review', '/records', 'Recovery requires one human review.')
    for r in reviews:
        if r.get('producer_role') != 'human':
            add('agent_claimed_human_approval', '/records', 'An agent role cannot supply human approval.')
    rec = next((r for r in records if r.get('record_type') == 'reconciliation'), {})
    if rec.get('status') not in ELIGIBLE and any(r.get('decision') == 'approve' for r in reviews):
        add('approval_for_ineligible_reconciliation', '/records', 'An ineligible reconciliation cannot be approved.')
    if rec.get('status') == 'confirmed_not_dispatched' and any(r.get('record_type') == 'execution' for r in sr):
        add('not_dispatched_with_source_execution', '/records', 'A recorded execution prohibits a no-dispatch conclusion.')
    if rec.get('status') in ELIGIBLE:
        if rec.get('fence_status') != 'enforced':
            add('old_operation_unfenced', '/records', 'Eligible recovery requires a permanent source fence.')
        if rec.get('reservation_status') not in {'none', 'released'}:
            add('reservation_unresolved', '/records', 'Eligible recovery requires a cleared reservation.')
        if rec.get('status') == 'confirmed_no_effect' and rec.get('execution_finality') != 'terminal':
            add('unknown_outcome_treated_as_no_effect', '/records', 'Unknown finality cannot establish no effect.')
        kinds = {r.get('kind') for r in object_rows(rec.get('evidence')) if isinstance(r.get('kind'), str)}
        if kinds == {'target_snapshot'}:
            add('target_snapshot_only_no_effect', '/records', 'Snapshots alone cannot establish no effect or dispatch finality.')
    successor = bundle.get('successor')
    if isinstance(successor, list):
        add('duplicate_successor', '/successor', 'Successor must be a single mission object, not a collection.')
    if 'successor' in bundle and any(r.get('record_type') == 'recovery_admission' and r.get('decision') == 'deny' for r in records):
        add('successor_after_deny', '/successor', 'Denied recovery cannot contain a successor.')
    if isinstance(successor, dict):
        if 'recovery_ref' not in successor:
            add('missing_recovery_context', '/successor', 'Successor must identify the enclosing recovery.')
        rows = object_rows(successor.get('records'))
        kinds = {r.get('record_type') for r in rows if isinstance(r.get('record_type'), str)}
        if 'execution' in kinds:
            for kind in ('review', 'gate', 'dispatch_check'):
                if kind not in kinds:
                    add('missing_successor_' + kind, '/successor/records', 'Successor execution lacks its own ' + kind + '.')
    return out


class SemanticValidatorV03:
    """Document-only v0.3 checks, after canonical schema success. No external lookup."""

    def __init__(self, bundle: dict[str, Any]):
        self.bundle = bundle
        self.errors: list[Diagnostic] = []

    def check(self, ok: bool, code: str, path: str, message: str) -> None:
        if not ok:
            item = Diagnostic('semantic', code, path, message)
            if item not in self.errors:
                self.errors.append(item)

    def sequence(self, rows: list[dict[str, Any]], prefix: str) -> None:
        for i in range(1, len(rows)):
            self.check(instant(rows[i-1]['created_at']) <= instant(rows[i]['created_at']),
                       'record_time_order', f'{prefix}/records/{i}/created_at', 'Record creation times must be nondecreasing.')

    def mission(self, bundle: dict[str, Any], prefix: str) -> None:
        # Run inherited checks on actual v0.3 records, without relabeling versions.
        for error in SemanticValidatorV02(bundle).run():
            self.errors.append(Diagnostic(error.layer, error.code, prefix + error.path, error.message))
        self.sequence(bundle['records'], prefix)
        ids = {r['record_id'] for r in bundle['records']}
        self.external_aliases(bundle, ids, prefix)

    def external_aliases(self, value: Any, ids: set[str], path: str) -> None:
        """Only explicitly external fields; local review evidence remains locally bound."""
        external = {'authorization_ref', 'policy_ref', 'read_authorization_ref',
                    'control_authorization_ref', 'recovery_policy_ref', 'reviewer_ref',
                    'reviewer_authority_ref', 'issuer_ref', 'claim_ref', 'reservation_ref',
                    'source_reservation_ref', 'enforcement_ref', 'receipt_ref', 'source_ref'}
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {'extensions', 'parameters'}:
                    continue  # Opaque application data has no protocol reference semantics.
                here = path + pointer([key])
                if key in external or key == 'evidence_ref' and value.get('kind') in {
                    'dispatch_ledger', 'operation_receipt', 'effect_audit', 'reservation_ledger',
                    'fence_receipt', 'target_snapshot', 'lookup_failure'}:
                    self.check(item not in ids, 'external_reference_alias', here,
                               'An external reference must not alias an internal record ID.')
                if key == 'evidence_refs' and (value.get('record_type') == 'human_review' or
                        path.endswith(('/authorization_check', '/target_check'))):
                    self.check(not set(item) & ids, 'external_reference_alias', here,
                               'Approval and dispatch-check evidence must be external.')
                self.external_aliases(item, ids, here)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                self.external_aliases(item, ids, path + '/' + str(i))

    @staticmethod
    def carried(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        state: dict[str, dict[str, Any]] = {}
        for row in rows:
            if row['record_type'] == 'assessment':
                for issue in row['open_issues']:
                    iid = issue['issue_id']
                    blocking = issue['blocks_execution'] or state.get(iid, {}).get('blocks_execution', False)
                    state[iid] = {'issue_id': iid, 'source_record_ref': row['record_id'], 'blocks_execution': blocking}
            elif row['record_type'] == 'review':
                for issue in row['issue_updates']:
                    iid = issue['issue_id']
                    if issue['status'] == 'resolved':
                        state.pop(iid, None)
                    else:
                        state[iid] = {'issue_id': iid, 'source_record_ref': row['record_id'],
                                      'blocks_execution': issue['blocks_execution']}
        return state

    def run(self) -> list[Diagnostic]:
        b = self.bundle
        if b['document_type'] == 'mission_bundle':
            self.mission(b, '')
            return self.errors
        source = b['source']; sr = source['records']; sm = sr[0]
        self.mission(source, '/source')
        self.sequence(b['records'], '')
        h, rec, review, admission = b['records']
        c = h['candidate']
        closure = next(r for r in sr if r['record_type'] == 'closure')
        if sr[-1] is not closure:
            self.check(False, 'source_reopened', '/source/records', 'No source work may follow its terminal closure.')
        executions = [r for r in sr if r['record_type'] == 'execution']
        successor = b.get('successor')
        all_rows = sr + b['records'] + (successor['records'] if successor else [])
        ids = [r['record_id'] for r in all_rows]
        self.check(len(ids) == len(set(ids)), 'duplicate_record_id', '/', 'Record IDs must be unique across the recovery document.')
        self.external_aliases(b, set(ids), '')
        for i, row in enumerate(b['records']):
            self.check(row['recovery_id'] == b['recovery_id'], 'recovery_mismatch', f'/records/{i}/recovery_id', 'Record must belong to enclosing recovery.')
            for field, target in (('handoff_ref', h), ('reconciliation_ref', rec), ('human_review_ref', review)):
                if field in row:
                    self.check(row[field] == target['record_id'], 'recovery_reference_mismatch', f'/records/{i}/{field}', 'Reference must identify the preceding recovery record of the required type.')
        for field, expected in (('source_mission_ref', sm['record_id']), ('source_closure_ref', closure['record_id']),
                                ('source_operation_id', sm['operation_id']), ('source_reason_codes', closure['reason_codes'])):
            self.check(json_equal(h[field], expected), 'source_reference_mismatch', '/records/0/' + field, 'Handoff must preserve the exact source binding.')
        if executions:
            self.check(h.get('source_execution_ref') == executions[0]['record_id'], 'source_reference_mismatch', '/records/0/source_execution_ref', 'Handoff must identify source execution.')
        reservations = [r['reservation_ref'] for r in sr if r['record_type'] in {'execution', 'closure'} and 'reservation_ref' in r]
        self.check(('source_reservation_ref' in h) == bool(reservations) and all(h.get('source_reservation_ref') == x for x in reservations),
                   'source_reservation_mismatch', '/records/0/source_reservation_ref', 'Handoff must match every source reservation, iff one exists.')
        self.check(c['mission_id'] != source['mission_id'], 'candidate_mission_reused', '/records/0/candidate/mission_id', 'Candidate mission ID must be new.')
        self.check(c['operation_id'] == sm['operation_id'], 'changed_operation_id', '/records/0/candidate/operation_id', 'Recovery must retain stable operation identity.')
        for field in ('objective', 'observation_scope', 'expected_results', 'stop_conditions'):
            self.check(json_equal(c[field], sm[field]), 'changed_candidate_fields', '/records/0/candidate/' + field, 'Candidate must preserve the source objective and scope.')
        self.check(c['authorization_ref'] != sm['authorization_ref'], 'reused_source_authorization', '/records/0/candidate/authorization_ref', 'Candidate requires a new authorization snapshot.')
        for field in ('resource_budgets',):
            bids = [x['budget_id'] for x in c['limits'][field]]
            self.check(len(bids) == len(set(bids)), 'duplicate_identifier', '/records/0/candidate/limits/' + field, 'Candidate budget IDs must be unique.')
        expected = [x['condition_id'] for x in c['expected_results'] + c['stop_conditions']]
        self.check(len(expected) == len(set(expected)), 'duplicate_identifier', '/records/0/candidate', 'Candidate condition IDs must be unique.')
        carried = self.carried(sr)
        actual = {x['issue_id']: x for x in h['issue_carryover']}
        self.check(len(actual) == len(h['issue_carryover']), 'duplicate_identifier', '/records/0/issue_carryover', 'Carried issue IDs must be unique.')
        missing, extra = carried.keys() - actual.keys(), actual.keys() - carried.keys()
        self.check(not missing, 'carried_blocker_omitted', '/records/0/issue_carryover', 'Every open source issue must be carried.')
        self.check(not (missing and extra), 'carried_blocker_renamed', '/records/0/issue_carryover', 'Carried issue IDs cannot be replaced with new IDs.')
        self.check(not extra, 'unexpected_carried_issue', '/records/0/issue_carryover', 'Carryover must contain exactly the open source issues.')
        for iid in carried.keys() & actual.keys():
            self.check(actual[iid]['blocks_execution'] == carried[iid]['blocks_execution'], 'carried_blocker_downgraded', '/records/0/issue_carryover', 'Preserve each carried blocking flag exactly.')
            self.check(actual[iid]['source_record_ref'] == carried[iid]['source_record_ref'], 'carryover_reference_mismatch', '/records/0/issue_carryover', 'Carryover must cite its latest explicit source state.')
        deadline = instant(h['limits']['deadline_at']); ht = instant(h['created_at'])
        self.check(instant(closure['created_at']) <= ht < deadline, 'recovery_time', '/records/0/created_at', 'Handoff must follow source closure and precede recovery deadline.')
        self.check(instant(c['limits']['deadline_at']) > ht, 'invalid_deadline', '/records/0/candidate/limits/deadline_at', 'Candidate deadline must follow proposal creation.')
        checked = instant(rec['checked_at'])
        self.check(ht <= checked <= instant(rec['created_at']) < deadline, 'reconciliation_time', '/records/1', 'Reconciliation must follow handoff and finish before the recovery deadline.')
        evidence_refs = [x['evidence_ref'] for x in rec['evidence']]
        self.check(len(evidence_refs) == len(set(evidence_refs)), 'duplicate_evidence_reference', '/records/1/evidence', 'Evidence references must be unique.')
        for i, evidence in enumerate(rec['evidence']):
            self.check(instant(closure['created_at']) <= instant(evidence['observed_at']) <= checked,
                       'recovery_evidence_time', f'/records/1/evidence/{i}/observed_at', 'Evidence must follow source closure and precede reconciliation checking.')
        self.check(instant(rec['created_at']) <= instant(review['reviewed_at']) <= instant(review['created_at']) < instant(review['valid_until']),
                   'human_review_time', '/records/2', 'Review must follow reconciliation and precede its approval expiry.')
        self.check(instant(review['created_at']) < deadline, 'recovery_deadline', '/records/2/created_at', 'Human review must precede recovery deadline.')
        at = instant(admission['checked_at']); issued = instant(admission['created_at'])
        self.check(instant(review['created_at']) <= at <= issued, 'admission_time', '/records/3', 'Admission checking must follow review and precede issuance.')
        max_age = h['limits']['max_evidence_age_seconds']
        expiry = min(instant(e['observed_at']) + max_age for e in rec['evidence'])
        eligible = (rec['status'] in ELIGIBLE and rec['execution_finality'] == 'terminal' and rec['fence_status'] == 'enforced'
                    and rec['reservation_status'] in {'none', 'released'})
        budgets = {x['budget_id']: x['limit'] for x in h['limits']['resource_budgets']}
        self.check(len(budgets) == len(h['limits']['resource_budgets']), 'duplicate_identifier', '/records/0/limits/resource_budgets', 'Recovery budgets must have unique IDs.')
        previous: dict[str, Any] = {}
        capacity = True
        for i, row in ((1, rec), (3, admission)):
            usage = {x['budget_id']: x for x in row['resource_usage']}
            self.check(len(usage) == len(row['resource_usage']) and usage.keys() == budgets.keys(), 'identifier_coverage', f'/records/{i}/resource_usage', 'Usage must cover exactly the recovery budgets.')
            for bid, entry in usage.items():
                self.check(entry['used'] >= previous.get(bid, 0), 'resource_usage_decreased', f'/records/{i}/resource_usage', 'Cumulative recovery use cannot decrease.')
                previous[bid] = entry['used']
            if admission['decision'] == 'allow':
                self.check(all(x['used'] + x['reserved'] <= budgets.get(bid, -1) for bid, x in usage.items()),
                           'resource_limit_exceeded', f'/records/{i}/resource_usage',
                           'An allowed recovery must remain within each fixed budget.')
            if i == 3:
                capacity = all(x['used'] + x['reserved'] <= budgets.get(bid, -1) for bid, x in usage.items())
        facts = {'source_terminal': sr[-1] is closure and closure['disposition'] in {'held', 'stopped'},
                 'reconciliation_eligible': eligible, 'evidence_fresh': issued <= expiry,
                 'human_approval_valid': review['decision'] == 'approve' and eligible and issued < instant(review['valid_until']),
                 'old_operation_fenced': rec['fence_status'] == 'enforced',
                 'reservation_resolved': rec['reservation_status'] in {'none', 'released'},
                 'budgets_available': capacity,
                 'deadline_valid': issued < min(deadline, instant(c['limits']['deadline_at']))}
        for key, fact in facts.items():
            self.check(admission['checks'][key] != 'pass' or fact, 'admission_check_contradiction', '/records/3/checks/' + key, 'Pass contradicts structured document facts.')
        if admission['decision'] == 'deny':
            codes = {RECOVERY_CODES[k] for k, value in admission['checks'].items() if value != 'pass'}
            self.check(codes <= set(admission['reason_codes']), 'admission_reason_missing', '/records/3/reason_codes', 'Denial must include every code mapped from a non-pass check.')
        else:
            before = instant(admission['start_before'])
            self.check(issued < before <= min(instant(review['valid_until']), deadline, instant(c['limits']['deadline_at']), expiry),
                       'successor_start_window_invalid', '/records/3/start_before', 'Start window must fit approval, evidence, and both deadlines.')
        if successor:
            self.mission(successor, '/successor')
            rows = successor['records']; mission = rows[0]; created = instant(mission['created_at'])
            self.check(successor['recovery_ref'] == b['recovery_id'], 'missing_recovery_context', '/successor/recovery_ref', 'Successor must bind the enclosing recovery.')
            for field, value in c.items():
                if field == 'extensions':
                    continue
                code = 'changed_operation_id' if field == 'operation_id' else 'changed_candidate_fields'
                self.check(json_equal(mission.get(field), value), code, '/successor/records/0/' + field, 'Successor must copy every candidate field exactly.')
            self.check(issued <= created < instant(admission['start_before']), 'successor_at_start_deadline', '/successor/records/0/created_at', 'Successor creation must follow admission and precede the exclusive start deadline.')
            self.check(created < instant(review['valid_until']), 'successor_with_expired_approval', '/successor/records/0/created_at', 'Human approval must be unexpired at successor creation.')
            observations = [r for r in rows if r['record_type'] == 'observation' and r['phase'] == 'pre_execution']
            self.check(bool(observations) and all(instant(r['observed_at']) > created and
                       all(instant(s['retrieved_at']) > created for s in r['sources']) for r in observations),
                       'missing_fresh_successor_observation', '/successor/records', 'Successor observations and source retrievals must be fresh after creation.')
            first = next((r for r in rows if r['record_type'] == 'assessment'), None)
            opened = {x['issue_id']: x['blocks_execution'] for x in first['open_issues']} if first else {}
            for iid, issue in carried.items():
                self.check(iid in opened and opened[iid] == issue['blocks_execution'], 'successor_carryover_missing', '/successor/records', 'First successor assessment must initialize every carried issue with its exact flag.')
            kinds = {r['record_type'] for r in rows}
            if 'execution' in kinds:
                for kind in ('review', 'gate', 'dispatch_check'):
                    self.check(kind in kinds, 'missing_successor_' + kind, '/successor/records', 'Successor execution requires its own ' + kind + '.')
            for row in rows:
                if row['record_type'] == 'execution':
                    self.check(row['reservation_ref'] not in reservations, 'reused_source_reservation', '/successor/records', 'Successor execution requires a new reservation.')
        return self.errors


def runtime_fixture_check(bundle: dict[str, Any], name: str) -> list[Diagnostic]:
    """Opt-in repository test adapter ONLY. Never called by validate_bundle/file mode.

    Treat fixture extensions as a synthetic service response, not trusted evidence.
    Each negative is paired below with a repaired positive control. This tests
    rejection logic, not any deployment's durable registry or atomic enforcement.
    """
    def require(ok: bool) -> None:
        if not ok:
            raise ValueError('Synthetic service response has inconsistent bindings or accounting.')
    f = bundle['extensions']['fixture']; registry = f['external_reference_registry']
    code = KNOWN_FAILURES_V03[name]
    if name == 'source-edited.json':
        archive = registry[f['source_snapshot_ref']]
        require(archive['kind'] == 'mock_immutable_source_snapshot')
        require(archive['source_mission_id'] == bundle['source']['mission_id'])
        require(archive['source_closure_ref'] == bundle['records'][0]['source_closure_ref'])
        rejected = not json_equal(bundle['source'], archive['snapshot'])
    elif name == 'hidden-recovery-chain.json':
        lineage = registry[f['lineage_registry_ref']]
        require(lineage['kind'] == 'mock_operation_lineage')
        require(lineage['operation_id'] == bundle['records'][0]['source_operation_id'])
        source = [r for r in lineage['mission_lineage'] if r['mission_id'] == bundle['source']['mission_id']]
        require(len(source) == 1)
        rejected = (source[0]['generation'] != 0 or source[0]['parent_mission_id'] is not None or
                    source[0]['created_by_recovery_id'] is not None)
    else:
        claim_ref = bundle['records'][3]['claim_ref']; claim = registry[claim_ref]
        require(claim['kind'] == 'single_use_recovery_claim')
        events = claim['consumption_events']
        require(all(e['claim_ref'] == claim_ref and e['candidate_mission_id'] == bundle['successor']['mission_id'] for e in events))
        require(len({e['event_id'] for e in events}) == len(events))
        consumed = sum(e['result'] == 'consumed' for e in events)
        require(claim['consume_count'] == consumed)
        rejected = consumed > 1
    return [Diagnostic('runtime_fixture', code, '/extensions/fixture',
                       'Synthetic external-state negative detected; not a document-conformance failure.')] if rejected else []


def runtime_fixture_pair(bundle: dict[str, Any], name: str, validator: Any) -> list[Diagnostic]:
    try:
        errors = runtime_fixture_check(bundle, name)
        control = copy.deepcopy(bundle); f = control['extensions']['fixture']; registry = f['external_reference_registry']
        if name == 'source-edited.json':
            control['source'] = copy.deepcopy(registry[f['source_snapshot_ref']]['snapshot'])
        elif name == 'hidden-recovery-chain.json':
            lineage = registry[f['lineage_registry_ref']]
            row = next(r for r in lineage['mission_lineage'] if r['mission_id'] == control['source']['mission_id'])
            row.update(generation=0, parent_mission_id=None, created_by_recovery_id=None,
                       prior_claim_consumed=False, successor_allowance_permanently_consumed=False)
            lineage['root_mission_id'] = row['mission_id']
        else:
            claim = registry[control['records'][3]['claim_ref']]
            claim['consumption_events'][1]['result'] = 'rejected_already_consumed'
            claim['consume_count'] = 1; f['runtime_summary']['claim_consume_count'] = 1
        if not errors or runtime_fixture_check(control, name) or validate_bundle(control, validator):
            raise ValueError('Synthetic negative or repaired positive control did not behave as expected.')
        return errors
    except (KeyError, TypeError, ValueError, AssertionError, IndexError) as exc:
        return [Diagnostic('harness', 'runtime_fixture_invalid', '/extensions/fixture',
                           'Malformed synthetic test or failing paired control: ' + str(exc))]


def schema_diagnostics(bundle: Any, errors: list[Any]) -> list[Diagnostic]:
    summaries = {"oneOf": "Value must match exactly one permitted record schema.",
                 "contains": "Required matching array item is missing.",
                 "maxContains": "Matching array items exceed the permitted count."}
    result = [Diagnostic("schema", "schema_validation", pointer(e.absolute_path),
                         f"{e.validator}: {summaries.get(e.validator, e.message[:300])}") for e in errors]
    # Stable root-cause codes for the existing negative fixtures. Structural
    # validation is still authoritative; these labels do not suppress errors.
    if not isinstance(bundle, dict) or not isinstance(bundle.get("records"), list):
        return result
    records = [r for r in bundle["records"] if isinstance(r, dict)]
    executions = [r for r in records if r.get("record_type") == "execution"]
    completed = any(r.get("record_type") == "closure" and r.get("disposition") == "completed" for r in records)
    if len(executions) > 1:
        result.append(Diagnostic("schema", "duplicate_execution", "/records", "At most one execution record is permitted."))
    if completed and not any(r.get("record_type") == "verification" for r in records):
        result.append(Diagnostic("schema", "completed_without_verification", "/records", "Completed closure has no outcome verification."))
    if completed and any(r.get("outcome") == "unknown" for r in executions):
        result.append(Diagnostic("schema", "unknown_outcome_completed", "/records", "Completed closure includes an unknown execution outcome."))
    if bundle.get("protocol_version") == "0.2.0":
        checks = [r for r in records if r.get("record_type") == "dispatch_check"]
        if executions and not checks:
            result.append(Diagnostic("schema", "missing_dispatch_check", "/records", "Execution has no final dispatch check."))
        if executions and any(r.get("decision") == "deny" for r in checks):
            result.append(Diagnostic("schema", "execution_dispatch_denied", "/records", "Execution follows a denied final check."))
        if len(checks) > 1:
            result.append(Diagnostic("schema", "duplicate_dispatch_check", "/records", "At most one final check is permitted."))
    if bundle.get("protocol_version") == "0.3.0":
        try:
            result.extend(v03_shape_codes(bundle))
        except (TypeError, KeyError, ValueError):
            pass  # Arbitrarily malformed values already have authoritative schema errors.
    return result


def validate_bundle(bundle: Any, validator: Any) -> list[Diagnostic]:
    if not isinstance(bundle, dict) or not isinstance(bundle.get("protocol_version"), str) or bundle["protocol_version"] not in SCHEMAS:
        return [Diagnostic("schema", "unsupported_version", "/protocol_version", "Expected protocol_version 0.1.0, 0.2.0, or 0.3.0.")]
    errors = sorted(validator.iter_errors(bundle), key=lambda e: (pointer(e.absolute_path), str(e.validator)))
    if errors:
        return schema_diagnostics(bundle, errors)
    if bundle["protocol_version"] == "0.3.0":
        return SemanticValidatorV03(bundle).run()
    return (SemanticValidatorV02(bundle) if bundle["protocol_version"] == "0.2.0" else SemanticValidator(bundle)).run()


def local_references_only(value: Any, root: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"$ref", "$dynamicRef"}:
                if not isinstance(item, str) or not (item == "#" or item.startswith("#/")):
                    raise ValueError("Only local JSON Pointer schema references are supported; external resolution is disabled.")
                target = root
                try:
                    if item != "#":
                        for part in unquote(item[2:]).split("/"):
                            target = target[part.replace("~1", "/").replace("~0", "~")]
                except (KeyError, TypeError) as exc:
                    raise ValueError(f"Unresolved local schema reference: {item}") from exc
            local_references_only(item, root)
    elif isinstance(value, list):
        for item in value:
            local_references_only(item, root)


def load_validator(path: Path) -> Any:
    schema = read_json(path)
    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Expected a Draft 2020-12 schema object.")
    local_references_only(schema, schema)
    JSONValidator.check_schema(schema)
    return JSONValidator(schema, format_checker=FORMATS)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path, help="Validate explicit bundle paths; each must be accepted.")
    parser.add_argument("--examples", action="store_true", help="Check repository pass/fail fixtures (also the default).")
    parser.add_argument("--schema", type=Path, default=None, help="Alternate local schema; its supported protocol version selects the example suite.")
    parser.add_argument("--version", choices=tuple(SCHEMAS), help="Restrict examples or explicit files to this protocol version.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit a machine-readable report.")
    args = parser.parse_args(argv)
    if args.examples and args.files:
        parser.error("--examples cannot be combined with positional files")
    suite = args.examples or not args.files
    try:
        validators_by_version = {version: load_validator(path) for version, path in SCHEMAS.items()}
        selected_version = args.version
        alternate = None
        if args.schema:
            alternate = load_validator(args.schema)
            declared = alternate.schema.get("properties", {}).get("protocol_version", {}).get("const")
            if declared not in SCHEMAS:
                raise ValueError("Alternate schema must declare a supported protocol_version const.")
            if selected_version and selected_version != declared:
                raise ValueError("--version and --schema declare different versions.")
            selected_version = declared
    except (OSError, ValueError, SchemaError, ArithmeticError) as exc:
        print(f"Schema configuration error: {exc}", file=sys.stderr)
        return 2
    if suite:
        jobs = []
        for version, directory in (("0.1.0", ROOT / "examples"), ("0.2.0", ROOT / "examples/v0.2"), ("0.3.0", ROOT / "examples/v0.3")):
            if selected_version and selected_version != version:
                continue
            passes = sorted((directory / "pass").rglob("*.json"))
            failures = sorted((directory / "fail").rglob("*.json"))
            if not passes or not failures:
                print(f"Example suite requires nonempty {directory}/pass and fail directories.", file=sys.stderr)
                return 2
            if version == "0.3.0":
                missing = set(KNOWN_FAILURES_V03) - {p.name for p in failures}
                if missing:
                    print(f"Missing registered v0.3 negatives: {sorted(missing)}", file=sys.stderr)
                    return 2
            jobs.extend((p, True, version) for p in passes)
            jobs.extend((p, False, version) for p in failures)
    else:
        jobs = [(p, True, selected_version) for p in args.files]
    report = []
    io_failure = False
    for path, expect_valid, expected_version in jobs:
        readable = True
        document_valid = None
        runtime_test = False
        try:
            bundle = read_json(path)
        except OSError as exc:
            diagnostics = [Diagnostic("input", "file_read_error", "/", str(exc))]
            io_failure = True
            readable = False
        except (ValueError, UnicodeError, ArithmeticError, RecursionError) as exc:
            diagnostics = [Diagnostic("input", "invalid_json", "/", str(exc))]
            readable = False
        else:
            version = bundle.get("protocol_version") if isinstance(bundle, dict) else None
            if not isinstance(version, str) or version not in validators_by_version:
                diagnostics = [Diagnostic("schema", "unsupported_version", "/protocol_version", "Unsupported protocol version.")]
            elif expected_version and version != expected_version:
                diagnostics = [Diagnostic("schema", "version_mismatch", "/protocol_version", "Bundle version does not match the selected suite/version.")]
            else:
                # Canonical structure is always checked before semantic code, even
                # with a permissive --schema override. Overrides may only tighten it.
                diagnostics = validate_bundle(bundle, validators_by_version[version])
                if alternate:
                    extra = list(alternate.iter_errors(bundle))
                    if extra:
                        diagnostics.extend(schema_diagnostics(bundle, extra))
        document_valid = not diagnostics if readable else None
        if (suite and expected_version == "0.3.0" and not expect_valid
                and path.name in RUNTIME_FIXTURES and document_valid):
            runtime_test = True
            diagnostics.extend(runtime_fixture_pair(bundle, path.name, validators_by_version["0.3.0"]))
        valid = not diagnostics
        expectations = {"0.1.0": KNOWN_FAILURES, "0.2.0": KNOWN_FAILURES_V02,
                        "0.3.0": KNOWN_FAILURES_V03}.get(expected_version, {})
        expected_code = expectations.get(path.name) if suite and not expect_valid else None
        code_matches = expected_code is None or expected_code in {d.code for d in diagnostics}
        if suite and expected_version == "0.3.0" and not expect_valid and expected_code is None:
            code_matches = False  # New negatives must register an intended diagnostic.

        # A typo or unreadable fixture must not masquerade as a successful negative test.
        matched = readable and valid == expect_valid and code_matches
        report.append({"file": display_path(path), "expected": "accept" if expect_valid else "reject",
                       "actual": "accept" if valid else "reject", "matched": matched,
                       "document_valid": document_valid,
                       "validation_scope": "synthetic_runtime_fixture" if runtime_test else "document_consistency",
                       "expected_code": expected_code, "diagnostics": [asdict(d) for d in diagnostics]})
    matched_count = sum(r["matched"] for r in report)
    output = {"mode": "examples" if suite else "files", "scope": LIMITATIONS,
              "total": len(report), "matched": matched_count, "results": report}
    if args.json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for item in report:
            codes = sorted({d["code"] for d in item["diagnostics"]})
            suffix = f" [{', '.join(codes)}]" if codes else ""
            if item["validation_scope"] == "synthetic_runtime_fixture":
                suffix += " (synthetic runtime test; document accepted)"
                if item["matched"]:
                    suffix += " (repaired control accepted)"
            print(f"{'PASS' if item['matched'] else 'FAIL'} {item['file']} "
                  f"expected={item['expected']} actual={item['actual']}{suffix}")
            if not item["matched"]:
                for diagnostic in item["diagnostics"]:
                    print(f"  {diagnostic['path']}: {diagnostic['message']}")
        print(f"{matched_count}/{len(report)} expectations met.")
        print(LIMITATIONS)
    return 2 if io_failure else (0 if matched_count == len(report) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
