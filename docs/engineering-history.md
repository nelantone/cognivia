# Engineering History

Cognivia was initially developed in a private repository. This document is the
canonical concise chronology of that work. It summarizes meaningful engineering
phases without reproducing private commits, hashes, tags, repository metadata,
or publication-excluded material. The public repository begins with a sanitized
baseline dated 2026-09-01.

This is a capability history, not a release log or a claim that every historical
experiment remains supported. Current-state evidence belongs in
[Architecture](architecture.md), [Testing](testing.md),
[Evaluation](evaluation.md), and [Sources and provenance](sources.md).

## 1. Interactive coaching prototype

- **Period:** 2026-04-27 to 2026-04-30.
- **Problem:** Establish a usable interaction loop for structured learning and
  interview coaching.
- **Engineering changes:** Added the first Streamlit views, prompt-building
  functions, provider-backed chat, model controls, and user-facing failures.
- **Key decisions:** Keep the first version small, make prompt construction
  explicit, and avoid exposing raw provider errors.
- **Validation:** Input checks, friendly error paths, and linting were added as
  the prototype stabilized; no current runtime claim is inferred from them.
- **Outcome:** A working prompt-centered prototype established the UI and
  provider interaction pattern.

## 2. Skill Compass and the RAG baseline

- **Period:** 2026-05-20 to 2026-05-27.
- **Problem:** Generic generated guidance lacked inspectable evidence and
  repeatable evaluation.
- **Engineering changes:** Added security checks, learning-priority and study
  tools, document loading and splitting, semantic retrieval, a local knowledge
  base, evidence display, and retrieval evaluation.
- **Key decisions:** Make Skill Compass the primary mode, cache the vector
  store, and distinguish retrieved context from unsupported general advice.
- **Validation:** The private phase added focused security, provider-retry,
  explanation, and retrieval-evaluation checks; no pass total is carried into
  the public history.
- **Outcome:** Learning recommendations could use local evidence rather than
  relying only on prompt text.

## 3. Persistent, source-aware retrieval

- **Period:** 2026-06-19 to 2026-06-23.
- **Problem:** The initial retrieval path needed PDF coverage, persistent index
  lifecycle management, and clearer separation between evidence and scores.
- **Engineering changes:** Added PDF ingestion, evidence-aware planning,
  persistent Qdrant storage, source-aware invalidation, and informational
  answers.
- **Key decisions:** Replace the earlier vector-store implementation with local
  Qdrant, preserve Markdown coverage, and keep display evidence separate from
  decision scoring.
- **Validation:** Loader coverage and retriever unit paths were maintained, and
  indexing was hardened for source changes and lossless rebuilding.
- **Outcome:** Retrieval became persistent, inspectable, and better aligned with
  corpus provenance.

## 4. Bounded graph orchestration and grounding

- **Period:** 2026-06-24 to 2026-06-30.
- **Problem:** Retrieval, fallback, intent handling, and multi-turn context were
  too implicit for reliable review.
- **Engineering changes:** Introduced a typed LangGraph workflow, deterministic
  routing with bounded model fallback, short-term checkpoint memory,
  graph-owned retrieval, one query reformulation, and explicit terminal states.
- **Key decisions:** Bound retrieval and model retries, disable tracing by
  default, fail closed when evidence is insufficient, and separate relevance
  from direct support.
- **Validation:** Historical work added graph input checks, a manual evaluation
  plan, workflow evidence, and targeted fixes for clarification memory and
  out-of-domain grounding.
- **Outcome:** Noise-to-Signal became a bounded, evidence-aware workflow rather
  than an open-ended agent loop.

## 5. Cognivia framing and guided intake

- **Period:** 2026-07-01 to 2026-07-09.
- **Problem:** Strong backend behavior was not yet presented as a coherent
  learner-centered product, and vague goals lacked structured context.
- **Engineering changes:** Introduced Cognivia branding, a guided learner intake
  flow, recursive ingestion fixes, token-aware chunking, career-source guidance,
  and integrated guided decisions into Noise-to-Signal.
- **Key decisions:** Route vague learning-path requests to guided intake while
  retaining direct routing for clear questions, and keep evidence limitations
  visible.
- **Validation:** The private phase records targeted splitter updates,
  retrieval-evaluation hardening, and repeated stabilization of the guided
  decision flow.
- **Outcome:** The application could gather learner context before proposing a
  direction and presented a more consistent product identity.

## 6. Memory, provider, and retrieval boundaries

- **Period:** 2026-07-10 to 2026-07-11.
- **Problem:** Learner context was session-bound, provider selection was narrow,
  and index reuse needed provider-aware safeguards.
