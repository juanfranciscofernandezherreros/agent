# MiniAgent — Product Vision, Target Architecture & Expanded Backlog

> **Status:** Product vision and planning baseline  
> **Scope:** Static repository analysis only. MiniAgent must not execute or modify analyzed source code.  
> **Planning note:** The backlog is a roadmap, not a claim that the listed capabilities already exist. Detection coverage and confidence must be validated incrementally.

## 1. Product vision

MiniAgent will evolve from a static code analyzer using heuristics into an extensible platform for code quality and contextual security analysis.

It will inspect repositories without executing or changing their code, understand repository structure and selected code relationships, identify potential quality and security issues, correlate evidence, estimate confidence and contextual risk, prioritize findings, and produce actionable explanations and reports.

### Product promise

> Analyze a software repository, identify potential quality and security risks, explain the evidence and code context behind each finding, and help developers decide what to investigate first.

MiniAgent is an aid to investigation—not a guarantee that a repository is secure, nor a replacement for a full security audit or runtime testing.

## 2. Target outcomes

- Repository and architecture inventory.
- Quality analysis and maintainability signals.
- Modular security detectors.
- Basic Source-to-Sink tracking and data-flow evidence.
- Context-aware findings with severity, confidence, and risk kept distinct.
- Correlation and deduplication of related evidence.
- Explainable remediation recommendations.
- Structured, versioned reports.
- Repeatable tests and security benchmarks.
- Extensible language, framework, and tool support.
- Safe operation when analyzing untrusted repositories.

## 3. Target user workflow

1. Select or provide a repository.
2. MiniAgent inventories the repository and identifies languages, frameworks, structure, and relevant components.
3. An analysis plan selects applicable quality and security checks.
4. Static analyzers and detectors inspect the repository.
5. Source/Sink and data-flow analysis add context where supported.
6. Evidence is normalized, correlated, and deduplicated.
7. Confidence and contextual risk are evaluated with explainable criteria.
8. Findings are prioritized.
9. MiniAgent generates a report and machine-readable output.
10. Developers inspect findings and decide on remediation; MiniAgent does not automatically alter analyzed code.

## 4. Target architecture

Repository Orchestrator  
→ Repository Inventory & Context  
→ Analysis Planning  
→ Quality Engine / Security Engine / Data-Flow Engine  
→ Detector Registry & Language Profiles  
→ Evidence Normalization and Correlation  
→ Confidence Evaluation  
→ Risk Engine  
→ Reporting and Export

### Architectural principles

- Keep the orchestrator thin; detector logic must be modular.
- Use a shared finding and evidence contract.
- Treat repository content as untrusted data.
- Never execute analyzed code.
- Preserve traceability to files, lines, and evidence.
- Separate severity, confidence, risk, and exploitability.
- Make detector coverage and limitations explicit.
- Add capabilities behind tests and benchmarks.
- Prefer explainable heuristics and analysis over opaque scores.

## 5. Target capabilities

### 5.1 Repository understanding
- Identify languages, frameworks, dependencies, and project structure.
- Detect entry points, modules, APIs/endpoints, and sensitive components where feasible.
- Build a reusable repository context.
- Record files analyzed, excluded, unsupported, or failed and the reason.

### 5.2 Code quality
- Complexity and maintainability signals.
- Long functions and files.
- Duplication candidates.
- Structural issues and suspicious patterns.
- Quality findings with location, explanation, and recommendation.

### 5.3 Security analysis
Planned detector families, implemented incrementally:
- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal
- Server-Side Request Forgery (SSRF)
- Insecure Deserialization
- Secret exposure
- Security misconfiguration
- Authentication and authorization weaknesses, where static evidence permits

Detection must be described as candidate/potential unless sufficient evidence supports a stronger classification. Static analysis limitations must be visible.

### 5.4 Source → Sink and data-flow analysis
- Catalog sources, sinks, transformations, validation, and sanitization.
- Track assignments and basic propagation.
- Follow values through expressions, arguments, returns, and selected inter-file relationships as capabilities mature.
- Identify source-to-sink paths.
- Represent path evidence and missing/unknown links.
- Distinguish direct evidence from inferred propagation.
- Avoid claiming complete data-flow coverage when analysis is partial.

### 5.5 Evidence correlation
- Normalize evidence across detectors.
- Deduplicate repeated findings.
- Group evidence from a common flow or code path.
- Correlate source, transformation, and sink observations.
- Preserve original detector findings and locations.
- Explain why evidence was grouped.

### 5.6 Confidence and false-positive reduction
- Establish explainable confidence levels.
- Document factors that increase/decrease confidence.
- Account for source/sink certainty, path completeness, controls, and ambiguity.
- Keep confidence separate from severity and risk.
- Create vulnerable and safe examples.
- Measure precision and recall when a benchmark is available.

### 5.7 Risk evaluation
- Consider severity, confidence, exposure, reachability, sensitive context, impact, and controls when supported.
- Use explainable risk bands and prioritization.
- Avoid double-counting correlated findings.
- Explain risk rationale and unknowns.

### 5.8 Reporting
- Executive summary and priorities.
- Quality and security findings.
- Severity, confidence, risk, and evidence.
- Source-to-sink traces where available.
- File and line locations.
- CWE, OWASP, and references.
- Remediation guidance.
- Coverage, exclusions, unsupported areas, and errors.
- Versioned JSON schema and backward-compatibility policy.

## 6. Expanded backlog

Priority guide: **P0** foundational/blocking; **P1** high-value; **P2** planned capability; **P3** later optimization/UX. Estimates are intentionally not assigned until work is decomposed and validated.

### EPIC 0 — Stabilization and validation (P0)
- STAB-01: Establish baseline test suite and record current status.
- STAB-02: Reproduce and fix existing regressions.
- STAB-03: Validate imports, package structure, and dependency setup.
- STAB-04: Validate analysis end-to-end on representative repositories.
- STAB-05: Validate JSON output and error handling.
- STAB-06: Test single-repository and multi-repository paths.
- STAB-07: Validate security findings appear in reports.
- STAB-08: Test agent failures and partial-analysis behavior.
- STAB-09: Establish performance baseline.
- STAB-10: Document known limitations and baseline coverage.

### EPIC 1 — Unified SecurityFinding model (P0)
- CORE-01: Define stable finding identifier.
- CORE-02: Define finding type/category and title.
- CORE-03: Define severity.
- CORE-04: Define confidence.
- CORE-05: Define status/classification (candidate, confirmed by evidence, needs review, etc.).
- CORE-06: Define evidence model.
- CORE-07: Define one or multiple locations.
- CORE-08: Define source and sink fields.
- CORE-09: Define CWE and OWASP mappings.
- CORE-10: Define risk fields and rationale.
- CORE-11: Define remediation and references.
- CORE-12: Implement serialization.
- CORE-13: Integrate with analysis/reporting.
- CORE-14: Preserve compatibility with existing findings where practical.

Proposed fields: id, type, title, severity, confidence, status, evidence, language, locations, source, sink, data_flow, cwe, owasp, risk, remediation, references, detector, and schema/version metadata.

### EPIC 2 — Source/Sink and data-flow engine (P0)
- FLOW-01: Define Source catalog and contract.
- FLOW-02: Catalog HTTP parameters, query, headers, cookies, body, CLI, environment, files, and messaging inputs.
- FLOW-03: Define Sink catalog and contract.
- FLOW-04: Catalog SQL, command execution, HTML/JS, filesystem, HTTP, deserialization, dynamic code, and authorization sinks.
- FLOW-05: Track basic variables and assignments.
- FLOW-06: Track propagation through concatenation and interpolation.
- FLOW-07: Track function arguments and returns.
- FLOW-08: Track simple transformations.
- FLOW-09: Represent validation and sanitization.
- FLOW-10: Recognize selected safe/mitigating patterns.
- FLOW-11: Build intra-file flow graph.
- FLOW-12: Add selected cross-function propagation.
- FLOW-13: Expand to multi-file propagation incrementally.
- FLOW-14: Represent path reachability and partial paths.
- FLOW-15: Generate evidence traces and explanations.
- FLOW-16: Mark analysis completeness and unknown links.
- FLOW-17: Add unit and integration tests for propagation and controls.

### EPIC 3 — Contextual SQL Injection analysis (P0)
- SQLI-01: Review and validate current SQLi heuristic.
- SQLI-02: Cover string concatenation.
- SQLI-03: Cover f-strings/interpolation.
- SQLI-04: Cover format(), percent formatting, and template patterns.
- SQLI-05: Cover multiline/dynamic query construction.
- SQLI-06: Track query variables.
- SQLI-07: Identify external sources.
- SQLI-08: Identify SQL execution sinks.
- SQLI-09: Recognize common parameterized-query patterns.
- SQLI-10: Recognize positional and named parameters where supported.
- SQLI-11: Recognize selected ORM/query-builder patterns.
- SQLI-12: Identify dynamic SQL identifiers separately from values.
- SQLI-13: Recognize allowlist/control patterns conservatively.
- SQLI-14: Connect source, query construction, and sink.
- SQLI-15: Generate contextual evidence.
- SQLI-16: Evaluate confidence and severity separately.
- SQLI-17: Explain the potential issue.
- SQLI-18: Generate remediation guidance.
- SQLI-19: Add vulnerable positive tests.
- SQLI-20: Add safe negative tests.
- SQLI-21: Add multiline and variable propagation tests.
- SQLI-22: Validate against isolated training/lab examples.
- SQLI-23: Document limitations and supported patterns.
- SQLI-24: Measure false positives on safe corpus.
- SQLI-25: Integrate with unified SecurityFinding.
- SQLI-26: Integrate OWASP/CWE metadata.
- SQLI-27: Ensure reports preserve evidence and locations.

### EPIC 4 — Security knowledge base (P0/P1)
- OWASP-01: Centralize versioned OWASP Top 10 catalog.
- OWASP-02: Add CWE catalog/mappings.
- OWASP-03: Add ASVS references.
- OWASP-04: Add API Security Top 10 references.
- OWASP-05: Add WSTG references as applicable.
- OWASP-06: Define vulnerability-to-reference mapping.
- OWASP-07: Define mitigation/reference metadata.
- OWASP-08: Add language/framework security catalogs.
- OWASP-09: Version catalog data.
- OWASP-10: Test mappings and URLs.
- OWASP-11: Document update process.
- OWASP-12: Avoid duplicate or conflicting mappings.
- OWASP-13: Include references in findings/report.
- OWASP-14: Track coverage gaps.
- OWASP-15: Keep knowledge data separate from detector implementation.

### EPIC 5 — XSS detector (P2)
- XSS-01: Catalog input sources.
- XSS-02: Catalog HTML, template, JS, and DOM sinks.
- XSS-03: Detect dynamic HTML construction.
- XSS-04: Detect risky DOM assignments and APIs.
- XSS-05: Identify context-specific escaping patterns.
- XSS-06: Recognize selected sanitization controls.
- XSS-07: Connect source to sink where possible.
- XSS-08: Distinguish reflected/stored/DOM hypotheses only when evidence supports it.
- XSS-09: Map CWE/OWASP.
- XSS-10: Generate evidence and remediation.
- XSS-11: Add vulnerable tests.
- XSS-12: Add safe tests.
- XSS-13: Document unsupported contexts and limitations.
- XSS-14: Integrate with reporting and correlation.
- XSS-15: Benchmark false positives.

