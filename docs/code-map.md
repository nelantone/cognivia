# Historical Code Map

> Historical/planning context: this code map was written before the current
> Cognivia consolidation. It may contain stale project names, file lists, and
> older corpus references. For current technical review, use
> [README](../README.md), [Architecture](architecture.md), and
> [Technical review guide](capstone-reviewer-guide.md).

# Skill Compass Code Map

## 1. How to use this document

This document maps the main project folders and files to their
responsibilities. It is not a full code reference.

It helps answer reviewer questions like:

- Where is the LangGraph workflow defined?
- Where does retrieval happen?
- Where is evidence assessed?
- Where is insufficient evidence decided?
- Where does the UI render the result?
- Where are the tests for the main behavior?

The main Sprint 3 product path is:

`app.py` -> `tools/noise_to_signal_graph.py` -> `rag/retriever.py` ->
`tools/study_plan.py` -> back to `app.py`

## 2. High-level project map

```text
cognivia/
├── app.py
├── openrouter_client.py
├── prompts.py
├── security.py
├── rag/
│   ├── evaluation.py
│   ├── generator.py
│   ├── loader.py
│   ├── pipeline.py
│   ├── retriever.py
│   └── splitter.py
├── tools/
│   ├── explanation.py
│   ├── noise_to_signal_graph.py
│   ├── priority.py
│   └── study_plan.py
├── tests/
│   ├── test_noise_to_signal_app.py
│   ├── test_noise_to_signal_graph.py
│   ├── test_noise_to_signal_ui_copy.py
│   ├── test_rag_loader.py
│   ├── test_rag_pipeline.py
│   ├── test_rag_retriever.py
│   ├── test_rag_splitter.py
│   ├── test_security.py
│   └── test_study_plan.py
├── data/
│   ├── knowledge_base/
│   └── sources/
└── docs/
    ├── architecture.md
    ├── code-map.md
    ├── evaluation.md
    ├── future-improvements.md
    ├── presentation-outline.md
    └── project-evolution.md
```

## 3. Main runtime path

### UI entry point

- `app.py`
  Noise-to-Signal mode is selected from the sidebar.
- The UI validates input with `validate_user_input` and then calls
  `run_noise_to_signal(...)` from `tools/noise_to_signal_graph.py`.
- The returned decision dictionary is rendered by:
  - `_render_noise_to_signal_metrics`
  - `_render_noise_to_signal_evidence`
  - `_render_noise_to_signal_study_plan`
  - `_render_noise_to_signal_trace`
  - `_render_noise_to_signal_technical_details`
  - `_render_noise_to_signal_result`

### Graph orchestration

- `tools/noise_to_signal_graph.py`
  This is the main Sprint 3 workflow file.
- Public entry point:
  - `run_noise_to_signal(...)`
- Graph builder:
  - `_build_graph(...)`
- State model:
  - `NoiseToSignalState`
- Optional structured LLM routing model:
  - `AmbiguousIntentClassification`

### Retrieval path

- `retrieve_evidence(...)` in `tools/noise_to_signal_graph.py`
  calls `rag.retriever.retrieve_relevant_chunks(...)`.
- `rag/retriever.py` loads or builds the local Qdrant index.
- `rag/loader.py` loads Markdown and PDF sources.
- `rag/splitter.py` chunks them.

### Evidence and decision shaping

- `prepare_evidence(...)` in `tools/noise_to_signal_graph.py`
  converts raw retrieved docs into:
  - `reasoning_evidence`
  - `evidence`
- Those helper summaries come from `tools/study_plan.py`:
  - `_summarize_reasoning_evidence(...)`
  - `summarize_retrieved_evidence(...)`

### Final outcome

The graph ends in one of these terminal response nodes:

- `answer_informational`
- `request_clarification`
- `plan_for_focus`
- `respond_comparison`
- `respond_insufficient`

## 4. Main folders and files

### `app.py`

Main Streamlit application.

What lives here:

- App mode switch for:
  - `Noise-to-Signal Agent`
  - `AI Skill Compass`
  - `Interview Coach (Sprint 1 legacy)`
- Noise-to-Signal UI rendering
- Session state and thread ID handling
- Visible decision summary, evidence, study plan, trace, and technical details

Important functions:

- `_render_noise_to_signal_header()`
- `_render_noise_to_signal_metrics(decision)`
- `_render_noise_to_signal_evidence(decision)`
- `_render_noise_to_signal_result(decision, study_plan)`
- `_start_new_noise_to_signal_conversation()`

If a reviewer asks where the current demo UI behavior is implemented, start
here.

### `tools/noise_to_signal_graph.py`

Main Sprint 3 backend workflow.

What lives here:

- LangGraph `StateGraph` definition
- Bounded retrieval loop
- Clarification memory handling
- Evidence assessment
- One-time query reformulation
- Deterministic routing and optional LLM routing for ambiguous requests
- Final terminal response nodes

