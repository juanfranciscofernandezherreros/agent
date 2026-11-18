# Individual implementation plans for MiniAgent backlog

This document contains an execution plan for **every task** listed in `docs/MINAGENT_PRODUCT_VISION_AND_BACKLOG.md`. The backlog determines *what*; each plan describes *how to approach it*. Plans are starting guidance and must be verified against the repository before implementation.

## Rules for Claude Code
- Before starting a backlog task, read its plan section in this file.
- Verify current code and dependencies; do not assume files or APIs mentioned by generic plan guidance exist.
- Follow the steps and acceptance criteria. If discoveries require a change, explain it in the task log and update this plan before proceeding.
- Execute tasks autonomously in dependency/priority order; checkpoints do not pause execution.
- Never execute or modify the repositories being analyzed by MiniAgent. MiniAgent's own tests are allowed.
- Mark tasks complete only after review and actual validation evidence.

## Plan index
- [STAB-01](#stab-01) — Establish baseline test suite and record current status.
- [STAB-02](#stab-02) — Reproduce and fix existing regressions.
- [STAB-03](#stab-03) — Validate imports, package structure, and dependency setup.
- [STAB-04](#stab-04) — Validate analysis end-to-end on representative repositories.
- [STAB-05](#stab-05) — Validate JSON output and error handling.
- [STAB-06](#stab-06) — Test single-repository and multi-repository paths.
- [STAB-07](#stab-07) — Validate security findings appear in reports.
- [STAB-08](#stab-08) — Test agent failures and partial-analysis behavior.
- [STAB-09](#stab-09) — Establish performance baseline.
- [STAB-10](#stab-10) — Document known limitations and baseline coverage.
- [CORE-01](#core-01) — Define stable finding identifier.
- [CORE-02](#core-02) — Define finding type/category and title.
- [CORE-03](#core-03) — Define severity.
- [CORE-04](#core-04) — Define confidence.
- [CORE-05](#core-05) — Define status/classification (candidate, confirmed by evidence, needs review, etc.).
- [CORE-06](#core-06) — Define evidence model.
- [CORE-07](#core-07) — Define one or multiple locations.
- [CORE-08](#core-08) — Define source and sink fields.
- [CORE-09](#core-09) — Define CWE and OWASP mappings.
- [CORE-10](#core-10) — Define risk fields and rationale.
- [CORE-11](#core-11) — Define remediation and references.
- [CORE-12](#core-12) — Implement serialization.
- [CORE-13](#core-13) — Integrate with analysis/reporting.
- [CORE-14](#core-14) — Preserve compatibility with existing findings where practical.
- [FLOW-01](#flow-01) — Define Source catalog and contract.
- [FLOW-02](#flow-02) — Catalog HTTP parameters, query, headers, cookies, body, CLI, environment, files, and messaging inputs.
- [FLOW-03](#flow-03) — Define Sink catalog and contract.
- [FLOW-04](#flow-04) — Catalog SQL, command execution, HTML/JS, filesystem, HTTP, deserialization, dynamic code, and authorization sinks.
- [FLOW-05](#flow-05) — Track basic variables and assignments.
- [FLOW-06](#flow-06) — Track propagation through concatenation and interpolation.
- [FLOW-07](#flow-07) — Track function arguments and returns.
- [FLOW-08](#flow-08) — Track simple transformations.
- [FLOW-09](#flow-09) — Represent validation and sanitization.
- [FLOW-10](#flow-10) — Recognize selected safe/mitigating patterns.
- [FLOW-11](#flow-11) — Build intra-file flow graph.
- [FLOW-12](#flow-12) — Add selected cross-function propagation.
- [FLOW-13](#flow-13) — Expand to multi-file propagation incrementally.
- [FLOW-14](#flow-14) — Represent path reachability and partial paths.
- [FLOW-15](#flow-15) — Generate evidence traces and explanations.
- [FLOW-16](#flow-16) — Mark analysis completeness and unknown links.
- [FLOW-17](#flow-17) — Add unit and integration tests for propagation and controls.
- [SQLI-01](#sqli-01) — Review and validate current SQLi heuristic.
- [SQLI-02](#sqli-02) — Cover string concatenation.
- [SQLI-03](#sqli-03) — Cover f-strings/interpolation.
- [SQLI-04](#sqli-04) — Cover format(), percent formatting, and template patterns.
- [SQLI-05](#sqli-05) — Cover multiline/dynamic query construction.
- [SQLI-06](#sqli-06) — Track query variables.
- [SQLI-07](#sqli-07) — Identify external sources.
- [SQLI-08](#sqli-08) — Identify SQL execution sinks.
- [SQLI-09](#sqli-09) — Recognize common parameterized-query patterns.
- [SQLI-10](#sqli-10) — Recognize positional and named parameters where supported.
- [SQLI-11](#sqli-11) — Recognize selected ORM/query-builder patterns.
- [SQLI-12](#sqli-12) — Identify dynamic SQL identifiers separately from values.
- [SQLI-13](#sqli-13) — Recognize allowlist/control patterns conservatively.
- [SQLI-14](#sqli-14) — Connect source, query construction, and sink.
- [SQLI-15](#sqli-15) — Generate contextual evidence.
- [SQLI-16](#sqli-16) — Evaluate confidence and severity separately.
- [SQLI-17](#sqli-17) — Explain the potential issue.
- [SQLI-18](#sqli-18) — Generate remediation guidance.
- [SQLI-19](#sqli-19) — Add vulnerable positive tests.
- [SQLI-20](#sqli-20) — Add safe negative tests.
- [SQLI-21](#sqli-21) — Add multiline and variable propagation tests.
- [SQLI-22](#sqli-22) — Validate against isolated training/lab examples.
- [SQLI-23](#sqli-23) — Document limitations and supported patterns.
- [SQLI-24](#sqli-24) — Measure false positives on safe corpus.
- [SQLI-25](#sqli-25) — Integrate with unified SecurityFinding.
- [SQLI-26](#sqli-26) — Integrate OWASP/CWE metadata.
- [SQLI-27](#sqli-27) — Ensure reports preserve evidence and locations.
- [OWASP-01](#owasp-01) — Centralize versioned OWASP Top 10 catalog.
- [OWASP-02](#owasp-02) — Add CWE catalog/mappings.
- [OWASP-03](#owasp-03) — Add ASVS references.
- [OWASP-04](#owasp-04) — Add API Security Top 10 references.
- [OWASP-05](#owasp-05) — Add WSTG references as applicable.
- [OWASP-06](#owasp-06) — Define vulnerability-to-reference mapping.
- [OWASP-07](#owasp-07) — Define mitigation/reference metadata.
- [OWASP-08](#owasp-08) — Add language/framework security catalogs.
- [OWASP-09](#owasp-09) — Version catalog data.
- [OWASP-10](#owasp-10) — Test mappings and URLs.
- [OWASP-11](#owasp-11) — Document update process.
- [OWASP-12](#owasp-12) — Avoid duplicate or conflicting mappings.
- [OWASP-13](#owasp-13) — Include references in findings/report.
- [OWASP-14](#owasp-14) — Track coverage gaps.
- [OWASP-15](#owasp-15) — Keep knowledge data separate from detector implementation.
- [XSS-01](#xss-01) — Catalog input sources.
- [XSS-02](#xss-02) — Catalog HTML, template, JS, and DOM sinks.
- [XSS-03](#xss-03) — Detect dynamic HTML construction.
- [XSS-04](#xss-04) — Detect risky DOM assignments and APIs.
- [XSS-05](#xss-05) — Identify context-specific escaping patterns.
- [XSS-06](#xss-06) — Recognize selected sanitization controls.
- [XSS-07](#xss-07) — Connect source to sink where possible.
- [XSS-08](#xss-08) — Distinguish reflected/stored/DOM hypotheses only when evidence supports it.
- [XSS-09](#xss-09) — Map CWE/OWASP.
- [XSS-10](#xss-10) — Generate evidence and remediation.
- [XSS-11](#xss-11) — Add vulnerable tests.
- [XSS-12](#xss-12) — Add safe tests.
- [XSS-13](#xss-13) — Document unsupported contexts and limitations.
- [XSS-14](#xss-14) — Integrate with reporting and correlation.
- [XSS-15](#xss-15) — Benchmark false positives.
- [CMD-01](#cmd-01) — Catalog external sources.
- [CMD-02](#cmd-02) — Catalog command execution sinks.
- [CMD-03](#cmd-03) — Detect dynamic command construction.
- [CMD-04](#cmd-04) — Detect concatenation/interpolation.
- [CMD-05](#cmd-05) — Recognize shell execution vs direct argument APIs.
- [CMD-06](#cmd-06) — Track data to command sinks.
- [CMD-07](#cmd-07) — Recognize structured-argument patterns where appropriate.
- [CMD-08](#cmd-08) — Identify controls and validation conservatively.
- [CMD-09](#cmd-09) — Generate evidence and explanation.
- [CMD-10](#cmd-10) — Map CWE/OWASP.
- [CMD-11](#cmd-11) — Recommend safer APIs and argument handling.
- [CMD-12](#cmd-12) — Add positive and negative tests.
- [CMD-13](#cmd-13) — Integrate reporting.
- [CMD-14](#cmd-14) — Benchmark false positives.
- [CMD-15](#cmd-15) — Document supported APIs and limitations.
- [CMD-16](#cmd-16) — Add framework/wrapper patterns incrementally.
- [CMD-17](#cmd-17) — Validate on isolated examples.
- [PATH-01](#path-01) — Catalog path sources.
- [PATH-02](#path-02) — Catalog file read/write/delete sinks.
- [PATH-03](#path-03) — Detect dynamic path construction.
- [PATH-04](#path-04) — Detect traversal patterns.
- [PATH-05](#path-05) — Track source-to-filesystem flow.
- [PATH-06](#path-06) — Recognize normalization patterns.
- [PATH-07](#path-07) — Recognize confinement/base-directory checks.
- [PATH-08](#path-08) — Evaluate controls conservatively.
- [PATH-09](#path-09) — Generate evidence.
- [PATH-10](#path-10) — Map CWE/OWASP.
- [PATH-11](#path-11) — Generate remediation.
- [PATH-12](#path-12) — Add positive tests.
- [PATH-13](#path-13) — Add negative/safe tests.
- [PATH-14](#path-14) — Integrate reports.
- [PATH-15](#path-15) — Benchmark false positives.
- [PATH-16](#path-16) — Document limitations.
- [PATH-17](#path-17) — Validate on isolated examples.
- [SSRF-01](#ssrf-01) — Catalog URL/request sources.
- [SSRF-02](#ssrf-02) — Catalog HTTP/network sinks.
- [SSRF-03](#ssrf-03) — Detect dynamic URL construction.
- [SSRF-04](#ssrf-04) — Track source-to-request flow.
- [SSRF-05](#ssrf-05) — Recognize destination allowlists.
- [SSRF-06](#ssrf-06) — Recognize selected URL/IP validation.
- [SSRF-07](#ssrf-07) — Consider redirect handling where code evidence is available.
- [SSRF-08](#ssrf-08) — Identify internal-network context only when supported by evidence.
- [SSRF-09](#ssrf-09) — Generate evidence and explanation.
- [SSRF-10](#ssrf-10) — Map CWE/OWASP.
- [SSRF-11](#ssrf-11) — Generate remediation.
- [SSRF-12](#ssrf-12) — Add positive tests.
- [SSRF-13](#ssrf-13) — Add negative tests.
- [SSRF-14](#ssrf-14) — Integrate reporting.
- [SSRF-15](#ssrf-15) — Benchmark false positives.
- [SSRF-16](#ssrf-16) — Document unsupported cases.
- [SSRF-17](#ssrf-17) — Validate on isolated examples.
- [COR-01](#cor-01) — Define normalized evidence contract.
- [COR-02](#cor-02) — Normalize file/line/API references.
- [COR-03](#cor-03) — Deduplicate repeated detector output.
- [COR-04](#cor-04) — Group related evidence.
- [COR-05](#cor-05) — Correlate source, propagation, and sink.
- [COR-06](#cor-06) — Correlate evidence in same flow/function/file where justified.
- [COR-07](#cor-07) — Correlate cross-file evidence when flow engine supports it.
- [COR-08](#cor-08) — Preserve detector-origin findings.
- [COR-09](#cor-09) — Handle contradictory evidence.
- [COR-10](#cor-10) — Consolidate contextual findings.
- [COR-11](#cor-11) — Explain grouping decisions.
- [COR-12](#cor-12) — Avoid loss of individual evidence.
- [COR-13](#cor-13) — Add correlation tests.
- [COR-14](#cor-14) — Integrate with reporting and risk.
- [CONF-01](#conf-01) — Define confidence levels and semantics.
- [CONF-02](#conf-02) — Define evidence factors.
- [CONF-03](#conf-03) — Account for source certainty.
- [CONF-04](#conf-04) — Account for sink certainty.
- [CONF-05](#conf-05) — Account for flow completeness.
- [CONF-06](#conf-06) — Account for controls/mitigations.
- [CONF-07](#conf-07) — Account for pattern ambiguity.
- [CONF-08](#conf-08) — Explain confidence rationale.
- [CONF-09](#conf-09) — Keep confidence independent of severity.
- [CONF-10](#conf-10) — Mark incomplete analysis.
- [CONF-11](#conf-11) — Identify likely false-positive candidates.
- [CONF-12](#conf-12) — Build safe/vulnerable corpus.
- [CONF-13](#conf-13) — Calibrate using benchmark results.
- [CONF-14](#conf-14) — Track confidence quality across releases.
- [RISK-01](#risk-01) — Define contextual risk model.
- [RISK-02](#risk-02) — Define explainable risk bands.
- [RISK-03](#risk-03) — Incorporate severity.
- [RISK-04](#risk-04) — Incorporate confidence.
- [RISK-05](#risk-05) — Incorporate exposure/reachability where known.
- [RISK-06](#risk-06) — Incorporate sensitive context and impact where evidence exists.
- [RISK-07](#risk-07) — Incorporate controls.
- [RISK-08](#risk-08) — Avoid double-counting correlated findings.
- [RISK-09](#risk-09) — Produce ranking.
- [RISK-10](#risk-10) — Explain risk rationale.
- [RISK-11](#risk-11) — Represent unknown context.
- [RISK-12](#risk-12) — Add model tests.
- [RISK-13](#risk-13) — Validate against benchmark cases.
- [RISK-14](#risk-14) — Version the risk model.
- [RISK-15](#risk-15) — Document assumptions and limitations.
- [REP-01](#rep-01) — Executive summary.
- [REP-02](#rep-02) — Overall quality/security overview.
- [REP-03](#rep-03) — Findings by severity.
- [REP-04](#rep-04) — Findings by type.
- [REP-05](#rep-05) — Prioritized findings.
- [REP-06](#rep-06) — Confidence and risk rationale.
- [REP-07](#rep-07) — Source-to-sink trace.
- [REP-08](#rep-08) — Evidence and code locations.
- [REP-09](#rep-09) — CWE/OWASP/ASVS metadata.
- [REP-10](#rep-10) — Remediation and references.
- [REP-11](#rep-11) — False-positive review guidance.
- [REP-12](#rep-12) — Coverage and detector status.
- [REP-13](#rep-13) — Unsupported files/languages.
- [REP-14](#rep-14) — Excluded files and reasons.
- [REP-15](#rep-15) — Agent/detector execution summary.
- [REP-16](#rep-16) — Analysis errors and partial results.
- [REP-17](#rep-17) — Repository metadata.
- [REP-18](#rep-18) — Report timestamp.
- [REP-19](#rep-19) — Report and schema version.
- [REP-20](#rep-20) — JSON schema.
- [REP-21](#rep-21) — Backward compatibility strategy.
- [REP-22](#rep-22) — Stable report naming.
- [REP-23](#rep-23) — Timestamped report naming.
- [REP-24](#rep-24) — Validate report contract.
- [REP-25](#rep-25) — Add report fixtures and tests.
- [DET-01](#det-01) — Define detector interface.
- [DET-02](#det-02) — Define input context.
- [DET-03](#det-03) — Define output contract.
- [DET-04](#det-04) — Implement registry.
- [DET-05](#det-05) — Implement detector configuration.
- [DET-06](#det-06) — Define dependency/capability metadata.
- [DET-07](#det-07) — Define execution lifecycle.
- [DET-08](#det-08) — Add timeouts and resource limits.
- [DET-09](#det-09) — Handle detector exceptions independently.
- [DET-10](#det-10) — Add metrics.
- [DET-11](#det-11) — Add optional safe parallelism.
- [DET-12](#det-12) — Add caching only where correctness is preserved.
- [DET-13](#det-13) — Version rules/detectors.
- [DET-14](#det-14) — Add contract tests.
- [DET-15](#det-15) — Prevent detector implementation from bloating central analysis modules.
- [LANG-01](#lang-01) — Define language coverage matrix.
- [LANG-02](#lang-02) — Define capability matrix by language.
- [LANG-03](#lang-03) — Prioritize Python.
- [LANG-04](#lang-04) — Add Java support incrementally.
- [LANG-05](#lang-05) — Add JavaScript/TypeScript support incrementally.
- [LANG-06](#lang-06) — Add Go and other languages based on demand.
- [LANG-07](#lang-07) — Detect frameworks.
- [LANG-08](#lang-08) — Detect ORM/query APIs.
- [LANG-09](#lang-09) — Add framework-specific sources and sinks.
- [LANG-10](#lang-10) — Add language-specific safe patterns.
- [LANG-11](#lang-11) — Keep detector capabilities explicit.
- [LANG-12](#lang-12) — Add per-language test corpus.
- [LANG-13](#lang-13) — Document coverage.
- [LANG-14](#lang-14) — Expand only when benchmarked.
- [TESTSEC-01](#testsec-01) — Create vulnerable sample corpus.
- [TESTSEC-02](#testsec-02) — Create safe sample corpus.
- [TESTSEC-03](#testsec-03) — SQLi positive cases.
- [TESTSEC-04](#testsec-04) — SQLi safe parameterization cases.
- [TESTSEC-05](#testsec-05) — Source/Sink cases.
- [TESTSEC-06](#testsec-06) — Sanitization/validation cases.
- [TESTSEC-07](#testsec-07) — Variable propagation cases.
- [TESTSEC-08](#testsec-08) — Multi-function cases.
- [TESTSEC-09](#testsec-09) — Multi-file cases as supported.
- [TESTSEC-10](#testsec-10) — False-positive cases.
- [TESTSEC-11](#testsec-11) — False-negative review.
- [TESTSEC-12](#testsec-12) — Calculate precision/recall/F1 when dataset labels support it.
- [TESTSEC-13](#testsec-13) — Measure coverage by detector and language.
- [TESTSEC-14](#testsec-14) — Version benchmark.
- [TESTSEC-15](#testsec-15) — Add regression thresholds.
- [TESTSEC-16](#testsec-16) — Run in CI.
- [TESTSEC-17](#testsec-17) — Document benchmark methodology.
- [TESTSEC-18](#testsec-18) — Use isolated training targets such as OWASP Juice Shop, DVWA, WebGoat, NodeGoat, or crAPI where appropriate; do not execute untrusted targets outside controlled environments.
- [EXT-01](#ext-01) — Define integration adapter contract.
- [EXT-02](#ext-02) — Evaluate Semgrep.
- [EXT-03](#ext-03) — Evaluate CodeQL.
- [EXT-04](#ext-04) — Evaluate Bandit.
- [EXT-05](#ext-05) — Evaluate Trivy.
- [EXT-06](#ext-06) — Evaluate Gitleaks.
- [EXT-07](#ext-07) — Consider ZAP only for a separate controlled dynamic-testing workflow.
- [EXT-08](#ext-08) — Normalize external output.
- [EXT-09](#ext-09) — Deduplicate and correlate.
- [EXT-10](#ext-10) — Preserve source tool and version.
- [EXT-11](#ext-11) — Preserve configuration and coverage.
- [EXT-12](#ext-12) — Handle missing tools.
- [EXT-13](#ext-13) — Handle tool errors and partial results.
- [EXT-14](#ext-14) — Document licensing, installation, and operational requirements.
- [EXT-15](#ext-15) — Keep MiniAgent's contextual analysis/reporting value independent of tool availability.
- [AGSEC-01](#agsec-01) — Threat model MiniAgent.
- [AGSEC-02](#agsec-02) — Guarantee analyzed code is not executed.
- [AGSEC-03](#agsec-03) — Guarantee analyzed repository is not modified.
- [AGSEC-04](#agsec-04) — Treat file content as untrusted input.
- [AGSEC-05](#agsec-05) — Defend against prompt/content injection if LLM components are used.
- [AGSEC-06](#agsec-06) — Enforce file-size limits.
- [AGSEC-07](#agsec-07) — Enforce time and resource limits.
- [AGSEC-08](#agsec-08) — Handle symlinks safely.
- [AGSEC-09](#agsec-09) — Prevent archive/path traversal if archive ingestion is added.
- [AGSEC-10](#agsec-10) — Protect secrets in logs.
- [AGSEC-11](#agsec-11) — Isolate evidence and analysis contexts.
- [AGSEC-12](#agsec-12) — Clean temporary files.
- [AGSEC-13](#agsec-13) — Handle concurrency safely.
- [AGSEC-14](#agsec-14) — Add malicious-repository test cases.
- [AGSEC-15](#agsec-15) — Review dependency and tool risks.
- [AGSEC-16](#agsec-16) — Document safe operating model.
- [AGSEC-17](#agsec-17) — Test failure containment.
- [AGSEC-18](#agsec-18) — Ensure reports do not unnecessarily expose secrets.
- [AGSEC-19](#agsec-19) — Add resource exhaustion tests.
- [AGSEC-20](#agsec-20) — Establish security regression suite.
- [PLAN-01](#plan-01) — Build repository profile.
- [PLAN-02](#plan-02) — Detect language/framework/architecture.
- [PLAN-03](#plan-03) — Identify sensitive components.
- [PLAN-04](#plan-04) — Select detectors based on capability and profile.
- [PLAN-05](#plan-05) — Resolve detector dependencies.
- [PLAN-06](#plan-06) — Avoid unnecessary work.
- [PLAN-07](#plan-07) — Re-plan when analysis discovers relevant context.
- [PLAN-08](#plan-08) — Track plan execution.
- [PLAN-09](#plan-09) — Explain selected checks.
- [PLAN-10](#plan-10) — Explain skipped checks.
- [PLAN-11](#plan-11) — Explain unsupported checks.
- [PLAN-12](#plan-12) — Record plan changes.
- [PLAN-13](#plan-13) — Add plan tests.
- [PLAN-14](#plan-14) — Validate efficiency and coverage tradeoffs.
- [OBS-01](#obs-01) — Track duration per agent/detector.
- [OBS-02](#obs-02) — Track files scanned.
- [OBS-03](#obs-03) — Track files skipped and reasons.
- [OBS-04](#obs-04) — Track parse failures.
- [OBS-05](#obs-05) — Track detector failures.
- [OBS-06](#obs-06) — Track resource usage where available.
- [OBS-07](#obs-07) — Track findings by category.
- [OBS-08](#obs-08) — Track coverage by language/detector.
- [OBS-09](#obs-09) — Track partial-analysis state.
- [OBS-10](#obs-10) — Track analysis history.
- [OBS-11](#obs-11) — Support comparisons.
- [OBS-12](#obs-12) — Expose actionable diagnostics.
- [OBS-13](#obs-13) — Avoid leaking secrets in metrics/logs.
- [CI-01](#ci-01) — Automated unit tests.
- [CI-02](#ci-02) — Automated integration tests.
- [CI-03](#ci-03) — Lint and formatting.
- [CI-04](#ci-04) — Import/package checks.
- [CI-05](#ci-05) — Detector contract tests.
- [CI-06](#ci-06) — Security benchmark.
- [CI-07](#ci-07) — Regression checks.
- [CI-08](#ci-08) — Report-schema validation.
- [CI-09](#ci-09) — Artifact publication.
- [CI-10](#ci-10) — Matrix for supported Python/runtime versions.
- [CI-11](#ci-11) — Document CI workflow.
- [CI-12](#ci-12) — Define non-flaky quality gates.
- [PERF-01](#perf-01) — Profile per-file analysis.
- [PERF-02](#perf-02) — Identify duplicate reads/work.
- [PERF-03](#perf-03) — Reuse repository context.
- [PERF-04](#perf-04) — Optimize parsing and analysis.
- [PERF-05](#perf-05) — Add caching with invalidation.
- [PERF-06](#perf-06) — Evaluate detector parallelism.
- [PERF-07](#perf-07) — Handle large repositories.
- [PERF-08](#perf-08) — Add configurable limits.
- [PERF-09](#perf-09) — Define graceful degradation.
- [PERF-10](#perf-10) — Detect performance regressions.
- [PERF-11](#perf-11) — Create large-repository benchmark.
- [PERF-12](#perf-12) — Document tradeoffs.
- [UX-01](#ux-01) — Executive summary.
- [UX-02](#ux-02) — Sort by priority/risk.
- [UX-03](#ux-03) — Filter by severity.
- [UX-04](#ux-04) — Filter by CWE/OWASP.
- [UX-05](#ux-05) — Filter by file/language/confidence.
- [UX-06](#ux-06) — Inspect evidence and traces.
- [UX-07](#ux-07) — Inspect correlation rationale.
- [UX-08](#ux-08) — Compare analysis runs.
- [UX-09](#ux-09) — Identify new findings.
- [UX-10](#ux-10) — Identify resolved findings.
- [UX-11](#ux-11) — Show risk trends.
- [UX-12](#ux-12) — Export filtered findings.
- [UX-13](#ux-13) — Improve report navigation.
- [UX-14](#ux-14) — Keep explanations actionable.

---

## STAB-01 — Establish baseline test suite and record current status.

**Objective:** Establish baseline test suite and record current status.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-02 — Reproduce and fix existing regressions.

**Objective:** Reproduce and fix existing regressions.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-03 — Validate imports, package structure, and dependency setup.

**Objective:** Validate imports, package structure, and dependency setup.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-04 — Validate analysis end-to-end on representative repositories.

**Objective:** Validate analysis end-to-end on representative repositories.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-05 — Validate JSON output and error handling.

**Objective:** Validate JSON output and error handling.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-06 — Test single-repository and multi-repository paths.

**Objective:** Test single-repository and multi-repository paths.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-07 — Validate security findings appear in reports.

**Objective:** Validate security findings appear in reports.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-08 — Test agent failures and partial-analysis behavior.

**Objective:** Test agent failures and partial-analysis behavior.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-09 — Establish performance baseline.

**Objective:** Establish performance baseline.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## STAB-10 — Document known limitations and baseline coverage.

**Objective:** Document known limitations and baseline coverage.

**Implementation plan**
1. Baseline and reproducibility: Inspect the existing project structure, test/configuration entry points, and relevant behavior. Capture the current state before changing anything; avoid assumptions based on docs alone.
2. Use existing test infrastructure to exercise the behavior with representative fixtures. Record command, outcome, failures, and environmental constraints. Fix only issues within this task's scope.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-01 — Define stable finding identifier.

**Objective:** Define stable finding identifier.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-02 — Define finding type/category and title.

**Objective:** Define finding type/category and title.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-03 — Define severity.

**Objective:** Define severity.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-04 — Define confidence.

**Objective:** Define confidence.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-05 — Define status/classification (candidate, confirmed by evidence, needs review, etc.).

**Objective:** Define status/classification (candidate, confirmed by evidence, needs review, etc.).

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-06 — Define evidence model.

**Objective:** Define evidence model.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-07 — Define one or multiple locations.

**Objective:** Define one or multiple locations.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-08 — Define source and sink fields.

**Objective:** Define source and sink fields.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-09 — Define CWE and OWASP mappings.

**Objective:** Define CWE and OWASP mappings.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-10 — Define risk fields and rationale.

**Objective:** Define risk fields and rationale.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-11 — Define remediation and references.

**Objective:** Define remediation and references.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-12 — Implement serialization.

**Objective:** Implement serialization.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-13 — Integrate with analysis/reporting.

**Objective:** Integrate with analysis/reporting.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CORE-14 — Preserve compatibility with existing findings where practical.

**Objective:** Preserve compatibility with existing findings where practical.

**Implementation plan**
1. Shared finding contract: Inspect current finding models, detector outputs, and report consumers. Design this field/behavior to fit the shared contract and preserve compatibility where practical.
2. Implement the smallest typed change; update serialization, consumers, and migration/default handling as needed. Include malformed/missing-value behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-01 — Define Source catalog and contract.

**Objective:** Define Source catalog and contract.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-02 — Catalog HTTP parameters, query, headers, cookies, body, CLI, environment, files, and messaging inputs.

**Objective:** Catalog HTTP parameters, query, headers, cookies, body, CLI, environment, files, and messaging inputs.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-03 — Define Sink catalog and contract.

**Objective:** Define Sink catalog and contract.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-04 — Catalog SQL, command execution, HTML/JS, filesystem, HTTP, deserialization, dynamic code, and authorization sinks.

**Objective:** Catalog SQL, command execution, HTML/JS, filesystem, HTTP, deserialization, dynamic code, and authorization sinks.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-05 — Track basic variables and assignments.

**Objective:** Track basic variables and assignments.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-06 — Track propagation through concatenation and interpolation.

**Objective:** Track propagation through concatenation and interpolation.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-07 — Track function arguments and returns.

**Objective:** Track function arguments and returns.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-08 — Track simple transformations.

**Objective:** Track simple transformations.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-09 — Represent validation and sanitization.

**Objective:** Represent validation and sanitization.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-10 — Recognize selected safe/mitigating patterns.

**Objective:** Recognize selected safe/mitigating patterns.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-11 — Build intra-file flow graph.

**Objective:** Build intra-file flow graph.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-12 — Add selected cross-function propagation.

**Objective:** Add selected cross-function propagation.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-13 — Expand to multi-file propagation incrementally.

**Objective:** Expand to multi-file propagation incrementally.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-14 — Represent path reachability and partial paths.

**Objective:** Represent path reachability and partial paths.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-15 — Generate evidence traces and explanations.

**Objective:** Generate evidence traces and explanations.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-16 — Mark analysis completeness and unknown links.

**Objective:** Mark analysis completeness and unknown links.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## FLOW-17 — Add unit and integration tests for propagation and controls.

**Objective:** Add unit and integration tests for propagation and controls.

**Implementation plan**
1. Data-flow analysis: Inspect parser/AST representation and existing detector plumbing. Define the supported syntax and conservative boundaries for this flow capability.
2. Implement tracking/evidence without executing analyzed code. Preserve locations and provenance; represent unknown or partial flow explicitly rather than guessing.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-01 — Review and validate current SQLi heuristic.

**Objective:** Review and validate current SQLi heuristic.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-02 — Cover string concatenation.

**Objective:** Cover string concatenation.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-03 — Cover f-strings/interpolation.

**Objective:** Cover f-strings/interpolation.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-04 — Cover format(), percent formatting, and template patterns.

**Objective:** Cover format(), percent formatting, and template patterns.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-05 — Cover multiline/dynamic query construction.

**Objective:** Cover multiline/dynamic query construction.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-06 — Track query variables.

**Objective:** Track query variables.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-07 — Identify external sources.

**Objective:** Identify external sources.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-08 — Identify SQL execution sinks.

**Objective:** Identify SQL execution sinks.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-09 — Recognize common parameterized-query patterns.

**Objective:** Recognize common parameterized-query patterns.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-10 — Recognize positional and named parameters where supported.

**Objective:** Recognize positional and named parameters where supported.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-11 — Recognize selected ORM/query-builder patterns.

**Objective:** Recognize selected ORM/query-builder patterns.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-12 — Identify dynamic SQL identifiers separately from values.

**Objective:** Identify dynamic SQL identifiers separately from values.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-13 — Recognize allowlist/control patterns conservatively.

**Objective:** Recognize allowlist/control patterns conservatively.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-14 — Connect source, query construction, and sink.

**Objective:** Connect source, query construction, and sink.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-15 — Generate contextual evidence.

**Objective:** Generate contextual evidence.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-16 — Evaluate confidence and severity separately.

**Objective:** Evaluate confidence and severity separately.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-17 — Explain the potential issue.

**Objective:** Explain the potential issue.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-18 — Generate remediation guidance.

**Objective:** Generate remediation guidance.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-19 — Add vulnerable positive tests.

**Objective:** Add vulnerable positive tests.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-20 — Add safe negative tests.

**Objective:** Add safe negative tests.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-21 — Add multiline and variable propagation tests.

**Objective:** Add multiline and variable propagation tests.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-22 — Validate against isolated training/lab examples.

**Objective:** Validate against isolated training/lab examples.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-23 — Document limitations and supported patterns.

**Objective:** Document limitations and supported patterns.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-24 — Measure false positives on safe corpus.

**Objective:** Measure false positives on safe corpus.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-25 — Integrate with unified SecurityFinding.

**Objective:** Integrate with unified SecurityFinding.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-26 — Integrate OWASP/CWE metadata.

**Objective:** Integrate OWASP/CWE metadata.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SQLI-27 — Ensure reports preserve evidence and locations.

**Objective:** Ensure reports preserve evidence and locations.

**Implementation plan**
1. SQL Injection contextual analysis: Inspect SQLi detector, Python AST handling, source/sink catalogs, and query patterns currently supported. Specify syntax and false-positive boundaries.
2. Implement detection/flow evidence for the task's SQL pattern; distinguish parameterized values from dynamic identifiers and avoid claiming exploitability from a heuristic alone.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-01 — Centralize versioned OWASP Top 10 catalog.

**Objective:** Centralize versioned OWASP Top 10 catalog.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-02 — Add CWE catalog/mappings.

**Objective:** Add CWE catalog/mappings.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-03 — Add ASVS references.

**Objective:** Add ASVS references.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-04 — Add API Security Top 10 references.

**Objective:** Add API Security Top 10 references.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-05 — Add WSTG references as applicable.

**Objective:** Add WSTG references as applicable.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-06 — Define vulnerability-to-reference mapping.

**Objective:** Define vulnerability-to-reference mapping.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-07 — Define mitigation/reference metadata.

**Objective:** Define mitigation/reference metadata.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-08 — Add language/framework security catalogs.

**Objective:** Add language/framework security catalogs.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-09 — Version catalog data.

**Objective:** Version catalog data.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-10 — Test mappings and URLs.

**Objective:** Test mappings and URLs.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-11 — Document update process.

**Objective:** Document update process.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-12 — Avoid duplicate or conflicting mappings.

**Objective:** Avoid duplicate or conflicting mappings.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-13 — Include references in findings/report.

**Objective:** Include references in findings/report.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-14 — Track coverage gaps.

**Objective:** Track coverage gaps.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OWASP-15 — Keep knowledge data separate from detector implementation.

**Objective:** Keep knowledge data separate from detector implementation.

**Implementation plan**
1. Security knowledge catalog: Review current security metadata and authoritative catalog conventions. Define stable identifiers, versioning, mapping semantics, and data/implementation separation.
2. Add or update catalog entries and mapping logic. Validate references and prevent duplicate, stale, or contradictory metadata; do not fabricate mappings.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-01 — Catalog input sources.

**Objective:** Catalog input sources.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-02 — Catalog HTML, template, JS, and DOM sinks.

**Objective:** Catalog HTML, template, JS, and DOM sinks.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-03 — Detect dynamic HTML construction.

**Objective:** Detect dynamic HTML construction.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-04 — Detect risky DOM assignments and APIs.

**Objective:** Detect risky DOM assignments and APIs.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-05 — Identify context-specific escaping patterns.

**Objective:** Identify context-specific escaping patterns.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-06 — Recognize selected sanitization controls.

**Objective:** Recognize selected sanitization controls.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-07 — Connect source to sink where possible.

**Objective:** Connect source to sink where possible.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-08 — Distinguish reflected/stored/DOM hypotheses only when evidence supports it.

**Objective:** Distinguish reflected/stored/DOM hypotheses only when evidence supports it.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-09 — Map CWE/OWASP.

**Objective:** Map CWE/OWASP.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-10 — Generate evidence and remediation.

**Objective:** Generate evidence and remediation.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-11 — Add vulnerable tests.

**Objective:** Add vulnerable tests.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-12 — Add safe tests.

**Objective:** Add safe tests.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-13 — Document unsupported contexts and limitations.

**Objective:** Document unsupported contexts and limitations.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-14 — Integrate with reporting and correlation.

**Objective:** Integrate with reporting and correlation.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## XSS-15 — Benchmark false positives.

**Objective:** Benchmark false positives.

**Implementation plan**
1. Cross-site scripting analysis: Inspect supported language/framework syntax, source/sink APIs, existing flow and escaping helpers. Define contexts where this heuristic can and cannot make a claim.
2. Implement context-aware candidate analysis and evidence. Treat escaping/sanitization conservatively and do not conflate reflected, stored, or DOM XSS without evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-01 — Catalog external sources.

**Objective:** Catalog external sources.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-02 — Catalog command execution sinks.

**Objective:** Catalog command execution sinks.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-03 — Detect dynamic command construction.

**Objective:** Detect dynamic command construction.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-04 — Detect concatenation/interpolation.

**Objective:** Detect concatenation/interpolation.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-05 — Recognize shell execution vs direct argument APIs.

**Objective:** Recognize shell execution vs direct argument APIs.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-06 — Track data to command sinks.

**Objective:** Track data to command sinks.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-07 — Recognize structured-argument patterns where appropriate.

**Objective:** Recognize structured-argument patterns where appropriate.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-08 — Identify controls and validation conservatively.

**Objective:** Identify controls and validation conservatively.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-09 — Generate evidence and explanation.

**Objective:** Generate evidence and explanation.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-10 — Map CWE/OWASP.

**Objective:** Map CWE/OWASP.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-11 — Recommend safer APIs and argument handling.

**Objective:** Recommend safer APIs and argument handling.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-12 — Add positive and negative tests.

**Objective:** Add positive and negative tests.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-13 — Integrate reporting.

**Objective:** Integrate reporting.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-14 — Benchmark false positives.

**Objective:** Benchmark false positives.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-15 — Document supported APIs and limitations.

**Objective:** Document supported APIs and limitations.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-16 — Add framework/wrapper patterns incrementally.

**Objective:** Add framework/wrapper patterns incrementally.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CMD-17 — Validate on isolated examples.

**Objective:** Validate on isolated examples.

**Implementation plan**
1. Command injection analysis: Inspect command APIs and argument forms for supported languages. Distinguish shell-string execution from structured argument APIs and document supported patterns.
2. Trace relevant inputs into command sinks and recognize controls conservatively. Keep target repositories read-only and never execute their code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-01 — Catalog path sources.

**Objective:** Catalog path sources.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-02 — Catalog file read/write/delete sinks.

**Objective:** Catalog file read/write/delete sinks.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-03 — Detect dynamic path construction.

**Objective:** Detect dynamic path construction.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-04 — Detect traversal patterns.

**Objective:** Detect traversal patterns.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-05 — Track source-to-filesystem flow.

**Objective:** Track source-to-filesystem flow.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-06 — Recognize normalization patterns.

**Objective:** Recognize normalization patterns.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-07 — Recognize confinement/base-directory checks.

**Objective:** Recognize confinement/base-directory checks.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-08 — Evaluate controls conservatively.

**Objective:** Evaluate controls conservatively.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-09 — Generate evidence.

**Objective:** Generate evidence.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-10 — Map CWE/OWASP.

**Objective:** Map CWE/OWASP.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-11 — Generate remediation.

**Objective:** Generate remediation.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-12 — Add positive tests.

**Objective:** Add positive tests.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-13 — Add negative/safe tests.

**Objective:** Add negative/safe tests.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-14 — Integrate reports.

**Objective:** Integrate reports.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-15 — Benchmark false positives.

**Objective:** Benchmark false positives.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-16 — Document limitations.

**Objective:** Document limitations.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PATH-17 — Validate on isolated examples.

**Objective:** Validate on isolated examples.

**Implementation plan**
1. Path traversal analysis: Inspect file/path sources, filesystem sinks, path normalization and confinement patterns in supported syntax.
2. Trace untrusted path components to filesystem operations; evaluate normalization/base-directory checks conservatively and account for platform semantics.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-01 — Catalog URL/request sources.

**Objective:** Catalog URL/request sources.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-02 — Catalog HTTP/network sinks.

**Objective:** Catalog HTTP/network sinks.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-03 — Detect dynamic URL construction.

**Objective:** Detect dynamic URL construction.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-04 — Track source-to-request flow.

**Objective:** Track source-to-request flow.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-05 — Recognize destination allowlists.

**Objective:** Recognize destination allowlists.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-06 — Recognize selected URL/IP validation.

**Objective:** Recognize selected URL/IP validation.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-07 — Consider redirect handling where code evidence is available.

**Objective:** Consider redirect handling where code evidence is available.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-08 — Identify internal-network context only when supported by evidence.

**Objective:** Identify internal-network context only when supported by evidence.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-09 — Generate evidence and explanation.

**Objective:** Generate evidence and explanation.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-10 — Map CWE/OWASP.

**Objective:** Map CWE/OWASP.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-11 — Generate remediation.

**Objective:** Generate remediation.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-12 — Add positive tests.

**Objective:** Add positive tests.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-13 — Add negative tests.

**Objective:** Add negative tests.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-14 — Integrate reporting.

**Objective:** Integrate reporting.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-15 — Benchmark false positives.

**Objective:** Benchmark false positives.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-16 — Document unsupported cases.

**Objective:** Document unsupported cases.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## SSRF-17 — Validate on isolated examples.

**Objective:** Validate on isolated examples.

**Implementation plan**
1. SSRF analysis: Inspect URL/request sources, network sinks, validation/allowlist logic, redirects, and supported APIs.
2. Trace user-controlled URLs to requests. Consider redirects and internal-network context only when statically evidenced; do not invent network behavior.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-01 — Define normalized evidence contract.

**Objective:** Define normalized evidence contract.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-02 — Normalize file/line/API references.

**Objective:** Normalize file/line/API references.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-03 — Deduplicate repeated detector output.

**Objective:** Deduplicate repeated detector output.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-04 — Group related evidence.

**Objective:** Group related evidence.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-05 — Correlate source, propagation, and sink.

**Objective:** Correlate source, propagation, and sink.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-06 — Correlate evidence in same flow/function/file where justified.

**Objective:** Correlate evidence in same flow/function/file where justified.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-07 — Correlate cross-file evidence when flow engine supports it.

**Objective:** Correlate cross-file evidence when flow engine supports it.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-08 — Preserve detector-origin findings.

**Objective:** Preserve detector-origin findings.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-09 — Handle contradictory evidence.

**Objective:** Handle contradictory evidence.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-10 — Consolidate contextual findings.

**Objective:** Consolidate contextual findings.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-11 — Explain grouping decisions.

**Objective:** Explain grouping decisions.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-12 — Avoid loss of individual evidence.

**Objective:** Avoid loss of individual evidence.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-13 — Add correlation tests.

**Objective:** Add correlation tests.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## COR-14 — Integrate with reporting and risk.

**Objective:** Integrate with reporting and risk.

**Implementation plan**
1. Evidence correlation: Inspect detector evidence structures, identity/location normalization, and existing duplicate/grouping behavior. Preserve original detector provenance.
2. Implement deterministic correlation/grouping rules with explicit rationale and conflict/unknown handling; never discard raw evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-01 — Define confidence levels and semantics.

**Objective:** Define confidence levels and semantics.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-02 — Define evidence factors.

**Objective:** Define evidence factors.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-03 — Account for source certainty.

**Objective:** Account for source certainty.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-04 — Account for sink certainty.

**Objective:** Account for sink certainty.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-05 — Account for flow completeness.

**Objective:** Account for flow completeness.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-06 — Account for controls/mitigations.

**Objective:** Account for controls/mitigations.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-07 — Account for pattern ambiguity.

**Objective:** Account for pattern ambiguity.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-08 — Explain confidence rationale.

**Objective:** Explain confidence rationale.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-09 — Keep confidence independent of severity.

**Objective:** Keep confidence independent of severity.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-10 — Mark incomplete analysis.

**Objective:** Mark incomplete analysis.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-11 — Identify likely false-positive candidates.

**Objective:** Identify likely false-positive candidates.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-12 — Build safe/vulnerable corpus.

**Objective:** Build safe/vulnerable corpus.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-13 — Calibrate using benchmark results.

**Objective:** Calibrate using benchmark results.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CONF-14 — Track confidence quality across releases.

**Objective:** Track confidence quality across releases.

**Implementation plan**
1. Confidence evaluation: Inspect current confidence fields and evidence quality. Define interpretable factors and ensure confidence is distinct from severity/risk/exploitability.
2. Implement transparent factor handling and unknown/partial analysis behavior. Avoid arbitrary numeric calibration without benchmark evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-01 — Define contextual risk model.

**Objective:** Define contextual risk model.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-02 — Define explainable risk bands.

**Objective:** Define explainable risk bands.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-03 — Incorporate severity.

**Objective:** Incorporate severity.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-04 — Incorporate confidence.

**Objective:** Incorporate confidence.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-05 — Incorporate exposure/reachability where known.

**Objective:** Incorporate exposure/reachability where known.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-06 — Incorporate sensitive context and impact where evidence exists.

**Objective:** Incorporate sensitive context and impact where evidence exists.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-07 — Incorporate controls.

**Objective:** Incorporate controls.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-08 — Avoid double-counting correlated findings.

**Objective:** Avoid double-counting correlated findings.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-09 — Produce ranking.

**Objective:** Produce ranking.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-10 — Explain risk rationale.

**Objective:** Explain risk rationale.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-11 — Represent unknown context.

**Objective:** Represent unknown context.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-12 — Add model tests.

**Objective:** Add model tests.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-13 — Validate against benchmark cases.

**Objective:** Validate against benchmark cases.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-14 — Version the risk model.

**Objective:** Version the risk model.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## RISK-15 — Document assumptions and limitations.

**Objective:** Document assumptions and limitations.

**Implementation plan**
1. Contextual risk evaluation: Inspect severity/confidence/context fields and current prioritization. Define model inputs, unknown handling, bands, and versioning.
2. Implement explainable risk calculation without double-counting correlated findings; only use exposure/context supported by evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-01 — Executive summary.

**Objective:** Executive summary.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-02 — Overall quality/security overview.

**Objective:** Overall quality/security overview.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-03 — Findings by severity.

**Objective:** Findings by severity.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-04 — Findings by type.

**Objective:** Findings by type.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-05 — Prioritized findings.

**Objective:** Prioritized findings.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-06 — Confidence and risk rationale.

**Objective:** Confidence and risk rationale.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-07 — Source-to-sink trace.

**Objective:** Source-to-sink trace.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-08 — Evidence and code locations.

**Objective:** Evidence and code locations.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-09 — CWE/OWASP/ASVS metadata.

**Objective:** CWE/OWASP/ASVS metadata.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-10 — Remediation and references.

**Objective:** Remediation and references.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-11 — False-positive review guidance.

**Objective:** False-positive review guidance.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-12 — Coverage and detector status.

**Objective:** Coverage and detector status.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-13 — Unsupported files/languages.

**Objective:** Unsupported files/languages.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-14 — Excluded files and reasons.

**Objective:** Excluded files and reasons.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-15 — Agent/detector execution summary.

**Objective:** Agent/detector execution summary.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-16 — Analysis errors and partial results.

**Objective:** Analysis errors and partial results.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-17 — Repository metadata.

**Objective:** Repository metadata.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-18 — Report timestamp.

**Objective:** Report timestamp.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-19 — Report and schema version.

**Objective:** Report and schema version.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-20 — JSON schema.

**Objective:** JSON schema.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-21 — Backward compatibility strategy.

**Objective:** Backward compatibility strategy.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-22 — Stable report naming.

**Objective:** Stable report naming.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-23 — Timestamped report naming.

**Objective:** Timestamped report naming.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-24 — Validate report contract.

**Objective:** Validate report contract.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## REP-25 — Add report fixtures and tests.

**Objective:** Add report fixtures and tests.

**Implementation plan**
1. Reporting and export: Inspect report formats, CLI/report paths, schemas and compatibility requirements. Define output shape and expected presentation for this task.
2. Implement report fields/format while preserving stable naming, versioning and safe handling of paths/secrets. Ensure partial results and limitations are visible where relevant.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-01 — Define detector interface.

**Objective:** Define detector interface.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-02 — Define input context.

**Objective:** Define input context.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-03 — Define output contract.

**Objective:** Define output contract.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-04 — Implement registry.

**Objective:** Implement registry.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-05 — Implement detector configuration.

**Objective:** Implement detector configuration.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-06 — Define dependency/capability metadata.

**Objective:** Define dependency/capability metadata.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-07 — Define execution lifecycle.

**Objective:** Define execution lifecycle.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-08 — Add timeouts and resource limits.

**Objective:** Add timeouts and resource limits.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-09 — Handle detector exceptions independently.

**Objective:** Handle detector exceptions independently.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-10 — Add metrics.

**Objective:** Add metrics.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-11 — Add optional safe parallelism.

**Objective:** Add optional safe parallelism.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-12 — Add caching only where correctness is preserved.

**Objective:** Add caching only where correctness is preserved.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-13 — Version rules/detectors.

**Objective:** Version rules/detectors.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-14 — Add contract tests.

**Objective:** Add contract tests.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## DET-15 — Prevent detector implementation from bloating central analysis modules.

**Objective:** Prevent detector implementation from bloating central analysis modules.

**Implementation plan**
1. Detector framework: Inspect existing detector implementations and orchestration. Define lifecycle, configuration, capabilities, error handling and resource expectations for this capability.
2. Implement modularly without bloating central orchestrator. Isolate failures, keep target code unexecuted, and preserve consistent contracts.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-01 — Define language coverage matrix.

**Objective:** Define language coverage matrix.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-02 — Define capability matrix by language.

**Objective:** Define capability matrix by language.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-03 — Prioritize Python.

**Objective:** Prioritize Python.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-04 — Add Java support incrementally.

**Objective:** Add Java support incrementally.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-05 — Add JavaScript/TypeScript support incrementally.

**Objective:** Add JavaScript/TypeScript support incrementally.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-06 — Add Go and other languages based on demand.

**Objective:** Add Go and other languages based on demand.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-07 — Detect frameworks.

**Objective:** Detect frameworks.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-08 — Detect ORM/query APIs.

**Objective:** Detect ORM/query APIs.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-09 — Add framework-specific sources and sinks.

**Objective:** Add framework-specific sources and sinks.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-10 — Add language-specific safe patterns.

**Objective:** Add language-specific safe patterns.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-11 — Keep detector capabilities explicit.

**Objective:** Keep detector capabilities explicit.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-12 — Add per-language test corpus.

**Objective:** Add per-language test corpus.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-13 — Document coverage.

**Objective:** Document coverage.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## LANG-14 — Expand only when benchmarked.

**Objective:** Expand only when benchmarked.

**Implementation plan**
1. Language/framework support: Inspect current parser abstractions and language coverage. Define supported constructs, dependencies and capability boundaries for this profile.
2. Add incremental support using appropriate static parsing; unsupported syntax must be reported, not silently interpreted. No execution of analyzed code.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-01 — Create vulnerable sample corpus.

**Objective:** Create vulnerable sample corpus.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-02 — Create safe sample corpus.

**Objective:** Create safe sample corpus.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-03 — SQLi positive cases.

**Objective:** SQLi positive cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-04 — SQLi safe parameterization cases.

**Objective:** SQLi safe parameterization cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-05 — Source/Sink cases.

**Objective:** Source/Sink cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-06 — Sanitization/validation cases.

**Objective:** Sanitization/validation cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-07 — Variable propagation cases.

**Objective:** Variable propagation cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-08 — Multi-function cases.

**Objective:** Multi-function cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-09 — Multi-file cases as supported.

**Objective:** Multi-file cases as supported.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-10 — False-positive cases.

**Objective:** False-positive cases.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-11 — False-negative review.

**Objective:** False-negative review.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-12 — Calculate precision/recall/F1 when dataset labels support it.

**Objective:** Calculate precision/recall/F1 when dataset labels support it.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-13 — Measure coverage by detector and language.

**Objective:** Measure coverage by detector and language.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-14 — Version benchmark.

**Objective:** Version benchmark.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-15 — Add regression thresholds.

**Objective:** Add regression thresholds.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-16 — Run in CI.

**Objective:** Run in CI.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-17 — Document benchmark methodology.

**Objective:** Document benchmark methodology.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## TESTSEC-18 — Use isolated training targets such as OWASP Juice Shop, DVWA, WebGoat, NodeGoat, or crAPI where appropriate; do not execute untrusted targets outside controlled environments.

**Objective:** Use isolated training targets such as OWASP Juice Shop, DVWA, WebGoat, NodeGoat, or crAPI where appropriate; do not execute untrusted targets outside controlled environments.

**Implementation plan**
1. Security benchmark and test corpus: Inspect existing fixtures, labels, harness and benchmark methodology. Keep samples isolated and clearly categorized; never execute untrusted sample code.
2. Add reproducible cases and expected outcomes, with safe negatives and metadata. Measure only metrics supported by labels and avoid overstating coverage.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-01 — Define integration adapter contract.

**Objective:** Define integration adapter contract.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-02 — Evaluate Semgrep.

**Objective:** Evaluate Semgrep.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-03 — Evaluate CodeQL.

**Objective:** Evaluate CodeQL.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-04 — Evaluate Bandit.

**Objective:** Evaluate Bandit.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-05 — Evaluate Trivy.

**Objective:** Evaluate Trivy.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-06 — Evaluate Gitleaks.

**Objective:** Evaluate Gitleaks.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-07 — Consider ZAP only for a separate controlled dynamic-testing workflow.

**Objective:** Consider ZAP only for a separate controlled dynamic-testing workflow.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-08 — Normalize external output.

**Objective:** Normalize external output.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-09 — Deduplicate and correlate.

**Objective:** Deduplicate and correlate.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-10 — Preserve source tool and version.

**Objective:** Preserve source tool and version.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-11 — Preserve configuration and coverage.

**Objective:** Preserve configuration and coverage.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-12 — Handle missing tools.

**Objective:** Handle missing tools.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-13 — Handle tool errors and partial results.

**Objective:** Handle tool errors and partial results.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-14 — Document licensing, installation, and operational requirements.

**Objective:** Document licensing, installation, and operational requirements.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## EXT-15 — Keep MiniAgent's contextual analysis/reporting value independent of tool availability.

**Objective:** Keep MiniAgent's contextual analysis/reporting value independent of tool availability.

**Implementation plan**
1. External tool integration: Evaluate tool purpose, license, installation/runtime requirements, output schema, versioning, failure modes, and whether it can operate safely in static/read-only mode.
2. Implement optional adapter with graceful absence/failure, normalized results, source/version/configuration and coverage. Do not make core analysis depend on tool availability.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-01 — Threat model MiniAgent.

**Objective:** Threat model MiniAgent.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-02 — Guarantee analyzed code is not executed.

**Objective:** Guarantee analyzed code is not executed.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-03 — Guarantee analyzed repository is not modified.

**Objective:** Guarantee analyzed repository is not modified.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-04 — Treat file content as untrusted input.

**Objective:** Treat file content as untrusted input.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-05 — Defend against prompt/content injection if LLM components are used.

**Objective:** Defend against prompt/content injection if LLM components are used.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-06 — Enforce file-size limits.

**Objective:** Enforce file-size limits.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-07 — Enforce time and resource limits.

**Objective:** Enforce time and resource limits.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-08 — Handle symlinks safely.

**Objective:** Handle symlinks safely.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-09 — Prevent archive/path traversal if archive ingestion is added.

**Objective:** Prevent archive/path traversal if archive ingestion is added.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-10 — Protect secrets in logs.

**Objective:** Protect secrets in logs.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-11 — Isolate evidence and analysis contexts.

**Objective:** Isolate evidence and analysis contexts.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-12 — Clean temporary files.

**Objective:** Clean temporary files.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-13 — Handle concurrency safely.

**Objective:** Handle concurrency safely.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-14 — Add malicious-repository test cases.

**Objective:** Add malicious-repository test cases.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-15 — Review dependency and tool risks.

**Objective:** Review dependency and tool risks.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-16 — Document safe operating model.

**Objective:** Document safe operating model.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-17 — Test failure containment.

**Objective:** Test failure containment.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-18 — Ensure reports do not unnecessarily expose secrets.

**Objective:** Ensure reports do not unnecessarily expose secrets.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-19 — Add resource exhaustion tests.

**Objective:** Add resource exhaustion tests.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## AGSEC-20 — Establish security regression suite.

**Objective:** Establish security regression suite.

**Implementation plan**
1. MiniAgent safety hardening: Threat-model the behavior and attack surface, including hostile repository content, filesystem traversal, secrets, resource exhaustion and untrusted instructions.
2. Implement defenses and fail-safe behavior; preserve no-execution/read-only guarantees. Use isolated adversarial fixtures and avoid exposing sensitive content in logs/reports.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-01 — Build repository profile.

**Objective:** Build repository profile.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-02 — Detect language/framework/architecture.

**Objective:** Detect language/framework/architecture.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-03 — Identify sensitive components.

**Objective:** Identify sensitive components.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-04 — Select detectors based on capability and profile.

**Objective:** Select detectors based on capability and profile.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-05 — Resolve detector dependencies.

**Objective:** Resolve detector dependencies.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-06 — Avoid unnecessary work.

**Objective:** Avoid unnecessary work.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-07 — Re-plan when analysis discovers relevant context.

**Objective:** Re-plan when analysis discovers relevant context.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-08 — Track plan execution.

**Objective:** Track plan execution.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-09 — Explain selected checks.

**Objective:** Explain selected checks.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-10 — Explain skipped checks.

**Objective:** Explain skipped checks.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-11 — Explain unsupported checks.

**Objective:** Explain unsupported checks.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-12 — Record plan changes.

**Objective:** Record plan changes.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-13 — Add plan tests.

**Objective:** Add plan tests.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PLAN-14 — Validate efficiency and coverage tradeoffs.

**Objective:** Validate efficiency and coverage tradeoffs.

**Implementation plan**
1. Adaptive analysis planning: Inspect repository inventory, detector capabilities, dependency resolution and current planning/orchestration. Define selection and re-planning rules with traceability.
2. Implement capability-aware selection, dependency handling, selected/skipped/unsupported rationale, and durable plan execution status without silently omitting checks.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-01 — Track duration per agent/detector.

**Objective:** Track duration per agent/detector.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-02 — Track files scanned.

**Objective:** Track files scanned.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-03 — Track files skipped and reasons.

**Objective:** Track files skipped and reasons.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-04 — Track parse failures.

**Objective:** Track parse failures.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-05 — Track detector failures.

**Objective:** Track detector failures.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-06 — Track resource usage where available.

**Objective:** Track resource usage where available.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-07 — Track findings by category.

**Objective:** Track findings by category.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-08 — Track coverage by language/detector.

**Objective:** Track coverage by language/detector.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-09 — Track partial-analysis state.

**Objective:** Track partial-analysis state.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-10 — Track analysis history.

**Objective:** Track analysis history.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-11 — Support comparisons.

**Objective:** Support comparisons.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-12 — Expose actionable diagnostics.

**Objective:** Expose actionable diagnostics.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## OBS-13 — Avoid leaking secrets in metrics/logs.

**Objective:** Avoid leaking secrets in metrics/logs.

**Implementation plan**
1. Observability and metrics: Inspect current logs, events, timings, error handling and report diagnostics. Define metric meaning, lifecycle, privacy and cardinality boundaries.
2. Instrument the relevant stage with useful diagnostics while avoiding secrets and excessive overhead. Ensure failures/partial analysis are represented.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-01 — Automated unit tests.

**Objective:** Automated unit tests.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-02 — Automated integration tests.

**Objective:** Automated integration tests.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-03 — Lint and formatting.

**Objective:** Lint and formatting.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-04 — Import/package checks.

**Objective:** Import/package checks.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-05 — Detector contract tests.

**Objective:** Detector contract tests.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-06 — Security benchmark.

**Objective:** Security benchmark.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-07 — Regression checks.

**Objective:** Regression checks.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-08 — Report-schema validation.

**Objective:** Report-schema validation.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-09 — Artifact publication.

**Objective:** Artifact publication.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-10 — Matrix for supported Python/runtime versions.

**Objective:** Matrix for supported Python/runtime versions.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-11 — Document CI workflow.

**Objective:** Document CI workflow.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## CI-12 — Define non-flaky quality gates.

**Objective:** Define non-flaky quality gates.

**Implementation plan**
1. Continuous integration and regression gates: Inspect repository CI configuration, supported runtimes, test/lint/schema commands and existing gates. Choose reliable, deterministic checks for this task.
2. Add or update workflow jobs, caching/matrix only where justified, artifacts and clear failure behavior. Avoid flaky or overly broad gates.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-01 — Profile per-file analysis.

**Objective:** Profile per-file analysis.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-02 — Identify duplicate reads/work.

**Objective:** Identify duplicate reads/work.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-03 — Reuse repository context.

**Objective:** Reuse repository context.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-04 — Optimize parsing and analysis.

**Objective:** Optimize parsing and analysis.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-05 — Add caching with invalidation.

**Objective:** Add caching with invalidation.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-06 — Evaluate detector parallelism.

**Objective:** Evaluate detector parallelism.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-07 — Handle large repositories.

**Objective:** Handle large repositories.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-08 — Add configurable limits.

**Objective:** Add configurable limits.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-09 — Define graceful degradation.

**Objective:** Define graceful degradation.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-10 — Detect performance regressions.

**Objective:** Detect performance regressions.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-11 — Create large-repository benchmark.

**Objective:** Create large-repository benchmark.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## PERF-12 — Document tradeoffs.

**Objective:** Document tradeoffs.

**Implementation plan**
1. Performance and scalability: Inspect baseline metrics, hot paths, memory/time behavior and workload characteristics before optimization. Define a measurable target and benchmark method.
2. Optimize only after evidence; preserve correctness and resource safeguards. Include graceful degradation/limits and avoid unsafe concurrency or cache invalidation.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-01 — Executive summary.

**Objective:** Executive summary.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-02 — Sort by priority/risk.

**Objective:** Sort by priority/risk.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-03 — Filter by severity.

**Objective:** Filter by severity.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-04 — Filter by CWE/OWASP.

**Objective:** Filter by CWE/OWASP.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-05 — Filter by file/language/confidence.

**Objective:** Filter by file/language/confidence.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-06 — Inspect evidence and traces.

**Objective:** Inspect evidence and traces.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-07 — Inspect correlation rationale.

**Objective:** Inspect correlation rationale.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-08 — Compare analysis runs.

**Objective:** Compare analysis runs.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-09 — Identify new findings.

**Objective:** Identify new findings.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-10 — Identify resolved findings.

**Objective:** Identify resolved findings.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-11 — Show risk trends.

**Objective:** Show risk trends.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-12 — Export filtered findings.

**Objective:** Export filtered findings.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-13 — Improve report navigation.

**Objective:** Improve report navigation.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## UX-14 — Keep explanations actionable.

**Objective:** Keep explanations actionable.

**Implementation plan**
1. Developer-facing report experience: Inspect current CLI/report navigation, formats, user workflow and output consumers. Define the interaction and backward-compatible behavior for this task.
2. Implement filtering/navigation/export/comparison using existing conventions; make explanations actionable and preserve finding identity/evidence.
3. Inspect existing modules and interfaces first; identify exact files to change only after repository reconnaissance.
4. Implement incrementally, preserving compatibility and keeping the analyzed target repository read-only.
5. Add/update focused tests, run them, then relevant broader checks; inspect the diff and document any remaining gaps.

**Acceptance criteria**
- Task behavior matches the backlog title and product vision, with scope and unsupported cases explicit.
- Evidence, source locations, provenance, or output contract (as applicable) are preserved and explainable.
- Positive/negative or edge tests cover the behavior; test commands and outcomes are recorded accurately.
- Reviewed changes, limitations, and task status are recorded in the execution tracker.

**Risks / boundaries:** avoid unrelated refactoring; do not invent coverage or mappings; never execute target code or modify analyzed repositories.


## Plan maintenance
If a task is decomposed, keep its parent task plan here and add subtask IDs, dependencies, and individual plan sections for each new backlog task. Do not create duplicate tasks merely to document implementation steps.
