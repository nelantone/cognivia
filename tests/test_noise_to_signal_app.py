"""Streamlit AppTest coverage for the Noise-to-Signal UI."""

import ast
import base64
import re
import sys
import tomllib
from html import unescape
from inspect import getsource
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import openrouter_client
import pytest
import streamlit as st
from PIL import Image
from streamlit.testing.v1 import AppTest

from tools.learning_direction import generate_learning_direction_schemas
from tools.runtime_status import build_runtime_status_lines

APP_TEST_TIMEOUT_SECONDS = 30


@pytest.fixture(autouse=True)
def _reset_streamlit_main_form_context():
    st._main._form_data = None
    yield
    st._main._form_data = None


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear_channels = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return (
        0.2126 * linear_channels[0]
        + 0.7152 * linear_channels[1]
        + 0.0722 * linear_channels[2]
    )


def _contrast_ratio(first_color: str, second_color: str) -> float:
    first_luminance = _relative_luminance(first_color)
    second_luminance = _relative_luminance(second_color)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


class RecordingMemoryStore:
    def __init__(
        self,
        fail=False,
        fail_reads=False,
        recent_events=None,
        latest_profile=None,
    ):
        self.fail = fail
        self.fail_reads = fail_reads
        self.recent_events = list(recent_events or [])
        self.latest_profile = latest_profile
        self.saved_profiles = []
        self.saved_events = []

    def save_learner_profile(self, learner_id, profile, raw_form=None):
        if self.fail:
            raise RuntimeError("memory unavailable")
        self.saved_profiles.append(
            {
                "learner_id": learner_id,
                "profile": profile,
                "raw_form": raw_form,
            }
        )
        return f"profile-{len(self.saved_profiles)}"

    def get_latest_learner_profile(self, learner_id):
        if self.fail_reads:
            raise RuntimeError("memory unavailable")
        return self.latest_profile

    def save_learning_event(self, **event):
        if self.fail:
            raise RuntimeError("memory unavailable")
        self.saved_events.append(event)
        return f"event-{len(self.saved_events)}"

    def get_recent_learning_events(self, learner_id, limit=10):
        if self.fail_reads:
            raise RuntimeError("memory unavailable")
        learner_events = [
            event
            for event in [*reversed(self.saved_events), *self.recent_events]
            if event.get("learner_id") in {None, learner_id}
        ]
        return learner_events[:limit]

    def search_memory(self, learner_id, query, limit=5):
        return []


def _run_noise_to_signal_app(
    mock_result,
    user_input,
    after_decision=None,
    retriever=None,
    memory_store=None,
):
    app, _ = _run_noise_to_signal_app_sequence(
        [(user_input, mock_result, after_decision)],
        retriever=retriever,
        memory_store=memory_store,
    )
    return app


def _run_noise_to_signal_app_sequence(
    steps,
    retriever=None,
    memory_store=None,
    initial_results=None,
    initial_session_state=None,
    intro_complete=True,
    examples_open=False,
    submit_with_current_input=False,
):
    results = (
        list(initial_results)
        if initial_results is not None
        else [result for _, result, _ in steps]
    )
    calls = []

    def run_noise_to_signal_stub(*args, **kwargs):
        calls.append((args, kwargs))
        result = results[0] if len(results) == 1 else results.pop(0)
        if isinstance(result, Exception):
            raise result
        if callable(result):
            return result(*args, **kwargs)
        return result

    graph_stub = ModuleType("tools.noise_to_signal_graph")
    graph_stub.run_noise_to_signal = run_noise_to_signal_stub
    graph_stub.calls = calls
    evaluation_stub = ModuleType("rag.evaluation")
    evaluation_stub.EVALUATION_CASES = []
    evaluation_stub.run_evaluation_set = lambda *args, **kwargs: []
    generator_stub = ModuleType("rag.generator")
    generator_stub.answer_with_rag = lambda *args, **kwargs: {"answer": "", "sources": []}
    retriever_stub = ModuleType("rag.retriever")
    retriever_stub.retrieve_relevant_chunks = retriever or (lambda *args, **kwargs: [])

    with patch.dict(
        sys.modules,
        {
            "rag.evaluation": evaluation_stub,
            "rag.generator": generator_stub,
            "rag.retriever": retriever_stub,
            "tools.noise_to_signal_graph": graph_stub,
        },
    ):
        app = AppTest.from_file("app.py")
        if memory_store is not None:
            app.session_state["cognivia_memory_store"] = memory_store
        for key, value in (initial_session_state or {}).items():
            app.session_state[key] = value
        if intro_complete:
            app.session_state["noise_to_signal_intro_state"] = "complete"
        app.session_state["noise_to_signal_examples_open"] = examples_open
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.radio[0].set_value("Noise-to-Signal Agent").run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        for user_input, _, after_decision in steps:
            goal_input = app.text_input(key="noise_to_signal_goal")
            goal_input.set_value(user_input)
            if not submit_with_current_input:
                app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
            app.button(key="generate_noise_to_signal_decision").click().run(
                timeout=APP_TEST_TIMEOUT_SECONDS
            )
            if after_decision:
                after_decision(app)
        return app, graph_stub


def test_noise_to_signal_first_submission_captures_current_input_in_single_event():
    goal = "Kubernetes for AI Engineer?"
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [(goal, _single_focus_result(goal), None)],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert not app.exception
    assert graph_stub.calls == [
        (
            (goal,),
            {"thread_id": app.session_state["noise_to_signal_thread_id"]},
        )
    ]
    assert app.session_state["noise_to_signal_last_goal"] == goal
    assert "Please enter a learning goal or decision." not in "\n".join(
        str(item.value) for item in app.error
    )


def test_noise_to_signal_replacement_submits_current_query_once():
    query_a = "Should I learn LangGraph or RAG evaluation?"
    query_b = "Kubernetes for AI Engineer?"
    result_a = _single_focus_result(query_a)
    result_b = _single_focus_result(query_b)

    app, graph_stub = _run_noise_to_signal_app_sequence(
        [
            (query_a, result_a, None),
            (query_b, result_b, None),
        ],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert not app.exception
    assert [call[0][0] for call in graph_stub.calls] == [query_a, query_b]
    assert app.session_state["noise_to_signal_goal"] == query_b
    assert app.session_state["noise_to_signal_last_goal"] == query_b
    assert app.session_state["noise_to_signal_last_decision"] == result_b


def test_noise_to_signal_visible_non_empty_value_never_uses_empty_validation():
    goal = "Kubernetes for AI Engineer?"
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [(goal, _single_focus_result(goal), None)],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert [call[0][0] for call in graph_stub.calls] == [goal]
    assert app.text_input(key="noise_to_signal_goal").value == goal
    assert "Please enter a learning goal or decision." not in "\n".join(
        str(item.value) for item in app.error
    )


def test_noise_to_signal_new_search_submits_first_replacement_immediately():
    query_a = "Should I learn LangGraph or RAG evaluation?"
    query_b = "Kubernetes for AI Engineer?"
    thread_ids = []

    def start_new_search(app):
        thread_ids.append(app.session_state["noise_to_signal_thread_id"])
        app.button(key="noise_to_signal_start_new").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        thread_ids.append(app.session_state["noise_to_signal_thread_id"])

    app, graph_stub = _run_noise_to_signal_app_sequence(
        [
            (query_a, _single_focus_result(query_a), start_new_search),
            (query_b, _single_focus_result(query_b), None),
        ],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert not app.exception
    assert thread_ids[0] != thread_ids[1]
    assert [call[0][0] for call in graph_stub.calls] == [query_a, query_b]
    assert graph_stub.calls[1][1]["thread_id"] == thread_ids[1]
    assert app.session_state["noise_to_signal_last_goal"] == query_b


def test_noise_to_signal_same_query_can_be_submitted_twice():
    goal = "Explain LangGraph"
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [
            (goal, _single_focus_result(goal), None),
            (goal, _single_focus_result(goal), None),
        ],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert not app.exception
    assert [call[0][0] for call in graph_stub.calls] == [goal, goal]
    assert app.session_state["noise_to_signal_last_goal"] == goal


def test_noise_to_signal_whitespace_only_submission_stays_invalid():
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("   ", _single_focus_result("unused"), None)],
        memory_store=RecordingMemoryStore(),
        submit_with_current_input=True,
    )

    assert not app.exception
    assert graph_stub.calls == []
    assert "Please enter a learning goal or decision." in "\n".join(
        str(item.value) for item in app.error
    )
    assert app.session_state["noise_to_signal_last_goal"] == ""
    assert app.session_state["noise_to_signal_last_decision"] is None


def _guided_intake_result(goal, entry_point):
    return {
        "goal": goal,
        "decision_status": "needs_clarification",
        "interaction_mode": "guided_intake",
        "guided_intake_entry_point": entry_point,
        "evidence_quality": "not_required",
        "retrieval_attempts": 0,
        "selected_focus": None,
        "recommendation": "Cognivia needs learner profile context first.",
        "next_action": "Complete the guided intake fields.",
        "decision_trace": [],
        "evidence": {"items": []},
        "study_plan": None,
        "query_reformulated": False,
        "retrieval_trace": ["Retrieval skipped: more context required."],
    }


