# TACP Conformance Index

**Snapshot:** 2026-10-09

GitHub Actions run #106 completed successfully on Python 3.10 and 3.12 for the registered v0.1-v0.4 validation suites.

| Version | Primary scope | Registered validation status |
| --- | --- | --- |
| 0.1.0 | Mission structure, observation, challenge review, gate, execution, verification | PASS |
| 0.2.0 | Execution-time authorization and bounded held/expired/revoked/resource states | PASS |
| 0.3.0 | Recovery, successor handling, and synthetic external-state negatives | PASS |
| 0.4.0 | Human-reviewed remediation and compensation after confirmed effects | PASS |

## v0.4 registered suite

The v0.4 suite currently contains:

- 3 positive examples,
- 9 negative examples,
- 1 registered synthetic runtime negative: `duplicate-remediation.json`.

The registered negative cases cover:

- reused operation identity,
- missing causal link,
- unresolved impact followed by execution,
- missing human review,
- expired human approval,
- source authorization reuse,
- remediation without admission,
- duplicate remediation,
- remediation-of-remediation.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m py_compile scripts/validate.py scripts/validate_legacy.py
python scripts/validate.py --examples --json
python scripts/validate.py --examples --version 0.4.0 --json
```

## Interpretation of PASS

`PASS` means that the registered example suite produced the expected accept/reject outcomes under the repository's current schema, semantic validator, and synthetic runtime fixtures.

It does **not** establish production safety or complete protocol conformance. In particular, the current validation does not prove:

- authenticity of evidence,
- actual reviewer identity or authority,
- truth of external effects,
- distributed claim uniqueness,
- atomic cross-process enforcement,
- executor isolation,
- or deployment-specific policy correctness.

Those properties require separate implementation, runtime, and security verification.

## Fixture classes

Future fixtures should be classified explicitly as one of the following:

1. **Conformant safe denial** — the document is valid and correctly denies or holds an unsafe operation.
2. **Document nonconformance** — structure, references, chronology, or semantics contradict the protocol.
3. **Runtime-state nonconformance** — the document is internally valid, but external authoritative state makes the attempted action invalid.

A safe denial is not automatically a failing protocol document merely because the proposed operation was unsafe.
