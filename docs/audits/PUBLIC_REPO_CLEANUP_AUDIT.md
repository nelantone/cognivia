# Cognivia Public Repository Cleanup Audit

**Audit date:** 2026-08-19

**Branch audited:** `chore/public-repo-cleanup`

**Scope:** repository identity, educational residue, publication metadata,
privacy/secret paths, targeted Git history, agent tooling, and media/RAG source
precheck.

**Excluded:** product behavior review, full secret scanning, full licensing or
PDF analysis, RAG-content validation, runtime testing, and implementation.

## 1. Executive verdict

**Not safe to publish yet.** The checked-out tree is clean and identical to
`main`, but the repository still identifies itself as an educational
submission through its `origin`, root course briefs, README and reviewer
language, public UI labels, tags/branch names, and historical commits. It also
has no repository license, contains roughly 69 MB of third-party PDFs and 37 MB
of image/video/audio assets without a repository-level rights record, and would
expose personal commit-email metadata if the full history were published.

Finding count: **2 P0, 7 P1, 5 P2, and 3 P3**. The P0 findings are rights
clearance gates, not evidence of infringement. No committed secret was found by
the targeted path and signature searches, and no secret values were inspected.

Current-tree cleanup alone is insufficient for a full-history publication.
A filtered/squashed publication history or equivalent targeted history rewrite
is likely required for course-provided documents and privacy; the final choice
depends on which technical history the author wants to retain and can lawfully
redistribute.

## 2. Current repository identity

Precheck evidence:

- `chore/public-repo-cleanup` and `main` both point to `763791b`.
- `git status --short --branch` was clean before this audit was created.
- `git diff main...HEAD --stat` was empty: there is no product difference from
  `main`.
- Fetch and push `origin` are both
  `<former-submission-repository>`.
- The repository has `requirements.txt`, but no `pyproject.toml`, package author
  metadata, or `LICENSE*` file.
- The README contains no clone URL, repository badge, issue link, or PR link.
- `.github/` contains only `pull_request_template.md`; no CI workflow embeds an
  old repository path.

The current `origin` belongs to an educational submissions organization and
uses an assessment-style repository name. Establishing an author-controlled
publication destination is **required** before this can be treated as an
independent portfolio repository. No remote was changed during the audit.

Repository refs also carry educational context. Local refs include
`backup/local-main-before-capstone-remote`,
`docs/capstone-documentation-consolidation`, and
`sync/capstone-origin-main`; tags include `cognivia-capstone-start` and five
`sprint-*` tags. These do not affect a main-branch-only push, but must not be
published accidentally with `--all` or `--tags` without an explicit retention
decision.

## 3. Educational references inventory

### Direct course/submission material

- `115.md` is a Sprint 1 Interview Practice assignment with evaluation,
  submission, peer/JTL, and institutional review instructions.
- `125.md` is a Sprint 2 advanced-RAG assignment with evaluation and institutional
  submission instructions.
- `AE.CAP_afa.md` is the AI Engineering graded Capstone brief and links to the
  education-provider showcase.
- `135.md` is absent from the current tree but remains in commit `4ab9e31`; it
  is the Sprint 3 agent assignment with course and submission instructions.

These are course-provided briefs rather than Cognivia project documentation.
They should leave the public tree and receive a history/rights decision.

### Current public-facing framing

- `README.md:9,131-152` calls Cognivia a Capstone, routes visitors to a
  Capstone reviewer guide, describes before-submission work, and contains a
  Capstone requirements map.
- `app.py:141,152,2527` exposes `Interview Coach (Sprint 1 legacy)` as a current
  UI mode; `app.py:2052,2087` uses reviewer-oriented labels. Matching assertions
  occur throughout `tests/test_noise_to_signal_app.py`.
- `.github/pull_request_template.md:23-25` requires a Capstone demo explanation
  and reviewer checklist.