def _complete_guided_intake(app):
    app.text_area(key="noise_to_signal_guided_current_skills").set_value(
        "Python"
    ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.text_area(key="noise_to_signal_guided_interests").set_value(
        "AI apps"
    ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.text_input(key="noise_to_signal_guided_target_role").set_value(
        "AI engineer"
    ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.button(key="noise_to_signal_generate_guided_path").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )


def _click_guided_intake_submit_if_present(app):
    try:
        submit_button = app.button(key="noise_to_signal_generate_guided_path")
    except KeyError:
        return

    if submit_button:
        app.button(key="noise_to_signal_generate_guided_path").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )


def _page_text(app):
    return "\n".join(
        " ".join(unescape(re.sub(r"<[^>]+>", " ", str(item.value))).split())
        for collection in (
            app.subheader,
            app.markdown,
            app.caption,
            app.info,
            app.success,
            app.warning,
            app.json,
        )
        for item in collection
    )


def _expander_labels(app):
    return "\n".join(item.label for item in app.expander)


def _tab_labels(app):
    return "\n".join(item.label for item in app.tabs)


def _has_learner_memory_download_button(app):
    return "download_learner_memory_json" in str(app.session_state)


def _run_interview_coach_request(model_label: str, max_tokens: int):
    with patch(
        "openrouter_client.call_provider_chat",
        return_value="Mock interview response",
    ) as provider_call:
        app = AppTest.from_file("app.py")
        app.session_state["temperature"] = 1.4
        app.session_state["interview_coach_temperature"] = 0.2
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.radio[0].set_value(
            "Interview Coach"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.selectbox(key="interview_coach_model").set_value(
            model_label
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.slider(key="interview_coach_max_tokens").set_value(
            max_tokens
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        next(
            button
            for button in app.button
            if button.label == "Generate interview prompt"
        ).click().run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert provider_call.call_count == 1
    return app, provider_call.call_args.kwargs


def _capture_openrouter_payload(monkeypatch, request_kwargs):
    captured = {}

    def fake_make_request(payload, headers):
        captured["payload"] = payload
        return SimpleNamespace(
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setattr(openrouter_client, "_make_request", fake_make_request)
    assert (
        openrouter_client.call_openrouter(
            "User prompt",
            "System prompt",
            **request_kwargs,
        )
        == "ok"
    )
    return captured["payload"]


def _capture_openai_payload(monkeypatch, request_kwargs):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["payload"] = json
        return SimpleNamespace(
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
            raise_for_status=lambda: None,
        )

    monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(openrouter_client.requests, "post", fake_post)
    assert (
        openrouter_client.call_provider_chat(
            "User prompt",
            "System prompt",
            **request_kwargs,
        )
        == "ok"
    )
    return captured["payload"]


def test_noise_to_signal_video_intro_appears_on_first_visit():
    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    page_text = _page_text(app)
    button_labels = "\n".join(button.label for button in app.button)
    markdown = "\n".join(str(item.value) for item in app.markdown)

    assert not app.exception
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert 'id="nts-intro-video"' in markdown
    assert "Your AI learning compass" in page_text
    assert "What's your next decision?" in page_text
    assert "First time here? This experience takes less than a minute." not in page_text
    assert "Begin" not in button_labels


def test_noise_to_signal_startup_cover_is_the_first_opaque_app_delta():
    app_source = Path("app.py").read_text(encoding="utf-8")
    page_config_call = 'st.set_page_config(initial_sidebar_state="collapsed")'
    cover_id = 'id="cognivia-startup-intro-cover"'

    assert app_source.index(page_config_call) < app_source.index(cover_id)
    assert app_source.index(cover_id) < app_source.index("load_dotenv()")
    assert app_source.index(cover_id) < app_source.index(
        "app_mode = st.sidebar.radio("
    )
    assert "position: fixed" in app_source
    assert "inset: 0" in app_source
    assert "z-index: 100003" in app_source
    assert "background: #0B132B" in app_source
    assert "opacity: 1" in app_source

    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    markdown = [str(item.value) for item in app.markdown]
    assert not app.exception
    assert cover_id in markdown[0]
    assert "cognivia-full-inverse-clean.png" not in markdown[0]
    assert "data:image/png;base64," in markdown[0]


def test_noise_to_signal_intro_does_not_replay_after_normal_rerun():
    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert 'id="nts-intro-video"' in "\n".join(
        str(item.value) for item in app.markdown
    )

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    markdown = "\n".join(str(item.value) for item in app.markdown)
    page_text = _page_text(app)
    assert not app.exception
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert 'id="nts-intro-video"' not in markdown
    assert "What's your next decision?" in page_text
    assert "Let's find the signal together." in page_text


def test_noise_to_signal_completed_intro_stays_complete():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    page_text = _page_text(app)
    button_labels = "\n".join(button.label for button in app.button)

    assert not app.exception
    assert "next decision" in page_text
    assert "Begin" not in button_labels
    assert app.session_state["noise_to_signal_intro_state"] == "complete"


def test_noise_to_signal_intro_query_forces_replay_for_completed_session():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.query_params["intro"] = "1"
    app.query_params["topic"] = "rag"

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    markdown = "\n".join(str(item.value) for item in app.markdown)
    assert not app.exception
    assert 'id="nts-intro-video"' in markdown
    assert "What's your next decision?" in _page_text(app)
    assert app.query_params["topic"] == ["rag"]


def test_page_config_collapses_but_keeps_sidebar_available():
    app_source = Path("app.py").read_text(encoding="utf-8")
    page_config_call = 'st.set_page_config(initial_sidebar_state="collapsed")'

    assert app_source.count("st.set_page_config(") == 1
    assert page_config_call in app_source
    assert app_source.index(page_config_call) < app_source.index(
        "app_mode = st.sidebar.radio("
    )

    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert app.sidebar.radio[0].label == "App Mode"
    assert app.sidebar.radio[0].options == [
        "Cognivia — From noise to clarity",
        "AI Skill Compass",
        "Interview Coach",
    ]
    assert app.sidebar.radio[0].value == "Noise-to-Signal Agent"


def test_cognivia_css_keeps_native_sidebar_opener_outside_hidden_toolbar_content():
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    hidden_selector_blocks = re.findall(
        r"([^{}]+)\{\{[^{}]*display:\s*none\s*!important;[^{}]*\}\}",
        styles_source,
    )
    toolbar_hidden_rule = styles_source.split("#MainMenu,", 1)[1].split("}}", 1)[0]

    assert 'div[data-testid="stToolbar"]' not in toolbar_hidden_rule
    assert 'div[data-testid="stToolbarActions"]' in toolbar_hidden_rule
    assert all(
        "stSidebarCollapsedControl" not in selectors
        for selectors in hidden_selector_blocks
    )
    assert all(
        "stExpandSidebarButton" not in selectors
        for selectors in hidden_selector_blocks
    )
    assert '[data-testid="stSidebarCollapsedControl"]' in styles_source
    assert 'button[data-testid="stExpandSidebarButton"]' in styles_source
    assert 'button[data-testid="stBaseButton-header"]' not in styles_source


def test_sidebar_visible_labels_map_to_internal_modes():
    for visible_label, internal_mode in (
        ("Cognivia — From noise to clarity", "Noise-to-Signal Agent"),
        ("AI Skill Compass", "AI Skill Compass"),
        ("Interview Coach", "Interview Coach"),
    ):
        app = AppTest.from_file("app.py")
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.radio[0].set_value(visible_label).run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

        assert not app.exception
        assert app.sidebar.radio[0].value == internal_mode


def test_noise_to_signal_home_renders_collapsed_examples_control():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    page_text = _page_text(app)
    button_labels = "\n".join(button.label for button in app.button)

    assert not app.exception
    assert "What's your next decision?" in page_text
    assert "Let's find the signal together." in page_text
    assert "Your AI learning compass" in page_text
    assert "Try examples" in button_labels
    assert app.session_state["noise_to_signal_examples_open"] is False
    cognivia_app = import_module("app")
    home_source = getsource(cognivia_app._render_noise_to_signal_home)
    assert "noise_to_signal_examples_toggle" in home_source
    assert "noise_to_signal_examples_row_toggle" in home_source
    assert "st.expander" not in home_source
    assert "What should you learn next?" not in page_text
    assert "What do you want to learn?" not in page_text
    assert "I'm overwhelmed by AI resources..." not in str(app)
    assert "Help me decide what to learn next..." in str(app)
    assert "I don't know what to learn next" not in button_labels
    assert "Should I learn LangGraph or RAG evaluation?" not in button_labels
    assert "Compare AI Engineer vs Machine Learning Engineer" not in button_labels
    assert "Build a RAG roadmap" not in button_labels
    assert "Create a focused study plan" not in button_labels
    assert "Explain LangGraph" not in button_labels


def test_noise_to_signal_main_search_uses_one_native_submission_form():
    for intro_complete in (False, True):
        app = AppTest.from_file("app.py")
        if intro_complete:
            app.session_state["noise_to_signal_intro_state"] = "complete"

        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

        goal_input = app.text_input(key="noise_to_signal_goal")
        submit_button = app.button(key="generate_noise_to_signal_decision")
        assert not app.exception
        assert goal_input.form_id
        assert submit_button.form_id == goal_input.form_id
        assert submit_button.label == "↵"
        assert not submit_button.shortcut
        assert submit_button.help == "Submit learning decision"

    cognivia_app = import_module("app")
    home_source = getsource(cognivia_app._render_noise_to_signal_home)
    control_source = getsource(
        cognivia_app._render_noise_to_signal_control_accessibility
    )
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    assert "submission_form = st.form(" in home_source
    assert "goal = submission_form.text_input(" in home_source
    assert "submitted = submission_form.form_submit_button(" in home_source
    assert '"noise_to_signal_search_form"' in home_source
    assert 'shortcut="Enter"' not in home_source
    assert "on_change=" not in home_source
    assert home_source.count("_submit_noise_to_signal_goal(goal)") == 1
    assert 'appDocument.addEventListener("keydown"' not in control_source
    assert "submitButton.click()" not in control_source
    assert (
        "div.st-key-generate_noise_to_signal_decision button kbd"
        in styles_source
    )
    assert "display: none !important" in styles_source


def test_guided_intake_and_reflection_fields_are_outside_main_search_route():
    guided_app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        memory_store=RecordingMemoryStore(),
    )

    assert not guided_app.exception
    assert guided_app.text_input(key="noise_to_signal_goal").form_id
    assert (
        guided_app.text_area(key="noise_to_signal_guided_current_skills").form_id
        == ""
    )
    assert guided_app.text_area(key="noise_to_signal_guided_interests").form_id == ""

    result_app, _ = _run_noise_to_signal_app_sequence(
        [("I want to learn RAG evaluation", _single_focus_result(), None)],
        memory_store=RecordingMemoryStore(),
    )
    result_app.button(
        key="noise_to_signal_select_learning_schema_project_first"
    ).click().run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not result_app.exception
    assert (
        result_app.text_input(key="noise_to_signal_learning_note_title").form_id == ""
    )
    assert (
        result_app.text_area(key="noise_to_signal_learning_note_body").form_id == ""
    )
    assert (
        result_app.text_input(key="noise_to_signal_learning_note_tags").form_id == ""
    )


def test_noise_to_signal_examples_controls_share_one_toggle_state():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.session_state["toggle_audit_sentinel"] = "preserved"

    app.button(key="noise_to_signal_examples_toggle").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    button_labels = "\n".join(button.label for button in app.button)
    assert not app.exception
    assert app.session_state["noise_to_signal_examples_open"] is True
    assert app.session_state["toggle_audit_sentinel"] == "preserved"
    assert "I don't know what to learn next" in button_labels
    assert "Should I learn LangGraph or RAG evaluation?" in button_labels
    assert "Compare AI Engineer vs Machine Learning Engineer" not in button_labels
    assert "Build a RAG roadmap" in button_labels
    assert "Create a focused study plan" in button_labels
    assert "Explain LangGraph" in button_labels

    app.button(key="noise_to_signal_examples_toggle").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert app.session_state["noise_to_signal_examples_open"] is False
    assert app.session_state["toggle_audit_sentinel"] == "preserved"
    assert "Explain LangGraph" not in "\n".join(
        button.label for button in app.button
    )

    app.button(key="noise_to_signal_examples_row_toggle").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert app.session_state["noise_to_signal_examples_open"] is True
    assert app.session_state["toggle_audit_sentinel"] == "preserved"
    assert "Explain LangGraph" in "\n".join(button.label for button in app.button)


def test_toggle_callbacks_and_disclosures_have_single_stable_state_paths():
    cognivia_app = import_module("app")
    app_source = Path("app.py").read_text(encoding="utf-8")
    runtime_source = Path("frontend/runtime/drawer.py").read_text(encoding="utf-8")
    skill_compass_source = Path("frontend/skill_compass/view.py").read_text(
        encoding="utf-8"
    )
    source_trees = (
        ast.parse(app_source),
        ast.parse(runtime_source),
        ast.parse(skill_compass_source),
    )
    expander_calls = [
        node
        for source_tree in source_trees
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "expander"
    ]
    expander_keys = []

    for call in expander_calls:
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        assert ast.literal_eval(keywords["on_change"]) == "ignore"
        expander_keys.append(ast.unparse(keywords["key"]))

    callback_sources = "\n".join(
        (
            getsource(cognivia_app._toggle_noise_to_signal_examples),
            getsource(cognivia_app._set_noise_to_signal_focus_mode),
        )
    )
    runtime_drawer_source = getsource(
        cognivia_app._render_noise_to_signal_runtime_drawer
    )

    assert len(expander_calls) == 15
    assert len(expander_keys) == len(set(expander_keys))
    assert "st.rerun" not in app_source + runtime_source + skill_compass_source
    assert "st.rerun" not in callback_sources
    assert "__cogniviaRuntimeDrawerOpen" in runtime_drawer_source
    assert "synchronizeDrawer" in runtime_drawer_source


def test_runtime_drawer_controller_is_idempotent_and_handles_replaced_nodes():
    cognivia_app = import_module("app")
    source = getsource(cognivia_app._render_noise_to_signal_runtime_drawer)
    panel_styles = source.split(".nts-runtime-drawer-panel {{", 1)[1].split(
        "}}", 1
    )[0]

    assert 'data-cognivia-runtime-drawer="true"' in source
    assert 'data-cognivia-runtime-drawer-toggle="true"' in source
    assert 'data-cognivia-runtime-drawer-panel="true"' in source
    assert "(() => {" in source
    assert "})();" in source
    assert "resolveParentContext" in source
    assert "window.parent === window" in source
    assert "} catch (error) {" in source
    assert "if (!parentContext) {" in source
    assert 'controllerKey = "__cogniviaRuntimeDrawerController"' in source
    assert "appDocument.querySelectorAll(rootSelector)" in source
    assert "eventTarget.closest(toggleSelector)" in source
    assert "new parentWindow.MutationObserver(synchronizeDrawer)" in source
    assert "previousController.observer.disconnect()" in source
    assert 'appDocument.removeEventListener(' in source
    assert '"click", previousController.handleDrawerClick' in source
    assert source.count(
        'appDocument.addEventListener("click", handleDrawerClick)'
    ) == 1
    assert 'toggle.addEventListener("click"' not in source
    assert 'document.querySelector(".nts-runtime-drawer-toggle")' not in source
    assert 'document.querySelector(".nts-runtime-drawer-panel")' not in source
    assert 'panel.classList.toggle("is-open", isOpen)' in source
    assert 'toggle.setAttribute("aria-expanded", String(isOpen))' in source
    assert "icon.src = isOpen ? backwardIcon : forwardIcon" in source
    assert "parentWindow[controllerKey] = {" in source
    assert "box-sizing: border-box" in panel_styles
    assert "width: min(340px, calc(100vw - 24px))" in panel_styles
    assert "max-width: calc(100vw - 24px)" in panel_styles
    assert "overflow-x: hidden" in panel_styles
    assert "overflow-wrap: anywhere" in panel_styles
    assert "pointer-events: auto" in panel_styles
    for scoped_selector in (
        ".nts-runtime-drawer-heading",
        ".nts-runtime-status-line",
        ".nts-runtime-mode",
        ".nts-runtime-technical",
        ".nts-runtime-technical-copy",
    ):
        assert (
            f".nts-runtime-drawer-panel {scoped_selector}"
            in source
        )
    assert ".nts-runtime-primary" not in source
    assert ".nts-runtime-facts" not in source
    assert ".nts-runtime-fact" not in source
    assert "\n            details {{" not in source
    assert "\n            summary {{" not in source


def test_parent_document_injections_guard_access_and_clean_up_controllers():
    cognivia_app = import_module("app")
    stability_source = getsource(
        cognivia_app._install_app_rerender_stability_guard
    )
    control_source = getsource(
        cognivia_app._render_noise_to_signal_control_accessibility
    )

    for source in (stability_source, control_source):
        assert "window.parent === window" in source
        assert "} catch (error) {" in source
        assert "return null;" in source
        assert "if (!" in source

    assert "resolveParentDocument" in stability_source
    assert "if (!appDocument?.head)" in stability_source
    assert "cognivia-app-rerender-stability" in stability_source
    assert "resolveParentContext" in control_source
    assert 'legacyObserverKey = "__cogniviaControlLabelObserver"' in control_source
    assert "parentWindow[legacyObserverKey]?.disconnect()" in control_source
    assert 'controllerKey = "__cogniviaControlController"' in control_source
    assert "previousController.observer.disconnect()" in control_source
    assert 'appDocument.removeEventListener(' in control_source
    assert '"keydown",' in control_source
    assert "previousController.handleSearchKeydown" in control_source
    assert "new parentWindow.MutationObserver(applyLabels)" in control_source
    assert "parentWindow[controllerKey] = {{" in control_source
    assert 'appDocument.addEventListener("keydown"' not in control_source


def test_noise_to_signal_quick_prompt_uses_existing_query_path():
    mock_result = _single_focus_result("Build a RAG roadmap")
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [],
        initial_results=[mock_result],
        memory_store=RecordingMemoryStore(),
        examples_open=True,
    )

    app.button(key="noise_to_signal_quick_prompt_2").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert len(graph_stub.calls) == 1
    assert graph_stub.calls[0][0][0] == "Build a RAG roadmap"
    assert app.session_state["noise_to_signal_goal"] == "Build a RAG roadmap"
    assert app.session_state["noise_to_signal_last_goal"] == "Build a RAG roadmap"
    assert app.session_state["noise_to_signal_examples_open"] is False
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert "New search" in "\n".join(button.label for button in app.button)

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert len(graph_stub.calls) == 1


def test_learning_next_quick_prompt_offers_guided_intake_without_graph_submission():
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [],
        initial_results=[],
        memory_store=RecordingMemoryStore(),
        examples_open=True,
    )
    app.session_state["noise_to_signal_focus_mode"] = True

    app.button(key="noise_to_signal_quick_prompt_0").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert graph_stub.calls == []
    assert app.session_state["noise_to_signal_goal"] == (
        "I don't know what to learn next"
    )
    assert app.session_state["noise_to_signal_examples_open"] is False
    assert "Start guided intake" in "\n".join(
        button.label for button in app.button
    )
    assert "Guided intake" not in _page_text(app)
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True

    app.button(key="noise_to_signal_start_guided_intake").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    decision = app.session_state["noise_to_signal_last_decision"]
    assert not app.exception
    assert graph_stub.calls == []
    assert decision["interaction_mode"] == "guided_intake"
    assert decision["guided_intake_entry_point"] == (
        "I want to choose what to learn next"
    )
    assert "Guided intake" in _page_text(app)
    assert "Current level" in "\n".join(item.label for item in app.selectbox)
    assert "Start guided intake" not in "\n".join(
        button.label for button in app.button
    )
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert graph_stub.calls == []
    assert app.session_state["noise_to_signal_last_decision"] == decision
    assert sum(item.value == "Guided intake" for item in app.subheader) == 1


def test_learning_next_quick_prompt_completes_and_new_search_resets_existing_intake():
    memory_store = RecordingMemoryStore()
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [],
        initial_results=[],
        memory_store=memory_store,
        examples_open=True,
    )
    app.session_state["noise_to_signal_focus_mode"] = True
    app.button(key="noise_to_signal_quick_prompt_0").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    app.button(key="noise_to_signal_start_guided_intake").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    _complete_guided_intake(app)

    assert not app.exception
    assert graph_stub.calls == []
    assert app.session_state["noise_to_signal_guided_recommendation"]
    guided_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "guided_intake_recommendation"
    ]
    assert len(guided_events) == 1
    assert "Learning direction schemas" in _page_text(app)

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert graph_stub.calls == []
    assert app.session_state["noise_to_signal_guided_recommendation"]
    assert len(
        [
            event
            for event in memory_store.saved_events
            if event["event_type"] == "guided_intake_recommendation"
        ]
    ) == 1

    app.button(key="noise_to_signal_start_new").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert graph_stub.calls == []
    assert app.session_state["noise_to_signal_goal"] == ""
    assert app.session_state["noise_to_signal_last_goal"] == ""
    assert app.session_state["noise_to_signal_last_decision"] is None
    assert "noise_to_signal_guided_recommendation" not in app.session_state
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True
    assert all(item.value != "Guided intake" for item in app.subheader)
    assert not app.selectbox
    assert not app.text_area
    assert "Start guided intake" not in "\n".join(
        button.label for button in app.button
    )


def test_decision_quick_prompts_continue_to_submit_normally():
    expected_quick_prompts = [
        "I don't know what to learn next",
        "Should I learn LangGraph or RAG evaluation?",
        "Build a RAG roadmap",
        "Create a focused study plan",
        "Explain LangGraph",
    ]
    assert import_module("app").NOISE_TO_SIGNAL_QUICK_PROMPTS == expected_quick_prompts

    for index, prompt in enumerate(
        expected_quick_prompts[1:],
        start=1,
    ):
        app, graph_stub = _run_noise_to_signal_app_sequence(
            [],
            initial_results=[_single_focus_result(prompt)],
            memory_store=RecordingMemoryStore(),
            examples_open=True,
        )

        app.button(key=f"noise_to_signal_quick_prompt_{index}").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

        assert not app.exception
        assert len(graph_stub.calls) == 1
        assert graph_stub.calls[0][0] == (prompt,)
        assert app.session_state["noise_to_signal_last_goal"] == prompt
        assert app.session_state["noise_to_signal_last_decision"]["goal"] == prompt

        if prompt == "Should I learn LangGraph or RAG evaluation?":
            page_text = _page_text(app)
            for visible_section in (
                "Priority now",
                "Why now",
                "Next action",
                "Recommended direction",
                "Focused study sprint",
                "Recommendation summary",
            ):
                assert visible_section in page_text


def test_noise_to_signal_has_no_frontend_comparison_preflight():
    cognivia_app = import_module("app")
    submission_source = getsource(cognivia_app._submit_noise_to_signal_goal)
    result_source = getsource(cognivia_app._render_noise_to_signal_result)
    subject_source = getsource(cognivia_app._structured_learning_subject)

    assert not hasattr(cognivia_app, "_is_incomplete_comparison_request")
    assert not hasattr(cognivia_app, "_render_comparison_clarification")
    assert "comparison_clarification" not in submission_source
    assert "comparison_clarification" not in result_source
    assert "selected_focus" in subject_source
    assert "recommended_direction" in subject_source
    assert "split(" not in subject_source
    assert "re." not in subject_source
    assert '"vs"' not in subject_source
    assert "'vs'" not in subject_source
    assert '" or "' not in subject_source
    assert "' or '" not in subject_source


def test_noise_to_signal_search_submits_only_once_across_normal_rerun():
    mock_result = _single_focus_result("Explain LangGraph")
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", mock_result, None)],
        memory_store=RecordingMemoryStore(),
    )

    assert not app.exception
    assert len(graph_stub.calls) == 1

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert len(graph_stub.calls) == 1
    assert app.session_state["noise_to_signal_last_goal"] == "Explain LangGraph"
    assert app.session_state["noise_to_signal_processing"] is False
    assert "Finding the signal…" not in _page_text(app)
    assert "Recommendation ready." not in _page_text(app)
    assert app.sidebar.radio[0].value == "Noise-to-Signal Agent"
    assert app.sidebar.radio[0].options == [
        "Cognivia — From noise to clarity",
        "AI Skill Compass",
        "Interview Coach",
    ]
    runtime_drawer_markup = "\n".join(
        element.proto.body
        for element in app.get("html")
        if "data-cognivia-runtime-drawer" in element.proto.body
    )
    assert 'data-cognivia-runtime-drawer="true"' in runtime_drawer_markup
    assert (
        'appDocument.addEventListener("click", handleDrawerClick)'
        in runtime_drawer_markup
    )


def test_noise_to_signal_sets_processing_before_graph_call_and_clears_afterward():
    processing_values = []

    def record_processing_state(*args, **kwargs):
        processing_values.append(
            st.session_state["noise_to_signal_processing"]
        )
        return _single_focus_result("Explain LangGraph")

    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", record_processing_state, None)],
        memory_store=RecordingMemoryStore(),
    )

    assert not app.exception
    assert processing_values == [True]
    assert len(graph_stub.calls) == 1
    assert app.session_state["noise_to_signal_processing"] is False


