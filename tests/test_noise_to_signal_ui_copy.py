"""Tests for Noise-to-Signal Streamlit copy helpers."""

import ast
from pathlib import Path


HELPER_NAMES = {
    "NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK_MESSAGES",
    "DEFAULT_NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK",
    "INSUFFICIENT_EVIDENCE_HEADING",
    "GUIDED_INTAKE_NO_EVIDENCE_HEADING",
    "GUIDED_INTAKE_NO_EVIDENCE_MESSAGE",
    "LOCAL_EVIDENCE_STORE_BUSY_MESSAGE",
    "NOISE_TO_SIGNAL_PROGRESS_MESSAGES",
    "EVIDENCE_LABELS",
    "_is_local_evidence_store_lock_error",
    "_noise_to_signal_progress_messages",
    "_noise_to_signal_study_plan_fallback_message",
    "_should_display_noise_to_signal_evidence",
    "_noise_to_signal_evidence_heading",
}


def _load_app_copy_helpers():
    app_source = Path("app.py").read_text(encoding="utf-8")
    app_module = ast.parse(app_source)
    helper_nodes = []

    for node in app_module.body:
        if isinstance(node, ast.Assign):
            target_names = {
                target.id for target in node.targets if isinstance(target, ast.Name)
            }
            if target_names & HELPER_NAMES:
                helper_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in HELPER_NAMES:
            helper_nodes.append(node)

    helper_module = ast.Module(body=helper_nodes, type_ignores=[])
    ast.fix_missing_locations(helper_module)
    namespace = {}
    exec(compile(helper_module, filename="app.py", mode="exec"), namespace)
    return namespace


def test_noise_to_signal_study_plan_copy_is_status_specific():
    helpers = _load_app_copy_helpers()
    message_for = helpers["_noise_to_signal_study_plan_fallback_message"]

    assert message_for("needs_clarification") == (
        "No study plan was generated because more context is needed."
    )
    assert message_for("informational") == (
        "No study plan was generated because this was an informational question."
    )
    assert message_for("insufficient_evidence") == (
        "No study plan was generated because the retrieved evidence does not "
        "directly support the question."
    )


def test_comparison_study_plan_copy_remains_unchanged_for_other_statuses():
    helpers = _load_app_copy_helpers()
    message_for = helpers["_noise_to_signal_study_plan_fallback_message"]

    assert message_for("tie") == (
        "No option-specific study plan was generated because the decision needs "
        "stronger evidence or clearer focus."
    )


def test_noise_to_signal_evidence_display_is_status_specific():
    helpers = _load_app_copy_helpers()
    should_display = helpers["_should_display_noise_to_signal_evidence"]
    heading_for = helpers["_noise_to_signal_evidence_heading"]

    assert should_display("needs_clarification") is False
    assert should_display("insufficient_evidence") is True
    assert should_display("informational") is True
    assert heading_for("insufficient_evidence") == (
        "Retrieved candidates — not sufficient to support the answer"
    )
    assert heading_for("informational") == "Retrieved evidence"


def test_noise_to_signal_contextual_evidence_label_is_not_sufficient():
    helpers = _load_app_copy_helpers()
    evidence_labels = helpers["EVIDENCE_LABELS"]

    assert evidence_labels["contextual"] == "Contextual"
    assert evidence_labels["contextual"] != "Sufficient"
    assert evidence_labels["failed"] == "Unavailable"


def test_guided_intake_no_evidence_copy_is_concise_status_message():
    helpers = _load_app_copy_helpers()

    assert helpers["GUIDED_INTAKE_NO_EVIDENCE_HEADING"] == "Evidence status"
    assert helpers["GUIDED_INTAKE_NO_EVIDENCE_MESSAGE"] == (
        "No knowledge-base evidence was attached to this guided recommendation.\n\n"
        "Treat this as a profile-based draft, not evidence-backed guidance."
    )


def test_local_evidence_store_lock_copy_and_detection_are_concise():
    helpers = _load_app_copy_helpers()
    is_lock_error = helpers["_is_local_evidence_store_lock_error"]

    assert helpers["LOCAL_EVIDENCE_STORE_BUSY_MESSAGE"] == (
        "The local evidence store is busy or unavailable. Try again after the "
        "current retrieval finishes."
    )
    assert is_lock_error(
        RuntimeError(
            "Storage folder data/vector_store/qdrant is already accessed by "
            "another instance of Qdrant client."
        )
    )
    assert not is_lock_error(RuntimeError("temporary network timeout"))


def test_noise_to_signal_progress_copy_explains_long_running_retrieval():
    helpers = _load_app_copy_helpers()
    messages = helpers["_noise_to_signal_progress_messages"]()

    assert messages == (
        "Searching local evidence. First run can take longer...",
        "Assessing whether the evidence directly supports this request...",
        "Preparing recommendation...",
    )
