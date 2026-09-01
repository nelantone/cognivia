# Cognivia Frontend Architecture Audit

**Date:** 2026-08-08
**Branch:** `refactor/frontend-architecture`
**Scope:** Read-only. No refactor implemented. No UX/backend changes.
**Baseline:** `app.py` is 5,637 lines (grown from 5,296 at the 2026-08-03
closeout referenced in `PROJECT_STATUS.md`). Validated baseline: 518 tests
passing (not re-run in this audit — see Validation).

This document extends, and does not replace, the authoritative
`docs/audits/COGNIVIA_FRONTEND_AUDIT_FINAL.md`. That audit is UX/defect
focused (F-01…F-08); this one is structural and targets a phased extraction
of `frontend/` from `app.py`.

## 1. Executive diagnosis

`app.py` is a single Streamlit script combining page bootstrap, three modes'
presentation, ~1,350 lines of injected CSS, parent-document JavaScript
controllers, session-state initialization, memory-write orchestration, and
markdown export builders. It is imported as a module by tests (`import app`)
**and** executed as a script by `AppTest.from_file("app.py")` — both patterns
must keep working through any extraction.

Two of the three modes (Interview Coach, AI Skill Compass) are not even
function-wrapped: they are inline top-level `if`/`elif` script blocks
starting at line 4887 and 5033, mixing widget declarations, provider calls,
and rendering in the same scope as the mode-dispatch `if`. Noise-to-Signal
(the primary flow) is largely function-based and dispatched from one
`elif` branch at line 5032, which is the best-decomposed of the three.

The single highest-leverage, lowest-risk move is extracting the CSS block
(`_render_noise_to_signal_styles`, ~1,354 lines) and static theme/asset
helpers into `frontend/browser/styles.py` and `frontend/assets.py`, because
this code has no session-state coupling, no widget callbacks, and is called
from exactly one site.

The highest architectural risk is not size — it is that structural tests
read `app.py`'s literal source text and AST, and count elements (e.g.
"exactly 15 `st.expander` calls", "`st.rerun` not in `app_source`") across
the **whole file**. Extraction changes what counts as "the source" for those
assertions and will silently under-count if code moves without updating the
test's file target.

## 2. Current responsibility map