- `docs/architecture.md`, `docs/evaluation.md`, `docs/demo-script.md`,
  `docs/smoke-test-checklist.md`, `docs/future-improvements.md`,
  `docs/current-state-validation-and-next-steps.md`, `docs/code-map.md`, and
  `docs/project-evolution.md` frame current behavior or validation around the
  Capstone/reviewer/submission lifecycle.
- `PROJECT_PLAN.md` is explicitly a Sprint 3 historical learning artifact.
  `PROJECT_STATUS.md` is a stale branch closeout record that still defines
  readiness within a local Capstone scope.
- `docs/presentation-outline.md`, `docs/capstone-code-summary.md`, and
  `docs/capstone-reviewer-guide.md` are assessment/presentation artifacts.
- `CLAUDE_COGNIVIA_CHAT_FORM_ARCHITECTURE.md` is a one-off Capstone task prompt.
- `data/knowledge_base/career_sources/curated/human_ai_coding_quality.md:64`
  uses a Capstone-MVP heading; `docs/change-plans/001-durable-learner-memory-mvp.md:104`
  uses Capstone as its scope boundary.

### Legitimate terms that are not residue

`guided-intake`, learning/learner terminology, evidence assessment, normal form
submission helpers, and a focused study sprint are product/domain terms. They
should remain. `docs/refactor/FRONTEND_ARCHITECTURE_AUDIT.md` and tests that use
`submission` for a UI event are also technical, not academic, references.

## 4. File classification

Each row has one primary action. Grouped rows share the same evidence and
recommended treatment.

