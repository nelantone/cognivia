"""Deterministic recommendation explanation helpers."""

from __future__ import annotations


DIRECTION_DESCRIPTIONS = {
    "RAG / LLM Applications": (
        "Focus on building applications that connect LLMs with external "
        "knowledge, retrieval systems, structured prompts, and user-facing "
        "workflows."
    ),
    "Agents / Workflow Automation": (
        "Focus on workflows where an AI system follows steps, uses tools, and "
        "keeps state while solving a bounded task."
    ),
    "AI Evaluation / Quality": (
        "Focus on testing whether AI systems are useful, grounded, reliable, "
        "and safe enough for their intended users."
    ),
    "AI Backend / Integration": (
        "Focus on the APIs, data flows, provider integrations, storage, and "
        "runtime services behind AI products."
    ),
    "MLOps / Deployment": (
        "Focus on shipping, monitoring, and operating AI systems reliably "
        "outside a notebook."
    ),
    "Human-AI Coding / Code Quality": (
        "Focus on using AI coding tools while preserving software quality, "
        "tests, review discipline, and engineering judgment."
    ),
}

DIRECTION_FIT_REASONS = {
    "RAG / LLM Applications": (
        "This fits when the learner wants to turn broad AI uncertainty into "
        "a concrete product path with evidence, retrieval, and application logic."
    ),
    "Agents / Workflow Automation": (
        "This fits when the learner is interested in multi-step automation "
        "rather than one-shot chat responses."
    ),
    "AI Evaluation / Quality": (
        "This fits when the learner wants stronger judgment about whether an "
        "AI system is actually working."
    ),
    "AI Backend / Integration": (
        "This fits when the learner wants to build the reliable service layer "
        "that makes AI features usable."
    ),
    "MLOps / Deployment": (
        "This fits when the learner is ready to move from local demos toward "
        "operational systems."
    ),
    "Human-AI Coding / Code Quality": (
        "This fits when the learner wants AI assistance without losing code "
        "review, debugging, and maintainability skills."
    ),
}

DIRECTION_FIRST_ACTIONS = {
    "RAG / LLM Applications": (
        "Build or inspect a tiny RAG flow: load docs, split by section, embed, "
        "retrieve, and answer with evidence."
    ),
    "Agents / Workflow Automation": (
        "Map one small workflow into steps, then decide where tool use and "
        "state are actually needed."
    ),
    "AI Evaluation / Quality": (
        "Create a five-case checklist that tests helpfulness, grounding, and "
        "failure behavior."
    ),
    "AI Backend / Integration": (
        "Sketch one API endpoint for an AI feature, including inputs, provider "
        "call, storage, and safe error handling."
    ),
    "MLOps / Deployment": (
        "Write a minimal runbook for starting, checking, and recovering a local "
        "AI service."
    ),
    "Human-AI Coding / Code Quality": (
        "Before using an AI coding tool, write your expected change and one "
        "test you expect to pass afterward."
    ),
}

CAREER_PATH_DESCRIPTIONS = {
    "AI Application Engineer": (
        "Builds user-facing AI products using LLM APIs, RAG, evaluation, "
        "guardrails, and application logic."
    ),
    "LLM Application Developer": (
        "Focuses on prompt design, structured outputs, retrieval workflows, "
        "agents, and practical LLM-powered features."
    ),
    "AI Backend Engineer": (
        "Builds backend systems behind AI products: APIs, databases, vector "
        "stores, auth, observability, and deployment."
    ),
    "Agentic Workflow Engineer": (
        "Designs bounded AI workflows that coordinate tools, state, routing, "
        "and safe handoffs."
    ),
    "AI Automation Engineer": (
        "Builds AI-assisted automations that reduce repetitive work while "
        "keeping human review points clear."
    ),
    "Developer Productivity Engineer": (
        "Improves engineering workflows with automation, code quality systems, "
        "review tools, and AI coding support."
    ),
    "AI Evaluation Engineer": (
        "Designs tests and rubrics to measure AI quality, grounding, safety, "
        "and regressions."
    ),
    "AI Quality Engineer": (
        "Focuses on reliability, failure analysis, test coverage, and safe AI "
        "behavior."
    ),
    "Responsible AI Engineer": (
        "Works on safeguards, evaluation, transparency, privacy, and risk "
        "controls for AI systems."
    ),
    "AI Platform Engineer": (
        "Builds shared infrastructure, deployment paths, observability, and "
        "runtime services for AI teams."
    ),
    "MLOps Engineer": (
        "Ships and monitors ML or AI systems with deployment, configuration, "
        "testing, and operational discipline."
    ),
    "Software Engineer, AI Products": (
        "Builds production software that includes AI features while preserving "
        "normal engineering quality."
    ),
}

