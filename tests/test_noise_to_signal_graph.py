"""Tests for the LangGraph Noise-to-Signal workflow."""

import ast
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.documents import Document

from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from tools.noise_to_signal_graph import (
    _reasoning_items_with_full_text,
    route_by_decision_status,
    run_noise_to_signal,
)
from tools.study_plan import PROJECT_DOCUMENTATION_ROLE, build_noise_to_signal_decision

PUBLIC_PARITY_FIELDS = (
    "decision_status",
    "selected_focus",
    "recommendation",
    "next_action",
    "decision_trace",
    "evidence",
)

APP_RENDERER_FIELDS = (
    "decision_status",
    "recommendation",
    "study_plan",
    "decision_trace",
    "evidence",
    "next_action",
)

AMBIGUOUS_GOAL = (
    "I am moving from backend development into AI, and I am unsure whether "
    "LangGraph is the right next step for me."
)
INTERNAL_ORCHESTRATION_TEXT = (
    "Original request:",
    "User-provided context:",
    "Use the provided context",
    "Do not treat the context",
)


def _assert_public_parity(goal, docs):
    graph_result = run_noise_to_signal(goal, docs)
    direct_result = build_noise_to_signal_decision(goal, docs)

    for field in PUBLIC_PARITY_FIELDS:
        assert graph_result[field] == direct_result[field]


def _wef_pdf_doc(content, page=39):
    return Document(
        page_content=content,
        metadata={
            "source": "data/sources/pdfs/wef_future_of_jobs_report_2025.pdf",
            "filename": "wef_future_of_jobs_report_2025.pdf",
            "source_type": "pdf",
            "document_role": "primary_source",
            "source_authority": "official",
            "page": page,
            "title": "Future of Jobs Report 2025",
        },
    )


