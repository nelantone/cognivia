---
name: task-brief
description: Turn an implementation, debugging, audit, or migration request into a precise scope, objective, constraint, file, validation, and reporting brief before work begins. Use for multi-file, ambiguous, architectural, or staged work and explicit requests for a task brief. Do not use for architecture inventory, refactor execution, commit review, session handoffs, or trivial requests with complete acceptance criteria.
---

# Task Brief

## Purpose

Produce an implementation-ready contract without solving or implementing the
task. Separate verified repository facts from assumptions and decisions.

## Trigger

Use when a request needs scope clarification, acceptance criteria, protected
areas, phased work, or a validation contract before implementation.

## Do not trigger

Do not use for a full architecture inventory, behavior-preserving extraction,
documentation editing, commit preparation, or handoff generation. Route those
responsibilities to their dedicated skills.

## Inputs

- User objective and acceptance criteria.
- Current branch, working-tree state, and relevant repository instructions.
- Known implementation evidence and unresolved assumptions.
- Allowed and protected product areas, files, dependencies, and provider use.
- Required final report or artifact format.

## Workflow

1. Inspect only enough repository context to define the task accurately.
2. Record observed facts separately from assumptions and open decisions.
3. State one concrete objective and measurable acceptance criteria.
4. Mark affected areas and explicitly unchanged areas: frontend, backend,
   prompts, graph, RAG, memory, persistence, providers, tests, dependencies,
   configuration, and deployment.
5. List expected files, protected files, constraints, and non-goals.
6. Identify validation appropriate to the proposed scope using `AGENTS.md`.
7. Define the required final report, approval boundary, risks, and rollback
   point.
8. Stop with the brief; do not implement it.

## Outputs

Return a concise brief using
[the task brief format](references/task-brief-format.md). Call out any missing
decision that genuinely blocks safe implementation.

## Safety

- Remain read-only unless the user separately authorizes writing the brief to a
  named path.
- Do not infer permission for product edits, provider calls, dependencies, Git
  mutations, or broader cleanup.
- Do not turn an uncertain dependency assumption into an architecture finding.
- Do not include secrets or credential values.

## Validation

- Verify named existing paths before presenting them as current.
- Label planned paths and commands as planned.
- Check that acceptance criteria cover the objective and that non-goals prevent
  scope drift.
- Confirm that the validation plan and final report match the requested scope.

## References

- [`AGENTS.md`](../../../AGENTS.md) — durable repository rules and validation.
- [`docs/agents/README.md`](../../../docs/agents/README.md) — tooling ownership.
- [Task brief format](references/task-brief-format.md) — output structure.
