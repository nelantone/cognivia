# Cognivia Agent Tooling Audit and Migration Plan

**Audit date:** 2026-08-05

**Repository:** `<repository-root>`

**Branch audited:** `chore/agent-tooling`

**Phase:** inventory, research, architecture, and planning only

## 1. Executive summary

The repository has useful agent guidance, but no single clean tooling architecture. `AGENTS.md` is the automatically discovered Codex instruction source and says permanent rules belong there, while three workflow documents and a large prompt library repeat many of the same scope, validation, review, Git, and provider rules. `CLAUDE.md` correctly uses Claude Code's supported `@AGENTS.md` import, but it also imports two large workflow files at startup. That makes Claude load procedural material on every session and gives the Codex-branded workflow more authority than its intended role.

The three repository skills are valid Codex skills under `.agents/skills/`. `cxp` combines task briefing, implementation discipline, commit readiness, self-scoring, and handoff persistence in one 163-line workflow. The two `capstone-*` skills contain good focused rules but use educational terminology that is narrower than the repository's next engineering phase. Claude Code does not document `.agents/skills/` as a project skill discovery path; its documented project path is `.claude/skills/`. The five proposed skill responsibilities are justified, but a small Claude discovery adapter is required if both tools must expose the same skills natively.

Sentinel is a mixture, not one gate. `scripts/sentinel.sh` is a safe, deterministic, local shell preflight that prints Git status and runs `git diff --check`. It does not invoke the separate LLM prompt, inspect staged or untracked content, search for secrets, or enforce the prompt's verdict. It is correctly labeled advisory in most current documentation. Its script and prompt disagree about whether generated reports belong under `/tmp` or `.codex-reports/`. Sentinel must remain advisory and be separated into deterministic checks, optional interpretation guidance, and human-facing workflow documentation.

The pragmatic target is the proposed minimal structure with one necessary addition: `.claude/skills/` compatibility entries for Claude Code. `AGENTS.md` should be the concise shared durable source of truth; `CLAUDE.md` should import only `AGENTS.md` and add Claude-specific guidance; `.agents/skills/` should own the five canonical workflow bodies; `scripts/agent/` should own deterministic tooling; and `docs/agents/README.md` should explain ownership and use. No custom Claude subagent or hook is needed now.

Six migration phases are safer than replacing everything at once. The exact first phase should establish ownership with minimal changes to `AGENTS.md` and `CLAUDE.md` plus a new `docs/agents/README.md`, without deleting, moving, or rewriting legacy workflows. That preserves current Codex behavior and creates a stable landing point before skill or Sentinel migration.

## 2. Audit method and baseline

The required baseline passed before repository research began:

| Check | Observed result |
| --- | --- |
| `git status --short --branch` | `## chore/agent-tooling`; no staged, modified, or untracked files |
| `git log --oneline -8` | HEAD `1de7484`; recent history inspected |
| `git diff main...HEAD --stat` | Empty; no branch changes relative to `main` |
| `git worktree list` | One worktree at the repository path on `chore/agent-tooling` |
| `codex login status` | Logged in using ChatGPT; not OpenRouter |

The audit used filename discovery, full content reads, `rg` reference searches, Git history, ignore-source checks, permission inspection, `bash -n`, and official primary documentation. Product code was not audited. Files that merely contain product prompts, the word “agent,” or test sentinel variables were excluded after content inspection.

## 3. Current tooling inventory

### 3.1 Persistent and executable tooling

| Current path | Type and classification | Purpose | Intended consumer | Actual discovery or references | Activity assessment | Recommendation | Proposed target |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Markdown; shared persistent instructions with Codex-specific sections | Project rules, modes, architecture, safety, validation, Git, provider guard | Codex primarily; imported into Claude | Codex auto-discovers it; `CLAUDE.md` imports it; workflow docs link to it | Active and authoritative for Codex | Rewrite concisely; retain durable shared rules, move procedures to skills/docs | `AGENTS.md` |
| `CLAUDE.md` | Markdown; Claude-specific adapter | Imports shared and workflow instructions | Claude Code | Claude auto-loads it; it imports three files | Active, but over-importing | Keep minimal; import only `AGENTS.md`, add Claude-specific plan/subagent rules and a literal docs pointer | `CLAUDE.md` |
| `.agents/skills/cxp/SKILL.md` | Agent Skill; reusable workflow | Large engineering wrapper plus persistent handoff | Codex | Auto-discovered by Codex; explicitly named in `AGENTS.md`; recent history | Active/discoverable | Split unique content across `task-brief`, `safe-refactor`, and `session-handoff`; retain compatibility pointer temporarily | `.agents/skills/task-brief/`, `.agents/skills/safe-refactor/`, `.agents/skills/session-handoff/` |
| `.agents/skills/cxp/agents/openai.yaml` | Codex skill UI metadata | Display name, summary, default prompt | Codex/ChatGPT skill UI | Loaded only with `cxp` skill metadata | Active metadata | Replace with matching metadata for canonical skills where useful; retire with `cxp` | New skills' optional `agents/openai.yaml` |
| `.agents/skills/capstone-doc-edit/SKILL.md` | Agent Skill | Factual Capstone documentation updates | Codex | Auto-discovered by Codex; no literal repo references required | Discoverable; actual invocation cannot be proven from Git | Generalize while preserving fact/limitation/future separation; compatibility pointer | `.agents/skills/docs-update/SKILL.md` |
| `.agents/skills/capstone-commit-review/SKILL.md` | Agent Skill | Read-only commit grouping and recommendations | Codex | Auto-discovered by Codex; no literal repo references required | Discoverable; actual invocation cannot be proven from Git | Generalize; preserve read-only planning and exact path staging advice | `.agents/skills/commit-review/SKILL.md` |
| `docs/agent-prompts.md` | Prompt-template library; duplicate/workflow documentation | Copy/paste prompts for planning, implementation, PR review, PR writing, and comment fixes | Humans, Codex, Claude | Linked by `agentic-pr-workflow.md`; referenced by its own prompts | Human-invoked, not auto-discovered | Merge unique templates into skills or concise docs; replace with compatibility pointer; remove later | Five skills plus `docs/agents/README.md` |
| `docs/agent-prompts/safety-architecture-review.md` | Prompt template/reference material | Broad read-only safety and architecture checklist | Humans/agents when explicitly requested | `AGENTS.md` explicitly routes optional reviews to it | Active by instruction | Preserve unique review checklist as optional reference under `safe-refactor`; do not make it always-on | `.agents/skills/safe-refactor/references/safety-architecture-review.md` |
| `docs/agent-prompts/sentinel-review.md` | LLM prompt template | Advisory read-only change interpretation with PASS rubric | Humans and an LLM reviewer | Printed by `scripts/sentinel.sh`; no execution linkage | Active as an optional prompt | Rename/rehome as interpretation guidance; reconcile report path; keep clearly non-deterministic | `docs/agents/` or `scripts/agent/` adjacent reference, not executable gate |
| `docs/agentic-pr-workflow.md` | Workflow documentation; duplicate | Five-role PR lifecycle and sample commands | Humans/agents | Links to `AGENTS.md`, `CODEX_WORKFLOW.md`, and `AGENT_HANDOFF.md` | Referenced but partly stale | Merge durable lifecycle explanation into README and skills; replace with pointer; remove later | `docs/agents/README.md`, `task-brief`, `commit-review` |
| `docs/AGENT_HANDOFF.md` | Handoff format/workflow documentation | Cross-tool role routing and handoff packet | Humans, Claude, Codex | Imported by `CLAUDE.md`; referenced by `AGENTS.md` and workflow docs | Active | Merge packet fields into `session-handoff`; remove hard tool-role assumptions; compatibility pointer | `.agents/skills/session-handoff/SKILL.md` and `docs/agents/README.md` |
| `docs/CODEX_WORKFLOW.md` | Codex-specific workflow documentation; duplicate | Modes, implementation/review flows, validation, short prompts | Codex, humans; currently Claude too | Referenced by `AGENTS.md`; imported by `CLAUDE.md`; linked elsewhere | Active but over-broad | Distribute procedures to skills and concise human docs; replace with pointer; remove later | Five skills and `docs/agents/README.md` |
| `scripts/sentinel.sh` | Executable validation; advisory | Print status and run unstaged whitespace-error check | Humans/agents | Invoked by README and five current/status docs; points to Sentinel prompt | Active; shell syntax valid; executable | Move deterministic body carefully; leave wrapper at old path until references migrate | `scripts/agent/sentinel.sh` |