def _langgraph_basic_rag_docs():
    return [
        Document(
            page_content="LangGraph is useful when workflows need durable state.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        ),
        Document(
            page_content="LangGraph supports stateful multi-step AI workflows.",
            metadata={"source": "agents_more.md", "filename": "agents_more.md"},
        ),
        Document(
            page_content="Basic RAG is useful for retrieval-grounded answers.",
            metadata={"source": "rag.md", "filename": "rag.md"},
        ),
    ]


def _assert_no_internal_orchestration_text(result):
    user_facing_values = [
        result.get("goal"),
        result.get("selected_focus"),
        result.get("recommendation"),
        result.get("next_action"),
        "\n".join(result.get("decision_trace") or []),
    ]
    study_plan = result.get("study_plan")
    if study_plan:
        user_facing_values.append(study_plan.get("plan"))

    rendered_text = "\n".join(str(value or "") for value in user_facing_values)
    for internal_text in INTERNAL_ORCHESTRATION_TEXT:
        assert internal_text not in rendered_text


class RecordingIntentClassifier:
    def __init__(self, result=None, error=None, results=None, errors=None):
        self.result = result
        self.error = error
        self.results = list(results) if results is not None else None
        self.errors = list(errors) if errors is not None else None
        self.calls = []

    def __call__(self, goal, evidence):
        call_index = len(self.calls)
        self.calls.append({"goal": goal, "evidence": evidence})

        if self.errors is not None:
            if call_index < len(self.errors) and self.errors[call_index]:
                raise self.errors[call_index]
        elif self.error:
            raise self.error

        if self.results is not None:
            if call_index < len(self.results):
                return self.results[call_index]
            return self.results[-1]

        return self.result


class RecordingRetriever:
    def __init__(self, results=None, error=None):
        self.results = list(results or [])
        self.error = error
        self.calls = []

    def __call__(self, query, k=20, min_relevance_score=None):
        self.calls.append(
            {
                "query": query,
                "k": k,
                "min_relevance_score": min_relevance_score,
            }
        )

        if self.error:
            raise self.error

        if self.results:
            call_index = len(self.calls) - 1
            if call_index < len(self.results):
                return self.results[call_index]
            return self.results[-1]

        return []


def test_graph_matches_direct_decision_for_vague_goal():
    _assert_public_parity("What should I learn next?", [])


def test_graph_matches_direct_decision_for_informational_question_with_evidence():
    docs = [
        _wef_pdf_doc(
            "The report identifies analytical thinking, AI and big data, "
            "technological literacy, resilience, flexibility, and lifelong "
            "learning as important skills for future work.",
        )
    ]

    _assert_public_parity(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )


def test_graph_matches_direct_decision_for_informational_question_without_evidence():
    goal = "What does WEF identify as important for developers?"

    graph_result = run_noise_to_signal(goal, [])
    direct_result = build_noise_to_signal_decision(goal, [])

    for field in PUBLIC_PARITY_FIELDS:
        if field != "recommendation":
            assert graph_result[field] == direct_result[field]

    assert graph_result["recommendation"] == (
        "The retrieved evidence is insufficient to answer this question reliably. "
        "Refine the question or add evidence that directly addresses the topic."
    )


def test_graph_matches_direct_decision_for_single_focus_goal():
    _assert_public_parity("I want to learn RAG evaluation", [])


def test_graph_single_focus_includes_study_plan():
    result = run_noise_to_signal("I want to learn RAG evaluation", [])

    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "RAG evaluation"
    assert result["study_plan"] is not None
    assert result["study_plan"]["plan"]


def test_graph_matches_direct_decision_for_selected_comparison():
    docs = [
        Document(
            page_content=(
                "RAG evaluation should check answer quality, retrieval relevance, "
                "and source grounding before adding more advanced agent behavior."
            ),
            metadata={"source": "rag.md", "filename": "rag.md"},
        ),
        Document(
            page_content="RAG evaluation helps measure grounded answer quality.",
            metadata={"source": "rag_eval.md", "filename": "rag_eval.md"},
        ),
        Document(
            page_content="LangGraph is useful when workflows need durable state.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        ),
        Document(
            page_content="Docker is useful for deployment but is not the main learning gap.",
            metadata={"source": "deployment.md", "filename": "deployment.md"},
        ),
        Document(
            page_content="AI agents can automate multi-step tasks with tool use.",
            metadata={"source": "agents_general.md", "filename": "agents_general.md"},
        ),
    ]

    _assert_public_parity(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        docs,
    )


def test_graph_selected_comparison_keeps_recommendation_and_includes_study_plan():
    docs = _langgraph_basic_rag_docs()

    result = run_noise_to_signal("Should I learn LangGraph or basic RAG?", docs)

    assert result["decision_status"] == "selected"
    assert result["selected_focus"] == "LangGraph"
    assert result["recommendation"] == (
        "Focus on LangGraph. Prioritize one practical skill path that is "
        "supported by the retrieved evidence and can produce a portfolio-ready "
        "result this week."
    )
    assert result["study_plan"] is not None
    assert result["study_plan"]["plan"]


def test_graph_matches_direct_decision_for_comparison_without_evidence():
    _assert_public_parity(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        [],
    )


def test_graph_classify_cleans_goal_before_decision_logic():
    _assert_public_parity("  I   want   to   learn   RAG   evaluation  ", [])


def test_run_noise_to_signal_rejects_non_string_goal():
    with pytest.raises(TypeError, match="goal must be a string"):
        run_noise_to_signal(123, [])


def test_run_noise_to_signal_rejects_whitespace_only_goal():
    with pytest.raises(ValueError, match="goal must not be empty"):
        run_noise_to_signal("   \n\t   ", [])


def test_run_noise_to_signal_omitted_retrieved_docs_uses_internal_retrieval():
    retriever = RecordingRetriever(results=[[]])

    result = run_noise_to_signal("What should I learn next?", retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "needs_clarification"


def test_run_noise_to_signal_rejects_invalid_document_collection():
    with pytest.raises(TypeError, match="retrieved_docs must be a list or tuple"):
        run_noise_to_signal("What should I learn next?", "not a document collection")


def test_run_noise_to_signal_accepts_empty_document_list():
    result = run_noise_to_signal("What should I learn next?", [])

    assert result["retrieved_docs"] == []
    assert result["decision_status"] == "needs_clarification"


@pytest.mark.parametrize(
    "goal",
    ["Intermediate", "AI Product Engineer", "What should I learn next?"],
)
def test_agentic_rag_clarification_skips_retrieval(goal):
    retriever = RecordingRetriever()

    result = run_noise_to_signal(goal, retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "needs_clarification"
    assert "Retrieval skipped: more context required." in result["decision_trace"]


def test_agentic_rag_lost_learning_path_routes_to_guided_intake_without_retrieval():
    retriever = RecordingRetriever()

    result = run_noise_to_signal(
        "I feel lost and want a practical AI learning path",
        retriever=retriever,
    )

    assert retriever.calls == []
    assert result["decision_status"] == "needs_clarification"
    assert result["interaction_mode"] == "guided_intake"
    assert result["guided_intake_entry_point"] == "I feel lost and need direction"
    assert result["selected_focus"] is None
    assert result["retrieval_attempts"] == 0
    assert result["study_plan"] is None
    assert "learner profile context" in result["recommendation"]


def test_agentic_rag_study_next_routes_to_guided_intake_without_retrieval():
    retriever = RecordingRetriever()

    result = run_noise_to_signal("What should I study next?", retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "needs_clarification"
    assert result["interaction_mode"] == "guided_intake"
    assert result["guided_intake_entry_point"] == "I want to choose what to learn next"
    assert result["selected_focus"] is None
    assert result["retrieval_attempts"] == 0
    assert result["study_plan"] is None


def test_agentic_rag_first_retrieval_can_be_sufficient():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "LangGraph is a framework for building stateful multi-step "
                        "agent workflows with durable execution."
                    ),
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal("Explain LangGraph", retriever=retriever)

    assert len(retriever.calls) == 1
    assert retriever.calls[0]["query"] == "Explain LangGraph"
    assert result["decision_status"] == "informational"
    assert "Retrieval attempt 1: sufficient." in result["decision_trace"]


def test_agentic_rag_passes_default_relevance_threshold_to_retriever():
    retriever = RecordingRetriever(results=[[]])

    run_noise_to_signal("Explain LangGraph", retriever=retriever)

    assert retriever.calls[0]["k"] == 20
    assert retriever.calls[0]["min_relevance_score"] == DEFAULT_MIN_RELEVANCE_SCORE


@pytest.mark.parametrize(
    "goal",
    [
        "Why is RAG evaluation useful for AI engineers?",
        "How does LangGraph work?",
        "What are the benefits of RAG evaluation?",
    ],
)
def test_agentic_rag_self_contained_informational_questions_retrieve(goal):
    retriever = RecordingRetriever(results=[[], []])

    result = run_noise_to_signal(goal, retriever=retriever)

    assert 1 <= len(retriever.calls) <= 2
    assert result["decision_status"] in {"informational", "insufficient_evidence"}
    assert result["decision_status"] != "needs_clarification"
    assert result["needs_clarification"] is False
    assert result["retrieval_attempts"] == len(retriever.calls)
    assert "Retrieval skipped: more context required." not in result["decision_trace"]


def test_agentic_rag_why_question_with_sufficient_evidence_is_informational():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "RAG evaluation is useful for AI engineers because it checks "
                        "retrieval relevance, answer quality, and source grounding."
                    ),
                    metadata={"source": "rag.md", "filename": "rag.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        retriever=retriever,
    )

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "informational"
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert "retrieval relevance" in result["recommendation"]
    assert "source grounding" in result["recommendation"]


def test_agentic_rag_why_question_excludes_heading_fragments():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "Implications for AI Learners. RAG evaluation is useful "
                        "for AI engineers because it combines retrieval quality, "
                        "answer quality, source traceability, failure analysis, "
                        "quality control, and source grounding."
                    ),
                    metadata={"source": "rag_eval.md", "filename": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        retriever=retriever,
    )

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "retrieval quality" in result["recommendation"]
    assert "answer quality" in result["recommendation"]
    assert "source traceability" in result["recommendation"]
    assert "failure analysis" in result["recommendation"]
    assert "Implications for AI Learners" not in result["recommendation"]


def test_agentic_rag_how_question_rejects_topic_mentions_without_mechanism():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "LangGraph is useful when workflows need durable state. "
                        "AI engineers may prioritize LangGraph after learning RAG."
                    ),
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
            [
                Document(
                    page_content="LangGraph is an important learning priority.",
                    metadata={"source": "agents_more.md", "filename": "agents_more.md"},
                )
            ],
        ]
    )

    result = run_noise_to_signal("How does LangGraph work?", retriever=retriever)

    assert 1 <= len(retriever.calls) <= 2
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"


def test_agentic_rag_how_question_rejects_real_generic_use_false_positive():
    false_positive = (
        "Learning and Career Decision Guidance When comparing RAG evaluation, "
        "LangGraph, Docker, and AI agents, OECD-style skills evidence supports "
        "prioritizing skills that improve reliable AI use and training transfer."
    )
    retriever = RecordingRetriever(
        results=[
            [Document(page_content=false_positive, metadata={"source": "notes.md"})],
            [Document(page_content=false_positive, metadata={"source": "notes.md"})],
        ]
    )

    result = run_noise_to_signal("How does LangGraph work?", retriever=retriever)

    assert 1 <= len(retriever.calls) <= 2
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert not result["recommendation"].startswith("Based on the retrieved evidence:")
    assert false_positive not in result["recommendation"]


def test_agentic_rag_how_question_accepts_mechanistic_evidence():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "LangGraph works by representing an AI workflow as nodes "
                        "and edges that route state between steps."
                    ),
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal("How does LangGraph work?", retriever=retriever)

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "nodes and edges" in result["recommendation"]


