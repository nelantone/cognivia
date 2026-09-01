<p align="center">
  <img src="assets/cognivia-full-clean.png" alt="Cognivia logo" width="520">
</p>

# Cognivia

Cognivia is a Python and Streamlit application for turning noisy learning
questions into evidence-aware next steps. Its product principle is simple:
strengthen human judgment rather than replace it.

## The problem Cognivia addresses

AI learners face an overload of tools, topics, frameworks, role labels, and
generic recommendations. A fluent answer alone does not show whether a goal
was understood, whether evidence directly supports a recommendation, whether
the request is outside the available evidence, or what the learner should
reflect on before acting.

Cognivia treats this as a learning-decision workflow rather than a one-shot
answer-generation task. It helps a learner clarify the question, inspect the
strength and limits of available evidence, choose a direction, and retain
authority over the decision.

## What it does

The current application provides three modes:

- **Noise-to-Signal Agent** — retrieves local learning evidence, identifies
  ambiguity, and produces an answer, clarification, comparison, or learning
  plan.
- **AI Skill Compass** — helps frame skill-development questions.
- **Interview Coach** — supports structured interview practice.

The primary Noise-to-Signal flow routes vague or context-only goals to guided
intake and uses a direct-decision path for clear requests. It includes quick
prompts, a Focus Mode, source-aware responses, and exportable notes or learning
plans. Where a configured provider can create embeddings, it retrieves from the
bundled knowledge base through local Qdrant. Retrieval relevance is not treated
as direct support: the graph separately assesses whether evidence supports the
request and can return low-evidence or out-of-scope outcomes. Provider behavior
and capability differ by configuration. Optional PostgreSQL-backed learner
memory is append-only; without a database URL, the null store provides no
durable history.

## How the primary workflow works

1. The learner enters a goal or question directly or through guided intake.
2. The bounded application graph shapes the request and decides whether
   retrieval is needed.
3. When provider configuration supports embeddings, RAG retrieves from
   `data/knowledge_base/` through local Qdrant.
4. The graph treats retrieval relevance as a candidate filter, then separately
   checks whether the evidence directly supports the request.
5. The workflow can answer, ask for clarification, produce a focused plan,
   compare supported options, or return an insufficient-evidence outcome.
6. The learner can inspect the evidence state, select a learning path, save a
   Study note, and export reflection or learning-plan material.

The graph is bounded: an insufficient first retrieval can trigger one query
reformulation and one retry. It is not an open-ended autonomous agent.

## Why Cognivia, not ChatGPT?

General-purpose LLMs provide broad language and reasoning capabilities.
Cognivia does not try to replace them as general assistants; it provides a
bounded methodology around their use for learning decisions. Goal
clarification, explicit evidence states, learning paths, reflection, runtime
transparency, and learner authority are product responsibilities rather than
properties supplied by a model alone.

See [Why Cognivia and Not Just ChatGPT?](docs/product/why-cognivia-not-chatgpt.md)
for the fuller product rationale.

## Capabilities and boundaries

Implemented in the current repository:

- a Streamlit application with Noise-to-Signal Agent, AI Skill Compass, and
  Interview Coach modes;
- guided intake, direct-query routing, quick prompts, Focus Mode, and new-search
  reset behavior;
- bounded LangGraph orchestration with explicit answer, clarification, plan,
  comparison, and insufficient-evidence outcomes;
- recursive Markdown/PDF loading, token-aware chunking, heading and provenance
  metadata, local Qdrant retrieval, relevance filtering, and direct-support
  assessment;
- selectable learning paths, next-step guidance, Study notes, and Markdown or
  JSON exports, including a full learning-plan Markdown export;
- explicit `offline`, `openai`, and `openrouter` provider modes; and
- an optional append-only PostgreSQL learner-memory foundation with a null
  fallback when durable storage is not configured.

Important limits:

- Offline mode demonstrates local UI and deterministic workflow paths, but it
  is not provider-backed RAG and cannot create or query the embedding index.
- Provider capabilities and behavior are not equivalent across configurations.
- Retrieval relevance does not prove direct support, and Cognivia does not
  eliminate hallucinations or guarantee factual certainty.
- The bundled corpus is curated and limited; legitimate questions can produce
  an insufficient-evidence outcome.
- Local Qdrant and the current memory foundation are suitable for local
  development, not proof of production-grade index integrity or multi-user
  persistence.
- Production hosting, authentication, authorization, privacy isolation,
  backups, rate limiting, scalability, and deployment hardening are not
  claimed.

## Run locally

Prerequisites:

- Python
- A virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
COGNIVIA_LLM_PROVIDER=offline python -m streamlit run app.py
```

The offline command avoids OpenAI and OpenRouter model calls. It supports a
local UI and workflow demonstration, but it does not provide evidence-backed
retrieval because creating/querying the local index requires a configured
provider embedding key. Provider credentials and optional database settings are
documented in [`.env.example`](.env.example); never commit real secrets.

The setup command and current UI flow were not executed as part of this
documentation recovery. Runtime behavior therefore remains **PENDING manual
verification**.

## Demo and validation guidance

For an offline walkthrough, select **Noise-to-Signal Agent**, use guided intake
or a quick prompt, inspect the communicated uncertainty, enter and exit Focus
Mode, reset with **New search**, and inspect any offered note or learning-plan
export. These interaction outcomes remain expected rather than manually
verified in this recovery commit.

An evidence-backed RAG demonstration requires explicitly authorized OpenAI or
OpenRouter access with an embedding-capable key and may incur provider cost.
See the [demo guide](docs/demo-guide.md) for the conservative walkthrough and
[testing](docs/testing.md) for validation commands and current evidence limits.
No product test total or evaluation score is claimed here.

## Architecture

```text
Streamlit UI
    |
    v
Application graph ──> request shaping / routing
    |                         |
    v                         v
Local RAG                 provider boundary
    |
    v
Markdown/PDF knowledge base

Optional PostgreSQL memory sits behind the memory-store boundary.
```

Presentation, orchestration, retrieval, provider access, memory, persistence,
security, and evaluation remain separate implementation concerns. See
[`docs/architecture.md`](docs/architecture.md) for the verified component
map.

## Documentation map

- [Architecture](docs/architecture.md)
- [Demo guide](docs/demo-guide.md)
- [Testing](docs/testing.md)
- [Evaluation](docs/evaluation.md)
- [Sources and provenance](docs/sources.md)
- [Product rationale: Why Cognivia and Not Just ChatGPT?](docs/product/why-cognivia-not-chatgpt.md)
- [Guided learning intake](docs/guided-learning-intake.md)
- [Future improvements](docs/future-improvements.md)
- [Engineering history](docs/engineering-history.md)
- [Project evolution](docs/project-evolution.md)

No test total or evaluation score is claimed here. Current validation status
and the commands used to establish it belong in the linked testing and
evaluation documents.

## Licensing

Cognivia source code is licensed under the [MIT License](LICENSE), copyright
(c) 2026 Antonio Serna Gutiérrez.

Project documentation remains copyrighted by Antonio Serna Gutiérrez unless a
document explicitly states otherwise. Brand, image, video, screenshot, and
other media assets are excluded from the MIT License and remain all rights
reserved unless explicitly stated otherwise. See
[Asset provenance](ASSET_PROVENANCE.md) for the project-owned asset boundary.

Third-party materials retain their original rights and licenses. See
[Third-party notices](THIRD_PARTY_NOTICES.md) for retained and excluded source
artifacts.
