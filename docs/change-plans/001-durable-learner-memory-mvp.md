# Change Plan: Durable Learner Memory MVP

## 1. Context

Cognivia currently supports guided intake, Noise-to-Signal decisions, study plans,
and evidence-aware RAG backed by Qdrant. It does not persist meaningful learner
history across app restarts.

The MVP should add durable learner memory without changing the current evidence
retrieval path. Qdrant remains the evidence RAG store. PostgreSQL stores learner
memory. pgvector is optional later memory search.

## 2. Goal

Add a small durable memory layer so Cognivia can:

* remember structured learner profiles and learning events;
* show recent goals, recommendations, selected focus, and next actions;
* show the current learning direction from the latest stored recommendation;
* export stored learner history as JSON;
* continue working when the database is unavailable.

“Current learning path/direction” means the latest stored recommended direction,
selected focus, and next action. It is not a new progress-tracking model.

## 3. Out of scope

This MVP will not:

* replace Qdrant for evidence retrieval;
* make PostgreSQL the knowledge-base store;
* require pgvector or semantic memory search;
* make live OpenRouter calls in tests;
* require live embeddings in tests;
* store full retrieved documents or full chat transcripts in learner memory;
* edit `.env`;
* implement production authentication, privacy controls, or account management;
* implement a complex dashboard;
* redesign the Streamlit UI.

## 4. Current state

Cognivia currently has:

* guided learner intake;
* Noise-to-Signal decision flow;
* study plan generation;
* evidence-aware RAG backed by Qdrant;
* Streamlit session state for temporary UI state;
* no durable learner memory across app restarts.

Existing behavior that must not break:

* Qdrant evidence retrieval;
* guided intake;
* study plan generation;
* Noise-to-Signal recommendations;
* guardrails and input validation;
* offline tests without live OpenRouter calls.

## 5. Proposed design

Use a small `MemoryStore` boundary so app code depends on a store contract, not
directly on SQLAlchemy or PostgreSQL.

Responsibilities:

* Qdrant: evidence RAG over the local knowledge base.
* PostgreSQL: durable learner profiles, learning events, recommendations, next
  actions, and evidence references.
* pgvector: optional later memory search over derived memory summaries.
* Streamlit session state: immediate UI state for the current session.
* PostgreSQL memory: durable defaults/history used across sessions.

Initial memory should store:

* learner ID;
* learner profile snapshot;
* learner goal;
* selected focus;
* recommended direction;
* recommendation;
* next action;
* evidence references, not full evidence text;
* decision status and interaction type;
* timestamp.

MVP learner identity:

* generate one local demo learner ID;
* store it in Streamlit session state;
* defer real authentication and production accounts.

The store must fail gracefully. If PostgreSQL is unavailable, Cognivia should keep
the current in-session behavior and should not expose raw database errors in the UI.

## 6. Key decisions

| Decision | Choice | Reason |
| --- | --- | --- |
| Evidence retrieval | Keep Qdrant | It already powers grounded RAG and should not be migrated in this MVP |
| User memory | Add `MemoryStore` boundary | Keeps UI and graph code separate from persistence details |
| Durable storage | PostgreSQL | Better fit for structured profiles, events, and history |
| Learner identity | Local demo learner ID in session state | Enough for the current MVP before auth |
| Vector memory | Defer pgvector search | Avoids embeddings and extension setup in early phases |
| Export | JSON only | Smallest useful export format for the MVP |
| UI | Minimal history/current-direction section | Avoids dashboard scope creep |

## 7. Implementation plan

Small steps, ideally one commit per phase.

### Phase 1: Foundation

Scope:

* Add `MemoryStore` protocol/contract.
* Add schema normalization for learner profiles and learning events.
* Add `NullMemoryStore`.
* Add `InMemoryMemoryStore` test fake.
* Add minimal `PostgresMemoryStore` boundary and schema foundation.
* Add `.env.example` `DATABASE_URL=` placeholder only.
* Do not wire `app.py` yet.

Tests:

* profile normalization and validation;
* event payload normalization;
* null-store fallback behavior;
* in-memory store latest-profile and recent-event behavior;
* default schema does not require pgvector.

Commit message:

```text
Add memory store contract and Postgres schema foundation
```

### Phase 2: Write Events

Scope:

* Initialize a memory store in `app.py`.
* Create or reuse the local demo learner ID in Streamlit session state.
* Save guided intake learner profiles and recommendation events.
* Save Noise-to-Signal decision events.
* Keep recommendations working when memory writes fail.

Tests:

* guided intake saves profile and learning event through a fake store;
* Noise-to-Signal decision saves event through a fake store;
* store failure does not break the user flow;
* no live OpenRouter, embeddings, or database required.

Commit message:

```text
Persist guided learning events to memory store
```

