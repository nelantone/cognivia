# Cognivia Demonstration and Technical Review Guide

This is the main guide for presenting and technically evaluating Cognivia. It
focuses on the current implementation, not historical Skill Compass surfaces or
future product ideas.

## 20-Second Explanation

Cognivia is an evidence-aware AI learning coach. It helps learners turn noisy AI-learning goals into clearer learning decisions by using a bounded LangGraph/RAG workflow, explicit evidence states, selectable learning paths, and reflection notes instead of simply generating generic answers.

## 10-Minute Presentation Structure

Suggested timing:

- 0:00-1:00 - Problem and user need.
- 1:00-2:00 - What Cognivia is.
- 2:00-3:30 - Why not just ChatGPT.
- 3:30-5:00 - Architecture and evidence flow.
- 5:00-8:00 - Controlled three-step demo.
- 8:00-9:00 - Technical decisions and trade-offs.
- 9:00-10:00 - Limitations and next steps.

Keep the presentation adaptable. The goal is to show the workflow and judgment boundaries, not to recite exact text.

## Three-Step Demo

Use safe offline mode unless providers and costs are intentionally configured.

1. Submit a learning goal or question.
   Use `What should I learn next?` to show guided intake, or a focused AI-learning question to show direct query handling.

2. Inspect recommendation, evidence state, and learning paths.
   Point out whether the recommendation is evidence-backed, profile-based, context-based, low-evidence, or insufficient. Show the numbered learning direction schemas.

3. Select a path and show reflection / Study note / export.
   Choose a learning path, save a Study note, and mention Markdown/JSON export behavior.

Stable out-of-scope check: `Tacos al pastor` should not produce a false AI-learning plan. The important behavior is low-evidence or insufficient-evidence handling.

## Demo Plan B

If a live rerun fails:

- Keep `COGNIVIA_LLM_PROVIDER=offline` and tracing disabled.
- Walk through [Architecture](architecture.md) and the current screenshots already under `docs/demo-screenshots/` if useful.
- Use a previously generated result only if it is already available locally.
- Do not debug provider keys, Qdrant rebuilds, `.env`, dependency installs, or optional services during the presentation.
- Do not claim live provider behavior unless it was deliberately configured and verified.

## Technical Questions and Answers

### Why LangGraph?

The workflow has meaningful state and branching: guided intake, direct query handling, retrieval decisions, evidence assessment, one reformulation, comparison handling, low-evidence states, and terminal responses. LangGraph makes that control flow explicit and testable.

### Why RAG?

The product is about learning decisions that should be grounded when evidence exists. RAG lets Cognivia retrieve from a curated local corpus instead of relying only on model prior knowledge.

### Why Qdrant?

Qdrant is the current local vector store. It supports persistent semantic retrieval for the curated corpus and avoids rebuilding the index on every run when source and embedding identity metadata still match.

### How is retrieval relevance different from direct support?

Retrieval relevance means a chunk appears similar to the query. Direct support means the retrieved evidence actually supports the conclusion or recommendation being shown. Cognivia separates these checks so related but insufficient evidence does not become confident advice.

### What happens when evidence is insufficient?

The graph can return an insufficient-evidence or low-evidence state. It may ask for clarification, present limited context-based guidance, or refuse to choose between options when support is weak.

### How does out-of-scope gating work?

For unrelated or unsupported prompts, the graph requires AI-learning domain relevance or direct evidence support. If that support is missing, it fails closed instead of forcing a learning path.

### How does memory work today?

Cognivia has an append-only learner memory foundation. It can save learner profiles, decisions, generated paths, selected paths, and Study notes when storage is configured. Without `DATABASE_URL`, it falls back to no durable history.

### Why multiple provider modes?

Provider modes make runtime behavior explicit. `offline` is safe for demos, `openai` and `openrouter` are controlled live modes when configured. The workflow is provider-flexible, while provider capabilities and behavior may differ.

### How do tests avoid external LangSmith tracing?

The pytest bootstrap disables LangSmith tracing and neutralizes LangSmith credentials so local shell or `.env` configuration cannot cause trace ingestion during tests.

### What are the main trade-offs?

Cognivia favors bounded, reviewable behavior over open-ended autonomy. It accepts conservative non-answers when evidence is weak. Streamlit and local Qdrant keep the demo inspectable but are not a full production deployment architecture.

