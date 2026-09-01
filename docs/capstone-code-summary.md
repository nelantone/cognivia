# Historical Skill Compass Codebase Summary for Capstone Planning

> Historical/planning context: this summary predates the final Cognivia
> documentation consolidation. It may contain stale absolute paths, old project
> names, and older corpus/chunking descriptions. For current Capstone review,
> use [README](../README.md), [Architecture](architecture.md),
> [Capstone reviewer guide](capstone-reviewer-guide.md), and
> [Current state, validation, and next steps](current-state-validation-and-next-steps.md).

This document summarizes the current Skill Compass implementation to support Capstone planning. It is a planning reference, not a claim that all future features are already implemented.

## 1. Project One-Liner

Skill Compass is a local Streamlit app for AI learners and aspiring AI engineers that turns vague or overloaded learning questions into either a clarification request, an evidence-grounded answer, a focused study plan, or an insufficient-evidence refusal. Its main Sprint 3 workflow is `Noise-to-Signal`, a bounded LangGraph-based Agentic RAG flow over a small local knowledge base.

## 2. Current Product Scope

### Main user flow

The current primary product surface is the `Noise-to-Signal Agent` mode in [app.py](../app.py). The user enters a learning or prioritization question such as:

- `What should I learn next?`
- `Why is RAG evaluation useful for AI engineers?`
- `Should I learn LangGraph or RAG evaluation?`

The app validates the input, runs `run_noise_to_signal(...)` from [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py), and renders:

- decision status
- evidence quality
- selected focus
- retrieval attempts
- recommendation or answer
- next action
- retrieved evidence
- study plan when applicable
- decision trace
- technical details such as query reformulation and routing source

### Streamlit UI

The Streamlit UI currently exposes three app modes:

- `Noise-to-Signal Agent`: current main workflow
- `AI Skill Compass`: older deterministic/RAG tool suite
- `Interview Coach (Sprint 1 legacy)`: older prompt-based OpenRouter mode

The current repo therefore contains both the main Sprint 3 product flow and earlier project surfaces kept for history/demo purposes.

### Learning recommendation flow

The current recommendation behavior supports four broad outcomes:

- clarification when the request is too vague
- informational answers when the corpus directly supports a factual/explanatory question
- comparison decisions when explicit options are provided and each has positive evidence support
- single-focus study plans when the user already names one topic

For single-focus requests, the app can still generate a study plan even if evidence is weak, but it labels that plan as not strongly evidence-grounded unless evidence is actually present.

### RAG / evidence flow

The main workflow retrieves from a local corpus in `data/knowledge_base` plus a default PDF directory in `data/sources/pdfs`. Retrieval is semantic search over a persistent local Qdrant vector store. Retrieved documents are converted into display evidence and reasoning evidence, then judged deterministically for direct support rather than simple topical relevance.

### Interview / practice / coach modes

There is no current separate interview-practice mode inside the main Noise-to-Signal graph.

What does exist:

- `Interview Coach (Sprint 1 legacy)` in [app.py](../app.py), which uses `prompts.py` and `openrouter_client.py` to generate interview-prep content
- `Evaluate explanation` inside the older `AI Skill Compass` mode, powered by [tools/explanation.py](../tools/explanation.py)

These are real features in the repo, but they are not the main Sprint 3 capstone-worthy flow.

## 3. Architecture Overview

### Frontend / UI layer

- [app.py](../app.py) is the single Streamlit entrypoint.
- It handles app-mode selection, input validation, session state, thread IDs, and rendering for results/evidence/trace.
- It also contains legacy UI branches for interview coaching, study-plan generation, explanation evaluation, and deterministic RAG evaluation.

### Orchestration / workflow layer

- [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py) is the main orchestration file.
- It defines a LangGraph `StateGraph` using a typed `NoiseToSignalState` `TypedDict`.
- It uses `MemorySaver` for short-term checkpoint memory by `thread_id`.
- It owns request-shape detection, retrieval decisions, evidence assessment, retry/reformulation, ambiguous-intent LLM fallback, and terminal response selection.

### RAG layer

