# Cognivia Manual Smoke-Test Checklist

Use this checklist before a project demo or technical walkthrough.

## Setup

- [ ] Start from the intended branch/worktree.
- [ ] Use safe offline runtime:

```bash
unset OPENAI_API_KEY
unset OPENROUTER_API_KEY

export COGNIVIA_LLM_PROVIDER=offline
export LANGSMITH_TRACING=false
export LANGCHAIN_TRACING_V2=false

.venv/bin/python -m streamlit run app.py
```

- [ ] Confirm `.env` is not displayed or committed.

## App Startup

- [ ] App starts without a crash.
- [ ] Sidebar renders.
- [ ] `Noise-to-Signal Agent` is selectable.
- [ ] Runtime status is visible.
- [ ] Offline provider mode is visible when configured.
- [ ] `Runtime details` explains provider, memory, evidence, API-credit, and Codex/ChatGPT tooling boundaries.
- [ ] Missing optional providers do not break app startup.
- [ ] Missing `DATABASE_URL` degrades to local fallback / no durable DB status.
- [ ] No large `Display options` checkbox panel appears.
- [ ] Background media controls are visible for playback and background style.
- [ ] Background controls remain visible after query submission.
- [ ] Buttons remain clickable on a narrower browser window.

## Noise-to-Signal Flow

- [ ] Direct Noise-to-Signal request works for a valid AI-learning question.
- [ ] Guided intake appears for vague input such as `What should I learn next?`.
- [ ] Guided intake form accepts realistic learner context.
- [ ] Guided intake recommendation renders without raw stack traces.
- [ ] Recommendation explanation renders in plain language.
- [ ] AI career path explanations render where relevant.
- [ ] Skill gap explanations render where relevant.
- [ ] Off-topic/no-evidence input such as `Tacos al pastor` fails closed or asks for relevant context.
- [ ] Evidence area renders; if no evidence is available, the app labels that honestly.
- [ ] Decision summary and technical details are understandable.

## Learning Direction and Memory

- [ ] Learning direction schemas render as numbered cards.
- [ ] Schema subtitles are visible.
- [ ] Selecting a schema with `Choose this path` works.
- [ ] Selected path remains visible after rerun.
- [ ] Study note / mini notebook appears after path selection.
- [ ] Saving a note works or degrades with a safe local/durable-memory message.
- [ ] Memory events are recorded when memory is available: `learning_direction_generated`, `learning_direction_selected`, `learning_note_saved`.
- [ ] Recent memory/history renders when events are available.
- [ ] Learner memory JSON export appears when there is memory content.
- [ ] Export does not include secrets or full retrieved document text.

## Safety and Degradation

- [ ] No API keys, tokens, raw provider errors, or raw stack traces are shown.
- [ ] Optional providers disabled do not break the offline demo.
- [ ] Optional durable memory disabled does not block the learner flow.
- [ ] Local Qdrant busy/unavailable messages are concise if encountered.
- [ ] No live API calls are made during offline smoke testing.

## Validation Commands

Complete suite:

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

Do not force `COGNIVIA_LLM_PROVIDER=offline` for the complete suite because provider-selection tests exercise mocked provider scenarios.

## Demo Notes

- [ ] Capture screenshots only if useful for presentation backup.
- [ ] Note any optional service not running.
- [ ] Note any known local warning separately from product behavior.
- [ ] Do not claim production readiness beyond the documented local scope.
