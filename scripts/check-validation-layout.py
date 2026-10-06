#!/usr/bin/env python3

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALIDATOR = ROOT / "scripts" / "validate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

REQUIRED_VERSIONS = {
    "0.1.0": ROOT / "examples",
    "0.2.0": ROOT / "examples" / "v0.2",
    "0.3.0": ROOT / "examples" / "v0.3",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_validator() -> str:
    if not VALIDATOR.is_file():
        fail("scripts/validate.py is missing.")

    text = VALIDATOR.read_text(encoding="utf-8")

    try:
        ast.parse(text, filename=str(VALIDATOR))
    except SyntaxError as error:
        fail(
            "scripts/validate.py is not valid Python: "
            f"{error.msg} at line {error.lineno}"
        )

    if "def " not in text:
        fail("scripts/validate.py does not appear to contain Python functions.")

    return text


def check_fixture_directories() -> None:
    for version, path in REQUIRED_VERSIONS.items():
        if not path.is_dir():
            fail(
                f"Fixture directory for TACP {version} is missing: "
                f"{path.relative_to(ROOT)}"
            )


def extract_registered_v03_fixtures(validator_text: str) -> set[str]:
    """
    Detect JSON fixture names explicitly registered in validate.py.

    This intentionally checks only literal *.json references so that
    generated/runtime values are not mistaken for fixture declarations.
    """
    return set(
        re.findall(
            r'["\']([A-Za-z0-9._-]+\.json)["\']',
            validator_text,
        )
    )


def check_registered_v03_fixtures(validator_text: str) -> None:
    fail_dir = ROOT / "examples" / "v0.3" / "fail"

    if not fail_dir.is_dir():
        fail("examples/v0.3/fail is missing.")

    registered = extract_registered_v03_fixtures(validator_text)

    existing = {
        path.name
        for path in fail_dir.iterdir()
        if path.is_file() and path.suffix == ".json"
    }

    # Only names that look like v0.3 fail fixtures and are referenced
    # by the validator are relevant here.
    missing = sorted(
        name
        for name in registered
        if name not in existing
        and (
            "recovery" in name
            or "source" in name
            or "successor" in name
            or "claim" in name
            or "effect" in name
        )
    )

    if missing:
        fail(
            "Validator references missing v0.3 fixtures: "
            + ", ".join(missing)
        )

    suspicious_extensions = sorted(
        path.name
        for path in fail_dir.iterdir()
        if path.is_file()
        and path.suffix != ".json"
        and path.name.startswith(
            (
                "target-",
                "source-",
                "successor-",
                "recovery-",
                "duplicate-",
            )
        )
    )

    if suspicious_extensions:
        fail(
            "Suspicious v0.3 fixture extensions: "
            + ", ".join(suspicious_extensions)
        )


def check_workflow() -> None:
    if not WORKFLOW.is_file():
        fail(".github/workflows/validate.yml is missing.")

    text = WORKFLOW.read_text(encoding="utf-8")

    required_commands = (
        "python -m py_compile scripts/validate.py",
        "--version 0.1.0",
        "--version 0.2.0",
        "--version 0.3.0",
    )

    for command in required_commands:
        if command not in text:
            fail(
                "Workflow is missing required validator invocation: "
                f"{command}"
            )

    if "scripts/validate.py" not in text:
        fail("Workflow does not invoke scripts/validate.py.")


def main() -> int:
    validator_text = check_validator()
    check_fixture_directories()
    check_registered_v03_fixtures(validator_text)
    check_workflow()

    print("Validation-system preflight passed.")
    print("- validator: Python syntax OK")
    print("- fixture directories: present")
    print("- registered v0.3 fixtures: present")
    print("- workflow bindings: present")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
