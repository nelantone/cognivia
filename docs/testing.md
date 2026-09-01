# Testing

The repository contains automated tests for application, graph, retrieval,
provider, memory, security, and helper boundaries. No product tests were run
during this documentation-only update, so no passing total is claimed.

## Test ownership

| Surface | Repository evidence |
| --- | --- |
| Streamlit flows and UI state | AppTest and application tests under `tests/` |
| Graph routing and state | graph-focused tests under `tests/` |
| Retrieval, corpus loading, and index behavior | RAG-focused tests under `tests/` |
| Provider configuration and selection | provider-focused tests under `tests/` |
| Memory and persistence boundaries | memory-focused tests under `tests/` |
| Input and security behavior | security-focused tests under `tests/` |

File presence verifies test coverage intent, not that the current suite passes.

## Validation commands

The isolated full-suite command used by project guidance is:

```bash
env -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  -u COGNIVIA_LLM_PROVIDER -u LANGSMITH_API_KEY \
  -u LANGCHAIN_API_KEY \
  LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests -q
```

The pytest bootstrap sets LangSmith and LangChain tracing flags to false and
clears their API-key environment variables. This isolates tests from local shell
or `.env` tracing configuration; it does not establish that the suite passes.

Additional checks should be selected according to the changed surface:

```bash
python -m ruff check .
git diff --check
```

Agent-tooling validation is separate from product testing and is not part of
this public product-documentation change.

## Current status

- Automated suite result: **PENDING**
- Automated test total: **PENDING**
- Streamlit browser walkthrough: **PENDING**
- Live provider behavior: **PENDING**
- Evaluation cases and scores: **PENDING**
- Current LangSmith-isolation test result: **PENDING**

Future reports should state the exact command, environment constraints, result,
and date. A passing command is evidence only for the surface it covered.
