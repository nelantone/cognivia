# Evaluation

Cognivia keeps evaluation methodology separate from observed evidence. The
repository contains deterministic evaluation code and case definitions, but
no evaluation run was performed for this documentation recovery.

## Current implemented methodology

The deterministic evaluator inspects retrieved source names and metadata.
Built-in cases define a question plus expected source references and metadata,
then report whether the retrieved documents meet those checks. It does not
evaluate generated answers, citation presentation, or behavioral outcomes.

A useful evaluation run should record:

- the exact case set;
- provider and model configuration;
- corpus and index identity;
- pass/fail criteria;
- per-case results and failures; and
- the date and execution environment.

Method definitions show what can be measured. They do not establish product
quality by themselves.

The implementation in `rag/evaluation.py` calculates per-case source/metadata
matches and an aggregate pass rate. It can use documents injected by a caller
or call the configured retriever. It does **not** send generated answers to
another LLM, inspect answer text, score citation presentation, or evaluate the
behavioral quality of the complete application response. Cognivia does not
currently implement RAGAS, DeepEval, LangSmith LLM evaluators, or an
LLM-as-a-judge workflow for generated responses.

## Observed repository evidence — 2026-08-30

| Evidence | Status |
| --- | --- |
| Deterministic evaluator implementation exists | Observed by repository inspection on 2026-08-30 |
| Built-in case registry exists | Observed by repository inspection on 2026-08-30 |
| Current case registry matches the present corpus | **PENDING**; some expected filenames and branding appear stale |
| Current evaluation pass rate | **PENDING** |
| Retrieval-quality benchmark | **PENDING** |
| Provider-to-provider comparison | **PENDING** |
| Human assessment of usefulness and judgment support | **PENDING** |

No score, pass rate, or quality threshold is claimed until the registry is
reconciled with the current corpus and the evaluation is run under recorded
conditions.

## Historical qualitative evaluation design

The following author-created design is retained as historical methodology, not
as evidence of a completed evaluation. It was intended to assess whether the
learning workflow turns requests into safe, evidence-grounded decisions across
retrieval, grounding, focus, actionability, and uncertainty handling.

### Historical criteria

- **Retrieval relevance:** whether retrieved material matches the request.
- **Groundedness:** whether direct evidence supports the answer rather than
  merely sharing its topic.
- **Focus:** whether the response stays on the requested learning topic or
  comparison.
- **Actionability:** whether the response offers a clear next step.
- **Uncertainty handling:** whether the workflow clarifies, refuses, or returns
  `insufficient_evidence` when support is missing.

The historical design proposed a 1–5 qualitative scale, from poor to strong.
No score in the table below is an observed result.

### Representative cases and expected but not executed results

| Representative case | Expected outcome | Historical target: relevance | Groundedness | Focus | Actionability | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| What should I learn next? | Clarification or guided intake | N/A | 4 | 5 | 4 | 5 |
| Why is RAG evaluation useful for AI engineers? | Evidence-backed answer only if direct support is retrieved; otherwise `insufficient_evidence` | 2 | 4 | 4 | 2 | 5 |
| Should I learn LangGraph or RAG evaluation? | Compare only with support for both options; otherwise `insufficient_evidence` | 2 | 4 | 4 | 2 | 5 |
| How does LangGraph work? | Answer only from directly supporting evidence; otherwise `insufficient_evidence` | 2 | 4 | 4 | 2 | 5 |
| Explain a completely unknown technology called ZorblaxDB. | `insufficient_evidence` | 1 | 5 | 5 | 2 | 5 |
| Tacos al pastor | Out-of-scope or `insufficient_evidence` | 1 | 5 | 5 | 2 | 5 |

These targets predate the current recovery and were not executed here. The
expected statuses may also depend on the corpus, provider, index, and workflow
version used in a future run.

### Interpretation guidance

If a recorded manual evaluation were to match the historical targets, strong
uncertainty handling would mean the workflow avoids forcing a plan for a vague,
unknown, unsupported, or out-of-scope request. Low retrieval relevance for an
otherwise valid AI-learning question would instead expose corpus coverage or
retrieval limitations. Choosing insufficient evidence over a speculative
answer can be the safer outcome, but it should not be mistaken for strong
retrieval quality.

The five qualitative dimensions should be reported separately. An aggregate
score can hide the important distinction between retrieving a related source,
finding direct support, and producing a useful answer.

## Limitations

- The historical six-case design is a small hand-scored sample, not a
  statistically valid benchmark or an observed result.
- The current built-in deterministic cases contain expected filenames and
  branding that may not match the present corpus.
- The local corpus is limited, so legitimate AI-engineering questions may
  return `insufficient_evidence`.
- Source-name and metadata matches do not measure answer correctness,
  faithfulness, completeness, usefulness, citation quality, latency, cost, or
  retrieval recall across a larger corpus.
- Automated tests can verify evaluator behavior without establishing current
  retrieval or product quality.
- Provider-backed runs require explicit authorization, recorded configuration,
  and cost awareness.

## Proposed improvements

- Reconcile built-in cases with the current source manifest while preserving a
  versioned record of the evaluated corpus and index identity.
- Add a larger labeled set spanning supported topics, clarification cases,
  comparisons, low-evidence requests, and out-of-scope prompts.
- Track retrieval relevance, direct support, and generated-answer quality as
  separate measures.
- Add gold evidence examples and explicit pass/fail definitions for each case.
- Record latency, failures, and provider configuration where provider-backed
  evaluation is explicitly authorized.
- Compare a current baseline with a future candidate before changing graph or
  retrieval behavior.
- Treat any future real LLM-as-a-judge feature as separate implementation work,
  not as part of this recovered historical design.

## Recommended evidence sequence

1. Reconcile case expectations with the current source manifest.
2. Run deterministic retrieval cases with recorded inputs and provider
   configuration, or with documented injected retrieval fixtures.
3. Record retrieval failures separately from any future generation or
   citation-review failures.
4. Run explicitly authorized provider cases, if needed.
5. Add human review focused on whether responses strengthen user judgment,
   communicate uncertainty, and avoid unsupported confidence.

Evaluation execution is outside this documentation-only phase. Testing scope is
documented in [Testing](testing.md), and corpus provenance in
[Sources and provenance](sources.md).
