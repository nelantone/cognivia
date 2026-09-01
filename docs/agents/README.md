# Cognivia Agent Tooling

## Purpose

This guide explains how Codex and Claude Code share repository instructions,
where reusable workflows belong, and which parts of the tooling migration are
implemented versus planned. It is documentation for maintainers, not an
automatically discovered instruction file.

The approved design and repository evidence are recorded in the
[Agent Tooling Audit](AGENT_TOOLING_AUDIT.md). The completed compatibility
decisions are tracked in the [Skill Migration Map](SKILL_MIGRATION.md).

## Source-of-truth model

| Owner | Responsibility |
| --- | --- |
| `AGENTS.md` | Shared, durable project rules that apply to most repository work |
| `CLAUDE.md` | Minimal Claude Code adapter that imports `AGENTS.md` |
| `.agents/skills/` | Canonical reusable workflows |
| `scripts/agent/` | Deterministic local checks and agent-tooling validation |
| `docs/agents/` | Human guidance, audits, migration status, and maintenance notes |

Detailed procedures should have one canonical owner. Persistent instruction
files point to skills, scripts, or human documentation instead of reproducing
their bodies.

## Current migration status

Phase 1 establishes the shared instruction foundation:

- `AGENTS.md` is the concise shared source of truth.
- `CLAUDE.md` imports it and adds only Claude-specific behavior.
- This guide centralizes the human-facing architecture and migration status.
- The completed audit remains the authoritative migration design record.

Phase 1.5 aligns the active legacy workflow documents so they defer to
`AGENTS.md` for durable rules while remaining available for temporary
procedural detail.

Phase 2 introduced six canonical skill bodies and temporary explicit-only
compatibility entry points.

Phase 3 implementation is complete for the agent-tooling infrastructure:

- `scripts/agent/sentinel.sh` is the canonical deterministic advisory gate;
- `scripts/agent/validate-agent-tooling.sh` is the structural validator;
- Codex discovery is verified structurally and in the current session;
- `.claude/skills/` supplies no-copy Claude discovery adapters; and
- compatibility evidence is documented in [Validation](VALIDATION.md).

Public-repository cleanup Phase 3 completed the compatibility gate and removed
three skill names from Codex and Claude discovery. A later recovery correctly
reclassified project-owned `cxp` as a supported explicit-only orchestration
utility. The two Capstone aliases remain retired, and the six canonical skills
remain the authoritative responsibility owners.

## Current files and roles

| Path | Current role |
| --- | --- |
| `AGENTS.md` | Automatically discovered shared project instructions for Codex |
| `CLAUDE.md` | Claude Code entry point and import adapter |
| `.agents/skills/task-brief/` | Canonical task-contract workflow |
| `.agents/skills/architecture-audit/` | Canonical read-only architecture inventory workflow |
| `.agents/skills/safe-refactor/` | Canonical behavior-preserving refactor workflow |
| `.agents/skills/docs-update/` | Canonical evidence-based documentation workflow |
| `.agents/skills/commit-review/` | Canonical pre-commit review workflow |
| `.agents/skills/session-handoff/` | Canonical factual handoff workflow |
| `.agents/skills/cxp/` | Project-owned explicit-only Codex Prompt orchestration workflow |
| `.claude/skills/` | Six canonical discovery symlinks plus the explicit-only CXP import adapter |
| `docs/CODEX_WORKFLOW.md` | Legacy detailed Codex workflow and scope-control reference |
| `docs/agentic-pr-workflow.md` | Legacy PR workflow documentation |
| `docs/agent-prompts.md` | Legacy prompt index |
| `docs/agent-prompts/` | Legacy prompt templates, including Sentinel review guidance |
| `docs/AGENT_HANDOFF.md` | Legacy cross-agent role and handoff guidance |
| `scripts/agent/sentinel.sh` | Canonical deterministic local advisory gate |
| `scripts/agent/validate-agent-tooling.sh` | Canonical structural agent-tooling validator |
| `scripts/sentinel.sh` | Temporary forwarding wrapper for the old Sentinel path |
| `docs/agents/VALIDATION.md` | Validation commands, discovery smoke tests, and removal criteria |
| `docs/agents/AGENT_TOOLING_AUDIT.md` | Approved audit and migration plan |

