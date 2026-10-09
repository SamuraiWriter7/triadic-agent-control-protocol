# TACP Conformance Index

**Snapshot:** 2026-10-09

GitHub Actions run #179 completed successfully on Python 3.10 and 3.12 for the registered v0.1-v0.6 validation suites.

| Version | Primary scope | Registered validation status |
| --- | --- | --- |
| 0.1.0 | Mission structure, observation, challenge review, gate, execution, verification | PASS |
| 0.2.0 | Execution-time authorization and bounded held/expired/revoked/resource states | PASS |
| 0.3.0 | Recovery, successor handling, and synthetic external-state negatives | PASS |
| 0.4.0 | Human-reviewed remediation and compensation after confirmed effects | PASS |
| 0.5.0 | Independent post-remediation verification and terminal escalation | PASS |
| 0.6.0 | Explicit escalation handoff, receiver acceptance, responsibility transfer, and terminal non-transfer | PASS |

## v0.6 registered suite

The v0.6 suite currently contains:

- 5 positive examples,
- 16 negative examples,
- 3 registered synthetic runtime negatives,
- 21/21 matched expected outcomes in GitHub Actions run #179.

The registered negative cases cover:

- delivery incorrectly treated as acceptance,
- missing explicit acceptance receipt,
- escalation identity mismatch,
- remediation operation identity mismatch,
- accepted scope exceeding requested scope,
- receiver authority self-issued by the originating TACP path,
- original executor self-accepting the handoff,
- transfer incorrectly recorded after rejection,
- transfer incorrectly recorded after timeout,
- closure recorded before disposition,
- automatic second remediation created after handoff,
- self-expansion of authority during handoff,
- receiver outside the declared permitted set,
- acceptance after the handoff deadline,
- stale acceptance evidence,
- and handoff history rewritten after closure.

The registered synthetic runtime negatives are:

- `second-remediation-created-after-handoff.json`,
- `authority-expanded-during-handoff.json`,
- `handoff-history-rewritten.json`.

The v0.6 invariant is:

```text
escalation != handoff_completion
delivery != acceptance
acceptance != execution_authorization
accepted_scope <= requested_scope
handoff_timeout != implicit_acceptance
transferred requires explicit attributable acceptance
handoff MUST NOT restart autonomous remediation
source/remediation/v0.5 escalation history immutable
```

v0.6 is the **First Complete Cycle Boundary**. After this milestone, the protocol enters feature freeze and architecture review before any further capability expansion.

## v0.5 registered suite

The v0.5 suite currently contains:

- 5 positive examples,
- 18 negative examples,
- 4 registered synthetic runtime negatives,
- 23/23 matched expected outcomes in GitHub Actions run #147.

The registered negative cases cover:

- executor success without independent post-remediation observation,
- partial remediation incorrectly closed as completed,
- ineffective remediation incorrectly closed as completed,
- harmful remediation incorrectly closed as completed,
- unresolved remediation incorrectly closed as completed,
- stale post-remediation evidence,
- missing post-remediation observation,
- remediation operation identity mismatch,
- closure-to-verification reference mismatch,
- automatic second remediation creation,
- self-expansion of authority after remediation failure,
- verification after the final verification deadline,
- `not_dispatched` contradicted by execution evidence,
- newly observed adverse effects omitted from verification,
- missing terminal policy for clean non-dispatch closure,
- observation timestamps later than verification,
- observations outside declared target scope,
- unique evidence references exceeding the declared retrieval budget.

The registered synthetic runtime negatives are:

- `second-remediation-created.json`,
- `authority-expanded-after-failure.json`,
- `not-dispatched-with-execution-evidence.json`,
- `new-effect-silently-omitted.json`.

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
python -m py_compile scripts/validate.py scripts/validate_legacy.py scripts/validate_v05.py scripts/validate_v05_examples.py scripts/validate_v06.py scripts/validate_v06_examples.py
python scripts/validate.py --examples --json
python scripts/validate.py --examples --version 0.4.0 --json
python scripts/validate_v05_examples.py --json
python scripts/validate_v06_examples.py --json
```

## Interpretation of PASS

`PASS` means that the registered example suite produced the expected accept/reject outcomes under the repository's current schema, semantic validator, and synthetic runtime fixtures.

It does **not** establish production safety or complete protocol conformance. In particular, the current validation does not prove:

- authenticity of evidence,
- actual reviewer or receiver identity,
- truth of external effects,
- real-world receiver authority,
- legal responsibility transfer,
- distributed claim uniqueness,
- atomic cross-process enforcement,
- executor isolation,
- runtime privilege isolation after escalation or handoff,
- actual handoff delivery to an authorized human or external process,
- absence of hidden remediation outside the recorded trace,
- or deployment-specific policy correctness.

Those properties require separate implementation, runtime, and security verification.

## Fixture classes

Fixtures are classified explicitly as one of the following:

1. **Conformant safe denial** — the document is valid and correctly denies or holds an unsafe operation.
2. **Document nonconformance** — structure, references, chronology, or semantics contradict the protocol.
3. **Runtime-state nonconformance** — the document is internally valid, but external authoritative state makes the attempted action invalid.

A safe denial is not automatically a failing protocol document merely because the proposed operation was unsafe.
