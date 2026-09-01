# Public Repository Migration

## Goal

Create an independent, author-controlled Cognivia portfolio repository.

## Publication strategy

Preserve useful real development history through a later one-time sanitized
history rewrite. The publication repository will not expose the complete
educational history and will not collapse Cognivia into one synthetic initial
commit.

## Source-of-truth audit

The evidence, priorities, and final safety gate are defined in the
[Public Repository Cleanup Audit](PUBLIC_REPO_CLEANUP_AUDIT.md).

## Phases

| Phase | Status | Objective | Evidence/decision |
| --- | --- | --- | --- |
| Current-tree institutional cleanup | Implemented in this phase | Remove course-only artifacts and neutralize narrow repository-facing submission wording. | Removed the three audit-confirmed root course briefs; README and PR template no longer present Cognivia as a submission. |
| Product educational-copy cleanup | Implemented in Phase 2 | Remove clearly educational user-visible labels without changing behavior. | Removed the Sprint/legacy qualifier from Interview Coach and the former reviewer audience qualifier from diagnostic expanders; directly coupled tests preserve the same mode dispatch and rendering checks. |
| Legacy tooling cleanup and CXP recovery | Implemented in Phase 3 plus focused recovery | Retire the two obsolete Capstone aliases while preserving project-owned tooling. | The cleanup removed all three wrappers after its compatibility gate. Ownership was later reassessed: CXP was restored as an explicit-only project orchestration utility; both Capstone aliases remain deleted. |
| Documentation consolidation | Pending | Retain useful technical history while removing, archiving, renaming, or neutrally rewriting educational documentation. | The audit classification remains authoritative; no broad documentation rewrite occurred in this phase. |
| Security/privacy | Pending | Clear current-tree and publication-history secret and personal-data risks. | Targeted audit evidence exists; full publication scan and personal commit-metadata decision remain deferred. |
| Assets/PDF/licensing | Pending | Establish provenance and redistribution rights or exclude affected material. | Nine PDFs and repository media remain unchanged pending the dedicated audit. |
| Publication allowlist | Pending | Approve the exact branch, tags, paths, and other refs allowed into the public repository. | Publication will be selective; no branch, tag, or remote changed in this phase. |
| History sanitization | Pending | Create the one-time publication history while retaining useful main development chronology. | Run only after cleanup, privacy, and licensing decisions are complete. |
| Clean-clone validation | Pending | Validate the rewritten candidate as a fresh clone with only approved refs and files. | Requires the disposable rewritten publication candidate. |
| Publication | Pending | Create and publish the author-controlled Cognivia repository. | The existing institutional submission remote remains unchanged until separately authorized. |

## History policy

- Do not rewrite history until current-tree cleanup and licensing decisions are
  complete.
- Preserve the original repository separately.
- Perform the publication rewrite on a disposable copy.
- Retain useful main development chronology.
- Exclude known course, private, and unredistributable material from the
  publication history.
- Expect rewritten commit hashes.

## Current cleanup decisions

- Removed the course-only `115.md`, `125.md`, and `AE.CAP_afa.md` briefs from
  the current tree after confirming that no runtime or independent-project file
  referenced them.
- Reworded only the README's explicit Capstone/submission/reviewer framing;
  technical behavior, setup, and limitations remain unchanged.
- Reworded the pull-request template's Capstone/reviewer headings as neutral
  demo and maintainer headings.
- Neutralized the remaining product-facing educational copy in `app.py`: the
  Interview Coach mode no longer carries a Sprint/legacy qualifier, and
  diagnostic expanders no longer address former educational reviewers.
- Updated only the directly coupled product-copy assertions; widget keys,
  ordering, callbacks, session state, provider payloads, prompts, and dispatch
  targets remain unchanged.
- Retained legitimate product/domain terminology, including "Focused study
  sprint," internal submission and assessment names, and general reviewer
  language used for answer verification.
- Completed the agent-skill compatibility gate and removed three Codex wrappers
  and Claude adapters. A focused recovery later restored project-owned CXP, its
  explicit-only metadata and adapter, validation coverage, and ignored handoff
  path. The six canonical skills remain responsibility owners; the two
  Capstone aliases remain deleted.
- Left historical product and audit documents, PDFs, assets, remotes, refs, and
  history unchanged.
- Classified remaining search matches as: legitimate software/domain terms
  (`submission`, `assessment`, sprint planning, and review workflows); valuable
  but not yet consolidated historical documentation; authoritative audit
  evidence; compatibility-required identifiers; or third-party PDF metadata
  deferred to licensing review. No remaining match is unexplained.

## Deferred

- Historical `135.md` and other historical institutional references.
- Educational wording in historical/audit evidence and out-of-scope documents;
  no educational terminology was found in model prompt construction during the
  scoped current-product search.
- Historical agent-tooling documents that mention retired compatibility names;
  these remain evidence, not maintained invocation paths.
- Personal commit metadata.
- PDFs, assets, provenance, licensing, and RAG-source decisions.
- The one-time sanitized history rewrite.
- Remote migration and creation of the author-controlled repository.
- General README and documentation restructuring.

## Publication gate

Publication remains blocked until the candidate repository satisfies the
audit's [definition of safe to make public](PUBLIC_REPO_CLEANUP_AUDIT.md#16-definition-of-safe-to-make-public).