### Phase 3: Read and Display History

Scope:

* Read recent learning events for the local demo learner.
* Show a minimal previous-history section.
* Show current learning direction from the latest stored recommended direction,
  selected focus, and next action.
* Keep Streamlit session state as the immediate UI state.
* Use PostgreSQL only for durable defaults/history.

Tests:

* recent events render when available;
* unavailable memory store leaves the UI usable;
* latest event drives the current-direction display;
* existing guided intake and Noise-to-Signal flows still render.

Commit message:

```text
Display recent learner memory history
```

### Phase 4: JSON Export

Scope:

* Add a JSON-only download for stored learner history.
* Include learner profile snapshots and learning events.
* Do not include full retrieved documents, full chat transcripts, secrets, or raw
  database errors.

Tests:

* export payload includes expected profile and event fields;
* empty history exports a safe empty structure;
* database unavailable path does not crash.

Commit message:

```text
Add JSON export for learner memory
```

### Phase 5: Optional pgvector Memory Search

Scope:

* Add memory summary embeddings only if local PostgreSQL + pgvector setup is
  reliable.
* Keep embedding generation injectable for tests.
* Fall back to recency or keyword search when embeddings or pgvector are
  unavailable.

Tests:

* fake embeddings support deterministic search tests;
* search is scoped by learner ID;
* pgvector-unavailable path falls back cleanly;
* no live embeddings or OpenRouter calls in tests.

Commit message:

```text
Add optional pgvector memory search foundation
```

## 8. Acceptance criteria

### Phase 1: Foundation

* [ ] `MemoryStore` contract exists.
* [ ] `NullMemoryStore` returns safe no-op values.
* [ ] `InMemoryMemoryStore` supports offline tests.
* [ ] PostgreSQL schema foundation exists without requiring a live database.
* [ ] Default tests pass without pgvector, OpenRouter, embeddings, or PostgreSQL.

### Phase 2: Write Events

* [ ] Guided intake can save a learner profile and learning event.
* [ ] Noise-to-Signal can save a learning event.
* [ ] Event payloads include goal, recommendation, next action, selected focus,
  decision status, interaction type, timestamp, and evidence references.
* [ ] Memory write failures do not block recommendations or expose raw DB errors.

### Phase 3: Read and Display History

* [ ] The user can see recent previous learning events in the UI.
* [ ] The user can see the current learning direction from the latest stored event.
* [ ] DB-unavailable behavior leaves the app usable.
* [ ] Existing Qdrant RAG, guided intake, and Noise-to-Signal flows still work.

### Phase 4: Export

* [ ] The user can download learner history as JSON.
* [ ] Export excludes full retrieved documents, full chat transcripts, and secrets.
* [ ] Empty or unavailable memory exports are handled safely.

### Phase 5: Optional pgvector Memory Search

* [ ] Semantic memory search is optional.
* [ ] Tests use fake embeddings only.
* [ ] Missing pgvector or embeddings falls back to recency or keyword behavior.

## 9. Validation plan

Run focused validation per phase.

Phase 1:

```bash
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests/test_memory_store.py -q
python -m ruff check memory tests/test_memory_store.py
git diff --check
```

Phase 2:

```bash
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests/test_noise_to_signal_app.py tests/test_guided_intake.py -q
python -m ruff check app.py memory tests
git diff --check
```

Phase 3 and Phase 4:

```bash
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests/test_noise_to_signal_app.py tests/test_guided_intake.py -q
python -m ruff check app.py memory tests
git diff --check
```

Phase 5:

```bash
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests/test_memory_store.py -q
python -m ruff check memory tests
git diff --check
```

Manual checks after UI phases:

* run guided intake and confirm a learning event is saved;
* refresh or restart and confirm recent history is visible;
* confirm current direction reflects the latest stored event;
* download JSON history;
* run an existing evidence/RAG query and confirm Qdrant behavior still works;
* simulate unavailable database and confirm graceful fallback.

## 10. Risks

* Breaking Qdrant-backed evidence RAG by mixing evidence storage and learner memory.
* Expanding the UI into a dashboard before the memory path is stable.
* PostgreSQL setup taking longer than expected.
* Memory failures leaking raw database errors to users.
* Storing sensitive learner context, full transcripts, or full evidence text.
* Letting pgvector or embeddings become required for tests.
* Treating “progress” as a new product model instead of the latest stored
  recommendation fields.

## 11. Notes for Codex

Codex should:

* keep phases small and reversible;
* implement Phase 1 before any `app.py` wiring;
* not replace Qdrant;
* not require live OpenRouter, live embeddings, pgvector, or PostgreSQL in tests;
* not edit `.env`;
* prefer `MemoryStore` over direct database calls from `app.py`;
* implement fallback behavior before UI polish;
* create tests with each phase, not at the end.
