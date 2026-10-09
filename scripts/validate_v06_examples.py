#!/usr/bin/env python3
"""Run the registered TACP v0.6 escalation handoff example suite."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import validate_legacy as legacy
import validate_v06 as v06

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples/v0.6"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        validator = legacy.load_validator(v06.SCHEMA)
    except Exception as exc:
        print(f"Schema configuration error: {exc}", file=sys.stderr)
        return 2

    passes = sorted((EXAMPLES / "pass").rglob("*.json"))
    failures = sorted((EXAMPLES / "fail").rglob("*.json"))
    if not passes or not failures:
        print("v0.6 example suite requires nonempty pass and fail directories.", file=sys.stderr)
        return 2

    failure_names = {path.name for path in failures}
    registered_names = set(v06.KNOWN_FAILURES_V06)
    missing = registered_names - failure_names
    unregistered = failure_names - registered_names
    if missing:
        print(f"Missing registered v0.6 negatives: {sorted(missing)}", file=sys.stderr)
        return 2
    if unregistered:
        print(f"Unregistered v0.6 negatives: {sorted(unregistered)}", file=sys.stderr)
        return 2

    jobs = [(path, True) for path in passes] + [(path, False) for path in failures]
    report: list[dict[str, Any]] = []
    io_failure = False

    for path, expect_valid in jobs:
        readable = True
        runtime_test = False
        try:
            bundle = legacy.read_json(path)
        except OSError as exc:
            diagnostics = [v06.diagnostic("file_read_error", "/", str(exc), layer="input")]
            readable = False
            io_failure = True
        except Exception as exc:
            diagnostics = [v06.diagnostic("invalid_json", "/", str(exc), layer="input")]
            readable = False
        else:
            version = bundle.get("protocol_version") if isinstance(bundle, dict) else None
            if version != "0.6.0":
                diagnostics = [
                    v06.diagnostic(
                        "version_mismatch",
                        "/protocol_version",
                        "v0.6 example suite requires protocol_version 0.6.0.",
                        layer="schema",
                    )
                ]
            else:
                diagnostics = v06.validate_document(bundle, validator)

        document_valid = not diagnostics if readable else None

        if (
            readable
            and not expect_valid
            and path.name in v06.RUNTIME_FIXTURES_V06
            and document_valid
        ):
            runtime_test = True
            diagnostics.extend(v06.runtime_fixture(bundle, path.name))

        valid = not diagnostics
        expected_code = v06.KNOWN_FAILURES_V06.get(path.name) if not expect_valid else None
        observed_codes = {item.code for item in diagnostics}
        code_matches = expected_code is None or expected_code in observed_codes
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
                "diagnostics": [asdict(item) for item in diagnostics],
            }
        )

    matched_count = sum(row["matched"] for row in report)
    positive_count = len(passes)
    negative_count = len(failures)
    runtime_count = sum(
        1 for row in report if row["validation_scope"] == "synthetic_runtime_fixture"
    )

    output = {
        "mode": "v0.6-examples",
        "scope": (
            "Document consistency plus explicitly marked synthetic runtime fixtures. "
            "Conformance does not prove receiver identity authenticity, real-world authority, "
            "legal responsibility transfer, notification delivery truth, hidden remediation absence, "
            "or runtime privilege isolation outside the recorded fixture context."
        ),
        "positive_cases": positive_count,
        "negative_cases": negative_count,
        "synthetic_runtime_cases": runtime_count,
        "total": len(report),
        "matched": matched_count,
        "results": report,
    }

    if args.json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for row in report:
            codes = sorted({item["code"] for item in row["diagnostics"]})
            suffix = f" [{', '.join(codes)}]" if codes else ""
            if row["validation_scope"] == "synthetic_runtime_fixture":
                suffix += " (synthetic runtime test; document accepted)"
            print(
                f"{'PASS' if row['matched'] else 'FAIL'} {row['file']} "
                f"expected={row['expected']} actual={row['actual']}{suffix}"
            )
            if not row["matched"]:
                if row["expected_code"] is not None:
                    print(f"  expected diagnostic: {row['expected_code']}")
                for item in row["diagnostics"]:
                    print(f"  {item['path']}: {item['message']}")

        print(
            f"{matched_count}/{len(report)} expectations met "
            f"({positive_count} positive, {negative_count} negative, "
            f"{runtime_count} synthetic runtime)."
        )
        print(output["scope"])

    return 2 if io_failure else (0 if matched_count == len(report) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