- [rag/loader.py](../rag/loader.py) loads Markdown and PDF content and attaches metadata.
- [rag/splitter.py](../rag/splitter.py) chunks text by character count with overlap and word-boundary adjustments.
- [rag/retriever.py](../rag/retriever.py) builds/reuses the persistent Qdrant vector store and performs similarity search.
- [rag/generator.py](../rag/generator.py) powers the older `Ask with RAG` flow.
- [rag/evaluation.py](../rag/evaluation.py) provides deterministic retrieval-evaluation helpers.

### LLM / model client layer

- [openrouter_client.py](../openrouter_client.py) wraps raw OpenRouter chat completion calls using `requests` plus `tenacity` retry logic.
- [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py) uses `langchain_openai.ChatOpenAI` with an OpenRouter base URL for structured classification in ambiguous cases.
- [rag/generator.py](../rag/generator.py) also uses `ChatOpenAI` for the legacy RAG answer flow.

### Storage / vector store layer

- The active vector database is local persistent Qdrant, not Chroma.
- Qdrant persistence is managed in [rag/retriever.py](../rag/retriever.py) under `data/vector_store/qdrant/<hashed-source-dir>/`.
- A `source_manifest.json` file is written per persisted index to track file fingerprints and schema version.

### Tests / evaluation layer

- `pytest` is configured through [pytest.ini](../pytest.ini).
- The repo contains focused unit and regression tests across graph behavior, app rendering, RAG ingestion, retriever caching, evaluation helpers, and security.
- There is also a small deterministic evaluation set in [rag/evaluation.py](../rag/evaluation.py) and manual-evaluation guidance in [docs/evaluation.md](../docs/evaluation.md).

## 4. Important Files and Responsibilities

- [app.py](../app.py): Streamlit app entrypoint, app-mode switcher, session/thread handling, result rendering.
- [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py): main LangGraph workflow, retrieval control, evidence assessment, routing, memory, fail-closed behavior.
- [tools/study_plan.py](../tools/study_plan.py): deterministic helpers for focus extraction, evidence formatting, evidence claim building, ranking options, and study-plan generation.
- [rag/retriever.py](../rag/retriever.py): embeddings client setup, Qdrant build/load/rebuild logic, source fingerprinting, retrieval API.
- [rag/loader.py](../rag/loader.py): Markdown/PDF loading and metadata extraction.
- [rag/splitter.py](../rag/splitter.py): character-based chunking with overlap and word-boundary preservation.
- [rag/generator.py](../rag/generator.py): older grounded-answer flow for the `Ask with RAG` tool.
- [rag/evaluation.py](../rag/evaluation.py): deterministic retrieval evaluation helpers and small evaluation case set.
- [security.py](../security.py): simple prompt-injection/offensive-language validation for user inputs.
- [openrouter_client.py](../openrouter_client.py): OpenRouter HTTP client with safe error handling and retry policy.
- [prompts.py](../prompts.py): system prompts for the legacy interview-coach mode.
- [langsmith_config.py](../langsmith_config.py): optional LangSmith environment defaults; tracing is disabled unless explicitly enabled.
- [requirements.txt](../requirements.txt): pinned dependencies.
- [tests/test_noise_to_signal_graph.py](../tests/test_noise_to_signal_graph.py): largest regression suite for graph routing, grounding, retry, provenance, and memory.
- [tests/test_noise_to_signal_app.py](../tests/test_noise_to_signal_app.py): Streamlit-facing rendering tests for the main UI path.
- [docs/architecture.md](../docs/architecture.md): architecture and graph overview.
- [docs/code-map.md](../docs/code-map.md): reviewer-oriented file map.
- [docs/project-evolution.md](../docs/project-evolution.md): evolution from prompt app to bounded Agentic RAG.
- [docs/future-improvements.md](../docs/future-improvements.md): future-facing capstone ideas, not implemented features.

## 5. LangGraph / Agentic RAG Flow

### Main nodes

The main nodes in [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py) are:

- `reset_retrieval_state`
- `resolve_clarification_context`
- `determine_request_shape`
- `retrieve_evidence`
- `prepare_evidence`
- `assess_evidence`
- `reformulate_retrieval_query`
- `classify_deterministic_intent`
- `classify_ambiguous_intent_with_llm`
- `answer_informational`
- `request_clarification`
- `plan_for_focus`
- `respond_comparison`
- `respond_insufficient`

