# Cognivia Project Instructions

## Project purpose

- Cognivia is currently a Python and Streamlit application.
- A JavaScript, React, or Next.js migration may happen later, but it is not the
  current production architecture.
- Do not apply future-stack conventions to current Python code unless the task
  explicitly concerns that migration.

## Repository boundaries

- Keep Streamlit presentation and interaction concerns separate from backend
  and domain logic.
- Keep provider access, prompts, graph orchestration, RAG, memory, persistence,
  security, and evaluation behind their existing boundaries.
- Do not introduce product, architecture, or UX redesign as part of a refactor.
- During frontend-only work, do not change backend or domain behavior.
- Do not change prompts, graph logic, RAG, memory, persistence, providers, or
  schemas unless the task explicitly authorizes that area.
- Make changes small, focused, and easy to review. Do not modify unrelated
  files or add speculative abstractions.
- Distinguish observed facts from assumptions and recommendations.

## Behavior-preserving refactors

- Inventory the current architecture and map dependencies before moving code.
- Extract incrementally, with one coherent responsibility per phase.
- Preserve behavior unless the task explicitly requires a behavior change.
- Keep Streamlit rerun behavior, widget identity, callbacks, and session-state
  transitions explicit.
- Use namespaced session-state keys and avoid hidden shared mode state.
- Do not combine architecture movement with UX or visual changes.
- Keep focused tests green after every phase, then run the broader validation
  justified by the changed surface.

## Security and provider safety

- Treat user input and external content as untrusted.
- Never print, log, expose, or commit secrets, credentials, tokens, or full API
  responses that may contain them.
- Do not inspect `.env` contents unless the task makes that strictly necessary;
  report suspected secret locations without printing values.
- Do not make paid provider or model calls unless the user explicitly authorizes
  them.
- Before expensive agent work, determine whether Codex or Claude is using a
  normal first-party login or a paid gateway such as OpenRouter. Report only
  provider status, never credential values, and stop for confirmation if the
  provider is OpenRouter or unclear.
- Show users safe, concise errors; keep technical diagnostics internal and do
  not expose raw stack traces.
- Retry only transient failures. Do not hide failures or silently continue after
  a correctness or security check fails.

## Git safety

- Inspect the current branch, working tree, staged changes, and relevant diff
  before editing or committing.
- Preserve existing user changes and stop if unexpected overlapping changes
  appear.
- Never reset, restore, discard, amend, force-push, merge, push, drop stashes,
  remove worktrees, delete branches, or delete files without explicit
  authorization for that exact operation.
- Never use `git add .` or `git add ..`; stage only explicitly approved paths.
- Review `git diff --cached --check` and the complete staged diff before every
  commit.
- Commit only with explicit authorization and use the approved files, order,
  and messages.
- Never claim that a commit, merge, push, test, validation command, or browser
  check succeeded without direct evidence.

## Validation ladder

Choose the smallest sufficient progression for the task, and report what was
run, what passed, and what remains unverified:

1. Focused unit or regression tests for the changed behavior.
2. Relevant Streamlit AppTests for affected UI flows.
3. Frontend, provider, RAG, or integration tests when those boundaries change.
4. Ruff on changed Python files, expanding to the repository before a commit
   when appropriate.
5. `python -m py_compile` for changed Python modules when useful.
6. `git diff --check` and a complete diff review.
7. The deterministic agent-tooling validator when that surface changes:
   `bash scripts/agent/validate-agent-tooling.sh`.
8. The advisory Sentinel gate: `bash scripts/agent/sentinel.sh`.
9. The isolated full suite when the scope or commit readiness requires it:

```bash
env -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  -u COGNIVIA_LLM_PROVIDER -u LANGSMITH_API_KEY \
  -u LANGCHAIN_API_KEY \
  LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests -q
```

Do not run the full suite for documentation-only work unless another change or
known risk justifies it. A passing command is evidence only for what it covered.

## Documentation and evidence

- Update documentation only from verified implementation or repository
  evidence.
- Label work accurately as implemented, automated-test verified,
  manually verified, or pending.
- Preserve authoritative audits and historical source documents; do not
  silently rewrite history to describe a planned state as current.
- Keep source-of-truth documents concise and link to detailed workflows instead
  of duplicating them.

## Agent-tooling ownership

- `AGENTS.md` owns shared, durable project rules.
- `CLAUDE.md` imports those rules and adds only Claude Code-specific guidance.
- `.agents/skills/` is the canonical home for reusable agent workflows.
- `scripts/agent/` owns deterministic local gates and tooling validation.
- `docs/agents/` owns human-facing tooling guidance and migration records.
- Historical workflows, prompts, handoffs, and the `scripts/sentinel.sh`
  compatibility wrapper remain separately governed by their documented
  removal criteria.

## Skill usage

The canonical skills are:

- `task-brief`
- `architecture-audit`
- `safe-refactor`
- `docs-update`
- `commit-review`
- `session-handoff`

These six names are the authoritative responsibility owners. The project-owned
`cxp` (Codex Prompt) skill is an additional explicit-only orchestration utility
that delegates to them; it is not an implicit workflow owner. Do not restore
the retired `capstone-doc-edit` or `capstone-commit-review` aliases or duplicate
canonical skill bodies for another agent runtime.

## Current Python and Streamlit conventions

- Prefer explicit, single-purpose functions, narrow responsibilities, and clear
  names.
- Use type hints where they improve readability and maintenance.
- Prefer functions, modules, dataclasses, and typed mappings over classes unless
  a class materially improves cohesion or state handling.
- Keep UI, business logic, RAG, memory, evaluation, persistence, and provider
  access separate.
- Preserve provider and domain boundaries and follow existing repository
  conventions.
- Handle errors explicitly; do not broadly catch exceptions or swallow failures.
- Add fast, deterministic, offline-friendly tests when behavior changes.
- Do not add dependencies or change the Python version or infrastructure
  without approval. The current development environment is macOS on Intel and
  Python 3.14.

## Future React and Next.js conventions

This section applies only after an explicitly authorized migration task:

- Use TypeScript and the App Router.
- Keep server and client boundaries explicit and avoid unnecessary client
  components.
- Preserve validation, accessibility, tested behavior, and backend contracts
  throughout the migration.