### EPIC 6 — Command Injection detector (P2)
- CMD-01: Catalog external sources.
- CMD-02: Catalog command execution sinks.
- CMD-03: Detect dynamic command construction.
- CMD-04: Detect concatenation/interpolation.
- CMD-05: Recognize shell execution vs direct argument APIs.
- CMD-06: Track data to command sinks.
- CMD-07: Recognize structured-argument patterns where appropriate.
- CMD-08: Identify controls and validation conservatively.
- CMD-09: Generate evidence and explanation.
- CMD-10: Map CWE/OWASP.
- CMD-11: Recommend safer APIs and argument handling.
- CMD-12: Add positive and negative tests.
- CMD-13: Integrate reporting.
- CMD-14: Benchmark false positives.
- CMD-15: Document supported APIs and limitations.
- CMD-16: Add framework/wrapper patterns incrementally.
- CMD-17: Validate on isolated examples.

### EPIC 7 — Path Traversal detector (P2)
- PATH-01: Catalog path sources.
- PATH-02: Catalog file read/write/delete sinks.
- PATH-03: Detect dynamic path construction.
- PATH-04: Detect traversal patterns.
- PATH-05: Track source-to-filesystem flow.
- PATH-06: Recognize normalization patterns.
- PATH-07: Recognize confinement/base-directory checks.
- PATH-08: Evaluate controls conservatively.
- PATH-09: Generate evidence.
- PATH-10: Map CWE/OWASP.
- PATH-11: Generate remediation.
- PATH-12: Add positive tests.
- PATH-13: Add negative/safe tests.
- PATH-14: Integrate reports.
- PATH-15: Benchmark false positives.
- PATH-16: Document limitations.
- PATH-17: Validate on isolated examples.

### EPIC 8 — SSRF detector (P2)
- SSRF-01: Catalog URL/request sources.
- SSRF-02: Catalog HTTP/network sinks.
- SSRF-03: Detect dynamic URL construction.
- SSRF-04: Track source-to-request flow.
- SSRF-05: Recognize destination allowlists.
- SSRF-06: Recognize selected URL/IP validation.
- SSRF-07: Consider redirect handling where code evidence is available.
- SSRF-08: Identify internal-network context only when supported by evidence.
- SSRF-09: Generate evidence and explanation.
- SSRF-10: Map CWE/OWASP.
- SSRF-11: Generate remediation.
- SSRF-12: Add positive tests.
- SSRF-13: Add negative tests.
- SSRF-14: Integrate reporting.
- SSRF-15: Benchmark false positives.
- SSRF-16: Document unsupported cases.
- SSRF-17: Validate on isolated examples.

### EPIC 9 — Evidence correlation and deduplication (P1)
- COR-01: Define normalized evidence contract.
- COR-02: Normalize file/line/API references.
- COR-03: Deduplicate repeated detector output.
- COR-04: Group related evidence.
- COR-05: Correlate source, propagation, and sink.
- COR-06: Correlate evidence in same flow/function/file where justified.
- COR-07: Correlate cross-file evidence when flow engine supports it.
- COR-08: Preserve detector-origin findings.
- COR-09: Handle contradictory evidence.
- COR-10: Consolidate contextual findings.
- COR-11: Explain grouping decisions.
- COR-12: Avoid loss of individual evidence.
- COR-13: Add correlation tests.
- COR-14: Integrate with reporting and risk.

### EPIC 10 — Confidence and false-positive management (P1)
- CONF-01: Define confidence levels and semantics.
- CONF-02: Define evidence factors.
- CONF-03: Account for source certainty.
- CONF-04: Account for sink certainty.
- CONF-05: Account for flow completeness.
- CONF-06: Account for controls/mitigations.
- CONF-07: Account for pattern ambiguity.
- CONF-08: Explain confidence rationale.
- CONF-09: Keep confidence independent of severity.
- CONF-10: Mark incomplete analysis.
- CONF-11: Identify likely false-positive candidates.
- CONF-12: Build safe/vulnerable corpus.
- CONF-13: Calibrate using benchmark results.
- CONF-14: Track confidence quality across releases.

