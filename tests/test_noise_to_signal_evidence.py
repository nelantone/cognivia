"""Characterization tests for graph-level evidence interpretation contracts."""

from copy import deepcopy

import pytest
from langchain_core.documents import Document

from tools import noise_to_signal_graph as graph


INFORMATIONAL_GOAL = "Why is RAG evaluation useful for AI engineers?"


def _reasoning_item(**overrides):
    item = {
        "source": "rag-evaluation.md",
        "excerpt": "RAG evaluation overview.",
    }
    item.update(overrides)
    return item


def _single_focus_state(focus, reasoning_items):
    return {
        "goal": focus,
        "selected_focus": focus,
        "decision_status": "single_focus",
        "options": [],
        "reasoning_evidence": {
            "has_evidence": bool(reasoning_items),
            "items": reasoning_items,
        },
        "retrieved_docs": [],
        "retrieval_attempts": 1,
        "retrieval_override": True,
        "retrieval_trace": [],
    }


def test_informational_answer_preserves_exact_claim_order_and_input_values():
    reasoning_items = [
        _reasoning_item(
            full_text=(
                "RAG evaluation is useful because it checks retrieval relevance. "
                "RAG evaluation helps teams detect unsupported answers. "
                "RAG evaluation enables targeted analysis of retrieval failures."
            )
        )
    ]
    original_items = deepcopy(reasoning_items)

    answer = graph.build_informational_answer(INFORMATIONAL_GOAL, reasoning_items)

    assert answer == (
        "RAG evaluation is useful because it checks retrieval relevance. "
        "RAG evaluation helps teams detect unsupported answers. "
        "RAG evaluation enables targeted analysis of retrieval failures."
    )
    assert reasoning_items == original_items


@pytest.mark.parametrize(
    ("max_claims", "expected"),
    [
        (0, ""),
        (1, "LangGraph is a framework for stateful workflows."),
        (
            2,
            "LangGraph is a framework for stateful workflows. "
            "LangGraph supports durable execution across workflow steps.",
        ),
    ],
)
def test_informational_answer_stops_at_the_configured_maximum_claim_count(
    max_claims,
    expected,
):
    reasoning_items = [
        {
            "full_text": (
                "LangGraph is a framework for stateful workflows. "
                "LangGraph supports durable execution across workflow steps. "
                "LangGraph enables explicit routing between workflow nodes."
            )
        }
    ]

    answer = graph.build_informational_answer(
        "Explain LangGraph",
        reasoning_items,
        max_claims=max_claims,
    )

    assert answer == expected


def test_informational_answer_removes_duplicate_claims_across_evidence_items():
    repeated_claim = (
        "RAG evaluation is useful because it checks retrieval relevance and "
        "answer quality."
    )
    reasoning_items = [
        _reasoning_item(full_text=repeated_claim),
        _reasoning_item(source="duplicate.md", full_text=repeated_claim),
        _reasoning_item(
            source="grounding.md",
            full_text="RAG evaluation helps teams measure source grounding.",
        ),
    ]

    answer = graph.build_informational_answer(INFORMATIONAL_GOAL, reasoning_items)

    assert answer == (
        f"{repeated_claim} RAG evaluation helps teams measure source grounding."
    )
    assert answer.count(repeated_claim) == 1


def test_informational_answer_rejects_atx_and_setext_markdown_headings():
    reasoning_items = [
        {
            "full_text": (
                "# LangGraph is a framework that provides durable workflows.\n\n"
                "LangGraph supports orchestration across workflow nodes.\n"
                "=========================================================\n\n"
                "LangGraph is a framework for building stateful workflows."
            )
        }
    ]

    answer = graph.build_informational_answer("Explain LangGraph", reasoning_items)

    assert answer == "LangGraph is a framework for building stateful workflows."


@pytest.mark.parametrize("identity_field", ["id", "_id", "point_id"])
def test_reasoning_full_text_matches_each_supported_source_identity(identity_field):
    doc = Document(
        page_content="RAG evaluation helps teams measure grounded answer quality.",
        metadata={identity_field: "evidence-point-7"},
    )
    state = {
        "retrieved_docs": [doc],
        "reasoning_evidence": {
            "items": [{identity_field: "evidence-point-7", "excerpt": "Summary."}]
        },
    }
    original_items = deepcopy(state["reasoning_evidence"]["items"])

    enriched = graph._reasoning_items_with_full_text(state)

    assert enriched == [
        {
            identity_field: "evidence-point-7",
            "excerpt": "Summary.",
            "full_text": doc.page_content,
        }
    ]
    assert state["reasoning_evidence"]["items"] == original_items


def test_reasoning_full_text_fails_closed_when_identity_is_missing():
    state = {
        "retrieved_docs": [
            Document(
                page_content="This text must not be matched by list position.",
                metadata={},
            )
        ],
        "reasoning_evidence": {"items": [{"excerpt": "Summary."}]},
    }

    enriched = graph._reasoning_items_with_full_text(state)

    assert enriched == [{"excerpt": "Summary."}]


