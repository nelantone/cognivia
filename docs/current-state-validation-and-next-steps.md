# Cognivia Current State, Validation, and Next Steps

This public-safe note summarizes the current Cognivia state without exposing
private audit notes, local Git history, or internal source documents.

## What Cognivia Is

Cognivia is an evidence-aware AI learning coach that helps learners turn noisy information into clearer learning decisions and actionable next steps.

It uses a bounded learning workflow rather than a generic chatbot pattern: clarify the goal, decide whether retrieval is needed, assess evidence support, show low-evidence states, offer selectable learning paths, invite reflection through a Study note, and preserve human authority over the final decision.

## Why It Exists

AI learners can receive many fluent recommendations without knowing whether the advice fits their context or is supported by evidence. Cognivia exists to make the learning-decision process more explicit, conservative, and inspectable.

General-purpose LLMs provide broad language and reasoning capabilities. Cognivia structures how those capabilities are used for evidence-aware learning, reflection, and decisions.

## Current Capabilities

Current and supported:

- Direct-query and guided-intake flows.
- Bounded LangGraph/RAG workflow with explicit terminal outcomes.
- Retrieval-required decisions.
- Retrieval relevance separated from direct evidence support.
- Low-evidence states and out-of-scope gating.
- Evidence-aware recommendations.
- Prompt-specific learning directions.
- Selectable learning paths and learning path maps.
- Next-step guidance.
- Study note / reflection.
- Markdown and JSON exports.
- Full learning-plan Markdown export.
- Recursive PDF and Markdown ingestion from `data/knowledge_base`.
- Token-aware chunking with Markdown heading metadata.
- Local Qdrant vector store with stale-index and embedding-identity protection.
- Offline, OpenAI, and OpenRouter provider modes where configured.
- Runtime/provider transparency.
- Deterministic fallback behavior.
- Pytest-level LangSmith isolation.

Partial / foundation:

- Append-only learner memory foundation.
- Durable continuity only where `DATABASE_URL` is configured.
- Provider-flexible workflow, not provider equivalence.
- Evidence-backed results only when retrieved evidence directly supports the conclusion.
- Profile-based or context-based recommendations when direct evidence is absent.

Future / To-do:

- Complete Study Coach.
- Complete Thinking Coach.
- Focus Mode.
- Live labor-market research.
- Production-grade multi-user memory.
- Full pgvector RAG.
- Production deployment hardening.
- Broad public Product Constitution.

## Architecture Overview

Cognivia has five main layers:

1. Streamlit UI in `app.py`.
2. Guided intake and direct-query routing.
3. Bounded LangGraph workflow in `tools/noise_to_signal_graph.py`.
4. RAG ingestion, token-aware chunking, embeddings, and local Qdrant retrieval under `rag/`.
5. Learning direction, Study note, export, provider, and memory boundaries.

See [Architecture](architecture.md) for diagrams and implementation details.

## Safe Demo Command

Use this for local demonstrations:

```bash
unset OPENAI_API_KEY
unset OPENROUTER_API_KEY

export COGNIVIA_LLM_PROVIDER=offline
export LANGSMITH_TRACING=false
export LANGCHAIN_TRACING_V2=false

.venv/bin/python -m streamlit run app.py
```

## Complete Validation Command

Use this for the full suite. Keep `COGNIVIA_LLM_PROVIDER` unset because provider-selection tests exercise mocked provider scenarios:

```bash
unset OPENAI_API_KEY
unset OPENROUTER_API_KEY
unset COGNIVIA_LLM_PROVIDER
unset LANGSMITH_API_KEY
unset LANGCHAIN_API_KEY

export LANGSMITH_TRACING=false
export LANGCHAIN_TRACING_V2=false

.venv/bin/python -m pytest tests -q
.venv/bin/python -m ruff check .
git diff --check
bash scripts/sentinel.sh
```

## Publication-candidate validation — 2026-09-01

The complete offline product suite was run with dotenv loading disabled and
provider and database variables unset:

```bash
env -u OPENAI_API_KEY -u OPENROUTER_API_KEY -u COGNIVIA_LLM_PROVIDER -u DATABASE_URL -u LANGSMITH_API_KEY -u LANGCHAIN_API_KEY PYTHON_DOTENV_DISABLED=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python -m pytest tests -q
```

- 519 tests passed in 58.65 seconds.
- 0 tests were skipped.
- 0 warnings were reported.
- No live provider or database calls were made.

The LangSmith test-isolation fix added pytest-level protection through `tests/conftest.py` and `tests/test_langsmith_test_isolation.py`. The pytest bootstrap disables LangSmith tracing and neutralizes LangSmith credentials so local shell or `.env` configuration cannot cause trace ingestion during tests.

LangSmith is not removed from the application; it remains optional observability.

## Product Boundaries

Cognivia currently does not claim:

- factual certainty;
- production readiness;
- production-grade privacy;
- complete multi-user isolation;
- complete durable memory by default;
- pgvector as the current RAG vector store;
- complete Study Coach;
- complete Thinking Coach;
- Focus Mode;
- live labor-market intelligence;
- promised learning, decision, hiring, or employment outcomes.

Preferred wording:

> Cognivia reduces unsupported recommendations through evidence-aware retrieval, explicit low-evidence states, out-of-scope gating, and transparent fallback behavior.

## Immediate Next Steps

Before a release if still relevant:

1. Verify final Git state.
2. Diagnose active `rag/evaluation.py` expected-source path drift.
3. Complete a final human smoke test.
4. Perform a final documentation review.
5. Verify relative links and paths.
6. Rehearse demo and Q&A.
7. Confirm deployment claims remain conservative.

## Deferred Hardening

Future hardening:

- Corrupt/encrypted PDF handling per file/page.
- Richer PDF metadata and provenance.
- Explicit handling of visual-reference PDFs.
- Deferred Streamlit import-time UI refactor.
- Provider fallback review.
- Separately reviewed Focus Mode.
- Production-grade memory and multi-user isolation.
- Public deployment hardening.
- Broader evaluation and observability.
- Public edited Product Constitution.
- Historical documentation cleanup.

## Project Summary

Cognivia's main contribution is not a new foundation model. It is a bounded, evidence-aware learning workflow that helps a user clarify a learning goal, assess evidence, choose a path, reflect on the next action, retain continuity where configured, and keep final judgment human.