def test_noise_to_signal_processing_renders_one_dark_local_loading_card():
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [],
        initial_results=[],
        memory_store=RecordingMemoryStore(),
        examples_open=True,
    )
    app.session_state["noise_to_signal_processing"] = True
    app.session_state["noise_to_signal_focus_mode"] = True
    app.session_state["noise_to_signal_guided_recommendation"] = {"id": "saved"}

    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    loading_markdown = [
        item.value
        for item in app.markdown
        if 'data-cognivia-loading="true"' in str(item.value)
    ]
    submit_button = app.button(key="generate_noise_to_signal_decision")
    quick_prompt = app.button(key="noise_to_signal_quick_prompt_2")
    assert not app.exception
    assert graph_stub.calls == []
    assert len(loading_markdown) == 1
    assert "Finding the signal…" in loading_markdown[0]
    assert "Reviewing evidence and shaping your recommendation." in loading_markdown[0]
    assert 'role="status"' in loading_markdown[0]
    assert 'aria-live="polite"' in loading_markdown[0]
    assert submit_button.disabled is True
    assert quick_prompt.disabled is True
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True
    assert app.session_state["noise_to_signal_examples_open"] is True
    assert app.session_state["noise_to_signal_guided_recommendation"] == {
        "id": "saved"
    }


def test_app_rerender_guard_keeps_dark_roots_without_preserving_stale_content():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    cognivia_app = import_module("app")

    stability_css = cognivia_app.APP_RERENDER_STABILITY_CSS
    installer_source = getsource(cognivia_app._install_app_rerender_stability_guard)
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    submit_source = getsource(cognivia_app._submit_noise_to_signal_goal)
    assert not app.exception
    assert 'body:has(.nts-brand)' not in stability_css
    assert "html," in stability_css
    assert "body," in stability_css
    assert "#root," in stability_css
    assert 'div[data-testid="stApp"],' in stability_css
    assert 'div[data-testid="stAppViewContainer"]' in stability_css
    assert 'div[data-testid="stMain"]' in stability_css
    assert '[data-stale="true"]' not in stability_css
    assert "stElementContainer" not in stability_css
    assert "opacity" not in stability_css
    assert "visibility" not in stability_css
    assert "display" not in stability_css
    assert "animation" not in stability_css
    assert "transition" not in stability_css
    assert "position" not in stability_css
    assert "height" not in stability_css
    assert "background: #0B132B" in stability_css
    assert "background-color: #0B132B" in stability_css
    assert "color-scheme: dark" in stability_css
    assert "cognivia-app-rerender-stability" in installer_source
    app_source = Path("app.py").read_text(encoding="utf-8")
    assert (
        '_install_app_rerender_stability_guard()\n'
        'if app_mode == "Noise-to-Signal Agent":\n'
        '    _render_runtime_status()\n'
        'else:\n'
        '    _render_secondary_project_drawer()'
    ) in app_source
    assert "ntsFadeIn" not in styles_source
    assert "background: #182234" in styles_source
    assert "rgba(88, 147, 255, 0.18)" in styles_source
    assert "prefers-reduced-motion: reduce" in styles_source
    assert "st.status" not in submit_source
    assert "Recommendation ready." not in submit_source


def test_noise_to_signal_error_clears_loading_and_preserves_existing_ui_state():
    guided_recommendation = {"id": "existing-guided-result"}
    direction_schemas = [{"id": "existing-direction"}]
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", ValueError("offline retrieval failed"), None)],
        initial_session_state={
            "noise_to_signal_focus_mode": True,
            "noise_to_signal_guided_recommendation": guided_recommendation,
            "noise_to_signal_learning_direction_schemas": direction_schemas,
        },
        memory_store=RecordingMemoryStore(),
        examples_open=True,
    )

    error_text = "\n".join(str(item.value) for item in app.error)
    assert not app.exception
    assert len(graph_stub.calls) == 1
    assert "Could not generate the decision trace" in error_text
    assert app.session_state["noise_to_signal_processing"] is False
    assert "Finding the signal…" not in _page_text(app)
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True
    assert app.session_state["noise_to_signal_examples_open"] is True
    assert app.session_state["noise_to_signal_guided_recommendation"] == (
        guided_recommendation
    )
    assert app.session_state["noise_to_signal_learning_direction_schemas"] == (
        direction_schemas
    )


def test_noise_to_signal_focus_mode_is_idempotent_and_preserves_state():
    mock_result = _single_focus_result("Explain LangGraph")
    app, _ = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", mock_result, None)],
        memory_store=RecordingMemoryStore(),
    )
    app.session_state["toggle_audit_sentinel"] = "preserved"

    app.button(key="noise_to_signal_focus_mode_enter").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert app.session_state["noise_to_signal_focus_mode"] is True
    assert app.session_state["toggle_audit_sentinel"] == "preserved"

    app.button(key="noise_to_signal_focus_mode_exit").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert app.session_state["noise_to_signal_focus_mode"] is False
    assert app.session_state["toggle_audit_sentinel"] == "preserved"

    app.button(key="noise_to_signal_focus_mode_enter").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    app.button(key="noise_to_signal_focus_mode_exit").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert app.session_state["noise_to_signal_focus_mode"] is False
    assert app.session_state["toggle_audit_sentinel"] == "preserved"
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_last_goal"] == "Explain LangGraph"
    assert app.session_state["noise_to_signal_last_decision"] == mock_result


def test_noise_to_signal_new_search_reuses_reset_without_intro_or_submission():
    mock_result = _single_focus_result("Explain LangGraph")
    memory_store = RecordingMemoryStore()
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", mock_result, None)],
        memory_store=memory_store,
    )
    original_thread_id = app.session_state["noise_to_signal_thread_id"]
    original_memory_event_count = len(memory_store.saved_events)
    button_labels = "\n".join(button.label for button in app.button)
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    control_source = getsource(
        cognivia_app._render_noise_to_signal_control_accessibility
    )
    hidden_label_styles = styles_source.split(
        "div.st-key-noise_to_signal_start_new button p {{", 1
    )[1].split("}}", 1)[0]

    assert "Start new conversation" not in button_labels
    assert "New search" in button_labels
    assert 'content: "↺  New search"' in styles_source
    assert "display: none" not in hidden_label_styles
    assert "clip: rect(0, 0, 0, 0)" in hidden_label_styles
    assert (
        '".st-key-noise_to_signal_start_new button"'
        not in control_source
    )

    app.button(key="noise_to_signal_focus_mode_enter").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    app.button(key="noise_to_signal_start_new").click().run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert len(graph_stub.calls) == 1
    assert app.session_state["noise_to_signal_thread_id"] != original_thread_id
    assert app.session_state["noise_to_signal_goal"] == ""
    assert app.session_state["noise_to_signal_last_goal"] == ""
    assert app.session_state["noise_to_signal_last_decision"] is None
    assert "noise_to_signal_learning_direction_goal" not in app.session_state
    assert "noise_to_signal_learning_direction_schemas" not in app.session_state
    assert "noise_to_signal_selected_learning_schema_id" not in app.session_state
    assert app.session_state["noise_to_signal_intro_state"] == "complete"
    assert app.session_state["noise_to_signal_focus_mode"] is True
    assert len(memory_store.saved_events) == original_memory_event_count
    assert "Begin" not in "\n".join(button.label for button in app.button)
    assert "New search" not in "\n".join(
        button.label for button in app.button
    )


def test_noise_to_signal_result_query_uses_dark_card_without_changing_content():
    mock_result = _single_focus_result("Explain LangGraph")
    app, _ = _run_noise_to_signal_app_sequence(
        [("Explain LangGraph", mock_result, None)],
        memory_store=RecordingMemoryStore(),
    )
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    query_styles = styles_source.split(
        "div.st-key-noise_to_signal_query_summary", 1
    )[1].split(
        "div.st-key-noise_to_signal_focus_mode_enter", 1
    )[0]
    home_shell_styles = styles_source.split(
        "div.st-key-noise_to_signal_home_shell {{", 1
    )[1].split("}}", 1)[0]
    results_panel_styles = styles_source.split(
        "div.st-key-noise_to_signal_results_panel {{", 1
    )[1].split("}}", 1)[0]

    assert not app.exception
    assert "#182234" in query_styles
    assert "1px solid rgba(88, 147, 255, 0.18)" in query_styles
    assert "#DCE6EA" not in query_styles
    assert "#EAF1F3" not in query_styles
    assert "clamp(3rem, 8vh, 5rem)" in home_shell_styles
    assert "margin: 1.5rem auto 0" in results_panel_styles
    assert "Explain LangGraph" in _page_text(app)
    assert "Overview" in _tab_labels(app)
    assert "Learning paths" in _tab_labels(app)
    assert "Study note" in _tab_labels(app)
    assert "Evidence / technical" in _tab_labels(app)


def test_noise_to_signal_intro_video_markup_uses_video0_without_loop(monkeypatch):
    cognivia_app = import_module("app")
    monkeypatch.setattr(
        cognivia_app,
        "_asset_data_uri",
        lambda path: f"data:mock/{str(path).rsplit('/', 1)[-1]}",
    )

    markup = cognivia_app._noise_to_signal_intro_video_markup()

    assert markup is not None
    assert str(cognivia_app.NOISE_TO_SIGNAL_INTRO_VIDEO_PATH) == (
        "assets/brand/video0.mp4"
    )
    assert "data:mock/video0.mp4" in markup
    assert 'class="nts-intro-video-layer is-playing"' in markup
    assert "autoplay muted playsinline" in markup
    assert "loop" not in markup
    assert "video0-trimmed.mp4" not in markup
    assert "video1.mp4" not in markup
    assert "video2.mp4" not in markup
    assert "video3.mp4" not in markup


def test_noise_to_signal_intro_video_controller_releases_the_application():
    cognivia_app = import_module("app")
    source = getsource(cognivia_app._render_noise_to_signal_intro_video_controller)
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    intro_layer_styles = styles_source.split(
        ".nts-intro-video-layer {{",
        1,
    )[1].split(
        "@keyframes ntsIntroFailsafe",
        1,
    )[0]

    assert "nts-intro-video" in source
    assert "video.muted = true" in source
    assert "video.defaultMuted = true" in source
    assert "video.loop = false" in source
    assert 'video.addEventListener("ended", finishIntro' in source
    assert 'video.addEventListener("error", finishIntro' in source
    assert 'video.addEventListener(\n                        "loadeddata"' in source
    assert 'video.addEventListener(\n                        "playing"' in source
    assert "loadedDataReady = true" in source
    assert "playbackReady = true" in source
    assert "loadedDataReady = video.readyState >= 2" in source
    assert "playbackReady = !video.paused && !video.ended" in source
    assert "if (!loadedDataReady || !playbackReady || !layer)" in source
    assert 'layer.classList.add("is-ready")' in source
    assert 'cover.classList.add("is-releasing")' in source
    assert 'cover.addEventListener(\n                    "transitionend"' in source
    assert "releaseStartupCover();" in source
    assert "finishTimer = window.setTimeout(finishIntro, 12000)" in source
    assert "playback.catch(finishIntro)" in source
    assert 'layer.classList.add("is-playing")' in source
    assert 'layer.classList.add("is-complete")' in source
    assert "video.muted = false" not in source
    assert "domReadyTimeoutMs = 2000" in source
    assert "findIntroElements" in source
    assert "waitForIntroElements" in source
    assert "parentWindow.requestAnimationFrame(" in source
    assert "domReadyTimer = window.setTimeout(finishIntro, domReadyTimeoutMs)" in source
    assert "if (!layer || !video)" not in source
    assert "opacity: 0" in intro_layer_styles
    assert "visibility: hidden" in intro_layer_styles
    assert "pointer-events: none" in intro_layer_styles
    assert ".nts-intro-video-layer.is-playing" in intro_layer_styles


def test_noise_to_signal_intro_controller_guards_parent_and_local_contexts():
    cognivia_app = import_module("app")
    source = getsource(cognivia_app._render_noise_to_signal_intro_video_controller)

    assert "resolveParentContext" in source
    assert "window.parent === window" in source
    assert "return { parentWindow: window, appDocument: document }" in source
    assert "appDocument: window.parent.document" in source
    assert "} catch (error) {" in source
    assert "return null;" in source
    assert "if (!parentContext)" in source
    assert "const { parentWindow, appDocument } = parentContext" in source
    assert "const parentWindow = window.parent" not in source
    assert "const parentDocument = parentWindow.document" not in source
    assert 'appDocument.querySelector(".nts-intro-video-layer")' in source
    assert 'appDocument.getElementById("nts-intro-video")' in source


def test_noise_to_signal_intro_controller_persists_and_supports_forced_replay():
    cognivia_app = import_module("app")
    source = getsource(cognivia_app._render_noise_to_signal_intro_video_controller)
    app_source = getsource(cognivia_app._noise_to_signal_intro_replay_requested)

    assert 'playedKey = "cognivia.noise-to-signal.intro-played.v1"' in source
    assert "parentWindow.localStorage.getItem(playedKey)" in source
    assert 'parentWindow.localStorage.setItem(playedKey, "true")' in source
    assert 'url.searchParams.get("intro") === "1"' in source
    assert 'url.searchParams.delete("intro")' in source
    assert "`${url.pathname}${url.search}${url.hash}`" in source
    assert "parentWindow.history.replaceState(" in source
    assert "alreadyPlayed && !forceReplay" in source
    assert '"(prefers-reduced-motion: reduce)"' in source
    assert 'st.query_params.get("intro") == "1"' in app_source


def test_noise_to_signal_intro_has_no_audio_or_manual_gate():
    cognivia_app = import_module("app")
    intro_source = getsource(cognivia_app._render_noise_to_signal_intro)

    assert not hasattr(cognivia_app, "_render_noise_to_signal_intro_audio_control")
    assert not hasattr(cognivia_app, "NOISE_TO_SIGNAL_WAVES_AUDIO_PATH")
    assert "_render_noise_to_signal_intro_video_controller()" in intro_source
    assert intro_source.index("_render_noise_to_signal_intro_video_controller()") > (
        intro_source.index("if markup:")
    )
    assert "_complete_noise_to_signal_intro()" in intro_source
    assert "st.button" not in intro_source
    assert "audio" not in intro_source.lower()
    assert "First time here? This experience takes less than a minute." not in (
        intro_source
    )


def test_noise_to_signal_header_uses_real_logo_without_manual_intro_gate():
    cognivia_app = import_module("app")
    intro_source = getsource(cognivia_app._render_noise_to_signal_intro)
    header_source = getsource(cognivia_app._render_noise_to_signal_header)

    assert (
        str(cognivia_app.NOISE_TO_SIGNAL_LOGO_PATH)
        == "assets/brand/cognivia-full-inverse-clean.png"
    )
    assert "_asset_data_uri(NOISE_TO_SIGNAL_LOGO_PATH)" in header_source
    assert "First time here? This experience takes less than a minute." not in intro_source
    assert '"Begin"' not in intro_source
    assert "NOISE_TO_SIGNAL_SUBTITLE" in header_source


def test_noise_to_signal_form_controls_use_dark_accessible_states():
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)

    assert (
        'body:has(.nts-brand)\n'
        '        div[data-testid="stTextInput"] div[data-baseweb="input"]'
        in styles_source
    )
    assert (
        'body:has(.nts-brand)\n'
        '        div[data-testid="stTextInput"] div[data-baseweb="base-input"]'
        in styles_source
    )
    assert (
        'body:has(.nts-brand)\n'
        '        div[data-testid="stTextArea"] div[data-baseweb="textarea"]'
        in styles_source
    )
    assert 'div[data-baseweb="textarea"] > div' in styles_source
    assert 'div[data-baseweb="input"]:has(input:focus-visible)' in styles_source
    assert (
        'div[data-baseweb="textarea"]:has(textarea:focus-visible)'
        in styles_source
    )
    assert 'div[data-baseweb="input"]:has(input:disabled)' in styles_source
    assert (
        'div[data-baseweb="textarea"]:has(textarea:disabled)'
        in styles_source
    )
    assert "background: var(--nts-control-bg) !important" in styles_source
    assert "background-color: var(--nts-control-bg) !important" in styles_source
    assert "background: var(--nts-control-bg-hover) !important" in styles_source
    assert (
        "background-color: var(--nts-control-bg-hover) !important"
        in styles_source
    )
    assert ":focus-within" in styles_source
    assert "outline: 2px solid #8AF2E7 !important" in styles_source
    assert 'div[data-baseweb="base-input"] input::placeholder' in styles_source
    assert (
        'div[data-baseweb="textarea"] textarea::placeholder'
        in styles_source
    )
    assert "resize: vertical !important" in styles_source
    assert "color-scheme: dark" in styles_source
    assert (
        "div.st-key-noise_to_signal_results_panel\n"
        '        div[data-testid="stTextInput"]'
        not in styles_source
    )
    assert (
        "div.st-key-noise_to_signal_results_panel\n"
        '        div[data-testid="stTextArea"]'
        not in styles_source
    )


