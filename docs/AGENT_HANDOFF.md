# Agent Handoff Guide

> **Authority:** [AGENTS.md](../AGENTS.md) is the source of truth for durable
> repository-wide rules. This guide provides temporary procedural guidance
> during the agent-tooling migration. Where instructions differ, follow
> `AGENTS.md`. The future `session-handoff` skill will replace the relevant
> procedures.

This guide defines roles, routing rules, and the handoff packet format when
Claude Code and Codex collaborate on this project. Read only when a handoff is
being considered.

The role descriptions below are routing examples, not exclusive capabilities
or authorization boundaries.

## Roles

**Claude Code** handles:
- broad codebase exploration and ambiguous requirements;
- architecture decisions and cross-module reasoning;
- difficult root-cause analysis that spans several subsystems;
- trade-off evaluation when the correct approach is not yet settled.

**Codex** handles:
- bounded implementation within a defined scope and clear acceptance criteria;
- regression tests and focused validation;
- P1/P2 reviews of the current diff;
- commit preparation and closure.

## Handoff Triggers

### Claude Code → Codex

Recommend Codex when all of the following are true:
- the architecture is settled and the approach is agreed;
- scope and acceptance criteria are explicit;
- no unresolved trade-off or cross-subsystem decision remains.

### Codex → Claude Code

Recommend Claude Code when any of the following is true:
- an architectural decision is unresolved or contradicted by new information;
- requirements conflict and resolution requires cross-module reasoning;
- several subsystems need trade-off analysis before implementation can proceed;
- root-cause analysis has failed after two focused attempts.

## Rules

- Agents must not invoke each other automatically.
- A handoff is a recommendation to the user, not an autonomous action.
- A handoff records prior authorization state but never transfers authority.
  The receiving agent must obtain explicit authorization in its current session
  before editing, committing, pushing, merging, or performing another
  state-changing action.

## Handoff Packet

Every handoff recommendation must include all of the following fields.

- **Objective** — one sentence: what the task is trying to accomplish.
- **Confirmed decisions / findings** — decisions already made and findings already verified; do not re-derive these.
- **Repository state** — output of `git status --short` and the current branch.
- **Files in scope** — exact list of files the receiving agent may edit.
- **Files out of scope** — exact list of files the receiving agent must not edit.
- **Acceptance criteria** — concrete, testable conditions that define done.
- **Validation already run** — tests, Ruff, and diff checks already completed.
- **Remaining uncertainty** — open questions or risks the receiving agent must resolve before editing.
- **Prompt for the receiving agent** — exact text to paste, including the
  requested operating mode and a reminder to verify current authorization.
- **Prior authorization state** — factual record of what was authorized in the
  previous session; it does not authorize the receiving agent.
