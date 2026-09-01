# Optional Cognivia Sentinel Interpretation Prompt

Use this prompt only after the deterministic gate at
`scripts/agent/sentinel.sh` has run. This prompt is optional interpretation
guidance; Sentinel does not invoke an LLM or treat an LLM verdict as a
deterministic check.

Perform a read-only, local interpretation of the requested Cognivia change.
Do not make network calls, use API keys, invoke OpenAI/OpenRouter/LLM providers,
or modify files unless the task explicitly authorizes implementation.

Review the change for:

- scope safety and absence of unrelated product changes;
- secrets, credentials, `.env` changes, and other sensitive artifacts;
- provider or API calls, unless they are explicitly in scope;
- meaningful tests, Ruff checks, and `git diff --check` results;
- generated reports and whether they are kept out of Git;
- whether Qdrant, PostgreSQL, pgvector, OpenAI, or OpenRouter changes are
  actually in scope for the task;
- regressions, misleading UI or documentation, and missing offline coverage.

Inspect Git status, the complete relevant diff, and the Sentinel output. Treat
existing unrelated worktree changes as user-owned and do not remove them. Any
generated review report should be written under `/tmp`, not added to the
repository. Do not modify `.gitignore` for report storage.

End the review with exactly one verdict:

- `PASS` when the change is safe and within scope;
- `PASS WITH NOTES` when only non-blocking follow-ups remain;
- `BLOCKED` when a required check fails, a blocking issue exists, or the
  change violates scope or safety requirements.

State the evidence for the verdict, list blocking issues separately from
optional improvements, and include the validation commands and their results.