### 3.2 Related local, historical, and reference artifacts

| Path | Classification | Finding | Treatment |
| --- | --- | --- | --- |
| `.claude/settings.local.json` | Claude-specific local instructions/settings | Ignored via the user's global Git ignore. It pre-approves several commands, including a Python-stdin form broad enough to execute arbitrary local Python without a new prompt. It is not team tooling. | Keep local and out of migration. Recommend the owner narrow permissions separately; never copy it into tracked project settings. |
| `.gitignore` | Supporting reference | Tracks `.cxp/` exclusion, so the CXP handoff is intentionally local. It does not track `.codex-reports/` exclusion. | Update only in a later approved phase if compatibility artifacts require it; no change is required for the target design. |
| `.git/info/exclude` entry for `.codex-reports/` | Local ignore state, not shared instructions | Makes reports ignored only in this checkout. A fresh clone does not inherit the exclusion. | Document honestly; do not treat `.codex-reports/` as a portable repository contract. |
| `.codex-reports/*.md` and `.codex-reports/debug/` | Historical/session artifacts | Numerous ignored task reports and debug outputs. They are outputs of prior agent work, not tooling or discovery inputs. | Retain locally or clean up separately at owner discretion; do not migrate as canonical guidance. |
| `CLAUDE_COGNIVIA_CHAT_FORM_ARCHITECTURE.md` | Historical one-off prompt/reference material | A tracked, 357-line Claude task brief for an earlier form/chat architecture. It is not auto-discovered and contains stale “frontend frozen” and capstone wording. No references were found. | Preserve only if product history matters; otherwise archive or remove later after confirming no unique roadmap value. Never merge it into persistent agent instructions. |
| `README.md`, `PROJECT_STATUS.md`, `docs/architecture.md`, `docs/capstone-reviewer-guide.md`, `docs/current-state-validation-and-next-steps.md`, `docs/smoke-test-checklist.md`, `docs/change-plans/002-openai-provider-support.md` | Product/status/reference documents | Mention Sentinel as part of validation. They do not define agent discovery. | Keep content ownership unchanged; update only Sentinel paths/claims in the later documentation migration phase. |
| `prompts.py`, `data/knowledge_base/**`, PDFs with “agent” in names, tests containing sentinel state keys | Product code/data; excluded | Search-name matches, but content is application behavior or evidence data, not development-agent tooling. | Explicit non-goal; no migration. |

### 3.3 Stale terminology and missing artifacts

The names `capstone-doc-edit`, `capstone-commit-review`, “Capstone reviewer,” “Learning & Defense Notes,” and “Skill Compass” tie reusable engineering behavior to an educational phase. The unique rules should survive, but the names and default outputs should become repository-neutral.

No tracked agent file directly names the former education provider, but the “Capstone” framing is pervasive in both skills, PR prompts, and the historical Claude task prompt. It is unnecessary for architecture inventories, frontend extraction, or ordinary reviewed commits.

All directly referenced tracked agent files exist. `.cxp/CXP_HANDOFF.md` does not exist because it is generated only when `$cxp` runs; that is expected. The current checkout contains `.venv/bin/python`. The important portability gap is `.codex-reports/`: its ignore rule exists only in `.git/info/exclude`, while the Sentinel prompt describes it as a stable ignored location.

## 4. Consumer and discovery map

| Consumer | Automatically loaded | Loaded only on trigger/import/read | Not automatically discovered |
| --- | --- | --- | --- |
| Codex | Root `AGENTS.md`; metadata for skills found in `.agents/skills/` | Full `SKILL.md` when explicitly invoked or description-matched; docs when an instruction or task causes Codex to read them | `CLAUDE.md`, general files under `docs/`, `scripts/sentinel.sh`, historical prompts |
| Claude Code | Root `CLAUDE.md`; imported `AGENTS.md`, `CODEX_WORKFLOW.md`, and `AGENT_HANDOFF.md`; local `.claude/settings.local.json` settings | `.claude/rules/` when present; `.claude/skills/` when present and triggered; files explicitly referenced/read | Repository `.agents/skills/` as native project skills; `docs/agent-prompts*`; shell scripts |
| Human maintainer | Nothing automatic | Everything by documentation links, commands, and copy/paste | N/A |
| Shell/CI | Nothing automatic | `scripts/sentinel.sh` only when invoked | All Markdown instructions and LLM prompts |

Observed automatic-discovery facts do not prove that a workflow was followed in prior sessions. Git history and references prove that files are present, linked, or recently changed; they do not provide runtime invocation telemetry.

### Source-of-truth graph

```text
Current

CLAUDE.md
  ├── imports AGENTS.md ──> points to CODEX_WORKFLOW + safety prompt + handoff
  ├── imports CODEX_WORKFLOW.md
  └── imports AGENT_HANDOFF.md

agentic-pr-workflow.md ──> AGENTS + CODEX_WORKFLOW + AGENT_HANDOFF + prompts
agent-prompts.md ────────> AGENTS + CLAUDE + all three workflow documents
scripts/sentinel.sh ─────> sentinel-review.md

Target

CLAUDE.md ──imports──> AGENTS.md (shared durable rules)
                         ├── names canonical skills
                         └── points literally to docs/agents/README.md

.agents/skills/* ───────> canonical on-demand procedures
.claude/skills/* ───────> Claude discovery adapters to canonical procedures
scripts/agent/* ────────> deterministic local checks
docs/agents/README.md ──> human architecture and maintenance guide
```

## 5. Duplication and conflict analysis

### 5.1 Repeated instructions

The following concepts appear in three or more places:

- Small, focused scope and no unrelated refactors: `AGENTS.md`, `CODEX_WORKFLOW.md`, `cxp`, `agentic-pr-workflow.md`, and multiple prompt templates.
- Preserve existing work and inspect Git status/diff: `AGENTS.md`, `cxp`, commit-review, pre-push prompt, Sentinel prompt, and handoff guide.
- Focused tests, Ruff, `git diff --check`, and final self-review: `AGENTS.md`, `CODEX_WORKFLOW.md`, `cxp`, PR workflow, prompt library, README validation, architecture, status docs, and smoke checklist.
- Explicit approval before editing or committing: `AGENTS.md`, `CODEX_WORKFLOW.md`, `cxp`, handoff guide, and prompt templates.
- No secrets or raw errors: `AGENTS.md`, safety review prompt, implementation prompt, pre-push prompt, PR writer prompt, Sentinel prompt, and product validation docs.
- Separation of UI, business logic, RAG, memory, persistence, and tests: `AGENTS.md`, `cxp`, safety review prompt, implementation prompt, pre-push prompt, and historical Claude architecture prompt.
- OpenRouter Cost Guard: `AGENTS.md`, `agent-prompts.md`, `agentic-pr-workflow.md`, and several copy/paste prompts.
- Planning/implementation/review roles: `AGENTS.md`, `CODEX_WORKFLOW.md`, `agentic-pr-workflow.md`, `agent-prompts.md`, and `AGENT_HANDOFF.md`.

