#!/usr/bin/env python3
"""TACP v0.6 escalation handoff semantic validation.

This module validates escalation_handoff_bundle semantics after JSON Schema
validation. Runtime-only assertions remain explicit synthetic fixture checks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import validate_legacy as legacy

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/tacp-v0.6.schema.json"

MANDATORY_PROHIBITIONS = {
    "restart_source_operation",
    "restart_remediation_operation",
    "create_remediation_of_remediation",
    "self_expand_authority",
    "self_accept_handoff",
    "assume_acceptance_from_delivery",
}

KNOWN_FAILURES_V06 = {
    "delivery-treated-as-acceptance.json": "delivery_as_acceptance",
    "missing-acceptance-receipt.json": "acceptance_receipt_missing",
    "acceptance-wrong-escalation-ref.json": "escalation_ref_mismatch",
    "acceptance-wrong-remediation-operation-id.json": "remediation_operation_id_mismatch",
    "accepted-scope-exceeds-request.json": "accepted_scope_exceeds_request",
    "self-issued-receiver-authority.json": "receiver_authority_self_issued",
    "executor-self-accepts-handoff.json": "executor_self_acceptance",
    "transferred-after-rejection.json": "transferred_after_rejection",
    "transferred-after-timeout.json": "transferred_after_timeout",
    "closure-before-disposition.json": "closure_before_disposition",
    "second-remediation-created-after-handoff.json": "second_remediation_created_after_handoff",
    "authority-expanded-during-handoff.json": "authority_expanded_during_handoff",
    "receiver-outside-declared-scope.json": "receiver_outside_declared_scope",
    "handoff-after-deadline-marked-accepted.json": "handoff_after_deadline_marked_accepted",
    "acceptance-evidence-stale.json": "acceptance_evidence_stale",
    "handoff-history-rewritten.json": "handoff_history_rewritten",
}

RUNTIME_FIXTURES_V06 = {
    "second-remediation-created-after-handoff.json",
    "authority-expanded-during-handoff.json",
    "handoff-history-rewritten.json",
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


def _unique_evidence_refs(records: list[Any]) -> set[str]:
    refs: set[str] = set()
    for row in records:
        if not isinstance(row, dict):
            continue
        for key in (
            "evidence_refs",
            "acceptance_evidence_refs",
            "disposition_evidence_refs",
        ):
            values = row.get(key)
            if isinstance(values, list):
                refs.update(ref for ref in values if isinstance(ref, str))
    return refs


def validate_semantics(bundle: dict[str, Any]) -> list[legacy.Diagnostic]:
    errors: list[legacy.Diagnostic] = []

    def add(code: str, path: str, message: str) -> None:
        item = diagnostic(code, path, message)
        if item not in errors:
            errors.append(item)

    if bundle.get("document_type") != "escalation_handoff_bundle":
        add(
            "unsupported_v06_document_type",
            "/document_type",
            "The v0.6 native validator accepts escalation_handoff_bundle only.",
        )
        return errors

    records = bundle.get("records")
    if not isinstance(records, list):
        add("records_missing", "/records", "An escalation handoff bundle requires records.")
        return errors

    requests = _typed_records(records, "handoff_request")
    deliveries = _typed_records(records, "handoff_delivery_observation")
    dispositions = _typed_records(records, "handoff_disposition")
    closures = _typed_records(records, "handoff_closure")

    if len(requests) != 1:
        add("request_cardinality_invalid", "/records", "Exactly one handoff_request is required.")
    if len(dispositions) != 1:
        add("disposition_cardinality_invalid", "/records", "Exactly one handoff_disposition is required.")
    if len(closures) != 1:
        add("closure_cardinality_invalid", "/records", "Exactly one handoff_closure is required.")

    record_ids = [
        row.get("record_id")
        for row in records
        if isinstance(row, dict) and isinstance(row.get("record_id"), str)
    ]
    if len(record_ids) != len(set(record_ids)):
        add("record_id_duplicate", "/records", "record_id values MUST be unique within the handoff bundle.")

    bundle_handoff = bundle.get("handoff_id")
    bundle_escalation = bundle.get("escalation_ref")
    bundle_remediation = bundle.get("remediation_ref")
    bundle_operation = bundle.get("remediation_operation_id")

    for i, row in enumerate(records):
        if not isinstance(row, dict):
            continue
        if row.get("handoff_id") != bundle_handoff:
            add("handoff_id_mismatch", f"/records/{i}/handoff_id", "Record handoff_id MUST match the bundle handoff_id.")
        if row.get("escalation_ref") != bundle_escalation:
            add("escalation_ref_mismatch", f"/records/{i}/escalation_ref", "Record escalation_ref MUST match the bundle escalation_ref.")
        if row.get("remediation_ref") != bundle_remediation:
            add("remediation_ref_mismatch", f"/records/{i}/remediation_ref", "Record remediation_ref MUST match the bundle remediation_ref.")
        if row.get("remediation_operation_id") != bundle_operation:
            add(
                "remediation_operation_id_mismatch",
                f"/records/{i}/remediation_operation_id",
                "Record remediation_operation_id MUST match the bundle remediation_operation_id.",
            )

    limits = bundle.get("handoff_limits") if isinstance(bundle.get("handoff_limits"), dict) else {}
    permitted_receivers = set(limits.get("permitted_receiver_refs") or [])
    max_deliveries = limits.get("max_delivery_observation_count")
    if isinstance(max_deliveries, int) and len(deliveries) > max_deliveries:
        add("delivery_observation_limit_exceeded", "/records", "Delivery observation count exceeds max_delivery_observation_count.")

    evidence_budget = limits.get("evidence_retrieval_budget")
    if isinstance(evidence_budget, int) and len(_unique_evidence_refs(records)) > evidence_budget:
        add(
            "evidence_budget_exceeded",
            "/handoff_limits/evidence_retrieval_budget",
            "Unique evidence references exceed the declared evidence_retrieval_budget.",
        )

    request_i = request = disposition_i = disposition = closure_i = closure = None
    if requests:
        request_i, request = requests[0]
        receiver_ref = request.get("receiver_ref")
        if permitted_receivers and receiver_ref not in permitted_receivers:
            add(
                "receiver_outside_declared_scope",
                f"/records/{request_i}/receiver_ref",
                "handoff_request.receiver_ref MUST be permitted by handoff_limits.permitted_receiver_refs.",
            )

        request_deadline = request.get("deadline")
        final_deadline = limits.get("final_handoff_deadline")
        if isinstance(request_deadline, str) and isinstance(final_deadline, str):
            try:
                if _instant(request_deadline) > _instant(final_deadline):
                    add(
                        "request_deadline_exceeds_final_deadline",
                        f"/records/{request_i}/deadline",
                        "handoff_request.deadline MUST NOT exceed final_handoff_deadline.",
                    )
            except ValueError:
                pass

    if dispositions:
        disposition_i, disposition = dispositions[0]
    if closures:
        closure_i, closure = closures[0]

    if request is not None and disposition is not None:
        if disposition.get("request_ref") != request.get("record_id"):
            add(
                "request_ref_mismatch",
                f"/records/{disposition_i}/request_ref",
                "handoff_disposition MUST reference the exact handoff_request record.",
            )

        request_receiver = request.get("receiver_ref")
        disposition_receiver = disposition.get("receiver_ref")
        if disposition_receiver != request_receiver:
            add(
                "receiver_ref_mismatch",
                f"/records/{disposition_i}/receiver_ref",
                "handoff_disposition.receiver_ref MUST match the requested receiver_ref.",
            )
        if permitted_receivers and disposition_receiver not in permitted_receivers:
            add(
                "receiver_outside_declared_scope",
                f"/records/{disposition_i}/receiver_ref",
                "handoff_disposition.receiver_ref MUST remain inside permitted_receiver_refs.",
            )

        requested_scope = request.get("requested_scope") if isinstance(request.get("requested_scope"), list) else []
        accepted_scope = disposition.get("accepted_scope") if isinstance(disposition.get("accepted_scope"), list) else []
        outside_scope = [item for item in accepted_scope if item not in requested_scope]
        if outside_scope:
            add(
                "accepted_scope_exceeds_request",
                f"/records/{disposition_i}/accepted_scope",
                "accepted_scope MUST be a subset of requested_scope.",
            )

        result = disposition.get("result")
        if result == "accepted":
            required_fields = (
                "receiver_id",
                "receiver_type",
                "receiver_authority_ref",
                "accepted_at",
            )
            for field in required_fields:
                if not disposition.get(field):
                    add(
                        "accepted_disposition_incomplete",
                        f"/records/{disposition_i}/{field}",
                        f"An accepted disposition requires {field}.",
                    )
            acceptance_refs = disposition.get("acceptance_evidence_refs")
            if not isinstance(acceptance_refs, list) or not acceptance_refs:
                add(
                    "acceptance_receipt_missing",
                    f"/records/{disposition_i}/acceptance_evidence_refs",
                    "An accepted disposition requires at least one explicit acceptance evidence reference.",
                )
            if not accepted_scope:
                add(
                    "accepted_scope_missing",
                    f"/records/{disposition_i}/accepted_scope",
                    "An accepted disposition requires nonempty accepted_scope.",
                )

            receiver_authority = str(disposition.get("receiver_authority_ref", "")).lower()
            if "self-issued" in receiver_authority or "self_issued" in receiver_authority:
                add(
                    "receiver_authority_self_issued",
                    f"/records/{disposition_i}/receiver_authority_ref",
                    "Receiver authority MUST be independently attributable and MUST NOT be self-issued by the originating TACP path.",
                )

            receiver_id = str(disposition.get("receiver_id", "")).lower()
            acceptance_refs_text = " ".join(str(ref).lower() for ref in (disposition.get("acceptance_evidence_refs") or []))
            reason_text = str(disposition.get("reason", "")).lower()
            if receiver_id.startswith("executor") or "original-executor" in receiver_id or "self-acceptance-by-original-executor" in acceptance_refs_text or "executor self-accept" in reason_text:
                add(
                    "executor_self_acceptance",
                    f"/records/{disposition_i}/receiver_id",
                    "The original TACP executor MUST NOT self-accept the handoff as the receiving responsibility domain.",
                )

            accepted_at = disposition.get("accepted_at")
            request_deadline = request.get("deadline")
            final_deadline = limits.get("final_handoff_deadline")
            disposition_created = disposition.get("created_at")
            max_age = limits.get("max_acceptance_age_seconds")
            if isinstance(accepted_at, str):
                try:
                    accepted = _instant(accepted_at)
                    if isinstance(request_deadline, str) and accepted > _instant(request_deadline):
                        add(
                            "handoff_after_deadline_marked_accepted",
                            f"/records/{disposition_i}/accepted_at",
                            "Acceptance MUST NOT occur after handoff_request.deadline.",
                        )
                    if isinstance(final_deadline, str) and accepted > _instant(final_deadline):
                        add(
                            "handoff_after_deadline_marked_accepted",
                            f"/records/{disposition_i}/accepted_at",
                            "Acceptance MUST NOT occur after final_handoff_deadline.",
                        )
                    if isinstance(disposition_created, str):
                        age = _instant(disposition_created) - accepted
                        if age < 0:
                            add(
                                "acceptance_time_after_disposition",
                                f"/records/{disposition_i}/accepted_at",
                                "accepted_at MUST NOT occur after disposition.created_at.",
                            )
                        elif isinstance(max_age, int) and age > max_age:
                            add(
                                "acceptance_evidence_stale",
                                f"/records/{disposition_i}/accepted_at",
                                "Acceptance evidence age exceeds max_acceptance_age_seconds.",
                            )
                except ValueError:
                    pass

        else:
            if accepted_scope:
                add(
                    "nonaccepted_scope_present",
                    f"/records/{disposition_i}/accepted_scope",
                    "rejected, unconfirmed, and timeout dispositions MUST NOT claim accepted_scope.",
                )
            acceptance_refs = disposition.get("acceptance_evidence_refs")
            if isinstance(acceptance_refs, list) and acceptance_refs:
                add(
                    "nonaccepted_acceptance_evidence_present",
                    f"/records/{disposition_i}/acceptance_evidence_refs",
                    "A non-accepted disposition MUST NOT carry acceptance evidence as proof of transfer.",
                )

    if request is not None and disposition is not None and closure is not None:
        if not (request_i < disposition_i < closure_i):
            if closure_i < disposition_i:
                add(
                    "closure_before_disposition",
                    f"/records/{closure_i}",
                    "handoff_closure MUST NOT precede handoff_disposition.",
                )
            else:
                add("record_order_violation", "/records", "Required order is request -> disposition -> closure.")

        for delivery_i, delivery in deliveries:
            if not (request_i < delivery_i < disposition_i):
                add(
                    "delivery_record_order_violation",
                    f"/records/{delivery_i}",
                    "Each handoff_delivery_observation MUST occur after request and before disposition.",
                )
            if delivery.get("receiver_ref") != request.get("receiver_ref"):
                add(
                    "receiver_ref_mismatch",
                    f"/records/{delivery_i}/receiver_ref",
                    "Delivery observation receiver_ref MUST match the requested receiver_ref.",
                )
            if permitted_receivers and delivery.get("receiver_ref") not in permitted_receivers:
                add(
                    "receiver_outside_declared_scope",
                    f"/records/{delivery_i}/receiver_ref",
                    "Delivery observation receiver_ref MUST remain inside permitted_receiver_refs.",
                )

        if closure_i != len(records) - 1:
            add("closure_not_final", f"/records/{closure_i}", "handoff_closure MUST be the final record.")

        if closure.get("disposition_ref") != disposition.get("record_id"):
            add(
                "disposition_ref_mismatch",
                f"/records/{closure_i}/disposition_ref",
                "handoff_closure MUST reference the exact handoff_disposition record.",
            )

        result = disposition.get("result")
        status = closure.get("status")
        transferred = closure.get("responsibility_transferred")

        if result == "accepted":
            if status != "transferred" or transferred is not True:
                add(
                    "accepted_not_transferred",
                    f"/records/{closure_i}/status",
                    "An accepted disposition MUST close as transferred with responsibility_transferred=true.",
                )
            if closure.get("receiver_ref") != disposition.get("receiver_ref"):
                add("receiver_ref_mismatch", f"/records/{closure_i}/receiver_ref", "Transferred closure receiver_ref MUST match disposition receiver_ref.")
            if closure.get("receiver_authority_ref") != disposition.get("receiver_authority_ref"):
                add(
                    "receiver_authority_ref_mismatch",
                    f"/records/{closure_i}/receiver_authority_ref",
                    "Transferred closure receiver_authority_ref MUST match disposition receiver_authority_ref.",
                )
            if closure.get("accepted_scope") != disposition.get("accepted_scope"):
                add(
                    "accepted_scope_mismatch",
                    f"/records/{closure_i}/accepted_scope",
                    "Transferred closure accepted_scope MUST match the accepted disposition scope.",
                )
        else:
            if status != "not_transferred" or transferred is not False:
                code = {
                    "rejected": "transferred_after_rejection",
                    "timeout": "transferred_after_timeout",
                    "unconfirmed": "delivery_as_acceptance",
                }.get(result, "invalid_nonaccepted_closure")
                add(
                    code,
                    f"/records/{closure_i}/status",
                    f"A {result} disposition MUST close as not_transferred with responsibility_transferred=false.",
                )
            remaining_state = closure.get("remaining_responsibility_state")
            if not isinstance(remaining_state, str) or not remaining_state:
                add(
                    "remaining_responsibility_state_missing",
                    f"/records/{closure_i}/remaining_responsibility_state",
                    "A not_transferred closure requires remaining_responsibility_state.",
                )

        prohibited = set(closure.get("prohibited_automatic_actions") or [])
        missing = MANDATORY_PROHIBITIONS - prohibited
        if missing:
            add(
                "mandatory_prohibition_missing",
                f"/records/{closure_i}/prohibited_automatic_actions",
                "handoff_closure MUST retain all mandatory automatic-action prohibitions.",
            )

        # A delivery observation can never be sufficient evidence for transfer.
        if result == "accepted":
            acceptance_refs = set(disposition.get("acceptance_evidence_refs") or [])
            delivery_refs = {
                ref
                for _, delivery in deliveries
                for ref in (delivery.get("evidence_refs") or [])
                if isinstance(ref, str)
            }
            if acceptance_refs and acceptance_refs.issubset(delivery_refs):
                add(
                    "delivery_as_acceptance",
                    f"/records/{disposition_i}/acceptance_evidence_refs",
                    "Transport or delivery evidence MUST NOT be reused as the sole acceptance receipt.",
                )

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
    extensions = bundle.get("extensions") if isinstance(bundle.get("extensions"), dict) else {}
    events = extensions.get("runtime_events") if isinstance(extensions.get("runtime_events"), list) else []

    if name == "second-remediation-created-after-handoff.json":
        match = next(
            (
                event
                for event in events
                if isinstance(event, dict)
                and event.get("event_type") == "remediation_operation_created"
                and event.get("parent_remediation_operation_id") == bundle.get("remediation_operation_id")
            ),
            None,
        )
        if match:
            return [diagnostic(
                "second_remediation_created_after_handoff",
                "/extensions/runtime_events",
                "A new remediation operation MUST NOT be autonomously created after v0.6 responsibility transfer.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/extensions/runtime_events", "Expected a post-handoff remediation creation event.", layer="harness")]

    if name == "authority-expanded-during-handoff.json":
        match = next(
            (
                event
                for event in events
                if isinstance(event, dict)
                and (
                    event.get("event_type") in {"authority_expanded", "authority_scope_expanded", "authority_change"}
                    or "authority" in str(event.get("event_type", "")).lower()
                )
                and (
                    event.get("added_scope")
                    or event.get("new_scope")
                    or event.get("scope_added")
                    or "expand" in str(event.get("reason", "")).lower()
                )
            ),
            None,
        )
        if match:
            return [diagnostic(
                "authority_expanded_during_handoff",
                "/extensions/runtime_events",
                "The originating TACP path MUST NOT expand its authority during handoff.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/extensions/runtime_events", "Expected authority expansion runtime evidence.", layer="harness")]

    if name == "handoff-history-rewritten.json":
        match = next(
            (
                event
                for event in events
                if isinstance(event, dict)
                and event.get("event_type") in {"record_rewrite_attempt", "handoff_history_rewrite", "history_rewrite_attempt"}
            ),
            None,
        )
        if match:
            return [diagnostic(
                "handoff_history_rewritten",
                "/extensions/runtime_events",
                "Committed handoff history MUST remain immutable after closure.",
                layer="runtime_fixture",
            )]
        return [diagnostic("runtime_fixture_invalid", "/extensions/runtime_events", "Expected a handoff history rewrite event.", layer="harness")]

    return []