def test_non_cognivia_modes_inherit_native_dark_theme_without_light_overrides():
    config = tomllib.loads(
        Path(".streamlit/config.toml").read_text(encoding="utf-8")
    )
    assert config["theme"] == {
        "base": "dark",
        "primaryColor": "#38D9C8",
        "backgroundColor": "#0B132B",
        "secondaryBackgroundColor": "#111F38",
        "textColor": "#F4F7FA",
    }

    interview_view = import_module("frontend.interview_coach.view")
    skill_compass_view = import_module("frontend.skill_compass.view")
    interview_source = getsource(interview_view._render_interview_coach)
    skill_compass_styles = getsource(
        skill_compass_view._render_ai_skill_compass
    ).split("transparent_logo_path =", 1)[0]

    for light_value in (
        "#f7fbfa",
        "#ffffff",
        "#d8ecea",
        "#89cfc9",
        "#b8e1de",
        "#2b5f5c",
        "#1f3f3d",
    ):
        assert light_value not in interview_source
        assert light_value not in skill_compass_styles

    assert "#38D9C8" in skill_compass_styles
    assert "#B9C6D5" in skill_compass_styles
    assert "#F4F7FA" in skill_compass_styles
    assert ".stTextInput input" not in skill_compass_styles
    assert ".stTextArea textarea" not in skill_compass_styles
    assert '.stSelectbox div[data-baseweb="select"]' not in skill_compass_styles

    for mode, expected_widget in (
        ("AI Skill Compass", "Action"),
        ("Interview Coach", "Developer level"),
    ):
        app = AppTest.from_file("app.py")
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.radio[0].set_value(mode).run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

        assert not app.exception
        assert expected_widget in "\n".join(item.label for item in app.selectbox)
        assert app.sidebar.radio[0].options == [
            "Cognivia — From noise to clarity",
            "AI Skill Compass",
            "Interview Coach",
        ]


def test_interview_coach_hides_temperature_and_keeps_model_and_max_tokens():
    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.sidebar.radio[0].set_value("Interview Coach").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    sidebar_slider_labels = [slider.label for slider in app.sidebar.slider]
    sidebar_selectbox_labels = [
        selectbox.label for selectbox in app.sidebar.selectbox
    ]
    sidebar_captions = "\n".join(caption.value for caption in app.sidebar.caption)
    model_control = app.sidebar.selectbox(key="interview_coach_model")
    max_tokens_control = app.sidebar.slider(key="interview_coach_max_tokens")

    assert not app.exception
    assert sidebar_selectbox_labels == ["Model"]
    assert sidebar_slider_labels == ["Max tokens"]
    assert model_control.options == [
        "GPT-5 mini (recommended)",
        "GPT-5 nano (cheaper)",
        "MiniMax M2.7 (dev alternative)",
    ]
    assert max_tokens_control.value == 1200
    assert "Max tokens: answer length" in sidebar_captions
    assert "Temperature" not in sidebar_slider_labels
    assert "Temp: focus ↔ creativity" not in sidebar_captions


def test_interview_coach_adapts_tokens_until_the_user_overrides_them():
    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.sidebar.radio[0].set_value("Interview Coach").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    questions = next(
        slider for slider in app.slider if slider.label == "Number of questions"
    )
    max_tokens = app.sidebar.slider(key="interview_coach_max_tokens")
    assert questions.value == 1
    assert max_tokens.value == 1200
    assert app.session_state["interview_coach_max_tokens_overridden"] is False

    questions.set_value(2).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    assert app.sidebar.slider(key="interview_coach_max_tokens").value == 1800
    assert app.session_state["interview_coach_max_tokens_overridden"] is False

    questions = next(
        slider for slider in app.slider if slider.label == "Number of questions"
    )
    questions.set_value(5).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    assert app.sidebar.slider(key="interview_coach_max_tokens").value == 3000
    assert app.session_state["interview_coach_max_tokens_overridden"] is False

    app.sidebar.slider(key="interview_coach_max_tokens").set_value(2400).run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert app.session_state["interview_coach_max_tokens_overridden"] is True

    questions = next(
        slider for slider in app.slider if slider.label == "Number of questions"
    )
    questions.set_value(2).run(timeout=APP_TEST_TIMEOUT_SECONDS)
    assert app.sidebar.slider(key="interview_coach_max_tokens").value == 2400
    assert app.session_state["interview_coach_max_tokens_overridden"] is True

    app.session_state["noise_to_signal_thread_id"] = "preserved-cognivia-thread"
    app.sidebar.radio[0].set_value("Noise-to-Signal Agent").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert app.session_state["noise_to_signal_thread_id"] == (
        "preserved-cognivia-thread"
    )
    assert "Max tokens" not in [slider.label for slider in app.sidebar.slider]

    app.sidebar.radio[0].set_value("Interview Coach").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert app.sidebar.slider(key="interview_coach_max_tokens").value == 1200
    assert app.session_state["interview_coach_max_tokens_overridden"] is False


def test_interview_coach_registered_model_policy_reaches_provider_payload(
    monkeypatch,
):
    cognivia_app = import_module("app")
    expected_cases = (
        (
            "GPT-5 mini (recommended)",
            "openai/gpt-5-mini",
            1700,
            None,
        ),
        (
            "GPT-5 nano (cheaper)",
            "openai/gpt-5-nano",
            2100,
            None,
        ),
        (
            "MiniMax M2.7 (dev alternative)",
            "minimax/minimax-m2.7",
            2600,
            1.0,
        ),
    )

    assert cognivia_app.INTERVIEW_MODEL_OPTIONS == {
        label: model for label, model, _, _ in expected_cases
    }
    assert set(cognivia_app.INTERVIEW_MODEL_TEMPERATURE_POLICY) == set(
        cognivia_app.INTERVIEW_MODEL_OPTIONS.values()
    )
    assert cognivia_app.INTERVIEW_MODEL_TEMPERATURE_POLICY == {
        model: temperature for _, model, _, temperature in expected_cases
    }

    for model_label, model, max_tokens, temperature in expected_cases:
        app, request_kwargs = _run_interview_coach_request(
            model_label,
            max_tokens,
        )
        payload = _capture_openrouter_payload(monkeypatch, request_kwargs)

        assert not app.exception
        assert request_kwargs["model"] == model
        assert request_kwargs["max_tokens"] == max_tokens
        assert payload["model"] == model
        assert payload["max_tokens"] == max_tokens
        assert app.session_state["temperature"] == 1.4
        assert app.session_state["interview_coach_temperature"] == 0.2
        assert app.session_state["interview_coach_model"] == model_label
        assert app.session_state["interview_coach_max_tokens"] == max_tokens
        if temperature is None:
            assert "temperature" not in request_kwargs
            assert "temperature" not in payload
            openai_payload = _capture_openai_payload(monkeypatch, request_kwargs)
            assert openai_payload["model"] == model.removeprefix("openai/")
            assert openai_payload["max_tokens"] == max_tokens
            assert "temperature" not in openai_payload
        else:
            assert request_kwargs["temperature"] == temperature
            assert payload["temperature"] == temperature


def test_interview_settings_do_not_change_cognivia_or_skill_compass(
    monkeypatch,
):
    app, interview_kwargs = _run_interview_coach_request(
        "MiniMax M2.7 (dev alternative)",
        2400,
    )
    app.sidebar.radio[0].set_value("Noise-to-Signal Agent").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert interview_kwargs == {
        "model": "minimax/minimax-m2.7",
        "max_tokens": 2400,
        "temperature": 1.0,
    }
    assert "Model" not in [item.label for item in app.sidebar.selectbox]
    assert "Max tokens" not in [item.label for item in app.sidebar.slider]
    assert "Temperature" not in [item.label for item in app.sidebar.slider]

    app.sidebar.radio[0].set_value("Interview Coach").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert not app.exception
    assert app.sidebar.selectbox(key="interview_coach_model").value in (
        "GPT-5 mini (recommended)",
        "GPT-5 nano (cheaper)",
        "MiniMax M2.7 (dev alternative)",
    )
    assert 1000 <= app.sidebar.slider(key="interview_coach_max_tokens").value <= 3000
    assert "Temperature" not in [item.label for item in app.sidebar.slider]

    noise_graph = import_module("tools.noise_to_signal_graph")
    captured_cognivia_kwargs = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured_cognivia_kwargs.update(kwargs)

        def with_structured_output(self, schema):
            return ("structured", schema)

    monkeypatch.setattr(
        noise_graph,
        "get_provider_config",
        lambda: SimpleNamespace(error=None),
    )
    monkeypatch.setattr(
        noise_graph,
        "provider_api_key",
        lambda provider_config: "test-provider-key",
    )
    monkeypatch.setattr(
        noise_graph,
        "provider_base_url",
        lambda provider_config: None,
    )
    monkeypatch.setattr(noise_graph, "ChatOpenAI", FakeChatOpenAI)

    noise_graph._build_llm_intent_classifier()

    assert captured_cognivia_kwargs == {
        "model": noise_graph.DEFAULT_MODEL.removeprefix("openai/"),
        "api_key": "test-provider-key",
        "temperature": 0,
        "timeout": 20,
    }
    cognivia_config_source = getsource(noise_graph._build_llm_intent_classifier)
    for interview_key in (
        "interview_coach_model",
        "interview_coach_temperature",
        "interview_coach_max_tokens",
        "interview_coach_max_tokens_overridden",
    ):
        assert interview_key not in cognivia_config_source
    assert "st.session_state" not in cognivia_config_source

    app.sidebar.radio[0].set_value("AI Skill Compass").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )
    assert not app.exception
    assert "Action" in [item.label for item in app.selectbox]
    assert "Model" not in [item.label for item in app.sidebar.selectbox]
    assert "Max tokens" not in [item.label for item in app.sidebar.slider]
    assert "Temperature" not in [item.label for item in app.sidebar.slider]


def test_noise_to_signal_focus_mode_uses_optimized_ui_assets(monkeypatch):
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    control_source = getsource(cognivia_app._render_noise_to_signal_focus_mode_control)
    original_paths = (
        Path("assets/brand/focus-mode-enter-white-transparent.png"),
        Path("assets/brand/focus-mode-exit-white-transparent.png"),
    )
    optimized_paths = (
        cognivia_app.FOCUS_MODE_ENTER_ICON_PATH,
        cognivia_app.FOCUS_MODE_EXIT_ICON_PATH,
    )

    assert (
        str(cognivia_app.FOCUS_MODE_ENTER_ICON_PATH)
        == "assets/brand/focus-mode-enter-ui.png"
    )
    assert (
        str(cognivia_app.FOCUS_MODE_EXIT_ICON_PATH)
        == "assets/brand/focus-mode-exit-ui.png"
    )
    original_payload_length = 0
    optimized_payload_length = 0
    original_payloads = []
    for path in original_paths:
        with Image.open(path) as image:
            assert image.size == (1254, 1254)
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        original_payloads.append(payload)
        original_payload_length += len(payload)
    for path in optimized_paths:
        assert path.exists()
        assert path.stat().st_size < 50_000
        with Image.open(path) as image:
            assert image.size == (128, 128)
            assert "A" in image.getbands()
            assert image.getchannel("A").getextrema()[0] < 255
        optimized_payload_length += len(base64.b64encode(path.read_bytes()))

    rendered_styles = []
    monkeypatch.setattr(
        cognivia_app.st,
        "markdown",
        lambda body, **kwargs: rendered_styles.append(body),
    )
    cognivia_app._render_noise_to_signal_styles()
    generated_css = rendered_styles[0]
    embedded_png_uris = re.findall(
        r"data:image/png;base64,[A-Za-z0-9+/=]+",
        generated_css,
    )
    embedded_payload_length = sum(
        len(uri.split(",", 1)[1]) for uri in embedded_png_uris
    )

    assert len(embedded_png_uris) == 2
    assert embedded_png_uris[0] != embedded_png_uris[1]
    assert embedded_payload_length == optimized_payload_length
    assert embedded_payload_length < 100_000
    assert optimized_payload_length < original_payload_length * 0.02
    assert all(payload not in generated_css for payload in original_payloads)
    assert "width: 52px !important" in styles_source
    assert "height: 52px !important" in styles_source
    assert "width: 44px" in styles_source
    assert "height: 44px" in styles_source
    assert "background-size: 72px 72px" in styles_source
    assert '"Enter Focus Mode"' in control_source
    assert '"Exit Focus Mode"' in control_source


def _single_focus_result(goal="I want to learn RAG evaluation"):
    return {
        "goal": goal,
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "contextual",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "Build a study plan for RAG evaluation.",
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [],
        "retrieval_trace": [],
        "evidence": {"items": []},
        "study_plan": {"plan": "Practice RAG evaluation for 60 minutes."},
    }


def _out_of_scope_result(goal="Tacos al Pastor"):
    return {
        "goal": goal,
        "decision_status": "insufficient_evidence",
        "interaction_mode": "direct_decision",
        "evidence_quality": "weak",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": None,
        "recommendation": (
            "The retrieved evidence is insufficient to answer this question reliably."
        ),
        "next_action": "Ask an AI learning, career, or study question.",
        "decision_trace": [],
        "retrieval_trace": [
            "Retrieval attempt 1: weak - focus is outside scope and not directly supported."
        ],
        "evidence_reason": (
            "The focus appears outside the AI Engineering learning scope, "
            "and retrieved evidence does not directly support the topic."
        ),
        "evidence": {"items": []},
        "study_plan": None,
    }


def test_runtime_status_reports_offline_fallback_when_provider_is_absent():
    status_lines = build_runtime_status_lines({})

    assert status_lines == [
        "Runtime status:",
        "Offline mode active",
        (
            "No OpenAI or OpenRouter models are being used. Cognivia will use "
            "deterministic guidance and may skip evidence-backed retrieval."
        ),
        "Offline mode does not use OpenAI/OpenRouter credits.",
        "Codex/ChatGPT Plus is development tooling, not Cognivia app runtime.",
        "Memory: local fallback / no durable DB configured",
        "Evidence: local Qdrant/RAG evidence path",
    ]


def test_runtime_status_reports_openrouter_when_configured():
    status_lines = build_runtime_status_lines(
        {
            "OPENROUTER_API_KEY": "test-openrouter-key",
            "DATABASE_URL": "postgresql://example/test",
        }
    )

    assert "OpenRouter mode active" in status_lines
    assert "Provider: OpenRouter" in status_lines
    assert "Live model calls may use OpenRouter API credits." in status_lines
    assert "Memory: PostgreSQL configured" in status_lines


def test_runtime_status_reports_openai_only_when_explicitly_selected():
    status_lines = build_runtime_status_lines({"OPENAI_API_KEY": "test-openai-key"})

    assert "Offline mode active" in status_lines
    assert "No OpenAI or OpenRouter models are being used." in "\n".join(status_lines)
    assert "Provider: OpenRouter" not in status_lines

    status_lines = build_runtime_status_lines(
        {
            "COGNIVIA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-openai-key",
        }
    )
    assert "OpenAI mode active" in status_lines
    assert "Provider: OpenAI" in status_lines
    assert "Live model calls may use OpenAI API credits." in status_lines


def test_runtime_status_reports_missing_selected_provider_key():
    status_lines = build_runtime_status_lines({"COGNIVIA_LLM_PROVIDER": "openai"})

    assert "Provider not configured" in status_lines
    assert (
        "The selected provider API key is missing. Cognivia will continue "
        "with deterministic guidance where possible."
    ) in status_lines
    assert "No OpenAI/OpenRouter credits are used until a provider is configured." in status_lines


def test_runtime_drawer_presents_openai_status_once_with_collapsed_details():
    cognivia_app = import_module("app")
    markup = cognivia_app._runtime_drawer_markup(
        {
            "COGNIVIA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-openai-key",
        }
    )
    details_tag = markup.split("<details", 1)[1].split(">", 1)[0]

    assert "<h2>" not in markup
    assert 'class="nts-runtime-primary"' not in markup
    assert 'class="nts-runtime-facts"' not in markup
    assert 'class="secondary-project-drawer-marker"' not in markup
    assert '<p class="nts-runtime-drawer-heading">Runtime</p>' in markup
    assert markup.count('class="nts-runtime-status-line') == 3
    assert (
        markup.count(
            '<p class="nts-runtime-status-line nts-runtime-mode">OpenAI</p>'
        )
        == 1
    )
    assert '<strong>Memory:</strong> Local' in markup
    assert "<strong>Evidence:</strong> Local Qdrant / RAG" in markup
    assert "<summary>Technical details</summary>" in markup
    assert " open" not in details_tag
    assert "<strong>Provider:</strong> OpenAI" in markup
    assert "<strong>Persistence:</strong> None" in markup
    assert "<strong>API credits:</strong> May use OpenAI credits" in markup
    assert "mode active" not in markup
    assert "Live model calls" not in markup
    assert "Codex" not in markup
    assert "ChatGPT Plus" not in markup
    assert "deterministic guidance" not in markup


def test_runtime_drawer_preserves_dynamic_alternative_runtime_states():
    cognivia_app = import_module("app")
    runtime_cases = (
        (
            {
                "OPENROUTER_API_KEY": "test-openrouter-key",
                "DATABASE_URL": "postgresql://example/test",
            },
            "OpenRouter",
            "<strong>Memory:</strong> PostgreSQL",
            "<strong>API credits:</strong> May use OpenRouter credits",
        ),
        (
            {},
            "Offline",
            "<strong>Memory:</strong> Local",
            "<strong>API credits:</strong> Not used",
        ),
    )

    for config, primary_status, memory_status, technical_copy in runtime_cases:
        markup = cognivia_app._runtime_drawer_markup(config)

        assert (
            markup.count(
                f'<p class="nts-runtime-status-line nts-runtime-mode">{primary_status}</p>'
            )
            == 1
        )
        assert memory_status in markup
        assert "<strong>Evidence:</strong> Local Qdrant / RAG" in markup
        assert technical_copy in markup
        assert "mode active" not in markup
        assert "Live model calls" not in markup


