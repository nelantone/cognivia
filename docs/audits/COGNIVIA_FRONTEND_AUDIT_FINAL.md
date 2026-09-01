# Cognivia Frontend Audit — Consolidated Final Report

**Date:** 2026-07-29  
**Auditor:** Claude Opus (read-only source review)  
**Consolidated by:** ChatGPT from the available Claude audit output and terminal transcript  
**Worktree:** `<repository-worktree>`
**Branch:** `audit/ux-v2-final`  
**HEAD:** `a30cf9a917f30fc6073fa68824d339ac0bb00bf8`

> Note: the available terminal transcript contains the executive verdict, scope-integrity review, metadata, and references to findings F-02 through F-08, but not the complete verbatim body of every finding. This document preserves only findings supported by the visible audit output and marks browser-dependent conclusions accordingly.

## Executive verdict

- **Ship readiness:** Ready with follow-up.
- **Justification:** The validated product flows hold up under source inspection. The graph remains single-call per explicit submission; memory writes stay behind existing guards; exports use the canonical decision and selected schema; and the committed frontend changes do not alter the RAG, provider, prompt, schema, persistence, evaluation, or backend business-rule modules.
- **Highest-risk architectural area:** The monolithic `app.py` presentation layer, especially injected CSS, parent-document JavaScript, Streamlit DOM coupling, and rerun/session-state coordination.
- **Recommended next engineering action:** Apply a small, evidence-driven frontend hardening patch for performance, accessibility, stale-state cleanup, and missing styling, then add a compact Playwright smoke suite before larger refactoring.

## Findings

### F-01 — Oversized base64 assets are rebuilt and inlined into the UI

- **Severity:** High
- **Confidence:** Confirmed
- **Evidence:** The audit measured roughly **3.3 MB** of base64-encoded assets used for controls rendered at about **44 × 44 px**. The generated style payload was approximately **2,794,019 characters** and required measurable rebuild/escape/hash work per render.
- **Impact:** Larger rerender payloads, unnecessary CPU and memory work, slower first paint, and avoidable browser/network overhead.
- **Root cause:** Full-size binary assets are embedded into CSS/HTML instead of using appropriately sized files or a cached/static delivery path.
- **Smallest safe recommendation:** Produce properly sized control assets, cache encoded data once, or serve them as normal static/media resources rather than rebuilding multi-megabyte strings on reruns.
- **Safe to automate:** Partially
- **Requires browser validation:** Yes

### F-02 — Parent-document controllers are unsafe in embedded contexts

- **Severity:** Medium
- **Confidence:** Probable
- **Evidence:** Parent-document JavaScript accesses `window.parent.document` without a robust same-origin/embed guard. Claude cross-checked Streamlit 1.56 semantics and noted that `st.html` is not itself iframe-isolated.
- **Impact:** A hosted or embedded deployment may throw a `SecurityError`, leaving controls partially initialized or broken.
- **Root cause:** The implementation assumes same-origin access to the parent document.
- **Smallest safe recommendation:** Guard parent-document access with `try/catch`, verify same-origin capability, and degrade gracefully to the local document when access is unavailable.
- **Safe to automate:** Yes
- **Requires browser validation:** Yes, under `?embed=true` or a real embedding host

### F-03 — Responsive CSS may create horizontal scrolling

- **Severity:** Medium
- **Confidence:** Probable
- **Evidence:** The audit identified a confirmed CSS cascade/layout condition with a likely horizontal-scroll consequence on narrow viewports.
- **Impact:** Mobile users may see clipped content, sideways scrolling, or displaced controls.
- **Root cause:** Width/min-width/positioning rules in the custom presentation layer do not consistently collapse within the viewport.
- **Smallest safe recommendation:** Add a narrow-viewport regression rule, constrain child widths with `min-width: 0` / `max-width: 100%`, and validate the exact selectors flagged in the audit.
- **Safe to automate:** Partially
- **Requires browser validation:** Yes

### F-04 — The processing flag is not a complete double-submit guarantee