| Area | Functions / constants | Lines (approx) | Session-state keys | Tests | Extraction risk |
| --- | --- | --- | --- | --- | --- |
| Imports, constants, mode table | `APP_MODES`, `_app_mode_label`, `INTERVIEW_MODEL_*`, `RUNTIME_DETAIL_SESSION_KEYS` | 1–353 | — | Constant-value assertions (`test_...` at line 895) | Low |
| Runtime status/drawer (shared) | `_render_runtime_status`, `_runtime_presentation_data`, `_runtime_drawer_markup`, `_render_secondary_project_drawer`, `_render_noise_to_signal_runtime_drawer` | 439–1088 | `RUNTIME_DETAIL_SESSION_KEYS`, drawer-open keys | `test_noise_to_signal_app.py` runtime/drawer suite (~14 tests) | Medium — JS controller string literals asserted verbatim (`synchronizeDrawer`, `__cogniviaRuntimeDrawerOpen`) |
| Memory boundary | `get_memory_store`, `get_or_create_demo_learner_id`, `build_evidence_refs`, `_save_*_memory`, `_save_learning_direction_event`, `_learner_memory_snapshot`, `_render_learner_memory_history` | 1089–1431 | `MEMORY_STORE_SESSION_KEY`, `DEMO_LEARNER_ID_SESSION_KEY` | Indirect via Noise-to-Signal AppTests | Medium — calls `memory.PostgresMemoryStore`/`NullMemoryStore` (a domain boundary) |
| Browser controllers | `_install_app_rerender_stability_guard`, `_render_noise_to_signal_control_accessibility`, `_render_noise_to_signal_intro_video_controller` | 1448–1483, 4489–4638, 4748–4880 | none directly | Source-string assertions on JS content | High — `window.parent` guards (F-02) are logic worth preserving verbatim; string-literal tests are brittle to reformatting |
| CSS / theme | `_render_noise_to_signal_styles`, `APP_RERENDER_STABILITY_CSS`, `NOISE_TO_SIGNAL_HELPER_TEXT_COLOR`, asset constants | 92–104, 347–358, 1484–2838 | none | `getsource(...)`-based contrast/selector tests (~10 tests) | Low — pure string builder, no state, single call site |
| Noise-to-Signal home/search/result | `_render_noise_to_signal_home`, `_submit_noise_to_signal_goal`, `_render_noise_to_signal_result`, `_render_noise_to_signal_metrics/evidence/study_plan/trace/technical_details` | 2838–4746 | `noise_to_signal_last_decision`, `_last_goal`, `_processing`, `_thread_id`, `_intro_state`, `_focus_mode`, `_examples_open`, `_result_focus_requested` | Bulk of `test_noise_to_signal_app.py` (~90+ tests) | High — largest, most state-coupled, most-tested block |
| Learning-direction / Guided Intake | `_render_guided_intake_recommendation`, `_normalize_learning_direction_for_display`, `_render_learning_direction_schema*`, `_select_learning_direction_schema`, `_start_noise_to_signal_guided_intake` | 3025–4126, 4449–4476 | `GUIDED_RECOMMENDATION_SESSION_KEY`, `LEARNING_DIRECTION_*_SESSION_KEY`, `SELECTED_LEARNING_SCHEMA_SESSION_KEY` | Learning-path selection/schema tests | Medium-High — `_start_noise_to_signal_guided_intake` hand-authors a graph-shaped dict (pre-existing boundary duplication, noted in the authoritative audit) |
| Exports | `build_full_learning_plan_markdown`, `build_learning_reflection_markdown`, `_render_full_learning_plan_download`, `_render_learning_note_exports`, `_learning_note_export_payload` | 3440–3757 | `FULL_LEARNING_PLAN_MARKDOWN_SESSION_KEY`, `LEARNING_NOTE_EXPORT_SESSION_KEY` | Export-content tests | Low-Medium — pure builders plus two `st.download_button` render calls |
| Mode dispatch / init | Inline `if app_mode == ...` chain, session-state initialization | 4883–4887, 5032–5637 | initializes `noise_to_signal_thread_id` and ~7 others inline | AppTest end-to-end coverage | High — not function-wrapped; this is literally the code that should become `app.py`'s remaining body |
| AI Skill Compass mode | Inline block under `elif app_mode == "AI Skill Compass":` | 5088–5637 | tool-selection widget state (unnamed keys, Streamlit auto keys) | Not covered by the three frontend test files (no dedicated test file found) | High to extract (no function boundary yet), Low to leave in place |
| Interview Coach mode | Inline block under `if app_mode == "Interview Coach (Sprint 1 legacy)":` | 4887–5032 | `INTERVIEW_MODEL_SESSION_KEY`, `INTERVIEW_MAX_TOKENS_SESSION_KEY`, `_OVERRIDDEN_SESSION_KEY` | Referenced in `PROJECT_STATUS.md` narrative; no dedicated test file found | High to extract, Low to leave in place |

## 3. Highest coupling / risk

1. **Module-execution side effects.** `app.py` calls `st.set_page_config(...)`
   and `_install_app_rerender_stability_guard()` at import time, and the
   bottom of the file is a top-level `if/elif` chain, not a `main()`. Both
   `import_module("app")` (for attribute access) and `AppTest.from_file
   ("app.py")` (for full-script execution) rely on this. Any extraction must
   keep `app.py` importable with the same public names, or add explicit
   compatibility re-exports.
2. **Source-text and AST assertions scoped to `app.py` as a file.** Tests
   read `Path("app.py").read_text()` and `ast.parse()` it, then assert
   counts and substrings across the *entire file* (e.g. exactly 15
   `st.expander` calls, `"st.rerun" not in app_source`). Moving any code
   containing an `st.expander` call or `st.rerun` reference out of `app.py`
   changes what these tests measure, even though `import module` combined
   with `getsource(app.X)` calls for individual functions will still work
   after extraction (as long as `app.py` re-exports `X`).