### What still needs production hardening?

Authentication, multi-user privacy, hosted storage, backups, rate limiting, production observability, public deployment hardening, and production-grade durable memory are not claimed.

### Why Cognivia rather than ChatGPT?

General-purpose LLMs provide broad language and reasoning capabilities. Cognivia structures how those capabilities are used for evidence-aware learning, reflection, and decisions. The methodology around the model is the product.

### What would be built next?

Immediate next steps are final Git review, evaluation-path drift review, final smoke testing, and demo rehearsal. Post-presentation hardening includes corrupt/encrypted PDF handling, richer provenance, provider fallback review, Focus Mode as a separate change, production memory, deployment hardening, broader evaluation, and historical documentation cleanup.

### How are hallucination risks reduced?

Cognivia reduces unsupported recommendations through evidence-aware retrieval, explicit low-evidence states, out-of-scope gating, direct-support checks, and transparent fallback behavior. It does not promise factual certainty.

### What ethical considerations were addressed?

The app avoids displaying secrets, hides raw provider errors, treats retrieved documents as untrusted, preserves source metadata, labels evidence boundaries, supports offline demos, and keeps human judgment authoritative.

## Implementation Evidence Map

| Project area | Current status | Evidence in repo | Limitation |
| --- | --- | --- | --- |
| Clear project objective | Current | `README.md`, this guide | Local learning/demo product, not production SaaS. |
| Functional AI application | Current with limitations | `app.py`, `tools/noise_to_signal_graph.py`, `openrouter_client.py` | Live providers require deliberate config. |
| Streamlit UI | Current | `app.py`, `tests/test_noise_to_signal_app.py` | Streamlit is current UI; React polish is future. |
| LangGraph/LangChain workflow | Current | `tools/noise_to_signal_graph.py` | Bounded workflow, not open-ended agent autonomy. |
| RAG and vector database | Current | `rag/loader.py`, `rag/splitter.py`, `rag/retriever.py` | Local Qdrant; pgvector RAG is future work. |
| Prompt/context engineering | Current | `tools/guided_intake.py`, `tools/learning_direction.py`, graph routing | Deterministic schemas are MVP helpers. |
| Evidence quality | Current | graph tests, retriever tests | Corpus is intentionally limited. |
| Learner continuity | Partial / foundation | `memory/`, app memory events | Durable continuity only where configured. |
| Provider flexibility | Current with caveats | `tools/provider_config.py`, provider tests | Providers are not equivalent. |
| Evaluation and validation | Current | `tests/`, Ruff, diff-check, sentinel | Larger benchmark and red-team suite are future. |
| Ethics and privacy | Current with limitations | `security.py`, `memory/export.py`, provider/runtime status | No production auth or deletion workflow. |
| Production deployment | Future | Future-work docs | Public deployment readiness is not claimed. |

## Engineering Decisions

- Streamlit keeps the local demo and technical-inspection path simple.
- LangGraph makes the workflow explicit and bounded.
- Qdrant remains the current vector store because it is implemented and tested.
- The canonical corpus is `data/knowledge_base`.
- Token-aware, Markdown-aware chunking improves traceability.
- Provider selection is explicit to avoid accidental API-credit use.
- LangSmith remains optional observability; tests isolate it.
- Memory uses an append-only boundary so continuity can grow without making durable storage mandatory.
- Learning direction schemas convert recommendations into user choices without another provider call.

## Known Limitations

- Recommendations are not live labor-market research.
- Learning paths are deterministic MVP schemas.
- Note management is append-only; full note CRUD is not implemented.
- No production authentication, authorization, team tenancy, deletion workflow, or multi-user privacy system exists.
- Local Qdrant can have embedded-store concurrency limits.
- pgvector semantic memory/RAG, Study Coach, Thinking Coach, Focus Mode, React polish, and production deployment are future work.

## Current Source of Truth

Start with:

1. [README](../README.md)
2. [Architecture](architecture.md)
3. [Current state, validation, and next steps](current-state-validation-and-next-steps.md)
4. [Future improvements](future-improvements.md)
5. [Why Cognivia and Not Just ChatGPT?](product/why-cognivia-not-chatgpt.md)

Historical docs remain useful for project evolution, but they should not override current code, tests, README, architecture, or this guide.