| Priority | Primary action | Files/items | Evidence and treatment |
| --- | --- | --- | --- |
| P1 | **REMOVE** | `115.md`, `125.md`, `AE.CAP_afa.md` | Course briefs, grading/evaluation requirements, and institutional submission instructions have no ongoing project function. Preserve privately only if the author wants them. |
| P1 | **REWRITE** | `README.md`, `.github/pull_request_template.md`, `app.py`, `tests/test_noise_to_signal_app.py` | Replace Capstone/Sprint/reviewer-facing product identity with independent-project, demo, user, and technical-inspection wording. Do not change behavior while changing UI copy/tests. |
| P1 | **RENAME** | `docs/capstone-reviewer-guide.md` | Retain useful demo, safety, and limitations material under a neutral name such as `docs/demo-guide.md`; remove the requirements map and rewrite educational wording. |
| P2 | **REWRITE** | `docs/architecture.md`, `docs/evaluation.md`, `docs/demo-script.md`, `docs/smoke-test-checklist.md`, `docs/future-improvements.md`, `docs/code-map.md`, `docs/engineering-journey.md`, `docs/project-evolution.md` | Preserve technical content and honest evolution, but replace submission/reviewer/Sprint milestones with release, iteration, evaluation, and portfolio language. |
| P2 | **PRIVATE ARCHIVE** | `PROJECT_PLAN.md`, `PROJECT_STATUS.md`, `CLAUDE_COGNIVIA_CHAT_FORM_ARCHITECTURE.md`, `docs/capstone-code-summary.md`, `docs/current-state-validation-and-next-steps.md`, `docs/presentation-outline.md`, `docs/demo-screenshots/` | Stale closeout data, course planning, speaker notes, assessment evidence, local paths, and historical screenshots are useful personally but create public confusion. |
| P2 | **REWRITE** | `docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md`, `docs/agents/AGENT_TOOLING_AUDIT.md` | Preserve authoritative audits; redact developer-local paths and add durable historical/snapshot labels rather than rewriting their technical conclusions. |
| P2 | **RENAME** | `data/knowledge_base/ai_skill_compass_notes.md` | The current RAG note retains the obsolete Skill Compass brand. Rename neutrally and update references/fingerprints with focused RAG validation. |
| P2 | **REWRITE** | `docs/public_career_skill_sources.md`, `data/knowledge_base/career_sources/README.md`, `data/knowledge_base/career_sources/curated/human_ai_coding_quality.md`, `docs/change-plans/001-durable-learner-memory-mvp.md`, `langsmith_config.py`, `tools/recommendation_explanations.py` | Remove isolated old-brand/Capstone/reviewer wording. Correct the claim that public availability implies public-domain or redistribution rights. |
| P2 | **REMOVE** | `.agents/skills/capstone-doc-edit/`, `.agents/skills/capstone-commit-review/`, matching `.claude/skills/` adapters | Canonical replacements already exist. Remove only after the explicit discovery/compatibility criteria in `docs/agents/VALIDATION.md` pass. Do not rename the wrappers because that would duplicate canonical skills. |
| P2 | **REWRITE** | `AGENTS.md`, `CLAUDE.md`, `docs/agents/README.md`, `docs/agents/SKILL_MIGRATION.md`, `docs/agents/VALIDATION.md`, `scripts/agent/validate-agent-tooling.sh` | After wrapper removal, delete obsolete compatibility references and expected-name checks while preserving canonical tooling ownership. |
| P2 | **REMOVE** | `docs/CODEX_WORKFLOW.md`, `docs/agentic-pr-workflow.md`, `docs/agent-prompts.md`, `docs/agent-prompts/`, `docs/AGENT_HANDOFF.md`, `scripts/sentinel.sh` | These are documented legacy compatibility surfaces. Remove only after their existing removal gates pass and canonical references are verified. |
| P0 | **LICENSE / RIGHTS REVIEW** | Nine tracked PDFs under `data/knowledge_base/career_sources/` and `data/sources/pdfs/` | These are third-party reports, papers, and roadmap visuals (about 69 MB). Publicly downloadable does not establish redistribution rights. Prefer licensed inclusion, links/download tooling, or owner-written summaries. |
| P0 | **LICENSE / RIGHTS REVIEW** | Used Cognivia logos/mascots, Focus Mode icons, `assets/brand/video0.mp4`, and other shipped brand media | At the time of this audit, repository commits showed addition/optimization but not original authorship or license. The later publication remediation recorded owner-supplied provenance separately. |
| P2 | **REMOVE** | Unreferenced alternate logos/mascots/backgrounds and disabled/orphaned `video1.mp4`-`video3.mp4` in `assets/` | Search found many zero-reference variants; the prior UX audit also identifies roughly 28 MB of orphaned decorative media. Confirm no runtime reference, retain only selected masters privately, then remove public duplicates. |
| P2 | **PRIVATE ARCHIVE** | `docs/demo-screenshots/*.png` | Likely owner-created application captures, but primarily presentation/test evidence. Archive unless a curated screenshot is deliberately selected for the portfolio README and passes privacy review. |
| P1 | **LICENSE / RIGHTS REVIEW** | Curated/derived Markdown under `data/knowledge_base/career_sources/` and `data/knowledge_base/derived/` | Likely owner-written summaries with source URLs, but derivation, quotation, attribution, and source terms need the next licensing/RAG audit. |
| P3 | **KEEP** | `docs/refactor/FRONTEND_ARCHITECTURE_AUDIT.md`, `docs/guided-learning-intake.md`, `docs/product/why-cognivia-not-chatgpt.md`, core Python modules/tests where matches are technical | Independent project evidence; matched words describe product learning, guided intake, evidence assessment, or UI submission behavior rather than coursework. |
| P3 | **KEEP** | `.env.example`, `.gitignore`, `.envrc`, `.vscode/settings.json`, `requirements.txt` | Current metadata is public-safe at the inspected level. `.envrc` is a 26-byte source directive with no assignments; `.env.example` documents names/placeholders only. |
| P1 | **HISTORY REVIEW** | Commits/paths listed in section 7, commit author metadata, and removed large assets | Decide between filtered history and a clean publication root before any public push. Do not publish all refs by default. |

## 5. Repository metadata and remotes

**P1 — publication identity:** the only configured remote is the institutional
submission repository. A visitor who sees that URL or a repository transferred
from that namespace will reasonably interpret Cognivia as an educational
submission. The publication repository should live under the author's GitHub
account with a neutral name such as `cognivia`, an intentional default branch,
and a separately approved remote migration.

