# MiniAgent — Software Design Description (SDD)

**Status:** Living specification / alignment authority  
**Revision:** 1.0  
**Scope:** Existing product behavior, intended target, architecture, contracts, and verification of implementation/backlog.  
**Audience:** Claude Code, maintainers, reviewers.

## 1. Purpose and authority

This SDD is the specification used to determine whether MiniAgent's current implementation and future changes match the product vision. It is not a replacement for the backlog or per-task plans:

- **Product Vision & Backlog** defines the capabilities and work items.
- **Task Plans** define how an individual backlog task should be implemented.
- **Execution Plan** defines execution order and progress.
- **This SDD** defines system boundaries, behavior, architectural constraints, expected contracts, current-vs-target status, and how conformance must be verified.

When documents conflict, do not silently choose. Record the conflict, follow the hard safety constraints in this SDD, and reconcile the documents before implementing affected behavior. The SDD describes target requirements, not claims that those requirements already exist.

## 2. Product definition

MiniAgent is a local repository-analysis tool for inspecting software repositories and producing evidence-backed architecture, quality, defect-candidate, and security-analysis outputs. It must distinguish facts extracted from source from heuristic inference and LLM interpretation.

### Product goals
1. Inventory repository structure, languages, components, and selected relationships.
2. Analyze architecture and functional behavior from static evidence.
3. Detect quality/bug candidates and security weaknesses incrementally.
4. Correlate evidence and preserve file/line provenance.
5. Explain findings, confidence, limitations, and remediation.
6. Produce navigable HTML/Markdown and structured machine-readable outputs.
7. Support analysis of multiple repositories where applicable.
8. Operate safely on untrusted repositories.

### Non-goals / prohibited behavior
- Do not execute code, scripts, build steps, tests, package lifecycle hooks, or binaries from an analyzed repository.
- Do not modify analyzed repositories or automatically remediate their source.
- Static evidence does not prove runtime exploitability, business intent, or correctness.
- LLM interpretation is not ground truth; it must be labeled as inference and validated against repository evidence where possible.
- No external upload of source code unless a user explicitly enables a documented LLM/external integration; the default local/static path must remain clear about data handling.

## 3. Current system (observed from repository structure and code)

This section records a code-inspection baseline. It is not a complete behavioral audit; assertions are limited to inspected modules and their documented roles.

### 3.1 Current workflow

The repository currently has a group-analysis workflow orchestrated by app/analysis_orchestrator.py and app/supervisor.py. The orchestrator prepares repositories/workspaces and delegates analysis to a supervisor. The agent adapters use a shared AnalysisContext and publish agent results through the communication store/contracts.

Observed high-level flow:
1. Repository/group input and workspace preparation.
2. Repository inventory/static analysis.
3. Deep structural analysis.
4. Functional behavior inference.
5. Java repository analysis.
6. Quality and bug-pattern analysis, dependent on prior results.
7. Integration/group analysis and activity analysis where configured.
8. Optional LLM interpretation/review/explanation/correlation agents.
9. Deterministic cross-validation and group cross-validation.
10. Individual and group report generation.

Actual agent selection, dependencies, skip/error handling, and output paths are controlled by the current supervisor/orchestrator; task implementers must inspect those implementations before changing them.

### 3.2 Existing modules and responsibilities (observed)

