# Agent Tooling Validation

## Purpose

This guide is the operational source for agent-tooling validation. It separates
deterministic local evidence from runtime discovery evidence and records the
completed compatibility gate.

## Deterministic commands

Run from the repository root:

```bash
git diff --check
bash -n scripts/agent/*.sh scripts/sentinel.sh
bash scripts/agent/test-agent-tooling.sh
bash scripts/agent/validate-agent-tooling.sh
bash scripts/agent/sentinel.sh
```

The legacy `bash scripts/sentinel.sh` path must produce the same Sentinel
result while its compatibility wrapper remains.

## Sentinel

The canonical executable is `scripts/agent/sentinel.sh`. With no arguments it
runs the complete deterministic check set, writes the detailed report to
`/tmp/cognivia-sentinel-YYYYMMDD-HHMMSS.txt`, atomically replaces the regular
file `/tmp/cognivia-sentinel-latest.txt`, and prints only a concise result,
blocking count, advisory count, report URLs, and copy/reveal commands. The
`file://` URLs are suitable for terminals that link local files.

The concise output includes these commands:

```bash
pbcopy < /tmp/cognivia-sentinel-latest.txt
open -R /tmp/cognivia-sentinel-latest.txt
```

The complete report records the timestamp, repository root, branch, commit,
optional expected branch and declared scopes, report format version, final
result, and every detailed check. Those checks cover dirty-tree counts, changed
paths, untracked or generated artifacts, likely credential patterns,
staged-scope sanity, diff whitespace, changed shell syntax, and agent-tooling
validation when relevant. Sentinel never prints or persists a matched
credential value.

Use optional arguments when the task has an exact branch or path boundary:

```bash
bash scripts/agent/sentinel.sh \
  --expected-branch chore/agent-tooling \
  --scope scripts/agent \
  --scope docs/agents
```

Tracked changes, rename/copy endpoints, and untracked paths remain NUL-delimited
from Git output through every scope, classification, credential, shell, and
agent-tooling consumer. Embedded newlines therefore remain part of one path;
only the human-readable report converts a path to an escaped Bash
representation. Both source and destination endpoints are scope-checked for
staged and unstaged tracked changes. A rename blocks when either endpoint falls
outside a declared scope, and the scope-success line appears only when every
complete path is inside the boundary.

Choose an output mode explicitly when needed:

```bash
# Persist the timestamped/latest reports and print the complete report.
bash scripts/agent/sentinel.sh --verbose

# Print the complete report without creating or updating any report file.
bash scripts/agent/sentinel.sh --stdout

# Persist outside the repository at an explicit absolute path and update latest.
bash scripts/agent/sentinel.sh --report /tmp/cognivia-sentinel-custom.txt

# Persist at the custom path and print the complete report.
bash scripts/agent/sentinel.sh \
  --verbose \
  --report /tmp/cognivia-sentinel-custom.txt
```

`--stdout` and `--report` are mutually exclusive and produce a usage error with
exit 2 when combined. A missing `--report` value and unknown options also
produce usage errors. Custom report paths must be absolute, must resolve
outside the repository, and must name a usable file rather than a directory.
Sentinel creates missing parent directories only for such an explicit,
validated destination.

Sentinel canonicalizes the repository root once with physical `pwd -P`
semantics. Report containment compares physical paths against that root, the
active Git directory, and the common Git directory. A repository reached
through a symlink, a case alias supported by the filesystem, a symlinked report
parent, or a linked-worktree administrative path cannot be used to persist a
report inside repository or Git administration storage.

Untracked regular files up to 4 MiB are scanned completely for likely
credential patterns. For larger text or binary files, Sentinel scans the first
4 MiB, names the escaped path in an advisory note, and withholds credential
PASS because the remainder was not inspected. A likely credential within that
bounded prefix remains blocking. Non-regular files and any read or scan error
also produce an advisory note and withhold credential PASS. Every filename
operand is separated from `grep` options, including names beginning with `-`;
matched values remain withheld.

Report files are created with restrictive permissions. The latest copy is an
atomic regular-file replacement rather than a symlink. If requested/default
persistence cannot be prepared or completed, Sentinel treats that condition as
a blocking deterministic finding, does not claim the report exists, and prints
the complete redacted findings to stdout so the underlying validation result is
not lost.

Expected summaries are:

- `PASS` when every deterministic check passes and no advisory decision remains;
- `PASS WITH NOTES` when deterministic checks pass but a human decision, such
  as undeclared scope or an untracked file, remains; and
- `BLOCKED` with a non-zero exit when a deterministic finding exists.

`docs/agent-prompts/sentinel-review.md` is optional interpretation guidance.
The executable does not invoke it or any provider.

## Validator

`scripts/agent/validate-agent-tooling.sh` is the single structural validator for
the agent-tooling surface. It is deterministic, local, fast, network-free, and
requires no installed package beyond Bash and standard repository tools.

It checks:

- expected instructions, the six canonical skills, explicit-only CXP,
  adapters, scripts,
  references, README, migration documentation, and this guide;
- required skill and instruction sections, including frontmatter whose first
  line is exactly `---`, whose distinct closing `---` precedes Markdown body
  content, and whose non-empty metadata is parsed only within that block;
- unique skill names within the canonical Codex source;
- unique canonical ownership in the migration map;
- exact duplicated canonical bodies and exact duplicated procedural sections;
- Codex metadata, canonical Claude symlink adapters, and the explicit-only CXP
  metadata and import adapter;
- local Markdown links and required import/reference targets;
- shell syntax and executable permissions;
- obsolete or still-planned wording for paths that now exist;
- `AGENTS.md` and `CLAUDE.md` import and ownership consistency;
- trailing whitespace; and
- likely credential patterns without printing matching values.

