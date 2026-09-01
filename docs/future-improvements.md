# Future Improvements and To-do

This document separates immediate final-review items from post-presentation hardening. It should not be read as a claim that future features are implemented.

For current behavior, start with [README](../README.md),
[Architecture](architecture.md), the
[technical review guide](capstone-reviewer-guide.md), and
[Current state, validation, and next steps](current-state-validation-and-next-steps.md).

## Before Release If Still Relevant

- Verify final Git state.
- Diagnose active `rag/evaluation.py` expected-source path drift. The current loader default is `data/knowledge_base`; do not treat older `data/sources/pdfs` references as fixed by documentation alone.
- Complete one final human smoke test.
- Perform a final documentation review.
- Verify relative links and paths.
- Rehearse demo and Q&A.
- Confirm deployment claims remain conservative.

## Future Hardening

### Retrieval, Corpus, and Evidence

- Add corrupt/encrypted PDF handling per file/page so one bad PDF does not block the full corpus.
- Add richer PDF metadata and provenance where source quality matters.
- Explicitly classify visual-reference PDFs as primary evidence or non-primary reference material.
- Expand the evaluation dataset for groundedness, out-of-scope prompts, weak evidence, and comparison cases.
- Explore reranking or hybrid retrieval after the current Qdrant path remains stable.
- Review whether an LLM evidence judge adds value without weakening deterministic safeguards.

### Product Workflow

- Complete Study Coach as a separately scoped learning workflow.
- Complete Thinking Coach as a separately scoped judgment/reflection workflow.
- Implement Focus Mode only through a separately reviewed frontend/product change.
- Add stronger refinement loops after a recommendation.
- Add progress checkpoints and mastery checks without implying automated learning outcomes.

#### Study Note v2

Current Study Note / Learning Plan exports combine the recommendation, learning path, today's study session, and reusable study methodology. This is comprehensive, but it can become repetitive across multiple exported notes.

Future versions could separate the export into:

1. Personalized Learning Note: learning goal, recommendation, selected learning path, today's mission, checkpoint, and reflection.
2. Reusable Study Toolkit: Feynman, 80/20, learning ladder, mastery quiz, one-page study sheet, and reflection framework.

Another future improvement is replacing template-like actions with topic-specific study actions so exported tasks reference the actual recommended topic rather than internal recommendation wording.

### Memory and Data

- Move beyond append-only learner memory toward production-grade memory only after privacy, deletion, and account boundaries are designed.
- Add multi-user isolation before any public multi-user deployment.
- Consider pgvector for semantic learner memory search later; current RAG remains Qdrant.
- Keep memory exports sanitized and avoid storing full retrieved documents or full chat transcripts.

### Providers and Observability

- Review provider fallback behavior, especially legacy OpenRouter selection when an OpenRouter key exists without an explicit provider selector.
- Add broader observability only when it can be run safely without accidental provider calls or trace ingestion.
- Keep LangSmith optional and controlled.
- Maintain pytest-level LangSmith isolation.

### UI and Deployment

- Defer Streamlit import-time UI refactor until after the current release unless a bug requires it.
- Review public deployment hardening separately: persistent storage, Qdrant/index lifecycle, filesystem behavior, secret management, resource limits, startup time, multi-user isolation, observability, backups, and rate limiting.
- Consider React polish only after the core workflow and product scope stabilize.

### Documentation

- Prepare a public edited Product Constitution only after human review.
- Clean historical documentation names, absolute paths, and stale corpus references in a separate documentation cleanup pass.
- Keep historical Skill Compass / Sprint documents clearly labeled as historical rather than silently rewriting the project history.