These roles describe the repository after Phase 3.

## Canonical skills

| Skill | Purpose | Trigger | Non-trigger | Typical output | Dependencies | Migration status |
| --- | --- | --- | --- | --- | --- | --- |
| `task-brief` | Convert a request into a precise delivery contract. | Ambiguous, architectural, multi-file, or staged work. | Architecture inventory, refactor execution, commit review, or handoff. | Scope, acceptance criteria, protected areas, validation, and report contract. | `AGENTS.md` and repository evidence. | Canonical in Phase 2. |
| `architecture-audit` | Inventory architecture, dependencies, ownership, coupling, and risks. | Read-only frontend, backend, security, RAG, repository, or deployment audit. | Implementation, refactor execution, commit review, or ordinary file lookup. | Dependency and ownership maps with phased recommendations. | `AGENTS.md`, source, tests, configuration, and verified runtime evidence. | Canonical in Phase 2. |
| `safe-refactor` | Execute one behavior-preserving refactor phase. | Approved extraction, module split, dependency untangling, or test migration. | Broad architecture discovery, UX redesign, feature work, or commit creation. | Implemented phase, compatibility path, validation, rollback, and commit boundary. | Approved brief and `architecture-audit` when dependencies are not already known. | Canonical in Phase 2. |
| `docs-update` | Synchronize documentation with verified implementation evidence. | Maintained documentation is stale after verified work or migration. | Product prompt edits, speculative roadmaps, code changes, or handoffs. | Evidence-backed documentation diff and unverified claims list. | Owning implementation, test, runtime, and migration evidence. | Canonical in Phase 2. |
| `commit-review` | Assess staged scope and readiness without mutating Git. | Commit preparation, split, message, or staged-diff review request. | Implementation, general code review, or automatic Git action. | P1/P2 findings, validation gaps, exact staging groups, and readiness. | Current Git state, complete diffs, approved scope, and validation evidence. | Canonical in Phase 2. |
| `session-handoff` | Transfer factual project state to another session or agent. | Requested handoff or paused work with useful verified state. | Trivial completion, task planning, architecture audit, or authorization transfer. | Git state, completed and remaining work, validation, risks, and exact next action. | Current Git state, diffs, validation evidence, and known issues. | Canonical in Phase 2. |

## CXP orchestration and retired aliases

- `cxp` is a supported project-owned orchestration utility. Planning routes to
  `task-brief`, read-only inventory routes to
  `architecture-audit`, approved refactors route to `safe-refactor`, and final
  continuity routes to `session-handoff`; documentation and commit readiness
  route to `docs-update` and `commit-review`.
- `capstone-doc-edit` was a retired alias for `docs-update`.
- `capstone-commit-review` was a retired alias for `commit-review`.
- `architecture-audit` now owns the reusable read-only inventory pattern.

CXP is discoverable only for explicit invocation and does not compete for
implicit responsibility. The Capstone names remain only as historical migration
records and are not discoverable or invocable. See the
[Skill Migration Map](SKILL_MIGRATION.md) for removal and recovery evidence.

## Codex usage

Codex automatically discovers `AGENTS.md` from the repository root toward the
current working directory, with more local instructions taking precedence.
The root file therefore contains rules useful across the repository rather than
one-off task procedures.

Project skills live under `.agents/skills/`. The six canonical names in the
table above own reusable responsibilities; `cxp` is the additional explicit-only
orchestration utility.

The current Codex session exposed all six canonical skills. Official Codex
documentation confirms repository discovery from `.agents/skills/`, explicit
and implicit activation, and symlink support. The completed compatibility
evidence is recorded in [Validation](VALIDATION.md).

## Claude Code usage

Claude Code loads the root `CLAUDE.md`, which imports `AGENTS.md` using the
supported `@AGENTS.md` syntax. The remainder of `CLAUDE.md` is intentionally
limited to Claude-specific planning, subagent, and worktree guidance.