**P1 — licensing identity:** no root license states what downstream users may
do with the author's code. Add a code license selected by the author only after
separating third-party/course materials; add asset/data notices where licenses
differ. Do not apply the code license indiscriminately to third-party PDFs or
media.

**P3 — portfolio metadata:** no clone command, repository badges, contribution
route, security contact, package metadata, or explicit author/ownership section
exists. These are polish items after identity, rights, and history are settled;
they are not reasons to keep educational framing.

## 6. Secrets and privacy surface

- A local `.env` exists and is ignored by `.gitignore`; its contents were not
  read. Targeted history paths found no committed `.env`.
- Tracked `.env.example` names provider, database, and tracing variables and is
  appropriate as a placeholder/configuration document. No real value was
  inspected or reported.
- Tracked `.envrc` has no assignment/export lines and only sources local
  configuration. It is not a secret-bearing artifact based on this structural
  check.
- `data/vector_store/`, `.venv/`, Python caches, pytest cache, and `.DS_Store`
  files are ignored local artifacts. No tracked local database, log, upload,
  user session, or vector-store artifact was found.
- There is no current user-upload flow. Durable learner memory is PostgreSQL via
  `DATABASE_URL`; public deployment privacy, deletion, tenancy, and stored-user
  data remain out of scope and deferred.
- `PROJECT_STATUS.md` and two tracked audits contained developer-local absolute
  paths. Public copies should use `<local-home>/...` or repository-relative
  paths instead.
- Git history uses two author identities and includes a personal Gmail-domain
  address across 260 commits plus a GitHub noreply domain across four. Review
  whether the personal address is intended to be public; use mailmap, filtered
  history, or a clean publication root if not.
- A targeted history search for common high-confidence key/token/private-key
  signatures returned no matches. This is evidence only for those signatures,
  not a substitute for the later full security audit.

## 7. Targeted Git-history findings

| Priority | Commit/path | Category | Required remediation |
| --- | --- | --- | --- |
| P1 | `b159d05` / `115.md` | Course assignment | Remove from public tree; filter or exclude from publication history unless redistribution is explicitly permitted. |
| P1 | `64f03ef` / `125.md` | Course assignment | Same as above. |
| P1 | `4ab9e31` / `135.md` | Removed course assignment still in history | Current-tree cleanup cannot remove it from full history; filter/exclude or obtain permission. |
| P1 | `f2a178e` / `AE.CAP_afa.md` | Capstone assignment brief | Remove current file and filter/exclude it from public history unless permitted. |
| P1 | `89abddb` | Commit metadata naming a former submission namespace and student slug | Retain only if the educational origin is deliberately disclosed; otherwise use filtered/clean publication history. |
| P1 | `f09adc2` | `Merge capstone remote main` history | Review as part of the publication-history boundary; it reinforces submission identity. |
| P1 | All commits to be published | Personal author email metadata | Confirm consent or rewrite author metadata without printing the address. |
| P2 | Removed assets such as old backgrounds, UX screenshots, legacy logos, and `video4.mp4` | Large/obsolete blobs | Filter for repository size only after the retention and licensing decisions; this is not a secret finding. |

The largest reachable blobs include a 37.9 MB Stanford report, an 18.6 MB WEF
report, an 11.7 MB PwC report, and 5.8-8.9 MB background videos. No historical
`.env` was found; only `.env.example` and the tracked `.envrc` appeared in the
credential-like filename search.

**History verdict:** likely rewrite or clean-root publication is required before
publishing all history, because deleted/current course briefs and personal
author metadata remain reachable. This conclusion is not driven by a known
credential leak. If the author deliberately preserves educational provenance
and secures redistribution rights, selected technical history can remain.

## 8. Agent-tooling legacy findings

The six canonical skills under `.agents/skills/` and the canonical
`scripts/agent/` checks are repository-neutral and should remain. The two
`capstone-*` skill directories and their Claude adapters are explicit-only
compatibility wrappers; their reusable behavior already lives in
`docs-update` and `commit-review`.

