---
name: architecture-audit
description: Perform a read-only architecture inventory and dependency analysis for frontend, backend, security, RAG, repository, or deployment concerns. Use before cross-cutting implementation, migrations, or architecture decisions that need ownership, coupling, risk, and phased recommendations. Do not use to edit code, execute a refactor, review commits, or produce a task handoff.
---

# Architecture Audit

## Purpose

Map the current architecture from repository evidence before implementation.
Explain ownership, dependencies, coupling, boundaries, and risks without editing
the repository.

## Trigger

Use for a read-only architecture audit of one or more named surfaces: frontend,
backend/domain logic, security, RAG, repository structure, or deployment.

## Do not trigger

Do not use for ordinary file discovery, implementation, refactor execution,
documentation synchronization, commit review, or handoff generation.

## Inputs

- Audit question, included surfaces, and explicit exclusions.
- Repository instructions, branch state, and relevant source and tests.
- Known runtime evidence, documentation, and prior audits.
- Constraints for compatibility, behavior, security, and deployment.

## Workflow

1. Establish the audit boundary and remain read-only.
2. Inventory relevant entry points, modules, configuration, tests, assets, and
   operational files.
3. Trace imports, calls, data flow, shared state, provider edges, persistence,
   and deployment dependencies relevant to the question.
4. Assign each responsibility to its current owner and distinguish intended
   boundaries from observed coupling.
5. Record behavior and architecture facts with file evidence; label inference
   and unknowns explicitly.
6. Identify concentration points, cycles, hidden state, unsafe trust boundaries,
   test gaps, and migration constraints.
7. Recommend ordered, behavior-preserving phases with prerequisites, validation,
   risks, and rollback points. Do not implement them.

## Outputs

Return the inventory, dependency map, ownership map, coupling analysis, risks,
and phased recommendations using
[the architecture audit format](references/architecture-audit-format.md).

## Safety

- Do not modify, stage, commit, run migrations, install dependencies, or call
  paid providers.
- Do not inspect or print credential values.
- Do not claim runtime behavior from static inspection alone.
- Do not present a proposed future architecture as current.
- Keep recommendations within the audited surface and explicit non-goals.

## Validation

- Cross-check important dependencies in both directions where practical.
- Verify cited paths and separate code evidence, test evidence, documentation,
  runtime evidence, and inference.
- Check that every proposed phase protects named behavior and has validation and
  rollback criteria.
- Report excluded or inaccessible surfaces as unverified.

## References

- [`AGENTS.md`](../../../AGENTS.md) — repository boundaries and safety rules.
- [`docs/agents/README.md`](../../../docs/agents/README.md) — tooling ownership.
- [Architecture audit format](references/architecture-audit-format.md) — output
  structure and surface checklist.