### 5.2 Conflicts and ambiguities

| Issue | Evidence | Risk | Resolution |
| --- | --- | --- | --- |
| Several canonical-workflow claims | `AGENTS.md` says detailed procedures live in `CODEX_WORKFLOW.md`; the PR workflow says it must align with three other files; the prompt library tells agents to follow all of them | Drift and arbitrary rule selection | One ownership model: durable rules in `AGENTS.md`, procedures in skills, explanation in one README |
| Claude loads Codex procedures unconditionally | `CLAUDE.md` imports `CODEX_WORKFLOW.md` and `AGENT_HANDOFF.md` after `AGENTS.md` | Context cost and tool-specific behavior leaking into Claude | Import only `AGENTS.md`; keep Claude behavior in a short adapter |
| Commit/push workflow versus approval gate | `agentic-pr-workflow.md` presents `git add`, `git commit`, and `git push` as normal sequential steps; `AGENTS.md` requires separate explicit approvals | An agent may treat workflow steps as authorization | Keep all state-changing Git authorization rules only in `AGENTS.md`; skills may propose commands, never infer authorization |
| CXP output location versus Sentinel output location | CXP always writes `.cxp/CXP_HANDOFF.md`; Sentinel prompt says `.codex-reports/`; script says `/tmp` | Unclear persistent-output policy | Session handoff should write only when requested; deterministic scripts should not create reports; docs define allowed local locations |
| Sentinel report-path contradiction | Prompt requires `.codex-reports/`; script prints “under /tmp” | Misleading operator instructions | Choose `/tmp` for ephemeral output or add a tracked ignore intentionally; do not rely on `.git/info/exclude` |
| Sentinel scope overstatement | Product docs say Sentinel “passed,” but the script only runs status plus unstaged `git diff --check` and merely prints the LLM prompt path | False confidence | Report deterministic command results separately from any optional LLM verdict |
| Handoff authorization ambiguity | Handoff rules require the receiving agent to obtain re-authorization; packet also contains `Editing authorized: Yes/No` | Receiving agent may not know whether packet authorization is sufficient | Define packet as factual continuity only; current-session user authorization remains required for edits |
| Review severity wording drift | Review mode treats P1/P2 as blocking; pre-push prompt calls P2 “should fix before merge if time allows” | Inconsistent closeout threshold | Adopt one rubric: P1/P2 blocking for approved task correctness; P3 optional/deferred |
| Capstone-specific validation | Existing skills and prompts hard-code reviewer/demo narratives | Noisy or irrelevant outputs during frontend engineering | Move product-demo guidance out of reusable skills; retain only in reviewer docs |
| Local Claude permission breadth | `.claude/settings.local.json` allows a Python stdin command | Arbitrary Python could run without a fresh tool approval in this local profile | Narrow local permission separately; never promote it to project settings |

## 6. Answers to the audit questions

1. **Current source of truth:** Codex automatically treats `AGENTS.md` as the root instruction source. The repository text intends it to own permanent rules, but operational truth is distributed across `CODEX_WORKFLOW.md`, `agentic-pr-workflow.md`, `agent-prompts.md`, and the handoff guide. Claude currently receives four instruction bodies because of imports.
2. **Multiple canonical workflows:** Yes. At least `AGENTS.md`, `CODEX_WORKFLOW.md`, and `agentic-pr-workflow.md` claim coordinating authority; `agent-prompts.md` repeats them as executable prose.
3. **Duplicated instructions:** Scope, validation, review severity, Git safety, secret handling, architecture separation, provider checks, and edit authorization are duplicated extensively.
4. **Conflicts:** Commit/push sequencing, P2 severity, report storage, handoff authorization, and tool-specific ownership conflict or remain ambiguous.
5. **Automatically discovered by Codex:** Root `AGENTS.md` and repo skills in `.agents/skills/`. Skill bodies load on trigger; `agents/openai.yaml` is optional metadata. General docs and `CLAUDE.md` are not default Codex instruction files.
6. **Human documentation only:** `agentic-pr-workflow.md`, `agent-prompts.md`, most of `CODEX_WORKFLOW.md`, `AGENT_HANDOFF.md`, product validation references, and the historical Claude task prompt unless an agent is explicitly told to read them.
7. **Sentinel today:** A mixture of an executable deterministic shell preflight, a separate LLM review prompt, and workflow/documentation claims. It is not a security control.
8. **Prompts that should become skills:** Pre-implementation/task planning, behavior-preserving refactor, factual docs update, commit review, and session handoff. The broad safety checklist should be a `safe-refactor` reference, not a sixth always-visible skill.
9. **Skills to rename:** `cxp` becomes three focused skills; `capstone-doc-edit` becomes `docs-update`; `capstone-commit-review` becomes `commit-review`.
10. **Content to preserve:** CXP scope mapping, sensitive-file review, browser-versus-AppTest distinction, validation honesty, and handoff fields; docs skill's implemented/limitation/future split; commit skill's read-only grouping, exact paths, secret/generated-file warnings, and evidence-based test claims.
11. **Obsolete terminology:** `capstone-*`, Capstone reviewer/demo language, Learning & Defense Notes, Skill Compass, and CXP as an unexplained repository-specific acronym.
12. **Educational coupling:** No tracked agent tooling names the former education provider directly, but Capstone/educational framing couples general workflows unnecessarily to that context.
13. **Files removable later without unique loss:** `docs/agent-prompts.md`, most of `docs/agentic-pr-workflow.md`, and eventually `docs/CODEX_WORKFLOW.md` after procedures migrate and pointers survive a compatibility window. The historical Claude task prompt can be removed if product-history ownership confirms it is obsolete.
14. **Compatibility pointers required:** Old skill names, `scripts/sentinel.sh`, and legacy workflow document paths need temporary pointers/wrappers because current files and docs reference them.
15. **Missing referenced tooling:** No required tracked file is missing. `.cxp/CXP_HANDOFF.md` is generated, not missing. The portable ignore policy for `.codex-reports/` is missing despite prompt claims.
16. **Unsafe scripts:** `scripts/sentinel.sh` is non-destructive and syntax-valid. Its weakness is incomplete coverage and potentially misleading “gate” language, not unsafe shell behavior.
17. **Risk-causing instructions:** The PR workflow can encourage commits/pushes without restating the separate approval gate; worktree cleanup is not automated in tracked tooling; no instruction deletes branches, stashes, or worktrees automatically. Parallel writes are not explicitly prohibited for Claude. Local Claude permissions are broader than necessary. Secret commands mostly redact values correctly.
18. **Capabilities needed for the frontend audit:** Task briefing, read-only architecture and dependency inventory, behavior/invariant capture, incremental extraction, test migration, focused/full validation, browser/manual evidence, diff and staged-scope review, explicit commit authorization, and factual handoff. The five skills plus deterministic validation cover these without adding an agent collection.

## 7. Official-source research notes

All sources were accessed on **2026-08-05**. Findings are paraphrased from official primary documentation.