### Routing decisions

The graph starts by cleaning input, resetting retrieval-specific state, and resolving clarification context from checkpoint memory. Then it classifies the request shape before retrieval.

At a high level:

- vague/context-only input routes to clarification without retrieval
- self-contained informational questions route toward retrieval
- single-focus learning requests route toward retrieval and then study-plan output
- explicit comparisons route toward retrieval and then comparison output
- ambiguous cases may go through one LLM classification node after deterministic classification

### Clarification path

Clarification is handled by:

- `resolve_clarification_context(...)`
- `determine_request_shape(...)`
- `request_clarification(...)`

If a prior turn left `pending_clarification=True`, the next input can be treated as context-only follow-up rather than a full new query. Clarification context is accumulated line-by-line, deduplicated case-insensitively, and displayed back as user-facing context rather than exposing internal orchestration details.

### Retrieval path

If retrieval is required, `retrieve_evidence(...)` calls `rag.retriever.retrieve_relevant_chunks(query, k=20)`. The graph, not the UI, owns this retrieval decision.

`prepare_evidence(...)` then converts raw documents into:

- `reasoning_evidence`: internal summarized items used for evidence checks
- `evidence`: UI-facing summarized evidence with excerpts/claims

### Evidence assessment

`assess_evidence(...)` is the core groundedness gate.

Observed behavior from code:

- informational questions require at least one direct answer claim extracted from retrieved evidence
- comparisons require positive support for every explicit option before the graph can safely choose or declare a tie
- single-focus requests require either AI-engineering domain relevance or direct evidence support; unrelated topics can be rejected as out of scope
- retrieval failures become either `insufficient_evidence` or a weak-evidence single-focus plan fallback, depending on request type

This is stricter than simple retrieval relevance. The code explicitly separates topical retrieval from direct support.

### Retry / reformulation behavior

The retry loop is bounded on purpose:

- maximum 2 retrieval attempts
- maximum 1 reformulation

`reformulate_retrieval_query(...)` creates deterministic query rewrites based on evidence gaps:

- informational: appends terms like `definition purpose how it works`
- comparison: targets unsupported options with `skills prerequisites learning tradeoffs`
- single-focus: uses `<focus> skills prerequisites learning roadmap`

`route_after_evidence_assessment(...)` only allows a retry when:

- evidence quality is `weak`
- attempts are still below 2
- the query has not already been reformulated
- retrieval was not provided via explicit override

### Fail-closed / insufficient evidence behavior

If evidence is still weak after the bounded retry, the graph terminates with `respond_insufficient(...)` rather than fabricating confidence.

This fail-closed path is used for:

- unsupported informational questions
- comparisons where one or more options lack support
- out-of-domain single-focus requests
- retrieval failures that prevent a safe evidence-grounded answer

There is no unbounded autonomous loop and no multi-agent implementation.

## 6. RAG Implementation

### Document loading

[rag/loader.py](../rag/loader.py) loads:

- Markdown files from `data/knowledge_base`
- PDFs from `data/sources/pdfs` when the default Markdown directory is used

Observed corpus files include:

- internal notes such as `data/knowledge_base/internal/ai_job_market_skills.md`
- derived official summaries such as `data/knowledge_base/derived/oecd_ai_skills_gap_2025.md`
- one primary PDF source: `data/sources/pdfs/wef_future_of_jobs_report_2025.pdf`

Markdown metadata is parsed from top-of-file `key: value` lines until the first `## ` heading. PDF metadata is inferred partly from file naming, with a special case for the WEF report.

### Chunking approach

[rag/splitter.py](../rag/splitter.py) uses character-based chunking with defaults:

- `chunk_size=1000`
- `chunk_overlap=200`

It adjusts chunk ends and overlap starts to avoid mid-word splits when possible. This is more careful than naive slicing, but it is still character-based, not token-based.

Current limitations observed from code:

- no tokenizer-aware chunk sizing
- no Markdown-structure-aware chunking beyond preserving raw text
- no heading hierarchy chunker
- no semantic chunker

