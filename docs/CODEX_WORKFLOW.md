# Codex Workflow Guide

> **Authority:** [AGENTS.md](../AGENTS.md) is the source of truth for durable
> repository-wide rules. This guide provides temporary procedural guidance
> during the agent-tooling migration. Where instructions differ, follow
> `AGENTS.md`. Future canonical skills will replace the relevant procedures.

Use this file for detailed operating procedures, reading only the sections
relevant to the current task.

## Operating Modes

### Mentor Mode

- Use for learning, unclear bugs, architecture, strategy, planning, and trade-offs.
- Inspect files, tests, errors, and Git state.
- Explain facts, assumptions, root cause, key concept, and the smallest likely solution.
- Ask exactly one useful reasoning question before the final recommendation.
- Wait for explicit approval before editing.

### Implementation Mode

- Use when the solution, scope, and acceptance criteria are already approved.
- Keep edits scoped to the requested behavior.
- Add or update focused tests before or with the fix.
- Prefer existing project patterns over new abstractions.
- Preserve existing uncommitted work.
- Do not reopen architecture or add optional improvements.

### Review Mode

- Inspect existing changes without editing.
- Lead with blocking P1/P2 findings ordered by severity.
- Include file and line references.
- Focus on bugs, regressions, missing tests, security risks, and user-visible behavior.
- Classify P3 and optional improvements as deferred.
- Stop when no blocking P1/P2 issue remains.

## Default Workflow

1. Inspect relevant files and run `git status --short`.
2. Explain the current problem, root cause, smallest solution, affected files, and test strategy.
3. Ask focused questions only when a real decision is needed.
4. Let the user reason through meaningful choices.
5. Present a concise implementation plan.
6. Wait for approval unless implementation was already explicitly approved.
7. Implement the smallest safe change.
8. Run focused tests and linting.
9. Review the diff for regressions and unrelated edits.
10. Explain what changed, limitations, validation results, and commit boundaries.

## Bug Workflow

1. Reproduce or clearly describe the incorrect behavior.
2. Trace input to output.
3. Identify the root cause, not only the failing line.
4. Define the behavioral contract and invariants.
5. Decide whether the example represents a broader class of inputs.
6. Create happy-path, edge-case, and regression examples.
7. Add a regression test before or with the fix.
8. Implement the smallest category-level fix.

## Review-Finding Workflow

- Do not patch only the reported example.
- Identify the broader failure category.
- Identify the missing invariant.
- Propose a regression-test matrix.
- Distinguish must-fix issues from optional improvements.
- Validate again after the fix.

## Scope control and review closure

### 1. Scope Boundary

Before implementation, define:

- intended behavior;
- files expected to change;
- tests required;
- explicit non-goals.

Do not expand beyond these boundaries unless the user approves it.

### 2. Review Finding Classification

Classify each review finding before acting on it.

Blocking findings:

- P1 or P2 introduced by the current diff;
- correctness regression;
- security issue;
- data loss;
- broken required behavior;
- failing required tests.

Deferred findings:

- pre-existing issue;
- unrelated issue;
- architectural improvement;
- performance optimization not required now;
- additional feature;
- nice-to-have or P3 observation.

Fix blocking findings now. Do not implement deferred findings during the current
task. Record them briefly as future improvements when useful.

### 3. Minimal-Fix Rule

For a blocking finding:

1. Identify the missing invariant.
2. Add the smallest focused regression test.
3. Implement the smallest safe fix.
4. Avoid unrelated refactoring.
5. Rerun validation.
6. Stop when the reported failure category is resolved.

Do not redesign surrounding architecture unless a local safe fix is genuinely
impossible. Ask for explicit approval before doing so.

### 4. Review-Loop Limit

Use at most two review-fix cycles for one implementation task.

After the second cycle:

- if no P1/P2 issue remains, close the task;
- if only P3 or optional improvements remain, defer them;
- if a new blocking issue remains, explain it and ask the user whether to continue.

Do not continue indefinitely because additional improvements are possible.

### 5. Closure Rule

A task is ready to close when:

- acceptance criteria are met;
- the tests, linting, diff checks, and other validation required for the task's
  scope by `AGENTS.md` pass;
- any required manual smoke test passes;
- no P1/P2 issue remains in the final review.

At that point:

- stop editing;
- report remaining limitations;
- suggest commit boundaries;
- recommend committing.

Do not search for additional improvements after the task satisfies its
Definition of Done.

### 6. Retrospective Rule

When repeated findings reveal a process weakness:

- briefly identify what rule or test could have prevented it;
- propose one future workflow improvement;
- do not change architecture or instruction files automatically;
- do not delay the current delivery unless the issue is blocking.

## Feature Workflow

- Define the user need.
- Define acceptance criteria.
- Define scope and non-goals.
- Check architecture fit.
- Identify tests and limitations.
- Avoid implementing speculative future requirements.

## Refactoring Workflow

- Identify the current pain.
- Define behavior that must remain unchanged.
- Make the smallest useful extraction.
- Protect behavior with tests.
- Avoid abstraction without a current use case.

## Validation Workflow

After meaningful changes:

1. Run focused tests.
2. Run Ruff on changed Python files.
3. Run `git diff --check`.
4. Review the diff yourself.
5. Report limitations.

Before recommending a commit, select the checks required by the validation
ladder in `AGENTS.md` for the task's actual scope:

1. Run the isolated full suite from `AGENTS.md` when the scope requires it.
2. Run `python -m ruff check .` when repository-wide lint is required.
3. Run `git diff --check`.
4. Perform a final self-review.
5. Ask for or recommend independent `/review`.
6. Manually smoke test when user-facing behavior changed.

Do not proceed past a failed required check. Report the failure and keep the
task or commit recommendation blocked until it is resolved or the user changes
the approved scope.

## Definition of Done

A task is complete only when:

- expected behavior is defined;
- the tests, linting, diff checks, and other validation required for the task's
  scope by `AGENTS.md` pass;
- no unrelated changes were introduced;
- user-facing behavior is manually tested when relevant;
- limitations are reported honestly;
- documentation does not claim unverified features.

## Retrospective Rule

When the same problem occurs twice, or a significant P1/P2 review issue appears:

- explain why the existing process did not prevent it;
- propose an improvement to instructions, tests, or architecture;
- do not modify instruction files automatically without approval.

## Reusable Short Prompts

### Mentor Mode Template

Use Mentor mode.

Do not edit yet.

Inspect the problem, explain the root cause briefly, and ask me exactly one useful reasoning question.

Let me answer before recommending the solution.

Then propose the smallest implementation plan and wait for approval.

### Implementation Mode Template

Use Implementation mode.

The solution, scope, and acceptance criteria are already approved.

Implement the smallest focused change, add or update regression tests, validate it, review the diff, and stop.

Do not introduce unrelated refactors or optional improvements.

Do not stage or commit.

### Review Mode Template

Use Review mode.

Inspect all current uncommitted changes.

Do not edit.

Report only:

1. blocking P1/P2 findings;
2. deferred P3 or optional improvements;
3. validation gaps;
4. whether the task is ready to close.

Do not search for additional improvements after the Definition of Done is satisfied.

### Bug Investigation

Investigate this bug without editing first. Reproduce or describe the incorrect
behavior, trace input to output, identify the missing invariant, propose
regression tests, and recommend the smallest fix.

### Code Review

Review this change. Lead with findings by severity, include file and line
references, identify missing tests or regressions, and keep summaries brief.

### Final Validation

Run focused tests, full tests if appropriate, Ruff, `git diff --check`, and
`git status --short`. Review the diff for unrelated changes and report remaining
limitations plus logical commit boundaries.
