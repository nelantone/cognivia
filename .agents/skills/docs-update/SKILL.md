---
name: docs-update
description: Update Cognivia documentation from verified implementation and current-session evidence. Use for README, architecture, validation, status, reviewer, or future-work documentation after implementation changes. Do not use for product prompt edits, speculative roadmap writing, code changes, generated handoffs, or claims that cannot be verified.
---

# Docs Update

## Purpose

Make documentation accurately describe current implementation, evidence,
limitations, and pending work without inventing features or validation.

## Trigger

Use when a maintained repository document must be synchronized with verified
code, tests, runtime evidence, or an approved migration state.

## Do not trigger

Do not use for product prompts, code comments, automatic handoff reports,
historical rewrites, marketing copy, or unverified future architecture.

## Inputs

- Target document, audience, and requested scope.
- Current code or configuration evidence.
- Tests and commands actually run in the current session.
- Manual or browser checks actually performed.
- Known limitations and explicitly planned work.

## Workflow

1. Read the target document and the evidence that owns each affected claim.
2. Classify claims as implemented, tested, manually verified, pending, or
   unverified using [evidence language](references/evidence-language.md).
3. Identify stale, ambiguous, historical, or marketing-heavy wording.
4. Edit only the requested sections and preserve historical evidence unless the
   task explicitly changes its status or ownership.
5. Separate current functionality, current limitations, and future work.
6. Review links, paths, commands, dates, and validation claims.

## Outputs

Return the documents and sections changed, the evidence used, claims still
pending verification, validation performed, and any intentionally preserved
historical wording.

## Safety

- Never invent implementation, test results, readiness, provider behavior, or
  security guarantees.
- Never treat agent documentation as product-domain evidence.
- Do not expose secrets, environment values, private URLs, or raw logs.
- Do not modify product code, tests, or unrelated documents through this skill.
- Do not silently rewrite an authoritative audit or historical source.

## Validation

- Verify every changed factual claim against its owning source.
- Check local links and literal repository paths.
- Run `git diff --check` and review the documentation diff.
- State clearly which product tests, if any, were not required for a docs-only
  change.

## References

- [`AGENTS.md`](../../../AGENTS.md) — evidence and documentation rules.
- [`docs/agents/README.md`](../../../docs/agents/README.md) — agent-tooling facts.
- [Evidence language](references/evidence-language.md) — canonical claim status
  definitions for this skill.
