# AI Engineering Learning Paths

## Purpose

This card summarizes practical AI Engineering learning paths for Cognivia's future Guided Learning Intake.

It helps map learner motivation, current level, and missing prerequisites to an AI Engineering branch, possible role direction, and next study step.

## Why Roadmaps Are Summarized Into Markdown

Web roadmaps and visual roadmaps are useful for human scanning, but they are often noisy for retrieval. They may include nested layouts, repeated labels, dense graphics text, tool lists without context, or broad learning sequences.

Curated Markdown gives Cognivia cleaner retrieval chunks, clearer branch boundaries, and source-aware guidance without requiring raw PDF or infographic parsing.

## Primary Sources

- Dataquest AI Engineer Roadmap 2026
- roadmap.sh AI Engineer
- roadmap.sh AI Agents
- Coursera AI Learning Roadmap
- Microsoft AI Skills Navigator

## Cognivia AI Engineering Branch Taxonomy

1. RAG / LLM Applications
2. Agents / Workflow Automation
3. AI Evaluation / Quality
4. AI Backend / Integration
5. MLOps / Deployment
6. Human-AI Coding / Code Quality

## Branch: RAG / LLM Applications

Who it fits:

- Learners who like building useful products with documents, search, chat, or knowledge bases.
- Learners motivated by practical AI apps more than model training.

Core skills:

- Prompting and structured outputs.
- Embeddings and vector search.
- Retrieval, chunking, metadata, and citations.
- RAG evaluation and failure analysis.
- Basic backend integration.

Example next step:

- Build a small document Q&A flow with citations and a short evaluation checklist.

Possible role direction:

- AI Application Engineer.
- LLM Application Developer.
- AI Backend Engineer.

## Branch: Agents / Workflow Automation

Who it fits:

- Learners who enjoy automation, tool use, multi-step workflows, and making systems act on tasks.
- Learners interested in planning, memory, and human-in-the-loop controls.

Core skills:

- Tool calling and function interfaces.
- Agent workflow design.
- State, memory, routing, and guardrails.
- Evaluation, observability, and failure recovery.
- Security boundaries for tools and user input.

Example next step:

- Build a constrained agent that chooses between two safe tools and logs its decision path.

Possible role direction:

- Agentic Workflow Engineer.
- AI Automation Engineer.
- AI Platform Engineer.

## Branch: AI Evaluation / Quality

Who it fits:

- Learners who care about correctness, reliability, testing, and reducing hallucination.
- Learners who enjoy comparing model outputs and designing quality checks.

Core skills:

- Evaluation datasets and rubrics.
- Regression tests for prompts and retrieval.
- Human review workflows.
- Safety checks and failure taxonomies.
- Metrics for groundedness, usefulness, and completeness.

Example next step:

- Create a small evaluation set for an LLM feature and score outputs with a written rubric.

Possible role direction:

- AI Evaluation Engineer.
- AI Quality Engineer.
- Responsible AI Engineer.

## Branch: AI Backend / Integration

Who it fits:

- Learners who like APIs, systems, data flow, and production application structure.
- Learners who want to connect AI features to real products.

Core skills:

- Python backend development.
- API design and validation.
- Authentication, rate limits, and error handling.
- LLM provider integration.
- Logging, monitoring, and cost controls.

Example next step:

- Wrap an LLM call behind a validated API endpoint with safe error messages and retry rules.

Possible role direction:

- AI Backend Engineer.
- AI Application Engineer.
- Software Engineer, AI Products.

## Branch: MLOps / Deployment

Who it fits:

- Learners who enjoy deployment, infrastructure, reliability, and making systems repeatable.
- Learners interested in the operational side of AI systems.

Core skills:

- Packaging and environment management.
- Model or service deployment.
- CI checks and automated tests.
- Monitoring and rollback habits.
- Data and model versioning concepts.

Example next step:

- Deploy a small AI service with configuration separated from code and a basic health check.

Possible role direction:

- MLOps Engineer.
- AI Platform Engineer.
- Machine Learning Engineer.

## Branch: Human-AI Coding / Code Quality

Who it fits:

- Learners who care about clean code, maintainability, architecture, and reviewing AI-generated work.
- Learners who feel demotivated by messy generated code and want a disciplined collaboration workflow.

Core skills:

- Code review and refactoring.
- Tests and executable specifications.
- Debugging AI output.
- Verification and validation artifacts.
- Architecture judgment and cognitive debt management.

Example next step:

- Ask an AI assistant to generate a small feature, then review, test, refactor, and document the changes.

Possible role direction:

- AI Software Engineer.
- AI Quality Engineer.
- Developer Productivity Engineer.

## Recommendation Pattern

Use this sequence for Guided Learning Intake recommendations:

1. Motivation.
2. Current level.
3. Branch.
4. Missing prerequisite.
5. Next study step.
6. Learning kata.
7. Evidence note.

Example:

Motivation: "I want to build useful AI apps."

Current level: "Comfortable with Python basics, new to retrieval."

Branch: RAG / LLM Applications.

Missing prerequisite: Embeddings and chunking.

Next study step: Build a tiny document Q&A prototype over three documents.

Learning kata: Compare two chunking strategies and write a short failure analysis.

Evidence note: Roadmaps consistently place embeddings, vector search, APIs, and evaluation near the center of practical AI application work.