3. **Inline, unwrapped mode bodies.** Interview Coach and AI Skill Compass
   are not functions — they are indented under module-level `if`/`elif`.
   Extracting them requires first wrapping each in a `_render_*(...)`
   function (a mechanical, behavior-preserving step) before the function can
   move to its own module.
4. **CSS/JS string literals asserted verbatim.** Several tests grep for
   exact JS identifiers (`synchronizeDrawer`, `__cogniviaRuntimeDrawerOpen`,
   `handleSearchKeydown`) inside `getsource(...)` output. This is fine after
   extraction as long as the string content is preserved unchanged — the
   fragility is to content edits, not to which module the function lives in.
5. **Memory writes as a frontend-embedded boundary.** `get_memory_store()`,
   `_save_noise_to_signal_memory`, and `_save_learning_direction_event` sit
   in `app.py` but call into the `memory` package (`PostgresMemoryStore`,
   `NullMemoryStore`). This is a legitimate frontend→domain boundary, not
   duplication, but it means a `frontend/` package will still import
   `memory`, `tools.*`, and `rag.*` directly — consistent with the existing
   architecture (`tools/`, `rag/`, `memory/` have no Streamlit imports, so
   the dependency arrow is one-directional and safe to preserve).

## 4. Session-state ownership

Session-state keys are namespaced per mode already (`noise_to_signal_*`,
`interview_coach_*`, `INTERVIEW_MODEL_SESSION_KEY`, etc.), which is good
existing hygiene. Ownership is currently implicit — keys are read/written
directly by whichever function needs them, not through an accessor module.
Observed groups:

- **Noise-to-Signal core**: `noise_to_signal_thread_id`, `_last_decision`,
  `_last_goal`, `_processing`, `_intro_state`, `_focus_mode`,
  `_examples_open`, `_result_focus_requested` — initialized inline at
  app.py:5033–5040+ inside the mode `elif`, not in a setup function.
- **Guided intake / learning direction**: `GUIDED_RECOMMENDATION_SESSION_KEY`
  family and `LEARNING_DIRECTION_*` family, cleared by
  `_clear_learning_direction_state` / `_clear_guided_recommendation_state`.
- **Interview Coach**: `INTERVIEW_MODEL_SESSION_KEY`,
  `INTERVIEW_MAX_TOKENS_SESSION_KEY`, and an "overridden" flag that survives
  question-count changes (documented behavior in `PROJECT_STATUS.md` §3).
- **Runtime drawer disclosure state**: `RUNTIME_DETAIL_SESSION_KEYS`, reset
  by `_reset_runtime_detail_expansion` on mode change.

No cross-mode key collisions were found in this pass; namespacing already
follows the `AGENTS.md` convention. A `frontend/state.py` module would
formalize ownership (typed accessors per namespace) without changing key
names or reset semantics — a documentation/ergonomics win, not a bug fix.

## 5. CSS/JS ownership

- All CSS lives in one function, `_render_noise_to_signal_styles`
  (app.py:1484–2838, ~1,354 lines), injected once via `st.html`/`st.markdown`
  from the Noise-to-Signal branch. It has zero session-state reads and one
  call site — the cleanest extraction candidate in the file.
- Parent-document JavaScript controllers are split across three functions:
  `_install_app_rerender_stability_guard` (rerender stability),
  `_render_noise_to_signal_runtime_drawer`'s embedded script (drawer sync),
  and `_render_noise_to_signal_control_accessibility` /
  `_render_noise_to_signal_intro_video_controller` (accessibility labels,
  Enter-key handling, intro video). All follow the same
  same-origin-guarded `window.parent` pattern noted as resolving F-02.
  This pattern should be preserved character-for-character during any move.
