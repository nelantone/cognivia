@AGENTS.md

# Claude Code adapter

- Enter Claude Code plan mode before architectural, multi-file, migration, or
  destructive changes so the proposed scope can be reviewed before edits.
- Prefer project skills for reusable, multi-step workflows instead of adding
  those procedures to this file.
- Keep custom subagents read-only by default and give them one bounded research
  or review responsibility.
- Do not run parallel agents that edit the same working tree.
- Use separate worktrees for parallel editing only when the user explicitly
  authorizes their creation and cleanup.
- Treat tool output as evidence to inspect, not proof by itself; verify the
  relevant files, diffs, and exit results.
- Use `docs/agents/README.md` as the human-facing guide to this tooling.
- Canonical project skill bodies live under `.agents/skills/`. Project entries
  under `.claude/skills/` are discovery adapters only; keep canonical adapters
  as symlinks instead of copying `SKILL.md` bodies.
- Keep symlink adapters for exactly the six canonical responsibility skills.
  The project-owned `cxp` workflow uses one additional import-only,
  explicit-only adapter; retired Capstone aliases must not be reintroduced.