Most important public function:

- `run_noise_to_signal(...)`

Most important internal functions:

- `resolve_clarification_context(...)`
- `reset_retrieval_state(...)`
- `determine_request_shape(...)`
- `retrieve_evidence(...)`
- `prepare_evidence(...)`
- `assess_evidence(...)`
- `reformulate_retrieval_query(...)`
- `classify_deterministic_intent(...)`
- `classify_ambiguous_intent_with_llm(...)`
- `route_by_decision_status(...)`

If a reviewer asks where fail-closed behavior is implemented, this is the most
important file.

### `tools/study_plan.py`

Shared deterministic decision and evidence helper logic.

What lives here:

- Goal-shape heuristics
- Evidence item formatting and filtering
- Option scoring for comparisons
- Informational answer building from evidence claims
- Deterministic study plan generation

Important functions:

- `select_diverse_evidence(...)`
- `summarize_retrieved_evidence(...)`
- `build_informational_answer(...)`
- `_select_decision_focus(...)`
- `build_noise_to_signal_decision(...)`
- `generate_study_plan(...)`
- `format_evidence_label(...)`

Why this file matters:

- It contains the older deterministic decision layer that the graph still
  reuses.
- It is where readable evidence labels and evidence summaries are built for the
  UI.

### `rag/retriever.py`

Retriever and vector-store lifecycle.

What lives here:

- OpenRouter-compatible embeddings setup
- Local Qdrant vector store creation and reuse
- Source-manifest fingerprinting
- Cache management for vector stores
- Final semantic retrieval function

Important functions:

- `create_embeddings()`
- `create_vector_store(...)`
- `rebuild_vector_store(...)`
- `retrieve_relevant_chunks(...)`
- `build_documents_from_chunks(...)`
- `clear_cache()`

If a reviewer asks where Qdrant is used, start here.

### `rag/loader.py`

Source loading and metadata extraction.

What lives here:

- Markdown loading from `data/knowledge_base`
- PDF loading from `data/sources/pdfs`
- Metadata derivation such as:
  - `document_role`
  - `source_authority`
  - `title`
  - `published_year`
  - `page`

Important functions:

- `load_markdown_documents(...)`
- `load_pdf_documents(...)`
- `load_documents(...)`

### `rag/splitter.py`

Document chunking.

Important function:

- `split_documents(...)`

This file is small but important because every downstream retrieval result
depends on how the source text was chunked.

### `rag/generator.py`

Older direct RAG answer path.

Important function:

- `answer_with_rag(...)`

This is part of the broader project, but it is not the main Sprint 3
Noise-to-Signal path.

### `rag/evaluation.py`

Evaluation helpers for retrieval quality.

Important functions:

- `evaluate_retrieved_sources(...)`
- `run_evaluation_set(...)`

### `security.py`

Input validation and simple prompt-injection / offensive-language checks.

Important functions:

- `validate_user_input(...)`
- `validate_job_description(...)`

### `openrouter_client.py`

OpenRouter request wrapper with retry behavior and safe user-facing errors.

Important pieces:

- `OpenRouterError`
- `call_openrouter(...)`
- `_should_retry(...)`

## 5. LangGraph node map

These are the actual nodes added in `_build_graph(...)` inside
`tools/noise_to_signal_graph.py`.

### Setup and request-shape nodes

- `reset_retrieval_state`
  Clears per-turn retrieval state while preserving checkpointed conversation
  memory.
- `resolve_clarification_context`
  Merges follow-up clarification context without exposing internal orchestration
  text to the user.
- `determine_request_shape`
  Decides whether the request is likely clarification, informational,
  single-focus, or comparison-shaped before retrieval.

### Retrieval and evidence nodes

- `retrieve_evidence`
  Calls the retriever and increments retrieval attempts.
- `prepare_evidence`
  Builds UI-facing and reasoning-facing evidence structures.
- `assess_evidence`
  Checks whether the retrieved evidence is strong enough for the current request
  shape.
- `reformulate_retrieval_query`
  Builds one deterministic retry query when evidence is weak.

### Routing nodes

- `classify_deterministic_intent`
  Reapplies deterministic decision logic after evidence is available.
- `classify_ambiguous_intent_with_llm`
  Uses structured LLM classification only for genuinely ambiguous cases.

### Terminal response nodes

- `answer_informational`
  Returns an evidence-grounded informational answer.
- `request_clarification`
  Requests a clearer goal.
- `plan_for_focus`
  Builds a study plan for one explicit topic.
- `respond_comparison`
  Returns a selected focus or tie result.
- `respond_insufficient`
  Returns fail-closed insufficient evidence behavior.

## 6. Where specific behaviors live

### Where is the LangGraph workflow defined?

