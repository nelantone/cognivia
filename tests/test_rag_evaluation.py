"""Tests for simple RAG evaluation utilities."""

import rag.evaluation as evaluation
from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.evaluation import (
    EVALUATION_CASES,
    _extract_sources,
    _match_expected_sources,
    evaluate_retrieved_sources,
    run_evaluation_set,
)


class FakeDocument:
    def __init__(self, source, **metadata):
        self.metadata = {"source": source, **metadata}


def test_extract_sources_handles_documents_and_dicts():
    docs = [
        FakeDocument("data/knowledge_base/a.md"),
        {"source": "data/knowledge_base/b.md"},
        {"metadata": {"source": "data/knowledge_base/c.md"}},
    ]

    sources = _extract_sources(docs)

    assert sources == [
        "data/knowledge_base/a.md",
        "data/knowledge_base/b.md",
        "data/knowledge_base/c.md",
    ]


def test_match_expected_sources_uses_filename_matching():
    retrieved_sources = [
        "data/knowledge_base/derived/oecd_ai_skills_gap_2025.md",
        "data/knowledge_base/ai_job_market_skills.md",
    ]
    expected_sources = ["oecd_ai_skills_gap_2025.md"]

    matched = _match_expected_sources(retrieved_sources, expected_sources)

    assert matched == ["oecd_ai_skills_gap_2025.md"]


def test_evaluation_cases_do_not_reference_removed_public_source_catalog():
    serialized_cases = repr(EVALUATION_CASES)

    assert "public_career_skill_sources.md" not in serialized_cases
    assert "public_sources_notes.md" not in serialized_cases


def test_evaluate_retrieved_sources_returns_expected_shape_and_score():
    docs = [
        FakeDocument("data/knowledge_base/derived/oecd_ai_skills_gap_2025.md"),
        FakeDocument("data/knowledge_base/other.md"),
    ]

    result = evaluate_retrieved_sources(
        question="Which sources mention AI skills?",
        retrieved_documents=docs,
        expected_sources=["oecd_ai_skills_gap_2025.md"],
    )

    assert result["question"] == "Which sources mention AI skills?"
    assert result["passed"] is True
    assert result["matched_sources"] == ["oecd_ai_skills_gap_2025.md"]
    assert result["matched_sources_any_of"] == []
    assert result["matched_metadata"] == []
    assert (
        "data/knowledge_base/derived/oecd_ai_skills_gap_2025.md"
        in result["retrieved_sources"]
    )
    assert result["score"] == 100


def test_evaluate_retrieved_sources_recognizes_wef_pdf_source_and_metadata():
    docs = [
        FakeDocument(
            "data/sources/pdfs/wef_future_of_jobs_report_2025.pdf",
            document_role="primary_source",
            source_authority="official",
            publisher="World Economic Forum",
            source_type="pdf",
        )
    ]

    result = evaluate_retrieved_sources(
        question="What does WEF say about future skills?",
        retrieved_documents=docs,
        expected_sources=["wef_future_of_jobs_report_2025.pdf"],
        expected_metadata=[
            {
                "document_role": "primary_source",
                "source_authority": "official",
                "publisher": "World Economic Forum",
                "source_type": "pdf",
            }
        ],
    )

    assert result["passed"] is True
    assert result["matched_sources"] == ["wef_future_of_jobs_report_2025.pdf"]
    assert result["matched_metadata"] == [
        {
            "document_role": "primary_source",
            "source_authority": "official",
            "publisher": "World Economic Forum",
            "source_type": "pdf",
        }
    ]


def test_evaluate_retrieved_sources_accepts_configured_any_of_current_sources():
    docs = [
        FakeDocument(
            "data/knowledge_base/derived/oecd_ai_skills_gap_2025.md",
            document_role="derived_summary",
            source_authority="derived_official",
            publisher="OECD",
        )
    ]

    result = evaluate_retrieved_sources(
        question="What skills are expected for an AI Engineer role?",
        retrieved_documents=docs,
        expected_sources_any_of=[
            "wef_future_of_jobs_report_2025.pdf",
            "oecd_ai_skills_gap_2025.md",
            "cedefop_ai_skills_europe_2025.md",
        ],
        expected_metadata=[
            {
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            }
        ],
    )

    assert result["passed"] is True
    assert result["matched_sources_any_of"] == ["oecd_ai_skills_gap_2025.md"]
    assert result["score"] == 100


