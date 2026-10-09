# Triadic Agent Control Protocol (TACP)

A protocol for coordinating scout, analyst, and executor roles under independently enforced authorization, bounded review, traceability, recovery, remediation, and post-remediation verification controls.

**Status:** evolving specification. v0.1.0-v0.5.0 registered example suites passed GitHub Actions run #147 on Python 3.10 and 3.12 on 2026-10-09. This is **not** a certification of runtime safety or deployment conformance.

## Version map

| Version | Focus |
| --- | --- |
| v0.1.0 | Mission planning, observation, challenge review, gated execution, and outcome verification |
| v0.2.0 | Execution-time authorization checks, held/expired/revoked states, deadlines, and resource limits |
| v0.3.0 | Recovery from non-dispatch, no-effect, uncertain outcomes, and bounded successor handling |
| v0.4.0 | Human-reviewed remediation after a confirmed external effect, with causal linkage and independent authorization |
| v0.5.0 | Independent post-remediation verification, outcome classification, bounded escalation, and prohibition of autonomous remediation chains |

See [v0.5 specification](specs/tacp-v0.5.md), [Conformance Index](CONFORMANCE_INDEX.md), and [Changelog](CHANGELOG.md).

## Roles and authority

- **Scout** — performs bounded observation and records evidence, state, freshness, and uncertainty.
- **Analyst** — evaluates evidence, challenges assumptions, and proposes actions; cannot authorize execution.
- **Executor** — performs only externally admitted operations within the approved target and scope.
- **Execution gate** — independently checks authorization and execution conditions. It is an enforcement component, not a deliberating agent.

An AI-generated recommendation is not permission. Deployments must enforce authority boundaries outside prompts.

## Core design principles

1. **Traceable basis** — decisions and actions must resolve to explicit records and references.
2. **Separated authority** — assessment, authorization, and execution are distinct responsibilities.
3. **Bounded review** — review rounds, deadlines, freshness, and resources are finite.
4. **Fresh conditions** — execution-time and post-remediation state must still be established by bounded fresh evidence.
5. **No evidence inflation** — reused evidence is not counted as independent evidence.
6. **Explicit uncertainty** — unknowns must not be silently converted into approval or success.
7. **Duplicate prevention** — uncertain or previously attempted operations must not be repeated without reconciliation.
8. **Outcome verification** — a tool or executor success response alone does not establish mission or remediation completion.
9. **Recovery is not retry** — v0.3 recovery requires fresh checks and a bounded successor path.
10. **Remediation is a new operation** — v0.4 remediation cannot erase the original effect or reuse its operation identity or authorization.
11. **Remediation must be verified** — v0.5 requires independent post-remediation observation before a remediation can be closed as effective.
12. **Escalation terminates autonomous remediation** — partial, ineffective, harmful, or unresolved remediation outcomes must not trigger an automatic remediation-of-remediation chain.

## v0.4 core invariant

Once an external effect has occurred, the trace of that effect remains part of the source history. A remediation action is not a rollback fiction and not permission to repeat the source operation.

A v0.4 remediation must therefore be treated as a separately bounded operation with:

- explicit impact assessment,
- an explicit causal link to the source operation,
- a new operation identity,
- independent authorization,
- human review,
- remediation admission,
- bounded resource and timing limits,
- duplicate-remediation protection,
- and no remediation-of-remediation chain.

## v0.5 core invariant

A remediation attempt is **not successful merely because it was admitted, dispatched, executed, or reported as successful by the executor**.

Before a remediation path can close as completed, v0.5 requires independent post-remediation observation and analyst verification of the resulting external state.

The verification result is classified as one of:

- `confirmed_effective`,
- `confirmed_partially_effective`,
- `confirmed_ineffective`,
- `confirmed_harmful`,
- `unresolved`,
- `not_dispatched`.

`confirmed_partially_effective`, `confirmed_ineffective`, `confirmed_harmful`, and `unresolved` must terminate as `escalated`. Escalation does not grant new authority. It explicitly prohibits automatic source repetition, remediation repetition, remediation-of-remediation, and self-expansion of authority.

## Validation

Install dependencies from `requirements.txt`, then run:

```bash
python -m py_compile scripts/validate.py scripts/validate_legacy.py scripts/validate_v05.py scripts/validate_v05_examples.py
python scripts/validate.py --examples --json
python scripts/validate.py --examples --version 0.4.0 --json
python scripts/validate_v05_examples.py --json
```

GitHub Actions validates v0.1-v0.5 on Python 3.10 and 3.12.

The v0.5 registered suite contains:

- 5 positive examples,
- 18 negative examples,
- 4 registered synthetic runtime negatives,
- 23/23 expected outcomes matched in GitHub Actions run #147.

The final consistency patch also registers negative cases for missing non-dispatch terminal policy, future-dated observation, out-of-scope observation, and evidence-budget overflow. `not_dispatched` clean completion requires an explicit terminal policy; extra strict escalation prohibitions are permitted.

The synthetic runtime negatives are:

- `second-remediation-created.json`,
- `authority-expanded-after-failure.json`,
- `not-dispatched-with-execution-evidence.json`,
- `new-effect-silently-omitted.json`.

These cases remain document-valid until the registered synthetic runtime context is applied.

## Validation boundary

A passing schema, semantic validator, or CI suite establishes only the checks actually encoded by those validators and fixtures. It does not prove:

- evidence authenticity,
- human reviewer identity or authority,
- actual external effects,
- race-free distributed uniqueness,
- atomic cross-process claim consumption,
- real enforcement of executor permissions,
- real privilege isolation after escalation,
- actual delivery of escalation to an authorized human process,
- or production deployment safety.

Those properties require separate runtime, security, and integration testing.

## Design principle

**Unify purpose and traceability. Separate authority and execution. Preserve uncertainty and externally observed effects. Verify remediation independently, and stop autonomous chains when verification fails.**