### EPIC 11 — Risk Engine (P1)
- RISK-01: Define contextual risk model.
- RISK-02: Define explainable risk bands.
- RISK-03: Incorporate severity.
- RISK-04: Incorporate confidence.
- RISK-05: Incorporate exposure/reachability where known.
- RISK-06: Incorporate sensitive context and impact where evidence exists.
- RISK-07: Incorporate controls.
- RISK-08: Avoid double-counting correlated findings.
- RISK-09: Produce ranking.
- RISK-10: Explain risk rationale.
- RISK-11: Represent unknown context.
- RISK-12: Add model tests.
- RISK-13: Validate against benchmark cases.
- RISK-14: Version the risk model.
- RISK-15: Document assumptions and limitations.

### EPIC 12 — Advanced reports (P1)
- REP-01: Executive summary.
- REP-02: Overall quality/security overview.
- REP-03: Findings by severity.
- REP-04: Findings by type.
- REP-05: Prioritized findings.
- REP-06: Confidence and risk rationale.
- REP-07: Source-to-sink trace.
- REP-08: Evidence and code locations.
- REP-09: CWE/OWASP/ASVS metadata.
- REP-10: Remediation and references.
- REP-11: False-positive review guidance.
- REP-12: Coverage and detector status.
- REP-13: Unsupported files/languages.
- REP-14: Excluded files and reasons.
- REP-15: Agent/detector execution summary.
- REP-16: Analysis errors and partial results.
- REP-17: Repository metadata.
- REP-18: Report timestamp.
- REP-19: Report and schema version.
- REP-20: JSON schema.
- REP-21: Backward compatibility strategy.
- REP-22: Stable report naming.
- REP-23: Timestamped report naming.
- REP-24: Validate report contract.
- REP-25: Add report fixtures and tests.

### EPIC 13 — Detector framework (P1)
- DET-01: Define detector interface.
- DET-02: Define input context.
- DET-03: Define output contract.
- DET-04: Implement registry.
- DET-05: Implement detector configuration.
- DET-06: Define dependency/capability metadata.
- DET-07: Define execution lifecycle.
- DET-08: Add timeouts and resource limits.
- DET-09: Handle detector exceptions independently.
- DET-10: Add metrics.
- DET-11: Add optional safe parallelism.
- DET-12: Add caching only where correctness is preserved.
- DET-13: Version rules/detectors.
- DET-14: Add contract tests.
- DET-15: Prevent detector implementation from bloating central analysis modules.

### EPIC 14 — Multi-language and framework support (P2)
- LANG-01: Define language coverage matrix.
- LANG-02: Define capability matrix by language.
- LANG-03: Prioritize Python.
- LANG-04: Add Java support incrementally.
- LANG-05: Add JavaScript/TypeScript support incrementally.
- LANG-06: Add Go and other languages based on demand.
- LANG-07: Detect frameworks.
- LANG-08: Detect ORM/query APIs.
- LANG-09: Add framework-specific sources and sinks.
- LANG-10: Add language-specific safe patterns.
- LANG-11: Keep detector capabilities explicit.
- LANG-12: Add per-language test corpus.
- LANG-13: Document coverage.
- LANG-14: Expand only when benchmarked.

### EPIC 15 — Security benchmark (P0/P1)
- TESTSEC-01: Create vulnerable sample corpus.
- TESTSEC-02: Create safe sample corpus.
- TESTSEC-03: SQLi positive cases.
- TESTSEC-04: SQLi safe parameterization cases.
- TESTSEC-05: Source/Sink cases.
- TESTSEC-06: Sanitization/validation cases.
- TESTSEC-07: Variable propagation cases.
- TESTSEC-08: Multi-function cases.
- TESTSEC-09: Multi-file cases as supported.
- TESTSEC-10: False-positive cases.
- TESTSEC-11: False-negative review.
- TESTSEC-12: Calculate precision/recall/F1 when dataset labels support it.
- TESTSEC-13: Measure coverage by detector and language.
- TESTSEC-14: Version benchmark.
- TESTSEC-15: Add regression thresholds.
- TESTSEC-16: Run in CI.
- TESTSEC-17: Document benchmark methodology.
- TESTSEC-18: Use isolated training targets such as OWASP Juice Shop, DVWA, WebGoat, NodeGoat, or crAPI where appropriate; do not execute untrusted targets outside controlled environments.