def test_evaluate_retrieved_sources_rejects_unrelated_sources():
    docs = [
        FakeDocument(
            "data/knowledge_base/internal/unrelated.md",
            document_role="internal_note",
            source_authority="internal",
        )
    ]

    result = evaluate_retrieved_sources(
        question="What skills are expected for an AI Engineer role?",
        retrieved_documents=docs,
        expected_sources_any_of=[
            "wef_future_of_jobs_report_2025.pdf",
            "oecd_ai_skills_gap_2025.md",
            "cedefop_ai_skills_europe_2025.md",
        ],
        expected_metadata=[
            {
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            }
        ],
    )

    assert result["passed"] is False
    assert result["matched_sources_any_of"] == []
    assert result["matched_metadata"] == []


def test_evaluate_retrieved_sources_handles_negative_case():
    result = evaluate_retrieved_sources(
        question="What is the capital of France?",
        retrieved_documents=[],
        expected_sources=[],
    )

    assert result["question"] == "What is the capital of France?"
    assert result["passed"] is True
    assert result["matched_sources"] == []
    assert result["retrieved_sources"] == []
    assert result["score"] == 100


def test_evaluate_retrieved_sources_rejects_unrelated_negative_case_results():
    docs = [FakeDocument("data/knowledge_base/internal/unrelated.md")]

    result = evaluate_retrieved_sources(
        question="What is the capital of France?",
        retrieved_documents=docs,
        expected_sources=[],
    )

    assert result["passed"] is False
    assert result["matched_sources"] == []
    assert result["retrieved_sources"] == [
        "data/knowledge_base/internal/unrelated.md"
    ]
    assert result["score"] == 0


def test_run_evaluation_set_uses_stubbed_retrieval():
    evaluation_cases = [
        {
            "question": "WEF future skills question",
            "expected_sources": ["wef_future_of_jobs_report_2025.pdf"],
        },
        {
            "question": "AI Engineer skills question",
            "expected_sources_any_of": [
                "oecd_ai_skills_gap_2025.md",
                "ai_job_market_skills.md",
            ],
        },
        {
            "question": "Weak context question",
            "expected_sources": [],
        },
    ]

    retrieved_documents_by_question = {
        "WEF future skills question": [
            FakeDocument("data/sources/pdfs/wef_future_of_jobs_report_2025.pdf")
        ],
        "AI Engineer skills question": [
            FakeDocument("data/knowledge_base/derived/oecd_ai_skills_gap_2025.md")
        ],
        "Weak context question": [],
    }

    result = run_evaluation_set(
        evaluation_cases,
        retrieved_documents_by_question=retrieved_documents_by_question,
    )

    assert result["pass_rate"] == 100
    assert len(result["results"]) == 3


def test_run_evaluation_set_passes_default_relevance_threshold(monkeypatch):
    calls = []

    def fake_retrieve(question, directory, k, min_relevance_score):
        calls.append(
            {
                "question": question,
                "directory": directory,
                "k": k,
                "min_relevance_score": min_relevance_score,
            }
        )
        return []

    monkeypatch.setattr(evaluation, "retrieve_relevant_chunks", fake_retrieve)

    run_evaluation_set(
        [{"question": "What is the capital of France?", "expected_sources": []}],
        directory="test-dir",
        k=5,
    )

    assert calls == [
        {
            "question": "What is the capital of France?",
            "directory": "test-dir",
            "k": 5,
            "min_relevance_score": DEFAULT_MIN_RELEVANCE_SCORE,
        }
    ]


def test_run_evaluation_set_pass_rate_counts_negative_case():
    evaluation_cases = [
        {
            "question": "WEF future skills question",
            "expected_sources": ["wef_future_of_jobs_report_2025.pdf"],
        },
        {
            "question": "Weak context question",
            "expected_sources": [],
        },
        {
            "question": "AI Engineer skills question",
            "expected_sources": ["ai_job_market_skills.md"],
        },
    ]

    retrieved_documents_by_question = {
        "WEF future skills question": [
            FakeDocument("data/sources/pdfs/wef_future_of_jobs_report_2025.pdf")
        ],
        "Weak context question": [],
        "AI Engineer skills question": [FakeDocument("data/knowledge_base/other.md")],
    }

    result = run_evaluation_set(
        evaluation_cases,
        retrieved_documents_by_question=retrieved_documents_by_question,
    )

    assert result["pass_rate"] == 67
    assert len(result["results"]) == 3
