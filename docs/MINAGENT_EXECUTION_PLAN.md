# MiniAgent — Execution Plan and Progress Tracker


**SDD conformance authority:** `docs/MINAGENT_SDD.md`. Before and after each task, validate current code and intended behavior against its requirements. A task is not done just because its local acceptance criteria pass; it must also be aligned with the SDD, or the discrepancy must be explicitly resolved.

**Per-task implementation plans:** `docs/MINAGENT_BACKLOG_TASK_PLANS.md` contains a plan section for every product backlog item. Claude must read and follow the matching plan before implementing a task.

This file turns the product backlog into an ordered implementation plan for Claude Code. Update statuses and validation evidence as work is completed.

**Status legend:** TODO · IN_PROGRESS · BLOCKED · DONE · DEFERRED  
**Current baseline:** roadmap items are not presumed implemented; inspect repository and verify each item.

## Execution rules
- Follow `CLAUDE.md`.
- Resolve dependencies before downstream tasks.
- Keep tasks small enough to test and review.
- Record validation commands/results for DONE items.
- Do not mark a task DONE merely because code was written.
- Do not execute or modify analyzed repositories.

## Milestones

### M0 — Stabilization and contracts (P0)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M0-01 | Inspect repository structure, working tree, architecture, and test baseline | — | TODO | |
| M0-02 | Run current tests and record baseline failures | M0-01 | TODO | |
| M0-03 | Validate package/import/dependency setup and CLI entry points | M0-01 | TODO | |
| M0-04 | Verify end-to-end analysis and report paths on safe fixtures | M0-01 | TODO | |
| M0-05 | Review existing SQLi detector and OWASP metadata; identify gaps | M0-01 | TODO | |
| M0-06 | Define/validate shared SecurityFinding and Evidence contracts | M0-02, M0-05 | TODO | |
| M0-07 | Add contract and serialization tests; preserve compatibility | M0-06 | TODO | |

### M1 — SQL Injection foundation (P0)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M1-01 | Define SQL source/sink catalog for supported Python patterns | M0-06 | TODO | |
| M1-02 | Detect dynamic SQL construction patterns (concat/interpolation/formatting) | M1-01 | TODO | |
| M1-03 | Recognize supported parameterized query patterns | M1-01 | TODO | |
| M1-04 | Add simple assignment/variable propagation needed by SQLi | M0-06 | TODO | |
| M1-05 | Connect source → query construction → execution sink evidence | M1-01–04 | TODO | |
| M1-06 | Add vulnerable and safe SQLi test corpus | M1-02–05 | TODO | |
| M1-07 | Integrate contextual SQLi findings into report/JSON | M0-07, M1-05 | TODO | |

### M2 — Basic data-flow engine (P0)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M2-01 | Define data-flow node/edge/path representation | M0-06 | TODO | |
| M2-02 | Track assignment, concatenation, and interpolation | M2-01 | TODO | |
| M2-03 | Track supported function arguments and returns | M2-02 | TODO | |
| M2-04 | Represent transforms, validation, and sanitization conservatively | M2-01–03 | TODO | |
| M2-05 | Produce explainable traces and partial-flow indicators | M2-01–04 | TODO | |
| M2-06 | Add positive/negative propagation tests and fixtures | M2-01–05 | TODO | |

### M3 — Evidence, confidence, correlation, and risk (P1)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M3-01 | Normalize evidence/location records | M0-06 | TODO | |
| M3-02 | Deduplicate findings without losing original detector provenance | M3-01 | TODO | |
| M3-03 | Correlate source, flow, and sink evidence into contextual findings | M1-05, M2-05, M3-01 | TODO | |
| M3-04 | Define explainable confidence levels and factors | M3-03 | TODO | |
| M3-05 | Keep severity, confidence, risk, and exploitability separate | M0-06, M3-04 | TODO | |
| M3-06 | Implement explainable risk ranking and rationale | M3-05 | TODO | |
| M3-07 | Add correlation/confidence/risk tests and fixtures | M3-01–06 | TODO | |

### M4 — Reports and benchmark gates (P1)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M4-01 | Define versioned report schema and compatibility policy | M0-06 | TODO | |
| M4-02 | Add executive summary and ranked findings | M3-06 | TODO | |
| M4-03 | Include traces, evidence, mappings, remediation, and limitations | M3-03, M4-01 | TODO | |
| M4-04 | Report coverage, exclusions, unsupported cases, and errors | M0-04 | TODO | |
| M4-05 | Build safe/vulnerable benchmark corpus and baseline metrics | M1-06 | TODO | |
| M4-06 | Establish detector regression checks in CI | M4-01, M4-05 | TODO | |
| M4-07 | Validate end-to-end JSON/report fixtures | M4-01–06 | TODO | |

### M5 — Detector expansion (P2)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M5-01 | XSS detector for supported contexts and APIs | M2, M3, M4 | TODO | |
| M5-02 | Command Injection detector | M2, M3, M4 | TODO | |
| M5-03 | Path Traversal detector | M2, M3, M4 | TODO | |
| M5-04 | SSRF detector | M2, M3, M4 | TODO | |
| M5-05 | Insecure deserialization candidate detection | Detector framework/contracts | TODO | |
| M5-06 | Secret exposure detector and safe reporting | Detector framework/contracts | TODO | |
| M5-07 | Security misconfiguration checks | Detector framework/contracts | TODO | |