### Embeddings

[rag/retriever.py](../rag/retriever.py) creates embeddings with `langchain_openai.OpenAIEmbeddings` configured for OpenRouter:

- model: `text-embedding-3-small`
- base URL: `https://openrouter.ai/api/v1`

This requires `OPENROUTER_API_KEY` in the environment.

### Vector database

The vector store is persistent local Qdrant via `langchain_qdrant.QdrantVectorStore` and `qdrant_client.QdrantClient`.

Persistence behavior:

- each source directory is normalized and hashed
- the hash determines a specific persistence subdirectory
- source file path/size/mtime are fingerprinted
- the fingerprint plus `INDEX_SCHEMA_VERSION` are stored in `source_manifest.json`
- if the fingerprint matches and the collection exists with documents, the index is reused
- otherwise the persisted directory is rebuilt

### Retrieval

Current retrieval is plain semantic similarity search:

- `retrieve_relevant_chunks(query, k=3)` in the generic RAG flow
- `retrieve_evidence(..., k=20)` inside the Noise-to-Signal graph

Important limitation from code:

- there is no similarity-score threshold in the retriever
- the graph compensates by doing stricter deterministic evidence assessment after retrieval

So the current system relies more on post-retrieval groundedness checks than on retriever-side relevance filtering.

### Persistence / cache / manifest behavior

[rag/retriever.py](../rag/retriever.py) keeps a module-level `_vector_store_cache` keyed by:

- normalized source directory
- resolved persist directory
- collection name

This avoids rebuilding or reopening the store for every request during one Python process. `clear_cache()` exists for tests or refreshes.

### Known limitations

Observed limitations relevant to capstone planning:

- no retrieval score threshold
- no reranking step
- no hybrid retrieval
- no token-aware chunking
- no Markdown-aware structural chunking
- small local corpus
- PDF support is present, but only one PDF source is visible in the current repo snapshot
- retrieval quality is intentionally separated from groundedness, but recall may still be limited

## 7. Memory and State

### Short-term memory

Short-term state exists in the Noise-to-Signal graph through `MemorySaver` from LangGraph.

Observed behavior:

- `NOISE_TO_SIGNAL_CHECKPOINTER = MemorySaver()` is created in [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py)
- `app.py` stores a `noise_to_signal_thread_id` in Streamlit session state
- `run_noise_to_signal(..., thread_id=...)` passes that thread ID into LangGraph config

This gives process-local multi-turn continuity for clarification context.

### What is persisted vs reset

The graph intentionally preserves clarification-related memory and resets retrieval-specific state each turn.

Preserved or reused across turns in the same thread:

- `pending_clarification`
- `clarification_context`
- original user goal when the graph is waiting for more context

Reset each turn by `reset_retrieval_state(...)`:

- `retrieved_docs`
- evidence summaries
- retrieval attempts
- retrieval query
- query reformulation flag
- retrieval trace
- retrieval error
- informational answer cache

### What is not yet long-term memory

Current memory is not durable user memory.

It is not:

- persisted across app restarts
- tied to a user account
- storing progress history over days or weeks
- storing learning milestones, quiz outcomes, or preferences in a database

### What would need to change for capstone long-term progress tracking

To support true capstone-style progress memory, the app would need at least:

- a durable data store for user profiles and history
- a user/session identity model beyond ephemeral Streamlit session state
- explicit schemas for goals, progress checkpoints, completed katas, and confidence/assessment results
- retrieval or recommendation logic that reads from that user state before responding
- deletion/update controls if treated as real user data

This does not exist in the current repo.

## 8. Prompting and Structured Outputs

### Prompt-engineering techniques used

There are two distinct prompt surfaces in the repo:

1. Legacy interview coaching in [prompts.py](../prompts.py)
2. Limited structured routing in [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py)

`prompts.py` contains named system prompts such as:

- `Zero-shot (Direct)`
- `Few-shot (3 examples)`
- `Persona (Strict interviewer)`
- `Structured output (Organized)`
- `Thinking coach (Reasoning)`
- `Best Coach (Combined)`

These are only used by the legacy `Interview Coach (Sprint 1 legacy)` mode.

