# Cognivia Demo Script

Use offline mode unless OpenAI/OpenRouter and Qdrant are already configured deliberately. Do not rely on live provider calls during the main demo.

## 20-Second Explanation

Cognivia is an evidence-aware AI learning coach. It helps learners turn noisy AI-learning goals into clearer next steps through a bounded workflow: clarify the goal, check evidence, show learning paths, and ask the learner to reflect before deciding what to do next.

## Safe Demo Startup

```bash
unset OPENAI_API_KEY
unset OPENROUTER_API_KEY

export COGNIVIA_LLM_PROVIDER=offline
export LANGSMITH_TRACING=false
export LANGCHAIN_TRACING_V2=false

.venv/bin/python -m streamlit run app.py
```

In the sidebar, select `Noise-to-Signal Agent`.

Point out:

- Runtime status.
- `Runtime details`.
- Offline provider mode.
- Memory fallback if `DATABASE_URL` is not configured.
- Local Qdrant/RAG evidence path.
- Codex/ChatGPT Plus is development tooling, not the app runtime provider.
- Background media controls: video playback and background style.

## 10-Minute Flow

### 0:00-1:00 - Problem

AI learners face too many tools, frameworks, topics, and career paths. Generic AI answers can sound confident without showing whether the recommendation fits the learner or is supported by evidence.

### 1:00-2:00 - What Cognivia Is

Cognivia is a local evidence-aware learning coach. It is designed to strengthen human judgment, not replace it.

### 2:00-3:30 - Why Not Just ChatGPT

General-purpose LLMs already read documents, summarize, ask questions, and recommend. Cognivia adds a learning and decision methodology around those capabilities: goal clarification, evidence states, bounded learning paths, reflection, provider transparency, and human authority.

### 3:30-5:00 - Architecture and Evidence Flow

Summarize:

- Streamlit UI.
- Bounded LangGraph workflow.
- Recursive local corpus loading from `data/knowledge_base`.
- Token-aware chunking.
- Embeddings and local Qdrant where configured.
- Evidence relevance separated from direct support.
- Low-evidence and out-of-scope behavior.

### 5:00-8:00 - Controlled Three-Step Demo

1. Submit a learning goal or question.
   Use:

   ```text
   What should I learn next?
   ```

   Explain that vague goals should trigger guided intake rather than fake certainty.

2. Inspect recommendation, evidence state, and learning paths.
   Complete the guided intake with realistic values. Show recommendation explanation, evidence status, career/skill-gap framing where present, and numbered learning direction schemas.

3. Select a path and show reflection / Study note / export.
   Choose a path, save a Study note, and mention Markdown/JSON export behavior.

Optional safety check:

```text
Tacos al pastor
```

Show that Cognivia does not force an unrelated AI-learning recommendation.

### 8:00-9:00 - Technical Decisions and Trade-Offs

- LangGraph keeps the workflow explicit and bounded.
- Qdrant provides local semantic retrieval.
- Evidence assessment avoids treating similarity as enough.
- Offline mode makes demos safe.
- Memory is append-only and durable only where configured.

### 9:00-10:00 - Limitations and Next Steps

Be explicit:

- Current app is validated for local demonstration.
- Public deployment readiness is not fully validated.
- Production readiness is not claimed.
- Future work includes Study Coach, Thinking Coach, Focus Mode, stronger evaluation, production memory, deployment hardening, and historical documentation cleanup.

## Demo Plan B

If a live rerun fails:

- Keep offline mode and tracing disabled.
- Use architecture diagrams from [Architecture](architecture.md).
- Use existing screenshots under `docs/demo-screenshots/` if useful.
- Explain the expected flow rather than debugging optional providers live.
- Do not edit `.env` live.
- Do not rebuild embeddings or Qdrant during the presentation.

## Avoid During Live Demo

- Do not depend on live OpenAI/OpenRouter calls unless explicitly configured and approved.
- Do not claim production auth, full note CRUD, pgvector RAG, Focus Mode, Study Coach, or Thinking Coach is implemented.
- Do not use stale control names; describe background media controls by function.
- Do not claim every recommendation is evidence-backed. Use evidence-backed only when retrieval directly supports it.