Success ends with `Agent tooling validator: PASS`. A failure names only the
category and path or metadata problem needed to fix it.

Run the focused regression fixtures after changing Sentinel, report behavior,
skill validation, or the validator itself:

```bash
/bin/bash scripts/agent/test-agent-tooling.sh
```

The harness uses isolated temporary Git repositories and copied tooling
fixtures. It covers newline-safe additions and rename endpoints,
non-contradictory scope output, physical report containment, leading-dash
filenames, bounded large-file and incomplete credential scans, malformed
canonical frontmatter, invalid Claude adapter targets, and missing CXP
explicit-only policies, plus all report modes and option failures, credential
redaction, result exit semantics, and the legacy Sentinel forwarding path
without modifying the Cognivia repository.

## Compatibility-gate record

The skill compatibility gate completed before the retired layer was removed.
Recorded Codex evidence was:

- canonical discovery: PASS 6/6;
- canonical explicit invocation: PASS 6/6;
- positive implicit routing: PASS 6/6;
- negative controls: PASS;
- legacy explicit checks: PASS 3/3;
- legacy implicit suppression: PASS; and
- no duplicate selector or trigger ambiguity found.

Recorded Claude evidence was:

- canonical discovery and explicit invocation: PASS 6/6;
- routing assessment: PASS 6/6;
- negative controls: PASS; and
- legacy wrappers: 3/3 discoverable and explicit-only.

The deterministic validator baseline passed 449 checks. The accepted residual
limitation is that Claude did not independently prove six isolated fresh-session
automatic triggers or execute all three legacy slash commands. That limitation
must not be restated as stronger runtime proof.

Based on this evidence, the compatibility gate was accepted as complete and the
three then-compatible Codex wrappers and Claude adapters were removed. The
historical removal does not change these six authoritative responsibility
owners:

- `task-brief`
- `architecture-audit`
- `safe-refactor`
- `docs-update`
- `commit-review`
- `session-handoff`

## CXP recovery validation

A later ownership review established that CXP means Codex Prompt and is
project-owned, not course material. The focused recovery restores CXP as a
supported orchestration utility while leaving the six canonical responsibility
owners unchanged and both Capstone aliases deleted.

The structural contract requires:

- `.agents/skills/cxp/SKILL.md` and Codex metadata to be discoverable;
- `policy.allow_implicit_invocation: false` for Codex;
- an import-only Claude adapter with `disable-model-invocation: true`;
- the exact five-line generated-prompt header;
- `.cxp/CXP_HANDOFF.md` behavior and the `.cxp/` ignore;
- no `cxp` row in canonical ownership; and
- no unexpected skill or adapter directories, including the retired Capstone
  aliases.

The validator proves this structural discovery and explicit-only contract. A
runtime invocation remains manual evidence and must not be inferred from the
structural PASS alone.

## Implicit-trigger smoke matrix

Use equivalent prompts in a fresh session for each runtime.

| Canonical skill | Positive prompt intent | Negative control |
| --- | --- | --- |
| `task-brief` | Turn a multi-file migration request into a scoped delivery contract before editing. | Look up one known file path. |
| `architecture-audit` | Produce a read-only frontend dependency and ownership inventory. | Implement an already approved small extraction. |
| `safe-refactor` | Execute one approved behavior-preserving module extraction. | Recommend broad architecture phases without editing. |
| `docs-update` | Synchronize maintained documentation with named verified implementation evidence. | Change a Cognivia product prompt. |
| `commit-review` | Review staged scope, validation evidence, and commit grouping without mutating Git. | Implement a bug fix. |
| `session-handoff` | Create a factual continuation handoff with current Git and validation state. | Summarize a trivial completed lookup. |

Expected results:

- each positive prompt selects only its canonical workflow;
- negative controls do not select that workflow;
- explicit invocations load the named workflow;
- no selector contains duplicate entries or ambiguous same-name owners.

CXP is outside the implicit-trigger matrix. Invoke `$cxp` or `/cxp` explicitly
and confirm that ordinary implementation, audit, refactor, documentation,
commit-review, and handoff requests continue to select only their canonical
owners.

## Failure handling

When Sentinel fails, keep the tree unchanged, inspect the named category and
path in the persisted report (or stdout fallback after a persistence failure),
correct only in-scope findings, and rerun the command. Treat secret findings as
sensitive: do not print or paste the value. If an actual credential entered Git
scope, stop and follow the repository security process.

When the validator fails, fix the canonical owner rather than copying content
into an adapter. Broken symlinks, imports, metadata, or links block discovery
claims. A manual trigger mismatch requires refining the canonical description
or runtime-only adapter metadata, then rerunning the complete smoke matrix.

## Hooks decision

No hook is implemented. Sentinel and the validator are explicit, reviewable,
network-free commands with clear scope and exit results. No deterministic gap
requires lifecycle interception, and an automatic hook would add another
discovery and failure surface without replacing either command.

## Compatibility removal and recovery status

The skill compatibility gate is complete, with its evidence and residual Claude
limitation recorded above. Public-repository cleanup Phase 3 removed CXP and
both Capstone aliases. The focused recovery restores only project-owned CXP;
the two Capstone wrappers and adapters remain retired. The `scripts/sentinel.sh`
forwarding wrapper is a separate compatibility surface and remains governed by
its own references and focused regression coverage.

Post-removal acceptance requires the focused regression harness, structural
validator, shell syntax check, `git diff --check`, scoped Sentinel, and complete
diff review to pass. Record those current-session results in the cleanup commit
and final report rather than rewriting the pre-removal evidence above.