def test_runtime_drawers_share_data_but_use_intentionally_different_markup():
    cognivia_app = import_module("app")
    config = {
        "COGNIVIA_LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-openai-key",
        "DATABASE_URL": "postgresql://example/test",
    }
    presentation = cognivia_app._runtime_presentation_data(config)
    cognivia_markup = cognivia_app._runtime_drawer_markup(config)
    secondary_markup = cognivia_app._secondary_runtime_markup()
    cognivia_source = getsource(cognivia_app._runtime_drawer_markup)
    secondary_source = getsource(cognivia_app._secondary_runtime_markup)

    for value in (
        presentation["mode"],
        presentation["memory"],
        presentation["evidence"],
    ):
        assert value in cognivia_markup
    for label, value in cognivia_app._runtime_technical_details(presentation):
        assert f"<strong>{label}:</strong> {value}" in cognivia_markup

    assert "_runtime_presentation_data(config)" in cognivia_source
    assert "_runtime_presentation_data(" not in secondary_source
    assert 'class="nts-runtime-status-line nts-runtime-mode"' in cognivia_markup
    assert 'class="secondary-project-drawer-marker"' in secondary_markup
    assert 'class="secondary-project-drawer-marker"' not in cognivia_markup


def test_secondary_runtime_drawer_uses_shared_compact_dynamic_data():
    cognivia_app = import_module("app")
    runtime_cases = (
        (
            {
                "COGNIVIA_LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-openai-key",
            },
            {
                "mode": "OpenAI",
                "provider": "OpenAI",
                "memory": "Local",
                "persistence": "None",
                "evidence": "Local Qdrant / RAG",
                "api_credits": "May use OpenAI credits",
            },
        ),
        (
            {
                "OPENROUTER_API_KEY": "test-openrouter-key",
                "DATABASE_URL": "postgresql://example/test",
            },
            {
                "mode": "OpenRouter",
                "provider": "OpenRouter",
                "memory": "PostgreSQL",
                "persistence": "Persistent",
                "evidence": "Local Qdrant / RAG",
                "api_credits": "May use OpenRouter credits",
            },
        ),
        (
            {},
            {
                "mode": "Offline",
                "provider": "None",
                "memory": "Local",
                "persistence": "None",
                "evidence": "Local Qdrant / RAG",
                "api_credits": "Not used",
            },
        ),
    )

    for config, expected_presentation in runtime_cases:
        presentation = cognivia_app._runtime_presentation_data(config)
        markup = cognivia_app._secondary_runtime_markup()

        assert presentation == expected_presentation
        assert 'class="secondary-project-drawer-marker"' in markup
        assert "Runtime status:" not in markup
        assert "OpenAI" not in markup
        assert "OpenRouter" not in markup


def test_secondary_project_drawer_is_scoped_scrollable_and_accessible():
    cognivia_app = import_module("app")
    source = getsource(cognivia_app._render_secondary_project_drawer)
    sidebar_styles = source.split(
        '[data-testid="stSidebar"] {{', 1
    )[1].split("}}", 1)[0]
    content_styles = source.split(
        'div[data-testid="stSidebarContent"] {{', 1
    )[1].split("}}", 1)[0]
    header_styles = source.split(
        'div[data-testid="stSidebarHeader"] {{', 1
    )[1].split("}}", 1)[0]
    body_styles = source.split(
        'div[data-testid="stSidebarUserContent"] {{', 1
    )[1].split("}}", 1)[0]

    assert source.index('div[data-testid="stSidebarHeader"]') < source.index(
        'div[data-testid="stSidebarUserContent"]'
    )
    assert "height: 100dvh" in sidebar_styles
    assert "max-height: 100dvh" in sidebar_styles
    assert "overflow: hidden" in sidebar_styles
    assert "display: flex" in content_styles
    assert "flex-direction: column" in content_styles
    assert "max-height: 100dvh" in content_styles
    assert "overflow: hidden" in content_styles
    assert "overscroll-behavior: contain" in content_styles
    assert "position: sticky" in header_styles
    assert "top: 0" in header_styles
    assert "order: 0" in header_styles
    assert "flex: 0 0 auto" in header_styles
    assert "order: 1" in body_styles
    assert "flex: 1 1 auto" in body_styles
    assert "min-width: 0" in body_styles
    assert "min-height: 0" in body_styles
    assert "overflow-x: hidden" in body_styles
    assert "overflow-y: auto" in body_styles
    assert "overflow-wrap: anywhere" in body_styles
    assert "padding-bottom: max(2rem, env(safe-area-inset-bottom))" in body_styles
    assert "touch-action: pan-y" in body_styles
    assert 'div[data-testid="stSidebar"]' not in Path("app.py").read_text()
    assert 'const sidebarSelector = \'[data-testid="stSidebar"]\'' in source
    assert 'sidebar.id = "cognivia-secondary-project-drawer"' in source
    assert 'data-cognivia-secondary-project-drawer="true"' in source
    assert 'div[data-testid="stSidebarCollapseButton"]' in source
    assert 'button[data-testid="stExpandSidebarButton"]' in source
    assert "pointer-events: auto" in source
    assert 'isSecondaryDrawer ? "Toggle project drawer"' in source
    assert 'setAttributeIfChanged(button, "aria-label", accessibleName)' in source
    assert '"aria-expanded",' in source
    assert 'String(isExpanded)' in source
    assert '"aria-controls"' in source
    assert 'key="secondary_runtime_technical_details"' in source
    assert 'expanded=False' in source
    assert 'addEventListener("click"' not in source
    assert "\n            details {{" not in source
    assert "\n            summary {{" not in source
    assert "\n            button {{" not in source
    assert "\n            p {{" not in source


def test_focus_mode_targets_the_tag_agnostic_sidebar_root():
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)

    assert (
        'body:has(.nts-focus-mode-active) [data-testid="stSidebar"],'
        in styles_source
    )
    assert (
        'body:has(.nts-focus-mode-active) div[data-testid="stSidebar"],'
        not in styles_source
    )


def test_secondary_modes_render_compact_runtime_details_without_primary_regression(
    monkeypatch,
):
    cognivia_app = import_module("app")
    monkeypatch.delenv("COGNIVIA_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    for mode, expected_widget in (
        ("AI Skill Compass", "Action"),
        ("Interview Coach", "Developer level"),
    ):
        app = AppTest.from_file("app.py")
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.sidebar.radio[0].set_value(mode).run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        secondary_markup = "\n".join(
            element.proto.body
            for element in app.get("html")
            if "data-cognivia-secondary-project-drawer" in element.proto.body
        )
        technical_copy = "\n".join(item.value for item in app.caption)

        assert not app.exception
        assert expected_widget in "\n".join(item.label for item in app.selectbox)
        assert secondary_markup
        assert "Runtime status:" not in secondary_markup
        assert "Offline" not in secondary_markup
        assert "Provider" not in secondary_markup
        assert "Technical details" in _expander_labels(app)
        assert "Runtime details" not in _expander_labels(app)
        assert "Mode: Offline" in technical_copy
        assert "Provider: None" in technical_copy
        assert "Memory: Local" in technical_copy
        assert "Persistence: None" in technical_copy
        assert "Evidence: Local Qdrant / RAG" in technical_copy
        assert "API credits: Not used" in technical_copy
        assert "Codex" not in technical_copy
        assert "ChatGPT Plus" not in technical_copy
        assert "deterministic guidance" not in technical_copy

    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert "Technical details" in _expander_labels(app)
    assert "Runtime details" not in _expander_labels(app)
    assert any(
        "data-cognivia-runtime-drawer" in element.proto.body
        for element in app.get("html")
    )
    runtime_sidebar_source = getsource(cognivia_app._render_runtime_status)
    assert "st.sidebar.info" not in runtime_sidebar_source
    assert "st.sidebar.subheader(\"Runtime\")" in runtime_sidebar_source


def test_mode_change_resets_only_runtime_detail_expansion_state():
    cognivia_app = import_module("app")
    app = AppTest.from_file("app.py")
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)
    app.session_state["runtime_details"] = True
    app.session_state["secondary_runtime_technical_details"] = True
    app.session_state["runtime_detail_reset_sentinel"] = "preserved"

    app.sidebar.radio[0].set_value("AI Skill Compass").run(
        timeout=APP_TEST_TIMEOUT_SECONDS
    )

    assert not app.exception
    assert "runtime_details" not in app.session_state
    assert "secondary_runtime_technical_details" not in app.session_state
    assert app.session_state["runtime_detail_reset_sentinel"] == "preserved"
    assert "Technical details" in _expander_labels(app)
    assert "expanded=False" in getsource(cognivia_app._render_secondary_project_drawer)


def test_learning_direction_schema_generation_is_deterministic_and_complete():
    schemas = generate_learning_direction_schemas(
        "I want to learn RAG evaluation",
        {
            "decision_status": "single_focus",
            "evidence_quality": "contextual",
            "selected_focus": "RAG evaluation",
        },
    )

    assert [schema["id"] for schema in schemas] == [
        "foundation_first",
        "project_first",
        "interview_practical",
    ]
    assert len(schemas) == 3
    for schema in schemas:
        assert schema["title"]
        assert schema["current_state"]
        assert schema["target_outcome"]
        assert schema["fit_reason"]
        assert len(schema["nodes"]) >= 3
        assert schema["first_action"]
        assert schema["checkpoint"]
        assert schema["risk_or_gap"]


def test_learning_direction_schema_generation_uses_prompt_context_for_generic_decisions():
    generic_decision = {
        "decision_status": "insufficient_evidence",
        "evidence_quality": "weak",
        "recommendation": (
            "The retrieved evidence is insufficient to answer this question reliably."
        ),
        "next_action": "Refine the question and retrieve evidence again.",
    }
    prompts = [
        "What should I learn next?",
        "Why is RAG evaluation useful for AI engineers?",
        "Should I learn LangGraph or RAG evaluation?",
        "How do I move from backend to AI engineering?",
    ]

    schema_text_by_prompt = {}
    for prompt in prompts:
        schemas = generate_learning_direction_schemas(prompt, generic_decision)
        schema_text_by_prompt[prompt] = "\n".join(
            part
            for schema in schemas
            for part in (
                schema["first_action"],
                schema["checkpoint"],
                schema["target_outcome"],
            )
        )

    assert len(set(schema_text_by_prompt.values())) == len(prompts)
    assert "retrieval relevance" in schema_text_by_prompt[
        "Why is RAG evaluation useful for AI engineers?"
    ]
    assert "LangGraph vs RAG evaluation" in schema_text_by_prompt[
        "Should I learn LangGraph or RAG evaluation?"
    ]
    backend_text = schema_text_by_prompt["How do I move from backend to AI engineering?"]
    assert "backend-to-AI engineering transition" in backend_text
    assert "LLM" in backend_text
    assert "APIs" in backend_text or "backend skills" in backend_text


def test_backend_to_ai_learning_paths_are_transition_oriented():
    schemas = generate_learning_direction_schemas(
        "How do I move from backend to AI engineering?",
        {
            "decision_status": "insufficient_evidence",
            "evidence_quality": "weak",
            "recommendation": "The retrieved evidence is insufficient.",
            "next_action": "Refine the question.",
        },
    )
    all_text = "\n".join(
        part
        for schema in schemas
        for part in (
            schema["subtitle"],
            schema["target_outcome"],
            schema["fit_reason"],
            schema["first_action"],
            schema["checkpoint"],
            schema["risk_or_gap"],
            *schema["nodes"],
        )
    )

    assert schemas[0]["id"] == "foundation_first"
    assert "five-sentence plain-language summary" not in schemas[0]["first_action"]
    assert "Map your backend skills" in schemas[0]["first_action"]
    assert any(
        transferable in all_text
        for transferable in ("APIs", "databases", "testing", "deployment", "observability")
    )
    assert any(
        ai_gap in all_text
        for ai_gap in ("LLM APIs", "embeddings", "retrieval", "RAG", "evaluation")
    )
    assert "minimal AI-enabled backend endpoint" in all_text
    assert "structured output or RAG" in all_text


def test_noise_to_signal_permanent_background_renderer_is_absent():
    cognivia_app = import_module("app")

    assert not hasattr(cognivia_app, "_noise_to_signal_background_video_markup")
    assert not hasattr(cognivia_app, "_render_noise_to_signal_background_video")
    assert not hasattr(cognivia_app, "BACKGROUND_VIDEO_SEQUENCE")


def test_noise_to_signal_home_does_not_render_old_permanent_video_controls():
    app = AppTest.from_file("app.py")
    app.session_state["noise_to_signal_intro_state"] = "complete"
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    markup = "\n".join(
        item.value
        for item in app.markdown
        if isinstance(item.value, str) and not item.value.lstrip().startswith("<style>")
    )

    assert not app.exception
    assert "nts-final-background-controls" not in markup
    assert "nts-background-video-layer" not in markup
    assert "Pause final background video" not in markup


def test_noise_to_signal_helper_tip_respects_feature_flag(monkeypatch):
    cognivia_app = import_module("app")
    monkeypatch.setattr(cognivia_app, "ENABLE_PIKO_IRI_TIPS", True)
    monkeypatch.setattr(
        cognivia_app,
        "_asset_data_uri",
        lambda path: f"data:mock/{str(path).rsplit('/', 1)[-1]}",
    )

    enabled_markup = cognivia_app._helper_tip_markup("piko", "Use one small task.")

    assert "Piko tip:" in enabled_markup
    assert "Use one small task." in enabled_markup
    assert "assets/piko.png" not in enabled_markup
    assert 'src="data:mock/piko.png"' in enabled_markup

    monkeypatch.setattr(cognivia_app, "ENABLE_PIKO_IRI_TIPS", False)

    assert cognivia_app._helper_tip_markup("iri", "Compare the evidence.") == ""


def test_noise_to_signal_helper_tip_falls_back_to_text_when_icon_missing(monkeypatch):
    cognivia_app = import_module("app")
    monkeypatch.setattr(cognivia_app, "ENABLE_PIKO_IRI_TIPS", True)
    monkeypatch.setattr(cognivia_app, "_asset_data_uri", lambda path: None)

    markup = cognivia_app._helper_tip_markup("iri", "Compare the evidence.")

    assert "Iri tip:" in markup
    assert "Compare the evidence." in markup
    assert "<img " not in markup


def test_noise_to_signal_helper_tip_text_meets_normal_text_contrast():
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    markup_source = getsource(cognivia_app._helper_tip_markup)

    assert (
        _contrast_ratio(
            cognivia_app.NOISE_TO_SIGNAL_HELPER_TEXT_COLOR,
            "#111F38",
        )
        >= 4.5
    )
    assert (
        "--nts-helper-text: {NOISE_TO_SIGNAL_HELPER_TEXT_COLOR}"
        in styles_source
    )
    assert "color:var(--nts-helper-text)" in markup_source
    assert "#49636b" not in markup_source


def test_noise_to_signal_compact_callout_has_scoped_dark_state_styling():
    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        memory_store=RecordingMemoryStore(),
    )
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    callout_styles = styles_source.split(
        ".nts-results-compact-callout {{", 1
    )[1].split("}}", 1)[0]
    callout_markup = [
        str(item.value)
        for item in app.markdown
        if "nts-results-compact-callout" in str(item.value)
    ]

    assert not app.exception
    assert callout_markup
    assert "border:" in callout_styles
    assert "background:" in callout_styles
    assert "color: var(--nts-muted)" in callout_styles