`docs/agents/README.md` states that wrapper removal is blocked until fresh
Codex/Claude discovery checks and compatibility criteria in
`docs/agents/VALIDATION.md` pass. That evidence supports **conditional P2
removal**, not immediate deletion. When the gate passes, remove the wrappers,
update `AGENTS.md`, `CLAUDE.md`, validation expectations and migration docs,
then remove the legacy workflow/prompt/Sentinel wrapper surfaces only if their
own references and compatibility checks also pass. Preserve
`docs/agents/AGENT_TOOLING_AUDIT.md` as a historical decision record after
redacting its local path.

## 9. Assets, PDFs, media, and RAG precheck

Current tracked inventory: **9 PDFs (~69 MB), 38 images, 4 videos, and 1 audio
file (~37 MB combined for image/video/audio).**

| Category | Likely provenance | Publication action |
| --- | --- | --- |
| Cognivia logos, mascots, UI icons | Likely owner-created, commissioned, or generated, but repository evidence does not establish which | Record creator/tool/source and rights; retain only final variants. |
| Background PNGs and MP4s; former audio-only asset | Provenance was unresolved at audit time; several visual assets were unused or disabled | Record provenance before publication. The later remediation retained owner-confirmed project visuals and removed the audio-only asset. |
| Demo screenshots | Likely owner-authored captures of Cognivia | Privacy/UI-data review; archive most, intentionally curate at most a small portfolio set. |
| PwC, Coursera, Stanford, WEF and research-paper PDFs | Third-party published works | Do not infer redistribution rights from free access. Verify licenses or replace raw files with source registry/download instructions and owner-written summaries. |
| roadmap.sh visual PDFs | Third-party visual documents | Review copying/redistribution terms; links and summaries are safer until cleared. |
| Curated/derived Markdown | Likely owner-written derivatives of public sources | Review quotations, attribution, transformation, factual provenance, and compatibility with RAG use. |
| Root Sprint/Capstone Markdown | Course-provided material | Remove from public tree and make a history/redistribution decision. |

The full asset/PDF license audit, document-text comparison, metadata extraction,
and RAG source-quality analysis are explicitly deferred.

## 10. Public-portfolio presentation issues

A new visitor currently sees a strong technical project description followed
by a Capstone requirements map, reviewer demo language, stale validation
claims, extensive historical/internal documents, and a live `Sprint 1 legacy`
mode. The repository therefore reads as a polished submission rather than a
focused independent product.

The public hierarchy should eventually become: concise independent README,
architecture, reproducible local setup, evaluation/results with dates, a small
curated demo, security/privacy limitations, source/provenance notices, and an
optional clearly labeled engineering-history narrative. Course instructions,
grading evidence, internal handoffs, stale status snapshots, and redundant
screenshots should not be in that primary path.

The README also has stale current-state claims (for example, Focus Mode is
listed as future although repository status evidence says it is implemented).
This is a separate credibility issue from educational wording and should be
fixed from verified implementation during the final portfolio rewrite.

## 11. P0/P1 publication blockers

| ID | Priority | Finding |
| --- | --- | --- |
| F-01 | P0 | Redistribution rights are unresolved for nine third-party PDFs and derived/source material. |
| F-02 | P0 | Authorship/license/provenance is unrecorded for shipped logos, mascots, video, audio, and other brand media. |
| F-03 | P1 | `origin` is an institutional submission repository, not an author-controlled portfolio destination. |
| F-04 | P1 | Three current root files are course/Capstone assignment briefs. |
| F-05 | P1 | README, docs, PR template, current UI labels, and matching tests frame Cognivia as Capstone/Sprint/reviewer work. |
| F-06 | P1 | The repository has no code license or scoped third-party asset/data notices. |
| F-07 | P1 | Full Git history exposes current/deleted course material and institution-specific merge identity; current-tree deletion alone is insufficient. |
| F-08 | P1 | Full history exposes a personal Gmail-domain commit address; consent or metadata remediation is required. |
| F-09 | P1 | Stale internal status/planning/audit documents expose local paths and obsolete branch/test context, confusing public project status. |

