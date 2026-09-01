# Cognivia Project Status

## 1. Snapshot

- **Date:** 2026-08-03
- **Current branch:** `feature/ux-v2-hardening`
- **Closeout base commit:** `a30cf9a917f30fc6073fa68824d339ac0bb00bf8` (`feat: finalize the Cognivia clarity experience`, 2026-07-29)
- **Closeout status:** The validated UX v2 closeout commits remain intact. The latest two independent P2 findings are corrected, and the branch awaits one final PR-style review against `main`. The isolated suite is fully green at `518 passed, 0 failed`.
- **Scope reviewed:** The authoritative audit at `docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md`; current and HEAD versions of `app.py`; `.streamlit/config.toml`; brand assets; frontend tests; README; architecture, validation, smoke-test, code-map, reviewer, and historical UX documentation; recent frontend Git history; the direct recommendation-to-learning-path state flow; and defined test, lint, compile, diff, sentinel, and startup commands.

## 2. Executive Summary

The current frontend is a working local Streamlit application whose primary reviewed flow is Noise-to-Signal. The branch contains a hardening patch aimed at F-02 through F-08 plus a focused correction to the post-recommendation learning flow. Learning schemas and maps now use the graph result's structured selected alternative instead of treating an original two-option decision question as one combined topic. Focused frontend validation passes, and the offline Streamlit server responds successfully. The patch gives direct source-and-test evidence that F-05 through F-08 are resolved at the code level.

The validated closeout baseline now includes focused review-followup corrections and the complete isolated suite passes (`518 passed, 0 failed`). The correction is ready for a fresh PR-style review against `main`; it has not been merged or pushed. The user manually checked the principal frontend behavior before these corrections, but the supported browser-control runtime was unavailable for an independent post-correction browser pass. The broader F-01 audit finding and the remaining browser-dependent parts of F-02 through F-04 remain documented follow-up work. `app.py` also remains a presentation monolith with substantial CSS and parent-document JavaScript coupling.

### Post-review correction (2026-08-03)

- All three selectors intended to target the Streamlit sidebar root now use the tag-agnostic `[data-testid="stSidebar"]`: the scoped secondary-drawer CSS, the secondary-drawer JavaScript controller, and the Focus Mode hiding rule. The pinned Streamlit 1.56.0 frontend renders that root as a `section`.
- The nested `stSidebarContent`, `stSidebarHeader`, `stSidebarUserContent`, and `stSidebarCollapseButton` selectors were inspected against the pinned frontend and remain narrowly targeted as `div` elements. Tests continue to protect drawer height, sticky toggle, vertical scrolling, horizontal-overflow containment, stable drawer ID, and `aria-label`, `aria-expanded`, and `aria-controls` semantics.
- Focus Mode state and separate enter/exit controls are unchanged. Its CSS now embeds 128×128 RGBA UI derivatives rather than the original 1254×1254 sources. The originals remain unchanged.
- Original icon sizes are 1,026,012 and 1,069,467 bytes; optimized sizes are 4,998 and 6,938 bytes. Combined base64 payload fell from 2,793,972 to 15,916 characters, a 99.43% reduction and well below the 100 KB target.
- The selector/Focus Mode correction passed its focused, frontend, and complete isolated validation. Browser validation remains pending because the supported browser-control runtime was not exposed in this session.
- The broader F-01 audit finding remains follow-up work; this correction addresses only the reviewed Focus Mode icon payload. No broader frontend refactoring or redesign was performed, and the authoritative audit was not modified.

### Final review follow-up (2026-08-03)

- Interview Coach again applies adaptive Max Tokens defaults of 1200, 1800, and 3000 while the control remains automatic. An explicit Interview Coach-scoped override flag preserves genuine user choices across question-count changes; leaving and returning retains the existing reset behavior and does not affect Cognivia or AI Skill Compass state.
- The intro controller now uses the established guarded same-origin parent/local context pattern before accessing the document or animation-frame APIs. Local and same-origin behavior is unchanged, while inaccessible cross-origin parents exit safely.
- Current-session validation passed: 13 focused regression tests, 118 frontend tests, 518 complete isolated tests, Ruff, `py_compile`, `git diff --check`, and Sentinel (advisory).

## 3. What Currently Works

The following statements are supported by current-session checks:

- The app compiles with Python 3.14.3 and starts in safe offline mode with Streamlit 1.56.0. Both `/` and `/_stcore/health` returned HTTP 200.
- The focused Streamlit suites pass: `118 passed` across `tests/test_noise_to_signal_app.py` and `tests/test_noise_to_signal_ui_copy.py`.
- AppTests cover the intro lifecycle, minimal search home, quick prompts, normal single submission, loading and error cleanup, Focus Mode state, New search reset, guided intake, evidence states, learning-path selection, Study notes, memory degradation, and exports.
- A normal search calls the graph once across the tested rerun path; this does **not** prove protection against rapid browser events. See `tests/test_noise_to_signal_app.py:815` and `:851`.
- Selecting a learning path updates the recommendation summary to the selected schema without another graph call in AppTest. See `app.py:3271-3285`, `:3432-3473`, `:3798-3810`, and `tests/test_noise_to_signal_app.py:2446-2489`.
- Helper-tip text now uses `#94A8B3`; the current contrast test measures 6.67:1 against `#111F38`. See `app.py:83`, `:1052`, `:2544-2570`, and `tests/test_noise_to_signal_app.py:1608-1625`.
- New search has a native Streamlit label and no longer depends on MutationObserver repair. See `app.py:1537-1555`, `:4284-4301`, `:4583-4591`, and `tests/test_noise_to_signal_app.py:1016-1064`.
- The compact callout class now has a matching scoped style and a rendering regression test. See `app.py:1578-1587`, `:2607-2628`, and `tests/test_noise_to_signal_app.py:1628-1649`.
- The sidebar runtime summary card was removed in every mode. It now provides only **Runtime** and a collapsed **Technical details** disclosure; changing modes clears only the two runtime-disclosure states so the next mode starts collapsed. See `app.py:422-431`, `:542-747`, and `tests/test_noise_to_signal_app.py:1731-1795`.
- Cognivia’s Runtime drawer remains one continuous panel with only Runtime, mode, Memory, and Evidence permanently visible. Its collapsed Technical details use concise label/value lines (Mode, Provider, Memory, Persistence, Evidence, API credits), with no explanatory runtime paragraphs or nested card. Runtime detection and backend behavior remain unchanged. See `app.py:434-535`, `:823-952`, and `tests/test_noise_to_signal_app.py:1513-1604`.
- The shared AI Skill Compass / Interview Coach drawer retains viewport-constrained vertical scrolling, safe wrapping, bottom padding, and sticky top `<< / >>` control. Its sidebar now uses the same concise collapsed label/value Technical details and no duplicate runtime summary card. Both surfaces share normalized runtime data but intentionally use different markup. Browser validation remains pending because the supported browser-control surface was unavailable. See `app.py:434-747` and `tests/test_noise_to_signal_app.py:1578-1795`.
- Interview Coach no longer renders a Temperature control or explanation. Its exact registered-model policy omits `temperature` for GPT-5 mini and GPT-5 nano and sends internal `temperature=1.0` for MiniMax M2.7; Max tokens remains user-configurable. Model and Max tokens now use Interview Coach-specific state keys, and stale temperature state is ignored. Cognivia retains its independent fixed classifier configuration, while AI Skill Compass remains unchanged. Deterministic tests use mocked clients and make no live provider calls; browser validation remains pending. See `app.py:119-165`, `:4935-4990`, and `tests/test_noise_to_signal_app.py:1442-1602`.
- Direct post-recommendation learning schemas, schema selection, maps, notes, and plan exports use the structured `selected_focus` (or structured `recommended_direction`) when present. The original two-option question is no longer converted into a combined learning topic. All three Learning Direction Schemas and the Learning Path Map remain available; deterministic tests cover both RAG evaluation and LangGraph selections. Standalone roadmap fallback and Guided Intake retain their existing goal-based behavior. No prompt parser, generic comparison support, graph change, backend change, or schema-module change was introduced. Browser validation remains pending.
- Ruff passes across the complete repository, `python -m py_compile app.py` passes, `git diff --check` passes, and the local sentinel gate passes/advisory.
- The core `tools/`, `rag/`, and `memory/` packages contain no Streamlit imports, preserving the UI/domain boundary identified by the audit.

## 4. Audit Reconciliation

`docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md` is authoritative. Statuses below describe the current working tree, not only HEAD.