def test_noise_to_signal_runtime_status_renders_without_provider_or_database(
    monkeypatch,
):
    monkeypatch.delenv("COGNIVIA_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("DATABASE_URL", "")

    app, _ = _run_noise_to_signal_app_sequence([], memory_store=RecordingMemoryStore())
    expander_labels = _expander_labels(app)
    cognivia_app = import_module("app")
    drawer_markup = cognivia_app._runtime_drawer_markup({})

    assert not app.exception
    assert "Technical details" in expander_labels
    assert "Runtime details" not in expander_labels
    assert '<p class="nts-runtime-drawer-heading">Runtime</p>' in drawer_markup
    assert '<p class="nts-runtime-status-line nts-runtime-mode">Offline</p>' in drawer_markup
    assert "<strong>Memory:</strong> Local" in drawer_markup
    assert "<strong>Evidence:</strong> Local Qdrant / RAG" in drawer_markup
    assert "<strong>Provider:</strong> None" in drawer_markup
    assert "<strong>API credits:</strong> Not used" in drawer_markup
    assert "Offline mode active" not in drawer_markup
    assert "No OpenAI or OpenRouter models" not in drawer_markup


def test_noise_to_signal_app_renders_clarification_without_exception():
    mock_result = {
        "decision_status": "needs_clarification",
        "evidence_quality": "not_required",
        "retrieval_attempts": 0,
        "selected_focus": None,
        "recommendation": (
            "Please provide a target role, project, or skill area before "
            "choosing a study plan."
        ),
        "next_action": (
            "Add a target role, project, or skill area, then rerun the decision."
        ),
        "decision_trace": [
            "User goal: What should I learn next?",
            "Retrieval skipped: more context required.",
            "Decision status: needs_clarification",
            "Short evidence-based reasoning: The goal is too broad to turn into a concrete study topic without more context.",
        ],
        "evidence": {"items": []},
        "study_plan": None,
        "query_reformulated": False,
        "retrieval_trace": ["Retrieval skipped: more context required."],
    }

    app = _run_noise_to_signal_app(mock_result, "What should I learn next?")
    page_text = _page_text(app)
    subheader_text = "\n".join(item.value for item in app.subheader)
    expander_labels = "\n".join(item.label for item in app.expander)

    assert not app.exception
    assert "Please provide a target role" in page_text
    assert "Focused study sprint" not in subheader_text
    assert "Decision trace" in expander_labels
    assert "Technical details" in expander_labels


def test_noise_to_signal_app_renders_guided_intake_without_fake_study_plan():
    mock_result = {
        "goal": "I feel lost and want a practical AI learning path",
        "decision_status": "needs_clarification",
        "interaction_mode": "guided_intake",
        "guided_intake_entry_point": "I feel lost and need direction",
        "evidence_quality": "not_required",
        "retrieval_attempts": 0,
        "selected_focus": None,
        "recommendation": (
            "I need a little learner profile context before choosing a "
            "learning path."
        ),
        "next_action": (
            "Add your current level, current skills, interests, preferred work "
            "style, target role if known, and available learning time."
        ),
        "decision_trace": [
            "User goal: I feel lost and want a practical AI learning path",
            "Retrieval skipped: more context required.",
            "Decision status: needs_clarification",
            "Short evidence-based reasoning: The goal is too broad to turn into a concrete study topic without more context.",
        ],
        "evidence": {"items": []},
        "study_plan": None,
        "query_reformulated": False,
        "retrieval_trace": ["Retrieval skipped: more context required."],
    }

    app = _run_noise_to_signal_app(
        mock_result,
        "I feel lost and want a practical AI learning path",
    )
    page_text = _page_text(app)
    text_area_labels = "\n".join(item.label for item in app.text_area)
    selectbox_labels = "\n".join(item.label for item in app.selectbox)
    text_input_labels = "\n".join(item.label for item in app.text_input)
    number_input_labels = "\n".join(item.label for item in app.number_input)
    button_labels = "\n".join(item.label for item in app.button)

    assert not app.exception
    assert "Guided intake" in page_text
    assert page_text.count("A little more context is needed") == 1
    assert (
        page_text.count(
            "Add your current level, skills, interests, work style, target role, "
            "and available learning time."
        )
        == 1
    )
    assert "Recommendation summary" not in page_text
    assert "Direction:" not in page_text
    assert "Why:" not in page_text
    assert "Next:" not in page_text
    assert "Why now" not in page_text
    assert "Next action" not in page_text
    assert _tab_labels(app) == ""
    assert "Learning direction schemas" not in page_text
    assert "Piko tip:" not in page_text
    assert "Turn this recommendation into one small study task for today." not in page_text
    assert "Entry point: I feel lost and need direction" in page_text
    assert "Current level" in selectbox_labels
    assert "Preferred work style" in selectbox_labels
    assert "Current skills" in text_area_labels
    assert "Interests" in text_area_labels
    assert "Target role or direction, if known" in text_input_labels
    assert "Study time available today (minutes)" in number_input_labels
    assert "Available study time today (minutes)" not in number_input_labels
    assert "Generate guided learning path" in button_labels
    assert "Focused study sprint" not in page_text


def test_noise_to_signal_guided_intake_no_evidence_shows_single_status_message():
    mock_result = _guided_intake_result(
        "What should I study next?",
        "I want to choose what to learn next",
    )

    app = _run_noise_to_signal_app(
        mock_result,
        "What should I study next?",
        after_decision=_complete_guided_intake,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Evidence status" in page_text
    assert (
        "No knowledge-base evidence was attached to this guided recommendation."
        in page_text
    )
    assert "Treat this as a profile-based draft, not evidence-backed guidance." in page_text
    assert "Evidence used" not in page_text
    assert "No retrieved knowledge-base evidence was available for this profile" not in page_text
    assert "No retrieved evidence was attached" not in page_text
    assert "Knowledge-base retrieval is unavailable right now" not in page_text


def test_noise_to_signal_guided_intake_explains_recommendations():
    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
        memory_store=RecordingMemoryStore(),
    )
    page_text = _page_text(app)
    expander_labels = _expander_labels(app)

    assert not app.exception
    assert "Recommended direction" in page_text
    assert "What this means" in page_text
    assert "Why this fits" in page_text
    assert "First action" in page_text
    assert "Focus on building applications that connect LLMs" in page_text
    assert "AI Application Engineer" in page_text
    assert "Builds user-facing AI products" in page_text
    assert "prompting" in page_text
    assert "Designing instructions, examples, and structured formats" in page_text
    assert "View captured learner profile JSON" in expander_labels


def test_noise_to_signal_guided_intake_defaults_to_study_next_entry_point():
    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
    )

    page_text = _page_text(app)

    assert not app.exception
    assert "Entry point: I want to choose what to learn next" in page_text
    assert '"entry_point": "I want to choose what to learn next"' in page_text


def test_noise_to_signal_guided_intake_defaults_to_lost_entry_point():
    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "I feel lost and want a practical AI learning path",
            "I feel lost and need direction",
        ),
        "I feel lost and want a practical AI learning path",
        after_decision=_complete_guided_intake,
    )

    page_text = _page_text(app)

    assert not app.exception
    assert "Entry point: I feel lost and need direction" in page_text
    assert '"entry_point": "I feel lost and need direction"' in page_text


def test_noise_to_signal_guided_intake_switching_requests_does_not_leak_entry_point():
    app, _ = _run_noise_to_signal_app_sequence(
        [
            (
                "I feel lost and want a practical AI learning path",
                _guided_intake_result(
                    "I feel lost and want a practical AI learning path",
                    "I feel lost and need direction",
                ),
                None,
            ),
            (
                "What should I study next?",
                _guided_intake_result(
                    "What should I study next?",
                    "I want to choose what to learn next",
                ),
                _complete_guided_intake,
            ),
        ]
    )

    page_text = _page_text(app)

    assert not app.exception
    assert "Entry point: I want to choose what to learn next" in page_text
    assert '"entry_point": "I want to choose what to learn next"' in page_text
    assert '"entry_point": "I feel lost and need direction"' not in page_text


def test_noise_to_signal_single_focus_after_guided_intake_does_not_run_stale_guided_retrieval():
    retriever_calls = []

    def retriever(*args, **kwargs):
        retriever_calls.append({"args": args, "kwargs": kwargs})
        return []

    single_focus_result = {
        "goal": "I want to learn RAG evaluation",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "contextual",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "Build a study plan for RAG evaluation.",
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [],
        "retrieval_trace": [],
        "evidence": {"items": []},
        "study_plan": {"plan": "Practice RAG evaluation for 60 minutes."},
    }

    app, _ = _run_noise_to_signal_app_sequence(
        [
            (
                "What should I study next?",
                _guided_intake_result(
                    "What should I study next?",
                    "I want to choose what to learn next",
                ),
                _complete_guided_intake,
            ),
            (
                "I want to learn RAG evaluation",
                single_focus_result,
                _click_guided_intake_submit_if_present,
            ),
        ],
        retriever=retriever,
    )

    page_text = _page_text(app)

    assert not app.exception
    assert len(retriever_calls) == 1
    assert "Focused study sprint" in page_text
    assert "Guided intake" not in page_text


def test_noise_to_signal_guided_intake_qdrant_lock_warning_is_concise():
    def locked_retriever(*args, **kwargs):
        raise RuntimeError(
            "Storage folder data/vector_store/qdrant is already accessed by "
            "another instance of Qdrant client."
        )

    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
        retriever=locked_retriever,
    )

    page_text = _page_text(app)

    assert not app.exception
    assert "The local evidence store is busy or unavailable" in page_text
    assert "Evidence status" in page_text
    assert "another instance of Qdrant client" not in page_text


def test_noise_to_signal_guided_intake_missing_provider_key_is_concise():
    def missing_provider_retriever(*args, **kwargs):
        raise ValueError("The selected provider API key is missing.")

    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
        retriever=missing_provider_retriever,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Provider not configured" in page_text
    assert "Evidence retrieval unavailable" in page_text
    assert "No embedding provider key is configured" in page_text
    assert "Learning direction schemas" in page_text
    assert "Traceback" not in page_text


def test_noise_to_signal_direct_missing_provider_key_state_is_concise():
    mock_result = {
        "goal": "I want to learn RAG evaluation",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "failed",
        "retrieval_error": "provider_configuration_unavailable",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "Build a study plan for RAG evaluation.",
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [],
        "retrieval_trace": ["Retrieval attempt 1: failed."],
        "evidence_reason": (
            "Evidence retrieval unavailable. No embedding provider key is "
            "configured, so Cognivia cannot build or query the evidence index right now."
        ),
        "evidence": {"items": []},
        "study_plan": {"plan": "Practice RAG evaluation for 60 minutes."},
    }

    app = _run_noise_to_signal_app(mock_result, "I want to learn RAG evaluation")
    page_text = _page_text(app)

    assert not app.exception
    assert "Provider not configured" in page_text
    assert "Evidence retrieval unavailable" in page_text
    assert "No embedding provider key is configured" in page_text
    assert "Learning direction schemas" in page_text


def test_noise_to_signal_single_focus_qdrant_lock_result_shows_busy_warning():
    mock_result = {
        "goal": "I want to learn RAG evaluation",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "failed",
        "retrieval_error": "local_evidence_store_locked",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "Build a study plan for RAG evaluation.",
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [],
        "retrieval_trace": ["Retrieval attempt 1: failed."],
        "evidence_reason": (
            "The local evidence store is busy, so this run used a deterministic "
            "study-plan fallback."
        ),
        "evidence": {"items": []},
        "study_plan": {"plan": "Practice RAG evaluation for 60 minutes."},
    }

    app = _run_noise_to_signal_app(mock_result, "I want to learn RAG evaluation")
    page_text = _page_text(app)

    assert not app.exception
    assert "Unavailable" in page_text
    assert "The local evidence store is busy or unavailable" in page_text
    assert "Focused study sprint" in page_text
    assert "another instance of Qdrant client" not in page_text


def test_noise_to_signal_success_persists_learning_event_with_curated_evidence_refs():
    memory_store = RecordingMemoryStore()
    mock_result = {
        "goal": "Why is RAG evaluation useful?",
        "decision_status": "informational",
        "interaction_mode": "direct_decision",
        "evidence_quality": "sufficient",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "RAG evaluation helps measure answer quality.",
        "next_action": "Choose one evaluation checklist to build.",
        "decision_trace": ["User goal: Why is RAG evaluation useful?"],
        "retrieval_trace": ["Retrieval attempt 1: sufficient."],
        "evidence": {
            "items": [
                {
                    "source": "rag_eval.md",
                    "title": "RAG Evaluation Notes",
                    "source_type": "markdown",
                    "page": 2,
                    "chunk_index": 4,
                    "source_authority": "derived_official",
                    "excerpt": "Do not store this excerpt in memory.",
                    "page_content": "Do not store full text.",
                    "metadata": {"chunk_id": "chunk-4"},
                }
            ]
        },
        "study_plan": None,
    }

    app = _run_noise_to_signal_app(
        mock_result,
        "Why is RAG evaluation useful?",
        memory_store=memory_store,
    )

    assert not app.exception
    decision_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "noise_to_signal_decision"
    ]
    assert len(decision_events) == 1
    event = decision_events[0]
    assert event["event_type"] == "noise_to_signal_decision"
    assert event["learner_id"]
    assert event["user_goal"] == "Why is RAG evaluation useful?"
    assert event["selected_focus"] == "RAG evaluation"
    assert event["recommendation"] == "RAG evaluation helps measure answer quality."
    assert event["next_action"] == "Choose one evaluation checklist to build."
    assert event["decision_status"] == "informational"
    assert event["interaction_mode"] == "direct_decision"
    assert event["decision_trace"] == ["User goal: Why is RAG evaluation useful?"]
    assert event["evidence_refs"] == [
        {
            "source": "rag_eval.md",
            "title": "RAG Evaluation Notes",
            "page": 2,
            "chunk_index": 4,
            "source_authority": "derived_official",
            "source_type": "markdown",
            "chunk_id": "chunk-4",
            "authority": "derived_official",
        }
    ]
    assert "excerpt" not in event["evidence_refs"][0]
    assert "page_content" not in event["evidence_refs"][0]


def test_noise_to_signal_memory_failure_does_not_break_result_rendering():
    memory_store = RecordingMemoryStore(fail=True)
    mock_result = _single_focus_result()

    app = _run_noise_to_signal_app(
        mock_result,
        "I want to learn RAG evaluation",
        memory_store=memory_store,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Focused study sprint" in page_text
    assert "RAG evaluation" in page_text


def test_noise_to_signal_learning_direction_options_render_and_save_generated_event():
    memory_store = RecordingMemoryStore()

    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        memory_store=memory_store,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Recommendation summary" in page_text
    assert "Priority now" in page_text
    assert "Why now" in page_text
    assert "Next action" in page_text
    assert "Recommended direction" in page_text
    assert "Focused study sprint" in page_text
    assert "Piko tip:" in page_text
    assert "Turn this recommendation into one small study task for today." in page_text
    assert "Learning direction schemas" in page_text
    assert "1. Foundation-first path — Build the basics first" in page_text
    assert "2. Project-first path — Learn by shipping" in page_text
    assert "3. Interview/practical path — Prepare to explain tradeoffs" in page_text
    assert "You are here" in page_text
    assert "Learning path map" in page_text
    assert "First action" in page_text
    assert "Checkpoint" in page_text
    assert "Risk" in page_text
    assert "Choose a learning path first to unlock the mini notebook and exports." in page_text
    assert "Download full learning plan" not in page_text
    assert "Overview" in _tab_labels(app)
    assert "Learning paths" in _tab_labels(app)
    assert "Study note" in _tab_labels(app)
    assert "Evidence / technical" in _tab_labels(app)
    assert "Choose this path" in "\n".join(item.label for item in app.button)
    assert "download_full_learning_plan_markdown" not in str(app.session_state)
    generated_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "learning_direction_generated"
    ]
    assert len(generated_events) == 1
    generated_metadata = generated_events[0]["metadata"]
    assert len(generated_metadata["schemas"]) == 3
    assert generated_metadata["schema_ids"] == [
        "foundation_first",
        "project_first",
        "interview_practical",
    ]
    assert generated_metadata["schema_count"] == 3
    assert "schema" not in generated_metadata


def test_learning_direction_compact_view_restores_three_bounded_visual_maps():
    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        memory_store=RecordingMemoryStore(),
    )
    page_text = _page_text(app)
    expected_titles = (
        "1. Foundation-first path — Build the basics first",
        "2. Project-first path — Learn by shipping",
        "3. Interview/practical path — Prepare to explain tradeoffs",
    )
    path_maps = [
        str(item.value)
        for item in app.markdown
        if 'data-cognivia-learning-path-map="true"' in str(item.value)
    ]
    detail_disclosures = [
        str(item.value)
        for item in app.markdown
        if 'data-cognivia-learning-path-details="' in str(item.value)
    ]

    assert not app.exception
    assert all(page_text.count(title) == 1 for title in expected_titles)
    assert len(path_maps) == 3
    for path_map in path_maps:
        step_labels = [
            unescape(label)
            for label in re.findall(
                r'<span class="nts-learning-path-step-text">([^<]+)</span>',
                path_map,
            )
        ]
        assert 1 <= len(step_labels) <= 4
        assert all(len(label) <= 36 for label in step_labels)
        assert f'data-step-count="{len(step_labels)}"' in path_map
        assert "StartYou are here" not in path_map

    assert "Flow" not in page_text
    assert "Current state:" not in page_text
    assert "Target outcome:" not in page_text
    assert page_text.count("First action:") == 3
    assert page_text.count("Checkpoint:") == 3
    assert page_text.count("Risk:") == 3
    assert len(detail_disclosures) == 3
    assert {
        re.search(r'id="([^"]+)"', disclosure).group(1)
        for disclosure in detail_disclosures
    } == {
        "noise-to-signal-learning-path-details-foundation_first",
        "noise-to-signal-learning-path-details-project_first",
        "noise-to-signal-learning-path-details-interview_practical",
    }
    for disclosure in detail_disclosures:
        opening_tag = disclosure.split(">", 1)[0]
        assert opening_tag.startswith("<details ")
        assert " open" not in opening_tag
        assert disclosure.count("<summary>See step details</summary>") == 1
        assert disclosure.count("Starting context") == 1
        assert disclosure.count("Intended outcome") == 1


def test_learning_direction_display_normalization_enforces_content_limits():
    cognivia_app = import_module("app")
    schema = generate_learning_direction_schemas(
        "I want to learn RAG evaluation"
    )[0]
    long_words = " ".join(f"meaningful{i}" for i in range(30))
    long_schema = {
        **schema,
        "fit_reason": f"Best when {long_words}.",
        "nodes": [
            f"step{i} {long_words}"
            for i in range(6)
        ],
        "first_action": long_words,
        "checkpoint": long_words,
        "risk_or_gap": long_words,
    }
    original_nodes = list(long_schema["nodes"])

    compact = cognivia_app._normalize_learning_direction_for_display(long_schema)

    assert len(compact["best_when"]) <= cognivia_app.LEARNING_PATH_BEST_WHEN_MAX_CHARS
    assert len(compact["steps"]) == cognivia_app.LEARNING_PATH_MAX_STEPS
    assert all(
        len(step) <= cognivia_app.LEARNING_PATH_STEP_LABEL_MAX_CHARS
        for step in compact["steps"]
    )
    assert len(compact["first_action"]) <= (
        cognivia_app.LEARNING_PATH_FIRST_ACTION_MAX_CHARS
    )
    assert len(compact["checkpoint"]) <= (
        cognivia_app.LEARNING_PATH_CHECKPOINT_MAX_CHARS
    )
    assert len(compact["risk"]) <= cognivia_app.LEARNING_PATH_RISK_MAX_CHARS
    assert not compact["best_when"].lower().startswith("best when")
    assert all(
        value.removesuffix("…").split()[-1] in long_words.split()
        for value in (
            compact["best_when"],
            compact["first_action"],
            compact["checkpoint"],
            compact["risk"],
        )
    )
    assert long_schema["nodes"] == original_nodes
    assert long_schema["first_action"] == long_words


