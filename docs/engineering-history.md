# Engineering History

Cognivia evolved from a prompt-centered learning assistant into a bounded,
evidence-aware Streamlit application. This is a capability history, not a
release log or a claim that every historical experiment remains supported.

## Capability progression

1. **Structured assistance** — early work established focused learning and
   coaching interactions.
2. **Local retrieval** — a Markdown/PDF knowledge base and chunked retrieval
   added an evidence layer.
3. **Graph orchestration** — explicit request shaping distinguished
   direct-decision routing from guided intake, while retrieval assessment,
   reformulation, classification, and terminal response paths made control flow
   inspectable.
4. **Grounding safeguards** — relevance filtering was kept separate from direct
   evidence support; provenance metadata, low-evidence, and out-of-scope
   outcomes clarified the limits of available sources.
5. **Product interaction** — guided intake, quick prompts, Focus Mode, reset
   behavior, and exports made the workflows usable through Streamlit.
6. **Operational boundaries** — explicit provider selection, offline behavior,
   provider-specific capabilities, append-only optional PostgreSQL memory with a
   no-history null fallback, security helpers, and deterministic retrieval
   evaluation separated infrastructure from product logic.

Across these stages, the durable product principle has remained to strengthen
human judgment rather than substitute for it.

## Current baseline

The current application architecture in this repository is Python and
Streamlit. Possible future technology migrations are not part of the present
implementation.

Detailed current-state evidence lives in [Architecture](architecture.md),
[Testing](testing.md), [Evaluation](evaluation.md), and
[Sources and provenance](sources.md).
