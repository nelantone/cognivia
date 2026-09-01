# Guided Learning Intake

## Purpose

Guided Learning Intake helps Cognivia move from a vague learner goal to a motivation-aware, evidence-guided recommendation.

It should answer:

- What should I learn next?
- Which AI Engineering branch fits me?
- Which role direction might fit me?
- What is my next practical step?
- What evidence supports this recommendation?

The intake should turn uncertainty into a small, explainable decision: a branch, an optional secondary branch, a role direction, a next study step, a learning kata, a knowledge check, and an evidence note.

## Interaction Model: Form-First, Chat-Assisted

Cognivia starts with a structured intake form, then uses chat-style follow-up only when the learner's goal is unclear or multiple branches match.

The MVP flow:

1. The user selects what they need from a short list of entry points.
2. Cognivia asks 3-5 path-specific questions.
3. Cognivia outputs a structured recommendation.
4. Chat-style follow-up is optional after the first recommendation or when one clarification is needed.

This is more controllable, testable, demo-friendly, and easier to evaluate than a fully open-ended chat. Cognivia should not start as a general chat assistant; the first version should guide users through clear choices and short questions.

## Why This Belongs in Cognivia

Cognivia should not only retrieve documents. It should help aspiring AI engineers make decisions under uncertainty.

The intake connects personal motivation, current level, learning preferences, AI Engineering branches, broad labor-market and skill signals, and practical next steps. Learners often ask broad questions before they know the right vocabulary. A structured intake can translate vague intent into a grounded recommendation without pretending that evidence promises career outcomes.

## MVP Scope

The MVP should be a structured form-first intake with optional chat-style clarification.

It should ask:

- one entry-point choice;
- 3-5 follow-up questions based on that entry point;
- one optional clarification question when confidence is low or multiple branches match.

It should produce:

- recommended branch;
- secondary branch, if relevant;
- role direction;
- reason;
- evidence note;
- next study step;
- learning kata;
- knowledge check;
- uncertainty / limitation note;
- optional follow-up question.

This is not a full free-form chat assistant, career counselor, job matcher, or course platform. It is a focused decision aid for choosing a practical next AI Engineering learning step.

## Out of Scope

- No job guarantees.
- No salary prediction.
- No full career platform.
- No personality diagnosis.
- No Copilot clone.
- No IDE integration.
- No automatic job scraping.
- No large frontend redesign.
- No new RAG architecture in the first implementation.

## Intake Entry Points

### 1. Find my next AI learning step

For learners who want to improve but do not know what to study next.

Example follow-up questions: What have you built or studied most recently? What feels hardest right now: concepts, implementation, reliability, deployment, or direction? How much time can you spend this week? Do you want a project, explanation, kata, or knowledge check?

Expected output: one recommended branch, a realistic next study step, and a small kata sized to the learner's time.

### 2. Choose an AI Engineering branch

For learners comparing paths such as RAG, agents, evaluation, backend integration, MLOps, or Human-AI Coding.

Example follow-up questions: Which work sounds most interesting: product apps, automation, quality, backend systems, deployment, or code quality? What do you already enjoy in software engineering? Do you prefer building features, testing behavior, operating systems, or improving workflows? Are you optimizing for curiosity, portfolio value, or role clarity?

Expected output: primary and secondary branch recommendations with a short fit explanation and limitation note.

### 3. Connect my skills to role directions

For learners who have existing skills and want plausible AI Engineering role directions.

Example follow-up questions: What are your strongest current skills? What type of work do you want more of? What type of work do you want to avoid? Do you want a role-oriented recommendation or a portfolio-oriented next step?

Expected output: a branch, possible role direction, skill bridge, and next portfolio-visible practice task.

### 4. Practice a concept or knowledge check

For learners who want to test understanding or turn a topic into active practice.

Example follow-up questions: Which concept do you want to practice? Do you want recall questions, debugging, design critique, or a mini-build? What level should the check assume? Do you want feedback after each answer or a final rubric?

Expected output: a scoped knowledge check, expected answer criteria, and a follow-up learning kata.

### 5. Improve my Human-AI coding workflow

For learners who use coding assistants and want better quality, review, testing, and maintainability.

Example follow-up questions: What usually goes wrong with AI-generated code? Do you struggle more with planning, reviewing, testing, refactoring, or debugging? What kind of project are you working in? Do you want a checklist, kata, or review workflow?

Expected output: a Human-AI Coding / Code Quality recommendation, review workflow, kata, and evidence note.

### 6. Build a small portfolio-oriented study plan

For learners who want a visible project that demonstrates practical AI Engineering skills.

Example follow-up questions: Which audience should the project help? What branch or topic should it demonstrate? How much time do you have: one session, one week, or one month? What constraints matter: no API keys, local-only, simple UI, evaluation, or deployment?