def test_agentic_rag_benefit_answer_excludes_realistic_malformed_fragments():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "Learning and Career Decision Guidance. "
                        "RAG evaluation is a good bridge skill because it combines "
                        "retrieval quality, answer quality, source traceability,. "
                        "RAG evaluation is often a strong first choice because it "
                        "supports quality control, source grounding, and. "
                        "RAG evaluation is useful because it combines retrieval "
                        "quality, answer quality, source traceability, and failure "
                        "analysis."
                    ),
                    metadata={"source": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        retriever=retriever,
    )

    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "RAG evaluation is useful because it combines retrieval quality" in result[
        "recommendation"
    ]
    assert "Learning and Career Decision Guidance" not in result["recommendation"]
    assert "source traceability,." not in result["recommendation"]
    assert "source grounding, and" not in result["recommendation"]
    assert ",." not in result["recommendation"]
    assert not result["recommendation"].endswith(("and.", "or."))


def test_agentic_rag_markdown_heading_is_removed_before_sentence_extraction():
    doc_text = (
        "## Learning and Career Decision Guidance\n\n"
        "When choosing among RAG evaluation, LangGraph, Docker, and AI agents, "
        "start with the option that best improves reliable AI use.\n\n"
        "RAG evaluation is a good bridge skill because it combines retrieval "
        "quality, answer quality, source traceability, and failure analysis."
    )
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=doc_text,
                    metadata={"source": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        retriever=retriever,
    )

    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "RAG evaluation is a good bridge skill because it combines" in result[
        "recommendation"
    ]
    assert "Learning and Career Decision Guidance" not in result["recommendation"]
    assert "When choosing among" not in result["recommendation"]
    assert all(
        "full_text" not in item
        for item in result["reasoning_evidence"].get("items", [])
    )


def test_agentic_rag_full_text_is_not_persisted_in_reasoning_state():
    long_prefix = (
        "Background context. " * 20
        + "RAG evaluation is a good bridge skill because it combines "
        "retrieval quality,. "
        + "Additional context. " * 10
    )
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        f"{long_prefix}RAG evaluation is useful because it combines "
                        "retrieval quality, answer quality, source traceability, and "
                        "failure analysis."
                    ),
                    metadata={"source": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        retriever=retriever,
    )

    assert result["decision_status"] == "informational"
    assert "source traceability" in result["recommendation"]
    assert "retrieval quality,." not in result["recommendation"]
    assert all(
        "full_text" not in item
        for item in result["reasoning_evidence"].get("items", [])
    )


def test_agentic_rag_filtered_doc_cannot_supply_transient_full_text():
    filtered_doc = Document(
        page_content=(
            "RAG evaluation is useful because it combines retrieval quality, "
            "answer quality, source traceability, and failure analysis."
        ),
        metadata={
            "source": "project_notes.md",
            "document_role": PROJECT_DOCUMENTATION_ROLE,
            "chunk_index": 0,
        },
    )
    allowed_weak_doc = Document(
        page_content="RAG evaluation is mentioned in learning plans.",
        metadata={"source": "allowed_notes.md", "chunk_index": 0},
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        [filtered_doc, allowed_weak_doc],
    )

    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert "source traceability" not in result["recommendation"]
    assert [item["source"] for item in result["reasoning_evidence"]["items"]] == [
        "allowed_notes.md"
    ]
    assert all(
        "full_text" not in item
        for item in result["reasoning_evidence"].get("items", [])
    )


def test_agentic_rag_allowed_doc_keeps_own_full_text_after_filtered_doc():
    filtered_doc = Document(
        page_content=(
            "RAG evaluation is useful because it combines filtered-only retrieval "
            "signals."
        ),
        metadata={
            "source": "project_notes.md",
            "document_role": PROJECT_DOCUMENTATION_ROLE,
            "chunk_index": 0,
        },
    )
    allowed_doc = Document(
        page_content=(
            "Background context. " * 25
            + "RAG evaluation is useful because it combines retrieval quality, "
            "answer quality, source traceability, and failure analysis."
        ),
        metadata={"source": "allowed_notes.md", "chunk_index": 4},
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        [filtered_doc, allowed_doc],
    )

    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "source traceability" in result["recommendation"]
    assert "filtered-only" not in result["recommendation"]
    assert all(
        "full_text" not in item
        for item in result["reasoning_evidence"].get("items", [])
    )


def test_agentic_rag_duplicate_source_chunks_require_chunk_identity_for_full_text():
    first_chunk = Document(
        page_content=(
            "RAG evaluation is useful because it combines retrieval quality, "
            "answer quality, source traceability, and failure analysis."
        ),
        metadata={"source": "same_source.md", "chunk_index": 1},
    )
    second_chunk = Document(
        page_content="RAG evaluation is only named here.",
        metadata={"source": "same_source.md", "chunk_index": 2},
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        [second_chunk, first_chunk],
    )

    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "source traceability" in result["recommendation"]


def test_agentic_rag_matches_real_qdrant_id_asymmetry_by_structural_key():
    doc = Document(
        page_content="RAG evaluation is useful because it combines retrieval quality.",
        metadata={
            "_id": "qdrant-point-1",
            "source": "rag_eval.md",
            "filename": "rag_eval.md",
            "chunk_index": 8,
            "page": None,
        },
    )
    state = {
        "retrieved_docs": [doc],
        "reasoning_evidence": {
            "items": [
                {
                    "source": "rag_eval.md",
                    "filename": "rag_eval.md",
                    "chunk_index": 8,
                    "page": None,
                    "metadata": {
                        "source": "rag_eval.md",
                        "filename": "rag_eval.md",
                        "chunk_index": 8,
                        "page": None,
                    },
                }
            ]
        },
    }

    enriched = _reasoning_items_with_full_text(state)

    assert enriched[0]["full_text"] == doc.page_content


def test_agentic_rag_matches_split_nested_and_top_level_identity_metadata():
    doc = Document(
        page_content="RAG evaluation is useful because it combines answer quality.",
        metadata={
            "source": "rag_eval.md",
            "filename": "rag_eval.md",
            "chunk_index": 4,
            "page": 2,
        },
    )
    state = {
        "retrieved_docs": [doc],
        "reasoning_evidence": {
            "items": [
                {
                    "source": "rag_eval.md",
                    "filename": "rag_eval.md",
                    "chunk_index": 4,
                    "page": 2,
                    "metadata": {"source": "rag_eval.md"},
                }
            ]
        },
    }

    enriched = _reasoning_items_with_full_text(state)

    assert enriched[0]["full_text"] == doc.page_content


def test_agentic_rag_ambiguous_duplicate_identity_skips_full_text_safely():
    long_prefix = "Background context. " * 25
    direct_doc = Document(
        page_content=(
            f"{long_prefix}RAG evaluation is useful because it combines retrieval "
            "quality, answer quality, source traceability, and failure analysis."
        ),
        metadata={"source": "same_source.md"},
    )
    weak_doc = Document(
        page_content="RAG evaluation is mentioned in AI engineering notes.",
        metadata={"source": "same_source.md"},
    )

    result = run_noise_to_signal(
        "Why is RAG evaluation useful for AI engineers?",
        [weak_doc, direct_doc],
    )

    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert "source traceability" not in result["recommendation"]
    assert all(
        "full_text" not in item
        for item in result["reasoning_evidence"].get("items", [])
    )