def test_reasoning_full_text_fails_closed_when_identity_matches_multiple_documents():
    state = {
        "retrieved_docs": [
            Document(page_content="First document.", metadata={"id": "shared-id"}),
            Document(page_content="Second document.", metadata={"_id": "shared-id"}),
        ],
        "reasoning_evidence": {
            "items": [{"point_id": "shared-id", "excerpt": "Summary."}]
        },
    }

    enriched = graph._reasoning_items_with_full_text(state)

    assert enriched == [{"point_id": "shared-id", "excerpt": "Summary."}]


def test_state_answer_uses_matched_full_text_without_mutating_reasoning_state():
    direct_claim = "LangGraph is a framework for stateful multi-step workflows."
    state = {
        "retrieved_docs": [
            Document(
                page_content=("Background context. " * 25) + direct_claim,
                metadata={"point_id": "langgraph-4"},
            )
        ],
        "reasoning_evidence": {
            "items": [
                {
                    "id": "langgraph-4",
                    "excerpt": "LangGraph overview without a direct claim.",
                }
            ]
        },
    }
    original_state = deepcopy(state)

    answer = graph.build_informational_answer_from_state(
        state,
        "Explain LangGraph",
    )

    assert answer == direct_claim
    assert state == original_state
    assert "full_text" not in state["reasoning_evidence"]["items"][0]


@pytest.mark.parametrize(
    ("focus", "reasoning_items", "expected_quality", "expected_status"),
    [
        ("LangGraph", [], "weak", None),
        (
            "Sourdough fermentation",
            [
                _reasoning_item(
                    excerpt=(
                        "Sourdough fermentation supports predictable bread-making "
                        "practice."
                    )
                )
            ],
            "contextual",
            None,
        ),
        (
            "Sourdough fermentation",
            [_reasoning_item(excerpt="Unrelated learning context.")],
            "weak",
            "insufficient_evidence",
        ),
    ],
)
def test_single_focus_assessment_accepts_domain_or_direct_support_and_rejects_neither(
    focus,
    reasoning_items,
    expected_quality,
    expected_status,
):
    state = _single_focus_state(focus, reasoning_items)
    original_state = deepcopy(state)

    assessment = graph.assess_evidence(state)

    assert assessment["evidence_quality"] == expected_quality
    assert assessment.get("decision_status") == expected_status
    assert state == original_state
    if expected_status == "insufficient_evidence":
        assert assessment["selected_focus"] is None
        assert assessment["evidence_reason"] == (
            "The focus appears outside the AI Engineering learning scope, and "
            "retrieved evidence does not directly support the topic."
        )


def test_graph_level_evidence_interpretation_names_remain_importable():
    compatibility_names = (
        "build_informational_answer",
        "build_informational_answer_from_state",
        "assess_evidence",
        "_reasoning_items_with_full_text",
        "_single_focus_has_domain_or_direct_support",
    )

    assert all(callable(getattr(graph, name, None)) for name in compatibility_names)


def test_state_answer_preserves_graph_level_builder_monkeypatch_seam(monkeypatch):
    calls = []

    def fake_builder(goal, reasoning_items, max_claims=3):
        calls.append((goal, reasoning_items, max_claims))
        return "Patched evidence answer."

    monkeypatch.setattr(graph, "build_informational_answer", fake_builder)
    state = {
        "retrieved_docs": [],
        "reasoning_evidence": {"items": [{"excerpt": "Evidence summary."}]},
    }

    answer = graph.build_informational_answer_from_state(state, "Explain LangGraph")

    assert answer == "Patched evidence answer."
    assert calls == [
        ("Explain LangGraph", [{"excerpt": "Evidence summary."}], 3)
    ]


def test_evidence_assessment_preserves_graph_level_state_builder_monkeypatch_seam(
    monkeypatch,
):
    calls = []

    def fake_state_builder(state, goal):
        calls.append((state, goal))
        return "LangGraph is a stateful workflow framework."

    monkeypatch.setattr(
        graph,
        "build_informational_answer_from_state",
        fake_state_builder,
    )
    state = {
        "goal": "Explain LangGraph",
        "decision_status": "informational",
        "reasoning_evidence": {"has_evidence": True, "items": []},
        "retrieval_attempts": 1,
        "retrieval_override": True,
        "retrieval_trace": [],
    }

    assessment = graph.assess_evidence(state)

    assert calls == [(state, "Explain LangGraph")]
    assert assessment == {
        "informational_answer": "LangGraph is a stateful workflow framework.",
        "evidence_quality": "sufficient",
        "evidence_reason": "Retrieved evidence contains a direct answer claim.",
        "retrieval_trace": [],
    }
