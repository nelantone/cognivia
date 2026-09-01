---
name: safe-refactor
description: Plan and execute one small behavior-preserving refactor phase with local dependency mapping, compatibility, rollback, validation, and commit boundaries. Use for approved extractions, module splits, dependency untangling, or test migration. Do not use to generate a broad architecture inventory, redesign UX or behavior, add features, update docs only, or create commits.
---

# Safe Refactor

## Purpose

Move one coherent responsibility while preserving observable behavior and
keeping rollback straightforward.

## Trigger

Use after the refactor scope and behavior contract are approved. Use an existing
architecture audit when the change crosses boundaries or the dependency map is
not already known.

## Do not trigger

Do not use to discover the whole architecture, redesign product behavior, make
visual changes, implement unrelated cleanup, or prepare commits. Use
`architecture-audit` first when a broad inventory is still required.

## Inputs

- Approved objective, phase, file scope, and non-goals.
- Current behavior contract and compatibility constraints.
- Relevant architecture/dependency evidence.
- Characterization or regression tests and required manual checks.
- Validation ladder and rollback point.

## Workflow

1. Confirm branch state, approved scope, protected areas, and current behavior.
2. Map only the dependencies touched by this phase; do not expand into a new
   architecture audit.
3. Capture invariants, including Streamlit rerun, callback, widget identity, and
   session-state semantics when applicable.
4. Define one extraction boundary and its temporary compatibility mechanism.
5. Move the smallest coherent responsibility without UX, schema, provider,
   persistence, or domain changes outside the approved task.
6. Move or add tests with the behavior they protect; retain characterization
   coverage until the new boundary is proven.
7. Run the scope-appropriate validation ladder and inspect the complete diff.
8. Report rollback instructions and logical commit boundaries. Do not stage or
   commit without separate authorization.

## Outputs

Return the implemented phase, preserved behavior, compatibility path, tests,
validation evidence, risks, rollback point, and commit boundary. Use
[the refactor phase checklist](references/refactor-phase-checklist.md) for
multi-step work.

## Safety

- Preserve behavior unless the approved task explicitly changes it.
- Do not combine architecture movement with UX changes or speculative cleanup.
- Do not let parallel agents edit the same working tree.
- Do not hide failures or alter unrelated code to make validation pass.
- Do not claim browser behavior from unit tests or Streamlit AppTests alone.
- Do not stage, commit, push, reset, discard, or delete compatibility paths
  without explicit authorization.

## Validation

- Follow the task-specific ladder in `AGENTS.md`, starting with focused tests.
- Verify compatibility before removing an old import, path, or test boundary.
- Keep automated, manual, browser, and provider evidence distinct.
- Stop the phase when required validation fails and report the blocker.
- Review staged scope later with `commit-review` when requested.

## References

- [`AGENTS.md`](../../../AGENTS.md) — behavior, Git, and validation rules.
- [`architecture-audit`](../architecture-audit/SKILL.md) — broad inventory that
  must precede this skill when dependencies are not known.
- [Refactor phase checklist](references/refactor-phase-checklist.md) — phase
  contract and rollback format.
