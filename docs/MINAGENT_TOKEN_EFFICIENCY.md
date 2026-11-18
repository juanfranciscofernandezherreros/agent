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


## Document generation efficiency

These rules apply when creating or regenerating project documentation, backlog plans, task plans, specifications, and checkpoints—not only when reading them.

- **Do not regenerate large documents in one pass.** Work in bounded batches (one milestone/epic or a small set of tasks) and preserve completed sections.
- **Keep task plans compact by default.** Target roughly 150–300 words per task, only longer when the task has genuinely complex design, security, data-flow, or migration concerns.
- **Use a shared reference instead of repeating boilerplate.** Safety rules, architecture principles, test policy, workflow, and generic acceptance conventions belong in the central documents. Task plans should link/reference them and contain only task-specific decisions.
- **Task-plan minimum:** ID/title; purpose and scope; dependencies; likely components/files (explicitly provisional until code inspection); implementation steps; edge cases; focused tests; acceptance criteria. Avoid lengthy background, generic advice, speculative file lists, and duplicated requirement text.
- **Generate from source, not from repeated full-context reads.** Extract the task IDs/titles and only the relevant backlog entry. Reuse already verified architecture context. Do not paste the full backlog or full plan document into the prompt/context.
- **Use a compact index.** Keep task IDs, titles, dependency/status, and links/anchors in the index; keep detailed guidance in task sections. Do not duplicate full plan content in indexes.
- **Batch safely:** create/update a small batch, validate IDs and coverage against the source backlog, then continue. Do not load or rewrite all batches just to validate one batch.
- **Avoid verbose prose output.** Produce concise Markdown, tables only when they reduce text, and no repeated introductory/concluding paragraphs per task.
- **Preserve existing detail selectively.** Do not mass-compress or delete existing plans without checking whether task-specific decisions, edge cases, or acceptance criteria would be lost. When reducing this  document, do it in batches and compare task coverage and key fields before committing.

### Compact task-plan template

```markdown
### TASK-ID — Title
- **Scope:** <specific outcome; in/out>
- **Depends on:** <IDs or none>
- **Approach:** <3–6 concrete steps, tailored to this task>
- **Tests:** <focused cases/commands>
- **Done when:** <observable acceptance criteria>
```

The template is a ceiling for routine tasks, not a constraint for complex tasks. Add detail only where it prevents implementation mistakes.