def test_learning_direction_details_are_native_client_only_and_backend_free():
    cognivia_app = import_module("app")
    render_source = getsource(cognivia_app._render_learning_direction_schema)
    details_source = getsource(cognivia_app._render_learning_path_details)
    normalize_source = getsource(
        cognivia_app._normalize_learning_direction_for_display
    )
    map_source = getsource(cognivia_app._render_learning_path_map)
    presentation_source = "\n".join(
        (render_source, details_source, normalize_source, map_source)
    )

    assert '_render_learning_path_details(schema["id"], details)' in render_source
    assert "st.expander(" not in presentation_source
    assert "'<details class=\"nts-learning-path-details\" '" in details_source
    assert '"<summary>See step details</summary>"' in details_source
    assert 'id="noise-to-signal-learning-path-details-' in details_source
    assert 'data-cognivia-learning-path-details="' in details_source
    assert "unsafe_allow_html=True" in details_source
    assert "st.rerun" not in presentation_source
    assert "<script" not in presentation_source
    assert "addEventListener" not in presentation_source
    for backend_call in (
        "run_noise_to_signal(",
        "generate_learning_direction_schemas(",
        "_save_learning_direction_event(",
        "_save_noise_to_signal_memory(",
        "retrieve_relevant_chunks(",
        "call_provider_chat(",
    ):
        assert backend_call not in presentation_source


def test_learning_direction_details_keep_native_accessibility_and_scoped_styles():
    cognivia_app = import_module("app")
    styles_source = getsource(cognivia_app._render_noise_to_signal_styles)
    details_source = getsource(cognivia_app._render_learning_path_details)

    assert "<details" in details_source
    assert "<summary>See step details</summary>" in details_source
    assert " open" not in details_source
    assert ".nts-learning-path-details > summary:focus-visible" in styles_source
    assert ".nts-learning-path-details[open] > summary" in styles_source
    assert ".nts-learning-path-details > summary::after" in styles_source
    assert ".nts-learning-path-details[open] > summary::after" in styles_source
    assert "transition:" not in styles_source.split(
        ".nts-learning-path-details {{", 1
    )[1].split(
        "div.st-key-noise_to_signal_results_panel p,", 1
    )[0]
    assert "animation:" not in styles_source.split(
        ".nts-learning-path-details {{", 1
    )[1].split(
        "div.st-key-noise_to_signal_results_panel p,", 1
    )[0]


def test_noise_to_signal_out_of_scope_prompt_does_not_render_learning_path_cards():
    app = _run_noise_to_signal_app(_out_of_scope_result(), "Tacos al Pastor")
    page_text = _page_text(app)

    assert not app.exception
    assert "No useful AI learning signal was detected" in page_text
    assert "Learning direction schemas" not in page_text
    assert "Foundation-first path" not in page_text
    assert "Project-first path" not in page_text
    assert "Interview/practical path" not in page_text
    assert "Overview" in _tab_labels(app)
    assert "Learning paths" in _tab_labels(app)


def test_noise_to_signal_out_of_scope_prompt_does_not_render_path_buttons():
    app = _run_noise_to_signal_app(_out_of_scope_result(), "Tacos al Pastor")
    button_labels = "\n".join(item.label for item in app.button)

    assert not app.exception
    assert "Choose this path" not in button_labels
    assert "Download full learning plan" not in _page_text(app)
    assert "download_full_learning_plan_markdown" not in str(app.session_state)


def test_noise_to_signal_out_of_scope_prompt_clears_stale_selected_path():
    memory_store = RecordingMemoryStore()

    def select_and_type_note(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        app.text_input(key="noise_to_signal_learning_note_title").set_value(
            "Old path note"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)

    app = _run_noise_to_signal_app_sequence(
        [
            ("I want to learn RAG evaluation", _single_focus_result(), select_and_type_note),
            ("Tacos al Pastor", _out_of_scope_result(), None),
        ],
        memory_store=memory_store,
    )[0]
    page_text = _page_text(app)

    assert not app.exception
    assert "noise_to_signal_selected_learning_schema_id" not in app.session_state
    assert "noise_to_signal_learning_note_title" not in app.session_state
    assert "Old path note" not in page_text
    assert "Save a reflection for this path" not in page_text
    assert "Choose a generated learning path before saving a study note." in page_text
    assert "download_full_learning_plan_markdown" not in app.session_state


def test_noise_to_signal_valid_prompts_still_render_learning_paths_when_evidence_is_low():
    prompts = [
        "Should I learn LangGraph or RAG evaluation?",
        "How do I move from backend to AI engineering?",
    ]

    for prompt in prompts:
        app = _run_noise_to_signal_app(_out_of_scope_result(prompt), prompt)
        page_text = _page_text(app)

        assert not app.exception
        assert "Learning direction schemas" in page_text
        assert "Foundation-first path" in page_text
        assert "Choose this path" in "\n".join(item.label for item in app.button)


def test_decision_learning_paths_use_the_structured_recommended_alternative():
    decision_goal = "Should I learn LangGraph or RAG evaluation?"

    for selected_focus in ("RAG evaluation", "LangGraph"):
        result = _single_focus_result(decision_goal)
        result.update(
            {
                "evidence_quality": "sufficient",
                "selected_focus": selected_focus,
                "recommendation": f"Prioritize {selected_focus}.",
                "next_action": f"Start one focused {selected_focus} exercise.",
                "study_plan": {"plan": f"Practice {selected_focus} for 60 minutes."},
            }
        )

        def select_project_first(app):
            app.button(
                key="noise_to_signal_select_learning_schema_project_first"
            ).click().run(timeout=APP_TEST_TIMEOUT_SECONDS)

        app, graph_stub = _run_noise_to_signal_app_sequence(
            [(decision_goal, result, select_project_first)],
            memory_store=RecordingMemoryStore(),
        )
        schemas = app.session_state["noise_to_signal_learning_direction_schemas"]
        schema_text = "\n".join(
            str(value)
            for schema in schemas
            for value in schema.values()
        )
        page_text = _page_text(app)

        assert not app.exception
        assert len(graph_stub.calls) == 1
        assert app.session_state["noise_to_signal_learning_direction_goal"] == (
            selected_focus
        )
        assert [schema["id"] for schema in schemas] == [
            "foundation_first",
            "project_first",
            "interview_practical",
        ]
        assert selected_focus in schema_text
        assert decision_goal not in schema_text
        assert "LangGraph vs RAG evaluation" not in schema_text
        assert all(
            schema["current_state"]
            == f"Recommended focus: {selected_focus}; evidence: sufficient."
            for schema in schemas
        )
        assert (
            app.session_state["noise_to_signal_selected_learning_schema_id"]
            == "project_first"
        )
        assert f"Prioritize {selected_focus}." in page_text
        assert "Learning direction schemas" in page_text
        assert "Foundation-first path" in page_text
        assert "Project-first path" in page_text
        assert "Interview/practical path" in page_text
        assert "Learning path map" in page_text
        assert "Selected path: 2. Project-first path" in page_text
        for visible_section in (
            "Priority now",
            "Why now",
            "Next action",
            "Recommended direction",
            "Focused study sprint",
            "Recommendation summary",
        ):
            assert visible_section in page_text


def test_standalone_learning_request_keeps_its_original_learning_subject():
    goal = "Build a RAG roadmap"
    result = _single_focus_result(goal)
    result.update(
        {
            "selected_focus": None,
            "recommendation": "Build a practical RAG roadmap.",
            "next_action": "Choose the first roadmap milestone.",
        }
    )

    def select_foundation_first(app):
        app.button(
            key="noise_to_signal_select_learning_schema_foundation_first"
        ).click().run(timeout=APP_TEST_TIMEOUT_SECONDS)

    app, graph_stub = _run_noise_to_signal_app_sequence(
        [(goal, result, select_foundation_first)],
        memory_store=RecordingMemoryStore(),
    )
    schemas = app.session_state["noise_to_signal_learning_direction_schemas"]
    schema_text = "\n".join(
        str(value)
        for schema in schemas
        for value in schema.values()
    )

    assert not app.exception
    assert len(graph_stub.calls) == 1
    assert app.session_state["noise_to_signal_learning_direction_goal"] == goal
    assert "RAG" in schema_text
    assert "LangGraph vs RAG evaluation" not in schema_text
    assert "Learning direction schemas" in _page_text(app)
    assert "Learning path map" in _page_text(app)


def test_noise_to_signal_study_note_remains_locked_for_out_of_scope_prompt():
    app = _run_noise_to_signal_app(_out_of_scope_result(), "Tacos al Pastor")
    page_text = _page_text(app)
    app_state = str(app.session_state)

    assert not app.exception
    assert "Choose a generated learning path before saving a study note." in page_text
    assert "Save a reflection for this path" not in page_text
    assert "download_learning_reflection_markdown" not in app_state
    assert "download_learning_reflection_json" not in app_state
    assert "download_full_learning_plan_markdown" not in app_state


def test_noise_to_signal_learning_direction_selection_records_state_and_event():
    memory_store = RecordingMemoryStore()
    app, graph_stub = _run_noise_to_signal_app_sequence(
        [
            (
                "I want to learn RAG evaluation",
                _single_focus_result(),
                None,
            )
        ],
        memory_store=memory_store,
    )
    graph_calls_before_selection = len(graph_stub.calls)

    app.button(
        key="noise_to_signal_select_learning_schema_project_first"
    ).click().run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    page_text = _page_text(app)
    summary_directions = [
        str(item.value)
        for item in app.markdown
        if str(item.value).startswith("**Direction:**")
    ]
    stored_schemas = app.session_state["noise_to_signal_learning_direction_schemas"]
    selected_schema = next(
        schema for schema in stored_schemas if schema["id"] == "project_first"
    )
    assert app.session_state["noise_to_signal_selected_learning_schema_id"] == "project_first"
    assert summary_directions == ["**Direction:** Project-first path"]
    assert "**Direction:** RAG evaluation" not in summary_directions
    assert "Selected path: 2. Project-first path — Learn by shipping" in page_text
    assert "Save a reflection for this path" in page_text
    assert "download_full_learning_plan_markdown" in str(app.session_state)
    assert len(graph_stub.calls) == graph_calls_before_selection
    selected_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "learning_direction_selected"
    ]
    assert len(selected_events) == 1
    assert selected_events[0]["recommended_direction"] == "Project-first path"
    assert selected_events[0]["metadata"]["schema"] == selected_schema


def test_noise_to_signal_full_learning_plan_markdown_includes_required_sections():
    def select_project_first(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        after_decision=select_project_first,
        memory_store=RecordingMemoryStore(),
    )
    markdown = app.session_state["noise_to_signal_full_learning_plan_markdown"]

    assert not app.exception
    for expected_text in [
        "Cognivia Learning Plan",
        "Learning goal",
        "Recommendation summary",
        "Selected learning path",
        "Learning path map",
        "Study method",
        "20-hour focused learning plan",
        "One-page study sheet",
        "Five-level learning ladder",
        "Mastery quiz",
        "Feynman loop",
        "Feynman Technique](https://fs.blog/feynman-technique/)",
        "Session reflection",
    ]:
        assert expected_text in markdown
    assert "RAG evaluation" in markdown
    assert "I want to learn RAG evaluation" not in markdown
    assert "Project-first path" in markdown
    assert "Start → First action → Practice → Checkpoint → Outcome" in markdown


def test_full_learning_plan_download_uses_canonical_export_contract():
    cognivia_app = import_module("app")
    canonical_schema = generate_learning_direction_schemas(
        "I want to learn RAG evaluation",
        _single_focus_result(),
    )[1]
    canonical_schema = {
        **canonical_schema,
        "nodes": [
            *canonical_schema["nodes"],
            "Canonical advanced practice step retained only in the complete export",
        ],
        "first_action": (
            "Canonical first action that deliberately exceeds the compact presentation "
            "limit and must remain complete in the downloaded learning plan."
        ),
        "checkpoint": (
            "Canonical checkpoint that deliberately exceeds the compact presentation "
            "limit and must remain complete in the downloaded learning plan."
        ),
        "target_outcome": (
            "Canonical expected outcome retained from the original selected schema."
        ),
    }
    decision = {
        **_single_focus_result(),
        "recommendation": "Generated recommendation preserved in the complete export.",
    }
    note = {
        "title": "Export reflection",
        "reflection": "Reflection belongs only in section eight.",
        "tags": ["export-contract"],
    }
    compact = cognivia_app._normalize_learning_direction_for_display(canonical_schema)
    session_state = {}

    with (
        patch.object(cognivia_app.st, "session_state", session_state),
        patch.object(cognivia_app.st, "download_button") as download_button,
    ):
        cognivia_app._render_full_learning_plan_download(
            goal="I want to learn RAG evaluation",
            decision=decision,
            selected_schema=canonical_schema,
            note=note,
        )

    download_button.assert_called_once()
    call = download_button.call_args
    markdown = call.kwargs["data"]
    expected_headings = [
        "## 1. Learning goal",
        "## 2. Recommendation summary",
        "## 3. Why this path",
        "## 4. Selected learning path",
        "## 5. Learning path map",
        "## 6. Study method",
        "## 7. Today’s first study session",
        "## 8. Reflection",
    ]

    assert call.args == (cognivia_app.FULL_LEARNING_PLAN_DOWNLOAD_LABEL,)
    assert call.kwargs["file_name"] == "cognivia-learning-plan.md"
    assert call.kwargs["mime"] == "text/markdown"
    assert call.kwargs["key"] == "download_full_learning_plan_markdown"
    assert call.kwargs["on_click"] == "ignore"
    heading_positions = [markdown.index(heading) for heading in expected_headings]
    assert heading_positions == sorted(heading_positions)
    assert "Generated recommendation preserved in the complete export." in markdown
    assert canonical_schema["title"] in markdown
    assert canonical_schema["first_action"] in markdown
    assert canonical_schema["checkpoint"] in markdown
    assert canonical_schema["target_outcome"] in markdown
    assert canonical_schema["nodes"][-1] in markdown
    assert compact["first_action"] != canonical_schema["first_action"]
    assert markdown.count(note["reflection"]) == 1
    assert markdown.index(note["reflection"]) > markdown.index("## 8. Reflection")
    assert session_state[cognivia_app.FULL_LEARNING_PLAN_MARKDOWN_SESSION_KEY] == (
        markdown
    )


def test_reflection_download_cannot_replace_full_learning_plan_download():
    cognivia_app = import_module("app")
    payload = {
        "exported_at": "2026-07-28T18:00:00+00:00",
        "goal": "I want to learn RAG evaluation",
        "selected_path": {
            "id": "project_first",
            "title": "Project-first path",
            "subtitle": "Learn by shipping",
        },
        "note": {
            "title": "Reflection",
            "reflection": "Reflection-only export content.",
            "tags": [],
        },
        "first_action": "Build one working slice.",
        "checkpoint": "Explain the evaluation result.",
    }

    with (
        patch.object(cognivia_app.st, "caption"),
        patch.object(cognivia_app.st, "download_button") as download_button,
    ):
        cognivia_app._render_learning_note_exports(payload)

    markdown_call = download_button.call_args_list[0]
    reflection_markdown = markdown_call.kwargs["data"]

    assert markdown_call.args == ("Download reflection Markdown",)
    assert markdown_call.kwargs["file_name"] == "cognivia-reflection.md"
    assert markdown_call.kwargs["mime"] == "text/markdown"
    assert markdown_call.kwargs["key"] == "download_learning_reflection_markdown"
    assert markdown_call.kwargs["on_click"] == "ignore"
    assert reflection_markdown == cognivia_app.build_learning_reflection_markdown(
        payload
    )
    assert reflection_markdown.startswith("# Cognivia reflection")
    assert "## 1. Learning goal" not in reflection_markdown
    assert "## 8. Reflection" not in reflection_markdown
    assert reflection_markdown != cognivia_app.build_full_learning_plan_markdown(
        goal=payload["goal"],
        decision=_single_focus_result(),
        selected_schema=generate_learning_direction_schemas(
            payload["goal"],
            _single_focus_result(),
        )[1],
        note=payload["note"],
    )