| Finding | Status | Evidence | Remaining Work |
| --- | --- | --- | --- |
| **F-01 — Oversized base64 assets** | **Partially resolved** | Focus Mode now embeds 128×128 UI derivatives sized 4,998 and 6,938 bytes instead of the unchanged 1254×1254 sources. Their combined encoded payload is 15,916 characters, down from 2,793,972 (99.43%). Focus Mode controls remain 52×52 px with 44×44 px pseudo-elements. | Keep the broader F-01 finding open for the repository's other embedded assets and complete a browser payload/paint check. This correction closes only the independent review finding for the two Focus Mode icons. |
| **F-02 — Unsafe parent-document controllers** | **Partially resolved** | Same-origin/local guards now exist in the runtime drawer, rerender guard, accessibility controller, and intro controller. Focused source regression tests protect the local, same-origin, and inaccessible-parent branches. | Verify graceful behavior under `?embed=true` or a real cross-origin host before closing the browser-dependent audit finding. |
| **F-03 — Responsive CSS may scroll horizontally** | **Partially resolved** | The runtime drawer now combines `box-sizing: border-box` with `width: min(340px, calc(100vw - 24px))` (`app.py:493-505`), and the rule is asserted at `tests/test_noise_to_signal_app.py:574-608`. The main stylesheet also has a 768 px breakpoint (`app.py:2332-2375`). No real narrow-viewport test was available, so the reported symptom is not disproved. | Test all three modes at narrow widths and inspect `document.documentElement.scrollWidth`; fix any remaining overflowing selector or control. |
| **F-04 — Processing flag is not a complete double-submit guarantee** | **Partially resolved** | The global Streamlit Enter shortcut was removed. A controller now handles Enter only for the main search input and ignores disabled submit controls (`app.py:4200-4214`, `:4325-4369`). `_submit_noise_to_signal_goal` still checks and sets the processing flag around the graph call (`app.py:3912-3958`). AppTests prove one call across a normal rerun and verify flag timing (`tests/test_noise_to_signal_app.py:815-868`). They do not simulate rapid browser click plus Enter. | Add browser coverage for rapid click, repeated Enter, and Enter in Guided Intake/note fields. If duplicates remain possible, add callback-boundary idempotency rather than relying only on presentation state. |
| **F-05 — Stale summary after path selection** | **Resolved** | Selection now runs in `on_click` before the rerender (`app.py:3432-3473`), and summary values are derived from the selected schema (`app.py:3271-3285`, `:3798-3810`). Direct and guided AppTests assert that only the selected path appears in the summary and no extra graph call occurs (`tests/test_noise_to_signal_app.py:2446-2489`, `:2880-2909`). | No further code work identified for this finding. Include a visual confirmation in the final browser smoke test. |
| **F-06 — Helper-tip contrast fails WCAG AA** | **Resolved** | The old `#49636b` inline color was replaced by `--nts-helper-text: #94A8B3` (`app.py:83`, `:1052`, `:2563-2570`). The measured ratio is 6.67:1 against the card background, and the passing test requires at least 4.5:1 (`tests/test_noise_to_signal_app.py:1608-1625`). | No further code work identified. Confirm computed styles during the accessibility smoke test. |
| **F-07 — New search name depends on MutationObserver** | **Resolved** | The authoritative button label is now `New search` (`app.py:4583-4591`); its text is visually clipped instead of removed (`app.py:1537-1547`); and New search was removed from the observer label map (`app.py:4284-4301`). The AppTest verifies the native label and absence of observer repair (`tests/test_noise_to_signal_app.py:1016-1043`). | No further code work identified for New search. Focus Mode and example controls still use observer-applied labels and need browser accessibility-tree coverage. |
| **F-08 — Missing callout stylesheet** | **Resolved** | `.nts-results-compact-callout` is defined at `app.py:1578-1587`, used at `app.py:2607-2628`, and tested for rendered markup plus scoped border/background/color at `tests/test_noise_to_signal_app.py:1628-1649`. | No further code work identified. Confirm the final appearance in the browser smoke test. |
| **Additional audit boundary — UI hand-authors a decision dict** | **Pending** | `_start_noise_to_signal_guided_intake` still constructs a graph-shaped `needs_clarification` dictionary in `app.py:3972-3997`. This duplicates part of the graph contract in the presentation layer. | In a separately approved change, route the transition through a canonical domain helper or graph API with focused contract tests. Do not combine this with visual hardening. |