In the main Noise-to-Signal path, prompting is minimal and controlled. Most routing is deterministic. The only LLM-driven part is ambiguous-intent classification, where the system prompt instructs the model to return only the structured schema and choose among a small set of route types.

### Structured outputs

Yes, structured outputs are used in the graph.

`AmbiguousIntentClassification` in [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py) is a Pydantic model with fields:

- `intent`
- `confidence`
- `reason`
- `selected_focus`
- `options`

`ChatOpenAI(...).with_structured_output(AmbiguousIntentClassification)` is used for this path.

### Pydantic schemas

Observed Pydantic usage:

- `AmbiguousIntentClassification(BaseModel)` for structured LLM routing output

The broader graph state itself is a `TypedDict`, not a Pydantic model.

### Validation and fallback behavior

The ambiguous-intent classifier is guarded in multiple ways:

- up to 2 attempts for structured classification
- `ValidationError` handling if the model output does not fit the schema
- rejection if the intent is outside the supported set
- extra validation that `single_focus` includes a usable focus and `comparison` includes enough options
- fallback to clarification if LLM classification fails twice

This is a relatively strong pattern for a small project: the LLM does not directly produce the final answer path without schema checks.

## 9. Safety / Guardrails

### Current input validation

[security.py](../security.py) performs a basic validation layer before prompts or graph execution.

Observed validation rules:

- empty input is rejected
- short text fields are limited to 100 chars in `validate_user_input(...)`
- long text fields are limited to 5000 chars in `validate_job_description(...)`
- blocked prompt-injection phrases are checked using simple substring matching
- offensive phrases are checked using substring matching plus whitespace-stripped normalization for simple obfuscations

### Bad-words / blocklist / regex checks

There is no external moderation service and no classifier.

Current safety relies on:

- `BLOCKED_PHRASES`
- `OFFENSIVE_PHRASES`
- `OFFENSIVE_NORMALIZED_PHRASES`
- a normalization helper that removes spaces to catch basic spaced-out profanity

This is deterministic and easy to explain, but also limited.

### Fail-closed behavior

The strongest current guardrail is not the blocklist. It is the graph’s evidence gating.

Observed fail-closed behaviors:

- unclear requests become clarification requests
- weak or unsupported informational questions become `insufficient_evidence`
- incomplete comparisons do not pick the first option arbitrarily
- out-of-domain single-focus inputs can be rejected if evidence does not directly support them
- retrieval failures are converted into safe user-facing outcomes, not raw provider errors

UI/provider safeguards:

- `openrouter_client.py` converts provider/network failures into generic user-safe messages
- `app.py` logs exceptions and displays concise error text instead of raw stack traces
- API keys are never displayed

### Known limitations

From the code and docs, current safety limitations include:

- blocklist-based moderation only
- no probabilistic moderation/classification model
- no prompt-injection sandboxing beyond simple phrase checks and evidence gating
- no user auth or permission model
- no upload hardening because user-upload flow does not currently exist
- no red-team automation

### Possible capstone improvement

A realistic capstone improvement would be to add a moderation classifier or policy model ahead of the workflow, especially for:

- abuse/toxicity detection
- more robust prompt-injection detection
- clearer separation between unsafe input handling and normal low-evidence handling

That would be an actual improvement over the current substring list approach.

## 10. Tests and Quality

### Existing tests

The test suite is broad for a local demo project and especially strong around deterministic graph behavior.

Current test files include:

- `tests/test_noise_to_signal_graph.py`
- `tests/test_noise_to_signal_app.py`
- `tests/test_noise_to_signal_ui_copy.py`
- `tests/test_rag_loader.py`
- `tests/test_loader.py`
- `tests/test_rag_splitter.py`
- `tests/test_rag_pipeline.py`
- `tests/test_rag_retriever.py`
- `tests/test_rag_generator.py`
- `tests/test_rag_evaluation.py`
- `tests/test_study_plan.py`
- `tests/test_explanation.py`
- `tests/test_priority.py`
- `tests/test_security.py`
- `tests/test_openrouter_client.py`

### What areas are covered

Covered areas include:

- LangGraph routing and result shapes
- clarification memory behavior and thread isolation
- bounded retry and reformulation behavior
- informational grounding logic
- comparison support requirements
- provenance and document-identity matching
- out-of-domain rejection behavior
- Streamlit-facing rendering for main result states
- Markdown/PDF loading
- chunking invariants
- vector-store manifest/cache behavior
- deterministic RAG evaluation utilities
- explanation-evaluation heuristics
- priority-score heuristics
- security validation
- retry policy selection for OpenRouter errors

### Current test count

In the current repository snapshot, `rg -n "^def test_" tests | wc -l` returns `197` test function definitions.

`pytest --collect-only -q tests` currently collects `287` test items, which is higher because parametrized tests expand into multiple collected cases.

Important note:

- docs that mention `287` can be consistent with the current pytest collection count
- docs that mention `286` appear historical or outdated unless reverified against the current test suite

### Linting / Ruff status

`ruff` is included in [requirements.txt](../requirements.txt), but there is no dedicated `pyproject.toml`, `ruff.toml`, or `.ruff.toml` in the current repo snapshot.

Observed configuration state:

- [pytest.ini](../pytest.ini) exists
- no `pyproject.toml`
- no `uv.lock`
- no `.env.example` file in the current snapshot, even though the README references one

### Known gaps

Observed quality gaps:

- the evaluation framework is still small and partly manual
- no dedicated benchmark dataset beyond the deterministic retrieval cases and many unit/regression tests
- no browser automation such as Playwright in the current repo
- no typed packaging/config setup via `pyproject.toml`
- no long-term-memory tests because long-term memory does not exist yet

## 11. Sprint 3 Reviewer Feedback Relevant to Capstone

The current repo and docs already point toward several improvements worth carrying forward. Some of these are visible as known limitations; others are future recommendations rather than implemented work.

### UI polish

The repo already improved UI visibility for decision status, evidence quality, retrieval attempts, and trace. However, if this becomes the capstone, the main polish opportunity is to keep making the system state easy to inspect without burying the user in technical detail.

This is supported by:

- the Sprint 3 docs emphasizing reviewer readability
- the dedicated rendering helpers in [app.py](../app.py)
- `tests/test_noise_to_signal_app.py` and `tests/test_noise_to_signal_ui_copy.py`

### Token-based and Markdown-aware chunking

This is not implemented yet.

Current chunking is custom character-based splitting with overlap. It is careful about word boundaries, but it is not token-aware and not structure-aware beyond preserving raw Markdown text.

So this is a real capstone carry-forward item.

### Retrieval relevance score threshold

This is also not implemented in the retriever.

The current system does not use `similarity_search_with_score(...)` or a score cutoff. Instead, it retrieves candidates and uses deterministic evidence assessment to decide whether they are actually good enough.

That is a valid Sprint 3 choice, but adding a retriever-side relevance threshold or reranking layer is a concrete next improvement.

### Temperature handling for GPT-5 models

There is some inconsistency here that is worth carrying forward carefully:

- the main ambiguous-intent classifier in [tools/noise_to_signal_graph.py](../tools/noise_to_signal_graph.py) uses `temperature=0`
- the legacy RAG generator in [rag/generator.py](../rag/generator.py) uses `temperature=0.7`
- the legacy interview coach in [app.py](../app.py) exposes a user-controlled temperature slider

If reviewers specifically flagged GPT-5 temperature handling, the safe interpretation is that model-specific defaults should be revisited and made more consistent, especially for structured or deterministic tasks.

### Better moderation approach

This is clearly still a gap.

Current moderation is blocklist-based, as [security.py](../security.py) explicitly describes itself as a simple first safety layer rather than production-grade moderation.

### More consistent type hints

The repo does use type hints in important places, especially in the graph state and Pydantic schema, but type coverage is inconsistent across older deterministic helpers and UI functions. There is no static type checker config visible in the current repo snapshot.

So type-hint consistency is a reasonable capstone cleanup goal, but it should stay secondary to product/value work.

### `pyproject.toml` / `uv` consideration

The current repo uses:

- pinned [requirements.txt](../requirements.txt)
- minimal [pytest.ini](../pytest.ini)

It does not currently use:

- `pyproject.toml`
- `uv.lock`
- a centralized tool config file