### EPIC 16 — External tools integration (P2)
- EXT-01: Define integration adapter contract.
- EXT-02: Evaluate Semgrep.
- EXT-03: Evaluate CodeQL.
- EXT-04: Evaluate Bandit.
- EXT-05: Evaluate Trivy.
- EXT-06: Evaluate Gitleaks.
- EXT-07: Consider ZAP only for a separate controlled dynamic-testing workflow.
- EXT-08: Normalize external output.
- EXT-09: Deduplicate and correlate.
- EXT-10: Preserve source tool and version.
- EXT-11: Preserve configuration and coverage.
- EXT-12: Handle missing tools.
- EXT-13: Handle tool errors and partial results.
- EXT-14: Document licensing, installation, and operational requirements.
- EXT-15: Keep MiniAgent's contextual analysis/reporting value independent of tool availability.

### EPIC 17 — MiniAgent self-security (P1)
- AGSEC-01: Threat model MiniAgent.
- AGSEC-02: Guarantee analyzed code is not executed.
- AGSEC-03: Guarantee analyzed repository is not modified.
- AGSEC-04: Treat file content as untrusted input.
- AGSEC-05: Defend against prompt/content injection if LLM components are used.
- AGSEC-06: Enforce file-size limits.
- AGSEC-07: Enforce time and resource limits.
- AGSEC-08: Handle symlinks safely.
- AGSEC-09: Prevent archive/path traversal if archive ingestion is added.
- AGSEC-10: Protect secrets in logs.
- AGSEC-11: Isolate evidence and analysis contexts.
- AGSEC-12: Clean temporary files.
- AGSEC-13: Handle concurrency safely.
- AGSEC-14: Add malicious-repository test cases.
- AGSEC-15: Review dependency and tool risks.
- AGSEC-16: Document safe operating model.
- AGSEC-17: Test failure containment.
- AGSEC-18: Ensure reports do not unnecessarily expose secrets.
- AGSEC-19: Add resource exhaustion tests.
- AGSEC-20: Establish security regression suite.

### EPIC 18 — Adaptive analysis planning (P2)
- PLAN-01: Build repository profile.
- PLAN-02: Detect language/framework/architecture.
- PLAN-03: Identify sensitive components.
- PLAN-04: Select detectors based on capability and profile.
- PLAN-05: Resolve detector dependencies.
- PLAN-06: Avoid unnecessary work.
- PLAN-07: Re-plan when analysis discovers relevant context.
- PLAN-08: Track plan execution.
- PLAN-09: Explain selected checks.
- PLAN-10: Explain skipped checks.
- PLAN-11: Explain unsupported checks.
- PLAN-12: Record plan changes.
- PLAN-13: Add plan tests.
- PLAN-14: Validate efficiency and coverage tradeoffs.

### EPIC 19 — Observability and analysis metrics (P2)
- OBS-01: Track duration per agent/detector.
- OBS-02: Track files scanned.
- OBS-03: Track files skipped and reasons.
- OBS-04: Track parse failures.
- OBS-05: Track detector failures.
- OBS-06: Track resource usage where available.
- OBS-07: Track findings by category.
- OBS-08: Track coverage by language/detector.
- OBS-09: Track partial-analysis state.
- OBS-10: Track analysis history.
- OBS-11: Support comparisons.
- OBS-12: Expose actionable diagnostics.
- OBS-13: Avoid leaking secrets in metrics/logs.