## 5. Known Issues

- The obsolete bottom-level source-layout assertion has been replaced with function-scoped AST checks. The regression now confirms that `_render_noise_to_signal_home` routes normal submissions through `_submit_noise_to_signal_goal`, that the helper delegates exactly once to `run_noise_to_signal`, and that neither presentation-layer function calls `retrieve_relevant_chunks`. Current offline-isolated result: `518 passed, 0 failed`.
- F-01 is still open beyond the corrected Focus Mode assets and remains follow-up work.
- F-02 through F-04 cannot be closed without the remaining real-browser checks.
- No Playwright/browser smoke suite exists, and browser automation was unavailable in this session.
- `app.py` has 5,296 lines and 104 top-level function definitions. It contains 323 `!important` occurrences, 146 `st-key-` selector occurrences, and 12 `window.parent` occurrences. These numbers describe coupling and specificity risk; they do not by themselves prove a user-visible defect.
- `app.py:3972-3997` duplicates a decision-shaped graph contract for the Guided Intake entry path.
- Current-facing documentation is stale about Focus Mode: code and commit `a30cf9a` implement it, while `README.md:62`, `docs/architecture.md:5`, `docs/current-state-validation-and-next-steps.md:53`, and other reviewer docs still call it future work.
- The documented `.venv/bin/python` command is unavailable in this worktree. Validation succeeded with the system Python 3.14.3 environment, which has the pinned pytest 9.0.3, Ruff 0.15.12, and Streamlit 1.56.0 packages.
- There is no configured static type checker (`pyproject.toml`, `mypy.ini`, and `pyrightconfig.json` are absent), so no project-defined type-check command could be run.
- The sidebar still exposes Noise-to-Signal, AI Skill Compass, and Interview Coach, and AI Skill Compass still exposes `Run RAG evaluation` (`app.py:124-139`, `:4689-4702`, `:5122-5154`). This is verified product scope, not evidence that those secondary modes received equivalent browser validation.

### Deferred — Comparison / “vs” intent

Cognivia currently supports decision-oriented prompts, not generic factual comparisons. “A vs B” must not be exposed as a quick prompt until the domain layer can distinguish a decision between alternatives from a neutral comparison request. A future implementation should determine whether the user wants:

- help choosing or prioritizing one of two options; or
- a neutral factual comparison of those options.

This work is intentionally deferred and must not be implemented through frontend-only prompt rewriting or additional heuristics in `app.py`. The temporary comparison experiment was rolled back in favor of the previous known-good decision-oriented prompt, “Should I learn LangGraph or RAG evaluation?”

## 6. Decisions Already Reflected in the Code

- **Streamlit remains the frontend framework and single entrypoint.** `app.py` owns page bootstrap, sidebar mode selection, rendering, session state, CSS, JavaScript, and frontend orchestration.
- **Noise-to-Signal is the primary reviewer-facing flow, but legacy surfaces remain reachable.** `APP_MODES` contains three entries at `app.py:124-139`.
- **The domain core remains independent of Streamlit.** `tools/`, `rag/`, and `memory/` have no Streamlit imports; `app.py:3912-3958` calls the graph through a single submission helper.
- **Evidence and uncertainty remain first-class UI states.** `app.py:156-177`, `:2423-2502`, and `:3656-3734` render decision status, evidence quality, attempts, insufficient-evidence copy, trace, and technical details.
- **The current clarity experience includes a short intro, minimal home, quick prompts, Focus Mode, results tabs, and a New search reset.** These were introduced/finalized by commit `a30cf9a` and are present at `app.py:4000-4255` and `:4550-4603`.
- **Learning-path selection is local presentation state; it does not rerun the graph.** Selection and export use stored `LearningDirectionSchema` values (`app.py:3261-3479`), and the passing AppTest asserts the graph call count is unchanged.
- **Safe offline execution is an explicit runtime mode.** README and architecture docs define `COGNIVIA_LLM_PROVIDER=offline`; concise runtime state is visible in the Noise-to-Signal drawer, while each sidebar keeps only collapsed Technical details (`app.py:422-747`).
- **Local Qdrant, append-only memory boundaries, and conservative fallback behavior remain backend choices.** The frontend patch does not modify `tools/`, `rag/`, `memory/`, provider, prompt, schema, or security modules.
- **The frontend currently uses injected CSS and parent-document JavaScript rather than a component framework.** This is demonstrated by `_render_noise_to_signal_styles`, `_install_app_rerender_stability_guard`, the runtime drawer, intro controller, and accessibility controller; it is also the audit’s highest-risk architectural area.

