"""Tests for study plan tool."""

import pytest
from langchain_core.documents import Document

from tools.study_plan import (
    build_informational_answer,
    build_noise_to_signal_decision,
    format_evidence_label,
    generate_study_plan,
    guided_intake_entry_point_for_goal,
    select_diverse_evidence,
    summarize_retrieved_evidence,
)


def _total_step_minutes(plan):
    return sum(step["time_minutes"] for step in plan["steps"])


def test_generate_study_plan_returns_expected_keys():
    result = generate_study_plan(
        topic="RAG",
        available_time=60,
        energy_level="medium",
        current_level="beginner",
    )

    assert "plan" in result
    assert "expected_outcome" in result
    assert "goal" in result
    assert "steps" in result


def test_generate_study_plan_includes_topic():
    result = generate_study_plan(
        topic="LangChain",
        available_time=45,
        energy_level="high",
        current_level="beginner",
    )

    assert "LangChain" in result["goal"]
    assert "LangChain" in result["plan"]


def test_generate_study_plan_short_time_has_focused_steps():
    result = generate_study_plan(
        topic="MCP",
        available_time=30,
        energy_level="low",
        current_level="beginner",
    )

    assert len(result["steps"]) == 3
    assert all("time_minutes" in step for step in result["steps"])


def test_short_session_has_smaller_steps_than_long_session():
    short_plan = generate_study_plan(
        topic="MCP",
        available_time=30,
        energy_level="medium",
        current_level="intermediate",
    )
    long_plan = generate_study_plan(
        topic="MCP",
        available_time=120,
        energy_level="medium",
        current_level="intermediate",
    )

    assert len(short_plan["steps"]) < len(long_plan["steps"])


def test_advanced_plan_mentions_tradeoffs_or_edge_cases():
    result = generate_study_plan(
        topic="RAG",
        available_time=120,
        energy_level="high",
        current_level="advanced",
    )

    plan_text = result["plan"].lower()
    expected_text = result["expected_outcome"].lower()
    assert (
        "trade-off" in plan_text
        or "edge case" in plan_text
        or "trade-off" in expected_text
    )


def test_beginner_plan_mentions_fundamentals():
    result = generate_study_plan(
        topic="RAG",
        available_time=60,
        energy_level="medium",
        current_level="beginner",
    )

    plan_text = result["plan"].lower()
    expected_text = result["expected_outcome"].lower()
    assert "fundamental" in plan_text or "fundamental" in expected_text


def test_invalid_available_time_raises_value_error():
    with pytest.raises(ValueError, match="greater than 0"):
        generate_study_plan(
            topic="RAG",
            available_time=0,
            energy_level="medium",
            current_level="beginner",
        )


def test_invalid_energy_level_raises_value_error():
    with pytest.raises(ValueError, match="energy_level"):
        generate_study_plan(
            topic="RAG",
            available_time=60,
            energy_level="super tired",
            current_level="beginner",
        )


def test_summarize_retrieved_evidence_handles_empty_retrieval():
    summary = summarize_retrieved_evidence([])

    assert summary["has_evidence"] is False
    assert summary["items"] == []
    assert "No retrieved" in summary["summary"]


def test_summarize_retrieved_evidence_uses_document_content_and_metadata():
    docs = [
        Document(
            page_content="RAG evaluation should check answer quality and source grounding.",
            metadata={"source": "rag-notes.md", "chunk_index": 2},
        )
    ]

    summary = summarize_retrieved_evidence(docs)

    assert summary["has_evidence"] is True
    assert summary["items"][0]["source"] == "rag-notes.md"
    assert summary["items"][0]["title"] == "RAG Notes"
    assert summary["items"][0]["chunk_index"] == 2
    assert "source grounding" in summary["summary"]


def test_noise_to_signal_decision_uses_evidence_for_outputs():
    raw_chunk = "LangGraph is useful when workflows need durable state."
    docs = [
        Document(
            page_content=raw_chunk,
            metadata={"source": "agents.md", "chunk_index": 1},
        )
    ]

    decision = build_noise_to_signal_decision(
        "Should I learn LangGraph or basic RAG?",
        docs,
    )

    assert decision["selected_focus"] == "LangGraph"
    assert decision["decision_status"] == "selected"
    assert "portfolio-ready" in decision["recommendation"]
    assert raw_chunk not in decision["recommendation"]
    assert "agents.md" not in decision["next_action"]
    assert raw_chunk not in decision["next_action"]
    assert any("Selected focus: LangGraph" in item for item in decision["decision_trace"])


