# Testing

The repository contains automated tests for application, graph, retrieval,
provider, memory, security, and helper boundaries. On 5 October 2026, the
isolated offline suite passed 593 tests in 64.29 seconds.

## Test ownership

| Surface | Repository evidence |
| --- | --- |
| Streamlit flows and UI state | AppTest and application tests under `tests/` |
| Graph routing and state | graph-focused tests under `tests/` |
| Retrieval, corpus loading, and index behavior | RAG-focused tests under `tests/` |
| Provider configuration and selection | provider-focused tests under `tests/` |
| Memory and persistence boundaries | memory-focused tests under `tests/` |
| Input and security behavior | security-focused tests under `tests/` |

The passing suite exercises these surfaces through current automated coverage;
it does not by itself verify live provider behavior or an interactive browser
walkthrough. Separately, one OpenAI-backed retrieval flow was manually verified
on 6 October 2026 with contextual evidence, three evidence items, no retrieval
error, and a rendered Streamlit result without UI errors. Broader live-provider
and interactive-browser behavior remains unverified.

## Validation commands

The isolated full-suite command used by project guidance is:

```bash
env -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  -u COGNIVIA_LLM_PROVIDER -u LANGSMITH_API_KEY \
  -u LANGCHAIN_API_KEY \
  PYTHON_DOTENV_DISABLED=1 \
  LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  .venv/bin/python -m pytest tests -q
```

`PYTHON_DOTENV_DISABLED=1` prevents `.env` from reintroducing provider
credentials after the shell variables are unset. The command also disables
LangSmith and LangChain tracing and clears their API-key environment variables.

Additional checks should be selected according to the changed surface:

```bash
python -m ruff check .
git diff --check
```

Agent-tooling validation is separate from product testing and is not part of
this public product-documentation change.

## Current status

- Automated suite result: **593 passed in 64.29 seconds**
- Automated test total: **593**
- Offline provider and dotenv isolation: **VERIFIED**
- Local startup: **VERIFIED**
- Local health check: **VERIFIED**
- Rendered Streamlit result: **VERIFIED for one OpenAI-backed retrieval flow on
  6 October 2026; broader interactive-browser behavior remains unverified**
- Live provider behavior: **VERIFIED for that single OpenAI-backed retrieval
  flow; broader live-provider behavior remains unverified**
- Evaluation cases and scores: **NOT VERIFIED; no score is claimed**
- LangSmith isolation for the offline suite: **VERIFIED**

Future reports should state the exact command, environment constraints, result,
and date. A passing command is evidence only for the surface it covered.
