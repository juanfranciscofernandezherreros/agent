# Token-efficient implementation strategy for Claude Code

## Goal
Implement MiniAgent backlog tasks with the lowest practical token/context cost **without reducing correctness, security, or verification**. Token savings must come from targeted context, concise outputs, and avoiding repeated work—not skipping tests or guessing.

## Rules for every task
1. **Start narrow:** read the task entry, its mapped SDD sections/FRs, the relevant execution-plan dependency/status, and only the source/tests directly related to the task. Do not reread all project docs or the entire backlog for every task.
2. **Targeted inspection:** use symbol search, file paths, line ranges, and focused test discovery first. Read whole files only when small or when the change requires full context. Expand search only when the initial evidence is insufficient.
3. **No redundant exploration:** reuse verified findings from the current task. Do not re-run tree listings, searches, or reread unchanged files without a concrete reason.
4. **Quiet tool output:** use commands that return concise summaries (e.g., test summary, filtered grep, diff stat); avoid dumping full logs, lockfiles, generated files, or entire test suites into context. Capture detailed output only when diagnosing a failure.
5. **Plan once, execute:** produce a short internal plan with files/symbols, approach, acceptance checks, and risks. Revise only if evidence changes the plan. Avoid lengthy speculative design prose.
6. **Small diffs:** implement the smallest cohesive change. Avoid unrelated refactors, formatting churn, and duplicate abstractions. Reuse existing patterns/contracts.
7. **Validate proportionally:** run the most targeted test first, then broader tests only if risk, dependencies, or task acceptance requires it. Never skip required checks merely to save tokens. Summarize exact commands and outcomes; include failure excerpts, not entire logs.
8. **Batch safely:** combine independent read-only searches or file inspections in one tool call. Parallelize independent tasks only when dependencies and shared-file conflicts are checked. Do not parallelize edits to the same file.
9. **Context hygiene:** after finishing a task, write a compact durable checkpoint (task ID, changed files, tests/outcomes, next task, unresolved issue) to the execution tracker. If the next task is unrelated and context is bloated, start a fresh Claude Code session using `/clear`; use `/compact` only to continue the same task with a brief task-specific summary.
10. **Model/effort selection:** use the lowest-cost model/effort that reliably fits. Routine, well-scoped edits and tests use a fast/efficient model; complex architecture, difficult debugging, cross-cutting security reasoning, or ambiguous tradeoffs warrant a stronger model/effort. Escalate only when evidence indicates the cheaper setting is struggling.
11. **Subagents:** use only when parallel investigation is genuinely independent and the subagent can return a short actionable summary; do not spawn agents for simple tasks or if their findings would require loading all details into the main context.
12. **Output discipline:** user-facing progress and completion notes should be concise: task, change, validation, outcome, next task. Do not narrate routine tool calls or print long plans/logs.

## Token-saving must never compromise
- SDD conformance, task acceptance criteria, security review, tests, evidence, or accurate status.
- Safety boundaries: never execute or modify repositories being analyzed.
- Do not claim tests or benchmark results that were not run.
- Do not omit important code context merely to meet an arbitrary token budget; broaden inspection when correctness requires it.

## Task completion checkpoint template
```text
Task: <ID> — <short title>
Status: DONE | BLOCKED | TODO
Changed: <paths>
Validation: <commands and concise actual outcomes>
Review: <scope/security/compatibility checked>
Next: <next eligible task>
```

## Context reset rule
When switching to an unrelated task, prefer a fresh session and re-read only the mandatory compact instructions plus that task's plan, SDD mapping, and targeted code. If continuing the same task, compact with a summary that preserves decisions, paths, test outcomes, and next action.