### EPIC 20 — CI/CD and regression gates (P1/P2)
- CI-01: Automated unit tests.
- CI-02: Automated integration tests.
- CI-03: Lint and formatting.
- CI-04: Import/package checks.
- CI-05: Detector contract tests.
- CI-06: Security benchmark.
- CI-07: Regression checks.
- CI-08: Report-schema validation.
- CI-09: Artifact publication.
- CI-10: Matrix for supported Python/runtime versions.
- CI-11: Document CI workflow.
- CI-12: Define non-flaky quality gates.

### EPIC 21 — Performance and scalability (P2/P3)
- PERF-01: Profile per-file analysis.
- PERF-02: Identify duplicate reads/work.
- PERF-03: Reuse repository context.
- PERF-04: Optimize parsing and analysis.
- PERF-05: Add caching with invalidation.
- PERF-06: Evaluate detector parallelism.
- PERF-07: Handle large repositories.
- PERF-08: Add configurable limits.
- PERF-09: Define graceful degradation.
- PERF-10: Detect performance regressions.
- PERF-11: Create large-repository benchmark.
- PERF-12: Document tradeoffs.

### EPIC 22 — Developer UX (P3)
- UX-01: Executive summary.
- UX-02: Sort by priority/risk.
- UX-03: Filter by severity.
- UX-04: Filter by CWE/OWASP.
- UX-05: Filter by file/language/confidence.
- UX-06: Inspect evidence and traces.
- UX-07: Inspect correlation rationale.
- UX-08: Compare analysis runs.
- UX-09: Identify new findings.
- UX-10: Identify resolved findings.
- UX-11: Show risk trends.
- UX-12: Export filtered findings.
- UX-13: Improve report navigation.
- UX-14: Keep explanations actionable.

## 7. Proposed sprint roadmap

This sequence is indicative; some epics will span multiple sprints depending on implementation and test results.

### Sprint 1 — Stabilize foundation
- Establish test baseline.
- Reproduce regressions.
- Validate imports and report paths.
- Define SecurityFinding.
- Validate existing SQLi detector.
- Add evidence contract and basic regression tests.

**Exit criteria:** Stable baseline and a consistent security finding representation.

### Sprint 2 — SQLi contextual analysis
- Sources and sinks for SQL.
- Query construction patterns.
- Parameterized query recognition.
- Basic variable tracking.
- Positive and negative tests.

**Exit criteria:** SQLi detector provides evidence and avoids known safe test cases.

### Sprint 3 — Basic data-flow engine
- Assignments and propagation.
- Function arguments/returns for supported patterns.
- Transformations and controls.
- Flow traces and partial-analysis indicators.

**Exit criteria:** Basic Source-to-Sink traces are testable and explainable.

### Sprint 4 — Evidence correlation
- Normalize evidence.
- Deduplicate.
- Group source/query/sink evidence.
- Explain correlation.
- Confidence rationale.

**Exit criteria:** Related signals can form a contextual finding without losing original evidence.

### Sprint 5 — Risk and reporting
- Risk model and rationale.
- Prioritized findings.
- Executive summary.
- Versioned JSON schema.
- Coverage and limitations.

**Exit criteria:** End-to-end security report is useful, traceable, and validated.

### Sprint 6 — XSS
- HTML/DOM sources and sinks.
- Context-sensitive patterns.
- Safe/unsafe tests.
- Evidence and remediation.

### Sprint 7 — Command Injection and Path Traversal
- Implement detector families using shared Source/Sink contracts.
- Add safe-pattern tests and benchmark cases.

### Sprint 8 — SSRF
- URL sources, network sinks, flow tracking, controls, tests.

### Sprint 9 — Benchmark and quality calibration
- Expand safe/vulnerable corpus.
- Measure false positives and false negatives.
- Tune detectors and confidence.
- Establish regression gates.

### Sprint 10 — Extensibility/platform
- Detector registry and configuration.
- Language/framework profiles.
- External-tool adapters.
- Adaptive planning.
- Metrics and performance.

The roadmap is not a promise that each sprint will fit a fixed duration. Data-flow analysis and multi-file support may require additional iterations.

## 8. MVP definition — MiniAgent Security MVP

The MVP is complete only when:

- SQL Injection analysis has been validated and contextualized.
- Basic Source/Sink analysis exists.
- Intra-file variable propagation works for the supported patterns.
- Parameterized queries are recognized in supported cases.
- Relevant validation/sanitization controls are considered.
- Findings contain evidence and locations.
- CWE/OWASP metadata is attached where applicable.
- Confidence is explainable and separate from severity.
- Related evidence is deduplicated.
- Positive and negative tests exist.
- A benchmark measures detector behavior.
- Security findings appear in the global report and structured JSON.
- Analysis remains static: repository code is neither executed nor modified.

## 9. Definition of Done for any detector

A detector is not considered complete merely because a regex or heuristic finds a pattern.

Each detector should have:
- Documented scope and supported language/framework patterns.
- Source and Sink definitions where applicable.
- Positive tests.
- Negative/safe tests.
- Evidence and code locations.
- CWE/OWASP mappings when justified.
- Confidence rationale.
- Remediation guidance.
- Limitations and unsupported cases.
- Integration with common finding/report contracts.
- Benchmark or regression validation.

## 10. Prioritization

### P0 — Foundations
- Stabilization and test baseline.
- Unified finding contract.
- Basic Source/Sink engine.
- SQLi contextual analysis.
- Security knowledge base foundations.
- Benchmark foundation.

### P1 — Make findings reliable and actionable
- Evidence correlation.
- Confidence/false-positive management.
- Risk engine.
- Advanced reports.
- Detector framework.
- MiniAgent self-security.
- CI regression gates.

### P2 — Expand coverage and platform
- XSS, Command Injection, Path Traversal, SSRF.
- Multi-language/framework coverage.
- External tools.
- Adaptive planning.
- Observability.

### P3 — Scale and UX
- Performance optimization.
- Large-repository handling.
- Rich navigation, comparisons, filtering, and trends.

## 11. Success criteria for the target product

The product vision is considered substantially achieved when MiniAgent can, on supported repositories:

1. Produce a repeatable repository inventory.
2. Run modular quality and security analysis.
3. Detect supported vulnerability patterns with evidence.
4. Trace supported Source-to-Sink flows.
5. Recognize selected mitigations and safe patterns.
6. Correlate related evidence without hiding provenance.
7. Explain confidence, severity, and risk separately.
8. Prioritize findings with an understandable rationale.
9. Produce validated, versioned reports.
10. Measure detection quality against safe/vulnerable benchmarks.
11. Report coverage, exclusions, limitations, and analysis failures.
12. Analyze repositories safely without executing or modifying their code.

## 12. What MiniAgent will not claim

- That every vulnerability has been detected.
- That a heuristic candidate is confirmed exploitable.
- That supported patterns imply complete language coverage.
- That static analysis alone proves runtime behavior.
- That an absence of findings means a repository is secure.

## 13. Recommended working method

- Work directly from prioritized backlog items.
- Keep main branch changes small and reviewable.
- Add tests with each detector or capability.
- Validate before claiming completion.
- Record limitations and benchmark results.
- Avoid building all detectors before the shared architecture is validated.
- Prioritize a reliable Source/Sink foundation and SQLi contextual analysis before expanding detector count.

## 14. Final product statement

MiniAgent aims to become a **static code quality and contextual security analysis platform** that understands repository structure, detects potential issues, follows data flows where supported, correlates evidence, estimates confidence and contextual risk, prioritizes what matters, and explains findings in a way developers can act on.

This document is the product vision and backlog baseline. Implementation status must be tracked separately from the roadmap and updated as work is completed and validated.