| Module | Current role (observed) | Notes / verification boundary |
|---|---|---|
| app/analysis_orchestrator.py | Prepares group-analysis execution and delegates to supervisor | Verify clone/cache/workspace behavior before changing |
| app/supervisor.py | Agent ordering, requirements/dependencies, status handling | Current runtime graph; not the future security detector registry |
| app/agents/context.py | Shared AnalysisContext and agent base abstractions | Inspect contract before adding state |
| app/agents/inventory.py | Adapter to repository inventory engine | Inventory results are not a security finding model |
| app/engines.py | Repository engine and cloning/inventory utilities | Static-analysis boundary must remain enforced |
| app/deep_analysis.py | Deep repository structure/architecture analysis | Coverage is language/tool dependent |
| app/agents/deep.py | Adapter for deep-analysis engine | Consumes inventory context |
| app/functional_analysis.py | AST/heuristic functional behavior inference | Inferred business rules must not be treated as confirmed requirements |
| app/agents/functional.py | Adapter for functional analysis | |
| app/java_analysis.py | Java-specific repository analysis | Supported patterns must be documented and tested |
| app/agents/java.py | Java analysis adapter/evidence collection | |
| app/quality_analysis.py | Heuristic quality scoring and bug-pattern detection | Candidate findings; not runtime-confirmed bugs |
| app/agents/quality.py | Quality agent; depends on deep, functional, and Java results | Preserve dependency semantics |
| app/integration_analysis.py | Cross-repository/group correlation | Correlation is not proof of runtime dependency |
| app/agents/integration.py | Group-scoped integration adapter | |
| app/agents/llm_agents.py | Optional LLM interpretation, bug review, architecture explanation, evidence correlation | Output must remain marked as inferred and provider-dependent |
| app/agents/validation.py | Deterministic cross-validation of agent outputs/evidence | Warnings/contradictions should be explainable |
| app/agents/reporting.py | Individual/group report orchestration | Report formats must preserve provenance/status |
| app/communication/contracts.py | JSON-serializable agent message, evidence, status/error/skip contracts | Current agent contract is not automatically the future SecurityFinding schema |
| app/communication/store.py | Shared communication/result store | Inspect concurrency/ownership before extending |
| app/agent_report.py, app/group_report.py, app/rich_report.py, app/bug_report.py, app/reports_index.py, app/report_details.py | Report content, HTML/Markdown, indexing and bug dossiers | Keep HTML escaping, stable links, and schema/output compatibility |
| app/security/owasp.py | Existing OWASP/CWE metadata for selected findings (including SQL injection) | Catalog is currently limited; not a full knowledge base |
| app/bug_hunter_api.py and related provisioning/exploration/intelligence modules | Separate Bug Hunter workflow/API for isolated repository clones and repository exploration | Do not conflate this feature with the static analyzer or violate analyzed-repo read-only rules |
| app/analysis_cache.py | Analysis caching | Verify invalidation and cache keys when analysis behavior changes |
| app/llm.py, app/codegen.py | LLM integration and related helpers/redaction | LLM paths require explicit configuration and safety review |
| app/local_analysis_cli.py, app/main.py | CLI/application entry points | Maintain invocation compatibility unless change is explicitly planned |
| tests/ | Existing test suite across agents, analysis, reports, CLI, SQL injection, LLM, safety | Add fixtures and regressions alongside affected behavior |

### 3.3 Current security-analysis baseline

Observed current code includes heuristic quality analysis, SQL-injection-related tests and OWASP metadata. The current system does not, based on inspected modules, yet constitute the target modular contextual security analyzer described in the backlog.

The following target capabilities must be treated as planned/not verified as implemented unless code and tests prove otherwise:
- Unified SecurityFinding model with stable schema.
- General Source/Sink catalog and reusable data-flow engine.
- Reliable intra-file and cross-function propagation, and multi-file flow.
- Contextual detectors for XSS, Command Injection, Path Traversal, SSRF.
- Evidence correlation/deduplication across detector families.
- Explainable confidence and contextual risk engine.
- Comprehensive/versioned OWASP/CWE/ASVS/API/WSTG knowledge base.
- Coverage accounting and benchmark-backed precision/recall.

The existing SQLi heuristic and current tests must be inspected before each SQLi backlog task. Do not imply that all SQLi patterns or languages are covered.

## 4. Target architecture

Target architecture is evolutionary: preserve and extend the existing repository analysis workflow instead of replacing it with an unrelated system.

    Input / Repository Selection
            |
    Safe Workspace & Repository Inventory
            |
    Repository Context / Language / Framework Profile
            |
    Adaptive Analysis Plan
            |
    +---------------------------+
    | Existing analysis agents |
    | inventory / deep /       |
    | functional / Java /      |
    | quality / activity       |
    +---------------------------+
            |                 |
       Quality Engine      Security Engine
                           Detector Registry
                           SQLi / XSS / CMD /
                           Path Traversal / SSRF
                                |
                       Source / Sink / Data Flow
                                |
                    Normalized Evidence & Finding
                                |
                   Correlation / Deduplication
                                |
                   Confidence & Contextual Risk
                                |
                   Reporting / JSON / HTML / MD
                                |
                   Coverage, errors, limitations,
                   provenance, benchmark validation

### Architectural rules
- Keep orchestration thin; domain analysis belongs in engines, detectors, or services.
- Use stable contracts between components and version externally consumed report structures.
- Detectors are modular, independently testable, capability-described, and failure-isolated.
- Security finding data is separate from agent execution status and from quality/bug candidate records; adapters may convert between them explicitly.
- Evidence must retain source repository, file, line/range when available, detector, evidence type, and confidence/provenance.
- Severity, confidence, risk, exploitability, and analysis completeness are distinct fields/concepts.
- Unknown or incomplete analysis is represented explicitly; never silently treated as safe.
- Do not deduplicate in a way that discards evidence or detector provenance.
- Language/framework support is capability-based. Unsupported syntax/frameworks must be disclosed.
- Parallelism and caching must preserve deterministic correctness and safe resource boundaries.

