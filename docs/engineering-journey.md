# Engineering Journey

Skill Compass started as a small interview-prep app and became a bounded
Agentic RAG project. The main lesson was that AI engineering is less about
adding autonomy everywhere and more about controlling where evidence enters the
system.

## Sprint 1: Brief Origin

The first version was an Interview Coach in Streamlit. It used OpenRouter chat
calls and prompt-based interaction to generate practice questions and coaching
style responses. It was useful as a first app, but most of the behavior lived in
prompts.

## Sprint 2: RAG Baseline

Sprint 2 moved the project toward Skill Compass. I added Markdown loading,
chunking, embeddings, semantic retrieval, and evidence-aware study plans. The
app could retrieve local learning material and use it to guide a recommendation.

The limitation was orchestration. Routing, retrieval, fallback, and response
assembly were still too concentrated. The app could retrieve evidence, but it
did not yet have a clear workflow for deciding when evidence was required, when
to retry, or when to refuse.

## Sprint 3: Main Journey

### PDF And Persistent Retrieval

Sprint 3 began by expanding the source set. Markdown was not enough, so I added
PDF loading for public career and skills reports. That introduced page metadata,
larger documents, and more realistic provenance concerns.

The next issue was startup cost and stale indexes. Rebuilding embeddings every
time was slow, but blindly reusing a local index could serve outdated chunks.
The fix was persistent Qdrant plus source fingerprints. When source files
change, the stored manifest no longer matches and the index is rebuilt.

### Moving Orchestration Into LangGraph

The previous flow had too much logic packed into one decision path. LangGraph
made the workflow explicit: typed state, named nodes, and conditional routes.

I split the flow into nodes such as `resolve_clarification_context`,
`determine_request_shape`, `retrieve_evidence`, `assess_evidence`,
`reformulate_retrieval_query`, `classify_deterministic_intent`, and the final
response nodes.

Most clear requests use deterministic classification. The LLM fallback remains
for genuinely ambiguous intent, and even that path is bounded and validated.

### Memory And Clarification

The project then needed short-term clarification memory. A vague request like
"What should I learn next?" should not lose context when the user follows up
with "AI Product Engineer" or "Intermediate".

`MemorySaver` plus a Streamlit `thread_id` gave the graph process-local memory.
The routing bugs came from treating context fragments as full requests or
letting old retrieval state leak forward. The fix was to accumulate
clarification context while resetting retrieval-specific fields each turn.

### Bounded Agentic RAG

The biggest backend change was moving retrieval ownership into the graph. The
graph now decides whether retrieval is required, runs retrieval, assesses
support, reformulates once when evidence is weak, and stops after a second
attempt.

That made the system agentic in a controlled way. It can react to weak evidence,
but it cannot loop indefinitely or keep spending tokens in search of a better
answer.

### Groundedness Problems Found

Several bugs only appeared once real questions were tested:

- A RAG-benefit question routed to clarification even though it was a valid
  informational question.
- A LangGraph mechanism question accepted evidence that merely mentioned
  LangGraph, without explaining how it works.
- Headings and malformed fragments were treated as answer claims.
- Evidence assessment and final answer generation used different claims.
- `full_text` made state too large and risked carrying more document text than
  the UI needed.

The fixes made direct support more specific. Mechanism questions need mechanism
claims. Benefit questions need benefit claims. The final answer now comes from
the same accepted claim set used by the evidence judge.

### Provenance Bugs Found

The provenance work was more subtle than expected:

- Positional zip after filtering could pair an evidence item with the wrong
  document text.
- Real Qdrant documents exposed `_id` differently from the summarized evidence.
- Some metadata lived nested under `metadata`; other fields were top-level.
- `"N/A"` placeholders could look like usable identity values.
- Duplicate or ambiguous identity now fails closed.

This was a useful shift in thinking. Retrieval quality is not only about the
top-k documents. It is also about proving that the displayed evidence and the
claim text came from the same source.

### Testing Strategy

Slow real tests were replaced with mocks where appropriate. That made graph
routing, memory, evidence assessment, and retry behavior fast to test.

Mocks were not enough for everything. Qdrant's real metadata shape exposed
identity asymmetry that pure fake documents did not show. A real smoke path
remained necessary.

The final reconstructed target includes 99 graph tests and 287 total tests after
adding the two Streamlit AppTests.

### Final Audit And Productisation

An independent read-only audit found no P0/P1 backend issues. The largest gap
was UI clarity: the backend returned useful state, but the app did not expose it
well enough.

The product hierarchy became clearer:

- Brand: Skill Compass.
- Positioning: AI Engineer Compass.
- Workflow: Noise-to-Signal.

The UI reconstruction surfaces existing agent state visually: decision status,
evidence quality, retrieval attempts, selected focus, recommendation, next
action, reasoning, evidence, trace, and technical details. Two Streamlit
AppTests cover the clarification and representative informational paths without
calling OpenRouter, embeddings, Qdrant, or remote services.

## Lessons Learned

- Relevance is not grounding.
- Agentic does not mean unbounded autonomy.
- Provenance must survive filtering.
- Mocks need at least one real integration path nearby.
- Safe refusal can be more valuable than a confident answer.
- Product clarity matters as much as backend complexity.

## How I Would Explain The Project In A Review

Skill Compass is an AI Engineer Compass that helps learners decide what to study
next. The main workflow, Noise-to-Signal, uses LangGraph to classify the request,
decide whether retrieval is needed, retrieve from a local Qdrant-backed
knowledge base, assess whether the evidence directly supports the answer, and
retry once with a reformulated query when support is weak. If evidence is still
missing, it returns an insufficient-evidence response instead of guessing. The
point of the project is not just RAG retrieval; it is controlled decision-making
around when evidence is strong enough to guide a learning action.

## Likely Review Questions

**Why LangGraph?**

Because the workflow has real state and branches: clarification, retrieval,
evidence assessment, retry, comparison, study plan, and insufficient evidence.
Named nodes made those paths testable.

**Why graph-owned retrieval?**

Because retrieval is part of the decision process. The graph needs to know when
retrieval was skipped, weak, retried, or sufficient.

**Why two retrieval attempts?**

One normal query plus one evidence-gap reformulation gives the system a recovery
path without becoming open-ended.

**Why deterministic heuristics?**

They are inspectable and easy to regression test. An LLM judge could be useful
later, but deterministic checks made the Sprint 3 behavior easier to defend.

**How are hallucinations reduced?**

The app only answers informational questions from accepted evidence claims,
requires direct support for the question shape, and returns insufficient
evidence when support is weak.

**Why Qdrant?**

It provides a persistent local vector store that fits the demo and avoids
rebuilding embeddings on every run.

**What would change for production?**

I would add durable user memory, authentication, upload hardening, hosted vector
storage, stronger observability, a manual evaluation dataset, and red-team
automation.

## Future Work

- Manual evaluation dataset.
- Hybrid retrieval and reranking.
- LLM evidence judge.
- Persistent memory.
- Optional LangSmith tracing for local smoke testing and debugging.
- Playwright.
- Production upload hardening.
- Red-team automation.
- Recurring technical-debt workflow.