- **Severity:** Medium
- **Confidence:** Confirmed
- **Evidence:** The older audit described the processing state as effective double-submit protection, but the final audit explicitly contradicted that conclusion after inspecting the current source lifecycle.
- **Impact:** Fast repeated interaction or global shortcut behavior may still allow duplicate UI events or inconsistent transient state even though graph call-count tests pass for normal reruns.
- **Root cause:** The flag coordinates presentation state but is not an atomic submission lock across every browser event path.
- **Smallest safe recommendation:** Make submission idempotent at the callback boundary, disable all equivalent triggers while processing, and add a browser test for rapid click plus Enter.
- **Safe to automate:** Partially
- **Requires browser validation:** Yes

### F-05 — Choosing a learning path leaves stale summary content for one interaction cycle

- **Severity:** Medium
- **Confidence:** Confirmed in source; visible symptom probable
- **Evidence:** The audit reported that `Choose this path` updates state in an order that leaves the previous recommendation summary visible until the next interaction/rerun cycle.
- **Impact:** Users may briefly see a path selected while the surrounding summary still describes the previous state.
- **Root cause:** State mutation and dependent presentation cleanup occur in different render cycles.
- **Smallest safe recommendation:** Clear or replace dependent summary state in the same callback that records the path selection, then rerender from one canonical selected-path state.
- **Safe to automate:** Yes
- **Requires browser validation:** Yes

### F-06 — Helper-tip contrast fails WCAG AA

- **Severity:** Medium
- **Confidence:** Confirmed
- **Evidence:** Declared token values produce approximately **2.9:1** contrast for helper-tip text. Panel compositing changes the result only marginally.
- **Impact:** Low-vision users and users on dim or low-quality displays may struggle to read secondary guidance.
- **Root cause:** Muted foreground color is too close to the dark panel background.
- **Smallest safe recommendation:** Raise the helper-text token to at least **4.5:1** for normal text, while preserving stronger hierarchy through size/weight rather than low contrast.
- **Safe to automate:** Yes
- **Requires browser validation:** Yes

### F-07 — “New search” accessibility depends on MutationObserver repair

- **Severity:** Medium
- **Confidence:** Confirmed
- **Evidence:** The accessible name is not reliably present in the initial semantic control and is patched back into the DOM by a MutationObserver.
- **Impact:** Screen readers may encounter an unnamed or inconsistently named control during initialization or node replacement.
- **Root cause:** Accessibility semantics are added after rendering rather than being part of the control’s authoritative markup/API declaration.
- **Smallest safe recommendation:** Provide the accessible label through the Streamlit widget declaration or stable semantic HTML, using DOM repair only as a defensive fallback.
- **Safe to automate:** Partially
- **Requires browser validation:** Yes, including a screen-reader/accessibility-tree check

### F-08 — A rendered empty/callout state has no matching stylesheet rule

- **Severity:** Low
- **Confidence:** Confirmed in source; visual consequence probable
- **Evidence:** The audit found styled markup/class intent for an empty or compact callout state, but no corresponding stylesheet selector.
- **Impact:** The state may render as unstyled text, weaken visual hierarchy, or differ from adjacent Cognivia cards.
- **Root cause:** Markup and stylesheet evolved separately and the selector was omitted or renamed.
- **Smallest safe recommendation:** Add the missing scoped style or remove the dead class and use an existing callout component consistently.
- **Safe to automate:** Yes
- **Requires browser validation:** Yes

## Additional boundary observation

`_start_noise_to_signal_guided_intake` hand-authors a decision-shaped dictionary instead of obtaining it from the graph. This duplicates part of the graph output contract in the UI layer. It is pre-existing and was not introduced by the committed frontend changes, but it is a useful future extraction target.

## Architecture map

Current `app.py` combines:

1. application bootstrap and Streamlit page configuration;
2. global theme, CSS, and injected JavaScript;
3. UI state and callback orchestration;
4. Noise-to-Signal home, search, examples, loading, result, and Guided Intake flows;
5. AI Skill Compass and Interview Coach presentation;
6. learning-path display normalization and rendering;
7. export assembly and download controls;
8. frontend integration boundaries for graph execution, memory writes, and provider-backed modes.