def test_agentic_rag_benefits_question_accepts_direct_benefit_evidence():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "RAG evaluation helps AI engineers measure retrieval "
                        "quality, answer quality, and source grounding."
                    ),
                    metadata={"source": "rag_eval.md", "filename": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal(
        "What are the benefits of RAG evaluation?",
        retriever=retriever,
    )

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert "retrieval quality" in result["recommendation"]


def test_agentic_rag_weak_first_retrieval_reformulates_once_and_succeeds():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                ),
                Document(
                    page_content=(
                        "RAG evaluation checks retrieval relevance, answer quality, "
                        "and source grounding."
                    ),
                    metadata={"source": "rag.md", "filename": "rag.md"},
                ),
            ],
        ]
    )

    result = run_noise_to_signal(
        "Should I learn LangGraph or RAG evaluation?",
        retriever=retriever,
    )

    assert 1 <= len(retriever.calls) <= 2
    assert retriever.calls[1]["query"] != retriever.calls[0]["query"]
    assert "RAG evaluation" in retriever.calls[1]["query"]
    assert "LangGraph" not in retriever.calls[1]["query"]
    assert result["decision_status"] in {"selected", "tie"}
    assert result["evidence_quality"] == "sufficient"
    assert any("Query reformulated:" in item for item in result["decision_trace"])


def test_agentic_rag_second_weak_retrieval_stops_without_selection():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
        ]
    )

    result = run_noise_to_signal(
        "Should I learn LangGraph or RAG evaluation?",
        retriever=retriever,
    )

    assert 1 <= len(retriever.calls) <= 2
    assert result["decision_status"] == "insufficient_evidence"
    assert result["selected_focus"] is None
    assert "Stopped after maximum retrieval attempts." in result["decision_trace"]


def test_agentic_rag_informational_weak_evidence_returns_insufficient_evidence():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content="LangGraph and RAG evaluation are often compared.",
                    metadata={"source": "notes.md", "filename": "notes.md"},
                )
            ],
            [],
        ]
    )

    result = run_noise_to_signal("Explain LangGraph", retriever=retriever)

    assert 1 <= len(retriever.calls) <= 2
    assert result["decision_status"] == "insufficient_evidence"
    assert not result["recommendation"].startswith("Based on the retrieved evidence:")


def test_agentic_rag_comparison_requires_support_for_every_option():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
            [
                Document(
                    page_content="LangGraph helps coordinate stateful workflows.",
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
        ]
    )

    result = run_noise_to_signal(
        "Should I learn LangGraph or RAG evaluation?",
        retriever=retriever,
    )

    assert len(retriever.calls) == 2
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_reason"] == "Missing support for RAG evaluation."


def test_agentic_rag_single_focus_can_generate_weak_evidence_plan():
    retriever = RecordingRetriever(results=[[], []])

    result = run_noise_to_signal("I want to learn LangGraph", retriever=retriever)

    assert len(retriever.calls) == 2
    assert result["decision_status"] == "single_focus"
    assert result["study_plan"] is not None
    assert result["evidence_quality"] == "weak"
    assert "not strongly evidence-grounded" in result["recommendation"]


def test_agentic_rag_out_of_domain_single_focus_rejects_unrelated_evidence():
    unrelated_docs = [
        Document(
            page_content=(
                "The Future of Jobs Report identifies AI and big data, "
                "technological literacy, and lifelong learning as important "
                "career skills."
            ),
            metadata={
                "source": "wef_future_of_jobs_report_2025.pdf",
                "filename": "wef_future_of_jobs_report_2025.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 39,
                "title": "Future of Jobs Report 2025",
            },
        ),
        Document(
            page_content=(
                "AI job market evidence highlights machine learning, LLMs, "
                "retrieval-augmented generation, and deployment skills."
            ),
            metadata={"source": "ai_job_market_skills.md"},
        ),
    ]
    retriever = RecordingRetriever(results=[unrelated_docs])

    result = run_noise_to_signal("Tacos al pastor", retriever=retriever)

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert result["study_plan"] is None
    assert result["selected_focus"] != "Tacos al pastor"
    assert not result["recommendation"].startswith("Build a study plan")
    assert "supported learning plan" not in result["recommendation"]
    assert (
        "outside the AI Engineering learning scope" in result["evidence_reason"]
        or "does not directly support the topic" in result["evidence_reason"]
    )


def test_agentic_rag_ai_domain_single_focus_still_accepts_supporting_evidence():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "RAG evaluation checks retrieval relevance, answer "
                        "quality, and source grounding for AI systems."
                    ),
                    metadata={"source": "rag_eval.md", "filename": "rag_eval.md"},
                )
            ]
        ]
    )

    result = run_noise_to_signal("I want to learn RAG evaluation", retriever=retriever)

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "RAG evaluation"
    assert result["study_plan"] is not None
    assert result["evidence_quality"] == "contextual"
    assert result["evidence_reason"] == "Retrieved evidence can support the study-plan context."


def test_agentic_rag_empty_reformulation_does_not_retry():
    retriever = RecordingRetriever(results=[[]])

    result = run_noise_to_signal("What is ?", retriever=retriever)

    assert len(retriever.calls) == 1
    assert result["decision_status"] == "insufficient_evidence"
    assert "Retrieval retry skipped" in "\n".join(result["decision_trace"])


def test_agentic_rag_retriever_failure_is_safe():
    retriever = RecordingRetriever(error=ValueError("OPENROUTER_API_KEY is missing"))

    result = run_noise_to_signal("Explain LangGraph", retriever=retriever)

    rendered_text = "\n".join(
        [
            result.get("recommendation", ""),
            result.get("next_action", ""),
            "\n".join(result.get("decision_trace") or []),
        ]
    )
    assert len(retriever.calls) == 1
    assert result["decision_status"] == "insufficient_evidence"
    assert "OPENROUTER_API_KEY" not in rendered_text
    assert "Retrieval attempt 1: failed." in result["decision_trace"]


def test_agentic_rag_qdrant_lock_failure_uses_deterministic_single_focus_fallback():
    retriever = RecordingRetriever(
        error=RuntimeError(
            "Storage folder data/vector_store/qdrant is already accessed by "
            "another instance of Qdrant client."
        )
    )

    result = run_noise_to_signal("I want to learn RAG evaluation", retriever=retriever)

    rendered_text = "\n".join(
        [
            result.get("recommendation", ""),
            result.get("next_action", ""),
            result.get("evidence_reason", ""),
            "\n".join(result.get("decision_trace") or []),
        ]
    )
    assert len(retriever.calls) == 1
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "RAG evaluation"
    assert result["study_plan"] is not None
    assert result["retrieval_error"] == "local_evidence_store_locked"
    assert result["evidence_quality"] == "failed"
    assert "local evidence store is busy" in result["evidence_reason"]
    assert "another instance of Qdrant client" not in rendered_text