@pytest.mark.parametrize(
    ("goal", "expected_options"),
    [
        (
            "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
            ["RAG evaluation", "LangGraph", "Docker", "AI agents"],
        ),
        (
            "According to future job-market trends, should I prioritize RAG "
            "evaluation, LangGraph, Docker, or AI agents?",
            ["RAG evaluation", "LangGraph", "Docker", "AI agents"],
        ),
        (
            "Should I focus on LangGraph or RAG evaluation?",
            ["LangGraph", "RAG evaluation"],
        ),
        (
            "Should I learn Docker or agents?",
            ["Docker", "agents"],
        ),
    ],
)
def test_noise_to_signal_decision_extracts_natural_question_options(
    goal,
    expected_options,
):
    decision = build_noise_to_signal_decision(goal, [])

    assert decision["options"] == expected_options
    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "insufficient_evidence"
    assert decision["selected_focus"] != expected_options[0]


def test_noise_to_signal_decision_uses_single_focus_for_explicit_topic():
    decision = build_noise_to_signal_decision("I want to learn RAG evaluation", [])

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["decision_status"] == "single_focus"
    assert decision["tied_options"] == []
    assert "not strongly evidence-grounded" in decision["recommendation"]


@pytest.mark.parametrize(
    "goal",
    [
        "I feel stupid about transformers",
        "I feel dumb about RAG evaluation",
        "I am confused and lost about AI agents",
        "I feel bad because I do not understand embeddings",
        "I hate that I still do not understand LangGraph",
    ],
)
def test_noise_to_signal_decision_accepts_emotional_learning_goals(goal):
    decision = build_noise_to_signal_decision(goal, [])

    assert decision["decision_status"] == "single_focus"
    assert decision["interaction_mode"] == "direct_decision"
    assert decision["selected_focus"]
    assert "study plan" in decision["recommendation"].lower()


def test_noise_to_signal_decision_uses_single_focus_for_bare_topic():
    decision = build_noise_to_signal_decision("RAG evaluation", [])

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["decision_status"] == "single_focus"
    assert decision["interaction_mode"] == "direct_decision"


def test_noise_to_signal_decision_keeps_concrete_learning_path_as_single_focus():
    decision = build_noise_to_signal_decision(
        "I want a RAG evaluation learning path",
        [],
    )

    assert decision["selected_focus"] is not None
    assert "RAG evaluation" in decision["selected_focus"]
    assert decision["decision_status"] == "single_focus"
    assert decision["interaction_mode"] == "direct_decision"
    assert decision["guided_intake_entry_point"] is None


@pytest.mark.parametrize(
    "goal",
    [
        "What should I learn next?",
        "What should I study next?",
    ],
)
def test_noise_to_signal_decision_requests_clarification_for_vague_goal(goal):
    decision = build_noise_to_signal_decision(goal, [])

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "needs_clarification"
    assert decision["needs_clarification"] is True
    assert decision["interaction_mode"] == "guided_intake"
    assert decision["guided_intake_entry_point"] == "I want to choose what to learn next"
    assert "learner profile context" in decision["recommendation"]
    assert "current level" in decision["next_action"]


