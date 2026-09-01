# Agentic PR Workflow

Use this workflow for medium or larger Cognivia changes that will go through branch review before merge. It keeps AI-assisted work transparent, scoped, and reviewable without shifting ownership away from the project owner.

> **Authority:** [AGENTS.md](../AGENTS.md) is the source of truth for durable
> repository-wide rules. This guide provides temporary procedural guidance
> during the agent-tooling migration. Where instructions differ, follow
> `AGENTS.md`. Future canonical skills will replace the relevant procedures.

## Principles

- Keep scope small and explicit.
- Prefer simple, readable code and existing project patterns.
- Separate planning, implementation, audit, and PR writing.
- Treat AI output as draft work that still needs owner review.
- Use Learning & Defense Notes when the task or audience requires them.
- Apply the provider-safety rules in `AGENTS.md` before expensive agentic work
  or external model/API usage.

## Roles

### 1. Pre-implementation Agent / Architecture Planning Agent

**Purpose**

Use before medium or large coding changes. Planning only unless the user explicitly authorizes edits.

**Rules**

- Clarify the smallest useful scope.
- List expected files or modules to touch.
- List files that must not be touched.
- Propose the simplest architecture and data flow that fits the task.
- Call out relevant Python, JavaScript, and general architecture trade-offs.
- Recommend when to use functions, dataclasses, `TypedDict`, classes, or plain modules.
- Check separation of concerns across UI, business logic, RAG, memory, evaluation, and persistence.
- Propose tests before implementation.
- Identify risks, edge cases, and rollback strategy.
- End with an implementation-ready plan.

**Output**

- Goal
- Minimal scope
- Non-goals
- Expected files
- Architecture/data flow
- Python/JS/architecture trade-offs
- Testing plan
- Risks/edge cases
- Recommended implementation prompt summary

### 2. Implementation Agent

**Purpose**

Write or modify code inside an approved scope.

**Rules**

- Apply the current coding, scope, and architecture rules in `AGENTS.md`.
- Keep changes minimal, local, and easy to review.
- Do not touch frontend visual polish unless explicitly requested.
- Add Learning & Defense Notes:
  - what changed;
  - why the approach was chosen;
  - what trade-off was accepted;
  - what remains out of scope.
- Include a Code Review Gate self-review before claiming readiness:
  - intended files only;
  - no unnecessary abstraction;
  - separation of concerns preserved;
  - tests updated where behavior changed;
  - validation run and reported honestly.
- Run validation appropriate to the change before handoff.

**Output**

- Implementation summary
- Learning & Defense Notes
- Validation results
- Code Review Gate result
- Remaining limitations or follow-up items

### 3. Pre-push Audit Agent / PR Preflight Agent

**Purpose**

Use before pushing a feature branch or opening or updating a PR.

**Rules**

- Review only. Do not edit unless explicitly asked.
- Treat the current branch and diff as a pre-PR audit.
- Select validation from the ladder in `AGENTS.md` according to scope. When the
  following checks apply, run or verify:
  - focused tests for the changed behavior;
  - the isolated full-suite command in `AGENTS.md` when broad validation is
    required;
  - `python -m ruff check .`
  - `git diff --check`
  - `git status --short`
- Check intended files only.
- Check the approved frontend scope and protected product boundaries.
- Check for secrets, API keys, or private files.
- Check scope, architecture, separation of concerns, tests, regressions, edge
  cases, and any explicitly required reviewer or demo readiness.
- Report findings as:
  - P1: must fix before push, PR, merge, or task closeout
  - P2: must fix before push, PR, merge, or task closeout
  - P3: defer or optional

**Output**

- Files reviewed
- Validation status
- P1/P2/P3 findings
- Final readiness verdict, which does not authorize a push or PR action:
  - Ready for an owner-authorized push/open PR
  - Safe after fixes
  - Not ready to push

### 4. PR Writer Agent

**Purpose**

Draft the PR description after implementation and the mini audit are complete.