| Official source | Domain | Concise finding | Design decision supported |
| --- | --- | --- | --- |
| [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | `developers.openai.com` (redirects to official ChatGPT Learn docs) | Codex constructs an instruction chain from global scope and then one instruction file per directory from repository root to CWD; closer files appear later. Default project discovery prioritizes `AGENTS.override.md`, then `AGENTS.md`. | Keep one concise root `AGENTS.md`; do not treat general docs as automatically loaded or create competing root instruction files. |
| [Build skills](https://developers.openai.com/codex/skills) | `developers.openai.com` | A skill is a directory with required `SKILL.md` name/description metadata and optional scripts, references, assets, and OpenAI UI metadata. Codex scans `.agents/skills` from CWD to repository root and loads full bodies only on invocation. | Keep canonical repo workflows under `.agents/skills`; use clear trigger/non-trigger descriptions and one job per skill. |
| [Subagents](https://developers.openai.com/codex/subagents) | `developers.openai.com` | Subagents reduce main-context noise and suit independent read-heavy exploration, tests, triage, and summaries; parallel write-heavy work increases conflict and coordination cost. | Default custom subagents to deferred; if used, prefer read-only work and isolate any writes. |
| [Code review](https://developers.openai.com/codex/code-review) | `developers.openai.com` | `/review` can inspect base-branch, uncommitted, or commit scopes and returns prioritized findings without changing the worktree. | Use built-in review plus the repository's severity/scope criteria instead of creating a custom implementation agent. |
| [How Claude remembers your project](https://code.claude.com/docs/en/memory) | `code.claude.com` | Claude Code loads project `CLAUDE.md`; `@path` imports are supported and the docs specifically recommend importing `AGENTS.md` for cross-tool sharing. Persistent instruction files should stay concise, with procedures moved to skills or path-scoped rules. | Keep `CLAUDE.md` as `@AGENTS.md` plus Claude-only behavior; remove unconditional workflow imports. |
| [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands) | `code.claude.com` | Skills are the recommended successor to custom commands, use `SKILL.md`, load on demand, and live at `.claude/skills/` for project scope. Existing `.claude/commands/` remains compatible. | Do not create custom commands; add Claude discovery adapters for the five canonical `.agents/skills` workflows. |
| [Create custom subagents](https://code.claude.com/docs/en/sub-agents) | `code.claude.com` | Subagents are appropriate for verbose, self-contained work or tool restriction; the main conversation is better when phases share context. Skills are preferred for reusable workflows in the main context. | Defer custom architecture-auditor, reviewer, and test-runner definitions until repeated context-noise evidence exists. |
| [Store rules and memory](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules) | `code.claude.com` | `.claude/rules/` is for modular persistent or path-scoped instructions; task-specific procedures belong in skills. | Do not add rules yet; the proposed durable shared rules fit `AGENTS.md`, and procedures fit skills. |
| [Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide) | `code.claude.com` | Hooks provide deterministic lifecycle control and can block or automate actions, while instruction files are behavioral context rather than enforcement. | Add no hook until a fast lifecycle-specific enforcement need cannot be served by an explicit validator or permissions. |
| [Common workflows](https://code.claude.com/docs/en/common-workflows#plan-before-editing) | `code.claude.com` | Plan mode reads and proposes before editing; worktrees isolate parallel sessions; subagents keep large exploration out of the main context. | Recommend plan mode for multi-file/architecture work and prohibit parallel agents editing the same checkout. |
| [Explore the context window](https://code.claude.com/docs/en/context-window) | `code.claude.com` | Root instructions are loaded at startup; skill bodies load when invoked; `/context`, `/compact`, and `/clear` support context management. | Avoid importing large workflow manuals into every Claude session; keep skills concise and on demand. |

The OpenAI Codex manual helper was attempted first as required by the local OpenAI documentation workflow, but the restricted shell could not resolve `developers.openai.com`. No OpenAI Docs MCP was installed in the session. Installing it would have changed user-level configuration outside this task's allowed write scope, so the research used official OpenAI web documentation only.

## 8. Current Sentinel diagnosis

### 8.1 What the shell script actually does

`scripts/sentinel.sh`:

1. enables `set -eu`;
2. resolves the repository root from the script directory;
3. prints an advisory label and no-network statement;
4. runs `git status --short --branch`;
5. runs default `git diff --check`; and
6. prints the path to `docs/agent-prompts/sentinel-review.md`.

It is executable and `bash -n scripts/sentinel.sh` passes. Its commands are local and non-destructive. It makes no provider or network call and does not read credentials.

### 8.2 What it does not do

It does not:

- execute the LLM review prompt;
- fail merely because the tree is dirty;
- inspect `git diff --cached --check`;
- compare a branch to its base;
- inspect untracked file contents;
- search for secret-like patterns;
- run tests, Ruff, compilation, or shell lint beyond its own invocation;
- validate report storage, agent paths, skill metadata, or documentation links; or
- produce a PASS/PASS WITH NOTES/BLOCKED verdict.

Therefore “Sentinel passed” means only that the invoked deterministic commands exited successfully, principally that the checked unstaged diff had no whitespace errors. Any LLM verdict is separate evidence.

### 8.3 Recommended separation

- **Deterministic check:** move the script body to `scripts/agent/sentinel.sh`, preserve safe local commands, add explicit labels for each checked scope, and keep it advisory.
- **LLM interpretation:** retain a concise optional review rubric as documentation or a skill reference. Never describe it as deterministic enforcement.
- **Human workflow:** explain when to run Sentinel and how to report its evidence in `docs/agents/README.md`.
- **Compatibility:** leave `scripts/sentinel.sh` as a tiny forwarding wrapper for at least one migration phase; update the six documents that invoke the old path and the additional reviewer guide that names Sentinel before removal.
- **Path correction:** a moved script must resolve the root with `../..`, not the current `..`.

## 9. Proposed minimal architecture

```text
AGENTS.md
CLAUDE.md

.agents/
└── skills/
    ├── task-brief/
    ├── safe-refactor/
    ├── docs-update/
    ├── commit-review/
    └── session-handoff/

.claude/
└── skills/
    ├── task-brief -> ../../.agents/skills/task-brief
    ├── safe-refactor -> ../../.agents/skills/safe-refactor
    ├── docs-update -> ../../.agents/skills/docs-update
    ├── commit-review -> ../../.agents/skills/commit-review
    └── session-handoff -> ../../.agents/skills/session-handoff

scripts/
└── agent/
    ├── sentinel.sh
    └── validate-agent-tooling.sh

docs/
└── agents/
    └── README.md
```

The `.claude/skills/` entries are the only addition to the original hypothesis. On this macOS repository, symlinked skill directories are the smallest no-duplication adapter. They must be tested in Claude Code before legacy names are removed. If Claude's installed version does not resolve the symlinks reliably, use generated mirrors with a validator-enforced canonical source header; do not hand-maintain duplicate bodies.

### 9.1 `AGENTS.md` responsibilities

Keep only durable repository-wide facts and rules:

- a short project and architecture summary;
- source-of-truth hierarchy;
- scope and behavior-preserving change rules;
- architecture boundaries;
- untrusted-input, secrets, and safe-error rules;
- Git authorization and preservation rules;
- validation ladder and evidence language;
- provider-cost guard if it remains a real repository requirement; and
- a concise skill routing table.

Move modes, detailed review loops, prompt templates, handoff schema, commit grouping steps, and lengthy examples out of `AGENTS.md`.

### 9.2 `CLAUDE.md` responsibilities

- Import `@AGENTS.md` using the official mechanism.
- Add only Claude-specific behavior: use plan mode for architectural/multi-file changes; prefer read-only subagents for noisy independent research; never allow parallel agents to edit the same checkout; use separate worktrees for parallel writes; and use `.claude/skills` adapters.
- Point to `docs/agents/README.md` as a literal backticked path, not an `@` import, so human documentation is not loaded on every session.
- Do not import `CODEX_WORKFLOW.md` or `AGENT_HANDOFF.md` after their content is available on demand.

### 9.3 Skill interoperability

The canonical skill bodies should use the shared Agent Skills format: YAML `name` and `description`, concise Markdown instructions, and optional references/scripts. Avoid Codex-only or Claude-only frontmatter in the canonical `SKILL.md`. Put optional OpenAI UI metadata in `agents/openai.yaml`. Put Claude invocation controls only in adapters if eventually needed. This allows one canonical procedure while respecting different discovery directories.

### 9.4 Sentinel and validator

`scripts/agent/sentinel.sh` remains a small advisory preflight. `scripts/agent/validate-agent-tooling.sh` becomes the deterministic structural validator. They should not be combined: Sentinel checks the current change; the validator checks tooling integrity.

### 9.5 Documentation count

One initial `docs/agents/README.md` is enough. It should cover architecture, ownership, Codex use, Claude use, skill triggers, Sentinel, validator commands, common workflows, compatibility/deprecation, and how to add a skill. Additional documents are justified only when a reference is too detailed for a skill body, such as the existing safety/architecture checklist. Prefer skill-local `references/` over more top-level workflow manuals.

## 10. Source-of-truth model

| Information | Canonical owner | Non-owner behavior |
| --- | --- | --- |
| Durable project constraints and Git/security rules | `AGENTS.md` | `CLAUDE.md` imports it; skills may reference but must not restate whole sections |
| Claude-only invocation/context behavior | `CLAUDE.md` | Never copy into `AGENTS.md` unless it is actually shared |
| Reusable procedures | `.agents/skills/<name>/SKILL.md` | Claude adapters expose the same body; docs summarize and link |
| Deterministic checks | `scripts/agent/*.sh` | Docs explain commands; skills call scripts rather than reimplement them |
| Human architecture and maintenance | `docs/agents/README.md` | Root files point to it literally; it is not auto-imported |
| Product architecture/evidence | Product code, tests, and current product docs | Agent docs must not become domain evidence |
| Session/task facts | Current conversation or explicitly requested handoff | Never promote automatically to persistent rules |

When two files disagree, higher-level safety and user instructions still win at runtime, but repository maintenance should treat the table above as the drift-resolution rule.

## 11. Skill migration map

### 11.1 `task-brief`

- **Justified:** Yes. The next frontend audit needs a repeatable contract before exploration or edits.
- **Migrate from:** CXP “Before editing” steps 1–6; pre-implementation prompt; PR workflow planning output; handoff scope/acceptance fields.
- **Trigger:** Ambiguous, architectural, multi-file, audit, refactor, or staged implementation work; explicit request for a brief/plan.
- **Do not trigger:** Trivial mechanical edits with complete acceptance criteria; simple factual questions; commit preparation.
- **Inputs:** Objective, current branch/state, observed problem, acceptance criteria, in/out-of-scope files, constraints, known evidence.
- **Outputs:** Facts versus assumptions, architecture/dependency inventory plan, invariants, file scope, validation plan, risks, rollback point, approval boundary.
- **Safety:** Read-only by default; no implementation, staging, provider calls, or dependency changes without explicit task authorization.
- **Shared implementation:** Yes; canonical `.agents` body with Claude discovery adapter.

### 11.2 `safe-refactor`

- **Justified:** Yes. It is the critical workflow for behavior-preserving frontend extraction and test migration.
- **Migrate from:** `CODEX_WORKFLOW.md` refactoring/minimal-fix rules; CXP implement/debug and browser-evidence distinctions; safety architecture checklist; CQM behavior-preservation content.
- **Trigger:** Extraction, module split, dependency untangling, test migration, or behavior-preserving architecture changes.
- **Do not trigger:** New features, visual redesign, pure docs work, or broad speculative cleanup.
- **Inputs:** Approved task brief, dependency map, current behavior/invariants, characterization tests, permitted phase, manual/browser acceptance checks.
- **Outputs:** One small extraction phase, exact files, behavior contract, test movement/additions, focused/full validation ladder, diff review, rollback point.
- **Safety:** No redesign, no opportunistic cleanup, no parallel writes in one checkout, no claim of browser behavior from unit/AppTest evidence alone.
- **Shared implementation:** Yes; keep optional checklist under `references/`.

### 11.3 `docs-update`

- **Justified:** Yes. Current docs already need factual synchronization after engineering changes.
- **Migrate from:** All unique `capstone-doc-edit` rules plus documentation honesty rules from `AGENTS.md`.
- **Trigger:** Updating README, architecture, validation, status, developer, or reviewer documentation after verified changes.
- **Do not trigger:** Product prompt editing, code comments, generated handoffs, or unverified roadmap writing.
- **Inputs:** Verified code/test evidence, implemented behavior, current limitations, future work, target audience and files.
- **Outputs:** Small factual diff, implemented/limited/future separation, links/claims needing verification, validation performed.
- **Safety:** Do not invent features, exact test results, readiness, or provider behavior; current code and tests outrank historical docs.
- **Shared implementation:** Yes. Capstone-specific reviewer tone should remain in product docs, not the skill core.

### 11.4 `commit-review`

- **Justified:** Yes. Reviewed commits and explicit authorization are roadmap requirements.
- **Migrate from:** `capstone-commit-review`, `AGENTS.md` commit workflow, PR preflight scope rules, and built-in `/review` handoff.
- **Trigger:** User asks for commit readiness, grouping, staging paths, or proposed commit messages.
- **Do not trigger:** Ordinary implementation completion unless commit planning is requested; never auto-trigger a commit.
- **Inputs:** Complete status, unstaged/staged diffs, validation evidence, manual checks, explicit task scope.
- **Outputs:** File/hunk groups, P1/P2 blockers, exact `git add -- <paths>` suggestions, order/dependencies, messages, files to leave uncommitted, authorization question.
- **Safety:** Read-only; never stage, commit, push, amend, reset, rebase, squash, or clean. Re-plan if files/messages change after approval.
- **Shared implementation:** Yes. Keep tool-specific commit execution outside the skill until explicit authorization.

### 11.5 `session-handoff`

- **Justified:** Yes. Frontend migration will span sessions and potentially tools.
- **Migrate from:** `AGENT_HANDOFF.md` packet; CXP handoff fields for changes, architecture, scope, risk, validation, Git state, and readiness.
- **Trigger:** User asks for a handoff, work is pausing, context must transfer tools/sessions, or a task is blocked with useful verified state.
- **Do not trigger:** Every completed trivial task; it must not create a file automatically on all work.
- **Inputs:** Objective, verified findings/decisions, current Git state, exact scope, validation, risks, unresolved questions, authorization state.
- **Outputs:** Concise factual packet plus an exact next prompt/action; optional file only at a user-approved path.
- **Safety:** No secrets, transcripts, huge diffs, stale test claims, or implied edit authorization. Handoff does not authorize commits or edits in a new session.
- **Shared implementation:** Yes; remove hard-coded Claude-versus-Codex role stereotypes.

## 12. Frontend-audit readiness analysis

| Required next workflow step | Coverage in target tooling | Gap or evidence requirement |
| --- | --- | --- |
| 1. Generate a precise task brief | `task-brief` | Must record frontend visual/non-visual scope and protected product areas |
| 2. Run read-only architecture inventory | `task-brief` plus optional read-only built-in subagent | Must map `app.py` responsibilities, imports/calls, state keys, CSS/JS coupling, tests, and runtime evidence without editing |
| 3. Create behavior-preserving extraction plan | `safe-refactor` | Must capture invariants and characterize current behavior before moving code |
| 4. Implement one small phase | `safe-refactor` | Requires explicit approval and exclusive file ownership in one checkout |
| 5. Run focused and complete validation | `safe-refactor`, Sentinel, project validation ladder | Needs a documented frontend command matrix and browser/manual acceptance evidence; no new skill is necessary |
| 6. Review staged scope | `commit-review` plus built-in `/review` | Must inspect both staged and unstaged state and base-branch scope |
| 7. Commit only with explicit authorization | `AGENTS.md` and `commit-review` | Authorization remains a user action, not a skill outcome |
| 8. Generate factual session handoff | `session-handoff` | Must distinguish verified facts, assumptions, skipped checks, and next action |

The only missing capability is not another skill: it is a deterministic, documented frontend validation matrix. During the frontend-audit planning task, capture the exact focused tests, full suite, Ruff, compile, diff, Streamlit startup, and real-browser checks that correspond to each extraction phase. Store stable commands in `docs/agents/README.md` or a skill-local reference only after the audit establishes them.

Test migration belongs inside `safe-refactor`: move tests only with the behavior they protect, retain characterization coverage during extraction, and remove obsolete tests only after the new boundary is proven. Dependency mapping belongs in the `task-brief` output, not a new dependency-mapper skill.

## 13. Subagent decision

| Candidate | Context noise removed | Why a skill alone might be insufficient | Required safety | Decision |
| --- | --- | --- | --- | --- |
| `architecture-auditor` | Large file reads, `rg` results, dependency traces | A separate context can return a compact module/state/dependency map | Read-only tools; no file edits; explicit directory exclusions | Defer custom definition. Use the main task brief or a one-off built-in Explore/Plan subagent only when the frontend inventory proves too noisy. |
| `code-reviewer` | Large diffs and repeated review notes | Isolation can keep review findings out of implementation context | Read-only diff access; no fixes; P1/P2/P3 rubric | Defer. Codex `/review`, Claude review features, and `commit-review` already cover the recurring need. |
| `test-runner` | Verbose test logs and stack traces | Context isolation is useful when suites are long or flaky | May run deterministic local tests; no code edits, installs, network, or credential output | Defer. Direct scripts are simpler now; create only after repeated log-volume problems. |

No autonomous implementation agent should be added. If future parallel agents write, each must use an isolated worktree and explicit non-overlapping scope. Read-only agents may share a checkout, but their results still need synthesis against the canonical task brief.

## 14. Hook decision

Recommend **no Claude hooks now**.

The proposed validator and Sentinel are explicit, deterministic, local, fast, reviewable, and shared by both tools. A Claude-only hook would add another configuration surface before a concrete lifecycle gap exists. Instruction files are advisory, but current Git mutations are also governed by Claude/Codex permissions and explicit authorization rules.

A hook becomes justified only if all of these are true:

1. a recurring unsafe action occurs despite concise instructions and permissions;
2. enforcement must happen before or immediately after a specific tool lifecycle event;
3. the check is deterministic, fast, local, and non-destructive; and
4. the explicit validator cannot provide equivalent protection more simply.

Any future hook must make no network call, inspect no credential values, modify no product file, and never stage, commit, push, install, delete, or clean Git state. Prefer a `PreToolUse` denial for one precisely matched destructive command over broad command parsing.

## 15. Complete legacy-file migration table

| Current path | Unique content worth preserving | Duplicate content | New owner | Proposed target | Action | Compatibility risk and references | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Durable architecture, security, Git authorization, validation, environment constraints, provider guard | Modes, workflows, CQM wording, review loops repeated elsewhere | Shared instructions | `AGENTS.md` | Rewrite incrementally | High: Codex auto-loads it; preserve semantics and verify discovery | 1–2 |
| `CLAUDE.md` | Correct `@AGENTS.md` import | CQM reminder and imported Codex/handoff procedures | Claude adapter | `CLAUDE.md` | Rewrite | Medium: Claude startup context changes; verify with `/context` | 1 |
| `.agents/skills/cxp/SKILL.md` | Scope map, sensitive-file gate, browser evidence distinction, handoff fields | General implementation, validation, Git safety | Three canonical skills | `task-brief`, `safe-refactor`, `session-handoff` | Merge, then replace with pointer | High: named in `AGENTS.md`, explicit `$cxp` users, `.cxp` output expectation | 3 |
| `.agents/skills/cxp/agents/openai.yaml` | UI metadata pattern | None | New skill metadata | Optional per-skill `agents/openai.yaml` | Replace | Low: UI display/default prompt only | 3 |
| `.agents/skills/capstone-doc-edit/SKILL.md` | Fact/limitation/future split, current-session evidence standard | General documentation honesty | `docs-update` | `.agents/skills/docs-update/SKILL.md` | Merge, then pointer | Medium: old explicit skill name may be used externally | 3 |
| `.agents/skills/capstone-commit-review/SKILL.md` | Read-only grouping, exact paths, secret/generated warnings | Git rules and validation repeated in `AGENTS.md` | `commit-review` | `.agents/skills/commit-review/SKILL.md` | Merge, then pointer | Medium: old skill name; ensure no automatic commit behavior | 3 |
| `docs/agent-prompts.md` | PR writer format and comment-fix scope contain small reusable fragments | Most planning, implementation, review, OCG, CQM, and validation text | Skills + human docs | Five skills and `docs/agents/README.md` | Merge; pointer; remove later | Medium: `agentic-pr-workflow.md` links it; copy/paste users may rely on headings | 5 |
| `docs/agent-prompts/safety-architecture-review.md` | Detailed optional security/RAG/tool checklist | General scope, errors, architecture, testing | `safe-refactor` reference | `.agents/skills/safe-refactor/references/safety-architecture-review.md` | Move later with pointer | Medium: `AGENTS.md` explicitly references current path | 3/5 |
| `docs/agent-prompts/sentinel-review.md` | PASS rubric and advisory review categories | Git/scope/secrets/validation repeated elsewhere | Sentinel interpretation guidance | Skill-local/reference location chosen in Phase 4 | Rewrite and move later | High: script prints exact path; report location conflicts | 4 |
| `docs/agentic-pr-workflow.md` | End-to-end PR role sequence and AI disclosure text | Scope, implementation, audit, validation, commit flow | Human README + focused skills | `docs/agents/README.md`, `task-brief`, `commit-review` | Merge; pointer; remove later | Medium: links from prompt library and human habits; contains push examples | 5 |
| `docs/AGENT_HANDOFF.md` | Objective/findings/state/scope/criteria/validation/uncertainty packet | Roles, approval, validation duplicated | `session-handoff` | `.agents/skills/session-handoff/SKILL.md` | Merge; pointer; remove later | High: imported by Claude and referenced by AGENTS/workflow | 3/5 |
| `docs/CODEX_WORKFLOW.md` | Minimal-fix, closure, refactor, validation, short-mode patterns | Modes and nearly all durable rules repeated in AGENTS/prompts | Skills + human README | Five skills and `docs/agents/README.md` | Merge; pointer; remove later | High: AGENTS and CLAUDE reference/import it | 2/5 |
| `scripts/sentinel.sh` | Safe root resolution, status, diff check, advisory label | Some validation commands documented elsewhere | Deterministic scripts | `scripts/agent/sentinel.sh` | Move body; keep forwarding wrapper; remove wrapper later | High: six known docs invoke the old path and one additional guide names Sentinel; root calculation changes after move | 4/6 |
| `CLAUDE_COGNIVIA_CHAT_FORM_ARCHITECTURE.md` | Historical form-first product ideas if still relevant | Architecture planning and frontend freeze are stale/repeated | Product history, not agent tooling | Optional historical archive outside canonical agent docs | Archive or remove later | Low agent risk; product owner must confirm unique roadmap value | 5 or separate task |
| `.claude/settings.local.json` | Personal command approvals | Not shared | User-local Claude configuration | Remain local | Keep; narrow separately | No tracked references; global ignore; broad Python stdin permission | Outside migration |
| `.gitignore` (`.cxp/`) | Keeps generated CXP handoff local | Becomes obsolete after CXP retirement | Repository ignore policy | `.gitignore` | Keep initially; remove entry later only if directory retired and empty | Low; avoid accidental tracking during compatibility window | 6 |
| `.codex-reports/**` | Historical local reports only | Repeated task histories | No canonical owner | None | Retain locally or remove separately | Not tracked; ignore is checkout-local, so never make canonical references depend on it | Outside migration |
| `README.md` | Product validation command | Sentinel path only | Product docs | Same path | Keep; update reference | Must remain factual about advisory scope | 5 |
| `PROJECT_STATUS.md` | Historical validation evidence | Sentinel path/status | Historical status docs | Same path | Keep; update only if current-facing | Avoid rewriting historical claims as current evidence | 5 |
| `docs/architecture.md` | Product validation architecture | Sentinel path only | Product docs | Same path | Keep; update reference | Current-facing source; coordinate docs skill | 5 |
| `docs/capstone-reviewer-guide.md` | Reviewer validation map | Sentinel label only | Product docs | Same path | Keep; update reference/wording if needed | Capstone-specific content remains product-owned | 5 |
| `docs/current-state-validation-and-next-steps.md` | Product state and validation | Sentinel path only | Product docs | Same path | Keep; update reference | Do not claim new validation without rerun | 5 |
| `docs/smoke-test-checklist.md` | Manual product checks | Sentinel path only | Product docs | Same path | Keep; update reference | Update exact command after compatibility period | 5 |
| `docs/change-plans/002-openai-provider-support.md` | Historical provider plan and CXP note | CXP/Sentinel references | Historical change plan | Same path | Keep historical or add note; do not rewrite as current workflow | Low; distinguish historical instructions | 5 |

No legacy file should be deleted in the same phase that introduces its replacement. Keep compatibility pointers through at least one successful Codex and Claude smoke session.

## 16. Ordered implementation phases

Repository evidence supports **six** phases. A small bootstrap phase comes before the proposed wholesale instruction rewrite because it creates an ownership map without removing any working path.

### Phase 1 — Source-of-truth bootstrap

- **Goal:** Declare ownership and make Claude's adapter minimal without moving legacy content.
- **Create:** `docs/agents/README.md` with ownership, current paths, compatibility status, and planned skill names.
- **Modify:** `AGENTS.md` minimally to declare the source-of-truth hierarchy and canonical docs pointer; `CLAUDE.md` to import only `@AGENTS.md` and add Claude-specific plan/subagent/worktree rules.
- **Remove/replace later:** Nothing.
- **Compatibility:** Keep all legacy docs and skill names. `AGENTS.md` continues pointing to them where needed.
- **Validation:** Baseline/status; instruction-path existence; Codex instruction summary; Claude `/context`; `git diff --check`; complete diff review.
- **Risk:** Low to medium; Claude startup context becomes smaller, while Codex semantics stay intact.
- **Rollback point:** Revert only these three documentation/instruction files.
- **Suggested commit:** `docs(agents): establish shared tooling source of truth`

### Phase 2 — Concise shared instruction foundation

- **Goal:** Reduce `AGENTS.md` to durable rules while preserving behavior and remove remaining workflow imports/repetition.
- **Create:** None beyond Phase 1.
- **Modify:** `AGENTS.md`, `CLAUDE.md`, `docs/agents/README.md`.
- **Remove/replace later:** None; legacy workflows remain available as references.
- **Compatibility:** Add a mapping from each removed AGENTS procedure to its still-existing legacy location or upcoming skill.
- **Validation:** Diff semantic checklist for every durable rule; Codex discovery; Claude import; path/link check; validator prototype command list reviewed manually.
- **Risk:** Medium; accidental loss of a safety or validation rule.
- **Rollback point:** Phase 1 commit.
- **Suggested commit:** `refactor(agents): separate durable rules from procedures`

### Phase 3 — Shared skill migration and Claude adapters

- **Goal:** Add the five focused canonical skills and expose them to both tools.
- **Create:** Five `.agents/skills/*` directories; optional skill references/metadata; five `.claude/skills/*` symlink adapters.
- **Modify:** `AGENTS.md`, `CLAUDE.md`, `docs/agents/README.md`; old skill files only to become explicit compatibility pointers after smoke tests.
- **Remove/replace later:** No immediate deletion. Old `cxp` and `capstone-*` names remain for one compatibility window.
- **Compatibility:** Old names explain replacements and do not duplicate canonical bodies; CXP handoff behavior is opt-in during transition.
- **Validation:** Frontmatter parse; unique names; trigger/non-trigger prompt matrix; Codex `/skills`; Claude `/skills`; symlink resolution; no implicit commit/handoff writes.
- **Risk:** Medium; trigger collisions, adapter discovery, and users invoking old names.
- **Rollback point:** Phase 2 commit; remove only new skill/adapters if smoke fails.
- **Suggested commit:** `feat(agents): add shared focused workflow skills`

### Phase 4 — Sentinel separation and tooling validator

- **Goal:** Separate deterministic checks from LLM interpretation and add tooling-integrity validation.
- **Create:** `scripts/agent/sentinel.sh`, `scripts/agent/validate-agent-tooling.sh`.
- **Modify:** `scripts/sentinel.sh` into a forwarding wrapper; Sentinel prompt/reference; `docs/agents/README.md`.
- **Remove/replace later:** Old wrapper only after all consumers migrate.
- **Compatibility:** Existing `bash scripts/sentinel.sh` continues to work.
- **Validation:** `bash -n` on scripts; executable bits; clean/dirty/staged/untracked fixtures in temporary Git repos; secret-pattern test values that never print matches; no network/provider access.
- **Risk:** Medium; shell portability, moved-root calculation, false positives, and misleading exit semantics.
- **Rollback point:** Phase 3 commit; wrapper can point back to previous body.
- **Suggested commit:** `chore(agents): separate advisory review and tooling validation`

### Phase 5 — Documentation consolidation and legacy pointers

- **Goal:** Make `docs/agents/README.md` the only human-facing agent architecture guide and update all references.
- **Create:** No additional top-level docs unless a unique reference proves necessary.
- **Modify:** README plus legacy workflow files into concise pointers; all Sentinel consumer paths; historical files only where current claims would otherwise be wrong.
- **Remove/replace later:** Mark `agent-prompts.md`, `agentic-pr-workflow.md`, `AGENT_HANDOFF.md`, and `CODEX_WORKFLOW.md` for removal after compatibility window.
- **Compatibility:** Pointers name canonical replacements and deprecation date/phase; historical product plans remain historical.
- **Validation:** Link/path scan, obsolete-path scan, duplicate-body scan, documentation claim review, `git diff --check`.
- **Risk:** Medium; breaking bookmarked paths or rewriting historical evidence.
- **Rollback point:** Phase 4 commit.
- **Suggested commit:** `docs(agents): consolidate workflows and compatibility guidance`

### Phase 6 — Compatibility smoke checks and closeout

- **Goal:** Prove discovery and commands in both tools, then remove only approved obsolete compatibility artifacts.
- **Create:** None expected.
- **Modify/remove:** Remove old skill pointers, workflow pointers, Sentinel wrapper, or `.cxp/` ignore only after explicit file-by-file approval and successful smoke evidence.
- **Compatibility:** One final inventory confirms no remaining references before deletion.
- **Validation:** Fresh Codex session instruction/skill discovery; fresh Claude `/context` and `/skills`; all scripts; link validator; obsolete path scan; full Git status/diff review; independent `/review`.
- **Risk:** Highest deletion risk despite no product code; old external habits may not be visible in repository search.
- **Rollback point:** Phase 5 commit; restore a pointer rather than reconstructing content.
- **Suggested commit:** `chore(agents): complete tooling compatibility migration`

## 17. Exact first implementation phase

Implement **Phase 1 — Source-of-truth bootstrap** next and nothing else.

### Exact files

- **Create `docs/agents/README.md`:** State that `AGENTS.md` owns shared durable rules, `CLAUDE.md` is the Claude adapter, current `.agents/skills` are Codex-discovered workflows, current legacy docs remain authoritative only for the procedures explicitly named, Sentinel is advisory, and the five target skills are planned but not yet available.
- **Modify `AGENTS.md`:** Add a short source-of-truth section and literal pointer to `docs/agents/README.md`. Do not delete or rewrite existing rules in this phase. Clarify that state-changing Git commands require explicit authorization even if a legacy workflow lists them.
- **Modify `CLAUDE.md`:** Retain `@AGENTS.md`; remove unconditional imports of `CODEX_WORKFLOW.md` and `AGENT_HANDOFF.md`; add only Claude-specific directions to use plan mode for architecture/multi-file work, prefer read-only subagents for independent noisy research, prohibit parallel editing in the same checkout, require worktree isolation for parallel writes, and consult the literal `docs/agents/README.md` path when agent-tooling details are needed.

### Legacy files left untouched

Leave every `.agents/skills/*` file, every `docs/agent-prompts*` file, `docs/agentic-pr-workflow.md`, `docs/AGENT_HANDOFF.md`, `docs/CODEX_WORKFLOW.md`, `scripts/sentinel.sh`, `.gitignore`, and all product files untouched.

### Validation commands

```bash
git status --short --branch
git diff --check
git diff --stat
git diff -- AGENTS.md CLAUDE.md docs/agents/README.md
rg -n 'AGENTS\.md|CLAUDE\.md|CODEX_WORKFLOW|AGENT_HANDOFF|docs/agents/README\.md' \
  AGENTS.md CLAUDE.md docs/agents/README.md
codex --ask-for-approval never "List the repository instruction sources and summarize their ownership."
```

In a fresh Claude Code session, run `/context` and confirm that `CLAUDE.md` plus imported `AGENTS.md` load, while the two legacy workflow documents do not load automatically. Then ask Claude to summarize the agent-tooling ownership without editing.

Expected commit message after validation and separate commit authorization:

```text
docs(agents): establish shared tooling source of truth
```

## 18. Tooling validator design

`scripts/agent/validate-agent-tooling.sh` should eventually be POSIX-conscious Bash for the current macOS environment, use repository-relative paths, make no network calls, and print paths/categories but never matching secret values.

It should validate:

1. expected root files, canonical skill directories, scripts, and README exist;
2. every canonical skill directory contains `SKILL.md`;
3. frontmatter is bounded by `---` and contains non-empty `name` and `description`;
4. skill names are unique across canonical bodies and compatibility adapters;
5. canonical names match directory names unless a documented exception exists;
6. Markdown links and literal canonical paths resolve;
7. no obsolete paths remain outside approved compatibility pointers;
8. scripts have executable permission and pass `bash -n`;
9. compatibility symlinks resolve inside the repository to canonical skills;
10. no two files contain duplicated canonical instruction bodies;
11. `CLAUDE.md` imports `AGENTS.md` exactly once and does not import large workflow manuals;
12. `AGENTS.md` and `CLAUDE.md` point to the canonical README without circular imports;
13. Sentinel is labeled advisory and does not imply it invokes an LLM;
14. likely secret patterns are reported by filename and rule only, never by line content or value; and
15. the validator itself performs no writes, staging, commits, cleanup, installs, or network access.

Recommended exit semantics: `0` for all structural checks passing, `1` for validation failures, and `2` for validator misuse or an internal/tooling error. Warnings that are intentionally non-blocking must be labeled separately and must not produce a false “pass.”

## 19. Validation strategy for the migration

Use a layered ladder:

1. **Structural:** expected paths, frontmatter, unique names, links, symlinks, executable bits, shell syntax.
2. **Discovery:** fresh Codex session reports root instructions and five skills; fresh Claude session `/context` and `/skills` report the adapter plus five skills.
3. **Trigger behavior:** positive and negative prompt matrix for each skill; commit-review and session-handoff must never auto-mutate state.
4. **Deterministic scripts:** clean, dirty, staged, untracked, broken-link, duplicate-name, invalid-frontmatter, and synthetic secret-pattern fixtures in `/tmp` repositories.
5. **Compatibility:** old skill names and `scripts/sentinel.sh` work during the announced window; all references resolve.
6. **Scope:** `git status`, complete diff, staged diff, `git diff --check`, and independent review confirm no product changes.
7. **Closeout:** only after all references are gone and explicit deletion approval exists may compatibility files be removed.

The product test suite is unnecessary for instruction-only phases unless a script changes product validation behavior. Script changes need their own deterministic fixture tests, not provider-backed application tests.

## 20. Risks and rollback strategy

| Risk | Mitigation | Rollback |
| --- | --- | --- |
| Dropping a durable safety rule while shortening `AGENTS.md` | Rule-by-rule semantic checklist and separate foundation phase | Restore prior `AGENTS.md`; no dependent deletion in same phase |
| Claude no longer sees needed procedure automatically | Keep legacy paths, add literal docs pointer and skills before removal | Restore import temporarily |
| Claude adapters do not resolve symlinked skills | Smoke test installed Claude version before pointer conversion | Remove adapters; use generated mirrors or leave legacy Claude access |
| Old skill invocation breaks | Compatibility skill pointers for at least one phase | Restore old skill body from previous commit |
| Sentinel move breaks root/path resolution | Wrapper plus temporary-repository tests; use `../..` | Wrapper points back to prior body |
| Validator exposes a secret | Print only filenames/rule IDs; synthetic fixtures; never echo matches | Disable secret check until safe output is proven |
| Validator becomes a false security claim | Name it structural validation; document limitations | Remove overclaiming checks/docs, keep minimal structural checks |
| Historical docs are rewritten as current claims | Use `docs-update`; distinguish historical evidence from current instructions | Restore historical file and add a pointer/note instead |
| Parallel agents conflict | Read-only default; worktrees for writes; exclusive file ownership | Stop parallel work and return to one checkout/agent |
| Git workflow causes unintended mutation | Central explicit-authorization rule; skills remain read-only until authorized | Stop immediately; never reset/discard automatically; report state |

Each phase should be one reviewable commit only after separate authorization. No phase should combine new canonical content with deletion of its only predecessor.

## 21. Explicit non-goals

This plan does not address:

- frontend architecture or frontend refactoring;
- backend, graph, RAG, memory, provider, schema, or product-prompt refactoring;
- education-provider repository cleanup or public-repository preparation;
- product-code security audit;
- PDF/RAG policy;
- deployment, authentication, user sessions, or long-term memory;
- React, Next.js, or product UI/UX;
- dependency or Python-version changes;
- autonomous implementation agents; or
- a broad hook, MCP, plugin, or agent-team platform.

The historical one-off Claude product prompt is inventoried only because its filename and contents are agent-related; deciding the underlying product architecture remains out of scope.

## 22. Definition of done

This audit phase is done when:

- the full current tooling inventory and discovery map are recorded;
- every relevant persistent tooling file has a migration disposition;
- duplicate, conflicting, stale, unsafe, missing, and portability concerns are explicit;
- official Codex and Claude Code findings have official source links, access date, and supported design decisions;
- Sentinel's deterministic and LLM parts are separated conceptually and remain advisory;
- the minimal shared architecture, Claude adapter requirement, five skills, validator, frontend readiness, subagent decision, and hook decision are specified;
- six ordered phases and one exact low-risk first phase are defined with files, validation, risk, rollback, and commit message;
- only this audit document is changed in the repository;
- the required `/tmp` summary exists and remains untracked; and
- nothing is staged, committed, merged, pushed, renamed, reorganized, or deleted.

Migration implementation is explicitly not part of this definition of done.
