---
name: cxp
description: Project-owned Codex Prompt orchestration workflow for generating or executing a structured repository task. Use only when the user explicitly invokes `$cxp`, writes `CXP`, or asks for the Cognivia CXP workflow; never select it implicitly.
---

# CXP — Codex Prompt

## Purpose

Generate or carry out a concise, repository-aware Codex prompt while preserving
the CXP-specific scope, quality, validation, commit-readiness, and handoff
contract. CXP orchestrates canonical skills; it does not own or duplicate their
reusable procedures.

## Trigger

Use only when the user explicitly invokes `$cxp`, writes `CXP`, or asks for the
Cognivia Codex Prompt workflow.

## Do not trigger

Do not select CXP implicitly for ordinary implementation, audit, refactor,
documentation, commit-review, or handoff requests. Use the matching canonical
responsibility skill directly.

## Inputs

- The requested outcome and whether CXP should generate a prompt, execute it,
  or do both.
- Current repository instructions, Git state, authorization boundary, and
  unrelated work that must be preserved.
- Scope, non-goals, affected boundaries, sensitive files, acceptance criteria,
  and focused validation.
- Required browser, manual, provider, persistence, or deployment evidence.

## Prompt contract

Every generated CXP prompt must begin with these five lines, in this order,
with values filled in for the task:

```text
ChatGPT/Codex:
recommended:
minimum:
reasoning recommended:
reasoning minimum:
```

After the header, include the objective, repository and branch, scope, protected
areas, constraints, non-goals, expected files, acceptance criteria, validation,
Git authorization, reporting contract, and exact next action. Keep the prompt
focused enough to execute without turning a narrow request into a broad audit.
If the user asked only for prompt generation, stop after producing the prompt;
do not infer authorization to execute it.

## Routing

- Use [`task-brief`](../task-brief/SKILL.md) for request normalization, scope,
  constraints, non-goals, acceptance criteria, and validation contracts.
- Use [`architecture-audit`](../architecture-audit/SKILL.md) for read-only
  repository inventory, dependencies, ownership, coupling, risks, and phases.
- Use [`safe-refactor`](../safe-refactor/SKILL.md) for one approved
  behavior-preserving refactor phase.
- Use [`docs-update`](../docs-update/SKILL.md) for evidence-backed maintained
  documentation changes.
- Use [`commit-review`](../commit-review/SKILL.md) for non-mutating staged scope,
  commit grouping, messages, and readiness.
- Use [`session-handoff`](../session-handoff/SKILL.md) for factual continuity.
- Apply only the skills required by the explicit request, in the order the work
  requires. The six canonical skills remain the responsibility owners.

## Workflow

1. Read repository instructions and task-local guidance. For expensive or
   agentic work, apply the repository provider guard before proceeding.
2. Inspect the branch, staged, unstaged, and untracked state plus relevant
   diffs. Preserve unrelated work and identify sensitive paths without printing
   secret values.
3. State the requested behavior, affected and unchanged boundaries, non-goals,
   expected files, risks, rollback point, and focused validation. Treat an
   uncertain cause as a hypothesis until repository or runtime evidence proves
   it.
4. Generate the structured CXP prompt when requested, using the exact header
   above. Execute it only when the user also authorized implementation.
5. Route each responsibility to its canonical skill. Make the smallest safe
   change and preserve behavior outside the approved scope.
6. Apply CQM throughout: pragmatic clean code, short focused functions, clear
   UI/business-logic/RAG boundaries, focused tests, clear names, type hints
   where useful, explicit errors, and no unnecessary duplication.
7. Validate according to the changed surface. Keep automated unit evidence,
   Streamlit AppTest evidence, real-browser evidence, manual checks, provider
   evidence, and documentation evidence distinct. Never claim that AppTest
   proves visual paint, DOM timing, or browser-only behavior.
8. Explain the changes, inspect the complete relevant diff, and perform an
   honest final self-review. Report failures, skipped checks, unrelated changes,
   and unresolved assumptions without inflating completeness.
9. Assess commit readiness without staging or committing automatically. State
   blockers, remaining manual checks, coherent commit boundaries, exact paths,
   sensitive files, and proposed messages when requested.
10. Create or overwrite `.cxp/CXP_HANDOFF.md`, then return the concise terminal
    summary defined below.

## Outputs

For prompt-generation requests, return the structured CXP prompt with the exact
five-line header.

For executed or assessed work, create `.cxp/CXP_HANDOFF.md` even when the task
is incomplete, blocked, or has failed validation. Treat explicit CXP invocation
as authorization for this ignored compatibility artifact only. Do not create
dated or task-specific CXP handoffs.

Keep the handoff concise and factual. Include:

- request, date, and complete/incomplete/blocked status;
- behavior and code changes;
- architecture impact and technical debt;
- files, areas, and sensitivity;
- affected and unchanged boundaries;
- sensitive-backend and risk review;
- tests, compilation, lint, diff, browser/manual, and skipped checks;
- commit readiness, blockers, split, exact paths, and proposed messages;
- staged, unstaged, untracked, and committed Git state;
- self-review result, unresolved assumptions, and one exact next action.

The final terminal response must be concise and include:

```text
Status: complete / incomplete / blocked
Ready to commit: yes / no
Handoff: .cxp/CXP_HANDOFF.md
```

On macOS, optionally show this command for the user to run. Never execute it
automatically:

```bash
pbcopy < .cxp/CXP_HANDOFF.md
```

## Safety

- Follow `AGENTS.md` and every selected canonical skill.
- CXP grants no provider, dependency, product-edit, staging, commit, merge,
  push, deletion, or history-rewrite authority beyond the user's request.
- Never reset, restore, revert, stash, discard, or delete existing work without
  exact authorization.
- Never include secrets, credential values, private URLs, full provider
  responses, command transcripts, large logs, or full diffs in the handoff.
- Do not mask failures with cosmetic workarounds, delays, reloads, hidden
  overflow, broad exception handling, or silent continuation.

## Validation

- Use the validation ladder in `AGENTS.md` and the selected canonical skill.
- Require focused deterministic tests for changed behavior where applicable.
- Distinguish checks actually run from recommended, unavailable, or skipped
  checks.
- Give full completeness only when the cause or objective is verified, relevant
  checks pass, required browser/manual work is complete, sensitive changes are
  explained, and no known blocker remains.
- Lower the self-review result when evidence is partial; never convert an
  inferred cause, unrun check, or unavailable browser into a passing claim.
- Verify the handoff records current Git state, actual evidence, known issues,
  and one exact next action.

## References

- [`AGENTS.md`](../../../AGENTS.md) — authoritative repository rules.
- [`docs/agents/README.md`](../../../docs/agents/README.md) — tooling ownership
  and supported workflow model.
- [`docs/agents/SKILL_MIGRATION.md`](../../../docs/agents/SKILL_MIGRATION.md) —
  CXP ownership and recovery record.
