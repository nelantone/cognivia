---
name: session-handoff
description: Create a concise factual handoff for work continuing in another session, tool, or agent. Use when the user requests a handoff, work pauses with useful state, or a blocked task needs an exact next action. Do not use automatically for trivial completed work, as an implementation plan, or to transfer edit or Git authorization.
---

# Session Handoff

## Purpose

Transfer verified project state without forcing the next session to reconstruct
completed work or trust unsupported claims.

## Trigger

Use when the user asks for a handoff or when paused or blocked work has verified
state worth preserving for a later session.

## Do not trigger

Do not generate a handoff automatically for every task. Do not use it as a task
brief, commit review, architecture audit, or authorization mechanism.

## Inputs

- Objective and current status.
- Current branch, staged, unstaged, and untracked state.
- Completed work and files changed.
- Validation actually run and manual evidence actually collected.
- Known issues, risks, assumptions, and remaining work.
- Exact next action and prior authorization state.

## Workflow

1. Inspect current Git state and relevant diffs before describing them.
2. Separate completed work, remaining work, known issues, and open decisions.
3. Record validation by command and result; identify failed, skipped, and
   unavailable checks.
4. Distinguish automated, manual, browser, provider, and documentation evidence.
5. State prior authorization only as historical context; require the receiving
   session to obtain its own authorization for state-changing work.
6. End with one exact next action.
7. Write a handoff file only when the user authorizes a specific path.

## Outputs

Return a handoff using
[the session handoff format](references/session-handoff-format.md). Keep it
compact enough to paste into a new session.

## Safety

- Never include secrets, environment values, private URLs, large logs, command
  transcripts, or full diffs.
- Never claim a file, commit, test, browser check, merge, or push exists without
  current evidence.
- Never imply that a handoff transfers edit, commit, push, merge, deletion, or
  provider-call authorization.
- Do not modify product files while generating a handoff.

## Validation

- Recheck branch and status immediately before finalizing the handoff.
- Verify named files, commits, and paths exist.
- Match validation claims to captured results from the current session.
- Ensure known failures and unverified assumptions are visible.
- Confirm the next action is specific and within remaining scope.

## References

- [`AGENTS.md`](../../../AGENTS.md) — evidence, security, and authorization rules.
- [`docs/AGENT_HANDOFF.md`](../../../docs/AGENT_HANDOFF.md) — temporary legacy
  compatibility guidance.
- [Session handoff format](references/session-handoff-format.md) — canonical
  output structure.