Expected output: a small project plan, branch fit, milestone sequence, evidence note, and one knowledge check.

## Intake Questions

The MVP should not ask every question every time. It should choose 3-5 questions from the selected entry point and only ask one clarification question when needed.

Useful question dimensions:

- goal: what the learner is trying to achieve now;
- level: current technical comfort;
- motivation: what kind of work feels energizing;
- branch interest: apps, automation, quality, backend, deployment, or code quality;
- constraints: time, tools, API keys, local-only work, or portfolio needs;
- confidence: how sure the learner is about the direction.

## Motivation Categories

| Category | User signals | Likely branch fit | Possible risk / misfit |
| --- | --- | --- | --- |
| Build useful AI products | Chat, document Q&A, search, product features, demos, portfolio apps | RAG / LLM Applications; AI Backend / Integration | May jump into retrieval before API basics, testing, or evaluation |
| Automate workflows | Agents, tools, repetitive tasks, personal automation, multi-step workflows | Agents / Workflow Automation | May choose agents before understanding state, tool boundaries, and recovery |
| Improve job prospects | Employable skills, portfolio direction, role clarity, market relevance | AI Backend / Integration; RAG / LLM Applications; MLOps / Deployment | May expect deterministic outcomes from broad market signals |
| Understand AI deeply | Foundations, ML concepts, model behavior, theory, prerequisites | RAG / LLM Applications as an applied entry point; foundations before advanced branches | May need foundations before branch-specific work |
| Work with clean code and architecture | Maintainability, code review, refactoring, readable systems | Human-AI Coding / Code Quality; AI Backend / Integration | May avoid practical system building if quality concerns dominate |
| Evaluate and improve AI quality | Hallucinations, correctness, tests, rubrics, safety, reliability | AI Evaluation / Quality | May need a simple app or retrieval baseline before evaluation |
| Deploy reliable systems | Operations, repeatability, monitoring, CI, environments | MLOps / Deployment; AI Backend / Integration | May be too advanced before building a small AI service |
| Explore research/foundations | Papers, future software engineering, AI impact, deeper concepts | Human-AI Coding / Code Quality; AI Evaluation / Quality; foundations-first path | May need help turning abstract interest into a concrete kata |

## AI Engineering Branch Mapping

### 1. RAG / LLM Applications

- Fits: learners who like building useful products with documents, search, chat, or knowledge bases; learners motivated by practical AI apps more than model training.
- Core skills: prompting and structured outputs; embeddings and vector search; retrieval, chunking, metadata, citations; RAG evaluation; basic backend integration.
- Role directions: AI Application Engineer; LLM Application Developer; AI Backend Engineer; Software Engineer, AI Products.
- Next step: build a small document Q&A flow over three documents with citations and a short evaluation checklist.
- Kata: compare two chunking strategies and write a short failure analysis for one missed or weak answer.
- Evidence: curated learning-path Markdown, roadmap summaries, and skill reports that place embeddings, retrieval, APIs, and evaluation near practical AI application work.

### 2. Agents / Workflow Automation

- Fits: learners who enjoy automation, tool use, multi-step workflows, and making systems act on tasks; learners interested in planning, memory, routing, and human-in-the-loop controls.
- Core skills: tool calling; agent workflow design; state, memory, routing, guardrails; evaluation, observability, failure recovery; security boundaries.
- Role directions: Agentic Workflow Engineer; AI Automation Engineer; AI Platform Engineer; Developer Productivity Engineer.
- Next step: build a constrained agent that chooses between two safe tools and logs its decision path.
- Kata: add a failure case and write how the workflow should recover or ask for help.
- Evidence: curated roadmap summaries for agents, tool use, memory, evaluation, observability, and security.

### 3. AI Evaluation / Quality

- Fits: learners who care about correctness, reliability, testing, reducing hallucination, comparing model outputs, and designing quality checks.
- Core skills: evaluation datasets and rubrics; regression tests; human review workflows; safety checks; failure taxonomies; groundedness and usefulness metrics.
- Role directions: AI Evaluation Engineer; AI Quality Engineer; Responsible AI Engineer; Software Engineer, AI Products.
- Next step: create a small evaluation set for an LLM feature and score outputs with a written rubric.
- Kata: take five generated answers, classify failure modes, and propose one test for each recurring failure.
- Evidence: curated learning-path Markdown, skill reports, and project evidence about evaluation, reliability, and responsible AI habits.

### 4. AI Backend / Integration

