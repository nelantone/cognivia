# Public Career and Skill Sources for AI Skill Compass

This document catalogs public, external sources that enhance the RAG knowledge base with authoritative career and skills information. These sources provide factual, up-to-date data that complements curated notes.

---

## 1. WEF Future of Jobs Report 2025

### What the Source Is

The World Economic Forum's *Future of Jobs Report 2025* is a global survey-based report published every 2-3 years that analyzes employment trends, skill demands, and workforce transformations across industries and countries. The 2025 edition covers 1,000+ companies worldwide.

**Source URL**: https://www.weforum.org/publications/the-future-of-jobs-report-2025/

### Source Metadata

| Field | Value |
|-------|-------|
| Publication page | https://www.weforum.org/publications/the-future-of-jobs-report-2025/ |
| PDF download | https://reports.weforum.org/docs/WEF_Future_of_Jobs_Report_2025.pdf |
| Coverage | 1,000+ companies, 22 industries, 57 economies |
| Publication cycle | Every 2-3 years |

### Why It Is Useful for AI Skill Compass

- Provides authoritative, globally-recognized data on which jobs are growing and declining
- Identifies top skills demanded by employers across industries
- Contains migration patterns (skills entering/leaving job roles)
- Helps answer questions about market trends and skill relevance
- Data-backed, not opinion-based

### What Kind of Questions It Can Help Answer

- Which tech jobs are growing fastest in 2025?
- What soft skills are employers prioritizing?
- Which skills are being automated or displaced?
- What is the projected job growth for software development roles?
- Which emerging skills should workers develop?

### Key Skill/Career Signals

- Job growth rates by occupation (2025-2030 projections)
- Skills decline/migration data (skills no longer required)
- Skills amplification data (skills becoming more important)
- Industry-specific employment trends
- Training and reskilling investment patterns
- Top 10 growing jobs and top 10 declining jobs

---

## 2. ESCO Skills and Occupations Framework

### What the Source Is

ESCO (European Skills, Competences, Qualifications and Occupations) is the EU's multilingual classification system that defines and interlinks occupations, skills, competencies, and qualifications. It covers 3,000+ occupations and 13,000+ skills.

**Source URL**: https://esco.ec.europa.eu/en

### Source Metadata

| Field | Value |
|-------|-------|
| Portal | https://esco.ec.europa.eu/en |
| CSV download | https://esco.ec.europa.eu/en/use-esco/download |
| REST API | https://esco.ec.europa.eu/en/use-esco/use-esco-services-api |
| Coverage | 3,000+ occupations, 13,000+ skills, 30+ languages |
| Maintenance | EU Commission, regular updates |

### Why It Is Useful for AI Skill Compass

- Provides standardized, structured skill taxonomy used across Europe
- Links skills to specific occupations with relationship strength
- Multilingual support (30+ languages) enables international context
- Free, authoritative, and regularly maintained
- Maps skill pathways between jobs

### What Kind of Questions It Can Help Answer

- What skills does a software developer need?
- How are related occupations (e.g., frontend vs backend dev) different in skill requirements?
- What alternative job titles exist for a given skill set?
- What is the skill hierarchy (broad occupation → specific skill)?
- Which transversal skills transfer across jobs?

### Key Skill/Career Signals

- Occupation-to-skill mappings with essential/optional flags
- Skill synonymy and alternative term mappings
- ISCO occupation classification alignment
- Transversal (cross-cutting) skills identification
- Skill level indicators (elementary ↔ expert)
- Occupation descriptions and typical tasks

---

## 3. BLS Occupational Outlook for Software Developers and Web Developers

### What the Source Is

The U.S. Bureau of Labor Statistics (BLS) Occupational Outlook Handbook provides detailed, regularly updated career profiles including job duties, education requirements, pay data, and job outlook projections. Specifically covers:

- **Software Developers** (SOC 15-1252): https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm
- **Web Developers** (SOC 15-1254): https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm

### Source Metadata

| Field | Value |
|-------|-------|
| Software Developers | https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm |
| Web Developers | https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm |
| Projection period | 2024–2034 |
| Update frequency | Monthly/annually |

### Why It Is Useful for AI Skill Compass

- Authoritative US government data source (BLS)
- Regularly updated with accurate employment projections
- Contains salary ranges by experience level and location
- Detailed job descriptions explain day-to-day work
- Education and certification requirements clearly stated
- Job outlook (fast/slow growth) with percentage projections

### What Kind of Questions It Can Help Answer

- How much do software developers earn (median, by experience)?
- What education or certifications are required for dev roles?
- Is the job market growing or shrinking?
- What do developers actually do day-to-day?
- What are typical entry requirements for junior developers?
- How do web developer roles differ from software developer roles?

### Key Skill/Career Signals

- Employment projections (2024-2034 growth percentages)
- Median annual wage data
- Education requirements (bachelor's, bootcamp, self-taught paths)
- Licensing/certification requirements
- Typical work activities and tasks
- Industry breakdown (what sectors hire developers)
- Entry-level requirements and advancement paths

---

## How These Sources Improve RAG-Worthiness

These external sources strengthen the RAG knowledge base in several ways:

1. **Authoritative grounding** — Factual, institution-backed data reduces hallucination risk. When the LLM retrieves context from these sources, it cites verifiable facts rather than speculation.

2. **Structured skill taxonomies** — ESCO's occupation-skill linkages provide hierarchical context that helps the retriever find semantically related skills and roles. This improves recall for queries like "what skills does a backend developer need?"

3. **Temporal relevance** — WEF and BLS projections (2024–2034) give the system up-to-date market context. The retriever can surface current growth trends rather than outdated information.

4. **Multilingual capability** — ESCO's 30+ language coverage enables the system to handle queries in different languages or provide international job market context.

5. **Traceable citations** — Source metadata tables make it easy to reference the origin of any retrieved fact, improving user trust and enabling verification.

---

## Future Improvements

### Current MVP Approach

This MVP currently uses **local Markdown summaries** — curated notes that distill key insights from the sources above. This keeps the knowledge base lightweight and fast to retrieve from.

> **Note**: The MVP does not fetch these URLs live. Summaries are stored locally with official links for attribution and future verification. Summaries are written in my own words and avoid copying long passages from original sources.

### Planned Enhancements

Future iterations could ingest these sources more directly:

1. **PDF ingestion** — Parse WEF's full PDF report to capture granular data beyond the summary
2. **CSV/JSON ingestion** — Use ESCO's downloadable datasets for complete occupation-skill mappings
3. **API integration** — Query ESCO's REST API and BLS data programmatically for real-time updates
4. **Live data feeds** — Subscribe to WEF data releases when available

These enhancements would reduce manual curation effort and improve data freshness.

### Other Opportunities

- **LinkedIn Economic Graph**: Real-time labor market trends (requires API access)
- **Burning Glass/Lightcast**: Detailed skill demand analytics (commercial source)
- **GitHub Octoverse**: Open source skill trends and language popularity
- **Stack Overflow Developer Survey**: Annual developer skill and salary data

---

## Source Quality Notes

- Sources above may be public domain, licensed for particular uses, or merely
  publicly accessible. Public accessibility alone does not grant redistribution
  permission.
- Data is **regularly updated** by authoritative institutions
- No paid or access-controlled source content is represented as redistributable.
- Publicly accessible sources are represented with attribution links. Any
  production or commercial use should review each original source's license and
  terms.
- Sources complement each other: global trends (WEF) + skill taxonomy (ESCO) + US market specifics (BLS)

---

## Document Metadata

- **Purpose**: Enhance RAG retrieval with authoritative external career/skill data
- **Created**: 2026-05-25
- **Update cycle**: Review quarterly or when sources publish new editions
- **RAG relevance**: High - provides factual grounding for skill recommendations and career guidance