## 5. Target domain contracts

These are required semantics; exact field names/types are finalized through CORE backlog tasks and contract tests.

### 5.1 Security finding
A security finding should carry: stable identifier; category/type; title; severity; confidence; review status; evidence; one or more locations; language; source/sink/data-flow context where available; CWE/OWASP mapping; risk score/band and rationale when computed; remediation; references; detector identity/version; schema metadata.

### 5.2 Evidence and provenance
Evidence must be independently traceable and machine-readable. It should distinguish:
- Direct source text or AST fact.
- Detector observation.
- Inferred propagation/path.
- LLM-derived hypothesis.
- Cross-validation result.

Evidence must never be upgraded from inferred to confirmed solely because an LLM agrees. Report generated evidence with file/line references when obtainable; record missing location/path context explicitly.

### 5.3 Agent and detector lifecycle
Agent messages currently communicate execution status, dependencies, payload, evidence, errors, and timing. Future detector lifecycle should not be forced into agent messages without a clear adapter. A detector should define identity/version, supported languages/frameworks/patterns, configuration, inputs, output contract, limits, and failure behavior.

### 5.4 Source/Sink and flow
Flow engine records source/sink types and locations, intermediate operations, sanitization/validation evidence, path completeness, and unresolved edges. Only supported syntactic relationships are claimed. A flow can be partial; partial traces must be visibly partial.

### 5.5 Confidence, severity, and risk
- **Severity:** potential impact/category magnitude independent of certainty.
- **Confidence:** how strongly evidence supports the candidate.
- **Risk:** prioritization derived from available context and documented factors.
- **Exploitability:** not asserted unless static evidence supports the claim; runtime conditions remain unknown.
- Explain the calculation/decision factors and missing data; avoid double counting correlated findings.

## 6. Functional requirements (target)

| ID | Requirement | Verification |
|---|---|---|
| SDD-FR-01 | Analyze repositories statically and read-only | Safety tests, code review, no target execution/writes |
| SDD-FR-02 | Inventory repository and supported files/languages | Fixture tests + coverage report |
| SDD-FR-03 | Produce architecture/functional inference with provenance and caveats | Tests and report inspection |
| SDD-FR-04 | Produce quality/bug candidates with locations and explanations | Positive/negative fixtures |
| SDD-FR-05 | Run optional LLM agents without elevating their claims to facts | LLM/validation tests |
| SDD-FR-06 | Support agent dependency, skip, error, and partial-analysis states | Supervisor tests |
| SDD-FR-07 | Contextual SQLi detection incrementally | Vulnerable/safe corpus |
| SDD-FR-08 | Normalize security findings to a stable contract | Contract/schema tests |
| SDD-FR-09 | Build supported Source/Sink/data-flow traces with explicit partial coverage | Flow fixtures |
| SDD-FR-10 | Correlate evidence and deduplicate without loss | Correlation tests/provenance assertions |
| SDD-FR-11 | Keep severity, confidence, risk, and status distinct and explainable | Schema and scoring tests |
| SDD-FR-12 | Generate report formats with evidence, mapping, remediation, coverage, errors, and limitations | Snapshot/schema/end-to-end tests |
| SDD-FR-13 | Add XSS, CMD, PATH, SSRF detector families through modular contracts | Detector fixtures and contract tests |
| SDD-FR-14 | Track language/framework capabilities and unsupported areas | Capability tests/report checks |
| SDD-FR-15 | Benchmark detector quality using labeled safe/vulnerable fixtures | Metrics and regression gate |
| SDD-FR-16 | Isolate failures, bound resource use, and safely handle untrusted repository content | Malicious fixtures and safety tests |
| SDD-FR-17 | Integrate optional external tools without losing provenance or making them mandatory | Adapter contract tests |
| SDD-FR-18 | Adaptive plan, observability, performance and UX improvements are measurable and explainable | Plan/metrics/performance/UI tests |

## 7. Non-functional requirements