- Fits: learners who like APIs, systems, data flow, production application structure, and connecting AI features to real products.
- Core skills: Python backend development; API design and validation; authentication; rate limits; error handling; provider integration; logging, monitoring, cost controls.
- Role directions: AI Backend Engineer; AI Application Engineer; Software Engineer, AI Products; AI Platform Engineer.
- Next step: wrap an LLM call behind a validated API endpoint with safe error messages and retry rules.
- Kata: add input validation and safe error handling to a small AI API, then document expected failure cases.
- Evidence: market and skill reports for broad demand signals, plus curated learning-path Markdown for practical API and integration structure.

### 5. MLOps / Deployment

- Fits: learners who enjoy deployment, infrastructure, reliability, repeatability, and the operational side of AI systems.
- Core skills: packaging and environments; model or service deployment; CI checks; automated tests; monitoring; rollback habits; data and model versioning concepts.
- Role directions: MLOps Engineer; AI Platform Engineer; AI Backend Engineer; Software Engineer, AI Products.
- Next step: deploy a small AI service with configuration separated from code and a basic health check.
- Kata: create a deploy checklist for an AI service and add one automated validation step.
- Evidence: market and skill reports for broad AI-exposed role signals, plus learning-path sources for deployment and operational skills.

### 6. Human-AI Coding / Code Quality

- Fits: learners who care about clean code, maintainability, architecture, reviewing AI-generated work, and disciplined collaboration workflows.
- Core skills: code review; refactoring; tests and executable specifications; debugging AI output; verification and validation artifacts; architecture judgment; cognitive debt management.
- Role directions: AI Software Engineer; AI Quality Engineer; AI Evaluation Engineer; Developer Productivity Engineer; Software Engineer, AI Products.
- Next step: review a small AI-generated feature in a familiar Python project, add tests, simplify it, and write a short rationale.
- Kata: generate a small function or feature, review it for correctness and maintainability, then refactor it without changing behavior.
- Evidence: research papers and curated Markdown on Human-AI Coding / Code Quality, future software engineering skills, verification, validation, and cognitive debt.

## Role Direction Mapping

These are exploratory role directions, not promised career outcomes.

| Branch | Possible role directions |
| --- | --- |
| RAG / LLM Applications | AI Application Engineer; LLM Application Developer; AI Backend Engineer; Software Engineer, AI Products |
| Agents / Workflow Automation | Agentic Workflow Engineer; AI Automation Engineer; AI Platform Engineer; Developer Productivity Engineer |
| AI Evaluation / Quality | AI Evaluation Engineer; AI Quality Engineer; Developer Productivity Engineer; Software Engineer, AI Products |
| AI Backend / Integration | AI Backend Engineer; AI Application Engineer; Software Engineer, AI Products; AI Platform Engineer |
| MLOps / Deployment | MLOps Engineer; AI Platform Engineer; AI Backend Engineer |
| Human-AI Coding / Code Quality | Developer Productivity Engineer; AI Quality Engineer; AI Evaluation Engineer; Software Engineer, AI Products |

## Evidence Usage

Cognivia should use evidence transparently and cautiously:

- Market reports can support broad labor-market signals.
- Skill reports can support skill demand and skill gap framing.
- Roadmaps can support learning structure and sequencing.
- Research papers can support Human-AI Coding / Code Quality and future software engineering claims.
- Curated Markdown should be the preferred RAG input because it is cleaner and more focused than raw reports or visual references.
- PDFs should remain original source artifacts for traceability and deeper manual review.

Recommendations should cite or summarize evidence in plain language. Evidence notes should avoid promising specific jobs, salaries, promotions, or hiring outcomes.

## Recommendation Output Format

```text
Recommended branch:
Secondary branch, if relevant:
Role direction:
Why this fits:
Evidence note:
Next study step:
Learning kata:
Knowledge check:
Uncertainty / limitation:
Optional follow-up question:
```

Example:

```text
Recommended branch: RAG / LLM Applications
Secondary branch, if relevant: AI Backend / Integration
Role direction: AI Application Engineer or LLM Application Developer
Why this fits: You like backend/product work and want a visible AI project that demonstrates practical skills.
Evidence note: The curated learning-path sources emphasize retrieval, APIs, evaluation, and product integration as core practical AI Engineering skills. Market sources should be treated as broad signals, not job guarantees.
Next study step: Build a three-document Q&A prototype with citations.
Learning kata: Compare two chunking approaches and write a short note on which answers improved or failed.
Knowledge check: Explain what embeddings, chunking, retrieval, and citations each do in the flow.
Uncertainty / limitation: This assumes you are comfortable with basic Python and API work. If not, start with a smaller Python/API foundation step.
Optional follow-up question: Do you want this turned into a one-week study plan or a smaller one-session kata?
```

## Chat Follow-Up

After the structured form output, users can ask:

- Why this branch?
- Give me a smaller step.
- Show the evidence.
- Quiz me.
- Compare this with another branch.
- Turn this into a 1-week study plan.