### M6 — Extensibility, language profiles, and integrations (P2)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M6-01 | Detector registry, configuration, lifecycle, and contracts | M0, M4 | TODO | |
| M6-02 | Language capability matrix and Python profile maturity | M6-01 | TODO | |
| M6-03 | Add Java profile incrementally | M6-02 | TODO | |
| M6-04 | Add JavaScript/TypeScript profile incrementally | M6-02 | TODO | |
| M6-05 | Evaluate and add optional external-tool adapters | M6-01 | TODO | |
| M6-06 | Adaptive analysis planning and skipped-check rationale | M6-01, repository context | TODO | |
| M6-07 | Observability: timings, errors, coverage, partial-analysis state | M6-01 | TODO | |

### M7 — MiniAgent self-security and scale (P1/P2)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M7-01 | Threat model for analyzing untrusted repositories | M0-01 | TODO | |
| M7-02 | Enforce no-execution/read-only contract in architecture and tests | M7-01 | TODO | |
| M7-03 | Safe file traversal, symlink handling, and archive safeguards if relevant | M7-01 | TODO | |
| M7-04 | Resource/time limits and failure containment | M7-01 | TODO | |
| M7-05 | Secret-safe logs and report output | M7-01 | TODO | |
| M7-06 | Malicious repository and resource exhaustion fixtures | M7-02–05 | TODO | |
| M7-07 | Profile performance and optimize large repositories | M0 baseline, M6 metrics | TODO | |

### M8 — UX and analysis comparison (P3)
| Task | Description | Dependencies | Status | Validation/evidence |
|---|---|---|---|---|
| M8-01 | Improve finding navigation and filtering | M4 reports | TODO | |
| M8-02 | Compare analysis runs and identify new/resolved findings | Stable IDs/schema | TODO | |
| M8-03 | Export filtered findings and risk trends | M8-01, M8-02 | TODO | |

## First task Claude should execute
**M0-01 — Repository reconnaissance.** Inspect working tree, file structure, architecture, tests, CLI, current detector/report contracts, and existing documentation. Produce a concise findings note and identify the next concrete implementation task. Do not modify code during reconnaissance unless a documentation-only correction is explicitly required. Do not mark later tasks complete based on assumptions.

## Autonomous checkpoint policy
Checkpoints are **not stopping points** and never require user confirmation:
1. Review the diff.
2. Run relevant validation and record exact outcomes.
3. Update statuses and evidence.
4. Append a concise progress note and next task to the running log.
5. Immediately continue with the next highest-priority eligible task.
Pause only for genuine human-required blockers, safety/permission issues, irreversible actions, or session/runtime limits. If interrupted, leave a precise resume point.

## Autonomous prioritization policy

Claude Code should use the task-level priority and prerequisite annotations in `MINAGENT_BACKLOG_TASK_PLANS.md` and this dependency-aware order as the default execution sequence. This is a default, not a rigid serial queue: independent ready tasks can be grouped or parallelized, and blocked tasks must not stop unrelated work.

1. **P0 stabilization and safety:** STAB-01..10; address actual baseline blockers before feature work.
2. **P0 shared contracts:** CORE-01..14, preserving compatibility and migrating incrementally.
3. **P0 data-flow primitives:** FLOW-01..17, with tested, explicit partial coverage.
4. **P0 SQLi MVP:** SQLI-01..27, using the contracts and flow primitives; bounded detection may proceed where a flow prerequisite is not yet available.
5. **P0 benchmark and safety gates:** TESTSEC and AGSEC tasks that enable safe regression measurement must be brought forward when their prerequisites are ready; safety rules apply from the beginning.
6. **P1 correlation, confidence, risk, detector framework, knowledge base, and report contracts:** COR, CONF, RISK, DET, OWASP, REP. Resolve contract dependencies before consumers; avoid broad rewrites.
7. **P1 CI gates:** CI tasks that validate stable tests, contracts, and benchmark behavior should be enabled as soon as checks are reliable; don't add flaky gates.
8. **P2 detector expansion:** XSS, CMD, PATH, SSRF; reuse shared Source/Sink, evidence, flow, detector, and report abstractions. Prioritize each detector's prerequisite-supported slice.
9. **P2 breadth and scale:** LANG, EXT, PLAN, OBS, PERF in dependency order; do not optimize without profiling evidence or claim unsupported language coverage.
10. **P3 UX:** UX tasks after stable finding/report data and basic usability needs are met.

For each task, Claude must refine the epic-level prerequisites into exact code-level dependencies after inspecting the current repository. The task plan must record the affected modules and symbols, implementation choices, edge cases, tests, validation commands/results, and any unresolved limitations. Routine choices are not user checkpoints.

## Token/context optimization policy
Read `docs/MINAGENT_TOKEN_EFFICIENCY.md`. Work task-first and inspect only relevant code/tests/docs; avoid repeated repository-wide exploration and verbose tool output. Make small cohesive diffs, run focused tests then expand based on risk, and keep durable checkpoints concise. Use lower-cost model/effort for routine work and escalate for complex security/architecture reasoning. Token savings must never skip acceptance criteria, tests, SDD conformance, safety, or evidence. Reset context between unrelated tasks; compact only when continuing the same task.
