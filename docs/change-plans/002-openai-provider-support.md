# Change Plan: OpenAI Provider Support

## 1. Context

Cognivia currently uses OpenRouter-compatible configuration through
`OPENROUTER_API_KEY`. The OpenRouter base URL and key are embedded in the direct
chat client, RAG generation, RAG embeddings, and the Noise-to-Signal structured
intent classifier. Existing deterministic routing and local Qdrant behavior are
important offline paths. OpenAI support must be explicit because the available
OpenAI credit is limited.

## 2. Goal

Add an explicit provider selector:

```text
COGNIVIA_LLM_PROVIDER=openrouter | openai | offline
```

`openrouter` keeps the current behavior and uses `OPENROUTER_API_KEY`;
`openai` uses `OPENAI_API_KEY` with the OpenAI-native default base URL; and
`offline` disables provider calls and keeps deterministic/local flows available
where possible. Missing or unsupported configuration must produce a clear,
safe status or domain error without breaking unrelated local UI flows.

## 3. Out of scope

- Replacing Qdrant or changing vector-store persistence and collection behavior.
- Changing learner memory, checkpointing, or database behavior.
- Enabling OpenRouter by default or making OpenAI the default provider.
- Live API calls, API-credit usage, or network-dependent tests.
- Adding model-selection UX beyond what is required to select a provider.
- Secret management, key rotation, billing controls, or `.env` changes.
- Broad refactoring of the LangGraph, RAG, or Streamlit architecture.

## 4. Current state

- `openrouter_client.py` posts directly to the OpenRouter chat-completions URL.
- `app.py` calls that client for the legacy interview flow and catches
  `OpenRouterError`.
- `rag/generator.py` constructs `ChatOpenAI` with the OpenRouter base URL and
  key for grounded answer generation.
- `rag/retriever.py` constructs `OpenAIEmbeddings` with the OpenRouter base URL
  and key before creating/loading the local Qdrant store.
- `tools/noise_to_signal_graph.py` constructs `ChatOpenAI` with the OpenRouter
  base URL and key for ambiguous-intent structured output; deterministic routes
  can avoid this call.
- `tools/runtime_status.py` currently detects keys, reports OpenRouter when its
  key exists, and explicitly reports that an OpenAI key is not supported.
- `.env.example` contains an OpenRouter placeholder only. No runtime files or
  tests should read or write `.env` or contain real secrets.

## 5. Proposed design

Introduce one small provider-configuration/factory seam, preferably a focused
module such as `llm_provider.py`, that:

1. Normalizes `COGNIVIA_LLM_PROVIDER` and validates it against the three allowed
   values.
2. Selects the required environment key without logging or exposing its value.
3. Builds chat and embedding clients from provider-specific settings.
4. Uses OpenRouter's existing base URL only for `openrouter`; leaves the OpenAI
   base URL unset/default for `openai`.
5. Returns an explicit offline/no-client result or raises a safe, typed
   configuration error for provider-required operations.

Keep `call_openrouter` as a compatibility wrapper for the existing OpenRouter
path, or rename only behind a narrow provider-neutral entry point after its
payload and retry tests are preserved. Route the interview flow, RAG generator,
and graph classifier through the chat factory. Route `create_embeddings` through
the embedding factory. Offline mode must bypass provider construction and retain
deterministic answers/routing or an honest local limitation message.

Reuse `langchain_openai.ChatOpenAI` and `OpenAIEmbeddings`: they already exist in
the project and support both OpenAI-native and OpenAI-compatible endpoints. The
provider seam should supply model, key, and optional base URL rather than adding
another HTTP or SDK dependency.

## 6. Key decisions

- Support both chat and embeddings. Chat is needed by the interview flow, RAG
  generation, and ambiguous-intent classifier; embeddings are needed to build
  or rebuild the Qdrant-backed RAG index.
- Provider selection is explicit. A key alone must not silently select OpenAI.
- `openrouter` preserves the current URL, key, model naming, retry policy, and
  existing behavior.
- `openai` uses `OPENAI_API_KEY` and OpenAI-native URL defaults. Model names must
  be reviewed separately because OpenRouter-prefixed names are not necessarily
  valid OpenAI model identifiers.
- `offline` is a first-class visible mode, not an accidental missing-key state.
- Missing key, invalid provider, and provider/key mismatch produce clear
  configuration diagnostics; deterministic local flows remain usable.
- Runtime status reports the selected provider and configuration state without
  making a network call or displaying secrets.
- `.env.example` may add only blank or placeholder entries for
  `COGNIVIA_LLM_PROVIDER` and `OPENAI_API_KEY`.

## 7. Alternatives considered

- Duplicating OpenAI branches in every caller: rejected because configuration
  and error semantics would drift across chat and embedding paths.
