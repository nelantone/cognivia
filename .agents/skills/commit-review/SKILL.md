---
name: commit-review
description: Review working-tree and staged scope, validation evidence, sensitive files, unrelated changes, commit grouping, and readiness before an authorized commit. Use when the user asks for commit preparation, staged-diff review, commit splitting, or messages. Do not use to implement fixes or automatically stage, commit, amend, push, merge, reset, rebase, squash, or clean.
---

# Commit Review

## Purpose

Decide whether the current change is ready for one or more reviewable commits
and present an exact, non-mutating commit plan.

## Trigger

Use when commit readiness, staged scope, file grouping, exact staging paths, or
commit messages are requested.

## Do not trigger

Do not use as a general code-review substitute, implementation workflow, or
authorization to mutate Git state. Do not invoke automatically at ordinary task
completion unless commit preparation was requested.

## Inputs

- User-approved task scope and intended commit boundaries.
- Current branch, status, staged diff, and unstaged diff.
- Validation results and required manual checks.
- Known sensitive, generated, protected, or unrelated paths.

## Workflow

1. Inspect the branch, complete status, staged diff, unstaged diff, and relevant
   base-branch scope.
2. Group files or hunks by coherent purpose and identify unrelated content.
3. Check for sensitive files and likely secret locations without printing
   values.
4. Compare claimed validation with commands actually run and report gaps.
5. Classify P1/P2 blockers and P3 optional findings consistently with
   `AGENTS.md`.
6. Check the staged diff with `git diff --cached --check`; if nothing is staged,
   say so and keep the review read-only.
7. Recommend exact `git add -- <paths>` commands, commit order, and imperative
   messages only after the split is clear.
8. State readiness and request explicit authorization before any commit action.

## Outputs

Return the assessment using
[the commit review format](references/commit-review-format.md), including files
that must remain uncommitted.

## Safety

- Never stage, commit, amend, push, merge, reset, restore, discard, rebase,
  squash, clean, delete, or drop stashes through this skill.
- Never use or recommend `git add .` or `git add ..`.
- Never print secret values or claim a check passed without evidence.
- Treat readiness as a review result, not authorization.
- Re-plan if approved files, ordering, or messages change.

## Validation

- Verify the proposed groups against both staged and unstaged state.
- Require `git diff --cached --check` and a complete staged review before an
  authorized commit.
- Report unrun, failed, or inapplicable checks separately.
- Confirm that the plan contains only intended files and one purpose per commit.

## References

- [`AGENTS.md`](../../../AGENTS.md) — authoritative Git and validation rules.
- [`docs/agents/README.md`](../../../docs/agents/README.md) — tooling ownership.
- [Commit review format](references/commit-review-format.md) — required output.
