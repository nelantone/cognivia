# Architecture audit format

## Scope and evidence

- Audit question:
- Included surfaces:
- Exclusions:
- Evidence inspected:
- Runtime checks performed:
- Unverified areas:

## Current architecture

- Entry points:
- Major components:
- Responsibility owners:
- State and persistence:
- External/provider boundaries:
- Test ownership:

## Dependency map

Record important edges as `source -> dependency -> reason`. Include only relevant
surface checks:

- Frontend: UI composition, reruns, callbacks, browser assets, session state.
- Backend: domain services, orchestration, schemas, error boundaries.
- Security: inputs, trust boundaries, credentials, logs, failure behavior.
- RAG: loaders, chunks, embeddings, retrieval, metadata, evaluation.
- Repository: modules, tests, tooling, documentation, generated artifacts.
- Deployment: entrypoints, environment, build/runtime configuration, services.

## Findings

- Ownership gaps:
- Coupling and cycles:
- Hidden or shared state:
- Compatibility constraints:
- Test and observability gaps:
- Risks ordered by impact:

## Phased recommendation

For each phase record:

- Goal and prerequisites:
- Files or components:
- Behavior preserved:
- Validation:
- Risk and rollback:
- Explicit non-goals:
