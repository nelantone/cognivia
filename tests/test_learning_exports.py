"""Characterization tests for the app-level learning export contracts."""

import ast
from copy import deepcopy
from pathlib import Path

import pytest

import app as cognivia_app
from tools import learning_exports


def _schema(nodes=None):
    return {
        "id": "project_first",
        "title": "Project-first path",
        "subtitle": "Learn by shipping",
        "current_state": "Evidence-aware beginner",
        "target_outcome": "Explain and measure RAG quality",
        "fit_reason": "Best when practical feedback matters",
        "nodes": list(
            nodes
            if nodes is not None
            else [
                "Inspect evidence",
                "Build evaluator",
                "Run failure analysis",
                "Explain trade-offs",
            ]
        ),
        "first_action": "Create one evaluation case",
        "checkpoint": "Explain one retrieval failure",
        "risk_or_gap": "May optimize metrics without diagnosis",
    }


def _decision():
    return {
        "selected_focus": "RAG evaluation",
        "recommendation": "Prioritize evaluation before orchestration.",
        "next_action": "Measure one grounded answer.",
        "decision_trace": [
            "Short evidence-based reasoning: The evidence favors evaluation "
            "because it exposes retrieval failures."
        ],
        "possible_ai_career_paths": ["AI Engineer", "ML Platform Engineer"],
        "skill_gap": ["Evaluation design", "Failure analysis"],
        "learner_profile": {"time_available_minutes": 45},
    }


def _note():
    return {
        "title": "Evaluation reflection",
        "reflection": "I will test one failure mode before expanding scope.",
        "tags": ["rag", "evaluation"],
    }


EXPECTED_FULL_PLAN = """# Cognivia Learning Plan

## 1. Learning goal
Build a reliable RAG evaluator.

## 2. Recommendation summary
- Recommended direction: RAG evaluation
- Short reason: The evidence favors evaluation because it exposes retrieval failures.
- Next action: Measure one grounded answer.

## 3. Why this path
Prioritize evaluation before orchestration.

Possible career directions:
- AI Engineer
- ML Platform Engineer

Skill gaps to practice:
- Evaluation design
- Failure analysis

## 4. Selected learning path
- Path title: Project-first path
- Path summary: Learn by shipping
- Why this path helps: Best when practical feedback matters
- First action: Create one evaluation case
- Practice step: Run failure analysis
- Checkpoint: Explain one retrieval failure
- Expected outcome: Explain and measure RAG quality
- Original path steps:
  1. Inspect evidence
  2. Build evaluator
  3. Run failure analysis
  4. Explain trade-offs

## 5. Learning path map
Start → First action → Practice → Checkpoint → Outcome

- Start: Inspect evidence
- First action: Create one evaluation case
- Practice: Run failure analysis
- Checkpoint: Explain one retrieval failure
- Outcome: Explain and measure RAG quality

## 6. Study method

### 20-hour focused learning plan
Use 10 focused blocks of 2 hours. Each block should target one high-leverage concept and end with a 15-minute review.

### 80/20 concept focus
Prioritize the small set of concepts that unlock the largest practical progress.

### One-page study sheet
Create one page with:
- key concepts
- vocabulary
- common mistakes
- practical checklist
- what you must be able to explain or build

### Five-level learning ladder
1. Recognize the concept.
2. Explain it simply.
3. Apply it in a small task.
4. Debug or evaluate it.
5. Teach it or build something with it.

### Mastery quiz
Use 5-10 questions with increasing difficulty. After each answer, write the correction and explanation.

### Feynman loop
Explain the topic in plain language, find the weak point, review it, and explain again.

Optional reference: [Feynman Technique](https://fs.blog/feynman-technique/)

### Curated resources
Use this as a resource strategy rather than live web recommendations:
- official documentation
- one practical tutorial
- one expert explanation
- one small project
- one reference to revisit later

### Session reflection
End each study session by writing:
- what worked
- what was confusing
- what distracted you
- what to improve next session

## 7. Today’s first study session
- Time available today: 45 minutes
- Focus objective: Explain and measure RAG quality
- Action: Create one evaluation case
- Checkpoint: Explain one retrieval failure
- Reflection prompt: What did you learn, where did you get stuck, and what will you try next?

## 8. Reflection
### Evaluation reflection

I will test one failure mode before expanding scope.

Tags:
- rag
- evaluation
"""


