"""Deterministic Markdown builders for learning-plan exports."""

from __future__ import annotations

from tools.learning_direction import LearningDirectionSchema


def _markdown_text(value: object, fallback: str = "Not specified.") -> str:
    if value is None:
        clean_value = None
    elif isinstance(value, str):
        clean_value = value.strip() or None
    elif isinstance(value, (list, tuple, set, dict)) and not value:
        clean_value = None
    else:
        clean_value = value

    if not clean_value:
        return fallback
    return " ".join(clean_value.split())


def _markdown_list(items: list[object]) -> list[str]:
    clean_items = [_markdown_text(item, "") for item in items or []]
    return [item for item in clean_items if item]


def _learning_path_map_steps(
    schema: LearningDirectionSchema,
) -> list[tuple[str, str]]:
    practice_step = schema["nodes"][2] if len(schema["nodes"]) > 2 else "Practice"
    return [
        ("Start", schema["nodes"][0] if schema["nodes"] else schema["current_state"]),
        ("First action", schema["first_action"]),
        ("Practice", practice_step),
        ("Checkpoint", schema["checkpoint"]),
        ("Outcome", schema["target_outcome"]),
    ]


def _time_available_today(decision: dict[str, object] | None) -> str:
    learner_profile = (
        decision.get("learner_profile")
        if isinstance(decision, dict) and isinstance(decision.get("learner_profile"), dict)
        else {}
    )
    minutes = learner_profile.get("time_available_minutes")
    if isinstance(minutes, int | float) and minutes > 0:
        return f"{int(minutes)} minutes"
    return "Not specified. Use one focused 2-hour block if available."