def test_noise_to_signal_learning_direction_selection_survives_rerun():
    memory_store = RecordingMemoryStore()

    def select_and_rerun(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        after_decision=select_and_rerun,
        memory_store=memory_store,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert app.session_state["noise_to_signal_selected_learning_schema_id"] == "project_first"
    assert "Selected path: 2. Project-first path — Learn by shipping" in page_text
    assert "Save a reflection for this path" in page_text


def test_noise_to_signal_new_prompt_clears_previous_selected_path_and_note_state():
    memory_store = RecordingMemoryStore()
    first_result = _single_focus_result("I want to learn RAG evaluation")
    second_result = {
        "goal": "How do I move from backend to AI engineering?",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "contextual",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "backend-to-AI engineering transition",
        "recommendation": "Build from backend APIs into LLM application engineering.",
        "next_action": "Map one backend API skill to one LLM app integration.",
        "decision_trace": [],
        "retrieval_trace": [],
        "evidence": {"items": []},
        "study_plan": None,
    }

    def select_and_type_note(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        app.text_input(key="noise_to_signal_learning_note_title").set_value(
            "Old path note"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)

    app = _run_noise_to_signal_app_sequence(
        [
            ("I want to learn RAG evaluation", first_result, select_and_type_note),
            ("How do I move from backend to AI engineering?", second_result, None),
        ],
        memory_store=memory_store,
    )[0]
    page_text = _page_text(app)

    assert not app.exception
    assert "noise_to_signal_selected_learning_schema_id" not in app.session_state
    assert "noise_to_signal_learning_note_title" not in app.session_state
    assert "Old path note" not in page_text
    assert "Choose a learning path first to unlock the mini notebook and exports." in page_text
    assert "backend-to-AI engineering transition" in page_text
    assert app.session_state["noise_to_signal_learning_direction_goal"] == (
        "backend-to-AI engineering transition"
    )
    latest_schema_text = "\n".join(
        str(value)
        for schema in app.session_state[
            "noise_to_signal_learning_direction_schemas"
        ]
        for value in schema.values()
    )
    assert "RAG evaluation: retrieval relevance" not in latest_schema_text


def test_noise_to_signal_learning_note_save_records_memory_event():
    memory_store = RecordingMemoryStore()

    def save_note(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        app.text_input(key="noise_to_signal_learning_note_title").set_value(
            "My project path"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.text_area(key="noise_to_signal_learning_note_body").set_value(
            "I learn best by building a small retrieval evaluation demo first."
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.text_input(key="noise_to_signal_learning_note_tags").set_value(
            "rag, portfolio"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.button(key="noise_to_signal_save_learning_note").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        after_decision=save_note,
        memory_store=memory_store,
    )
    page_text = _page_text(app)

    assert not app.exception
    note_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "learning_note_saved"
    ]
    assert len(note_events) == 1
    assert note_events[0]["recommended_direction"] == "Project-first path"
    assert note_events[0]["metadata"]["note_title"] == "My project path"
    assert note_events[0]["metadata"]["note_body"].startswith("I learn best")
    assert note_events[0]["metadata"]["tags"] == ["rag", "portfolio"]
    assert "Saved to learner memory." in page_text
    assert "View recent notes in Recent learner memory / Memory history." in page_text
    assert "Markdown export and JSON export for your selected path." in page_text
    app_state = str(app.session_state)
    assert "download_learning_reflection_markdown" in app_state
    assert "download_learning_reflection_json" in app_state


def test_noise_to_signal_learning_note_memory_failure_is_fail_soft():
    def save_note(app):
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )
        app.text_input(key="noise_to_signal_learning_note_title").set_value(
            "My project path"
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.text_area(key="noise_to_signal_learning_note_body").set_value(
            "I learn best by building a small retrieval evaluation demo first."
        ).run(timeout=APP_TEST_TIMEOUT_SECONDS)
        app.button(key="noise_to_signal_save_learning_note").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        after_decision=save_note,
        memory_store=RecordingMemoryStore(fail=True),
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Selected path: 2. Project-first path — Learn by shipping" in page_text
    assert "Saved to local session memory. Configure DATABASE_URL for durable memory." in page_text
    assert "download_learning_reflection_markdown" in str(app.session_state)


def test_noise_to_signal_learning_direction_memory_failure_does_not_break_ui():
    app = _run_noise_to_signal_app(
        _single_focus_result(),
        "I want to learn RAG evaluation",
        memory_store=RecordingMemoryStore(fail=True),
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Learning direction schemas" in page_text
    assert "Foundation-first path" in page_text


def test_noise_to_signal_guided_intake_persists_profile_and_event():
    memory_store = RecordingMemoryStore()
    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
        memory_store=memory_store,
    )

    assert not app.exception
    assert len(memory_store.saved_profiles) == 1
    guided_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "guided_intake_recommendation"
    ]
    assert len(guided_events) == 1
    profile_save = memory_store.saved_profiles[0]
    event = guided_events[0]
    assert profile_save["learner_id"] == event["learner_id"]
    assert profile_save["profile"]["goal"] == "What should I study next?"
    assert event["event_type"] == "guided_intake_recommendation"
    assert event["learner_profile"] == profile_save["profile"]
    assert event["profile_id"] == "profile-1"
    assert event["user_goal"] == "What should I study next?"
    assert event["recommended_direction"]
    assert event["next_action"]
    assert event["interaction_mode"] == "noise_to_signal_guided_intake"
    assert event["metadata"]["profile_id"] == "profile-1"


def test_noise_to_signal_guided_intake_renders_learning_direction_options():
    memory_store = RecordingMemoryStore()
    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=_complete_guided_intake,
        memory_store=memory_store,
    )
    page_text = _page_text(app)

    assert not app.exception
    assert page_text.count("Recommendation summary") == 1
    assert "A little more context is needed" not in page_text
    assert _tab_labels(app).splitlines() == [
        "Overview",
        "Learning paths",
        "Study note",
        "Evidence / technical",
    ]
    assert page_text.count("Learning direction schemas") == 1
    assert "Foundation-first path" in page_text
    assert app.session_state["noise_to_signal_learning_direction_goal"] == (
        "What should I study next?"
    )
    assert any(
        event["event_type"] == "learning_direction_generated"
        for event in memory_store.saved_events
    )


def test_noise_to_signal_guided_intake_selection_stays_on_generated_path():
    memory_store = RecordingMemoryStore()

    def complete_and_select(app):
        _complete_guided_intake(app)
        app.button(key="noise_to_signal_select_learning_schema_project_first").click().run(
            timeout=APP_TEST_TIMEOUT_SECONDS
        )

    app = _run_noise_to_signal_app(
        _guided_intake_result(
            "What should I study next?",
            "I want to choose what to learn next",
        ),
        "What should I study next?",
        after_decision=complete_and_select,
        memory_store=memory_store,
    )
    page_text = _page_text(app)
    summary_directions = [
        str(item.value)
        for item in app.markdown
        if str(item.value).startswith("**Direction:**")
    ]

    assert not app.exception
    assert "Recommended direction" in page_text
    assert summary_directions == ["**Direction:** Project-first path"]
    assert "Selected path: 2. Project-first path — Learn by shipping" in page_text
    assert "Save a reflection for this path" in page_text


def test_noise_to_signal_demo_learner_id_is_stable_during_session():
    memory_store = RecordingMemoryStore()
    app, _ = _run_noise_to_signal_app_sequence(
        [
            (
                "I want to learn RAG evaluation",
                {
                    "goal": "I want to learn RAG evaluation",
                    "decision_status": "single_focus",
                    "interaction_mode": "direct_decision",
                    "evidence_quality": "contextual",
                    "retrieval_attempts": 1,
                    "query_reformulated": False,
                    "selected_focus": "RAG evaluation",
                    "recommendation": "Build a study plan for RAG evaluation.",
                    "next_action": "Use the plan as a learning scaffold.",
                    "decision_trace": [],
                    "retrieval_trace": [],
                    "evidence": {"items": []},
                    "study_plan": None,
                },
                None,
            ),
            (
                "Why is RAG evaluation useful?",
                {
                    "goal": "Why is RAG evaluation useful?",
                    "decision_status": "informational",
                    "interaction_mode": "direct_decision",
                    "evidence_quality": "sufficient",
                    "retrieval_attempts": 1,
                    "query_reformulated": False,
                    "selected_focus": None,
                    "recommendation": "RAG evaluation helps measure quality.",
                    "next_action": "Choose one checklist to build.",
                    "decision_trace": [],
                    "retrieval_trace": [],
                    "evidence": {"items": []},
                    "study_plan": None,
                },
                None,
            ),
        ],
        memory_store=memory_store,
    )

    assert not app.exception
    decision_events = [
        event
        for event in memory_store.saved_events
        if event["event_type"] == "noise_to_signal_decision"
    ]
    assert len(decision_events) == 2
    assert decision_events[0]["learner_id"] == decision_events[1][
        "learner_id"
    ]


def test_noise_to_signal_recent_memory_history_renders_when_available():
    memory_store = RecordingMemoryStore(
        recent_events=[
            {
                "event_type": "guided_intake_recommendation",
                "user_goal": "Find a practical AI learning path",
                "recommended_direction": "RAG evaluation portfolio",
                "selected_focus": "RAG evaluation",
                "next_action": "Build a retrieval evaluation checklist.",
                "created_at": "2026-07-10T09:30:00+00:00",
            }
        ]
    )

    app, _ = _run_noise_to_signal_app_sequence([], memory_store=memory_store)
    page_text = _page_text(app)

    assert not app.exception
    assert "Learner memory" in page_text
    assert "Current direction" in page_text
    assert "RAG evaluation portfolio" in page_text
    assert "Build a retrieval evaluation checklist." in page_text
    assert "Guided intake recommendation" in page_text
    assert "2026-07-10 09:30:00 UTC" in page_text
    assert _has_learner_memory_download_button(app)


def test_noise_to_signal_memory_export_button_renders_with_profile_only():
    memory_store = RecordingMemoryStore(
        latest_profile={
            "goal": "Build a RAG portfolio project",
            "current_level": "beginner",
        }
    )

    app, _ = _run_noise_to_signal_app_sequence([], memory_store=memory_store)
    page_text = _page_text(app)

    assert not app.exception
    assert "Learner memory" in page_text
    assert "Recent learning history" not in page_text
    assert _has_learner_memory_download_button(app)


def test_noise_to_signal_latest_memory_event_drives_current_direction():
    memory_store = RecordingMemoryStore(
        recent_events=[
            {
                "event_type": "noise_to_signal_decision",
                "user_goal": "Choose my next focus",
                "recommended_direction": "LangGraph agents",
                "selected_focus": "Agents",
                "next_action": "Build one graph with two tools.",
            },
            {
                "event_type": "noise_to_signal_decision",
                "user_goal": "Start with RAG",
                "recommended_direction": "RAG basics",
                "selected_focus": "RAG",
                "next_action": "Read the retrieval notes.",
            },
        ]
    )

    app, _ = _run_noise_to_signal_app_sequence([], memory_store=memory_store)
    page_text = _page_text(app)

    assert not app.exception
    assert page_text.find("LangGraph agents") < page_text.find("RAG basics")
    assert page_text.find("Build one graph with two tools.") < page_text.find(
        "Read the retrieval notes."
    )


def test_noise_to_signal_empty_memory_does_not_render_history_section():
    app, _ = _run_noise_to_signal_app_sequence([], memory_store=RecordingMemoryStore())
    page_text = _page_text(app)

    assert not app.exception
    assert "Learner memory" not in page_text
    assert not _has_learner_memory_download_button(app)


def test_noise_to_signal_memory_read_failure_does_not_crash_app():
    app, _ = _run_noise_to_signal_app_sequence(
        [],
        memory_store=RecordingMemoryStore(fail_reads=True),
    )
    page_text = _page_text(app)

    assert not app.exception
    assert "Learner memory" not in page_text
    assert "memory unavailable" not in page_text
    assert not _has_learner_memory_download_button(app)


def test_noise_to_signal_memory_display_does_not_change_graph_prompt_payload():
    memory_store = RecordingMemoryStore(
        recent_events=[
            {
                "event_type": "noise_to_signal_decision",
                "user_goal": "Earlier goal",
                "recommended_direction": "Earlier direction",
                "next_action": "Earlier next action.",
            }
        ]
    )
    mock_result = {
        "goal": "I want to learn RAG evaluation",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "contextual",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": "Build a study plan for RAG evaluation.",
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [],
        "retrieval_trace": [],
        "evidence": {"items": []},
        "study_plan": None,
    }

    app, graph_stub = _run_noise_to_signal_app_sequence(
        [("I want to learn RAG evaluation", mock_result, None)],
        memory_store=memory_store,
    )

    assert not app.exception
    assert graph_stub.calls
    args, kwargs = graph_stub.calls[0]
    assert args == ("I want to learn RAG evaluation",)
    assert set(kwargs) == {"thread_id"}


def test_noise_to_signal_app_renders_representative_informational_result():
    mock_result = {
        "decision_status": "informational",
        "evidence_quality": "sufficient",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": (
            "Based on the retrieved evidence: RAG evaluation helps AI engineers "
            "measure retrieval relevance, answer quality, and source grounding."
        ),
        "next_action": (
            "Choose one identified skill to compare against your current goals."
        ),
        "decision_trace": [
            "User goal: Why is RAG evaluation useful?",
            "Retrieval attempt 1: sufficient.",
            "Decision status: informational",
            "Short evidence-based reasoning: The user asked an informational question, so the response answers from retrieved evidence.",
            "Selected focus: none",
            "Next action: Choose one identified skill to compare against your current goals.",
        ],
        "retrieval_trace": ["Retrieval attempt 1: sufficient."],
        "evidence": {
            "items": [
                {
                    "title": "RAG Evaluation Notes",
                    "source_type": "markdown",
                    "type_label": "Markdown",
                    "excerpt": (
                        "RAG evaluation helps measure retrieval relevance, "
                        "answer quality, and source grounding."
                    ),
                }
            ]
        },
        "study_plan": {
            "plan": "Spend 60 minutes building a small RAG evaluation checklist."
        },
    }

    app = _run_noise_to_signal_app(
        mock_result,
        "Why is RAG evaluation useful?",
    )

    page_text = _page_text(app)

    assert not app.exception
    assert "Why Cognivia recommended this" in _expander_labels(app)
    assert "Why now" in page_text
    assert "Next action" in page_text
    assert "Recommended direction" in page_text
    assert "What this means" in page_text
    assert "Evidence" in page_text
    assert "Retrieval attempts" in page_text
    assert "Type: Markdown" in page_text
    assert "Answered" in page_text
    assert "Sufficient" in page_text
    assert "1" in page_text
    assert "RAG evaluation" in page_text
    assert "Based on the retrieved evidence" in page_text
    assert "Choose one identified skill" in page_text


def test_noise_to_signal_app_renders_concrete_topic_study_plan():
    mock_result = {
        "goal": "I want to learn RAG evaluation",
        "decision_status": "single_focus",
        "interaction_mode": "direct_decision",
        "evidence_quality": "contextual",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": "RAG evaluation",
        "recommendation": (
            "Build a study plan for RAG evaluation. This plan is not strongly "
            "evidence-grounded unless retrieved evidence is shown below."
        ),
        "next_action": "Use the plan as a learning scaffold.",
        "decision_trace": [
            "User goal: I want to learn RAG evaluation",
            "Decision status: single_focus",
            "Short evidence-based reasoning: The user provided one explicit topic: RAG evaluation.",
            "Selected focus: RAG evaluation",
            "Next action: Use the plan as a learning scaffold.",
        ],
        "retrieval_trace": [],
        "evidence": {"items": []},
        "study_plan": {
            "plan": "Spend 60 minutes building a small RAG evaluation checklist."
        },
    }

    app = _run_noise_to_signal_app(mock_result, "I want to learn RAG evaluation")
    page_text = _page_text(app)

    assert not app.exception
    assert "Focused study sprint" in page_text
    assert "RAG evaluation" in page_text
    assert "Contextual" in page_text
    assert "Sufficient" not in page_text
    assert "Guided intake" not in page_text


def test_noise_to_signal_app_renders_clearer_out_of_scope_message_and_label():
    mock_result = {
        "decision_status": "insufficient_evidence",
        "evidence_quality": "weak",
        "retrieval_attempts": 1,
        "query_reformulated": False,
        "selected_focus": None,
        "recommendation": (
            "The retrieved evidence is insufficient to answer this question reliably. "
            "Refine the question or add evidence that directly addresses the topic."
        ),
        "next_action": "Try an AI engineering topic with direct supporting evidence.",
        "decision_trace": [],
        "retrieval_trace": ["Retrieval attempt 1: weak - focus is outside scope and not directly supported."],
        "evidence_reason": (
            "The focus appears outside the AI Engineering learning scope, "
            "and retrieved evidence does not directly support the topic."
        ),
        "evidence": {"items": []},
        "study_plan": None,
    }

    app = _run_noise_to_signal_app(mock_result, "Tacos al pastor")

    page_text = _page_text(app)
    expander_labels = "\n".join(item.label for item in app.expander)

    assert not app.exception
    assert "Insufficient evidence" in page_text
    assert (
        "The focus appears outside the AI Engineering learning scope, and retrieved evidence does not directly support the topic."
        in page_text
    )
    assert "Focused study sprint" not in expander_labels
    assert "Decision trace" not in expander_labels
    assert "Technical details" in expander_labels


def test_noise_to_signal_does_not_render_checkbox_background_panel():
    app, _ = _run_noise_to_signal_app_sequence([], memory_store=RecordingMemoryStore())
    app.run(timeout=APP_TEST_TIMEOUT_SECONDS)

    assert not app.exception
    assert "Display options" not in _expander_labels(app)
    assert not [
        checkbox
        for checkbox in app.checkbox
        if checkbox.label in {"Show visual background", "Play video background"}
    ]