## 12. P2/P3 cleanup

| ID | Priority | Finding |
| --- | --- | --- |
| F-10 | P2 | Legacy `capstone-*` agent wrappers and duplicated workflow surfaces remain, with evidence-based compatibility gates not yet recorded as passed. |
| F-11 | P2 | Course planning, presentation notes, closeout status, and demo screenshots belong in a private archive or a deliberately curated history. |
| F-12 | P2 | Numerous alternate/unused brand assets and retired historical blobs add size and dilute the current product identity. |
| F-13 | P2 | Local runtime hygiene relies on narrow ignores; confirm a clean clone cannot add `.env.*`, local DB/log/upload/session, cache, or vector-store output accidentally while preserving `.env.example`. |
| F-14 | P2 | Educational local branches/tags should be retained privately or pushed selectively, never published accidentally with all refs. |
| F-15 | P3 | Add optional package/project author metadata only if packaging or contributor ergonomics warrants it. |
| F-16 | P3 | Add a clone URL, status badges, issue/contribution route, and security contact after the personal repository exists. |
| F-17 | P3 | Preserve a concise, neutral engineering-evolution narrative; disclose educational origin only if the author chooses, without making assessment milestones the project taxonomy. |

## 13. Ordered cleanup phases

| Phase | Objective | Files/categories and strategy | Risk | Validation | Suggested commit message |
| --- | --- | --- | --- | --- | --- |
| 1. Repository identity | Establish the author-controlled publication destination and ref policy. | No file edits initially. Create/approve the personal `cognivia` destination, decide transfer versus new clean repo, decide which branches/tags/history will publish, and update remotes only with explicit authorization. | Pushing to the wrong namespace or accidentally publishing all refs. | `git remote -v`; destination ownership/default-branch check; dry review of refs; no push during setup. | N/A — remote configuration is not a repository commit. |
| 2. Course material and wording | Remove direct assignments and neutralize current user-facing educational identity. | Remove `115.md`, `125.md`, `AE.CAP_afa.md`; rewrite UI labels and matching tests; rename/rewrite the Capstone reviewer guide; update PR template and direct links. Defer full README information architecture to phase 7. | Broken links, widget-copy test failures, accidental product behavior change. | Targeted link search; focused UI-copy/AppTests; Ruff/compile for changed Python; complete diff review. | `chore(repo): remove educational submission framing` |
| 3. Legacy docs/tooling | Retire Capstone wrappers and duplicated agent surfaces after compatibility gates. | Run documented discovery checks; remove explicit wrappers and legacy docs/scripts only when gates pass; update canonical tooling references. | Breaking Codex/Claude discovery or old automation paths. | `bash scripts/agent/validate-agent-tooling.sh`; focused agent-tooling tests; Sentinel; reference search. | `chore(agent): retire capstone compatibility tooling` |
| 4. Current-tree privacy | Remove/archive stale internal records and harden ignore rules. | Move listed status/planning/prompt/screenshot artifacts to a private archive outside the public repo; redact retained audit paths; broaden safe ignores without hiding `.env.example`. | Losing useful technical evidence or accidentally ignoring a required artifact. | Fresh-clone/status simulation; ignored-file checks; path/email/secret scanner with redacted output; link check. | `chore(repo): sanitize private development artifacts` |
| 5. Publication history | Build the minimum filtered or clean-root history approved by the author. | Filter course briefs, unwanted personal email metadata, and obsolete large blobs, or create a clean publication root while retaining a private archival clone. | Irreversible commit IDs, broken tags, lost attribution, collaborator disruption. | Work in a disposable mirror; compare retained tree/tags; secret/history scan; author-map review; size report; no force-push without separate approval. | `chore(repo): establish public publication history` (only for a clean-root import; filtering itself rewrites commits). |
| 6. Assets/PDF/licensing | Clear or exclude every non-code artifact and RAG source. | Complete license/provenance matrix; remove raw third-party PDFs when rights are not explicit; prefer registry/download tooling and summaries; retain only selected brand assets. | Broken RAG fixtures, attribution loss, incompatible licenses. | PDF/source registry check; RAG loader/retriever tests; asset-reference check; notices/license review. | `chore(assets): align public sources and media rights` |
| 7. README/portfolio | Present Cognivia as an independent Applied AI project. | Rewrite README hierarchy, ownership, setup, current capabilities, dated evaluation evidence, architecture links, limitations, license/notices, and curated demo media. | Overclaiming current behavior or duplicating stale docs. | Verify every claim against code/current evidence; link check; safe offline setup smoke if separately authorized. | `docs: present Cognivia as an independent Applied AI project` |
| 8. Final public audit | Prove the exact repository/refs intended for publication are safe. | Repeat current-tree, history, secrets/privacy, rights, link, metadata, and ref audits on the candidate public repository. | False confidence from checking only the working tree. | Clean status; diff review; Sentinel; agent validator if applicable; history secret scan; license matrix complete; inspect remote and refs; no product test suite unless changed scope requires it. | `docs: record public repository readiness` |