Smallest useful extraction boundaries:

- `ui/theme.py` — stable tokens, CSS, asset helpers;
- `ui/browser_controllers.py` — parent-document scripts and lifecycle guards;
- `ui/noise_to_signal_state.py` — state keys, transitions, and submission guards;
- `ui/learning_paths.py` — compact adapters, cards, disclosures, selection lifecycle;
- `ui/exports.py` — full-plan and reflection builders/renderers.

Do not migrate frameworks. Extract one boundary at a time, protected by current tests plus browser smoke coverage.

## Highest-value browser / Playwright smoke scenarios

1. Cold load: dark first paint, intro lifecycle, reduced motion, replay query parameter, no incomplete-form warning.
2. Search: mouse click and Enter each trigger exactly one submission; Enter does nothing unintended while typing in Guided Intake or note fields.
3. Runtime controls: native sidebar opener and custom drawer survive search reruns, mode changes, and node replacement.
4. Learning path lifecycle: select a path and confirm the summary updates in the same cycle with no stale prior state.
5. Accessibility: keyboard-only traversal, visible focus, semantic names for New search and Focus Mode, disclosure operation.
6. Responsive: narrow viewport with no horizontal scroll, clipping, or inaccessible controls across all three modes.
7. Loading/error/new-search: stable focus and scroll position, no stale outgoing view or white flash.
8. Export: canonical full plan and separate reflection remain distinct after reload and mode switching.

## Recommended sequence

1. **Immediate hardening:** fix the oversized embedded assets, stale path-selection cycle, helper contrast, missing callout style, and semantic New search label.
2. **Small safe refactors:** add embed guards and centralize browser-controller cleanup; make submission idempotency explicit.
3. **E2E protection:** add the 6–8 Playwright smoke scenarios above, starting with search/Enter, path selection, controls, and narrow viewport.
4. **Deferred architecture:** extract state, browser controllers, learning-path presentation, and exports from `app.py` incrementally.
5. **Optional polish:** replace nine deprecated `use_container_width=True` calls with `width="stretch"`; decide whether to restore or remove the Compass logo block; add an explicit skip affordance to the 6.131-second intro overlay.

## Scope integrity

The audit found no evidence that commit `a30cf9a` altered:

- graph execution multiplicity;
- provider/model calls;
- RAG or retrieval;
- prompts or canonical schemas;
- persistence payloads;
- evaluation logic;
- backend business rules.

Specific evidence noted by the auditor:

- `run_noise_to_signal(...)` remains one source call per successful submission, now routed through `_submit_noise_to_signal_goal`;
- `tests/test_noise_to_signal_app.py` asserts one graph call across a follow-up rerun;
- the compact learning-direction adapter is display-only and exports read canonical `LearningDirectionSchema` data;
- `tools/`, `rag/`, `memory/`, provider, prompt, security, and evaluation modules were not changed by the frontend commit.

## Audit metadata

- **Worktree clean before/after:** Yes / Yes
- **Files inspected:** `app.py` in full, `.streamlit/config.toml`, `requirements.txt`, `tools/learning_direction.py`, selected frontend tests, previous frontend audit, asset listings, and relevant Streamlit 1.56 source files.
- **Commands run:** Git identity/status/diff inspection, file/line searches, asset inspection, `ffprobe`, and two throwaway measurements for base64/style payload size and construction cost.
- **Checks intentionally skipped:** full pytest, Ruff, `git diff --check`, and compilation; the existing 90-test green baseline was accepted for this read-only audit.
- **Browser driven:** No.

## Remaining uncertainty

- Narrow-view horizontal scrolling, one-cycle visual lag, empty-state styling, and screen-reader behavior require real-browser confirmation.
- Embedded-mode failure requires testing under `?embed=true` or another host.
- The global `st.button(shortcut="Enter")` may trigger while focus is in other text fields; this remains unverified and deserves an explicit browser test.
- The older tracked `docs/ux_v2/FRONTEND_AUDIT.md` is stale and refers to an earlier branch/snapshot. It should be replaced or clearly archived after the new findings are implemented.
