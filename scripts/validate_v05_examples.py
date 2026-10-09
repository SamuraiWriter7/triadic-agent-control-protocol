#!/usr/bin/env python3
"""Run the registered TACP v0.5 example suite."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import validate_legacy as legacy
import validate_v05 as v05

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples/v0.5"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        validator = legacy.load_validator(v05.SCHEMA)
    except Exception as exc:
        print(f"Schema configuration error: {exc}", file=sys.stderr)
        return 2

    passes = sorted((EXAMPLES / "pass").rglob("*.json"))
    failures = sorted((EXAMPLES / "fail").rglob("*.json"))
    if not passes or not failures:
        print("v0.5 example suite requires nonempty pass and fail directories.", file=sys.stderr)
        return 2

    failure_names = {path.name for path in failures}
    missing = set(v05.KNOWN_FAILURES_V05) - failure_names
    unregistered = failure_names - set(v05.KNOWN_FAILURES_V05)
    if missing:
        print(f"Missing registered v0.5 negatives: {sorted(missing)}", file=sys.stderr)
        return 2
    if unregistered:
        print(f"Unregistered v0.5 negatives: {sorted(unregistered)}", file=sys.stderr)
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
            diagnostics = [v05.diagnostic("file_read_error", "/", str(exc), layer="input")]
            readable = False
            io_failure = True
        except Exception as exc:
            diagnostics = [v05.diagnostic("invalid_json", "/", str(exc), layer="input")]
            readable = False
        else:
            version = bundle.get("protocol_version") if isinstance(bundle, dict) else None
            if version != "0.5.0":
                diagnostics = [
                    v05.diagnostic(
                        "version_mismatch",
                        "/protocol_version",
                        "v0.5 example suite requires protocol_version 0.5.0.",
                        layer="schema",
                    )
                ]
            else:
                diagnostics = v05.validate_document(bundle, validator)

        document_valid = not diagnostics if readable else None

        if (
            readable
            and not expect_valid
            and path.name in v05.RUNTIME_FIXTURES_V05
            and document_valid
        ):
            runtime_test = True
            diagnostics.extend(v05.runtime_fixture(bundle, path.name))

        valid = not diagnostics
        expected_code = v05.KNOWN_FAILURES_V05.get(path.name) if not expect_valid else None
        code_matches = expected_code is None or expected_code in {d.code for d in diagnostics}
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
        "mode": "v0.5-examples",
        "scope": (
            "Document consistency plus explicitly marked synthetic runtime fixtures. "
            "Conformance does not prove evidence authenticity, external effect truth, "
            "runtime privilege isolation, or that escalation reached an authorized human process."
        ),
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
        print(output["scope"])

    return 2 if io_failure else (0 if matched_count == len(report) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
