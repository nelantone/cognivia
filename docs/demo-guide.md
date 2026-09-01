# Demo Guide

This guide describes a conservative local demonstration of Cognivia. The
current documentation phase did not launch the application, so every visual
and interaction outcome below remains **PENDING manual verification**.

## Offline UI and workflow demo

Follow the local setup in the [README](../README.md) and start in offline mode:

```bash
COGNIVIA_LLM_PROVIDER=offline python -m streamlit run app.py
```

Offline mode is the safest default for a UI and workflow walkthrough because it
does not use OpenAI or OpenRouter model calls. It does not provide
evidence-backed retrieval: local Qdrant retrieval requires a configured
provider embedding key. Do not enter secrets or private learner data.

Suggested offline walkthrough:

1. Open **Noise-to-Signal Agent**.
2. Use the guided intake or a quick prompt to frame a learning question.
3. Inspect how the UI communicates uncertainty when evidence is unavailable.
4. Enter and exit **Focus Mode**.
5. Start a **New search** and confirm that the visible workflow resets.
6. If the result offers an export, inspect the note or learning-plan download
   without treating it as authoritative advice.
7. Briefly show **AI Skill Compass** and **Interview Coach** as separate modes.

## Evidence-backed RAG demo

An evidence-backed retrieval demonstration requires explicitly configured
`openai` or `openrouter` provider access and an embedding-capable API key.
Such a run can incur provider cost and was not performed for this documentation
update. With that access explicitly authorized, submit a question supported by
the local knowledge base and inspect the returned evidence, uncertainty, and
provenance. Do not present this behavior as manually verified until it has been
run and recorded.

The intended story is not autonomous decision-making. Cognivia helps a learner
reduce noise, inspect evidence, and make a better-informed judgment.

## Claims to avoid during a demo

Do not claim a current test total, evaluation score, production deployment,
live-provider reliability, or durable memory unless separately verified.
PostgreSQL-backed memory requires explicit configuration; without it, the null
memory store is selected and durable history is unavailable.

For implementation boundaries and unverified behavior, see
[Architecture](architecture.md), [Testing](testing.md), and
[Evaluation](evaluation.md).
