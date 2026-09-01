import openrouter_client
import streamlit as st

from openrouter_client import OpenRouterError
from prompts import SYSTEM_PROMPTS
from security import validate_job_description, validate_user_input


INTERVIEW_MODEL_OPTIONS = {
    "GPT-5 mini (recommended)": "openai/gpt-5-mini",
    "GPT-5 nano (cheaper)": "openai/gpt-5-nano",
    "MiniMax M2.7 (dev alternative)": "minimax/minimax-m2.7",
}
INTERVIEW_MODEL_TEMPERATURE_POLICY = {
    INTERVIEW_MODEL_OPTIONS["GPT-5 mini (recommended)"]: None,
    INTERVIEW_MODEL_OPTIONS["GPT-5 nano (cheaper)"]: None,
    INTERVIEW_MODEL_OPTIONS["MiniMax M2.7 (dev alternative)"]: 1.0,
}
INTERVIEW_MODEL_SESSION_KEY = "interview_coach_model"
INTERVIEW_MAX_TOKENS_SESSION_KEY = "interview_coach_max_tokens"
INTERVIEW_MAX_TOKENS_OVERRIDDEN_SESSION_KEY = (
    "interview_coach_max_tokens_overridden"
)


def _interview_request_kwargs(
    model: str,
    max_tokens: int,
) -> dict[str, str | int | float]:
    if model not in INTERVIEW_MODEL_TEMPERATURE_POLICY:
        raise ValueError(f"Unsupported Interview Coach model: {model}")

    request_kwargs: dict[str, str | int | float] = {
        "model": model,
        "max_tokens": max_tokens,
    }
    temperature = INTERVIEW_MODEL_TEMPERATURE_POLICY[model]
    if temperature is not None:
        request_kwargs["temperature"] = temperature
    return request_kwargs


def _interview_default_max_tokens(number_of_questions: int) -> int:
    if number_of_questions == 1:
        return 1200
    if number_of_questions <= 3:
        return 1800
    return 3000


def _synchronize_interview_max_tokens(default_max_tokens: int) -> None:
    if INTERVIEW_MAX_TOKENS_SESSION_KEY not in st.session_state:
        st.session_state[INTERVIEW_MAX_TOKENS_SESSION_KEY] = default_max_tokens
        st.session_state[INTERVIEW_MAX_TOKENS_OVERRIDDEN_SESSION_KEY] = False
    elif not st.session_state.get(
        INTERVIEW_MAX_TOKENS_OVERRIDDEN_SESSION_KEY,
        False,
    ):
        st.session_state[INTERVIEW_MAX_TOKENS_SESSION_KEY] = default_max_tokens


def _mark_interview_max_tokens_overridden() -> None:
    st.session_state[INTERVIEW_MAX_TOKENS_OVERRIDDEN_SESSION_KEY] = True


def _render_interview_coach() -> None:
    st.title("Developer Interview Decision Coach")
    st.write(
        "Prepare for developer interviews by practicing questions, trade-offs, "
        "and decision-making explanations."
    )

    role = st.text_input("Target role", "Python Backend Developer")

    job_description = st.text_area(
        "Job description (optional)",
        placeholder="Paste the job description here...",
    )

    level = st.selectbox("Developer level", ["Junior", "Mid I", "Mid II", "Senior"])

    topic = st.selectbox(
        "Interview topic",
        [
            "Software Architecture",
            "Design Patterns",
            "Python",
            "JavaScript",
            "System Design",
            "Behavioral",
            "Critical Thinking & Trade-offs",
        ],
    )

    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    number_of_questions = st.slider(
        "Number of questions",
        min_value=1,
        max_value=5,
        value=1,
        step=1,
    )

    default_max_tokens = _interview_default_max_tokens(number_of_questions)
    _synchronize_interview_max_tokens(default_max_tokens)

    prompt_options = list(SYSTEM_PROMPTS.keys())
    prompt_technique = st.selectbox(
        "Prompt technique",
        prompt_options,
        index=prompt_options.index("Best Coach (Combined)"),
    )

    def build_interview_prompt(
        role,
        level,
        topic,
        difficulty,
        number_of_questions,
        job_description=None,
    ):
        job_description_section = ""

        if job_description and job_description.strip():
            job_description_section = f"""
            Job description:
            {job_description.strip()}
            """
        return f"""
        You are helping me prepare for a developer interview.

        Target role: {role}
        Developer level: {level}
        Topic: {topic}
        Difficulty: {difficulty}
        {job_description_section}
        Generate {number_of_questions} interview questions.

        For each question, include:
        1. The question
        2. What the interviewer is testing
        3. What a strong answer should include
        4. A common mistake
        5. One follow-up question
        """

    selected_model_label = st.sidebar.selectbox(
        "Model",
        list(INTERVIEW_MODEL_OPTIONS.keys()),
        key=INTERVIEW_MODEL_SESSION_KEY,
    )

    selected_model = INTERVIEW_MODEL_OPTIONS[selected_model_label]

    st.sidebar.caption(f"Using: {selected_model}")

    max_tokens = st.sidebar.slider(
        "Max tokens",
        min_value=1000,
        max_value=3000,
        step=100,
        key=INTERVIEW_MAX_TOKENS_SESSION_KEY,
        on_change=_mark_interview_max_tokens_overridden,
    )

    st.sidebar.caption("Max tokens: answer length")

    if st.button("Generate interview prompt"):
        is_valid, error_message = validate_user_input(role)

        if not is_valid:
            st.error(error_message)
        else:
            is_valid_jd, error_message_jd = validate_job_description(job_description)

            if not is_valid_jd:
                st.error(error_message_jd)
            else:
                system_prompt = SYSTEM_PROMPTS[prompt_technique]

                user_prompt = build_interview_prompt(
                    role,
                    level,
                    topic,
                    difficulty,
                    number_of_questions,
                    job_description,
                )

                st.subheader("Generated prompt")
                st.code(user_prompt)

                try:
                    with st.spinner("Generating AI response..."):
                        ai_response = openrouter_client.call_provider_chat(
                            user_prompt,
                            system_prompt,
                            **_interview_request_kwargs(
                                selected_model,
                                max_tokens,
                            ),
                        )

                    st.subheader("AI response")
                    st.write(ai_response)

                except OpenRouterError as e:
                    st.error(str(e))