- Replacing all callers with a new large provider class hierarchy: rejected as
  unnecessary for three modes and harder to test.
- Using the OpenAI SDK directly: deferred because the existing LangChain OpenAI
  classes already cover both required interfaces.
- Selecting a provider based on whichever key is present: rejected because it
  could spend limited OpenAI credit unexpectedly and makes status misleading.
- Keeping embeddings OpenRouter-only: rejected because an OpenAI chat provider
  cannot reliably rebuild or refresh the RAG index without a matching explicit
  embedding configuration.

## 8. Risks

- OpenRouter model identifiers may not work on OpenAI; define provider-appropriate
  defaults and document model configuration.
- A provider switch can make existing persisted embeddings semantically
  incompatible. Preserve Qdrant but plan an explicit rebuild/version or provider
  identity check before mixing indexes.
- Import-time environment snapshots can make tests and UI status stale; read
  configuration through testable functions at call time or make cache scope
  explicit.
- A missing embedding key currently fails retrieval/index creation. Convert this
  to a safe, user-visible local limitation while preserving deterministic flows.
- Structured-output support and model-specific parameters may differ; keep the
  existing validation/fallback path and test provider-neutral behavior.

## 9. Implementation plan

1. Add provider constants, normalization, required-key lookup, safe error types,
   and chat/embedding factories in one focused module.
2. Adapt the direct interview client while preserving its OpenRouter wrapper,
   retry rules, payload shape, and non-secret error messages.
3. Replace hardcoded client construction in `rag/generator.py`,
   `rag/retriever.py`, and `tools/noise_to_signal_graph.py` with the factories.
4. Define offline behavior at each call site: deterministic graph/routing paths,
   local retrieval when an index is available, and concise limitation messages
   when a provider-backed operation is required.
5. Update `tools/runtime_status.py` to distinguish configured OpenRouter,
   configured OpenAI, explicit offline, missing configuration, and unsupported
   provider values. Keep status side-effect free.
6. Add placeholder-only provider variables to `.env.example`.
7. Add focused offline tests and update existing OpenRouter tests without making
   any live request or requiring Qdrant/network/API credentials.

## 10. Acceptance criteria

- `COGNIVIA_LLM_PROVIDER=openrouter` keeps existing OpenRouter chat and embedding
  behavior working with `OPENROUTER_API_KEY`.
- `COGNIVIA_LLM_PROVIDER=openai` uses `OPENAI_API_KEY` for both chat and
  embeddings and does not use the OpenRouter URL or key.
- `COGNIVIA_LLM_PROVIDER=offline` makes no provider calls and leaves supported
  deterministic/local flows usable and visible.
- Invalid, missing, or mismatched configuration produces an honest, concise
  diagnostic and does not crash unrelated local UI paths.
- Runtime status accurately identifies OpenRouter, OpenAI, offline, and invalid/
  missing configuration without exposing key values.
- Qdrant and memory behavior are unchanged.
- No `.env`, secret, live API call, or OpenAI credit is required by tests.

## 11. Validation plan

- Unit-test provider normalization, key selection, base URL selection, offline
  behavior, invalid values, and missing/mismatched keys.
- Mock `ChatOpenAI`, `OpenAIEmbeddings`, and HTTP request seams to assert
  construction and payload routing; assert no network calls occur.
- Preserve and extend direct-client retry and temperature/model parameter tests.
- Test runtime-status strings for each provider state and empty-key cases.
- Test deterministic graph and RAG fallback behavior with fake retrievers/models.
- Run the focused provider, runtime-status, graph, generator, and retriever
  tests, then the full suite, Ruff, `git diff --check`, and the sentinel.
- Perform a local UI smoke test only with `offline`; do not use live credentials.

## 12. Open questions

- Which OpenAI chat and embedding model identifiers should be the documented
  defaults, and should they be configurable independently?
- Should provider identity be included in the Qdrant index metadata/key so a
  provider switch requires an explicit rebuild?
- Should explicit `offline` differ in status wording from missing provider
  configuration, even though both avoid live calls?
- Should the legacy interview flow call the new provider-neutral function
  directly, or retain `call_openrouter` as a compatibility API during rollout?
- What exact UI action should offer an index rebuild after an embedding-provider
  change?

## 13. Notes for CXP

Treat this as a staged configuration and dependency-boundary change. First land
provider selection and side-effect-free factories, then wire one path at a time
with offline tests. Keep OpenRouter behavior as the regression baseline. Do not
enable OpenAI implicitly, spend credits during validation, or claim provider
support until both chat and embeddings have mocked coverage. Ask `/review` to
check provider isolation, secret handling, fallback honesty, and persisted-index
compatibility before implementation is closed.