Follow-up chat should stay anchored to the structured recommendation. It should clarify, resize, compare, quiz, or show evidence; it should not replace the form-first intake with an open-ended assistant.

Use chat-style follow-up only after the first recommendation, when multiple branches match, when confidence is low, or when the user asks for clarification, smaller steps, evidence, or a knowledge check.

## Example User Profiles

### 1. Backend/product web developer seeking job-relevant AI skills

Signals: comfortable with web development and APIs; wants market-relevant AI skills and a portfolio-visible step; likes practical product features.

Recommendation: primary RAG / LLM Applications; secondary AI Backend / Integration. Next step: build a small document Q&A feature with a validated API boundary and citations. Kata: add safe error handling and evaluate three expected questions against the retrieved sources.

Evidence note: use curated learning-path Markdown for RAG, APIs, and evaluation. Use market and skill reports only as broad employability signals.

### 2. Learner who enjoys automation and agents

Signals: interested in tool use, multi-step workflows, and automating repetitive tasks; has some programming experience but little evaluation experience.

Recommendation: primary Agents / Workflow Automation; secondary AI Evaluation / Quality. Next step: build a constrained agent that chooses between two safe tools and logs the decision path. Kata: add one failure case and define when the agent should stop, retry, or ask for clarification.

Evidence note: use curated roadmap summaries for agents, tool boundaries, memory, observability, and security. Emphasize that reliable agents require evaluation and guardrails.

### 3. Developer frustrated by messy AI-generated code

Signals: values clean architecture, tests, maintainability, and code review; wants a constructive way to use coding agents without lowering quality.

Recommendation: primary Human-AI Coding / Code Quality; secondary AI Evaluation / Quality. Next step: review a small AI-generated feature, add tests for expected behavior, and refactor unnecessary complexity. Kata: write acceptance criteria first, generate an implementation, then review it for correctness, security, readability, and missing edge cases.

Evidence note: use curated Human-AI Coding material and research sources on verification, validation, executable specifications, future software engineering skills, and cognitive debt.

### 4. Learner who wants foundations but is unsure about career direction

Signals: curious about AI foundations and model behavior; unsure which role direction fits; may not yet prefer product, automation, evaluation, or deployment.

Recommendation: primary foundations-first path before a branch; secondary RAG / LLM Applications as a practical exploration path. Next step: learn prompts, embeddings, retrieval, and evaluation through a tiny local example. Kata: explain the difference between model knowledge and retrieved context, then test one question where retrieval helps and one where it does not.

Evidence note: use learning roadmaps for sequencing and curated Markdown for practical AI Engineering branch context. Avoid forcing a role direction until the learner has tried a small applied task.

## Decision Rules

- If the user likes document search, chatbots, product features, or knowledge bases, recommend RAG / LLM Applications.
- If the user likes tools, workflows, automation, routing, or multi-step tasks, recommend Agents / Workflow Automation.
- If the user likes testing, correctness, hallucination reduction, rubrics, or groundedness, recommend AI Evaluation / Quality.
- If the user likes APIs, backend systems, integration, validation, or provider calls, recommend AI Backend / Integration.
- If the user likes deployment, monitoring, reliability, CI, or operations, recommend MLOps / Deployment.
- If the user likes clean code, refactoring, code review, architecture, or improving AI-generated code, recommend Human-AI Coding / Code Quality.
- If multiple branches match, return a primary and secondary branch.
- If confidence is low, ask one clarification question before recommending.
- If the user has a very low technical level, recommend foundations before advanced agents, RAG, or deployment.
- If motivation is job relevance, prefer a portfolio-visible next step and include a limitation note about market uncertainty.
- If the user has little time this week, choose a kata that can be completed in one focused session.

## Risks and Limitations

- Broad market data is directional.
- Local markets vary.
- Role names vary by company and region.
- Stale market data can mislead.
- RAG evidence may be incomplete.
- A short intake may miss constraints such as language, accessibility, prior education, or local job-market context.
- Motivation is not the same as ability.
- The intake must not overclaim labor-market outcomes.
- The intake must not recommend advanced topics too early.
- The intake must not diagnose personality or predict salary, job offers, promotions, or hiring outcomes.

## Future Improvements

Future versions could add persistent learner profiles, progress history, adaptive knowledge checks, branch confidence scores, role requirement comparisons, a portfolio project generator, roadmap visualization, source freshness indicators, better prerequisite detection, and follow-up recommendation history.

## Implementation Notes For Later

Do not implement this intake yet. A later implementation could:

- start as a deterministic mapping function;
- use RAG evidence snippets from curated career sources;
- add a LangGraph node for intake classification;
- keep the first implementation small and testable;
- avoid frontend redesign;
- keep PDFs as traceability artifacts rather than primary retrieval input;
- test branch mapping without external API calls, embeddings, vector store creation, or retriever calls.
