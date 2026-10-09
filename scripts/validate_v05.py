#!/usr/bin/env python3
"""TACP v0.5 post-remediation semantic validation.

This module validates remediation_outcome_bundle semantics after JSON Schema
validation. Runtime-only assertions remain explicit synthetic fixture checks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import validate_legacy as legacy

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/tacp-v0.5.schema.json"

MANDATORY_PROHIBITIONS = {
    "repeat_source_operation",
    "repeat_remediation_operation",
    "create_remediation_of_remediation",
    "self_expand_authority",
}

KNOWN_FAILURES_V05 = {
    "executor-success-without-verification.json": "post_remediation_observation_missing",
    "completed-with-partial-effect.json": "invalid_remediation_closure",
    "completed-with-ineffective-result.json": "invalid_remediation_closure",
    "completed-with-harmful-result.json": "invalid_remediation_closure",
    "completed-with-unresolved-result.json": "invalid_remediation_closure",
    "stale-post-remediation-evidence.json": "evidence_stale",
    "missing-post-remediation-observation.json": "post_remediation_observation_missing",
    "verification-operation-id-mismatch.json": "remediation_operation_mismatch",
    "closure-verification-ref-mismatch.json": "verification_ref_mismatch",
    "second-remediation-created.json": "remediation_chain_forbidden",
    "authority-expanded-after-failure.json": "authority_expansion_forbidden",
    "verification-after-deadline.json": "verification_deadline_exceeded",
    "not-dispatched-with-execution-evidence.json": "non_dispatch_conflict",
    "new-effect-silently-omitted.json": "new_effect_omitted",
    "not-dispatched-without-terminal-policy.json": "not_dispatched_policy_missing",
    "observation-after-verification.json": "observation_after_verification",
    "observation-outside-scope.json": "observation_scope_violation",
    "evidence-budget-exceeded.json": "evidence_budget_exceeded",
}

RUNTIME_FIXTURES_V05 = {
    "second-remediation-created.json",
    "authority-expanded-after-failure.json",
    "not-dispatched-with-execution-evidence.json",
    "new-effect-silently-omitted.json",
}


def diagnostic(code: str, path: str, message: str, layer: str = "semantic") -> legacy.Diagnostic:
    return legacy.Diagnostic(layer, code, path, message)


def _instant(value: str) -> Any:
    return legacy.instant(value)


def _typed_records(records: list[Any], record_type: str) -> list[tuple[int, dict[str, Any]]]:
    return [
        (i, row)
        for i, row in enumerate(records)
        if isinstance(row, dict) and row.get("record_type") == record_type
    ]


def validate_semantics(bundle: dict[str, Any]) -> list[legacy.Diagnostic]:
    errors: list[legacy.Diagnostic] = []

    def add(code: str, path: str, message: str) -> None:
        item = diagnostic(code, path, message)
        if item not in errors:
            errors.append(item)

    if bundle.get("document_type") != "remediation_outcome_bundle":
        add(
            "unsupported_v05_document_type",
            "/document_type",
            "The v0.5 native validator currently accepts remediation_outcome_bundle only.",
        )
        return errors

    records = bundle.get("records")
    if not isinstance(records, list):
        add("records_missing", "/records", "A remediation outcome bundle requires records.")
        return errors

    observations = _typed_records(records, "post_remediation_observation")
    verifications = _typed_records(records, "remediation_verification")
    closures = _typed_records(records, "remediation_closure")

    if not observations:
        add(
            "post_remediation_observation_missing",
            "/records",
            "At least one independent post-remediation observation is required.",
        )
    if len(verifications) != 1:
        add(
            "verification_cardinality_invalid",
            "/records",
            "Exactly one remediation_verification is required.",
        )
    if len(closures) != 1:
        add(
            "closure_cardinality_invalid",
            "/records",
            "Exactly one remediation_closure is required.",
        )

    limits = bundle.get("verification_limits") if isinstance(bundle.get("verification_limits"), dict) else {}
    max_observations = limits.get("max_observation_count")
    if isinstance(max_observations, int) and len(observations) > max_observations:
        add(
            "observation_limit_exceeded",
            "/records",
            "Post-remediation observation count exceeds max_observation_count.",
        )

    scope = limits.get("observation_scope")
    scope_set = set(scope) if isinstance(scope, list) else set()
    if scope_set:
        for obs_i, observation in observations:
            target_refs = observation.get("target_refs")
            target_refs = target_refs if isinstance(target_refs, list) else []
            outside = sorted({ref for ref in target_refs if ref not in scope_set})
            if outside:
                add(
                    "observation_scope_violation",
                    f"/records/{obs_i}/target_refs",
                    "Post-remediation observation target_refs MUST remain inside verification_limits.observation_scope.",
                )

    evidence_budget = limits.get("evidence_retrieval_budget")
    if isinstance(evidence_budget, int):
        unique_evidence = {
            ref
            for _, observation in observations
            for ref in (observation.get("evidence_refs") or [])
            if isinstance(ref, str)
        }
        if len(unique_evidence) > evidence_budget:
            add(
                "evidence_budget_exceeded",
                "/verification_limits/evidence_retrieval_budget",
                "Unique evidence references exceed the declared evidence_retrieval_budget.",
            )

    bundle_outcome = bundle.get("outcome_id")
    bundle_remediation = bundle.get("remediation_ref")
    bundle_operation = bundle.get("remediation_operation_id")
    for i, row in enumerate(records):
        if not isinstance(row, dict):
            continue
        if row.get("outcome_id") != bundle_outcome:
            add("outcome_identity_mismatch", f"/records/{i}/outcome_id", "Record outcome_id MUST match the bundle outcome_id.")
        if row.get("remediation_ref") != bundle_remediation:
            add("remediation_reference_mismatch", f"/records/{i}/remediation_ref", "Record remediation_ref MUST match the bundle remediation_ref.")
        if row.get("remediation_operation_id") != bundle_operation:
            add("remediation_operation_mismatch", f"/records/{i}/remediation_operation_id", "Record remediation_operation_id MUST match the bundle remediation_operation_id.")

    if observations and verifications:
        verification_i, verification = verifications[0]
        observation_ids = {
            row.get("record_id")
            for _, row in observations
            if isinstance(row.get("record_id"), str)
        }
        refs = verification.get("observation_refs")
        refs = refs if isinstance(refs, list) else []
        missing_refs = [ref for ref in refs if ref not in observation_ids]
        if missing_refs or not refs:
            add(
                "observation_ref_invalid",
                f"/records/{verification_i}/observation_refs",
                "Verification MUST reference existing post-remediation observation records.",
            )

        if any(i > verification_i for i, _ in observations):
            add(
                "record_order_invalid",
                f"/records/{verification_i}",
                "All post-remediation observations MUST precede verification.",
            )

        evaluated_at = verification.get("evaluated_at")
        max_age = limits.get("max_verification_age_seconds")
        if isinstance(evaluated_at, str) and isinstance(max_age, int):
            try:
                evaluated = _instant(evaluated_at)
                for obs_i, observation in observations:
                    observed_at = observation.get("observed_at")
                    if isinstance(observed_at, str):
                        age = evaluated - _instant(observed_at)
                        if age < 0:
                            add(
                                "observation_after_verification",
                                f"/records/{obs_i}/observed_at",
                                "A post-remediation observation MUST NOT occur after the verification evaluation time.",
                            )
                        elif age > max_age:
                            add(
                                "evidence_stale",
                                f"/records/{obs_i}/observed_at",
                                "Post-remediation evidence exceeds max_verification_age_seconds.",
                            )
            except ValueError:
                pass

        deadline = limits.get("final_verification_deadline")
        if isinstance(evaluated_at, str) and isinstance(deadline, str):
            try:
                if _instant(evaluated_at) > _instant(deadline):
                    add(
                        "verification_deadline_exceeded",
                        f"/records/{verification_i}/evaluated_at",
                        "Verification MUST NOT be finalized after final_verification_deadline.",
                    )
            except ValueError:
                pass

    if verifications and closures:
        verification_i, verification = verifications[0]
        closure_i, closure = closures[0]
        if closure_i != len(records) - 1:
            add("closure_not_final", f"/records/{closure_i}", "remediation_closure MUST be the final record.")
        if verification_i > closure_i:
            add("record_order_invalid", f"/records/{closure_i}", "Verification MUST precede closure.")
        if closure.get("verification_ref") != verification.get("record_id"):
            add(
                "verification_ref_mismatch",
                f"/records/{closure_i}/verification_ref",
                "Closure MUST reference the exact remediation_verification record.",
            )

        result = verification.get("result")
        status = closure.get("status")
        escalation_required = closure.get("escalation_required")
        escalation_results = {
            "confirmed_partially_effective",
            "confirmed_ineffective",
            "confirmed_harmful",
            "unresolved",
        }
        if result == "confirmed_effective":
            if status != "completed" or escalation_required is not False:
                add("invalid_remediation_closure", f"/records/{closure_i}/status", "confirmed_effective MUST close as completed without escalation.")
        elif result in escalation_results:
            if status != "escalated" or escalation_required is not True:
                add("invalid_remediation_closure", f"/records/{closure_i}/status", f"{result} MUST close as escalated.")
        elif result == "not_dispatched":
            if status == "completed":
                terminal_policy = bundle.get("terminal_policy")
                allowed = (
                    isinstance(terminal_policy, dict)
                    and terminal_policy.get("not_dispatched") == "completed"
                )
                if not allowed:
                    add(
                        "not_dispatched_policy_missing",
                        "/terminal_policy/not_dispatched",
                        "not_dispatched MAY close as completed only when the bundle explicitly declares that terminal policy.",
                    )
                if escalation_required is not False:
                    add("invalid_remediation_closure", f"/records/{closure_i}/status", "A completed not_dispatched closure MUST NOT require escalation.")
            elif status == "escalated":
                if escalation_required is not True:
                    add("invalid_remediation_closure", f"/records/{closure_i}/status", "An escalated not_dispatched closure MUST require escalation.")
            else:
                add("invalid_remediation_closure", f"/records/{closure_i}/status", "not_dispatched MUST close as completed-by-explicit-policy or escalated.")

        if status == "escalated":
            prohibited = set(closure.get("prohibited_automatic_actions") or [])
            missing = MANDATORY_PROHIBITIONS - prohibited
            if missing:
                add(
                    "mandatory_prohibition_missing",
                    f"/records/{closure_i}/prohibited_automatic_actions",
                    "Escalated closure MUST prohibit repeat, recursive remediation, and self authority expansion.",
                )
            scope_values = closure.get("escalation_scope")
            if not isinstance(scope_values, list) or not scope_values:
                add("escalation_scope_missing", f"/records/{closure_i}/escalation_scope", "Escalated closure requires nonempty escalation_scope.")

        remaining = verification.get("remaining_effects") or []
        new_effects = verification.get("new_effects") or []
        uncertainties = verification.get("uncertainties") or []
        if result == "confirmed_partially_effective" and not remaining:
            add("partial_effect_missing", f"/records/{verification_i}/remaining_effects", "confirmed_partially_effective requires remaining_effects.")
        if result == "confirmed_ineffective" and not remaining:
            add("ineffective_effect_missing", f"/records/{verification_i}/remaining_effects", "confirmed_ineffective requires remaining_effects.")
        if result == "confirmed_harmful" and not new_effects:
            add("harmful_effect_missing", f"/records/{verification_i}/new_effects", "confirmed_harmful requires new_effects.")
        if result == "unresolved" and not uncertainties:
            add("unresolved_uncertainty_missing", f"/records/{verification_i}/uncertainties", "unresolved requires explicit uncertainty.")
        if result == "confirmed_effective" and (remaining or new_effects or uncertainties):
            add("effective_result_conflict", f"/records/{verification_i}/result", "confirmed_effective MUST NOT retain blocking remaining effects, new effects, or unresolved uncertainty.")

    return errors


def validate_document(bundle: dict[str, Any], validator: Any) -> list[legacy.Diagnostic]:
    semantic = validate_semantics(bundle)
    schema_errors = sorted(
        validator.iter_errors(bundle),
        key=lambda e: (legacy.pointer(e.absolute_path), str(e.validator)),
    )
    if schema_errors:
        return legacy.schema_diagnostics(bundle, schema_errors) + semantic
    return semantic


def runtime_fixture(bundle: dict[str, Any], name: str) -> list[legacy.Diagnostic]:
    if name == "second-remediation-created.json":
        evidence = bundle.get("extensions", {}).get("runtime_evidence", {})
        if evidence.get("successor_remediation_created") is True and evidence.get("creation_mode") == "automatic":
            return [diagnostic(
                "remediation_chain_forbidden",
                "/extensions/runtime_evidence/successor_remediation_created",
                "Automatic successor remediation is forbidden after v0.5 terminal escalation.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/extensions/runtime_evidence", "Expected automatic successor remediation evidence.", layer="harness")]

    if name == "authority-expanded-after-failure.json":
        action = bundle.get("extensions", {}).get("invalid_follow_on_action", {})
        if action.get("action_type") == "authority_expansion" and str(action.get("authorization_source", "")).startswith("self-issued"):
            return [diagnostic(
                "authority_expansion_forbidden",
                "/extensions/invalid_follow_on_action",
                "An agent MUST NOT self-expand authority after remediation failure.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/extensions/invalid_follow_on_action", "Expected self-issued authority expansion evidence.", layer="harness")]

    if name == "not-dispatched-with-execution-evidence.json":
        records = bundle.get("records") if isinstance(bundle.get("records"), list) else []
        verification = next((r for r in records if isinstance(r, dict) and r.get("record_type") == "remediation_verification"), {})
        observations = [r for r in records if isinstance(r, dict) and r.get("record_type") == "post_remediation_observation"]
        refs = [str(ref).lower() for row in observations for ref in (row.get("evidence_refs") or [])]
        text = " ".join(str(x).lower() for row in observations for x in (row.get("observed_effects") or []))
        execution_evidence = any("execution" in ref for ref in refs) or "crossed the execution boundary" in text
        if verification.get("result") == "not_dispatched" and execution_evidence:
            return [diagnostic(
                "non_dispatch_conflict",
                "/records",
                "not_dispatched conflicts with authoritative execution evidence.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/records", "Expected not_dispatched plus execution evidence.", layer="harness")]

    if name == "new-effect-silently-omitted.json":
        records = bundle.get("records") if isinstance(bundle.get("records"), list) else []
        verification = next((r for r in records if isinstance(r, dict) and r.get("record_type") == "remediation_verification"), {})
        observations = [r for r in records if isinstance(r, dict) and r.get("record_type") == "post_remediation_observation"]
        observed_text = " ".join(str(x).lower() for row in observations for x in (row.get("observed_effects") or []))
        adverse_observed = "new remediation-induced" in observed_text or "new adverse effect" in observed_text
        if adverse_observed and not (verification.get("new_effects") or []):
            return [diagnostic(
                "new_effect_omitted",
                "/records",
                "A newly observed adverse effect was omitted from remediation_verification.new_effects.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/records", "Expected observed new adverse effect omitted from verification.", layer="harness")]

    return []