- **Engineering changes:** Added a memory-store contract, PostgreSQL schema
  foundation, null fallback, learning-event persistence, memory export, runtime
  provider status, explicit OpenAI support, and embedding identity in Qdrant
  manifests.
- **Key decisions:** Keep durable memory optional and append-only, avoid implicit
  OpenAI selection, and invalidate indexes when embedding identity changes.
- **Validation:** Runtime status made configuration inspectable, and retrieval
  relevance and Markdown chunking received focused hardening.
- **Outcome:** Provider and persistence concerns gained explicit boundaries,
  while remaining local-development foundations rather than production claims.

## 7. Learning directions, notes, and exports

- **Period:** 2026-07-11 to 2026-07-14.
- **Problem:** Evidence-aware decisions needed clearer learner choices,
  reflection support, and portable outputs.
- **Engineering changes:** Added structured learning-direction schemas,
  selection state, Study notes, complete-plan export, refined direction logic,
  and reviewer-facing explanations.
- **Key decisions:** Preserve all generated direction options, make the selected
  path explicit, and keep exports deterministic and offline-safe.
- **Validation:** Historical regression checks covered selected interaction
  details, while demo and reviewer documentation were synchronized with the
  implemented flow.
- **Outcome:** Cognivia connected evidence-aware decisions to concrete learning
  paths, reflection, and exportable plans.

## 8. Frontend clarity and UX hardening

- **Period:** 2026-07-26 to 2026-08-03.
- **Problem:** The growing Streamlit surface needed clearer interaction states,
  more stable controls, and an auditable user experience.
- **Engineering changes:** Performed a frontend audit, completed the Cognivia
  clarity experience, hardened dispatch and sidebar behavior, optimized assets,
  and fixed final review regressions.
- **Key decisions:** Preserve backend behavior while improving state visibility,
  accessibility, focus controls, and rerun stability.
- **Validation:** A dispatch regression check and focused frontend review fixes
  were recorded in the private phase; no browser result is claimed for the
  current public baseline here.
- **Outcome:** The primary workflow became clearer and more stable without a
  product or architecture rewrite.

## 9. Agent-tooling governance

- **Period:** 2026-08-05 to 2026-08-07.
- **Problem:** Reusable agent workflows and repository safety rules had become
  fragmented and difficult to validate consistently.
- **Engineering changes:** Established shared agent instructions, canonical
  project skills, deterministic tooling validation, and the advisory Sentinel
  review gate.
- **Key decisions:** Give durable rules, reusable workflows, deterministic
  checks, and advisory review distinct owners.
- **Validation:** The private phase hardened path and credential handling and
  added deterministic validation for the agent-tooling surface.
- **Outcome:** Repository automation gained explicit governance and safer local
  review gates.

## 10. Incremental frontend separation

- **Period:** 2026-08-09 to 2026-08-18.
- **Problem:** `app.py` had accumulated presentation, browser, runtime, and
  secondary-mode responsibilities.
- **Engineering changes:** Audited the frontend architecture, then extracted
  styles, assets, browser controllers, runtime presentation, and secondary-mode
  views in separate phases.
- **Key decisions:** Use small behavior-preserving extractions and retain
  `app.py` as the Streamlit composition root.
- **Validation:** The architecture audit defined responsibility boundaries and
  each extraction was recorded as a separate phase; this history does not claim
  a current full-suite result.
- **Outcome:** Frontend ownership improved, although `app.py` still coordinates
  residual workflow, export, and persistence concerns.

## 11. Private-to-public preparation

- **Period:** 2026-08-19 to 2026-09-01.
- **Problem:** The development repository contained history and material that
  should not be reproduced in a publication-ready source release.
- **Engineering changes:** Audited public readiness, removed publication-excluded
  artifacts and framing, established canonical public documentation, remediated
  publication blockers, and recorded validation evidence.
- **Key decisions:** Publish one sanitized baseline rather than rewrite,
  fabricate, or selectively expose the private commit graph; preserve useful
  owner-written history as documentation.
- **Validation:** Publication preparation included repository audits and local
  documentation/tooling gates. Product behavior is not re-validated by this
  chronology.
- **Outcome:** Version 0.1.0 begins the independent public history on
  2026-09-01, with earlier engineering evolution summarized here.

## Current baseline

The current application architecture is Python and Streamlit. Possible future
technology migrations are not part of the present implementation. The public
baseline does not establish production hosting, provider equivalence, durable
multi-user persistence, or complete prompt-injection protection.