- CSS and JS are coupled to `app.py` only through Python string
  concatenation (f-strings), not through file coupling — they are fully
  portable to new modules with a copy-and-import move.

## 6. Frontend/backend boundaries

Confirmed by import inspection: `app.py` imports from `memory`,
`openrouter_client`, `prompts`, `rag.*`, `security`, `tools.*`, and
`langsmith_config`. None of `tools/`, `rag/`, or `memory/` import Streamlit
(consistent with `PROJECT_STATUS.md` §3's stated invariant, not
re-verified exhaustively in this pass — treat as inherited fact from the
prior validated baseline). The frontend→domain boundary is directional and
should remain so: a new `frontend/` package continues to import
`tools/rag/memory`, never the reverse. No backend or domain code is in
scope for this audit or its proposed phases.

## 7. Test-coupling risks

| Pattern | Example | Risk after extraction |
| --- | --- | --- |
| `import_module("app")` + attribute access | `cognivia_app._render_noise_to_signal_styles` | Safe if `app.py` re-exports the name (`from frontend.browser.styles import render_noise_to_signal_styles as _render_noise_to_signal_styles`) |
| `AppTest.from_file("app.py")` | ~15+ call sites | Safe as long as `app.py` still executes the same script body at import/run time |
| `getsource(cognivia_app.<fn>)` on a moved function | contrast/selector/JS-content tests | Safe — `getsource` follows the function's `__code__`, not its declaring module, as long as the re-export doesn't wrap it |
| `Path("app.py").read_text()` + literal/AST scan of the **whole file** | `st.expander` count == 15, `"st.rerun" not in app_source` | **Breaks silently** (under-counts, not errors) if code containing those constructs moves out of `app.py`. Must update the test's target path (or scan both files) in the same phase that moves the relevant code |
| No dedicated test file for AI Skill Compass or Interview Coach | — | Extracting these two modes has weaker regression protection; add focused tests before or during their extraction phase |

## 8. Target package structure

```
frontend/
    __init__.py
    assets.py          # _asset_data_uri, BRAND_ASSET_DIR, asset path constants
    browser/
        styles.py       # _render_noise_to_signal_styles, APP_RERENDER_STABILITY_CSS
        controllers.py  # _install_app_rerender_stability_guard,
                         # _render_noise_to_signal_control_accessibility,
                         # _render_noise_to_signal_intro_video_controller
    state.py            # namespaced session-state constants + typed get/set/reset
                         # helpers per mode (no behavior change; wraps existing keys)
    memory_bridge.py     # get_memory_store, _save_*_memory, _learner_memory_snapshot
    runtime/
        drawer.py        # _render_runtime_status, _render_secondary_project_drawer,
                          # _render_noise_to_signal_runtime_drawer
    noise_to_signal/
        home.py          # _render_noise_to_signal_home, intro, focus mode
        search.py        # _submit_noise_to_signal_goal, quick prompts
        results.py       # _render_noise_to_signal_result/metrics/evidence/trace
        learning.py       # guided intake + learning-direction schema rendering
        exports.py        # build_full_learning_plan_markdown,
                           # build_learning_reflection_markdown, download renderers
    interview_coach/
        view.py           # extracted inline block, function-wrapped first
    skill_compass/
        view.py           # extracted inline block, function-wrapped first
```

Rationale for deviating from the illustrative structure in the task:
`skill_compass/` and `interview_coach/` are collapsed to a single `view.py`
each rather than `state.py`/`config.py`/`view.py` trios, because neither
mode currently has enough distinct state or configuration logic to justify
three files — the whole Interview Coach block is ~145 lines and AI Skill
Compass is ~550 lines of view code with few named constants. Split further
only if a later phase finds cause. `learning.py` and `exports.py` sit under
`noise_to_signal/` rather than top-level `cognivia/`, matching the actual
module name (`noise_to_signal`) used throughout `app.py`'s own constants
and function names, rather than introducing a new "Cognivia" naming layer
not present in the code today.