def test_full_plan_markdown_is_byte_stable_and_does_not_mutate_inputs():
    decision = _decision()
    schema = _schema()
    note = _note()
    original_decision = deepcopy(decision)
    original_schema = deepcopy(schema)
    original_note = deepcopy(note)
    original_nodes = list(schema["nodes"])

    markdown = learning_exports.build_full_learning_plan_document(
        goal="Build a reliable RAG evaluator.",
        decision=decision,
        selected_schema=schema,
        note=note,
        evidence_reason=(
            "The evidence favors evaluation because it exposes retrieval failures."
        ),
    )

    assert markdown == EXPECTED_FULL_PLAN
    assert markdown.endswith("\n")
    assert markdown.count(note["reflection"]) == 1
    assert decision == original_decision
    assert schema == original_schema
    assert note == original_note
    assert schema["nodes"] == original_nodes


def test_full_plan_missing_fields_and_absent_note_keep_current_fallbacks():
    schema = _schema(nodes=[])
    decision = {}
    original_schema = deepcopy(schema)
    original_decision = deepcopy(decision)

    markdown = cognivia_app.build_full_learning_plan_markdown(
        goal="",
        decision=decision,
        selected_schema=schema,
        note=None,
    )

    assert "## 1. Learning goal\nNo learning goal was provided.\n" in markdown
    assert "- Recommended direction: Next learning direction" in markdown
    assert (
        "- Short reason: Cognivia used the available learning context to size "
        "the next step."
    ) in markdown
    assert "- Next action: Create one evaluation case" in markdown
    assert "- Start: Evidence-aware beginner" in markdown
    assert "- Practice: Practice" in markdown
    assert "### Evaluation reflection" not in markdown
    assert "Use these prompts after your first study block:" in markdown
    assert markdown.endswith("\n")
    assert schema == original_schema
    assert decision == original_decision


def test_full_plan_uses_recommendation_when_trace_reason_is_absent():
    decision = _decision()
    decision["decision_trace"] = []
    original_decision = deepcopy(decision)

    markdown = cognivia_app.build_full_learning_plan_markdown(
        goal="Build a reliable RAG evaluator.",
        decision=decision,
        selected_schema=_schema(),
        note=None,
    )

    assert (
        "- Short reason: Prioritize evaluation before orchestration."
        in markdown
    )
    assert decision == original_decision


@pytest.mark.parametrize(
    ("nodes", "expected_start", "expected_practice"),
    [
        ([], "Evidence-aware beginner", "Practice"),
        (["Only step"], "Only step", "Practice"),
        (["First", "Second"], "First", "Practice"),
        (
            ["First", "Second", "Third", "Fourth"],
            "First",
            "Third",
        ),
    ],
)
def test_learning_path_map_steps_freeze_node_count_behavior(
    nodes,
    expected_start,
    expected_practice,
):
    schema = _schema(nodes=nodes)
    original_schema = deepcopy(schema)
    original_nodes = list(schema["nodes"])

    steps = learning_exports._learning_path_map_steps(schema)

    assert steps == [
        ("Start", expected_start),
        ("First action", "Create one evaluation case"),
        ("Practice", expected_practice),
        ("Checkpoint", "Explain one retrieval failure"),
        ("Outcome", "Explain and measure RAG quality"),
    ]
    assert schema == original_schema
    assert schema["nodes"] == original_nodes


def test_full_plan_preserves_long_canonical_values_without_truncation():
    schema = _schema()
    schema.update(
        {
            "first_action": "First action " + "implementation detail " * 20,
            "checkpoint": "Checkpoint " + "verification detail " * 20,
            "target_outcome": "Outcome " + "observable result " * 20,
            "nodes": [
                "Start",
                "Practice",
                "Advanced canonical node " + "retained detail " * 20,
            ],
        }
    )
    original_schema = deepcopy(schema)

    markdown = cognivia_app.build_full_learning_plan_markdown(
        goal="Preserve canonical values",
        decision=_decision(),
        selected_schema=schema,
        note=None,
    )

    assert schema["first_action"] in markdown
    assert schema["checkpoint"] in markdown
    assert schema["target_outcome"] in markdown
    assert schema["nodes"][-1] in markdown
    assert "…" not in markdown
    assert schema == original_schema