So packaging/tooling consolidation is a real improvement opportunity, but it is not functionally required for the current app.

## 12. Capstone Opportunities Based on Current Code

### Guided learning flow

This is the strongest natural extension of the current graph.

Why it fits:

- the current graph already supports clarification turns
- the app already has short-term thread-based memory
- the current product is already framed as a learning-decision workflow

The next step would be to turn the current one-shot text area into a guided multi-turn onboarding and recommendation flow for the next planning phase.

### Knowledge checks

This is also a strong fit because the repo already contains deterministic explanation evaluation in [tools/explanation.py](../tools/explanation.py). That logic could evolve into quick topic checkpoints or self-assessments.

### Technical vocabulary feedback

This is already partially present through `evaluate_explanation(...)`. The capstone version could integrate that into the main learning flow rather than leaving it as a side tool.

### Progress memory

This is not present yet, but it is an obvious upgrade path from current `MemorySaver` short-term state.

### Roadmap / skill map

The current deterministic study-plan generator and topic-priority framing could evolve into a more explicit skill roadmap. This would likely require a clearer topic taxonomy and persistent learner state.

### Learning katas / topic katas

This is realistic because the current app already supports:

- study plans
- explanation evaluation
- evidence-backed reasoning about why a topic matters

A capstone could add small repeatable exercises for topics like RAG evaluation, LangGraph, prompt engineering, or API integration.

### PostgreSQL + pgvector later if useful

This is not needed immediately, but it is a credible future infrastructure path if the app grows beyond local single-user/demo usage. Right now Qdrant is a reasonable local choice.

### React frontend later if the core is stable

Also plausible later, but not the first priority. The Streamlit frontend is enough for current experimentation and review. A React frontend only becomes justified once the user model, long-term memory, and interaction design are stable.

## 13. Risks / Scope Warnings

- Turning this into a full autonomous multi-agent platform would likely overexpand the project quickly.
- Long-term memory plus user accounts plus progress analytics plus market-aware ingestion could become a separate product, not a capstone-sized increment.
- Replacing both the backend workflow and the frontend in one capstone phase would make debugging and reviewer explanation harder.
- Live web ingestion, scraping, or broad trend aggregation adds freshness but also safety, provenance, and maintenance complexity.
- A full moderation system, auth system, and production deployment hardening are valuable but can easily consume the capstone scope.
- A complex skill graph/roadmap engine could become speculative if not grounded in a small, testable MVP.
- Switching databases or vector stores too early would risk infrastructure work crowding out the core product value.

## 14. Recommended MVP Path

### What to do first

Build the capstone around the current `Noise-to-Signal` workflow rather than replacing it.

Practical first phase:

- keep LangGraph as the orchestration core
- convert the main flow into a guided learner interaction flow instead of a single prompt box
- store a small learner profile and session goals in durable storage
- reuse the current clarification path as the first stage of onboarding
- keep the same fail-closed evidence logic

This preserves the strongest current asset: bounded, inspectable, evidence-aware workflow control.

### What to do second

Add the smallest valuable personalization and learning loop:

- progress checkpoints
- short knowledge checks or explanation scoring
- saved current level / target role / available time
- simple progress history and next-step continuity

At the same time, improve retrieval quality incrementally:

- add retrieval score visibility or thresholding
- improve chunking to be token-aware and Markdown-aware
- expand the evaluation dataset

### What to leave for later

Leave these until the core guided-learning MVP is stable:

- React frontend rewrite
- PostgreSQL + pgvector migration
- broad market/news ingestion
- multi-agent decomposition
- user accounts and full production hardening
- advanced analytics/dashboard layer

## Additional Honest Notes

- The current main technical strength is bounded, testable orchestration and conservative evidence gating.
- The current main limitation is corpus size and retrieval quality, not absence of orchestration.
- The repo contains legacy surfaces that are useful context, but the capstone should probably center on `Noise-to-Signal`, not on the older interview-coach branch.
- The README references `.env.example`, but that file is not present in the current repository snapshot.
- The repo currently shows `197` test function definitions with `rg`, while `pytest --collect-only -q tests` collects `287` items because parametrized tests expand into multiple cases.