`app.py` after all phases becomes: imports, `st.set_page_config`,
`APP_MODES`/mode-label helpers, composition of `frontend.*` render calls,
and the mode-dispatch `if/elif` — matching the stated end goal.

## 9. Ordered refactor phases

Each phase keeps `app.py` the single Streamlit entry point and importable
module; each is independently committable and reviewable.

**Phase 1 — Extract CSS/theme and static assets** (see §10 for full detail).

**Phase 2 — Extract browser controllers**
- Files: new `frontend/browser/controllers.py`; `app.py` re-exports.
- Moves: `_install_app_rerender_stability_guard`,
  `_render_noise_to_signal_control_accessibility`,
  `_render_noise_to_signal_intro_video_controller`.
- Compatibility: re-export under original names in `app.py`; JS string
  content unchanged byte-for-byte.
- Tests affected: JS-content `getsource`-based assertions (must still pass
  via re-export); no `Path("app.py").read_text()` scans currently target
  JS content in this block — verify during implementation, not assumed here.
- Risk: Medium (verbatim-string tests are sensitive to accidental
  reformatting during the move).
- Commit message: `refactor(frontend): extract browser controllers to frontend/browser/controllers.py`

**Phase 3 — Extract runtime drawer**
- Files: new `frontend/runtime/drawer.py`.
- Moves: `_render_runtime_status`, `_runtime_presentation_data`,
  `_runtime_technical_details`, `_runtime_drawer_markup`,
  `_secondary_runtime_markup`, `_render_secondary_project_drawer`,
  `_render_noise_to_signal_runtime_drawer`.
- Compatibility: re-export; `RUNTIME_DETAIL_SESSION_KEYS` stays in `app.py`
  or moves with a re-export — decide based on whether other phases need it.
- Tests affected: ~14 runtime/drawer tests; verify `st.expander` count
  assertion (§7) if this phase's code contains any of the 15 counted calls.
- Risk: Medium.
- Commit message: `refactor(frontend): extract runtime drawer to frontend/runtime/drawer.py`

**Phase 4 — Extract memory bridge**
- Files: new `frontend/memory_bridge.py`.
- Moves: `get_memory_store`, `get_or_create_demo_learner_id`,
  `build_evidence_refs`, `_save_guided_intake_memory`,
  `_should_save_noise_to_signal_memory`, `_save_noise_to_signal_memory`,
  `_learning_direction_event_payload`, `_save_learning_direction_event`,
  `_save_learning_direction_generated_once`, `_learner_memory_snapshot`,
  `_render_learner_memory_history`.
- Compatibility: re-export; no change to `memory` package calls.
- Tests affected: indirect, via Noise-to-Signal AppTests that exercise
  memory writes.
- Risk: Medium (touches the one real external-persistence boundary in the
  frontend; verify offline/`NullMemoryStore` fallback path still triggers
  identically).
- Commit message: `refactor(frontend): extract memory bridge to frontend/memory_bridge.py`

**Phase 5 — Function-wrap Interview Coach and AI Skill Compass (no move yet)**
- Files: `app.py` only.
- Change: wrap each inline `if`/`elif` body in `_render_interview_coach()`
  / `_render_ai_skill_compass()`, called from the dispatch chain. Pure
  mechanical indentation change; no logic edits.
- Compatibility: N/A (still in `app.py`).
- Tests affected: none expected to change behavior; add smoke tests first
  if none exist for these modes (see §7 gap).
- Risk: Low-Medium (large diff by line count, but behavior-preserving by
  construction; the risk is diff-review fatigue, not logic risk).
- Commit message: `refactor(frontend): wrap Interview Coach and AI Skill Compass mode bodies in functions`

**Phase 6 — Move Interview Coach and AI Skill Compass**
- Files: new `frontend/interview_coach/view.py`,
  `frontend/skill_compass/view.py`.
