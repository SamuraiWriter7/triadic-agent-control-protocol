#!/usr/bin/env python3
"""Validate TACP v0.1-v0.4 bundles.

v0.1-v0.3 validation is delegated unchanged to scripts/validate_legacy.py.
v0.4 adds remediation semantics, runtime-recovery wrappers, and synthetic
runtime checks while preserving document-only validation boundaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import validate_legacy as legacy

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = dict(legacy.SCHEMAS)
SCHEMAS["0.4.0"] = ROOT / "schemas/tacp-v0.4.schema.json"
LIMITATIONS = (
    legacy.LIMITATIONS
    + " TACP v0.4 remediation uniqueness and runtime-recovery completion "
      "remain synthetic/runtime-scoped checks."
)

KNOWN_FAILURES_V04 = {
    "same-operation-id.json": "operation_identity_reused",
    "missing-causal-link.json": "causal_link_missing",
    "impact-unresolved-but-executed.json": "effect_scope_unresolved",
    "missing-human-review.json": "human_review_missing",
    "expired-human-approval.json": "human_approval_expired",
    "source-authorization-reused.json": "source_authorization_reused",
    "remediation-without-admission.json": "remediation_admission_missing",
    "duplicate-remediation.json": "duplicate_remediation",
    "remediation-of-remediation.json": "remediation_of_remediation",
}

RUNTIME_FIXTURES_V04 = {"duplicate-remediation.json"}


def diagnostic(code: str, path: str, message: str, layer: str = "semantic") -> legacy.Diagnostic:
    return legacy.Diagnostic(layer, code, path, message)


def _record_index(records: list[Any]) -> dict[str, tuple[int, dict[str, Any]]]:
    out: dict[str, tuple[int, dict[str, Any]]] = {}
    for i, row in enumerate(records):
        if isinstance(row, dict) and isinstance(row.get("record_type"), str):
            out.setdefault(row["record_type"], (i, row))
    return out


def validate_v04_remediation(bundle: dict[str, Any]) -> list[legacy.Diagnostic]:
    errors: list[legacy.Diagnostic] = []

    def add(code: str, path: str, message: str) -> None:
        item = diagnostic(code, path, message)
        if item not in errors:
            errors.append(item)

    if bundle.get("document_type") == "mission_bundle":
        if "remediation_ref" in bundle:
            add(
                "missing_remediation_context",
                "/remediation_ref",
                "A remediation mission requires its enclosing remediation bundle.",
            )
        return errors

    if bundle.get("document_type") != "remediation_bundle":
        return errors

    source = bundle.get("source") if isinstance(bundle.get("source"), dict) else {}
    if source.get("remediation_ref") is not None:
        add(
            "remediation_of_remediation",
            "/source/remediation_ref",
            "A remediation mission MUST NOT become the source of another remediation.",
        )

    records = bundle.get("records")
    if not isinstance(records, list):
        return errors

    indexed = _record_index(records)
    impact_i, impact = indexed.get("impact_assessment", (None, None))
    plan_i, plan = indexed.get("remediation_plan", (None, None))
    review_i, review = indexed.get("human_review", (None, None))
    admission_i, admission = indexed.get("remediation_admission", (None, None))
    remediation_mission = bundle.get("remediation_mission")

    if review is None:
        add(
            "human_review_missing",
            "/records",
            "A v0.4 remediation bundle requires a human_review.",
        )

    if remediation_mission is not None and admission is None:
        add(
            "remediation_admission_missing",
            "/remediation_mission",
            "A remediation mission MUST NOT exist before remediation_admission.",
        )

    if remediation_mission is not None and admission is not None and admission.get("decision") != "allow":
        add(
            "remediation_not_admitted",
            "/remediation_mission",
            "A remediation mission MAY exist only after an allow admission.",
        )

    if plan is None:
        return errors

    source_operation_id = plan.get("source_operation_id")
    remediation_operation_id = plan.get("remediation_operation_id")

    if (
        isinstance(source_operation_id, str)
        and isinstance(remediation_operation_id, str)
        and source_operation_id == remediation_operation_id
    ):
        add(
            "operation_identity_reused",
            f"/records/{plan_i}/remediation_operation_id",
            "A remediation MUST use a new operation identity.",
        )

    proposed = plan.get("proposed_action") if isinstance(plan.get("proposed_action"), dict) else {}
    if (
        isinstance(remediation_operation_id, str)
        and isinstance(proposed.get("operation_id"), str)
        and proposed.get("operation_id") != remediation_operation_id
    ):
        add(
            "remediation_action_identity_mismatch",
            f"/records/{plan_i}/proposed_action/operation_id",
            "The proposed action MUST retain remediation_operation_id.",
        )

    causal = plan.get("compensates_operation_ref")
    if not isinstance(causal, str) or not causal:
        add(
            "causal_link_missing",
            f"/records/{plan_i}/compensates_operation_ref",
            "A remediation plan MUST identify the source operation it remediates.",
        )
    elif isinstance(source_operation_id, str) and causal != source_operation_id:
        add(
            "causal_link_invalid",
            f"/records/{plan_i}/compensates_operation_ref",
            "The causal reference MUST identify the exact source operation.",
        )

    if impact is not None:
        if impact.get("source_operation_id") != source_operation_id:
            add(
                "source_operation_mismatch",
                f"/records/{plan_i}/source_operation_id",
                "Plan and impact assessment MUST bind the same source operation.",
            )

        if (
            plan.get("remediation_type") in {"compensate", "correct"}
            and impact.get("effect_scope") == "unresolved"
        ):
            add(
                "effect_scope_unresolved",
                f"/records/{impact_i}/effect_scope",
                "State-changing remediation MUST NOT proceed with unresolved effect scope.",
            )

        if (
            remediation_mission is not None
            and plan.get("remediation_type") in {"compensate", "correct"}
            and impact.get("effect_scope") == "unresolved"
        ):
            add(
                "remediation_executed_with_unresolved_impact",
                "/remediation_mission",
                "A state-changing remediation mission MUST NOT exist with unresolved impact scope.",
            )

    source_records = source.get("records") if isinstance(source.get("records"), list) else []
    source_missions = [
        row for row in source_records
        if isinstance(row, dict) and row.get("record_type") == "mission"
    ]
    source_auth = source_missions[0].get("authorization_ref") if len(source_missions) == 1 else None
    if isinstance(source_auth, str) and source_auth == plan.get("authorization_ref"):
        add(
            "source_authorization_reused",
            f"/records/{plan_i}/authorization_ref",
            "Remediation MUST use independently valid authorization.",
        )

    if review is not None:
        if impact is not None and review.get("impact_assessment_ref") != impact.get("record_id"):
            add(
                "human_review_reference_mismatch",
                f"/records/{review_i}/impact_assessment_ref",
                "Human review MUST bind the exact impact assessment.",
            )
        if review.get("remediation_plan_ref") != plan.get("record_id"):
            add(
                "human_review_reference_mismatch",
                f"/records/{review_i}/remediation_plan_ref",
                "Human review MUST bind the exact remediation plan.",
            )

    if admission is not None and review is not None:
        if admission.get("human_review_ref") != review.get("record_id"):
            add(
                "human_review_reference_mismatch",
                f"/records/{admission_i}/human_review_ref",
                "Admission MUST reference the exact human review.",
            )
        checked_at = admission.get("checked_at")
        valid_until = review.get("valid_until")
        if isinstance(checked_at, str) and isinstance(valid_until, str):
            if legacy.instant(checked_at) >= legacy.instant(valid_until):
                add(
                    "human_approval_expired",
                    f"/records/{admission_i}/checks/human_approval_valid",
                    "Human approval MUST remain valid at admission.",
                )
        start_before = admission.get("start_before")
        if (
            admission.get("decision") == "allow"
            and isinstance(start_before, str)
            and isinstance(valid_until, str)
            and legacy.instant(start_before) > legacy.instant(valid_until)
        ):
            add(
                "start_after_human_approval_expiry",
                f"/records/{admission_i}/start_before",
                "start_before MUST NOT exceed human approval validity.",
            )

    if isinstance(remediation_mission, dict):
        if remediation_mission.get("remediation_ref") != bundle.get("remediation_id"):
            add(
                "remediation_reference_mismatch",
                "/remediation_mission/remediation_ref",
                "Embedded remediation mission MUST bind the enclosing remediation_id.",
            )
        mission_rows = remediation_mission.get("records")
        mission_rows = mission_rows if isinstance(mission_rows, list) else []
        mission_headers = [
            row for row in mission_rows
            if isinstance(row, dict) and row.get("record_type") == "mission"
        ]
        if len(mission_headers) == 1:
            header = mission_headers[0]
            if header.get("operation_id") != remediation_operation_id:
                add(
                    "remediation_operation_mismatch",
                    "/remediation_mission/records/0/operation_id",
                    "The remediation mission MUST retain the reviewed operation identity.",
                )
            if header.get("authorization_ref") != plan.get("authorization_ref"):
                add(
                    "remediation_authorization_mismatch",
                    "/remediation_mission/records/0/authorization_ref",
                    "The remediation mission MUST retain the reviewed authorization.",
                )

    return errors


def validate_runtime_recovery_wrapper(bundle: dict[str, Any]) -> list[legacy.Diagnostic]:
    errors: list[legacy.Diagnostic] = []
    recovery = bundle.get("recovery")
    if not isinstance(recovery, dict):
        return [diagnostic("runtime_recovery_missing", "/recovery", "runtime_recovery_bundle requires recovery.")]
    if recovery.get("protocol_version") != "0.3.0" or recovery.get("document_type") != "recovery_bundle":
        return [
            diagnostic(
                "runtime_recovery_invalid",
                "/recovery",
                "runtime_recovery_bundle MUST embed a canonical v0.3 recovery_bundle.",
            )
        ]
    v03_validator = legacy.load_validator(legacy.SCHEMAS["0.3.0"])
    nested = legacy.validate_bundle(recovery, v03_validator)
    errors.extend(
        legacy.Diagnostic(d.layer, d.code, "/recovery" + d.path, d.message)
        for d in nested
    )
    return errors


def validate_v04_document(bundle: dict[str, Any], validator: Any) -> list[legacy.Diagnostic]:
    if bundle.get("document_type") == "runtime_recovery_bundle":
        return validate_runtime_recovery_wrapper(bundle)
    schema_errors = sorted(
        validator.iter_errors(bundle),
        key=lambda e: (legacy.pointer(e.absolute_path), str(e.validator)),
    )
    if schema_errors:
        return legacy.schema_diagnostics(bundle, schema_errors)
    return validate_v04_remediation(bundle)


def runtime_fixture_v04(bundle: dict[str, Any], name: str) -> list[legacy.Diagnostic]:
    if name != "duplicate-remediation.json":
        return []
    try:
        state = bundle["extensions"]["synthetic_runtime_state"]["existing_remediation"]
        impact = bundle["records"][0]
        if any(
            state.get(key) != impact.get(key)
            for key in ("source_mission_ref", "source_closure_ref", "source_operation_id")
        ):
            raise ValueError("Synthetic existing remediation does not bind the candidate source effect.")
        if state.get("remediation_id") == bundle.get("remediation_id"):
            raise ValueError("Synthetic existing remediation must be distinct from the candidate.")
        if state.get("status") not in {"admitted", "claimed", "running", "completed"}:
            raise ValueError("Synthetic existing remediation does not consume the remediation slot.")
        return [
            diagnostic(
                "duplicate_remediation",
                "/records/3/checks/duplicate_remediation_absent",
                "Synthetic authoritative state already contains remediation for this source effect.",
                layer="runtime_fixture",
            )
        ]
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return [
            diagnostic(
                "runtime_fixture_invalid",
                "/extensions/synthetic_runtime_state",
                str(exc),
                layer="harness",
            )
        ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--version", choices=tuple(SCHEMAS))
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    if args.examples and args.files:
        parser.error("--examples cannot be combined with positional files")

    suite = args.examples or not args.files

    try:
        validators = {version: legacy.load_validator(path) for version, path in SCHEMAS.items()}
    except Exception as exc:
        print(f"Schema configuration error: {exc}", file=sys.stderr)
        return 2

    selected = args.version
    if args.schema:
        print("--schema override is not supported by the v0.4 front controller yet.", file=sys.stderr)
        return 2

    if suite:
        jobs: list[tuple[Path, bool, str]] = []
        suites = (
            ("0.1.0", ROOT / "examples"),
            ("0.2.0", ROOT / "examples/v0.2"),
            ("0.3.0", ROOT / "examples/v0.3"),
            ("0.4.0", ROOT / "examples/v0.4"),
        )
        for version, directory in suites:
            if selected and selected != version:
                continue
            passes = sorted((directory / "pass").rglob("*.json"))
            failures = sorted((directory / "fail").rglob("*.json"))
            if not passes or not failures:
                print(f"Example suite requires nonempty {directory}/pass and fail directories.", file=sys.stderr)
                return 2
            if version == "0.3.0":
                missing = set(legacy.KNOWN_FAILURES_V03) - {p.name for p in failures}
                if missing:
                    print(f"Missing registered v0.3 negatives: {sorted(missing)}", file=sys.stderr)
                    return 2
            if version == "0.4.0":
                missing = set(KNOWN_FAILURES_V04) - {p.name for p in failures}
                if missing:
                    print(f"Missing registered v0.4 negatives: {sorted(missing)}", file=sys.stderr)
                    return 2
            jobs.extend((p, True, version) for p in passes)
            jobs.extend((p, False, version) for p in failures)
    else:
        jobs = [(path, True, selected) for path in args.files]

    expectations = {
        "0.1.0": legacy.KNOWN_FAILURES,
        "0.2.0": legacy.KNOWN_FAILURES_V02,
        "0.3.0": legacy.KNOWN_FAILURES_V03,
        "0.4.0": KNOWN_FAILURES_V04,
    }

    report: list[dict[str, Any]] = []
    io_failure = False

    for path, expect_valid, expected_version in jobs:
        readable = True
        runtime_test = False
        try:
            bundle = legacy.read_json(path)
        except OSError as exc:
            diagnostics = [diagnostic("file_read_error", "/", str(exc), layer="input")]
            readable = False
            io_failure = True
        except Exception as exc:
            diagnostics = [diagnostic("invalid_json", "/", str(exc), layer="input")]
            readable = False
        else:
            version = bundle.get("protocol_version") if isinstance(bundle, dict) else None
            if not isinstance(version, str) or version not in SCHEMAS:
                diagnostics = [diagnostic("unsupported_version", "/protocol_version", "Unsupported protocol version.", layer="schema")]
            elif expected_version and version != expected_version:
                diagnostics = [diagnostic("version_mismatch", "/protocol_version", "Bundle version does not match the selected suite/version.", layer="schema")]
            elif version == "0.4.0":
                diagnostics = validate_v04_document(bundle, validators["0.4.0"])
            else:
                diagnostics = legacy.validate_bundle(bundle, validators[version])

        document_valid = not diagnostics if readable else None

        if (
            suite
            and expected_version == "0.3.0"
            and not expect_valid
            and path.name in legacy.RUNTIME_FIXTURES
            and document_valid
        ):
            runtime_test = True
            diagnostics.extend(legacy.runtime_fixture_pair(bundle, path.name, validators["0.3.0"]))

        if (
            suite
            and expected_version == "0.4.0"
            and not expect_valid
            and path.name in RUNTIME_FIXTURES_V04
            and document_valid
        ):
            runtime_test = True
            diagnostics.extend(runtime_fixture_v04(bundle, path.name))

        valid = not diagnostics
        expected_code = (
            expectations.get(expected_version, {}).get(path.name)
            if suite and not expect_valid
            else None
        )
        code_matches = expected_code is None or expected_code in {d.code for d in diagnostics}
        if suite and expected_version in {"0.3.0", "0.4.0"} and not expect_valid and expected_code is None:
            code_matches = False
        matched = readable and valid == expect_valid and code_matches
        report.append(
            {
                "file": legacy.display_path(path),
                "expected": "accept" if expect_valid else "reject",
                "actual": "accept" if valid else "reject",
                "matched": matched,
                "document_valid": document_valid,
                "validation_scope": "synthetic_runtime_fixture" if runtime_test else "document_consistency",
                "expected_code": expected_code,
                "diagnostics": [asdict(d) for d in diagnostics],
            }
        )

    matched_count = sum(row["matched"] for row in report)
    output = {
        "mode": "examples" if suite else "files",
        "scope": LIMITATIONS,
        "total": len(report),
        "matched": matched_count,
        "results": report,
    }

    if args.json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for row in report:
            codes = sorted({d["code"] for d in row["diagnostics"]})
            suffix = f" [{', '.join(codes)}]" if codes else ""
            if row["validation_scope"] == "synthetic_runtime_fixture":
                suffix += " (synthetic runtime test; document accepted)"
            print(
                f"{'PASS' if row['matched'] else 'FAIL'} {row['file']} "
                f"expected={row['expected']} actual={row['actual']}{suffix}"
            )
            if not row["matched"]:
                for item in row["diagnostics"]:
                    print(f"  {item['path']}: {item['message']}")
        print(f"{matched_count}/{len(report)} expectations met.")
        print(LIMITATIONS)

    return 2 if io_failure else (0 if matched_count == len(report) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