def build_full_learning_plan_document(
    *,
    goal: str,
    decision: dict[str, object] | None,
    selected_schema: LearningDirectionSchema,
    note: dict[str, object] | None = None,
    evidence_reason: str | None = None,
) -> str:
    """Build a deterministic, offline-safe Markdown learning plan."""
    decision = decision or {}
    recommended_direction = _markdown_text(
        decision.get("selected_focus") or decision.get("recommended_direction"),
        _markdown_text(decision.get("recommendation"), "Next learning direction"),
    )
    reason = _markdown_text(
        evidence_reason or decision.get("recommendation"),
        "Cognivia used the available learning context to size the next step.",
    )
    next_action = _markdown_text(
        decision.get("next_action"),
        selected_schema["first_action"],
    )
    why_this_path = _markdown_text(
        decision.get("recommendation") or selected_schema["fit_reason"],
        selected_schema["fit_reason"],
    )
    career_paths = _markdown_list(decision.get("possible_ai_career_paths") or [])
    skill_gaps = _markdown_list(decision.get("skill_gap") or [])
    map_steps = _learning_path_map_steps(selected_schema)
    map_line = " → ".join(label for label, _ in map_steps)
    practice_step = map_steps[2][1]
    time_available = _time_available_today(decision)
    note = note if isinstance(note, dict) else {}
    note_title = _markdown_text(note.get("title"), "")
    note_body = _markdown_text(note.get("reflection"), "")
    note_tags = _markdown_list(
        note.get("tags") if isinstance(note.get("tags"), list) else []
    )

    lines = [
        "# Cognivia Learning Plan",
        "",
        "## 1. Learning goal",
        _markdown_text(goal, "No learning goal was provided."),
        "",
        "## 2. Recommendation summary",
        f"- Recommended direction: {recommended_direction}",
        f"- Short reason: {reason}",
        f"- Next action: {next_action}",
        "",
        "## 3. Why this path",
        why_this_path,
        "",
    ]

    if career_paths:
        lines.extend(["Possible career directions:"])
        lines.extend(f"- {item}" for item in career_paths)
        lines.append("")
    if skill_gaps:
        lines.extend(["Skill gaps to practice:"])
        lines.extend(f"- {item}" for item in skill_gaps)
        lines.append("")

    lines.extend(
        [
            "## 4. Selected learning path",
            f"- Path title: {selected_schema['title']}",
            f"- Path summary: {selected_schema['subtitle']}",
            f"- Why this path helps: {selected_schema['fit_reason']}",
            f"- First action: {selected_schema['first_action']}",
            f"- Practice step: {practice_step}",
            f"- Checkpoint: {selected_schema['checkpoint']}",
            f"- Expected outcome: {selected_schema['target_outcome']}",
            "- Original path steps:",
            *(
                f"  {index}. {_markdown_text(step)}"
                for index, step in enumerate(selected_schema["nodes"], start=1)
            ),
            "",
            "## 5. Learning path map",
            map_line,
            "",
        ]
    )
    lines.extend(f"- {label}: {description}" for label, description in map_steps)
    lines.extend(
        [
            "",
            "## 6. Study method",
            "",
            "### 20-hour focused learning plan",
            (
                "Use 10 focused blocks of 2 hours. Each block should target one "
                "high-leverage concept and end with a 15-minute review."
            ),
            "",
            "### 80/20 concept focus",
            "Prioritize the small set of concepts that unlock the largest practical progress.",
            "",
            "### One-page study sheet",
            "Create one page with:",
            "- key concepts",
            "- vocabulary",
            "- common mistakes",
            "- practical checklist",
            "- what you must be able to explain or build",
            "",
            "### Five-level learning ladder",
            "1. Recognize the concept.",
            "2. Explain it simply.",
            "3. Apply it in a small task.",
            "4. Debug or evaluate it.",
            "5. Teach it or build something with it.",
            "",
            "### Mastery quiz",
            (
                "Use 5-10 questions with increasing difficulty. After each answer, "
                "write the correction and explanation."
            ),
            "",
            "### Feynman loop",
            (
                "Explain the topic in plain language, find the weak point, review it, "
                "and explain again."
            ),
            "",
            "Optional reference: [Feynman Technique](https://fs.blog/feynman-technique/)",
            "",
            "### Curated resources",
            "Use this as a resource strategy rather than live web recommendations:",
            "- official documentation",
            "- one practical tutorial",
            "- one expert explanation",
            "- one small project",
            "- one reference to revisit later",
            "",
            "### Session reflection",
            "End each study session by writing:",
            "- what worked",
            "- what was confusing",
            "- what distracted you",
            "- what to improve next session",
            "",
            "## 7. Today’s first study session",
            f"- Time available today: {time_available}",
            f"- Focus objective: {selected_schema['target_outcome']}",
            f"- Action: {selected_schema['first_action']}",
            f"- Checkpoint: {selected_schema['checkpoint']}",
            "- Reflection prompt: What did you learn, where did you get stuck, and what will you try next?",
            "",
            "## 8. Reflection",
        ]
    )

    if note_title or note_body or note_tags:
        if note_title:
            lines.extend([f"### {note_title}", ""])
        if note_body:
            lines.extend([note_body, ""])
        if note_tags:
            lines.extend(["Tags:", *(f"- {tag}" for tag in note_tags), ""])
    else:
        lines.extend(
            [
                "Use these prompts after your first study block:",
                "- Why did this path fit your current goal?",
                "- What did you understand better after studying?",
                "- What still feels fuzzy?",
                "- What is your next concrete action?",
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def build_learning_reflection_markdown(payload: dict[str, object]) -> str:
    """Build the reflection-only Markdown export."""
    selected_path = payload["selected_path"]
    note = payload["note"]
    if not isinstance(selected_path, dict) or not isinstance(note, dict):
        return ""

    return "\n".join(
        [
            "# Cognivia reflection",
            "",
            f"- Exported: {payload['exported_at']}",
            f"- Goal: {payload['goal']}",
            f"- Path: {selected_path.get('title', '')} ({selected_path.get('id', '')})",
            "",
            f"## {note.get('title', 'Reflection')}",
            "",
            str(note.get("reflection", "")),
            "",
            "## First action",
            "",
            str(payload.get("first_action", "")),
            "",
            "## Checkpoint",
            "",
            str(payload.get("checkpoint", "")),
        ]
    )