- Moves: the two functions created in Phase 5.
- Compatibility: re-export; dispatch chain calls the re-exported names.
- Tests affected: any new smoke tests from Phase 5.
- Risk: Low (mechanical, given Phase 5 already isolated the bodies).
- Commit message: `refactor(frontend): extract Interview Coach and AI Skill Compass views`

**Phase 7 — Extract Noise-to-Signal exports**
- Files: new `frontend/noise_to_signal/exports.py`.
- Moves: `build_full_learning_plan_markdown`,
  `build_learning_reflection_markdown`, `_render_full_learning_plan_download`,
  `_render_learning_note_exports`, `_learning_note_export_payload`,
  `_parse_learning_note_tags`.
- Compatibility: re-export.
- Tests affected: export-content and download-button tests.
- Risk: Low (pure builders, one render call site each).
- Commit message: `refactor(frontend): extract learning plan/reflection exports`

**Phase 8 — Extract Noise-to-Signal learning-direction/guided-intake**
- Files: new `frontend/noise_to_signal/learning.py`.
- Moves: schema normalization, rendering, and selection functions
  (app.py:3025–4126 subset not already moved), plus
  `_start_noise_to_signal_guided_intake`.
- Compatibility: re-export. Do **not** fix the pre-existing hand-authored
  decision-dict boundary duplication in this phase — that is a separate,
  explicitly authorized change per the authoritative audit.
- Tests affected: learning-path selection/schema suite (largest single
  cluster after Noise-to-Signal home/result).
- Risk: Medium-High (most state-coupled block remaining).
- Commit message: `refactor(frontend): extract learning-direction and guided-intake views`

**Phase 9 — Extract Noise-to-Signal home/search/result (largest, do last)**
- Files: new `frontend/noise_to_signal/home.py`, `search.py`, `results.py`.
- Moves: remaining large block, app.py:2838–4746 plus 4324–4477.
- Compatibility: re-export everything; update the `Path("app.py")`
  literal/AST test target (§7) in the same commit if any counted construct
  (`st.expander`, `st.rerun`) moved with this block.
- Tests affected: the majority of `test_noise_to_signal_app.py`.
- Risk: High (largest surface, most tests, most session-state reads).
- Commit message: `refactor(frontend): extract Noise-to-Signal home/search/result views`

**Phase 10 — Introduce `frontend/state.py` accessors (optional, cleanup)**
- Files: new `frontend/state.py`; update call sites incrementally.
- Change: typed get/set/reset wrappers per namespace, replacing direct
  `st.session_state[KEY]` access. No key renames, no reset-order changes.
- Risk: Low per call site, but wide diff if done in one commit — do
  namespace-by-namespace if pursued.
- Commit message: `refactor(frontend): introduce typed session-state accessors`

## 10. Exact first phase (recommended)

**Objective:** Extract the CSS/theme block and static asset helpers — the
largest single chunk of `app.py` (~1,365 lines) with zero session-state
coupling and a single call site — into `frontend/browser/styles.py` and
`frontend/assets.py`. This is the smallest-risk phase that still visibly
reduces `app.py`'s line count and establishes the `frontend/` package.

**Files created:**
- `frontend/__init__.py` (empty)
- `frontend/browser/__init__.py` (empty)
- `frontend/browser/styles.py`
- `frontend/assets.py`

**Files modified:**
- `app.py` — remove the moved definitions, add imports, keep the original
  names available at module scope.

**Functions/constants moved:**
- To `frontend/assets.py`: `BRAND_ASSET_DIR`, `NOISE_TO_SIGNAL_LOGO_PATH`,
  `NOISE_TO_SIGNAL_INTRO_VIDEO_PATH`, `FOCUS_MODE_ENTER_ICON_PATH`,
  `FOCUS_MODE_EXIT_ICON_PATH`, `_asset_data_uri`.
- To `frontend/browser/styles.py`: `APP_RERENDER_STABILITY_CSS`,
  `NOISE_TO_SIGNAL_HELPER_TEXT_COLOR`, `_render_noise_to_signal_styles`.

