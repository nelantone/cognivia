# Sprint 3 Project Plan - Historical Note

This file is kept as a lightweight historical planning note for the Sprint 3
phase. Earlier versions of this document described work that was still planned
at the time. The repository has since moved past that planning state.

For the current frozen implementation, treat this file as historical context,
not as the source of truth for shipped behavior.

## Current Freeze State

The current Sprint 3 implementation includes:

- a working Noise-to-Signal LangGraph workflow in
  `tools/noise_to_signal_graph.py`;
- graph-owned retrieval, evidence assessment, and fail-closed routing;
- a bounded retrieval loop with at most two retrieval attempts and one query
  reformulation;
- short-term clarification memory through `MemorySaver` and `thread_id`;
- persistent local Qdrant retrieval with source-manifest invalidation;
- reviewer-facing Streamlit rendering for decision status, evidence, study
  plan, trace, and technical details;
- optional LangSmith tracing for local smoke testing and observability, driven
  entirely by environment variables.

The project is still a local demo and learning artifact. It should not claim
production readiness.

## Source Of Truth

Use these files for the current frozen state:

- `README.md` for setup, validation, and reviewer-safe usage;
- `docs/architecture.md` for the actual Sprint 3 workflow and system design;
- `docs/code-map.md` for file responsibilities and reading order;
- `docs/project-evolution.md` and `docs/engineering-journey.md` for the
  evolution story;
- `docs/future-improvements.md` for post-freeze ideas that are not part of the
  current deliverable.

## Current Limitations

- The corpus is small and conservative fail-closed behavior is intentional.
- Short-term memory is process-local, not durable user memory.
- LangSmith is optional and not required for normal tests or reviewer-safe
  runs.
- Production concerns such as authentication, centralized observability,
  broader red-team coverage, and deployment hardening remain future work.