@pytest.mark.parametrize(
    ("value", "fallback", "expected"),
    [
        ("  RAG   evaluation\nquality  ", "fallback", "RAG evaluation quality"),
        ("", "fallback", "fallback"),
        (None, "fallback", "fallback"),
    ],
)
def test_markdown_text_freezes_normalization_and_fallback(value, fallback, expected):
    assert learning_exports._markdown_text(value, fallback) == expected


def test_markdown_list_normalizes_items_without_mutating_input():
    items = ["  RAG  ", "", None, "retrieval\n quality"]
    original_items = list(items)

    result = learning_exports._markdown_list(items)

    assert result == ["RAG", "retrieval quality"]
    assert items == original_items


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        ({"learner_profile": {"time_available_minutes": 45}}, "45 minutes"),
        ({"learner_profile": {"time_available_minutes": 45.9}}, "45 minutes"),
        ({"learner_profile": {"time_available_minutes": 0}}, None),
        ({"learner_profile": {"time_available_minutes": "45"}}, None),
        ({}, None),
        (None, None),
    ],
)
def test_time_available_today_freezes_supported_and_fallback_values(
    decision,
    expected,
):
    fallback = "Not specified. Use one focused 2-hour block if available."
    assert learning_exports._time_available_today(decision) == (expected or fallback)


def test_populated_reflection_markdown_is_byte_stable_and_non_mutating():
    payload = {
        "exported_at": "2026-09-02T08:30:00+00:00",
        "goal": "Build a reliable RAG evaluator",
        "selected_path": {
            "id": "project_first",
            "title": "Project-first path",
        },
        "note": {
            "title": "Evaluation reflection",
            "reflection": "Test one failure mode first.",
            "tags": ["rag"],
        },
        "first_action": "Create one evaluation case",
        "checkpoint": "Explain one retrieval failure",
    }
    original_payload = deepcopy(payload)

    markdown = learning_exports.build_learning_reflection_markdown(payload)

    assert markdown == """# Cognivia reflection

- Exported: 2026-09-02T08:30:00+00:00
- Goal: Build a reliable RAG evaluator
- Path: Project-first path (project_first)

## Evaluation reflection

Test one failure mode first.

## First action

Create one evaluation case

## Checkpoint

Explain one retrieval failure"""
    assert not markdown.endswith("\n")
    assert payload == original_payload


def test_empty_reflection_markdown_freezes_current_output():
    payload = {
        "exported_at": "",
        "goal": "",
        "selected_path": {},
        "note": {},
    }
    original_payload = deepcopy(payload)

    markdown = learning_exports.build_learning_reflection_markdown(payload)

    assert markdown == "\n".join(
        [
            "# Cognivia reflection",
            "",
            "- Exported: ",
            "- Goal: ",
            "- Path:  ()",
            "",
            "## Reflection",
            "",
            "",
            "",
            "## First action",
            "",
            "",
            "",
            "## Checkpoint",
            "",
            "",
        ]
    )
    assert learning_exports.build_learning_reflection_markdown(
        {**payload, "selected_path": []}
    ) == ""
    assert payload == original_payload


def test_existing_app_level_builder_names_remain_callable():
    assert callable(cognivia_app.build_full_learning_plan_markdown)
    assert callable(cognivia_app.build_learning_reflection_markdown)
    assert cognivia_app.build_full_learning_plan_markdown(
        goal="Build a reliable RAG evaluator.",
        decision=_decision(),
        selected_schema=_schema(),
        note=_note(),
    ) == EXPECTED_FULL_PLAN
    assert (
        cognivia_app.build_learning_reflection_markdown
        is learning_exports.build_learning_reflection_markdown
    )

    module_tree = ast.parse(Path(learning_exports.__file__).read_text())
    imported_modules = {
        node.module
        for node in ast.walk(module_tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(module_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert imported_modules == {"__future__", "tools.learning_direction"}