## 7. Test and Validation Status

### Commands executed and results

| Command | Result |
| --- | --- |
| `codex login status` | Passed; Codex reported ChatGPT login, not OpenRouter. |
| `python --version` | Passed: Python 3.14.3. |
| `python -m pytest --version` | Passed: pytest 9.0.3. |
| `python -m ruff --version` | Passed: Ruff 0.15.12. |
| `python -c 'import streamlit; print("streamlit", streamlit.__version__)'` | Passed: Streamlit 1.56.0. |
| `python -m pytest tests/test_noise_to_signal_app.py -q -k 'decision_learning_paths_use_the_structured_recommended_alternative or standalone_learning_request_keeps_its_original_learning_subject or new_prompt_clears_previous_selected_path_and_note_state or new_search_reuses_reset_without_intro_or_submission or guided_intake_renders_learning_direction_options or decision_quick_prompts_continue_to_submit_normally or has_no_frontend_comparison_preflight or runtime_status'` | Passed: 12 tests; 88 deselected in 19.31s. |
| `python -m pytest tests/test_noise_to_signal_app.py -q -k 'secondary or runtime_drawer or runtime_status or non_cognivia_modes or page_config_collapses or sidebar_visible_labels'` | Passed: 14 tests, 89 deselected in 8.81s. |
| `python -m pytest tests/test_noise_to_signal_app.py -q -k 'runtime_drawer or runtime_drawers_share_data or secondary_runtime_drawer or secondary_project_drawer or secondary_modes_render'` | Passed: 7 tests, 97 deselected in 5.57s. |
| `python -m pytest tests/test_noise_to_signal_app.py -q -k 'focus_mode or secondary_project_drawer'` | Passed: 4 tests; 105 deselected in 7.23s. |
| `python -m pytest tests/test_noise_to_signal_app.py -q -k 'interview_coach or intro_controller or runtime_drawer or focus_mode'` | Passed: 13 tests; 98 deselected in 12.15s. |
| `python -m pytest tests/test_noise_to_signal_app.py tests/test_noise_to_signal_ui_copy.py -q` | Passed: 118 tests in 101.17s. |
| `python -m pytest tests/test_noise_to_signal_graph.py::test_noise_to_signal_app_branch_does_not_pre_retrieve -q` | Passed: 1 test in 3.07s. |
| `python -m pytest tests/test_noise_to_signal_graph.py -q` | Passed: 110 tests in 6.84s. |
| `python -m pytest tests/test_openrouter_client.py -q` | Passed: 29 tests in 0.08s. |
| `env -u OPENAI_API_KEY -u OPENROUTER_API_KEY -u COGNIVIA_LLM_PROVIDER -u LANGSMITH_API_KEY -u LANGCHAIN_API_KEY LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests -q` | Passed: 518 tests in 117.49s. |
| `python -m ruff check app.py tests` | Passed. |
| `python -m ruff check .` | Passed. |
| `python -m py_compile app.py` | Passed. |
| `git diff --check` | Passed before this document was added; rerun after the document edit also passed. |
| `bash scripts/sentinel.sh` | Passed/advisory; no network or provider calls. |
| `enable_openai_cognivia` followed by `.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8503` | The first sandboxed bind failed with `PermissionError`; the approved local rerun started with the user-supported OpenAI setup without reconstructing credentials. |
| `curl -sS http://127.0.0.1:8503/_stcore/health` | Passed: body `ok`. |

Read-only inspection also used `git status`, `git log`, `git show`, `git diff`, `git blame`, `git rev-parse`, `rg`, `sed`, `nl`, `wc`, `find`, `du`, and image metadata checks against the paths named in the Snapshot. The post-review correction changed only `app.py`, `tests/test_noise_to_signal_app.py`, the two new optimized Focus Mode assets, and this status document. It did not install dependencies, change branches, rewrite existing commits, merge, or push.

### Limitations and pending manual checks

