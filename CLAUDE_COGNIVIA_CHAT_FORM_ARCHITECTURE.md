# Claude Code Task — Cognivia Chat + Form Architecture

## Project context

You are helping with the Cognivia capstone project.

Cognivia is an evidence-guided AI learning assistant for AI learners. The product helps a learner decide what to study next by combining:

- a structured learning intake form
- evidence from curated learning/career sources
- a recommendation
- a decision trace
- a next action / study plan
- optional chat follow-up

The frontend is currently frozen for several days. Do not change visual design, backgrounds, videos, audio, logos, icons, spacing, CSS, or layout unless explicitly asked.

Focus only on architecture and implementation planning for the chat + form flow.

---

## High-level goal

Design a clean architecture for a **form-first, chat-assisted** Cognivia experience.

The user should first fill a structured form. The app should use the form as the primary source of truth. After the first recommendation, the user can use chat to clarify, refine, or ask follow-up questions.

The chat should not replace the form. It should enhance the form-based recommendation.

---

## Product behavior

### 1. Form-first intake

The main user flow starts with a form that captures the learner's current situation.

The form should collect enough structured information to produce a useful recommendation without requiring a long free-text conversation.

Recommended form fields:

- current goal
- current level
- preferred AI engineering direction
- available time per week
- energy level
- preferred learning style
- strongest current skills
- weakest current skills
- current blocker
- resources already used
- desired output

The form should feel like a guided learning intake, not like a generic survey.

---

### 2. Suggested AI Engineering branches

The app should support six broad AI Engineering branches:

1. RAG / LLM Applications
2. Agents / Workflow Automation
3. AI Evaluation / Quality
4. AI Backend / Integration
5. MLOps / Deployment
6. Human-AI Coding / Code Quality

The form can let the user choose one branch, several branches, or “not sure”.

If the user is not sure, the app should infer the likely direction from their goal, current skills, blockers, and interests.

---

### 3. Recommendation output

After submitting the form, Cognivia should return a structured recommendation.

Recommended output sections:

1. **Recommended next learning step**
2. **Why this is the right next step**
3. **Evidence used**
4. **Decision trace**
5. **Risks / assumptions**
6. **Alternative path**
7. **Next action for this week**
8. **Mini knowledge check or reflection question**

The recommendation should be grounded in retrieved evidence where possible.

---

### 4. Chat-assisted follow-up

After the form result is generated, the user can continue with chat.

The chat should be scoped to the current recommendation and intake context.

Useful chat examples:

- “Make this easier.”
- “Give me a 3-day plan.”
- “Why not agents instead of RAG?”
- “What should I learn if I want a backend AI role?”
- “Quiz me on this.”
- “Explain the evidence.”
- “Update the recommendation: I only have 4 hours this week.”

The chat should be able to update or reinterpret the recommendation, but not silently overwrite the structured form state unless explicitly designed to do so.

---

## Architecture goals

Design a maintainable architecture with clear separation of concerns.

Avoid putting all logic in `app.py`.

Suggested modules:

```text
app.py
intake/
  schema.py
  validators.py
  form_state.py
  branch_mapping.py
chat/
  state.py
  prompts.py
  controller.py
  memory.py
recommendation/
  generator.py
  decision_trace.py
  formatter.py
rag/
  retriever.py
  loader.py
  sources.py
tools/
  study_plan.py
```

Do not create all modules blindly if the current project is smaller. Inspect the current repo first and propose the smallest clean architecture.

---

## Recommended data model

Create or propose a typed intake model.

Example shape:

```python
@dataclass
class LearningIntake:
    goal: str
    current_level: str
    preferred_branch: str | None
    available_hours_per_week: int | None
    energy_level: str
    learning_style: str | None
    strong_skills: list[str]
    weak_skills: list[str]
    blocker: str | None
    resources_used: list[str]
    desired_output: str | None
```

Use Pydantic or dataclasses depending on the current project style.

Prefer simple validation over heavy abstractions.

---

## Form state

The form should create a structured object, not just a string prompt.

The app should preserve:

- raw form values
- normalized intake values
- selected branch or inferred branch
- retrieved evidence
- generated recommendation
- chat history for the current session

Suggested session state keys:

```python
st.session_state["learning_intake"]
st.session_state["retrieved_evidence"]
st.session_state["recommendation"]
st.session_state["decision_trace"]
st.session_state["chat_messages"]
st.session_state["active_branch"]
```

Keep names consistent with the existing codebase if similar state already exists.

---

## Chat state

The chat should use:

- current `LearningIntake`
- current recommendation
- current evidence snippets
- recent chat messages

The chat prompt should explicitly say:

- answer within the context of the learner's goal
- use evidence where relevant
- do not invent sources
- explain uncertainty
- propose concrete next actions
- ask a clarifying question only if necessary

---

## RAG integration

The form result should trigger retrieval.

Retrieval query should be built from structured intake values, not only from free text.

Potential retrieval query components:

- goal
- preferred/inferred branch
- current level
- blocker
- desired role/output
- weak skills

The recommendation should cite or summarize evidence snippets.

Avoid overclaiming if evidence is weak.

---

## Decision trace

The decision trace should be readable and honest.

It should show:

- user goal interpreted
- relevant constraints
- evidence considered
- why the recommended branch/step was chosen
- what was rejected and why
- assumptions
- next action

Do not expose private chain-of-thought. Use a concise, user-facing decision rationale.

---

## Implementation plan requested from Claude Code

Please inspect the current repository and produce a plan before editing.

First response should include:

1. Current files related to form, RAG, recommendation, and study plan
2. Proposed architecture with minimal changes
3. Which files should be created or modified
4. Data flow diagram in text or Mermaid
5. Risks and tradeoffs
6. Suggested first implementation step

Do not modify files in the first pass unless explicitly instructed.

---

## Do not touch

Do not touch frontend styling or visual assets.

Specifically do not change:

- background videos
- audio intro
- play/pause controls
- landscape/wave controls
- logo positioning
- CSS polish
- brand assets
- layout spacing
- card/table visual design

Frontend is frozen.

---

## Quality bar

The architecture should be simple enough for a capstone, but clean enough to explain in a presentation.

Prioritize:

- clarity
- testability
- small modules
- explicit state
- evidence-grounded recommendations
- easy demo flow

Avoid:

- overengineering
- complex agents before the core flow works
- hidden state mutations
- large rewrites
- visual changes
- vague prompt-only architecture

---

## Suggested demo flow

A good final demo should show:

1. User fills the guided intake form.
2. Cognivia retrieves relevant evidence.
3. Cognivia recommends the next learning step.
4. User opens chat follow-up.
5. User asks for a shorter plan or alternative path.
6. Cognivia responds using the existing intake + evidence + recommendation context.

---

## Deliverable requested

Produce a concrete architecture proposal and implementation plan.

Do not code immediately.

Use this format:

```text
Architecture summary
Current repo observations
Recommended data flow
Files to modify/create
Minimal implementation plan
Testing plan
Risks / open questions
Next recommended step
```