- **Safety:** repository code is never executed; repositories are never modified by analysis.
- **Reliability:** one detector/agent failure does not unnecessarily abort independent work.
- **Traceability:** findings and report claims link to evidence and task/spec requirements.
- **Explainability:** detector rationale, confidence, limitations, and risk factors are inspectable.
- **Compatibility:** preserve current CLI/report consumers where practical; schema changes are versioned.
- **Performance:** resource limits are configurable; performance changes are benchmarked.
- **Maintainability:** avoid monolithic analyzers and duplicated detector logic.
- **Privacy:** secrets must be redacted from logs/reports and external prompts; data sharing must be explicit.
- **Testability:** fixtures must test vulnerable and safe patterns, edge cases, failure paths, and contracts.
- **Portability:** installation, CLI, and local analysis paths remain documented and tested for supported environments.

## 8. Alignment and conformance protocol (the core SDD gate)

Every backlog task and every implementation PR/commit must be checked against this SDD. Claude Code must perform a before-and-after conformance review, not a superficial checklist.

### Before implementation
1. Identify the exact backlog task ID and its plan.
2. Map it to SDD requirement IDs, architectural components, and contracts.
3. Inspect actual current code and tests. Record current behavior with file/symbol references; do not trust documentation alone.
4. Decide whether the task closes a real gap, improves an existing behavior, or is already satisfied.
5. If already satisfied, prove it with code/tests and mark the task as verified-existing rather than reimplementing.
6. If the backlog/plan/SDD disagree, record the discrepancy and resolve the documentation first (or continue only with unaffected scope).
7. Define the expected delta: current → intended behavior, touched components, test cases, and acceptance evidence.

### After implementation
1. Verify the changed code satisfies the task plan and mapped SDD requirements.
2. Run focused tests and relevant regression/full checks; record exact commands and outcomes.
3. Verify report/API/CLI compatibility and safety constraints.
4. Check that tests prove both intended detections/behavior and non-detections/negative cases.
5. Update task status only with evidence; no completion by assumption.
6. Update SDD status/traceability if the implementation changes current behavior or architecture.
7. Review the diff for unrelated changes and unsupported claims.

### Required traceability record per task
In the execution log, record:
- Backlog task ID and title.
- Priority and dependencies.
- SDD requirement(s)/section(s) impacted.
- Current state (implemented / partial / missing / not applicable), with code and test references.
- Intended change and decision rationale.
- Files/symbols affected.
- Test plan and commands.
- Actual validation results.
- Remaining limitations and follow-up links.

## 9. Requirement status vocabulary
Use only these statuses in SDD traceability:
- **IMPLEMENTED-VERIFIED:** behavior exists and tests/evidence verify it.
- **IMPLEMENTED-PARTIAL:** behavior exists only for a limited subset; coverage is documented.
- **PLANNED:** not implemented or not verified.
- **GAP:** required capability is absent or materially below target.
- **BLOCKED:** cannot validate/implement due to an explicit blocker.
- **N/A:** requirement does not apply to this component/task.

Never label a requirement implemented based only on filenames, comments, README claims, or a test name. Inspect behavior and test assertion. If a test is not run, verification remains unconfirmed.

## 10. Initial current-vs-target gap assessment

This is an initial assessment based on repository structure and the modules inspected while drafting the SDD. It must be refined through tests and deeper code inspection.

| Capability | Current evidence | Target | Initial status |
|---|---|---|---|
| Multi-agent orchestration | orchestrator, supervisor, shared context/store/contracts | reliable dependency/status/error handling | IMPLEMENTED-PARTIAL; needs validation |
| Repository inventory | inventory adapter + engines | robust language/file coverage and exclusions | IMPLEMENTED-PARTIAL |
| Deep architecture analysis | deep-analysis module/agent | traceable architecture/context | IMPLEMENTED-PARTIAL |
| Functional inference | AST/heuristic functional analysis | evidence-backed inference and caveats | IMPLEMENTED-PARTIAL |
| Java analysis | Java module/agent | capability matrix and validated coverage | IMPLEMENTED-PARTIAL |
| Quality/bug candidates | quality analysis + tests | explainable candidates, benchmark quality | IMPLEMENTED-PARTIAL |
| SQL injection | OWASP metadata + SQLi analysis/tests | contextual source-query-sink reasoning | IMPLEMENTED-PARTIAL; depth unverified |
| Unified SecurityFinding | existing agent/evidence contracts are not equivalent | stable security-specific schema | GAP |
| General Source/Sink catalog | no general reusable engine verified | catalog and contracts | GAP |
| Data-flow engine | no reusable flow engine verified | AST/graph propagation with partial paths | GAP |
| XSS/CMD/PATH/SSRF | no dedicated modular detectors verified | contextual detector families | GAP |
| Correlation/dedup | LLM evidence correlation and cross-validation exist; security evidence correlation not verified | deterministic normalized evidence correlation | IMPLEMENTED-PARTIAL / GAP |
| Confidence/risk | quality score and LLM review exist; unified confidence/risk model not verified | separate explainable confidence and risk | GAP |
| Knowledge base | selected OWASP SQLi metadata exists | versioned mappings/catalog | IMPLEMENTED-PARTIAL |
| Reporting | multiple HTML/Markdown/report/index modules and tests | versioned, complete, structured security reporting | IMPLEMENTED-PARTIAL |
| Benchmark | tests exist; labeled precision/recall corpus/gates not verified | benchmark with metrics and CI regression | GAP |
| Detector framework | agents/supervisor abstractions exist; detector registry not verified | modular detector registry/capabilities | GAP |
| Safety | read-only/static claims, safety tests, redaction helpers | robust adversarial repo handling and isolation | IMPLEMENTED-PARTIAL; audit required |
| Adaptive planning | supervisor dependency graph exists; detector capability planning not verified | repo-profile-based detector plan | GAP |
| Observability/performance | cache and agent timing contracts exist; comprehensive metrics not verified | coverage, resource metrics, actionable diagnostics | IMPLEMENTED-PARTIAL |
| CI gates | tests/config present; gates and benchmark quality not verified | reliable CI quality/security gates | PLANNED/GAP |
| UX | report/index pages exist | interactive filtering, comparison, risk trends | IMPLEMENTED-PARTIAL / PLANNED |