def test_agentic_rag_retrieval_state_resets_between_memory_turns():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "LangGraph is a framework for stateful multi-step workflows."
                    ),
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ],
            [
                Document(
                    page_content=(
                        "RAG evaluation checks retrieval relevance and answer quality."
                    ),
                    metadata={"source": "rag.md", "filename": "rag.md"},
                )
            ],
        ]
    )
    checkpointer = MemorySaver()
    thread_id = "agentic-rag-reset-test"

    first_result = run_noise_to_signal(
        "Explain LangGraph",
        retriever=retriever,
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    second_result = run_noise_to_signal(
        "Explain RAG evaluation",
        retriever=retriever,
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert len(retriever.calls) >= 2
    assert first_result["retrieval_attempts"] == 1
    assert second_result["retrieval_attempts"] in {1, 2}
    assert second_result["retrieval_query"] == "Explain RAG evaluation"
    assert "LangGraph" not in second_result["recommendation"]


def test_agentic_rag_self_contained_followup_uses_new_request_evidence():
    retriever = RecordingRetriever(
        results=[
            [
                Document(
                    page_content=(
                        "LangGraph is a framework for stateful multi-step workflows."
                    ),
                    metadata={"source": "agents.md", "filename": "agents.md"},
                )
            ]
        ]
    )
    checkpointer = MemorySaver()
    thread_id = "agentic-rag-self-contained-followup-test"

    first_result = run_noise_to_signal(
        "What should I learn next?",
        retriever=retriever,
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    second_result = run_noise_to_signal(
        "Explain LangGraph",
        retriever=retriever,
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert first_result["decision_status"] == "needs_clarification"
    assert len(retriever.calls) == 1
    assert retriever.calls[0]["query"] == "Explain LangGraph"
    assert second_result["decision_status"] == "informational"


def test_explicit_empty_evidence_is_assessed_without_internal_retrieval():
    retriever = RecordingRetriever(error=AssertionError("should not retrieve"))

    result = run_noise_to_signal("Explain LangGraph", [], retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert result["retrieval_attempts"] == 0
    assert "Query reformulated:" not in "\n".join(result["decision_trace"])


def test_explicit_irrelevant_informational_evidence_is_not_sufficient():
    docs = [
        Document(
            page_content="Docker is useful for packaging applications for deployment.",
            metadata={"source": "deployment.md", "filename": "deployment.md"},
        )
    ]
    retriever = RecordingRetriever(error=AssertionError("should not retrieve"))

    result = run_noise_to_signal("Explain LangGraph", docs, retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert result["evidence_reason"] == "No direct answer claim was found."


def test_explicit_incomplete_comparison_evidence_is_not_sufficient():
    docs = [
        Document(
            page_content="LangGraph helps coordinate stateful workflows.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]
    retriever = RecordingRetriever(error=AssertionError("should not retrieve"))

    result = run_noise_to_signal(
        "Should I learn LangGraph or RAG evaluation?",
        docs,
        retriever=retriever,
    )

    assert retriever.calls == []
    assert result["decision_status"] == "insufficient_evidence"
    assert result["selected_focus"] is None
    assert result["evidence_reason"] == "Missing support for RAG evaluation."
    assert "Query reformulated:" not in "\n".join(result["decision_trace"])


def test_explicit_sufficient_evidence_can_support_informational_answer():
    docs = [
        Document(
            page_content=(
                "LangGraph is a framework for building stateful multi-step "
                "workflows with durable execution."
            ),
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]
    retriever = RecordingRetriever(error=AssertionError("should not retrieve"))

    result = run_noise_to_signal("Explain LangGraph", docs, retriever=retriever)

    assert retriever.calls == []
    assert result["decision_status"] == "informational"
    assert result["evidence_quality"] == "sufficient"
    assert result["recommendation"].startswith("Based on the retrieved evidence:")


def test_informational_answer_is_built_once_when_assessment_succeeds(monkeypatch):
    calls = []

    def fake_build_informational_answer(goal, reasoning_items, max_claims=3):
        calls.append(
            {
                "goal": goal,
                "reasoning_items": reasoning_items,
                "max_claims": max_claims,
            }
        )
        return "LangGraph is a stateful workflow framework."

    monkeypatch.setattr(
        "tools.noise_to_signal_graph.build_informational_answer",
        fake_build_informational_answer,
    )
    docs = [
        Document(
            page_content="LangGraph is a framework for stateful workflows.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal("Explain LangGraph", docs)

    assert len(calls) == 1
    assert result["decision_status"] == "informational"
    assert "LangGraph is a stateful workflow framework." in result["recommendation"]


def test_noise_to_signal_app_branch_does_not_pre_retrieve():
    app_tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in app_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    submission_helper = functions["_submit_noise_to_signal_goal"]
    submission_calls = [
        node.func.id
        for node in ast.walk(submission_helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    normal_submission = functions["_render_noise_to_signal_home"]
    normal_submission_calls = [
        node.func.id
        for node in ast.walk(normal_submission)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]

    assert submission_calls.count("run_noise_to_signal") == 1
    assert "retrieve_relevant_chunks" not in submission_calls
    assert normal_submission_calls.count("_submit_noise_to_signal_goal") == 1
    assert "run_noise_to_signal" not in normal_submission_calls
    assert "retrieve_relevant_chunks" not in normal_submission_calls


@pytest.mark.parametrize(
    ("decision_status", "expected_node"),
    [
        ("informational", "answer_informational"),
        ("needs_clarification", "request_clarification"),
        ("single_focus", "plan_for_focus"),
        ("selected", "respond_comparison"),
        ("tie", "respond_comparison"),
        ("insufficient_evidence", "respond_insufficient"),
    ],
)
def test_router_handles_every_supported_status(decision_status, expected_node):
    assert route_by_decision_status({"decision_status": decision_status}) == expected_node


def test_router_raises_for_unknown_status():
    with pytest.raises(ValueError, match="Unknown decision status"):
        route_by_decision_status({"decision_status": "unexpected"})


def test_graph_result_contains_required_state_fields():
    result = run_noise_to_signal("What should I learn next?", [])

    assert {
        "goal",
        "retrieved_docs",
        "evidence",
        "reasoning_evidence",
        "decision_status",
        "needs_clarification",
        "options",
        "ranked_options",
        "selected_focus",
        "tied_options",
        "recommendation",
        "next_action",
        "decision_trace",
        "study_plan",
        "interaction_mode",
        "guided_intake_entry_point",
        "routing_attempts",
        "original_goal",
        "pending_clarification",
        "clarification_context",
        "context_only_followup",
    }.issubset(result)


def test_graph_remembers_pending_clarification_with_same_thread_id():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-memory-test"

    first_result = run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert first_result["decision_status"] == "needs_clarification"
    assert first_result["original_goal"] == "What should I learn next?"
    assert first_result["pending_clarification"] is True
    assert first_result["clarification_context"] is None

    second_result = run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert second_result["original_goal"] == "What should I learn next?"
    assert second_result["clarification_context"] == "AI Product Engineer"
    assert second_result["goal"] == "AI Product Engineer"
    assert "I want to learn AI Product Engineer" not in second_result["goal"]
    assert "repeat the original request" not in second_result["recommendation"].lower()
    _assert_no_internal_orchestration_text(second_result)
    if second_result["decision_status"] == "needs_clarification":
        assert second_result["pending_clarification"] is True
        assert "AI Product Engineer" in second_result["recommendation"]
        assert (
            "Please provide a target role, project, or skill area before choosing a "
            "study plan."
        ) not in second_result["recommendation"]
        assert any(
            missing_detail in second_result["recommendation"].lower()
            for missing_detail in ("current level", "project", "concrete")
        )
    else:
        assert second_result["pending_clarification"] is False


def test_graph_accumulates_clarification_context_across_follow_up_turns():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-three-turn-memory-test"

    first_result = run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    second_result = run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    third_result = run_noise_to_signal(
        "Intermediate",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert first_result["pending_clarification"] is True
    assert "AI Product Engineer" in second_result["clarification_context"]
    assert third_result["original_goal"] == "What should I learn next?"
    assert "AI Product Engineer" in third_result["clarification_context"]
    assert "Intermediate" in third_result["clarification_context"]
    assert "AI Product Engineer" in third_result["goal"]
    assert "Intermediate" in third_result["goal"]
    assert third_result["clarification_context"] != "Intermediate"
    assert "repeat the original request" not in third_result["recommendation"].lower()
    _assert_no_internal_orchestration_text(third_result)
    if third_result["decision_status"] == "needs_clarification":
        assert (
            "AI Product Engineer; Intermediate" in third_result["recommendation"]
        )


def test_context_only_level_then_role_stays_clarification_without_internal_text():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-context-only-level-role-test"

    first_result = run_noise_to_signal(
        "Intermediate",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    second_result = run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert first_result["decision_status"] == "needs_clarification"
    assert second_result["decision_status"] == "needs_clarification"
    assert second_result["selected_focus"] is None
    assert second_result["study_plan"] is None
    assert second_result["clarification_context"] == (
        "Intermediate\nAI Product Engineer"
    )
    assert second_result["goal"] == "Intermediate; AI Product Engineer"
    assert "skill" in second_result["recommendation"]
    assert "domain" in second_result["recommendation"]
    assert "project" in second_result["recommendation"]
    assert "learning decision" in second_result["recommendation"]
    _assert_no_internal_orchestration_text(second_result)


def test_self_contained_comparison_replaces_previous_vague_request():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-self-contained-comparison-test"

    run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    result = run_noise_to_signal(
        "Should I learn LangGraph or RAG evaluation?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert result["decision_status"] in {
        "selected",
        "tie",
        "insufficient_evidence",
    }
    assert result["decision_status"] != "needs_clarification"
    assert result["goal"] == "Should I learn LangGraph or RAG evaluation?"
    assert result["original_goal"] is None
    assert result["clarification_context"] is None
    assert result["pending_clarification"] is False
    _assert_no_internal_orchestration_text(result)


def test_self_contained_explanation_replaces_previous_vague_request():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-self-contained-explanation-test"

    run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    result = run_noise_to_signal(
        "Explain LangGraph",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    assert result["decision_status"] in {"informational", "insufficient_evidence"}
    assert result["goal"] == "Explain LangGraph"
    assert result["selected_focus"] is None
    assert result["study_plan"] is None
    assert result["original_goal"] is None
    assert result["clarification_context"] is None
    _assert_no_internal_orchestration_text(result)


def test_graph_does_not_duplicate_repeated_clarification_context():
    checkpointer = MemorySaver()
    thread_id = "noise-to-signal-duplicate-memory-test"

    run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )
    repeated_result = run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id=thread_id,
        checkpointer=checkpointer,
    )

    context_items = repeated_result["clarification_context"].splitlines()
    assert context_items == ["AI Product Engineer"]
    assert repeated_result["goal"].count("AI Product Engineer") == 1
    _assert_no_internal_orchestration_text(repeated_result)


def test_graph_checkpoint_memory_is_isolated_by_thread_id():
    checkpointer = MemorySaver()

    thread_a_result = run_noise_to_signal(
        "What should I learn next?",
        [],
        thread_id="thread-a",
        checkpointer=checkpointer,
    )
    thread_b_result = run_noise_to_signal(
        "AI Product Engineer",
        [],
        thread_id="thread-b",
        checkpointer=checkpointer,
    )

    assert thread_a_result["pending_clarification"] is True
    assert thread_b_result["original_goal"] == "AI Product Engineer"
    assert thread_b_result["pending_clarification"] is True
    assert thread_b_result["clarification_context"] is None
    assert thread_b_result["goal"] == "AI Product Engineer"
    assert thread_b_result["original_goal"] != thread_a_result["original_goal"]


def test_run_noise_to_signal_without_thread_id_keeps_single_turn_behavior():
    result = run_noise_to_signal("What should I learn next?", [])

    assert result["decision_status"] == "needs_clarification"
    assert result["original_goal"] == "What should I learn next?"
    assert result["pending_clarification"] is True
    assert result["clarification_context"] is None


def test_graph_result_contains_fields_required_by_noise_to_signal_renderer():
    docs = _langgraph_basic_rag_docs()

    result = run_noise_to_signal("Should I learn LangGraph or basic RAG?", docs)

    for field in APP_RENDERER_FIELDS:
        assert field in result

    assert isinstance(result["decision_trace"], list)
    assert result["study_plan"]["plan"]
    assert "items" in result["evidence"]
    assert "has_evidence" in result["evidence"]
    assert "claims" in result["evidence"]

    evidence_item = result["evidence"]["items"][0]
    assert {
        "title",
        "type_label",
        "page",
        "excerpt",
    }.issubset(evidence_item)


def test_clear_informational_input_does_not_call_llm():
    classifier = RecordingIntentClassifier(
        result={"intent": "needs_clarification", "confidence": 0.1, "reason": "unused"}
    )
    docs = [
        _wef_pdf_doc(
            "The report identifies analytical thinking, AI and big data, "
            "technological literacy, resilience, flexibility, and lifelong "
            "learning as important skills for future work.",
        )
    ]

    result = run_noise_to_signal(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "informational"
    assert result["routing_source"] == "deterministic"
    assert result["routing_attempts"] == 0
    assert classifier.calls == []


def test_clear_comparison_input_does_not_call_llm():
    classifier = RecordingIntentClassifier(
        result={"intent": "needs_clarification", "confidence": 0.1, "reason": "unused"}
    )
    docs = _langgraph_basic_rag_docs()

    result = run_noise_to_signal(
        "Should I learn LangGraph or basic RAG?",
        docs,
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "selected"
    assert result["selected_focus"] == "LangGraph"
    assert result["routing_source"] == "deterministic"
    assert result["routing_attempts"] == 0
    assert classifier.calls == []


def test_clear_single_focus_input_does_not_call_llm():
    classifier = RecordingIntentClassifier(
        result={"intent": "needs_clarification", "confidence": 0.1, "reason": "unused"}
    )

    result = run_noise_to_signal(
        "I want to learn RAG evaluation",
        [],
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "RAG evaluation"
    assert result["routing_source"] == "deterministic"
    assert result["routing_attempts"] == 0
    assert classifier.calls == []


@pytest.mark.parametrize(
    ("goal", "content"),
    [
        (
            "Can you explain LangGraph?",
            "LangGraph workflows can use durable state for multi-step apps.",
        ),
        (
            "What is LangGraph?",
            "LangGraph workflows can use durable state for multi-step apps.",
        ),
        (
            "Describe RAG evaluation.",
            "RAG evaluation checks answer quality, retrieval relevance, and source grounding.",
        ),
    ],
)
def test_clear_explanation_questions_route_deterministically_as_informational(
    goal,
    content,
):
    classifier = RecordingIntentClassifier(
        result={"intent": "single_focus", "confidence": 0.9, "reason": "unused"}
    )
    docs = [
        Document(
            page_content=content,
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal(goal, docs, intent_classifier=classifier)

    assert result["decision_status"] == "informational"
    assert result["selected_focus"] is None
    assert result["study_plan"] is None
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert result["routing_source"] == "deterministic"
    assert result["routing_attempts"] == 0
    assert classifier.calls == []


def test_clear_explanation_question_without_evidence_is_insufficient():
    classifier = RecordingIntentClassifier(
        result={"intent": "single_focus", "confidence": 0.9, "reason": "unused"}
    )

    result = run_noise_to_signal(
        "Can you explain LangGraph?",
        [],
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "insufficient_evidence"
    assert result["selected_focus"] is None
    assert result["study_plan"] is None
    assert result["recommendation"] == (
        "The retrieved evidence is insufficient to answer this question reliably. "
        "Refine the question or add evidence that directly addresses the topic."
    )
    assert result["routing_source"] == "deterministic"
    assert classifier.calls == []


def test_clear_explanation_question_with_unrelated_evidence_is_insufficient():
    classifier = RecordingIntentClassifier(
        result={"intent": "single_focus", "confidence": 0.9, "reason": "unused"}
    )
    docs = [
        _wef_pdf_doc(
            "The report identifies analytical thinking, AI and big data, "
            "technological literacy, resilience, flexibility, and lifelong "
            "learning as important skills for future work.",
        )
    ]

    result = run_noise_to_signal(
        "Can you explain LangGraph?",
        docs,
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "insufficient_evidence"
    assert result["selected_focus"] is None
    assert result["study_plan"] is None
    assert result["recommendation"] == (
        "The retrieved evidence is insufficient to answer this question reliably. "
        "Refine the question or add evidence that directly addresses the topic."
    )
    assert not result["recommendation"].startswith("Based on the retrieved evidence:")
    assert result["routing_source"] == "deterministic"
    assert classifier.calls == []


def test_explanation_question_rejects_superficial_comparison_mention():
    docs = [
        Document(
            page_content=(
                "When comparing RAG evaluation, LangGraph, Docker, and AI agents, "
                "each tool excels in different scenarios."
            ),
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal("Can you explain LangGraph?", docs)

    assert result["decision_status"] == "insufficient_evidence"
    assert result["study_plan"] is None
    assert not result["recommendation"].startswith("Based on the retrieved evidence:")


def test_comparison_without_evidence_preserves_comparison_insufficient_wording():
    result = run_noise_to_signal(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        [],
    )

    assert result["decision_status"] == "insufficient_evidence"
    assert result["study_plan"] is None
    assert result["routing_source"] == "deterministic"
    assert result["recommendation"] == (
        "Evidence is insufficient to choose among the listed options. Refine the "
        "query or retrieve stronger evidence before creating an option-specific "
        "study plan."
    )


def test_clear_explanation_question_with_relevant_evidence_is_informational():
    classifier = RecordingIntentClassifier(
        result={"intent": "single_focus", "confidence": 0.9, "reason": "unused"}
    )
    docs = [
        Document(
            page_content=(
                "LangGraph is a framework for building stateful multi-step agent "
                "workflows with durable execution."
            ),
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal(
        "Can you explain LangGraph?",
        docs,
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "informational"
    assert result["selected_focus"] is None
    assert result["study_plan"] is None
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert "LangGraph" in result["recommendation"]
    assert result["routing_source"] == "deterministic"
    assert classifier.calls == []


def test_explanation_question_accepts_alternative_explanatory_wording():
    docs = [
        Document(
            page_content=(
                "With LangGraph, developers can build stateful multi-step workflows."
            ),
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal("What is LangGraph?", docs)

    assert result["decision_status"] == "informational"
    assert result["study_plan"] is None
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert "LangGraph" in result["recommendation"]


def test_rag_evaluation_explanation_remains_informational():
    docs = [
        Document(
            page_content=(
                "RAG evaluation checks retrieval relevance, answer quality, and "
                "source grounding."
            ),
            metadata={"source": "rag.md", "filename": "rag.md"},
        )
    ]

    result = run_noise_to_signal("Describe RAG evaluation.", docs)

    assert result["decision_status"] == "informational"
    assert result["study_plan"] is None
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert "RAG evaluation" in result["recommendation"]


def test_broad_wef_skills_question_still_accepts_list_style_evidence():
    docs = [
        _wef_pdf_doc(
            "The report identifies analytical thinking, AI and big data, "
            "technological literacy, resilience, flexibility, and lifelong "
            "learning as important skills for future work.",
        )
    ]

    result = run_noise_to_signal(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert result["decision_status"] == "informational"
    assert result["study_plan"] is None
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert "analytical thinking" in result["recommendation"]


def test_standalone_proficiency_level_needs_clarification():
    result = run_noise_to_signal("Intermediate", [])

    assert result["decision_status"] == "needs_clarification"
    assert result["study_plan"] is None
    assert "which skill or domain" in result["recommendation"]
    assert "technology, role, or project" in result["recommendation"]


@pytest.mark.parametrize("goal", ["AI Product Engineer", "Backend Developer"])
def test_short_role_like_input_needs_clarification(goal):
    result = run_noise_to_signal(goal, [])

    assert result["decision_status"] == "needs_clarification"
    assert result["study_plan"] is None
    assert "target role" in result["recommendation"]
    assert "concrete skill, project, or learning decision" in result["recommendation"]
    assert result["selected_focus"] is None


def test_standalone_technology_remains_single_focus():
    result = run_noise_to_signal("LangGraph", [])

    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "LangGraph"
    assert result["study_plan"] is not None


@pytest.mark.parametrize(
    "goal",
    [
        "I want to learn LangGraph.",
        "Help me learn RAG evaluation.",
        "Create a study plan for LangGraph.",
    ],
)
def test_explicit_learning_requests_remain_single_focus(goal):
    classifier = RecordingIntentClassifier(
        result={"intent": "informational", "confidence": 0.9, "reason": "unused"}
    )

    result = run_noise_to_signal(goal, [], intent_classifier=classifier)

    assert result["decision_status"] == "single_focus"
    assert result["study_plan"] is not None
    assert result["routing_source"] == "deterministic"
    assert classifier.calls == []


@pytest.mark.parametrize(
    "goal",
    [
        "I feel dumb about RAG evaluation",
        "I am confused and lost about AI agents",
        "I feel bad because I do not understand embeddings",
        "I hate that I still do not understand LangGraph",
    ],
)
def test_emotional_learning_requests_remain_single_focus(goal):
    classifier = RecordingIntentClassifier(
        result={"intent": "informational", "confidence": 0.9, "reason": "unused"}
    )

    result = run_noise_to_signal(goal, [], intent_classifier=classifier)

    assert result["decision_status"] == "single_focus"
    assert result["study_plan"] is not None
    assert result["routing_source"] == "deterministic"
    assert classifier.calls == []


def test_emotional_out_of_corpus_goal_fails_closed_without_blocking():
    result = run_noise_to_signal("I feel stupid about transformers", [])

    assert result["decision_status"] == "insufficient_evidence"
    assert result["evidence_quality"] == "weak"
    assert "unsafe" not in result["recommendation"].lower()


def test_explanation_about_role_like_phrase_remains_informational():
    docs = [
        Document(
            page_content=(
                "An AI Product Engineer is a product role that works with AI "
                "systems, user needs, evaluation, and delivery constraints."
            ),
            metadata={"source": "role_guide.md", "title": "AI Product Engineer"},
        )
    ]

    result = run_noise_to_signal("Explain what an AI Product Engineer does", docs)

    assert result["decision_status"] == "insufficient_evidence"
    assert result["study_plan"] is None
    assert result["selected_focus"] is None
    assert "target role" not in result["recommendation"]
    assert "concrete skill, project, or learning decision" not in result["recommendation"]


def test_clear_vague_input_remains_deterministic_without_llm():
    classifier = RecordingIntentClassifier(
        result={"intent": "single_focus", "confidence": 0.9, "reason": "unused"}
    )

    result = run_noise_to_signal(
        "What should I learn next?",
        [],
        intent_classifier=classifier,
    )

    assert result["decision_status"] == "needs_clarification"
    assert result["routing_source"] == "deterministic"
    assert result["routing_attempts"] == 0
    assert classifier.calls == []


def test_ambiguous_input_calls_llm_once_and_uses_valid_route():
    classifier = RecordingIntentClassifier(
        result={
            "intent": "informational",
            "confidence": 0.82,
            "reason": "The user is asking whether a specific AI topic fits their transition.",
        }
    )
    docs = [
        Document(
            page_content="LangGraph workflows can use durable state for multi-step apps.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        docs,
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 1
    assert classifier.calls[0]["goal"] == AMBIGUOUS_GOAL
    assert result["decision_status"] == "informational"
    assert result["recommendation"].startswith("Based on the retrieved evidence:")
    assert result["routing_source"] == "llm"
    assert result["routing_confidence"] == 0.82
    assert result["routing_attempts"] == 1
    assert result["routing_reason"] == (
        "The user is asking whether a specific AI topic fits their transition."
    )


def test_ambiguous_input_retries_exception_once_and_uses_second_route():
    classifier = RecordingIntentClassifier(
        results=[
            None,
            {
                "intent": "single_focus",
                "confidence": 0.72,
                "reason": "The second attempt identified a concrete topic.",
                "selected_focus": "LangGraph",
            },
        ],
        errors=[TimeoutError("network timeout"), None],
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 2
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "LangGraph"
    assert result["routing_source"] == "llm"
    assert result["routing_attempts"] == 2


def test_ambiguous_input_retries_invalid_structured_output_once():
    classifier = RecordingIntentClassifier(
        results=[
            {
                "intent": "unsupported",
                "confidence": 0.8,
                "reason": "Invalid route.",
            },
            {
                "intent": "single_focus",
                "confidence": 0.74,
                "reason": "The retry identified a concrete topic.",
                "selected_focus": "LangGraph",
            },
        ]
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 2
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "LangGraph"
    assert result["routing_source"] == "llm"
    assert result["routing_attempts"] == 2


def test_ambiguous_single_focus_without_focus_retries_once():
    classifier = RecordingIntentClassifier(
        results=[
            {
                "intent": "single_focus",
                "confidence": 0.65,
                "reason": "The first attempt omitted the focus.",
                "selected_focus": " ",
            },
            {
                "intent": "single_focus",
                "confidence": 0.79,
                "reason": "The retry supplied a focus.",
                "selected_focus": "backend development",
            },
        ]
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 2
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "backend development"
    assert result["routing_source"] == "llm"
    assert result["routing_attempts"] == 2


def test_ambiguous_comparison_without_enough_options_retries_once():
    classifier = RecordingIntentClassifier(
        results=[
            {
                "intent": "comparison",
                "confidence": 0.63,
                "reason": "The first attempt omitted alternatives.",
                "options": ["LangGraph"],
            },
            {
                "intent": "comparison",
                "confidence": 0.81,
                "reason": "The retry found two explicit options.",
                "options": ["LangGraph", "RAG evaluation"],
            },
        ]
    )
    docs = [
        Document(
            page_content="LangGraph is useful when workflows need durable state.",
            metadata={"source": "agents.md", "filename": "agents.md"},
        )
    ]

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        docs,
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 2
    assert result["decision_status"] == "insufficient_evidence"
    assert result["selected_focus"] is None
    assert result["options"] == ["LangGraph", "RAG evaluation"]
    assert result["routing_source"] == "llm"
    assert result["routing_attempts"] == 2


def test_llm_single_focus_result_controls_plan_route_when_focus_is_valid():
    classifier = RecordingIntentClassifier(
        result={
            "intent": "single_focus",
            "confidence": 0.76,
            "reason": "The user names a concrete learning topic.",
            "selected_focus": "backend development",
        }
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 1
    assert result["decision_status"] == "single_focus"
    assert result["selected_focus"] == "backend development"
    assert result["study_plan"] is not None
    assert result["routing_source"] == "llm"
    assert result["routing_attempts"] == 1


def test_ambiguous_input_falls_back_after_two_failed_attempts():
    classifier = RecordingIntentClassifier(
        errors=[
            TimeoutError("first timeout"),
            RuntimeError("second timeout"),
        ],
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 2
    assert result["decision_status"] == "needs_clarification"
    assert result["selected_focus"] is None
    assert result["routing_source"] == "fallback"
    assert result["routing_confidence"] == 0.0
    assert result["routing_attempts"] == 2
    assert result["routing_reason"] == (
        "LLM intent classification failed; asking for clarification."
    )


def test_valid_llm_clarification_result_is_not_retried():
    classifier = RecordingIntentClassifier(
        result={
            "intent": "needs_clarification",
            "confidence": 0.84,
            "reason": "The ambiguous request needs one more constraint.",
        }
    )

    result = run_noise_to_signal(
        AMBIGUOUS_GOAL,
        [],
        intent_classifier=classifier,
    )

    assert len(classifier.calls) == 1
    assert result["decision_status"] == "needs_clarification"
    assert result["selected_focus"] is None
    assert result["routing_source"] == "llm"
    assert result["routing_confidence"] == 0.84
    assert result["routing_attempts"] == 1
    assert result["routing_reason"] == (
        "The ambiguous request needs one more constraint."
    )