@pytest.mark.parametrize(
    ("goal", "expected_entry_point"),
    [
        (
            "I feel lost and want a practical AI learning path",
            "I feel lost and need direction",
        ),
        (
            "What should I learn next?",
            "I want to choose what to learn next",
        ),
        (
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        (
            "What skills should I learn for backend development?",
            "I want to choose what to learn next",
        ),
    ],
)
def test_guided_intake_entry_point_covers_vague_and_guidance_goals(
    goal,
    expected_entry_point,
):
    assert guided_intake_entry_point_for_goal(goal) == expected_entry_point


def test_noise_to_signal_decision_routes_lost_learning_path_to_guided_intake():
    decision = build_noise_to_signal_decision(
        "I feel lost and want a practical AI learning path",
        [],
    )

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "needs_clarification"
    assert decision["needs_clarification"] is True
    assert decision["interaction_mode"] == "guided_intake"
    assert decision["guided_intake_entry_point"] == "I feel lost and need direction"
    assert "learner profile context" in decision["recommendation"]
    assert "I feel lost and want a practical AI learning path" not in decision[
        "recommendation"
    ]


def test_noise_to_signal_decision_answers_informational_wef_question_with_evidence():
    docs = [
        Document(
            page_content=(
                "The report identifies analytical thinking, AI and big data, "
                "technological literacy, resilience, flexibility, and lifelong "
                "learning as important skills for future work."
            ),
            metadata={
                "source": "data/sources/pdfs/wef_future_of_jobs_report_2025.pdf",
                "filename": "wef_future_of_jobs_report_2025.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 39,
                "title": "Future of Jobs Report 2025",
            },
        )
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert decision["decision_status"] == "informational"
    assert decision["selected_focus"] is None
    assert decision["needs_clarification"] is False
    assert "Based on the retrieved evidence" in decision["recommendation"]
    assert "analytical thinking" in decision["recommendation"]
    assert "ask for a study plan for that specific skill" in decision["next_action"]


def test_informational_answer_uses_limited_claim_subset_with_many_chunks():
    docs = [
        Document(
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
        for page, content in [
            (35, "Analytical thinking remains a core skill for future work."),
            (36, "AI and big data are among fast-growing technology skills."),
            (37, "Technological literacy is expected to matter across roles."),
            (38, "Programming skills support technical work in AI systems."),
            (39, "Networks and cybersecurity remain important technical skills."),
        ]
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert decision["decision_status"] == "informational"
    assert "Analytical thinking" in decision["recommendation"]
    assert "AI and big data" in decision["recommendation"]
    assert "Technological literacy" in decision["recommendation"]
    assert "Programming skills" not in decision["recommendation"]
    assert decision["recommendation"].count("Future of Jobs Report 2025") == 1
    assert len(decision["recommendation"]) < 520


def test_build_informational_answer_respects_configured_claim_limit():
    reasoning_items = [
        {
            "title": "Future of Jobs Report 2025",
            "source_type": "pdf",
            "document_role": "primary_source",
            "source_authority": "official",
            "page": page,
            "claim": claim,
        }
        for page, claim in [
            (35, "Analytical thinking remains a core skill for future work."),
            (36, "AI and big data are among fast-growing technology skills."),
            (37, "Technological literacy is expected to matter across roles."),
        ]
    ]

    answer = build_informational_answer(
        "What skills does the WEF report identify?",
        reasoning_items,
        max_claims=2,
    )

    assert "Analytical thinking" in answer
    assert "AI and big data" in answer
    assert "Technological literacy" not in answer
    assert "pages 35, 36" in answer


def test_informational_answer_allows_distinct_same_pdf_pages_without_repeated_title():
    docs = [
        Document(
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
        for page, content in [
            (35, "Analytical thinking remains a core skill for future work."),
            (36, "Resilience and flexibility support workers through transition."),
            (37, "Lifelong learning helps workers adapt to changing skill demand."),
        ]
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert "Analytical thinking" in decision["recommendation"]
    assert "Resilience and flexibility" in decision["recommendation"]
    assert "Lifelong learning" in decision["recommendation"]
    assert decision["recommendation"].count("Future of Jobs Report 2025") == 1
    assert "pages 35, 36, 37" in decision["recommendation"]


def test_informational_answer_excludes_boilerplate_when_stronger_claims_exist():
    docs = [
        Document(
            page_content="Table 3.4 Skills outlook by occupation and region.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 34,
                "title": "Future of Jobs Report 2025",
            },
        ),
        Document(
            page_content="Source World Economic Forum survey response totals.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 34,
                "title": "Future of Jobs Report 2025",
            },
        ),
        Document(
            page_content="AI and big data are among fast-growing technology skills.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 36,
                "title": "Future of Jobs Report 2025",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert "AI and big data" in decision["recommendation"]
    assert "Table 3.4" not in decision["recommendation"]
    assert "survey response totals" not in decision["recommendation"]


def test_informational_answer_with_only_boilerplate_returns_insufficient_evidence():
    docs = [
        Document(
            page_content="Table 3.4 Skills outlook by occupation and region.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 34,
                "title": "Future of Jobs Report 2025",
            },
        ),
        Document(
            page_content="Source World Economic Forum survey response totals.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 34,
                "title": "Future of Jobs Report 2025",
            },
        ),
        Document(
            page_content="Appendix C contains notes about survey weighting.",
            metadata={
                "source": "wef.pdf",
                "filename": "wef.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 35,
                "title": "Future of Jobs Report 2025",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert decision["decision_status"] == "insufficient_evidence"
    assert decision["selected_focus"] is None
    assert decision["needs_clarification"] is False
    assert "Based on the retrieved evidence" not in decision["recommendation"]
    assert "without inventing details" in decision["recommendation"]


def test_informational_answer_hides_paths_internal_metadata_and_every_page_list():
    docs = [
        Document(
            page_content=content,
            metadata={
                "source": "data/sources/pdfs/wef_future_of_jobs_report_2025.pdf",
                "filename": "wef_future_of_jobs_report_2025.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": page,
                "title": "Future of Jobs Report 2025",
                "_id": f"internal-{page}",
                "_collection_name": "skill_compass_knowledge_base",
            },
        )
        for page, content in [
            (35, "Analytical thinking remains a core skill for developers."),
            (36, "AI and big data are growing technical skill areas."),
            (37, "Technological literacy supports adaptation across roles."),
            (38, "Programming skills remain relevant to software work."),
            (39, "Networks and cybersecurity matter for technical roles."),
            (40, "Creative thinking supports problem solving in teams."),
            (41, "Quality control helps workers evaluate system outputs."),
        ]
    ]

    decision = build_noise_to_signal_decision(
        "What skills does the WEF Future of Jobs Report 2025 identify as important for developers?",
        docs,
    )

    assert "data/sources" not in decision["recommendation"]
    assert "_collection_name" not in decision["recommendation"]
    assert "internal-" not in decision["recommendation"]
    assert "pages 35, 36, 37" in decision["recommendation"]
    assert "38" not in decision["recommendation"].split("pages", 1)[1]


def test_noise_to_signal_decision_informational_question_without_evidence_does_not_invent_answer():
    decision = build_noise_to_signal_decision(
        "What does WEF identify as important for developers?",
        [],
    )

    assert decision["decision_status"] == "insufficient_evidence"
    assert decision["selected_focus"] is None
    assert decision["needs_clarification"] is False
    assert "does not contain enough usable evidence" in decision["recommendation"]
    assert "without inventing details" in decision["recommendation"]


def test_noise_to_signal_decision_preserves_help_me_learn_as_single_focus():
    decision = build_noise_to_signal_decision("Help me learn RAG evaluation.", [])

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["decision_status"] == "single_focus"
    assert decision["needs_clarification"] is False


def test_noise_to_signal_decision_preserves_comparison_path_over_informational_patterns():
    docs = [
        Document(
            page_content="RAG evaluation checks answer quality and source grounding.",
            metadata={"source": "rag.md", "filename": "rag.md"},
        )
    ]

    decision = build_noise_to_signal_decision(
        "According to future job-market trends, should I prioritize RAG evaluation or LangGraph?",
        docs,
    )

    assert decision["options"] == ["RAG evaluation", "LangGraph"]
    assert decision["decision_status"] == "selected"
    assert decision["selected_focus"] == "RAG evaluation"


def test_noise_to_signal_decision_treats_learning_guidance_as_clarification():
    decision = build_noise_to_signal_decision(
        "What skills should I learn for backend development?",
        [],
    )

    assert decision["decision_status"] == "needs_clarification"
    assert decision["selected_focus"] is None
    assert decision["needs_clarification"] is True
    assert decision["interaction_mode"] == "guided_intake"
    assert "learner profile context" in decision["recommendation"]


def test_noise_to_signal_decision_does_not_select_first_option_without_documents():
    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        [],
    )

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "insufficient_evidence"
    assert decision["options"][0] == "RAG evaluation"
    assert "RAG evaluation" not in decision["recommendation"].split(".", 1)[0]


def test_noise_to_signal_decision_does_not_select_option_for_unrelated_evidence():
    docs = [
        Document(
            page_content="This evidence is about salary negotiation and interview pacing.",
            metadata={"source": "career.md", "filename": "career.md"},
        )
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        docs,
    )

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "insufficient_evidence"
    assert all(item["score"] == 0 for item in decision["option_scores"])


def test_noise_to_signal_decision_selects_highest_scoring_option_from_evidence():
    docs = [
        Document(
            page_content=(
                "RAG evaluation should check answer quality, retrieval relevance, "
                "and source grounding before adding more advanced agent behavior."
            ),
            metadata={"source": "rag.md", "filename": "rag.md"},
        ),
        Document(
            page_content="Docker is useful for deployment but is not the main learning gap.",
            metadata={"source": "deployment.md", "filename": "deployment.md"},
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        docs,
    )

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["decision_status"] == "selected"
    assert any("ranks above" in item for item in decision["decision_trace"])
    assert decision["option_scores"][0]["option"] == "RAG evaluation"


def test_noise_to_signal_decision_scores_relevant_chunk_after_display_limit():
    docs = [
        Document(
            page_content="Primary PDF evidence about broad technology skills.",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 5,
            },
        ),
        Document(
            page_content="OECD evidence about general AI skills and training.",
            metadata={
                "source": "oecd.md",
                "filename": "oecd.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        ),
        Document(
            page_content="Internal note about broad developer learning priorities.",
            metadata={
                "source": "internal.md",
                "filename": "internal.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content=(
                "RAG evaluation should check retrieval quality, answer quality, "
                "and source grounding before agent orchestration."
            ),
            metadata={
                "source": "rag-extra.md",
                "filename": "rag-extra.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation, LangGraph, Docker, or AI agents?",
        docs,
    )

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["decision_status"] == "selected"
    assert len(decision["evidence"]["items"]) == 3
    assert all(item["source"] != "rag-extra.md" for item in decision["evidence"]["items"])


def test_noise_to_signal_decision_display_limit_remains_small_and_diverse():
    docs = [
        Document(
            page_content="Primary PDF evidence about future technology skills.",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 5,
            },
        ),
        Document(
            page_content="Another PDF chunk about AI skill demand.",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 6,
            },
        ),
        Document(
            page_content="OECD evidence about training and AI skills.",
            metadata={
                "source": "oecd.md",
                "filename": "oecd.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        ),
        Document(
            page_content="Internal evidence about RAG evaluation practice.",
            metadata={
                "source": "internal.md",
                "filename": "internal.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation or Docker?",
        docs,
    )
    displayed_sources = [item["source"] for item in decision["evidence"]["items"]]

    assert len(displayed_sources) == 3
    assert displayed_sources.count("future_jobs.pdf") == 1
    assert "oecd.md" in displayed_sources
    assert "internal.md" in displayed_sources


def test_noise_to_signal_decision_option_scoring_does_not_depend_on_display_order():
    docs = [
        Document(
            page_content="OECD evidence about general training and AI skills.",
            metadata={
                "source": "oecd.md",
                "filename": "oecd.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        ),
        Document(
            page_content="Docker helps package applications for deployment.",
            metadata={
                "source": "docker.md",
                "filename": "docker.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content="RAG evaluation checks answer quality and source grounding.",
            metadata={
                "source": "rag.md",
                "filename": "rag.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content="RAG evaluation also checks retrieval relevance.",
            metadata={
                "source": "rag-late.md",
                "filename": "rag-late.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize Docker or RAG evaluation?",
        docs,
    )

    assert decision["selected_focus"] == "RAG evaluation"
    assert decision["option_scores"][0]["option"] == "RAG evaluation"


def test_noise_to_signal_decision_late_chunk_prevents_false_insufficient_evidence():
    docs = [
        Document(
            page_content="General evidence about developer learning.",
            metadata={"source": "general.md", "filename": "general.md"},
        ),
        Document(
            page_content="More general evidence about market skills.",
            metadata={"source": "market.md", "filename": "market.md"},
        ),
        Document(
            page_content="Additional general evidence about AI literacy.",
            metadata={"source": "literacy.md", "filename": "literacy.md"},
        ),
        Document(
            page_content="LangGraph is useful when workflows need durable state.",
            metadata={"source": "langgraph.md", "filename": "langgraph.md"},
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I learn LangGraph or Docker?",
        docs,
    )

    assert decision["selected_focus"] == "LangGraph"
    assert decision["decision_status"] == "selected"


def test_noise_to_signal_decision_late_chunk_breaks_display_only_tie():
    docs = [
        Document(
            page_content="Docker and LangGraph both help practical AI projects.",
            metadata={"source": "tie.md", "filename": "tie.md"},
        ),
        Document(
            page_content="General official AI skills evidence.",
            metadata={
                "source": "official.md",
                "filename": "official.md",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        ),
        Document(
            page_content="General internal AI learning evidence.",
            metadata={
                "source": "internal.md",
                "filename": "internal.md",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content="LangGraph supports durable state for multi-step workflows.",
            metadata={"source": "langgraph-extra.md", "filename": "langgraph-extra.md"},
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I learn Docker or LangGraph?",
        docs,
    )

    assert decision["selected_focus"] == "LangGraph"
    assert decision["decision_status"] == "selected"
    assert decision["tied_options"] == []


def test_noise_to_signal_decision_excludes_unusable_and_project_docs_from_scoring():
    docs = [
        Document(
            page_content="RAG evaluation",
            metadata={"source": "too-short.md", "filename": "too-short.md"},
        ),
        Document(
            page_content="RAG evaluation appears in project documentation only.",
            metadata={
                "source": "public_sources_notes.md",
                "filename": "public_sources_notes.md",
                "document_role": "project_documentation",
            },
        ),
    ]

    decision = build_noise_to_signal_decision(
        "Should I prioritize RAG evaluation or Docker?",
        docs,
    )

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "insufficient_evidence"
    assert decision["evidence"]["items"] == []


def test_noise_to_signal_decision_reports_positive_score_tie_without_selecting_first():
    docs = [
        Document(
            page_content="Docker and LangGraph both help structure practical AI projects.",
            metadata={"source": "tools.md", "filename": "tools.md"},
        )
    ]

    decision = build_noise_to_signal_decision(
        "Should I learn Docker or LangGraph?",
        docs,
    )

    assert decision["selected_focus"] is None
    assert decision["decision_status"] == "tie"
    assert decision["tied_options"] == ["Docker", "LangGraph"]
    assert "immediate project value" in decision["next_action"]


def test_noise_to_signal_decision_handles_empty_vague_evidence():
    decision = build_noise_to_signal_decision("What should I learn next?", [])

    assert decision["evidence"]["has_evidence"] is False
    assert decision["decision_status"] == "needs_clarification"
    assert decision["interaction_mode"] == "guided_intake"
    assert "learner profile context" in decision["recommendation"]
    assert decision["decision_trace"][-1].startswith("Next action:")
    assert "current level" in decision["next_action"]


def test_generate_study_plan_can_include_evidence_summary_without_extra_time():
    base_result = generate_study_plan(
        topic="RAG evaluation",
        available_time=60,
        energy_level="medium",
        current_level="intermediate",
    )
    result = generate_study_plan(
        topic="RAG evaluation",
        available_time=60,
        energy_level="medium",
        current_level="intermediate",
        evidence_summary="Prefer source-grounded checks before complex metrics.",
    )

    assert "retrieved evidence" in result["plan"]
    assert "source-grounded checks" not in result["plan"]
    assert "evidence-backed next decision" in result["plan"]
    assert "retrieved evidence" in result["expected_outcome"]
    assert len(result["steps"]) == len(base_result["steps"])
    assert _total_step_minutes(result) == _total_step_minutes(base_result)
    assert _total_step_minutes(result) <= 60


@pytest.mark.parametrize("available_time", [30, 60, 120, 121])
def test_evidence_plan_total_time_does_not_exceed_supported_budget(available_time):
    result = generate_study_plan(
        topic="RAG evaluation",
        available_time=available_time,
        energy_level="medium",
        current_level="intermediate",
        evidence_summary="Use source-grounded checks.",
    )

    assert _total_step_minutes(result) <= available_time


def test_generate_study_plan_without_evidence_keeps_existing_shape():
    result = generate_study_plan(
        topic="RAG evaluation",
        available_time=60,
        energy_level="medium",
        current_level="intermediate",
    )

    assert len(result["steps"]) == 4
    assert _total_step_minutes(result) == 60
    assert "retrieved evidence" not in result["plan"]
    assert "evidence-backed next decision" not in result["plan"]


def test_generate_study_plan_ignores_empty_evidence_summary():
    result = generate_study_plan(
        topic="RAG evaluation",
        available_time=60,
        energy_level="medium",
        current_level="intermediate",
        evidence_summary="   ",
    )

    assert len(result["steps"]) == 4
    assert _total_step_minutes(result) == 60
    assert "retrieved evidence" not in result["plan"]


def test_markdown_evidence_label_is_readable_without_full_path():
    docs = [
        Document(
            page_content="AI job-market skills include RAG evaluation and deployment.",
            metadata={
                "source": "data/knowledge_base/ai_job_market_skills.md",
                "source_type": "markdown",
                "filename": "ai_job_market_skills.md",
                "chunk_index": 0,
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)
    label = format_evidence_label(evidence["items"][0])

    assert label == "AI Job Market Skills"
    assert "data/knowledge_base" not in label
    assert evidence["items"][0]["type_label"] == "Markdown"


def test_pdf_evidence_label_includes_filename_and_page_when_available():
    docs = [
        Document(
            page_content="Analytical thinking remains a core skill in future jobs.",
            metadata={
                "source": "data/sources/pdfs/wef_future_of_jobs_2025.pdf",
                "source_type": "pdf",
                "filename": "wef_future_of_jobs_2025.pdf",
                "page": 43,
                "chunk_index": 2,
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)
    label = format_evidence_label(evidence["items"][0])

    assert label == "WEF Future of Jobs 2025 - page 43"
    assert evidence["items"][0]["type_label"] == "PDF"


def test_evidence_label_prefers_verified_title_metadata():
    docs = [
        Document(
            page_content="AI skills evidence should connect training to reliable use.",
            metadata={
                "source": "data/knowledge_base/derived/oecd_ai_skills_gap_2025.md",
                "filename": "oecd_ai_skills_gap_2025.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
                "title": "OECD AI Skills Gap 2025",
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)

    assert format_evidence_label(evidence["items"][0]) == "OECD AI Skills Gap 2025"
    assert evidence["items"][0]["type_label"] == "Derived official summary"


def test_pdf_evidence_label_includes_zero_page_when_available():
    docs = [
        Document(
            page_content="The first PDF page can contain useful overview evidence.",
            metadata={
                "source": "future_jobs.pdf",
                "source_type": "pdf",
                "filename": "future_jobs.pdf",
                "page": 0,
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)

    assert format_evidence_label(evidence["items"][0]) == "Future Jobs - page 0"


def test_pdf_evidence_label_handles_missing_page_safely():
    docs = [
        Document(
            page_content="Future job-market shifts affect developer learning choices.",
            metadata={
                "source": "future_jobs.pdf",
                "source_type": "pdf",
                "filename": "future_jobs.pdf",
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)

    assert format_evidence_label(evidence["items"][0]) == "Future Jobs"


def test_low_quality_pdf_fragment_is_not_forced_into_evidence():
    docs = [
        Document(
            page_content="Markdown evidence about RAG evaluation and source grounding.",
            metadata={
                "source": "rag.md",
                "filename": "rag.md",
                "source_type": "markdown",
            },
        ),
        Document(
            page_content="laced by the current generation of GenAI Future of Jobs Report 2025 43",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "page": 43,
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert [item["source_type"] for item in selected] == ["markdown"]


def test_usable_pdf_candidate_is_selected_first_over_markdown():
    docs = [
        Document(
            page_content="Markdown evidence about RAG evaluation and source grounding.",
            metadata={
                "source": "rag.md",
                "filename": "rag.md",
                "source_type": "markdown",
            },
        ),
        Document(
            page_content=(
                "Future job-market evidence shows analytical thinking and AI skills "
                "remain important for career transitions."
            ),
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 12,
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert selected[0]["source_type"] == "pdf"
    assert selected[0]["page"] == 12
    assert selected[1]["source_type"] == "markdown"


def test_later_usable_pdf_candidate_is_selected_after_bad_pdf_candidate():
    docs = [
        Document(
            page_content="Markdown evidence about RAG evaluation and source grounding.",
            metadata={
                "source": "rag.md",
                "filename": "rag.md",
                "source_type": "markdown",
            },
        ),
        Document(
            page_content="laced by the current generation of GenAI Future of Jobs Report 2025 43",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 43,
            },
        ),
        Document(
            page_content=(
                "Employers expect analytical thinking, AI literacy, and resilient "
                "technical skills in future job-market transitions."
            ),
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 44,
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert selected[0]["source_type"] == "pdf"
    assert selected[0]["page"] == 44
    assert selected[1]["source_type"] == "markdown"


def test_project_documentation_is_excluded_from_evidence():
    docs = [
        Document(
            page_content="Project documentation describing which sources should be used.",
            metadata={
                "source": "public_sources_notes.md",
                "filename": "public_sources_notes.md",
                "source_type": "markdown",
                "document_role": "project_documentation",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content="Internal note about RAG evaluation and AI Engineering practice.",
            metadata={
                "source": "ai_job_market_skills.md",
                "filename": "ai_job_market_skills.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert len(selected) == 1
    assert selected[0]["source"] == "ai_job_market_skills.md"


def test_derived_official_summary_ranks_above_internal_note():
    docs = [
        Document(
            page_content="Internal note about AI agents and project learning priorities.",
            metadata={
                "source": "ai_job_market_skills.md",
                "filename": "ai_job_market_skills.md",
                "source_type": "markdown",
                "document_role": "internal_note",
                "source_authority": "internal",
            },
        ),
        Document(
            page_content="OECD evidence about AI skills, training, and reliable AI use.",
            metadata={
                "source": "oecd_ai_and_skills.md",
                "filename": "oecd_ai_and_skills.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert selected[0]["source"] == "oecd_ai_and_skills.md"
    assert selected[0]["type_label"] == "Derived official summary"
    assert selected[1]["source"] == "ai_job_market_skills.md"


def test_markdown_evidence_excerpt_removes_metadata_block():
    docs = [
        Document(
            page_content=(
                "# OECD AI Skills Gap 2025\n\n"
                "title: OECD AI Skills Gap 2025\n"
                "publisher: OECD\n"
                "document_role: derived_summary\n\n"
                "## Key Findings\n\n"
                "AI skills evidence should connect training to reliable use."
            ),
            metadata={
                "source": "oecd_ai_skills_gap_2025.md",
                "filename": "oecd_ai_skills_gap_2025.md",
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
            },
        )
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert selected[0]["excerpt"].startswith("Key Findings")
    assert "publisher:" not in selected[0]["excerpt"]
    assert "#" not in selected[0]["excerpt"]


def test_pdf_evidence_excerpt_trims_leading_fragment_when_possible():
    docs = [
        Document(
            page_content=(
                "generation, storage and distribution are also expected to be "
                "transformative. These trends are expected to fuel demand for "
                "technology-related skills, including AI and big data."
            ),
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "document_role": "primary_source",
                "source_authority": "official",
                "page": 5,
            },
        )
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert selected[0]["source_type"] == "pdf"
    assert selected[0]["excerpt"].startswith("These trends")
    assert not selected[0]["excerpt"].startswith("generation")


def test_diverse_evidence_selection_avoids_duplicate_sources_when_possible():
    docs = [
        Document(
            page_content=f"Markdown duplicate chunk {index}",
            metadata={
                "source": "same.md",
                "filename": "same.md",
                "source_type": "markdown",
                "chunk_index": index,
            },
        )
        for index in range(3)
    ]
    docs.append(
        Document(
            page_content="Different source with relevant AI skill evidence.",
            metadata={
                "source": "different.md",
                "filename": "different.md",
                "source_type": "markdown",
                "chunk_index": 0,
            },
        )
    )

    selected = select_diverse_evidence(docs, max_items=3)
    selected_sources = [item["source"] for item in selected]

    assert selected_sources.count("same.md") == 1
    assert "different.md" in selected_sources


def test_relevant_pdf_candidate_can_be_included_with_markdown_results():
    docs = [
        Document(
            page_content="Markdown evidence about AI engineering skills.",
            metadata={
                "source": "skills.md",
                "filename": "skills.md",
                "source_type": "markdown",
            },
        ),
        Document(
            page_content="Another markdown source about developer learning.",
            metadata={
                "source": "learning.md",
                "filename": "learning.md",
                "source_type": "markdown",
            },
        ),
        Document(
            page_content="PDF evidence about future job-market skill demand.",
            metadata={
                "source": "future_jobs.pdf",
                "filename": "future_jobs.pdf",
                "source_type": "pdf",
                "page": 12,
            },
        ),
        Document(
            page_content="Third markdown source that should be replaceable.",
            metadata={
                "source": "third.md",
                "filename": "third.md",
                "source_type": "markdown",
            },
        ),
    ]

    selected = select_diverse_evidence(docs, max_items=3)

    assert any(item["source_type"] == "pdf" for item in selected)


def test_internal_qdrant_metadata_is_not_exposed_in_evidence_items():
    docs = [
        Document(
            page_content="Evidence about RAG evaluation.",
            metadata={
                "source": "rag.md",
                "filename": "rag.md",
                "source_type": "markdown",
                "_id": "internal-id",
                "_collection_name": "internal-collection",
            },
        )
    ]

    evidence = summarize_retrieved_evidence(docs)
    metadata = evidence["items"][0]["metadata"]

    assert "_id" not in metadata
    assert "_collection_name" not in metadata
