#!/usr/bin/env python3
"""Validate TACP v0.1 closed mission bundles (Python 3.10+).

Dependency: python -m pip install "jsonschema>=4.18,<5"

From the repository root:
  python scripts/validate.py
  python scripts/validate.py --examples --json
  python scripts/validate.py examples/pass/mission-completed.json
  python scripts/validate.py examples/fail/stale-observation.json --json

No positional paths means the examples suite: files in examples/pass must be
accepted and files in examples/fail must be rejected. Direct file mode always
requires acceptance, including files whose directory happens to be named fail.
Exit codes: 0 = all expectations met; 1 = validation/expectation failure;
2 = dependency, schema, file-reading, or command configuration error.

The schema is resolved relative to this script, not the working directory.
All schema references must be local fragments; no network requests are made.
JSON duplicate keys, non-finite numbers, and invalid UTC dates are rejected.
Decimal numbers and timestamp fractions are compared without float rounding.

Scope: structural and mechanically checkable record-consistency requirements in
specs/tacp-v0.1.md. Natural-language evidence quality, materiality, independence,
issue classification, explicit stop rationale, external authorization/expiry,
live target state, and actual runtime enforcement require separate assessment.
External references are opaque; extensions (including fixture registries and
expected_validation) never grant authority or influence validation decisions.
This program neither dispatches actions nor certifies that a deployment is safe.
"""

from __future__ import annotations

import argparse
import calendar
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
DEFAULT_SCHEMA = ROOT / "schemas/tacp-v0.1.schema.json"
UTC_PATTERN = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]+))?Z$")
LIMITATIONS = (
    "Record consistency only; no runtime enforcement or external authorization verification. "
    "Natural-language evidence, independence, issue classification, material changes, and "
    "controller stop rationale require separate assessment. Extensions are not trusted evidence."
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
            if not final or row["disposition"] == "completed":
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
                    if last_review_assessment != row["assessment_ref"]:
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
                                     and review["decision"] == "pass" and not pending_resolutions,
                                     "gate_not_ready", i, "decision", "Allow requires current ready assessment and passing review.")
                        if review:
                            self.require(instant(row["checked_at"]) >= instant(review["created_at"]),
                                         "gate_time", i, "checked_at", "Gate check predates its review.")
                        self.changed_state(assessment, last_review_index, i)
                latest_gate = row
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
    return result


def validate_bundle(bundle: Any, validator: Any) -> list[Diagnostic]:
    errors = sorted(validator.iter_errors(bundle), key=lambda e: (pointer(e.absolute_path), str(e.validator)))
    if errors:
        return schema_diagnostics(bundle, errors)
    return SemanticValidator(bundle).run()


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
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Alternate local Draft 2020-12 schema.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit a machine-readable report.")
    args = parser.parse_args(argv)
    if args.examples and args.files:
        parser.error("--examples cannot be combined with positional files")
    suite = args.examples or not args.files
    try:
        validator = load_validator(args.schema)
    except (OSError, ValueError, SchemaError, ArithmeticError) as exc:
        print(f"Schema configuration error: {exc}", file=sys.stderr)
        return 2
    if suite:
        passes = sorted((ROOT / "examples/pass").rglob("*.json"))
        failures = sorted((ROOT / "examples/fail").rglob("*.json"))
        if not passes or not failures:
            print("Example suite requires nonempty examples/pass and examples/fail directories.", file=sys.stderr)
            return 2
        jobs = [(p, True) for p in passes] + [(p, False) for p in failures]
    else:
        jobs = [(p, True) for p in args.files]
    report = []
    io_failure = False
    for path, expect_valid in jobs:
        readable = True
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
            diagnostics = validate_bundle(bundle, validator)
        valid = not diagnostics
        expected_code = KNOWN_FAILURES.get(path.name) if suite and not expect_valid else None
        code_matches = expected_code is None or expected_code in {d.code for d in diagnostics}
        # A typo or unreadable fixture must not masquerade as a successful negative test.
        matched = readable and valid == expect_valid and code_matches
        report.append({"file": display_path(path), "expected": "accept" if expect_valid else "reject",
                       "actual": "accept" if valid else "reject", "matched": matched,
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