## 14. Exact first implementation phase

**Phase 1 is repository identity and publication-boundary selection.** Before
deleting or rewriting files, the author should create or approve an
author-controlled GitHub repository named `cognivia` (or another neutral final
name), choose whether publication uses filtered history or a clean root, and
list the exact branch/tag refs allowed to publish. Keep the current institutional
remote as read-only archival provenance only if desired, under a clearly named
non-`origin` remote; set the personal destination as `origin` only after exact
authorization. Validate ownership, URL, default branch, and ref allowlist, but
do not push in the same step.

This phase has no source-file change and therefore no commit. Its output is an
approved destination URL and publication-history/ref decision that constrains
all later cleanup.

## 15. Deferred to security, licensing, and RAG audits

- Full secret scanning of every historical blob/ref and any provider credential
  rotation decision; this audit used targeted filenames and signatures only.
- Inspection of real local `.env` values or any external provider/account.
- Commit-by-commit personal-data review beyond author email domains and known
  local paths.
- License text/terms for every PDF, roadmap visual, brand image, mascot, icon,
  video, audio file, generated asset, screenshot, prompt, and course document.
- PDF metadata/text comparison, quotation analysis, and whether owner-written
  summaries are sufficiently transformative and attributed.
- RAG source trust, prompt-injection handling, freshness, source-role policy,
  dataset bias, evaluation validity, and whether raw PDFs are required at
  runtime.
- Public deployment security: authentication, multi-user isolation, memory
  retention/deletion, database access, uploads, logs, telemetry, LangSmith, and
  privacy notices.

## 16. Definition of safe to make public

Cognivia is safe to make public when all of the following are true:

1. The publication remote is author-controlled, neutral, verified, and the
   exact branches/tags to publish are allowlisted.
2. All P0/P1 findings in this audit are closed with evidence.
3. Course briefs and assessment-only artifacts are absent from the public tree;
   retained project history is intentional, accurately labeled, and lawful.
4. A code license exists, and third-party/data/media notices clearly scope what
   the code license does not cover.
5. Every published PDF, dataset/summary, image, video, audio file, prompt, and
   screenshot has documented provenance and redistribution permission, or is
   excluded.
6. The exact history and refs to publish pass a full secret/privacy scan; author
   email exposure is intentional; no local `.env`, database, logs, caches,
   uploads, sessions, reports, or local paths are included.
7. README and primary docs describe verified current behavior as an independent
   Applied AI project, with dated limitations and no stale grading/submission
   hierarchy.
8. Canonical agent tooling validates, legacy removal gates are respected, the
   candidate tree is clean/unstaged, Sentinel passes for the intended scope,
   and the final diff/ref inventory contains only approved publication content.