- No configured static type-check command exists.
- HTTP health confirms server startup, not rendered browser behavior.
- The supported browser-control tool was unavailable, so the secondary drawer’s desktop/narrow/short viewport, toggle, scroll reachability, horizontal overflow, disclosure, and live accessibility checks remain pending. Server health alone is not counted as browser validation.
- All three sidebar modes were inspected in source and exercised with AppTest. Real-browser validation remains pending.
- The authoritative audit is included in the closeout documentation commit under `docs/audits/`.

## 8. Current Blockers

No blocker remains within the approved UX v2 closeout scope. The complete isolated suite is green.

The following broader audit items remain explicit follow-up work:

1. F-01 remains broader follow-up work after the Focus Mode asset payload correction.
2. Browser-dependent acceptance checks for F-02 through F-04 remain incomplete.

There is no blocker to continuing local work in the existing Python environment.

## 9. Immediate Next Step

Run a fresh PR-style `/review` against `main`. Do not merge or push before that independent review, and do not treat the broader F-01 or browser-dependent audit findings as resolved by this correction.

## 10. Next Three Steps

1. Run a fresh PR-style `/review` against `main`, with the corrected sidebar-root selectors and measured Focus Mode payload as primary review targets.
2. Add a compact browser smoke suite covering embedded mode, rapid Enter/click submission, and a narrow viewport.
3. After code and browser validation are green, update current-facing documentation to reflect implemented Focus Mode and archive or clearly label `docs/ux_v2/FRONTEND_AUDIT.md` as historical.

## 11. Definition of Done for the Frontend

The frontend is ready to merge or deploy within the documented local project scope when all of the following are true:

- F-01 is resolved with measured payload evidence; F-02 through F-04 are either resolved or explicitly accepted with documented browser evidence; F-05 through F-08 remain protected by regression tests.
- `python -m pytest tests -q`, `python -m ruff check .`, `python -m py_compile app.py`, `git diff --check`, and `bash scripts/sentinel.sh` pass in the intended environment.
- Safe offline startup succeeds without provider calls, raw exceptions, secrets, or a required durable database.
- Browser smoke checks show no horizontal overflow at agreed desktop and narrow widths, no controller failure in embedded mode, and exactly one graph submission for click, Enter, and rapid repeated interaction.
- Keyboard traversal has visible focus; New search, Focus Mode, example controls, tabs, and disclosures have stable accessible names in the accessibility tree; helper text meets WCAG AA computed contrast.
- Intro, search, loading, result, path selection, New search, Guided Intake, Study note, memory fallback, and exports work without stale content or unexpected state loss.
- Noise-to-Signal, AI Skill Compass, and Interview Coach either pass the agreed smoke scope or are explicitly excluded from the shipped surface.
- Current-facing README and architecture/reviewer docs match implemented behavior and current-session validation; historical audits are clearly labeled.
- The final diff contains only approved files, receives final review, and has no unresolved P1/P2 correctness, accessibility, data-loss, security, or regression finding.
- Public deployment is not claimed unless authentication, privacy, multi-user isolation, persistence, resource, secret, and deployment concerns are separately validated.

## 12. Recovery Notes

Authoritative context:

- Audit: `docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md`.
- Historical context only: `docs/ux_v2/FRONTEND_AUDIT.md`.
- Branch and closeout base: `feature/ux-v2-hardening` / `a30cf9a917f30fc6073fa68824d339ac0bb00bf8`.
- The F-02-through-F-08 frontend hardening is grouped with its regression coverage in the closeout implementation commit.
- Current isolated validation baseline: `518 passed, 0 failed`.

Minimum resume commands:

```bash
cd <repository-worktree>
git branch --show-current
git rev-parse HEAD
git status --short
git diff -- app.py tests/test_noise_to_signal_app.py
sed -n '1,240p' docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md
sed -n '1,280p' PROJECT_STATUS.md

env -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  -u COGNIVIA_LLM_PROVIDER -u LANGSMITH_API_KEY -u LANGCHAIN_API_KEY \
  LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests -q
python -m ruff check .
python -m py_compile app.py
git diff --check
```

For a local OpenAI-backed Streamlit session, use the interactive zsh alias `enable_openai_cognivia`. This is the user-provided supported setup path; do not print or manually reconstruct provider credentials.

Safe offline startup:

```bash
env -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  COGNIVIA_LLM_PROVIDER=offline \
  LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m streamlit run app.py
```

Do not merge, push, reset, or discard the branch without fresh authorization.
