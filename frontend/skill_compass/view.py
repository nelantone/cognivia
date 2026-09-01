import base64
import html
import logging
from pathlib import Path

import streamlit as st

from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.evaluation import EVALUATION_CASES, run_evaluation_set
from rag.generator import answer_with_rag
from rag.retriever import retrieve_relevant_chunks
from security import validate_job_description, validate_user_input
from tools.explanation import evaluate_explanation
from tools.guided_intake import (
    CURRENT_LEVEL_OPTIONS,
    ENTRY_POINTS,
    PREFERRED_WORK_STYLES,
    build_guided_intake_query,
    build_guided_intake_recommendation,
    build_learner_profile,
)
from tools.priority import calculate_priority_score
from tools.study_plan import generate_study_plan


logger = logging.getLogger(__name__)


def _validate_compass_input(value, field_label):
    is_valid, error_message = validate_user_input(value)
    if not is_valid:
        return False, error_message.replace("Role", field_label)
    return True, ""


def _validate_compass_long_input(value, field_label):
    is_valid, error_message = validate_job_description(value)
    if not is_valid:
        return False, error_message.replace("Job description", field_label)
    return True, ""


def _render_ai_skill_compass(
    *,
    LOCAL_EVIDENCE_STORE_BUSY_MESSAGE,
    _is_local_evidence_store_lock_error,
    _save_guided_intake_memory,
    _render_guided_intake_recommendation,
) -> None:
    st.markdown(
        """
        <style>
        /* Subtle AI Skill Compass styling */
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2 {
            color: #38D9C8;
        }
        div[data-testid="stAppViewContainer"] .stImage,
        div[data-testid="stAppViewContainer"] .stImage > img,
        div[data-testid="stAppViewContainer"] .stImage > figure {
            background: transparent !important;
            box-shadow: none !important;
        }
        .sc-hero {
            text-align: center;
            margin: 0.5rem 0 0.2rem 0;
        }
        .sc-subtitle {
            text-align: center;
            color: #B9C6D5;
            font-size: 0.98rem;
            margin: 0.2rem 0 0.8rem 0;
        }
        .sc-divider {
            height: 1px;
            background-color: rgba(56, 217, 200, 0.28);
            margin: 0.6rem 0 1rem 0;
            border-radius: 999px;
        }
        .piko-reco {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-top: 0.4rem;
        }
        .piko-reco .piko-avatar {
            width: 56px;
            height: 56px;
            object-fit: contain;
            border-radius: 12px;
        }
        .piko-reco .piko-text {
            line-height: 1.45;
            color: #F4F7FA;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    transparent_logo_path = Path("assets/skill_compass_logo_transparent.png")
    default_logo_path = Path("assets/skill_compass_logo.png")
    logo_path = (
        transparent_logo_path if transparent_logo_path.exists() else default_logo_path
    )
    logo_available = False

    if logo_path.exists():
        try:
            left_col, center_col, right_col = st.columns([1, 2, 1])
            with center_col:
                st.markdown('<div class="sc-hero">', unsafe_allow_html=True)
                st.image(str(logo_path), width=480)
                st.markdown("</div>", unsafe_allow_html=True)
            logo_available = True
        except Exception:
            logger.exception("Skill Compass logo failed to load")
            logo_available = False

    if not logo_available:
        st.title("AI Skill Compass")

    st.markdown(
        '<div class="sc-subtitle">RAG-powered learning and career guidance for AI developers.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sc-divider"></div>', unsafe_allow_html=True)

    st.write(
        "Ask questions about AI skills, learning paths, and career development. "
        "Use deterministic tools or search the knowledge base."
    )

    tool_options = [
        "Ask with RAG",
        "Guided learner intake",
        "Calculate priority score",
        "Generate study plan",
        "Evaluate explanation",
        "Run RAG evaluation",
    ]
    selected_tool = st.selectbox("Action", tool_options)

    # --- Guided Learner Intake ---
    if selected_tool == "Guided learner intake":
        entry_point = st.selectbox("Entry point", ENTRY_POINTS)
        current_level = st.selectbox("Current level", CURRENT_LEVEL_OPTIONS)
        current_skills = st.text_area(
            "Current skills",
            placeholder="e.g., Python, APIs, basic prompting",
            height=80,
        )
        interests = st.text_area(
            "Interests",
            placeholder="e.g., useful AI apps, clean code, reliable answers",
            height=80,
        )
        preferred_work_style = st.selectbox(
            "Preferred work style",
            PREFERRED_WORK_STYLES,
        )
        target_role = st.text_input(
            "Target role or direction, if known",
            placeholder="e.g., AI Backend Engineer",
        )
        goal = st.text_area(
            "Goal",
            placeholder="e.g., I feel lost and want a practical next AI learning step",
            height=100,
        )
        time_available = st.number_input(
            "Time available (minutes)",
            min_value=1,
            max_value=480,
            value=60,
            step=10,
        )

        if st.button("Build learning path"):
            text_fields = {
                "Current skills": current_skills,
                "Interests": interests,
                "Target role or direction": target_role,
                "Goal": goal,
            }
            validation_errors = []

            for field_label, field_value in text_fields.items():
                if not field_value or not field_value.strip():
                    continue

                if field_label in {"Current skills", "Interests", "Goal"}:
                    is_valid, error_message = _validate_compass_long_input(
                        field_value.strip(),
                        field_label,
                    )
                else:
                    is_valid, error_message = _validate_compass_input(
                        field_value.strip(),
                        field_label,
                    )

                if not is_valid:
                    validation_errors.append(error_message)

            if not goal or not goal.strip():
                st.error("Please enter a goal.")
            elif validation_errors:
                st.error(validation_errors[0])
            else:
                try:
                    learner_profile = build_learner_profile(
                        entry_point=entry_point,
                        current_level=current_level,
                        current_skills=current_skills,
                        interests=interests,
                        preferred_work_style=preferred_work_style,
                        target_role=target_role,
                        goal=goal,
                        time_available_minutes=int(time_available),
                    )
                    rag_query = build_guided_intake_query(learner_profile)
                    retrieved_docs = []

                    try:
                        with st.spinner("Searching knowledge base for guidance..."):
                            retrieved_docs = retrieve_relevant_chunks(
                                rag_query,
                                k=4,
                                min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
                            )
                    except Exception as error:
                        logger.exception(
                            "Error retrieving evidence for guided learner intake"
                        )
                        if _is_local_evidence_store_lock_error(error):
                            st.warning(LOCAL_EVIDENCE_STORE_BUSY_MESSAGE)

                    recommendation = build_guided_intake_recommendation(
                        learner_profile,
                        retrieved_docs,
                    )
                except ValueError as e:
                    st.error(str(e))
                except Exception:
                    logger.exception("Error in guided learner intake mode")
                    st.error(
                        "Unable to build a guided learning path right now. "
                        "Please try again later."
                    )
                else:
                    _save_guided_intake_memory(
                        recommendation,
                        interaction_mode="guided_intake",
                    )
                    _render_guided_intake_recommendation(
                        recommendation,
                        next_action_heading="Next action",
                    )

    # --- Ask with RAG ---
    elif selected_tool == "Ask with RAG":
        question = st.text_area(
            "Your question",
            placeholder="e.g., What skills do I need to become an AI engineer?",
            height=100,
        )

        if st.button("Get answer"):
            if not question or not question.strip():
                st.error("Please enter a question.")
            else:
                is_valid, error_message = _validate_compass_input(
                    question.strip(),
                    "Question",
                )
                if not is_valid:
                    st.error(error_message)
                else:
                    try:
                        with st.spinner("Searching knowledge base..."):
                            result = answer_with_rag(question.strip())

                        st.subheader("Answer")
                        st.write(result["answer"])

                        sources = result["sources"]
                        source_count = len(sources) if sources else 0
                        st.subheader(f"Retrieved RAG Sources ({source_count})")
                        if sources:
                            for i, src in enumerate(sources, start=1):
                                with st.expander(
                                    f"Source {i}: {src['source']}",
                                    key=f"skill_compass_rag_source_{i}",
                                    on_change="ignore",
                                ):
                                    st.caption(f"Chunk index: {src['chunk_index']}")
                                    st.text(src["preview"] + "...")
                        else:
                            st.info("No sources found for this question.")

                    except Exception:
                        logger.exception("Error in AI Skill Compass RAG mode")
                        st.error(
                            "An error occurred while processing your question. Please try again."
                        )

    # --- Calculate Priority Score ---
    elif selected_tool == "Calculate priority score":
        st.markdown(
            "**Note:** Market relevance is automatically calculated from the knowledge base."
        )
        topic = st.text_input("Learning topic", placeholder="e.g., RAG systems")
        interest = st.slider("Interest (1-5)", 1, 5, 3)
        difficulty = st.slider("Difficulty (1-5)", 1, 5, 3)
        urgency = st.slider("Urgency (1-5)", 1, 5, 3)

        if st.button("Calculate score"):
            if not topic or not topic.strip():
                st.error("Please enter a learning topic.")
            else:
                is_valid, error_message = _validate_compass_input(
                    topic.strip(),
                    "Learning topic",
                )
                if not is_valid:
                    st.error(error_message)
                else:
                    try:
                        with st.spinner(
                            "Searching knowledge base for market context..."
                        ):
                            chunks = retrieve_relevant_chunks(
                                topic.strip(),
                                k=3,
                                min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
                            )
                            retrieved_context = [
                                chunk.page_content for chunk in chunks
                            ]
                    except Exception:
                        logger.exception(
                            "Error retrieving evidence for priority score calculation"
                        )
                        st.error(
                            "Unable to retrieve supporting evidence right now. "
                            "Please try again later."
                        )
                    else:
                        try:
                            result = calculate_priority_score(
                                topic.strip(),
                                interest,
                                difficulty,
                                urgency,
                                retrieved_context,
                            )
                        except ValueError:
                            st.error("Priority ratings must be between 1 and 5.")
                        except Exception:
                            logger.exception("Error in priority score calculation")
                            st.error(
                                "An error occurred while calculating the priority score. "
                                "Please try again."
                            )
                        else:
                            st.subheader("Priority Score")
                            st.metric("Score", f"{result['score']}/100")
                            st.write(result["reason"])

                            st.subheader("Market relevance")
                            st.metric(
                                "Market Relevance (from RAG)",
                                f"{result['market_relevance_score']}/5",
                            )
                            if result["market_signals"]:
                                market_signals = ", ".join(result["market_signals"])
                                st.write(
                                    f"**Market signals:** {market_signals}"
                                )
                            else:
                                st.info(
                                    "No strong market signals detected for this topic."
                                )

                            source_count = len(chunks) if chunks else 0
                            if chunks:
                                with st.expander(
                                    f"RAG evidence used ({source_count})",
                                    key="skill_compass_priority_evidence",
                                    on_change="ignore",
                                ):
                                    for i, chunk in enumerate(chunks, start=1):
                                        source = chunk.metadata.get(
                                            "source", "Unknown"
                                        )
                                        chunk_index = chunk.metadata.get(
                                            "chunk_index", "N/A"
                                        )
                                        preview = " ".join(
                                            chunk.page_content.strip().split()
                                        )
                                        if len(preview) > 200:
                                            preview = (
                                                preview[:200].rstrip() + "..."
                                            )
                                        st.markdown(f"**Source {i}**")
                                        st.caption(f"Source path: {source}")
                                        st.caption(f"Chunk index: {chunk_index}")
                                        st.text(preview)
                            else:
                                st.info(
                                    "No evidence retrieved for market relevance."
                                )

    # --- Generate Study Plan ---
    elif selected_tool == "Generate study plan":
        topic = st.text_input("Topic to study", placeholder="e.g., Transformers")
        available_time = st.number_input(
            "Available time (minutes)",
            min_value=1,
            max_value=480,
            value=60,
            step=10,
        )
        energy_level = st.selectbox("Energy level", ["low", "medium", "high"])
        current_level = st.selectbox(
            "Current level",
            ["beginner", "intermediate", "advanced"],
        )

        if st.button("Generate plan"):
            if not topic or not topic.strip():
                st.error("Please enter a topic.")
            else:
                is_valid, error_message = _validate_compass_input(
                    topic.strip(),
                    "Topic",
                )
                if not is_valid:
                    st.error(error_message)
                else:
                    try:
                        result = generate_study_plan(
                            topic.strip(),
                            available_time,
                            energy_level,
                            current_level,
                        )
                        st.subheader("Study Plan")
                        st.write(result["plan"])
                        piko_primary_path = Path("assets/piko.png")
                        piko_path = piko_primary_path
                        piko_label = "Piko’s recommendation"
                        piko_image_uri = None
                        if piko_path.exists():
                            try:
                                encoded = base64.b64encode(
                                    piko_path.read_bytes()
                                ).decode("utf-8")
                                mime_type = (
                                    "image/png"
                                    if piko_path.suffix.lower() == ".png"
                                    else "image/jpeg"
                                )
                                piko_image_uri = f"data:{mime_type};base64,{encoded}"
                            except Exception:
                                logger.exception("Piko avatar failed to load")

                        expected_outcome_text = html.escape(result["expected_outcome"])
                        if piko_image_uri:
                            st.markdown(
                                f"""
                                <div class="piko-reco">
                                    <img class="piko-avatar" src="{piko_image_uri}" alt="Piko" />
                                    <div class="piko-text"><strong>{piko_label}:</strong> {expected_outcome_text}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(f"**{piko_label}:** {expected_outcome_text}")
                    except ValueError as e:
                        st.error(str(e))
                    except Exception:
                        logger.exception("Error in study plan generation")
                        st.error("An error occurred. Please check your inputs.")

    # --- Evaluate Explanation ---
    elif selected_tool == "Evaluate explanation":
        target_concept = st.text_input(
            "Target concept",
            placeholder="e.g., Attention mechanism",
        )
        user_explanation = st.text_area(
            "Your explanation",
            placeholder="Explain the concept in your own words...",
            height=120,
        )
        key_terms = st.text_input(
            "Key terms (comma-separated)",
            placeholder="e.g., query, key, value, dot product",
        )

        if st.button("Evaluate"):
            if not target_concept or not target_concept.strip():
                st.error("Please enter the target concept.")
            elif not user_explanation or not user_explanation.strip():
                st.error("Please enter your explanation.")
            elif not key_terms or not key_terms.strip():
                st.error("Please enter at least one key term.")
            else:
                is_valid, error_message = _validate_compass_input(
                    target_concept.strip(),
                    "Target concept",
                )
                if not is_valid:
                    st.error(error_message)
                else:
                    is_valid, error_message = _validate_compass_long_input(
                        user_explanation.strip(),
                        "Explanation",
                    )
                    if not is_valid:
                        st.error(error_message)
                    else:
                        terms_list = [
                            t.strip() for t in key_terms.split(",") if t.strip()
                        ]
                        invalid_term = False
                        for term in terms_list:
                            is_valid, error_message = _validate_compass_input(
                                term,
                                "Key term",
                            )
                            if not is_valid:
                                st.error(error_message)
                                invalid_term = True
                                break

                        if not invalid_term:
                            try:
                                result = evaluate_explanation(
                                    user_explanation.strip(),
                                    target_concept.strip(),
                                    terms_list,
                                )
                                st.subheader("Evaluation Result")
                                st.metric(
                                    "Clarity Score",
                                    f"{result['clarity_score']}/100",
                                )
                                st.write(result["feedback"])
                                st.write(f"**Next step:** {result['next_step']}")
                                if result["missing_terms"]:
                                    st.info(
                                        f"Missing terms: {', '.join(result['missing_terms'])}"
                                    )
                            except ValueError as e:
                                st.error(str(e))
                            except Exception:
                                logger.exception("Error in explanation evaluation")
                                st.error("An error occurred. Please check your inputs.")

    # --- Run RAG evaluation ---
    elif selected_tool == "Run RAG evaluation":
        st.markdown(
            "Run the deterministic evaluation set against the retriever and review results."
        )

        if st.button("Run evaluation"):
            try:
                with st.spinner("Running RAG evaluation..."):
                    evaluation = run_evaluation_set(EVALUATION_CASES)

                st.subheader("RAG Evaluation Results")
                st.metric("Pass rate", f"{evaluation['pass_rate']}%")

                rows = []
                for result in evaluation["results"]:
                    expected_sources = ", ".join(result.get("matched_sources") or [])
                    retrieved_sources = ", ".join(result.get("retrieved_sources") or [])
                    status_text = "✅ Pass" if result.get("passed") else "❌ Fail"
                    rows.append(
                        {
                            "Question": result.get("question", ""),
                            "Expected/Matched source": expected_sources or "—",
                            "Retrieved sources": retrieved_sources or "—",
                            "Score": result.get("score", 0),
                            "Status": status_text,
                        }
                    )

                st.dataframe(rows, use_container_width=True)
            except Exception:
                logger.exception("Error in RAG evaluation")
                st.error("An error occurred while running the evaluation.")
