# Career Sources

This folder contains source material for Cognivia's future Guided Learning Intake direction.

The intake experience is expected to ask about a learner's motivation, what they enjoy about coding or learning, their goals, and current level. These sources support evidence-guided recommendations for an AI Engineering branch, possible role direction, and next study step.

## Folder Structure

- `pdfs/` contains only third-party source artifacts whose redistribution terms
  are documented for this repository.
- External roadmaps and infographics are represented by source links rather
  than copied binaries when redistribution permission is not established.
- `curated/` contains RAG-friendly Markdown summaries derived from the original sources.

Curated Markdown is preferred for RAG because it is less noisy than raw PDFs
and infographics. External source links and owner-written summaries preserve
traceability without implying that publicly accessible binaries may be
redistributed.

These sources are directional evidence for learning guidance. They should not be presented as deterministic career guarantees, salary guarantees, or proof that a learner will obtain a specific role.

## Source Registry

| Source | URL | Type | Local artifact | Use in Cognivia | Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| PwC 2026 Global AI Jobs Barometer | https://www.pwc.com/gx/en/issues/artificial-intelligence/job-barometer/2026/2026-global-ai-jobs-barometer-full-report.pdf | PDF report | External link only | Labor-market signal; AI-exposed jobs; AI skills; wage premium; human expertise, judgment, and creativity | High | Binary excluded because local redistribution permission was not established. Use as directional labor-market evidence, not a promise of specific job or salary outcomes. |
| Coursera Job Skills Report 2026 | https://www.coursera.org/skills-reports/job-skills | PDF report | External link only | Fastest-growing skills; GenAI skills; Data, IT, and Software & Product Development; critical thinking, debugging, responsible AI | High | Binary excluded because local redistribution permission was not established. Use the official Coursera URL for attribution. |
| Dataquest AI Engineer Roadmap 2026 | https://www.dataquest.io/blog/ai-engineer-roadmap/ | Web roadmap/article | Not available locally | Practical AI Engineer learning path; beginner/intermediate sequence; project and portfolio orientation; AI Engineer vs ML Engineer distinction | High | Summarize into Markdown before RAG ingestion. |
| roadmap.sh AI Engineer | https://roadmap.sh/ai-engineer | Visual roadmap | External link only | Technical AI Engineering taxonomy: LLMs, embeddings, vector databases, RAG, prompt engineering, agents, safety, APIs | High | Binary excluded because local redistribution permission was not established. Prefer curated Markdown for RAG. |
| roadmap.sh AI Agents | https://roadmap.sh/ai-agents | Visual roadmap | External link only | Agents, tools, memory, architectures, evaluation, observability, security | High | Binary excluded because local redistribution permission was not established. Prefer curated Markdown for RAG. |
| Skills for the future software profession: beyond agentic AI! | https://arxiv.org/abs/2606.21894 | Research paper / PDF | External link only | Human-AI Coding / Code Quality; verification and validation; executable specifications; cognitive debt; future software engineering skills in the agentic AI era | High | Binary excluded because local redistribution permission was not established. |
| AI Skills Improve Job Prospects | https://arxiv.org/abs/2601.13286 | Research paper / PDF | External link only | Evidence that AI skills can improve hiring signals; career motivation evidence | Medium | Binary excluded because local redistribution permission was not established. Hiring-signal evidence is not a deterministic employment guarantee. |
| Stanford AI Index Report 2026 | https://hai.stanford.edu/assets/files/ai_index_report_2026.pdf | PDF report | `pdfs/stanford_ai_index_2026.pdf` | Broad AI ecosystem context: adoption, economy, education, evaluation, policy | Medium | Do not make this the main RAG source because it is broad and large. |
| Research Roadmap for Augmenting Software Engineering Processes and Software Products with Generative AI | https://arxiv.org/abs/2510.26275 | Research paper / PDF | External reference only | Advanced source for GenAI-augmented software engineering and human-AI software process transformation | Low / optional for MVP | The former local file was a byte-identical, mislabeled duplicate of the *Skills for the future software profession* paper and was removed. No replacement was downloaded. |
| Microsoft AI Skills Navigator | https://aiskillsnavigator.microsoft.com/ | Interactive learning navigator | Not available locally | Inspiration for Guided Learning Intake; role-based AI skill paths; AI learning navigation | Medium | Use as product and learning-path inspiration, not as labor-market evidence. |
| Coursera AI Learning Roadmap | https://www.coursera.org/resources/ai-learning-roadmap | Web learning roadmap | Not available locally | General AI learning progression; foundations and prerequisites | Medium | Useful for beginner-friendly sequencing. |

## Available Local Files

Retained PDF source artifact:

- `pdfs/stanford_ai_index_2026.pdf` — retained unmodified under the CC BY-ND
  4.0 notice contained in the PDF.

All other sources in the registry are external references or are represented by
owner-written curated cards. See
[`THIRD_PARTY_NOTICES.md`](../../../THIRD_PARTY_NOTICES.md) for redistribution
status.

## Curated Cards

- `curated/ai_job_market_signals.md` summarizes directional labor-market and hiring-signal evidence.
- `curated/ai_engineering_learning_paths.md` summarizes branch and learning-path guidance for Guided Learning Intake.
- `curated/human_ai_coding_quality.md` summarizes why Human-AI Coding / Code Quality belongs as a Cognivia branch.
