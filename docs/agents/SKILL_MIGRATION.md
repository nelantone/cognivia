# Skill Migration Map

## Purpose and authority

This document records ownership, compatibility evidence, and removal decisions
for the skill migration. `AGENTS.md` remains authoritative for durable
repository rules; each canonical `SKILL.md` owns its reusable procedure.

The completed migration keeps one canonical body per responsibility. Six
canonical skills own those responsibilities. Project-owned `cxp` is supported
separately as an explicit-only orchestration utility.

## Discovery decision

The current official Codex documentation, reverified on 2026-08-06, states that
Codex scans `.agents/skills` from the working directory through the repository
root and lists distinct skill names separately. A `SKILL.md` body loads after a
skill is selected, while its name and description support selection. See
[OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills).

Claude Code 2.1.81 is installed locally. Current Claude documentation requires
project skills under `.claude/skills/`, so the repository uses symlinks for the
six canonical directories plus an import-only explicit CXP adapter. No skill
body is copied. See
[Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/slash-commands).

## Canonical ownership

| Canonical skill | Owned responsibility | Owned reference |
| --- | --- | --- |
| `task-brief` | Request-to-delivery contract, including scope, constraints, non-goals, validation, and reporting | `references/task-brief-format.md` |
| `architecture-audit` | Read-only inventory, dependency and ownership mapping, coupling, risks, and phased recommendations | `references/architecture-audit-format.md` |
| `safe-refactor` | One approved behavior-preserving extraction phase, compatibility, validation, and rollback | `references/refactor-phase-checklist.md` |
| `docs-update` | Evidence-backed documentation status and claim language | `references/evidence-language.md` |
| `commit-review` | Non-mutating staged-scope and commit-readiness review | `references/commit-review-format.md` |
| `session-handoff` | Factual Git, work, validation, risk, and next-action transfer | `references/session-handoff-format.md` |

References remain inside the skill that owns the corresponding output. Skills
link to one another when sequencing is necessary instead of copying procedures.

## CXP delegation and historical content split

| Legacy content | New owner | Preserved capability |
| --- | --- | --- |
| `cxp` request normalization, scope, constraints, acceptance criteria, and final report contract | `task-brief` | Precise implementation brief before work begins |
| `cxp` repository inspection, dependency tracing, ownership, risk, and phased audit output | `architecture-audit` | Read-only architecture work across product and operational surfaces |
| `cxp` incremental implementation, behavior protection, validation, and rollback | `safe-refactor` | Small approved refactor phases |
| `cxp` final state, validation record, unresolved work, and next step | `session-handoff` | Session continuity plus the CXP-specific `.cxp/CXP_HANDOFF.md` contract |
| `capstone-doc-edit` fact/limitation/future distinction and evidence discipline | `docs-update` | Factual documentation without capstone policy framing |
| `capstone-commit-review` status, diff, validation, split, and message review | `commit-review` | Read-only commit preparation without automatic Git mutation |

## Compatibility removal record

| Skill or alias | Canonical owner | Strategy | Current status |
| --- | --- | --- | --- |
| `cxp` | All six canonical skills as applicable | Explicit-only orchestration utility | Removed in public-repository cleanup Phase 3, then restored after ownership was correctly reassessed as project-owned |
| `capstone-doc-edit` | `docs-update` | Explicit-only forwarding wrapper | Removed in public-repository cleanup Phase 3 after the compatibility gate completed |
| `capstone-commit-review` | `commit-review` | Explicit-only forwarding wrapper | Removed in public-repository cleanup Phase 3 after the compatibility gate completed |

The cleanup removed all matching metadata, adapters, validator expectations,
focused fixtures, and the `.cxp/` ignore. Recovery restored only CXP and its
supporting integration. Historical audit and migration references retain the
removal record; neither Capstone alias was restored.

## Compatibility-gate evidence

The compatibility gate is complete based on the following recorded evidence:

1. Codex canonical discovery, explicit invocation, and positive implicit
   routing passed for all six skills; negative controls passed.
2. Codex explicit legacy checks passed for all three wrappers, legacy implicit
   suppression passed, and no selector or trigger ambiguity was found.
3. Claude canonical discovery and explicit invocation passed for all six
   skills; its routing assessment passed for all six and negative controls
   passed.
4. All three Claude legacy wrappers were discoverable and explicit-only.
5. The deterministic baseline passed 449 checks before removal.

Accepted residual evidence limitation: Claude did not independently prove six
isolated fresh-session automatic triggers or execute all three legacy slash
commands. This is recorded as a limitation, not stronger runtime proof. The
full evidence interpretation is in [Validation](VALIDATION.md).

## Phase 2 exclusions

Phase 2 does not migrate Sentinel, create the agent-tooling validator, add
Claude adapters, add hooks or subagents, or remove legacy workflow documents.