- `tools/noise_to_signal_graph.py`
- Look at `_build_graph(...)`, `NOISE_TO_SIGNAL_GRAPH`, and
  `run_noise_to_signal(...)`.

### Where does retrieval happen?

- Graph call site: `tools/noise_to_signal_graph.py` -> `retrieve_evidence(...)`
- Retriever implementation: `rag/retriever.py` ->
  `retrieve_relevant_chunks(...)`

### Where is evidence assessed?

- `tools/noise_to_signal_graph.py` -> `assess_evidence(...)`

This function is the main groundedness gate for:

- informational questions
- comparison requests
- single-focus requests
- retrieval failure handling

### Where is insufficient evidence decided?

Two places matter:

- `tools/noise_to_signal_graph.py` -> `assess_evidence(...)`
  decides when weak evidence should become `insufficient_evidence`
- `tools/noise_to_signal_graph.py` -> `respond_insufficient(...)`
  formats the final user-facing insufficient-evidence response

### Where is out-of-domain protection for cases like `Tacos al pastor`?

- `tools/noise_to_signal_graph.py`
- Main helper:
  - `_single_focus_has_domain_or_direct_support(...)`
- Supporting helpers:
  - `_is_ai_engineering_domain_focus(...)`
  - `_evidence_directly_mentions_focus(...)`

This is the key fail-closed path for unrelated single-focus requests.

### Where are evidence summaries and labels built?

- `tools/study_plan.py`
- Main functions:
  - `select_diverse_evidence(...)`
  - `summarize_retrieved_evidence(...)`
  - `format_evidence_label(...)`

### Where is the study plan generated?

- `tools/study_plan.py` -> `generate_study_plan(...)`
- The graph calls it through:
  - `tools/noise_to_signal_graph.py` -> `_build_study_plan_for_focus(...)`

### Where does the UI render the result?

- `app.py`
- Main renderer:
  - `_render_noise_to_signal_result(...)`

That function delegates to the individual evidence, metrics, trace, study-plan,
and technical-details sections.

### Where is short-term memory handled?

- `tools/noise_to_signal_graph.py`
- Main pieces:
  - `MemorySaver`
  - `NOISE_TO_SIGNAL_CHECKPOINTER`
  - `resolve_clarification_context(...)`
  - `run_noise_to_signal(..., thread_id=...)`

## 7. Most important tests

### Main graph behavior

- `tests/test_noise_to_signal_graph.py`

This is the most important test file for Sprint 3. It covers:

- request-shape routing
- retrieval retry behavior
- insufficient-evidence behavior
- out-of-domain handling
- clarification memory behavior
- deterministic vs LLM routing
- graph parity with deterministic decision logic

### Main UI behavior

- `tests/test_noise_to_signal_app.py`

This covers the reviewer-facing Streamlit result rendering for:

- clarification
- informational answer
- out-of-scope insufficient evidence

### UI text/copy behavior

- `tests/test_noise_to_signal_ui_copy.py`

This is useful when a reviewer asks where result wording is locked down.

### Deterministic decision and evidence formatting

- `tests/test_study_plan.py`

This covers:

- study plan generation
- evidence selection
- informational answer construction
- option extraction and scoring

### Retriever and vector-store lifecycle

- `tests/test_rag_retriever.py`

This covers:

- Qdrant cache behavior
- manifest fingerprint invalidation
- rebuild behavior
- document conversion to LangChain `Document`

### Other useful test files

- `tests/test_rag_loader.py`
- `tests/test_rag_pipeline.py`
- `tests/test_rag_splitter.py`
- `tests/test_security.py`
- `tests/test_openrouter_client.py`

## 8. Reviewer question shortcuts

If you need a fast answer during the Sprint 3 review:

- LangGraph workflow:
  `tools/noise_to_signal_graph.py`
- Evidence assessment and fail-closed logic:
  `tools/noise_to_signal_graph.py` -> `assess_evidence(...)`
- Qdrant retrieval:
  `rag/retriever.py` -> `retrieve_relevant_chunks(...)`
- Loading Markdown/PDF sources:
  `rag/loader.py`
- Study plan generation:
  `tools/study_plan.py` -> `generate_study_plan(...)`
- Reviewer-facing Streamlit rendering:
  `app.py` -> `_render_noise_to_signal_result(...)`
- Main behavior tests:
  `tests/test_noise_to_signal_graph.py`

## 9. Suggested reading order

If you want to study the code efficiently before the review:

1. `app.py`
   Understand what the reviewer sees.
2. `tools/noise_to_signal_graph.py`
   Understand the Sprint 3 workflow and node boundaries.
3. `tools/study_plan.py`
   Understand evidence shaping, option scoring, and study-plan generation.
4. `rag/retriever.py`, `rag/loader.py`, `rag/splitter.py`
   Understand how evidence enters the system.
5. `tests/test_noise_to_signal_graph.py`
   Understand what behavior is protected by tests.