SKILL_GAP_DESCRIPTIONS = {
    "prompting": (
        "Designing instructions, examples, and structured formats so an LLM "
        "behaves reliably."
    ),
    "embeddings": (
        "Turning text into vectors so related ideas can be searched mathematically."
    ),
    "retrieval": (
        "Finding the most relevant context before asking the model to answer."
    ),
    "chunking": (
        "Splitting documents into useful sections so retrieval does not mix "
        "unrelated topics."
    ),
    "citations": (
        "Showing where an answer came from so a learner or reviewer can verify it."
    ),
    "RAG evaluation": (
        "Testing whether retrieval and answers are relevant, grounded, and useful."
    ),
    "evaluation": (
        "Testing whether the AI system is useful, grounded, and safe."
    ),
    "tool calling": (
        "Letting an AI system use specific functions or tools through controlled inputs."
    ),
    "state management": (
        "Keeping track of what has happened in a workflow without mixing old and new context."
    ),
    "routing": (
        "Choosing the right workflow path based on the user's request and current state."
    ),
    "guardrails": (
        "Rules and checks that keep AI behavior inside safe, useful boundaries."
    ),
    "workflow evaluation": (
        "Testing whether a multi-step AI workflow succeeds, fails safely, and stays understandable."
    ),
    "Python APIs": (
        "Building Python service endpoints that other code or users can call reliably."
    ),
    "input validation": (
        "Checking user input before it reaches tools, models, storage, or prompts."
    ),
    "provider integration": (
        "Connecting safely to model providers while handling configuration and failures."
    ),
    "safe error handling": (
        "Showing users useful messages without exposing secrets, raw stack traces, or internals."
    ),
    "logging": (
        "Recording technical details for debugging without leaking sensitive data to users."
    ),
}


def explain_direction(label: object) -> str:
    clean_label = _clean_label(label)
    return DIRECTION_DESCRIPTIONS.get(
        clean_label,
        f"Focus on a practical learning path around {clean_label or 'this direction'}.",
    )


def explain_direction_fit(label: object) -> str:
    clean_label = _clean_label(label)
    return DIRECTION_FIT_REASONS.get(
        clean_label,
        "This fits when the learner needs a clear next step from the available context.",
    )


def first_action_for_direction(label: object, fallback: object = None) -> str:
    clean_label = _clean_label(label)
    clean_fallback = _clean_label(fallback)
    if clean_fallback:
        return clean_fallback
    return DIRECTION_FIRST_ACTIONS.get(
        clean_label,
        f"Pick one small task that practices {clean_label or 'this direction'} today.",
    )


def explain_career_path(label: object) -> str:
    clean_label = _clean_label(label)
    return CAREER_PATH_DESCRIPTIONS.get(
        clean_label,
        f"Works on practical AI product problems related to {clean_label or 'this path'}.",
    )


def explain_skill_gap(label: object) -> str:
    clean_label = _clean_label(label)
    return SKILL_GAP_DESCRIPTIONS.get(
        clean_label,
        f"A skill area to practice so {clean_label or 'this topic'} becomes more concrete.",
    )


def _clean_label(label: object) -> str:
    return " ".join(str(label or "").split())
