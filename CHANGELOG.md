# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog 1.1.0, and this project uses Semantic
Versioning 2.0.0.

## [Unreleased]

### Changed

- Extracted deterministic learning-plan and reflection Markdown formatting to
  `tools/learning_exports.py` while retaining Streamlit coordination in
  `app.py`.
- Extracted deterministic evidence interpretation to
  `tools/noise_to_signal_evidence.py` while retaining graph orchestration and
  compatibility seams in `tools/noise_to_signal_graph.py`.
- Clarified the relationship between private development history and the
  sanitized public repository baseline.

## [0.1.0] - 2026-09-01

### Added

- Published the sanitized Cognivia baseline as a Python and Streamlit
  application.
- Included the bounded Noise-to-Signal workflow, local RAG components,
  provider configuration boundary, optional learner-memory foundation, and
  reviewer-facing documentation present in the public baseline.

### Security

- Removed private repository history and publication-excluded material from
  the public baseline instead of reproducing the private commit graph.