## 11. SDD-to-backlog mapping

The backlog epics map to requirements as follows (task-level mapping must be added in task plans/logs):

| Backlog epic | SDD sections / FR |
|---|---|
| STAB | 3, 7, 8; FR-01, FR-06, FR-16 |
| CORE | 5.1, 5.2, 5.3; FR-08, FR-10, FR-11 |
| FLOW | 5.4; FR-09 |
| SQLI | 5.4, 6; FR-07, FR-09, FR-15 |
| OWASP | 5.1, 6; FR-07, FR-12 |
| XSS / CMD / PATH / SSRF | 4, 5.4, 6; FR-13, FR-14, FR-15 |
| COR / CONF / RISK | 5.2, 5.5; FR-10, FR-11 |
| REP | 5, 6; FR-12 |
| DET | 4, 5.3; FR-13 |
| LANG | 4, 6; FR-14 |
| TESTSEC | 7, 8; FR-15, FR-16 |
| EXT | 4, 7; FR-17 |
| AGSEC | 2, 7; FR-01, FR-16 |
| PLAN | 4, 6; FR-18 |
| OBS | 7; FR-18 |
| CI | 7, 8; FR-15, FR-16 |
| PERF | 7; FR-18 |
| UX | 6, 7; FR-12, FR-18 |

## 12. Change control for the SDD
- A task may change architecture or requirements only when that change is justified and recorded.
- If implementation discovers the target is infeasible or incorrect, Claude should propose the smallest evidence-backed SDD/backlog update, apply documentation updates when the change is clearly within scope, and continue unaffected work. Do not silently weaken requirements to make tests pass.
- Keep the current-state section updated as verified behavior changes; target requirements should not be rewritten to describe accidental implementation.
- Use requirement IDs in task plans, tests (where practical), execution notes, and reviews.
- The SDD is a living document; every completed task must improve alignment or record why no SDD change was needed.

## 13. Definition of done for a backlog task

A task is complete only when:
- The backlog item and task plan are satisfied.
- SDD requirements are mapped and conformance checked.
- Implementation is reviewed and scoped.
- Tests pass (or any unavailable validation is explicitly recorded and task remains unverified).
- Evidence/provenance and limitations are preserved.
- Safety, compatibility, and false-positive boundaries are checked.
- Execution tracker includes status, commands, outcomes, and relevant code/test references.
- SDD traceability is updated when current behavior, coverage, or architecture changed.

## 14. Known uncertainties requiring future verification

This SDD intentionally does not overstate code inspection. During stabilization, Claude must verify:
- Exact CLI and API behavior, input validation, and report contracts.
- Current SQLi detector pattern coverage, safe-query handling, and evidence quality.
- Supported language/framework matrix and actual file coverage.
- Repository clone/workspace/cache semantics and safety limits.
- Agent dependency, partial-failure, timeout, and resource-limit behavior.
- Whether cross-validation/correlation is deterministic, evidence-backed, and lossless.
- Report schemas, compatibility consumers, and secret-redaction guarantees.
- CI workflow/gates and performance baselines.

The first stabilization tasks should turn these uncertainties into verified facts and update this SDD with concrete code references and evidence.