**Inputs**

- `git diff --stat`
- validation results
- Pre-push Audit summary
- Learning & Defense Notes
- relevant implementation summary

The PR Writer should treat the Pre-push Audit as the final quality filter. If the
audit says "Safe after fixes" or "Not ready to push," the PR should not be
framed as ready.

**Output**

- PR title
- Summary
- What changed
- Why it changed
- How it was tested
- Validation results
- AI assistance disclosure
- Risks/limitations
- Task-specific reviewer or demo explanation, when relevant
- Reviewer checklist
- Follow-up items

**AI assistance disclosure**

Use this wording in the PR description:

> AI-assisted implementation:  
> This PR was developed with support from Codex/Claude Code. The project owner reviewed the diff, validation results, and final behavior before merge.

Optional commit trailer:

```text
AI-assisted-by: Codex
Reviewed-by: Tonio Serna
```

Do not use `Co-authored-by` unless explicitly requested.

### 5. Fix PR Review Comments Agent

**Purpose**

Handle requested PR changes without reopening unrelated design work.

**Rules**

- Address only the requested review comments.
- Keep the same branch.
- Do not refactor unrelated code.
- Apply the current coding, scope, and architecture rules in `AGENTS.md` for any
  code changes.
- Add or update tests if the requested change affects behavior.
- Run validation again.
- Report exactly what changed and whether the PR is ready for re-review.

**Output**

- Review comments addressed
- Files changed
- Tests and validation rerun
- Remaining reviewer concerns
- Ready for re-review: Yes/No

## Practical Branch and PR Flow

1. Start clean:

   ```bash
   git status --short
   git branch --show-current
   ```

2. With explicit authorization, create a branch:

   ```bash
   git switch -c feature/<name>
   ```

3. Run the Pre-implementation Agent for medium or large changes.
4. Implement with the Implementation Agent.
5. Validate using the scope-dependent ladder in `AGENTS.md`. Applicable examples
   include:

   ```bash
   python -m ruff check .
   git diff --check
   ```

   Run the focused test command selected for the task. When broad validation is
   required, use the isolated full-suite command in `AGENTS.md`.

6. Run the Pre-push Audit Agent.
7. After explicit commit authorization, stage only approved files and commit:

   ```bash
   git add -- <approved-files>
   git commit -m "..."
   ```

8. After separate explicit push authorization, push:

   ```bash
   git push -u origin feature/<name>
   ```

9. Use the PR Writer Agent to draft the PR title and body from:
    - `git diff --stat`
    - validation results
    - Pre-push Audit summary
    - Learning & Defense Notes
10. Open the PR with that draft only with explicit authorization for the
    network action.
11. Review, request changes if needed, and use the Fix PR Review Comments Agent for follow-up.
12. Merge only with explicit merge authorization after the audit is clean,
    owner review is complete, and the PR is actually safe.

Readiness, a clean audit, or a listed command never supplies authorization for
a Git or network action.

## Suggested Prompt Order

1. Planning prompt for medium or large changes.
2. Implementation prompt with approved scope and the shared rules in
   `AGENTS.md`.
3. Pre-push audit prompt in review-only mode.
4. PR writing prompt using the audit and validation outputs.
5. Fix-comments prompt only when the owner requests PR changes.

## Historical example: Guided Intake Branch

This example records an earlier branch workflow. It is not current repository
policy and does not authorize branch, commit, push, PR, or merge actions.

For future guided-intake work, use the full flow:

1. Pre-implementation Agent
2. Implementation Agent
3. Pre-push Audit Agent
4. PR Writer Agent
5. Open the PR

For the already implemented `feature/guided-intake` branch, start with the current diff:

1. Run the Pre-push Audit Agent first.
2. If the verdict is clean, use the PR Writer Agent to draft the PR title and body.
3. Open or update the PR with that draft.

This keeps guided-intake follow-up work, memory, explanation evaluator, analytics, and evidence-trace changes reviewable without turning every task into a redesign exercise.
