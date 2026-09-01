# Project Evolution

> Historical context: this document explains how Skill Compass evolved into
> Cognivia. For current architecture and technical-review guidance, use
> [architecture.md](architecture.md) and
> [capstone-reviewer-guide.md](capstone-reviewer-guide.md).

The work described here was initially developed in a private repository. The
public repository begins with a sanitized baseline and intentionally does not
reproduce the private commit graph, hashes, tags, or repository metadata. This
document preserves the useful product chronology; the canonical concise
technical chronology is [Engineering History](engineering-history.md).

Skill Compass did not start as a complete Agentic RAG system. It evolved in
stages, and each stage solved a limitation that became obvious in the previous
version.

## Timeline

| Stage | Name                                  | Main change                                                     | Why it mattered                                   |
| ----- | ------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| S1    | Prompt-based Interview Coach          | Streamlit + OpenRouter prototype                                | First usable LLM app                              |
| S2    | Evidence-aware RAG baseline           | Documents, chunking, embeddings, retrieval                      | Recommendations started using evidence            |
| S3A   | LangGraph orchestration               | Typed state, nodes, conditional routes                          | Workflow became explicit and testable             |
| S3B   | Memory and bounded retry              | MemorySaver, thread_id, retry/fallback                          | Better multi-turn behavior and safer control flow |
| S3C   | Bounded Agentic RAG                   | Graph-owned retrieval, evidence assessment, query reformulation | The graph could decide when and how to retrieve   |
| S3D   | Groundedness and provenance hardening | Direct-support checks, document identity, fail-closed behavior  | Reduced false grounding and hallucination risk    |
| S3E   | Productisation and reviewer readiness | AI Engineer Compass framing, visible state, AppTests, audit     | Made the technical value visible and reviewable   |
| Capstone | Cognivia UX and docs consolidation | Explanation UX, numbered paths, restored controls, reviewer docs | Made the current app demo-ready and easier to audit |

## S1 — Prompt-based Interview Coach

The first version was a small Streamlit app that called OpenRouter and
generated interview-style prompts and coaching responses. It was useful as a
first LLM app because it proved the interface and interaction loop quickly.

The limitation was just as important: it was not evidence-grounded, and it was
not yet Skill Compass.

## S2 — Evidence-aware RAG baseline

Sprint 2 is where Skill Compass really started to take shape. The app gained a
Markdown knowledge base, chunking, embeddings, semantic retrieval, and
recommendations that could use retrieved evidence instead of only prompt text.

The private development history recorded a Sprint 2 baseline at this point. It
was a meaningful step forward because learning guidance stopped being purely
generative.

The remaining problem was orchestration. Retrieval, fallback, and response
assembly were still too implicit, memory was limited, and groundedness was not
strong enough for edge cases.

## S3A — LangGraph orchestration

Sprint 3 moved the core workflow into `tools/noise_to_signal_graph.py`. The
graph introduced typed state, explicit nodes, conditional routes, and
deterministic routing with LLM fallback for ambiguous cases.

This changed the shape of the codebase. The workflow became easier to test and
reason about because the control flow was visible instead of being buried in
Streamlit logic.

## S3B — Memory and bounded retry

The next step was short-term memory. `MemorySaver` plus a Streamlit `thread_id`
gave the app local conversational continuity, and clarification context could
survive follow-up turns.

I treated the bounded retry path as a deliberate design decision. The project
needed enough memory for a local Sprint 3 demo, but not persistent long-term
state. That trade-off kept the behavior safer and easier to test.

## S3C — Bounded Agentic RAG

Retrieval moved under graph control. The graph decides when retrieval is
needed, runs at most two retrieval attempts, reformulates the query once when
evidence is weak, and can stop with `insufficient_evidence` instead of forcing
an answer.

That is the important distinction: agentic does not mean unlimited autonomy.
The workflow is intentionally bounded for cost, safety, and testability.

## S3D — Groundedness and provenance hardening

This was the phase that made the system trustworthy enough to review.

Several bugs showed the same underlying lesson in different forms:

- A RAG-benefit question could route to clarification even though it was a
  valid informational question.
- A LangGraph question could accept evidence that merely mentioned LangGraph,
  without actually explaining the mechanism being asked about.
- Headings and malformed fragments could be treated as answer claims.
- Evidence assessment and answer generation could drift apart and use
  different accepted claims.
- `full_text` was kept too broadly in state, which made the payload larger than
  it needed to be.
- A positional zip after filtering could pair evidence with the wrong source
  text.
- Qdrant `_id` handling was asymmetric.
- Nested and top-level metadata shapes did not always match.
- `"N/A"` could be mistaken for a real identity value.
- Ambiguous identity now fails closed.
- An out-of-domain single-focus request like `Tacos al pastor` could be marked
  sufficient if generic AI/job-market evidence happened to retrieve.

The fix was to make single-focus evidence stricter. A single-focus topic now
needs either clear AI-engineering domain relevance or direct evidence support.
Generic AI career evidence is not enough for unrelated topics.

The main lesson is simple: relevance is not the same as groundedness.

## S3E — Productisation and reviewer readiness

The last Sprint 3 phase focused on making the engineering work visible and
reviewable. A historical read-only audit recorded no P0/P1 backend issues. The
main gap identified at that stage was UI clarity, so the product framing was
tightened instead of changing the backend again. This is a historical result,
not a current publication-readiness claim.

At that stage, the hierarchy was expressed as:

- Brand: Skill Compass
- Positioning: AI Engineer Compass
- Workflow: Noise-to-Signal
- Technical description: evidence-grounded decision assistant powered by a
  bounded Agentic RAG workflow

The UI exposes decision status, evidence quality, retrieval attempts, selected
focus, recommendation, next action, and trace information. Later Capstone work
expanded this into recommendation explanations, numbered learning directions,
selection state, notes, and broader AppTest coverage.

This phase was not cosmetic. It made the behavior understandable, exposed the
agentic workflow to reviewers, and gave the project stronger smoke coverage.

## Historical provenance

Earlier versions of this document cited private development tags and commit
identifiers for the Sprint 2 baseline, Sprint 3 checkpoints, bounded Agentic
RAG work, product framing, UI productisation, and groundedness hardening. Those
references were verified against the read-only private archive during public
documentation preparation. They are intentionally not presented as public Git
references because the sanitized public baseline has a separate history.

## What This Evolution Shows

The project got stronger because each sprint removed a specific limitation:

- from prompting to evidence
- from evidence to explicit orchestration
- from orchestration to bounded agentic retrieval
- from retrieval to groundedness and provenance
- from backend strength to product clarity, testing, and review readiness

That progression is the real story of Skill Compass.

## Capstone — Cognivia UX and documentation consolidation

After the private Sprint 3 review-ready checkpoint, the project was consolidated
under the Cognivia name. The current reviewer-facing app keeps the Noise-to-Signal
workflow but adds clearer recommendation explanations, AI career path and skill
gap descriptions, numbered learning direction schemas, persistent selected path
state, a mini notebook for reflection, compact runtime/provider messaging, and
restored icon-based background controls.

The current documentation set treats `README.md`, `docs/architecture.md`,
`docs/capstone-reviewer-guide.md`, `docs/demo-script.md`, and
`docs/smoke-test-checklist.md` as the source of truth for technical review.