**Compatibility strategy:** `app.py` adds, at the original definition
sites:

```python
from frontend.assets import (
    BRAND_ASSET_DIR,
    NOISE_TO_SIGNAL_LOGO_PATH,
    NOISE_TO_SIGNAL_INTRO_VIDEO_PATH,
    FOCUS_MODE_ENTER_ICON_PATH,
    FOCUS_MODE_EXIT_ICON_PATH,
    _asset_data_uri,
)
from frontend.browser.styles import (
    APP_RERENDER_STABILITY_CSS,
    NOISE_TO_SIGNAL_HELPER_TEXT_COLOR,
    _render_noise_to_signal_styles,
)
```

No wrapper functions — direct re-export preserves `getsource()` results
(Python's `inspect.getsource` follows `__code__.co_filename`, so
`cognivia_app._render_noise_to_signal_styles` still resolves to the
function defined in `frontend/browser/styles.py`, and existing
`getsource(...)`-based contrast/selector tests keep working unmodified).

**Focused tests (run first, before any broader validation):**
```bash
python -m pytest tests/test_noise_to_signal_app.py -q -k "styles or contrast or helper_tip or callout"
```

**Full validation gate for this phase:**
```bash
python -m pytest tests/test_noise_to_signal_app.py tests/test_noise_to_signal_ui_copy.py -q
python -m ruff check app.py frontend tests
python -m py_compile app.py frontend/assets.py frontend/browser/styles.py
git diff --check
bash scripts/agent/sentinel.sh --expected-branch refactor/frontend-architecture
```
Escalate to the full isolated suite (`python -m pytest tests -q` with the
provider env vars unset, per `AGENTS.md` §Validation ladder) before this
phase is considered commit-ready, since it changes a shared import surface.

**Commit message:**
`refactor(frontend): extract CSS/theme and static assets to frontend/ package`

## 11. Compliance-readiness integration point (analysis only)

AI-generated content currently flows through these central places:

- **Rendered:** `_render_noise_to_signal_result` (app.py:4207) and its
  callees (`_render_noise_to_signal_study_plan`,
  `_render_noise_to_signal_evidence`, `_render_recommendation_summary`,
  `_render_guided_intake_recommendation`) — these render the graph's
  decision output and study plan directly from `run_noise_to_signal(...)`
  results.
- **Exported/downloaded:** `build_full_learning_plan_markdown` and
  `build_learning_reflection_markdown` (app.py:3440, 3649) assemble
  Markdown files served via `st.download_button` in
  `_render_full_learning_plan_download` and `_render_learning_note_exports`.
- **Persisted:** `_save_noise_to_signal_memory`, `_save_guided_intake_memory`,
  and `_save_learning_direction_event` write decision/recommendation content
  into the memory store (`PostgresMemoryStore` / `NullMemoryStore`).

**Recommended future integration point:** a single provenance-tagging step
inside `build_evidence_refs` (app.py:1109), which already runs on every
decision before it reaches rendering, export, or memory persistence. Adding
a disclosure/provenance field there (e.g. model identifier, generation
timestamp, evidence-sufficiency flag) would propagate to all three
downstream surfaces — render, export, and persistence — through the single
existing choke point, without touching `rag/`, `tools/`, or prompt logic.
This is analysis only; no compliance behavior is implemented here, and
implementing it requires a separately authorized task per `AGENTS.md`.

## 12. Definition of done

For this audit (already met):
- Read-only; no product or test files modified.
- Findings are evidence-backed with file:line citations from this session's
  inspection, not from memory or assumption.
- Phased plan is ordered by risk, each phase independently reviewable,
  behavior-preserving, and reversible via `git revert`.

For the first phase, before it is considered complete:
- All listed tests pass; `python -m ruff check`, `py_compile`,
  `git diff --check`, and Sentinel pass.
- `app.py` line count drops by roughly the moved-code size; no rendered
  output, CSS selector, or JS controller string changes.
- `git diff` touches only `app.py` and the four new `frontend/` files.
