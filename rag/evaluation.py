"""Simple deterministic RAG retrieval evaluation utilities."""

from pathlib import Path

from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.retriever import retrieve_relevant_chunks


EVALUATION_CASES = [
    {
        "question": "What does the WEF Future of Jobs report say about future skills?",
        "expected_sources": ["wef_future_of_jobs_report_2025.pdf"],
        "expected_metadata": [
            {
                "document_role": "primary_source",
                "source_authority": "official",
                "publisher": "World Economic Forum",
                "source_type": "pdf",
            }
        ],
    },
    {
        "question": "How does ESCO map skills to occupations?",
        "expected_sources_any_of": ["esco_ai_software_skills.md"],
        "expected_metadata": [
            {
                "document_role": "derived_summary",
                "source_authority": "derived_official",
                "publisher": "European Commission",
            }
        ],
    },
    {
        "question": "What skills are expected for an AI Engineer role?",
        "expected_sources_any_of": [
            "wef_future_of_jobs_report_2025.pdf",
            "oecd_ai_skills_gap_2025.md",
            "oecd_ai_and_skills.md",
            "cedefop_ai_skills_europe_2025.md",
            "ai_job_market_skills.md",
        ],
    },
    {
        "question": "Which notes summarize the AI Skill Compass project?",
        "expected_sources": ["ai_skill_compass_notes.md"],
    },
    {
        "question": "How should AI learners connect training to skills evidence?",
        "expected_sources_any_of": [
            "oecd_ai_skills_gap_2025.md",
            "oecd_ai_and_skills.md",
            "cedefop_ai_skills_europe_2025.md",
        ],
        "expected_metadata": [
            {
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            }
        ],
    },
    {
        "question": "What is the capital of France?",
        "expected_sources": [],
    },
]


def _normalize_source(source):
    return Path(str(source)).name.lower().strip()


def _extract_sources(retrieved_documents):
    sources = []
    for doc in retrieved_documents or []:
        source = ""
        if hasattr(doc, "metadata"):
            source = doc.metadata.get("source", "")
        elif isinstance(doc, dict):
            source = doc.get("source") or doc.get("metadata", {}).get("source", "")
        else:
            source = getattr(doc, "source", "")

        if source:
            sources.append(str(source))
    return sources


def _extract_metadata(retrieved_documents):
    metadata_items = []
    for doc in retrieved_documents or []:
        if hasattr(doc, "metadata"):
            metadata = doc.metadata
        elif isinstance(doc, dict):
            metadata = doc.get("metadata", doc)
        else:
            metadata = getattr(doc, "metadata", {})

        if metadata:
            metadata_items.append(metadata)
    return metadata_items


def _match_expected_sources(retrieved_sources, expected_sources):
    normalized_retrieved = [_normalize_source(source) for source in retrieved_sources]
    matched_sources = []
    for expected in expected_sources:
        expected_normalized = _normalize_source(expected)
        if any(expected_normalized in retrieved for retrieved in normalized_retrieved):
            matched_sources.append(expected)
    return matched_sources


def _metadata_matches(metadata, expected_metadata):
    for key, expected_value in expected_metadata.items():
        actual_value = metadata.get(key)

        if str(actual_value).lower() != str(expected_value).lower():
            return False

    return True


def _match_expected_metadata(retrieved_metadata, expected_metadata_items):
    matched_metadata = []

    for expected_metadata in expected_metadata_items:
        if any(
            _metadata_matches(metadata, expected_metadata)
            for metadata in retrieved_metadata
        ):
            matched_metadata.append(expected_metadata)

    return matched_metadata


def evaluate_retrieved_sources(
    question,
    retrieved_documents,
    expected_sources=None,
    expected_sources_any_of=None,
    expected_metadata=None,
):
    """Evaluate whether retrieved sources match expected sources for a question."""
    expected_sources = expected_sources or []
    expected_sources_any_of = expected_sources_any_of or []
    expected_metadata = expected_metadata or []
    retrieved_sources = _extract_sources(retrieved_documents)
    retrieved_metadata = _extract_metadata(retrieved_documents)
    matched_sources = _match_expected_sources(retrieved_sources, expected_sources)
    matched_sources_any_of = _match_expected_sources(
        retrieved_sources,
        expected_sources_any_of,
    )
    matched_metadata = _match_expected_metadata(retrieved_metadata, expected_metadata)

    required_checks = len(expected_sources) + len(expected_metadata)
    passed_checks = len(matched_sources) + len(matched_metadata)

    if expected_sources_any_of:
        required_checks += 1

        if matched_sources_any_of:
            passed_checks += 1

    if not expected_sources and not expected_sources_any_of and not expected_metadata:
        passed = len(retrieved_sources) == 0
        score = 100 if passed else 0
    else:
        score = round((passed_checks / required_checks) * 100)
        passed = passed_checks == required_checks

    return {
        "question": question,
        "passed": passed,
        "matched_sources": matched_sources,
        "matched_sources_any_of": matched_sources_any_of,
        "matched_metadata": matched_metadata,
        "retrieved_sources": retrieved_sources,
        "score": score,
    }


def run_evaluation_set(
    evaluation_cases,
    retrieved_documents_by_question=None,
    directory="data/knowledge_base",
    k=3,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
):
    """Run a deterministic evaluation set against the retriever."""
    results = []
    for case in evaluation_cases:
        question = case["question"]
        expected_sources = case.get("expected_sources", [])
        expected_sources_any_of = case.get("expected_sources_any_of", [])
        expected_metadata = case.get("expected_metadata", [])
        if (
            retrieved_documents_by_question
            and question in retrieved_documents_by_question
        ):
            retrieved_documents = retrieved_documents_by_question[question]
        else:
            retrieved_documents = retrieve_relevant_chunks(
                question,
                directory=directory,
                k=k,
                min_relevance_score=min_relevance_score,
            )
        results.append(
            evaluate_retrieved_sources(
                question,
                retrieved_documents,
                expected_sources,
                expected_sources_any_of,
                expected_metadata,
            )
        )

    total = len(results)
    pass_rate = (
        round((sum(result["passed"] for result in results) / total) * 100)
        if total
        else 0
    )
    return {"results": results, "pass_rate": pass_rate}