Claude Code documentation identifies `.claude/skills/` as the project discovery
path. Six entries are relative symlinks to canonical `.agents/skills/`
directories. The CXP entry is an import-only adapter with automatic invocation
disabled; no skill body is copied. Claude compatibility evidence and its
accepted residual limitation are recorded in [Validation](VALIDATION.md).

## Sentinel

Sentinel has two deliberately separate parts:

- `scripts/agent/sentinel.sh` checks branch and tree state, declared scope,
  unexpected and generated files, likely credential patterns without printing
  values, staged scope, whitespace, changed shell syntax, and agent-tooling
  structure when relevant.
- `scripts/sentinel.sh` forwards old invocations to the canonical executable.
- `docs/agent-prompts/sentinel-review.md` remains optional interpretation
  guidance and is never invoked by the script.

Sentinel is deterministic, local, network-free, non-mutating, and advisory. A
deterministic finding exits non-zero; human scope decisions are reported as
notes. Its default terminal output is concise while complete timestamped and
latest reports are kept under `/tmp`; full-output modes and the focused
regression command are documented in [Validation](VALIDATION.md).

## Validator

Run `bash scripts/agent/validate-agent-tooling.sh` after changing instructions,
skills, adapters, Sentinel, or agent documentation. It validates expected
paths, sections, metadata, unique ownership, duplicated bodies and procedural
sections, references, links, shell syntax, permissions, stale path language,
AGENTS/CLAUDE consistency, whitespace, and likely credential patterns. It uses
only local shell and Git-era system tools, makes no network call, and withholds
any suspected credential value.

## Standard workflow

1. Inspect the branch, working tree, task boundaries, and relevant source.
2. Plan the smallest coherent change and identify its evidence needs.
3. Implement narrowly without unrelated cleanup or hidden behavior changes.
4. Run validation appropriate to the changed surface.
5. Review the complete diff and staged scope.
6. Commit only after explicit authorization.
7. Produce a factual handoff when work continues in another session or agent.

## Upcoming frontend architecture audit

The next major product task is a read-only frontend architecture audit followed
by an incremental refactor. The tooling must support:

- an architecture inventory and dependency map;
- explicit Streamlit rerun, callback, widget, and session-state behavior;
- behavior-preserving extraction phases that do not redesign the UX;
- focused tests after each phase and isolated full validation when appropriate;
- reviewed, explicitly authorized commits; and
- factual session handoffs with evidence and unresolved risks.

The `architecture-audit`, `task-brief`, and `safe-refactor` skills cover the
preparation and implementation boundaries. The remaining skills cover
documentation, commit review, and continuity. The tooling structure is ready
for this audit; the retired compatibility layer is no longer a prerequisite for
any workflow.

## Adding or changing agent tooling

- Do not add skills, agents, hooks, or instruction layers casually.
- Give each skill one reusable responsibility with clear triggers, inputs,
  outputs, and safety boundaries.
- Keep one canonical body; use adapters or pointers only when a runtime requires
  them.
- Prefer scripts for deterministic, fast, local checks and documentation for
  human explanation.
- Prefer read-only subagents for bounded discovery or review work. Do not add
  autonomous implementation agents without a demonstrated recurring need.
- Document and validate instruction and skill discovery before deprecating a
  compatibility path.

## Migration roadmap

1. **Source-of-truth bootstrap:** concise shared instructions, Claude adapter,
   central guide, and preservation of the audit.
2. **Skill migration:** six canonical skills, implemented in Phase 2.
3. **Sentinel, validator, and discovery adapters:** implemented in Phase 3.
4. **Compatibility cleanup:** evidence accepted and three skill names removed
   in public-repository cleanup Phase 3.
5. **CXP ownership recovery:** restore project-owned CXP as an explicit-only
   orchestration utility while keeping both Capstone aliases retired.
6. **Frontend architecture audit:** use the canonical audit and handoff
   workflows without product edits.

Historical-document consolidation remains a separate public-repository cleanup
phase and does not change the canonical six-skill model.
