# Cognivia Frontend Audit — audit/ux-v2-snapshot vs feature/ux-v2-clarity-experiment vs main

Date: 2026-07-26

## Scope and method

This is a read-only audit. No code, tests, assets, CSS, JavaScript, or application behavior was changed to produce it.

Three research passes were run in parallel:

1. **Current snapshot** (`audit/ux-v2-snapshot`, this worktree) — read directly via file reads of `app.py`, `docs/ux_v2/`, `tools/`, `rag/`, `memory/`, `tests/`, `assets/brand/`.
2. **`main`** — read via `git show main:<path>` / `git diff` / `git log`, without checking out the branch.
3. **`feature/ux-v2-clarity-experiment`** — read the same way, plus its own `docs/ux_v2/implementation/ux_v2_experiment_report.md`.

Findings are scored against `docs/DESIGN_PRINCIPLES.md`, which supplies the Keep/Simplify/Remove/Defer framework and Decision Checklist used below.

**Verification status.** Every finding below is labeled either:

- **Verified in current snapshot** — the finding was directly observed in this worktree's own files, with file/line evidence from this branch.
- **Needs live verification** — the finding was observed in `main` and/or `feature/ux-v2-clarity-experiment` and is presented here as relevant context or risk, but was **not** independently re-confirmed against the current snapshot's exact code. Do not assume it applies to this snapshot until checked directly.

Where the current-snapshot research pass explicitly contradicted a finding from another branch (e.g. a pattern that looked fixed in one branch but appears to have regressed in this one), that is called out explicitly rather than silently merged.

**Non-goals:** no branch was checked out; no visual/browser rendering was performed (contrast ratios, live animation timing, and viewport behavior below are inferred from source, not measured); no recommendation has been implemented.

---

## Summary verdict

The current snapshot inherited some UX ideas from the clarity-experiment branch (a short gated intro video, a Focus Mode) while retaining the full three-mode architecture, legacy code paths, and orphaned media assets from `main` — making it the largest of the three files (4,684 lines vs. main's 4,090 and the experiment's ~4,260). Its strongest asset — the evidence-first, uncertainty-visible decision logic — is intact and well-implemented. Its weakest areas are unchanged from `main`: three visually inconsistent products behind one sidebar radio, business logic embedded in the UI file, and CSS/JS built on fragile, undocumented Streamlit internals. It is not presentable as an MVP as-is; a scoped cut (see the MVP plan below) is the fastest safe path there.

---

## Findings by category

Legend: **Priority** = Critical / Important / Optional. **Class** = Keep / Simplify / Remove / Defer (per `docs/DESIGN_PRINCIPLES.md`).

### 1. Product clarity and cognitive load

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| Three unrelated products (Noise-to-Signal, AI Skill Compass, "Interview Coach (Sprint 1 legacy)") are one sidebar click apart with no explanation of which is current | `app.py:111-117` (mode radio); Interview Coach `app.py:3906+`; Skill Compass `app.py:4115+` | New users can't tell which surface is "the product"; legacy mode looks equally valid | Remove Interview Coach from the shipped MVP; gate or cut Skill Compass dev tools | Critical | Remove | **Verified in current snapshot** |
| AI Skill Compass flattens 6 unrelated actions — including a QA-only "Run RAG evaluation" — into one dropdown | `app.py:4227-4235` | Mixes end-user and developer/QA audiences in one menu | Remove "Run RAG evaluation" from user-facing UI; move to a dev-only script | Important | Remove | **Verified in current snapshot** |
| Runtime/provider status panel is always rendered regardless of mode, exposing infra details ("Offline mode active", "Memory: local fallback") | `_render_runtime_status()` app.py:392-412, called unconditionally at app.py:3903 | Implementation detail leaks into the primary surface; conflicts with "clarity over spectacle" | Gate behind a debug flag, off by default in the presentable build | Important | Simplify | **Verified in current snapshot** |
| Scope-detection keyword lists silently gate what the app will answer | `LEARNING_OR_AI_CAREER_PROMPT_TERMS` / `CLEAR_OUT_OF_SCOPE_PROMPT_TERMS`, app.py:211-255; `is_learning_or_ai_career_prompt()` app.py:324-336 | Legitimate queries can be silently misclassified with no visibility into why | Surface why a query was judged out-of-scope, or document the heuristic's limits | Optional | Simplify | **Verified in current snapshot** |
| Duplicate guided-intake implementations: nearly identical logic exists once inside Noise-to-Signal and once inside AI Skill Compass | `_render_noise_to_signal_guided_intake` app.py:2871-3033 vs. app.py:3643-3714+ | Same fields/validation/calls copy-pasted rather than shared — doubles maintenance surface | Extract one shared guided-intake component/function | Optional | Simplify | **Verified in current snapshot** |
| The home/search screen may follow a single-question + quick-prompts layout (a clearer pattern than main's 8-example-prompt grid), or may still use the older textarea+grid layout | Home render path for Noise-to-Signal mode | Determines whether the entry point is calm and minimal or cluttered | Confirm current layout directly, then either keep the single-question framing or adopt it | Important | — | **Needs live verification** — the single-question/quick-prompt pattern was directly observed in `feature/ux-v2-clarity-experiment` (`_render_noise_to_signal_home`, app.py:3997-4046); the current-snapshot pass did not independently re-confirm which layout this branch actually renders |
| If the single-question layout is present, the entry form may stay fully visible above the results panel even after a decision exists (no ask→answer narrowing) | Home/results render ordering | Re-adds cognitive load right after a "minimal home" | Collapse/hide the entry form once a result exists | Important | Simplify | **Needs live verification** — observed in `feature/ux-v2-clarity-experiment` (app.py:4228-4239), not independently re-confirmed in this snapshot |

### 2. Visual hierarchy and consistency

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| Three incompatible visual systems across modes: cinematic dark (Noise-to-Signal, ~1,200 lines of CSS), light teal (Skill Compass), unstyled default (Interview Coach) | Noise-to-Signal styles app.py:921-2124; Skill Compass app.py:4116-4191; Interview Coach app.py:3906-4060 | Product identity flips per click | Resolved by scoping to one mode (see §1) | Critical | Remove | **Verified in current snapshot** |
| Heavy reliance on undocumented Streamlit-private selectors (`div.st-key-*`, `data-testid`) for nearly all layout | ~188 occurrences of `st-key-` in `app.py` | Any Streamlit internals change can silently break the visual layer | Centralize into a smaller, documented selector/token set before further visual work | Important | Simplify | **Verified in current snapshot** |
| Some Streamlit versions of this styling approach accumulate duplicate/contradicting CSS rules for the same selector (later rules winning only via `!important`), alongside a large jump in `!important` usage (46 → 196 occurrences) | Observed pattern: `div.st-key-noise_to_signal_landing_card` redeclared 4 times | Dead/contradicting CSS accumulates, risking future changes silently losing to a forgotten earlier rule | Audit for duplicate blocks before adding more style passes; this snapshot's own `!important` count was not separately measured | Important | Simplify | **Needs live verification** — the specific duplicate-block pattern and the 196-count were observed in `feature/ux-v2-clarity-experiment` (vs. 46 in `main`); this snapshot's own count and duplicate-block status were not independently measured |
| A helper-tip component hardcodes inline text color, bypassing the shared stylesheet | `_helper_tip_markup`, app.py:2133-2159, inline `style="..."` at app.py:2151-2154 | Inline styles cannot be overridden by later theme changes; duplicates the styling approach used elsewhere | Move to a class-based style so it inherits from one theme source | Optional | Simplify | **Verified in current snapshot** (existence of hardcoded inline style; the specific low-contrast color value `#49636b` against a near-black panel was observed only in `feature/ux-v2-clarity-experiment`, app.py:2704/1977 — **needs live verification** whether this snapshot's exact color/contrast has the same issue) |
| A deliberate three-role typography system (Manrope / Inter / Atkinson Hyperlegible Next) with a documented rationale | app.py:944-947; rationale in `docs/ux_v2/04_typography_reference.png` | Genuine, accessibility-aware design decision | Carry forward as-is into any rebuild/design-token system | — | Keep | **Verified in current snapshot** |
| Guided-intake form inputs fall back to default (light) Streamlit styling inside an otherwise dark-styled panel, because that container key has no matching CSS override | `st.container(key="noise_to_signal_guided_intake")`, app.py:3018 | Visible inconsistency between two adjacent form surfaces in the same feature | Add the missing override, or migrate to a lower-selector-count stylesheet | Optional | Simplify | **Verified in current snapshot** |

### 3. Animations and decorative elements

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| ~28+ MB of orphaned decorative media (unused looping-background videos, unused background PNGs, alternate logo variants) sit in `assets/brand/` with no code references | `video1.mp4` (5.7 MB), `video2.mp4` (1.5 MB), `video3.mp4` (8.9 MB), 4× `background-simple*.png` (~2 MB each), `cognivia-mountain-landing.png` (1.7 MB), 5× logo variants, etc. | Repo bloat; signals leftover exploration assets never cleaned up | Delete unused assets | Optional | Remove | **Verified in current snapshot** |
| A short, gated intro video (`video0.mp4`, 304 KB) plays before the app is usable, dismissed via a "Begin"-style interaction | `_render_noise_to_signal_intro()` app.py:3704-3737, `_noise_to_signal_intro_is_complete()` app.py:3391-3392 | Adds friction before first use; whether it's skippable and whether it replays on every reload is not confirmed for this branch | Confirm reload/skip behavior directly | Important | — | **Verified in current snapshot** that this gated intro exists; **needs live verification** whether it lacks durable "seen once" persistence and replays on reload — that specific behavior claim was based on `feature/ux-v2-clarity-experiment`'s session_state-only implementation, not independently tested here |
| The intro/loading-dot fade animations may be driven by hardcoded CSS second-based timers rather than the video's real `ended`/`loadedmetadata` event | N/A (implementation not independently inspected in this branch) | If true, an asset-duration change could leave a black/frozen gap or an early-disappearing overlay | Confirm the current implementation's timing mechanism; prefer event-based triggers | Important | Simplify | **Needs live verification** — this timer-based pattern (`8.2s`, `8.1s`, `8s` hardcoded delays) was observed in `feature/ux-v2-clarity-experiment` (app.py:1755-1778, 449); this snapshot's own intro/audio CSS was not independently re-inspected for the same pattern |
| `prefers-reduced-motion` is respected for the loading-dot and evidence fade-in animations | `ntsFadeIn`/`ntsLoadingDot` keyframes with `@media (prefers-reduced-motion: reduce)` guards, app.py:1360-1366 and app.py:2111-2120 | Good accessibility practice for these specific animations | Keep | — | Keep | **Verified in current snapshot** |
| Whether the same reduced-motion guard covers the intro video/audio timers is unconfirmed | Intro video/audio rendering | Users with reduced-motion preferences may still get the full video+audio intro if unguarded | Confirm and add the media query if missing | Important | Simplify | **Needs live verification** — absence of a reduced-motion guard specifically for the new intro was observed in `feature/ux-v2-clarity-experiment`, not independently re-checked here |
| Two anthropomorphic mascot ("Piko"/"Iri") tips exist with inline styling | `_helper_tip_markup`, app.py:2133-2159 | Decorative personality layer not tied to evidence/uncertainty communication | Remove for MVP, or fold into one documented "tip" component if kept | Optional | Defer | **Verified in current snapshot** |

### 4. Accessibility and responsive behaviour

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| Accessible names for several icon-only buttons — "Start a new search," "Focus mode," "Try examples" — are patched in after the fact by a `MutationObserver` re-applying `aria-label`, because the real button text is hidden (`color: transparent !important; text-indent: -999px`) | `_render_noise_to_signal_control_accessibility()` app.py:3841-3900; hidden-text buttons e.g. app.py:1125, 1429, 1875 | If the observer fails to attach (iframe sandboxing, a future Streamlit DOM change), these controls silently lose their accessible name entirely — this includes the Focus Mode toggle, not just search controls | Set `aria-label` declaratively in the HTML/markdown at render time instead of patching via JS after the fact | Critical | Simplify | **Verified in current snapshot** — note this explicitly includes the Focus Mode button, which in `feature/ux-v2-clarity-experiment` used a more robust text-indent-only approach that did **not** depend on JS; this snapshot appears to have merged Focus Mode into the fragile JS-dependent pattern instead (**needs live verification** to confirm this is a real behavioral difference between the two branches and not a misreading of either report) |
| CSS relies on the `:has()` selector in several places with no fallback for older browsers | app.py:78, 1249, 1341-1347, 1788-1832, 1906-1919 | Silently fails open (falls back to default browser rendering) on unsupported browsers, with no detection | Acceptable as progressive enhancement; document the browser-support assumption | Optional | Simplify | **Verified in current snapshot** |
| No `st.set_page_config()` call anywhere in the file — no explicit page title, favicon, or lang | confirmed absent via grep | Browser tab and page-level a11y metadata show generic Streamlit defaults, not "Cognivia" | Add `st.set_page_config(page_title="Cognivia", ...)` | Important | Simplify | **Verified in current snapshot** |
| `:focus-visible` outlines are explicitly defined for several custom buttons | app.py:1196-1207, 1721-1724, 3557-3560 | Positive baseline for keyboard accessibility | Keep and extend to any remaining custom controls | — | Keep | **Verified in current snapshot** |
| Sidebar/mode-switcher remains visible and functional in this snapshot | app.py:111-117 | Unlike `feature/ux-v2-clarity-experiment` (which hid the sidebar with no replacement navigation while in Noise-to-Signal mode), this snapshot retains a working way to switch modes | No action needed here; if any future Focus Mode work hides the sidebar, ensure an equivalent navigation path is retained | — | Keep | **Verified in current snapshot** — the sidebar-removal regression is specific to `feature/ux-v2-clarity-experiment` and does not currently appear in this snapshot |
| Responsive breakpoints exist at `max-width: 768px` (app.py:501-506, 2075-2109) adjusting layout/padding for mobile | — | Basic mobile reflow was considered | Keep; verify visually on a real narrow viewport before shipping | Optional | Keep | **Verified in current snapshot** (breakpoints exist); actual rendered behavior at that width was not tested live — **needs live verification** |

### 5. Streamlit `session_state` management

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| No centralized state schema: ~78 `session_state` references across ~20 distinct keys, some declared as module-level constants, others as bare string literals | app.py:63-76 and inline elsewhere | Silent breakage risk on refactor/rename; hard to audit what state exists | Introduce one small constants module or dataclass for session keys before adding more state | Important | Simplify | **Verified in current snapshot** |
| Dedicated, well-named reset helpers exist for related groups of state (`_reset_noise_to_signal_result`, `_clear_learning_direction_state`, `_clear_guided_recommendation_state`), each popping a specific key set rather than scattering resets inline | app.py:3369-3373, 759-768, 771-773 | This is a deliberate, readable pattern | Keep | — | Keep | **Verified in current snapshot** — note: a similar-looking pattern on `main` (with a fourth function, `_start_new_noise_to_signal_conversation`) was assessed by a separate review pass as having more overlapping responsibility; that critique does not clearly apply to this snapshot's version and should not be treated as a current finding |
| A `st.selectbox` for guided-intake entry point is pre-seeded into `session_state` and also given an explicit `index=` default a few lines later — a dual-source-of-truth pattern that works only via Streamlit's (implicit, version-dependent) precedence rules | app.py:3005-3010 (pre-seed), app.py:3019-3024 (explicit index) | Fragile if Streamlit's precedence behavior changes | Pick one source of truth for the widget's default | Optional | Simplify | **Verified in current snapshot** |
| A processing/lock flag with a `finally`-guaranteed clear prevents double submission | `NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY`, app.py:3430-3432, 3446, 3476 | Good reliability practice — directly supports "prevent duplicate submissions" | Keep | — | Keep | **Verified in current snapshot** |
| A guided-intake entry path hand-authors a fake "decision" dict to simulate a `needs_clarification` state, rather than calling the real decision engine | `_start_noise_to_signal_guided_intake()`, app.py:3490-3515 | Duplicates/diverges from the actual `run_noise_to_signal` graph's schema — a correctness risk, not just a style issue | Route through the real decision engine instead of hand-building its output shape | Important | Simplify | **Verified in current snapshot** |

### 6. Custom CSS and JavaScript fragility

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| ~1,200 lines of CSS live inside a single Python f-string, targeting undocumented Streamlit internals | `_render_noise_to_signal_styles()`, app.py:921-2124 | No linting, no reuse, breaks silently on Streamlit upgrades; contradicts `DESIGN_PRINCIPLES.md`'s "centralise custom CSS" guidance | Extract to a single external stylesheet/template with a minimized selector surface | Critical | Simplify | **Verified in current snapshot** (for context: `main`'s equivalent block was ~721 lines and `feature/ux-v2-clarity-experiment`'s was ~1,258 lines — not directly comparable line-for-line, but all three share the same fragile approach) |
| Custom JS reaches into `window.parent.document` to mutate Streamlit's real DOM in at least 3 places (background/intro control, accessibility-label patching, stale-state guard) | app.py:906, 3583, 3849 | Unsupported technique; would break under stricter iframe sandboxing in future Streamlit versions | Minimize to the one interaction that's genuinely necessary; document why per `DESIGN_PRINCIPLES.md`'s JavaScript guidance | Critical | Remove/Simplify | **Verified in current snapshot** |
| Global mutable JS state is stashed on `window.parent` and recreated on every rerun | `window.parent.__cogniviaControlLabelObserver`, app.py:3879-3882 | Risk of stale observers accumulating or racing across reruns | Remove once accessible names are set declaratively (see §4) | Important | Remove | **Verified in current snapshot** |
| A CSS/JS workaround exists for a documented Streamlit stale-element rendering quirk, re-injected on every rerun | `_install_noise_to_signal_stale_state_guard()`, app.py:900-918 | Workaround for a framework limitation rather than a real fix; adds fragility for a cosmetic issue | Confirm whether the current pinned Streamlit version still has this quirk before carrying the workaround forward | Optional | Defer | **Verified in current snapshot** |
| `!important` usage in this snapshot's stylesheet was not separately counted | — | Unknown how this compares to `main` (46) or `feature/ux-v2-clarity-experiment` (196) | Run a direct count before further style work, to gauge how much specificity debt exists | Optional | — | **Needs live verification** |

### 7. Coupling between UI and application logic

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| The decision/retrieval/memory engine (`tools/`, `rag/`, `memory/`) has zero Streamlit imports and is independently unit-tested | confirmed via grep | This is the strongest structural asset in the codebase — already framework-agnostic and API-ready | Keep this boundary; do not let future UI work leak business logic back into it | — | Keep | **Verified in current snapshot** |
| `app.py` is not a thin rendering layer: a ~170-line markdown-generation function, a scope-classification heuristic, and memory-save orchestration all live inline in the UI file | `build_full_learning_plan_markdown()` app.py:2568-2734; `is_learning_or_ai_career_prompt()` app.py:211-255/324-336; memory-save functions app.py:589-661, 708-736 | Any change to this content/logic requires touching the UI file; blocks a clean API boundary | Move into `tools/`/`memory/` modules, following the existing (good) separation pattern | Important | Simplify | **Verified in current snapshot** |
| `app.py` cannot be safely imported as a plain module — its top level calls Streamlit APIs immediately — forcing the test suite to `ast`-parse and `exec` extracted fragments rather than import it directly | `tests/test_noise_to_signal_ui_copy.py:23-40` | Confirms the file mixes script-level side effects with library-style helpers | Wrap the top-level dispatch behind an explicit entrypoint function | Important | Simplify | **Verified in current snapshot** |
| Some render functions may call domain functions (e.g. `explain_direction`, `retrieve_relevant_chunks`) directly inline rather than receiving a precomputed view model | — | Blocks extracting pure presentation components later | Introduce a thin view-model step between domain calls and rendering | Optional | Defer | **Needs live verification** — this specific inline-call pattern was documented against `main` (`_render_recommended_direction` app.py:2234-2253, `_render_noise_to_signal_guided_intake` app.py:2871-3033 in main's line numbering); not independently re-confirmed against this snapshot's equivalent functions |

### 8. Loading, empty, error, retry, and insufficient-evidence states

| Finding | File/Component | Impact | Action | Priority | Class | Verification |
|---|---|---|---|---|---|---|
| Insufficient-evidence and out-of-scope states are modeled as first-class, explicitly labeled states with calm, specific copy | `INSUFFICIENT_EVIDENCE_HEADING` app.py:148-150; `GUIDED_INTAKE_NO_EVIDENCE_MESSAGE` app.py:152-155; `_render_out_of_scope_learning_path_empty_state` | Strongest embodiment of "evidence before confidence" / "make uncertainty visible" in the codebase | Keep as-is; treat as the canonical pattern/copy for any rebuild | — | Keep | **Verified in current snapshot** |
| Two different loading experiences coexist: staged `st.status` with progress messages for the main flow, vs. bare `st.spinner` elsewhere | staged: app.py:3406-3427/3447-3451/3475; spinners: app.py:3115, 4319, 4374, 4419, 4660 | Inconsistent "is it still working?" signal depending on which part of the app you're in | Standardize on the staged pattern everywhere long operations occur | Optional | Simplify | **Verified in current snapshot** |
| No retry affordance anywhere — user must manually re-submit the whole form on any failure | confirmed via grep (`retry` has zero hits) | Minor friction on transient failures; works against "reliability is part of the experience" | Add a lightweight "Try again" action that resubmits the last input | Optional | Defer | **Verified in current snapshot** |
| Provider/lock error detection matches on raw exception message substrings (e.g. `"already accessed by another instance of qdrant client"`) | `_is_local_evidence_store_lock_error` / `_is_provider_configuration_error`, app.py:339-350 | Silently stops matching (falls through to a generic error) if the upstream library changes its error wording | Match on exception type/code where available, not message substrings | Important | Simplify | **Verified in current snapshot** |
| Memory-save failures may be caught and logged without any user-facing notice | `_save_noise_to_signal_memory` / `_save_guided_intake_memory`, app.py:589-661 area | If true, the user believes their interaction was saved when it silently wasn't — a "reliability is part of the experience" gap | Surface a non-blocking notice on save failure | Important | Simplify | **Needs live verification** — the underlying save functions and their existence are confirmed in this snapshot; the specific "caught, logged, and invisible to the user" failure-handling behavior was documented against `main`'s version of these functions and was not independently re-confirmed line-by-line for this snapshot |

### 9. Difficulty of a later React/Next.js migration

| Finding | Impact | Action | Priority | Verification |
|---|---|---|---|---|
| ~1,200 lines of CSS keyed to Streamlit-private DOM markers (`st-key-*`, `data-testid`) — none of it is portable | Full visual layer needs a from-scratch rebuild regardless of migration timing | Don't invest further in this CSS approach | Critical | **Verified in current snapshot** |
| `window.parent.document` JS injections encode Streamlit-iframe-specific plumbing with no React equivalent | Must be deleted, not ported; the effect (e.g. accessible labels) has to be re-implemented as idiomatic state/hooks | Minimize/remove now rather than accumulate more | Critical | **Verified in current snapshot** |
| Base64-inlined media (video/audio/images) embedded into every CSS/HTML payload instead of served as static files | Wrong practice for Next.js (`/public` + `<Image>` is the natural fit); needs an asset-pipeline change, not a copy | Serve as static assets even within Streamlit if feasible | Optional | **Verified in current snapshot** (`_asset_data_uri`, app.py:278-299) |
| The underlying decision/evidence/session data model (`decision` dict, `evidence.items`, status enums) is clean, JSON-shaped, and Streamlit-independent | This is the part that migrates almost as-is behind a future API boundary | Keep this contract stable; treat it as the informal API already | — | **Verified in current snapshot** |
| CSS-only chrome-hiding via `:has()` with no source-of-truth state model, if used to hide navigation (as seen on another branch), forces a migration to reverse-engineer intent from CSS rather than reading component state | Increases migration cost | Prefer conditional rendering over CSS-hiding for any new "modes" | Important | **Needs live verification for the sidebar-hiding case** — the sidebar-removal instance of this pattern was observed only in `feature/ux-v2-clarity-experiment`; this snapshot's own `:has()` usage (§4) does not currently hide the sidebar |
| No clear component decomposition; ~75 functions in one file with implicit ordering dependencies, on `main`'s count | No natural seam exists to lift out a component without first isolating its data from Streamlit calls | Any pre-migration work should start by splitting `app.py` into modules with explicit data-in/markup-out functions | Important | **Needs live verification** — the "~75 functions" figure is `main`'s count; this snapshot (being larger, at 4,684 lines) was not independently function-counted |

### 10. Components or ideas worth transferring to a clean MVP

All items below were independently confirmed present in this snapshot unless noted.

- **Decision-trace / evidence-first structure** — `_render_noise_to_signal_metrics` (app.py:2157-2186) surfaces `decision_status`, `evidence_quality`, and `retrieval_attempts` together in a "Why Cognivia recommended this" expander. Directly reusable pattern for "evidence before confidence."
- **Two-tier progressive disclosure of technical detail** — `_render_noise_to_signal_trace` (app.py:3162-3176) and `_render_noise_to_signal_technical_details` (app.py:3178-3222) hide reviewer-level detail behind nested expanders. Matches `DESIGN_PRINCIPLES.md`'s progressive-disclosure principle exactly.
- **Insufficient-evidence / needs-clarification as first-class states** — the strongest asset in the codebase for "make uncertainty visible."
- **Staged progress messaging** during generation (`st.status` + message list) rather than a bare spinner, for the main search flow.
- **Memory store abstraction** (`memory/store.py` protocol, `PostgresMemoryStore`/`NullMemoryStore`, `get_memory_store()` app.py:545-553) — soft-fails to session-only memory when no database is configured, rather than crashing. Genuine "reliability is part of the experience" pattern.
- **Typography system** (Manrope/Inter/Atkinson Hyperlegible Next) with a documented rationale.
- **`AppTest`-based UI test strategy** (`tests/test_noise_to_signal_app.py`, ~2,373 lines) with a recording memory-store test double — reusable testing approach independent of the frontend framework.
- **Zero-Streamlit-coupling core** (`tools/`, `rag/`, `memory/`) — the single biggest de-risking factor for any future migration.
- *Needs live verification, not yet confirmed in this snapshot:* the single-question home screen with a short quick-prompt list, observed in `feature/ux-v2-clarity-experiment`, is a simpler entry point than `main`'s 8-prompt grid and would be worth adopting here if not already present — but whether this snapshot uses that layout or the older one was not independently confirmed (see §1).

---

## Cross-branch comparison

| Axis | `main` | `feature/ux-v2-clarity-experiment` | `audit/ux-v2-snapshot` (current) |
|---|---|---|---|
| `app.py` size | 4,090 lines | ~4,260+ lines (+911 vs. main in the branch diff) | 4,684 lines |
| Background video | Always-on looping crossfade (`USE_BACKGROUND_VIDEO=True`), 3 large video assets (5.7–8.9 MB) inlined as base64 | Disabled (`USE_BACKGROUND_VIDEO=False`), but reportedly ~374 lines of related code left in place unused | A single short, gated intro video (`video0.mp4`, 304 KB); the 3 large unused videos remain in `assets/brand/` as orphaned files (confirmed) |
| Navigation | Sidebar with 3 modes, always visible | Sidebar and mode-switching hidden entirely while in Noise-to-Signal mode — no escape hatch (regression) | Sidebar/mode radio confirmed still present and functional; all 3 modes still reachable |
| CSS `!important` count | 46 (measured) | 196 — 4.3x main (measured) | Not separately measured in this snapshot |
| Home screen | 8-example-prompt grid + labeled textarea (measured) | Single question + 5 quick prompts (measured), but shown simultaneously with results — no ask→answer narrowing (measured) | Not independently re-measured in this snapshot — needs live verification |
| Evidence/uncertainty logic | First-class, well-labeled (strong) | Unchanged from main — confirmed left untouched | Unchanged, same strong pattern confirmed present |
| Focus Mode / icon-button accessibility | N/A (feature doesn't exist) | Icon-only buttons use a robust text-indent-hidden-label technique that does not depend on JS | Icon-only buttons (including Focus Mode) appear to depend on a `MutationObserver`-based JS aria-label patch instead — needs live verification whether this is a real divergence from the experiment branch's approach |
| Net read | Feature-complete, cinema-styled, architecturally unseparated "pre-refactor" baseline | A visual-only experiment that partially succeeded at surface simplification (fewer prompts, one clear question, no permanent looping video) while introducing new fragility (timing-based animations, `!important` bloat, a lost accessible button label, an unrecoverable sidebar removal) | Appears to have adopted some clarity-experiment ideas (short intro, Focus Mode) while keeping the full multi-mode architecture and legacy code paths and orphaned assets — the largest and most complex of the three files |

**Overall:** none of the three branches is a clean MVP candidate as-is. `main` has the most complete and stable evidence/uncertainty logic but the heaviest decorative baggage. The clarity-experiment validated that a simpler home screen and no permanent background video are net positives, but its execution introduced new fragility and at least one real regression (the sidebar removal). This snapshot inherited some of those ideas without inheriting the discipline of removing what they were meant to replace, and several of the experiment branch's specific claims (home-screen layout, button-label details, timing mechanics) were not independently re-verified here — they are flagged above and should be checked live before acting on them.

---

## MVP implementation plan (not yet executed — provided for review only)

1. **Cut scope to one product surface.** Remove "Interview Coach (Sprint 1 legacy)" and demote/hide "AI Skill Compass" dev tools (especially "Run RAG evaluation") from the shipped MVP.
2. **Confirm the actual current home-screen layout live**, then either keep a single-question/quick-prompt framing or adopt it, and fix progressive disclosure so the entry form collapses once a result exists.
3. **Delete dead/orphaned assets** — the ~28+ MB of unused video/PNG files in `assets/brand/` confirmed above.
4. **Confirm the intro video's skip/reload/reduced-motion behavior live**, and fix any hardcoded-timer fragility found.
5. **Fix the confirmed accessibility gap**: set `aria-label`s declaratively in markup instead of via a `MutationObserver`, and confirm whether the Focus Mode button needs the same fix.
6. **Add `st.set_page_config()`** with a real title/favicon.
7. **Extract the markdown-generation function and the scope-classification heuristic** out of `app.py` into `tools/`, preserving the existing UI/logic separation already present in `tools/`, `rag/`, `memory/`.
8. **Leave the evidence/insufficient-evidence/decision-trace logic untouched** — it is the strongest asset in the codebase and already matches `DESIGN_PRINCIPLES.md` closely.
9. **Defer full CSS/JS consolidation** to a post-MVP pass or the eventual React/Next.js migration, per `DESIGN_PRINCIPLES.md`'s "add visual complexity only after the core flow is stable." Track it as Deferred, not silently dropped.
10. **Re-validate against `DESIGN_PRINCIPLES.md`'s Decision Checklist and MVP Definition of Done** before calling it presentable.

---

## Limitations

- No branch was checked out; `main` and `feature/ux-v2-clarity-experiment` were read via `git show`/`git diff` only.
- No visual/browser testing was performed — all contrast, layout, and animation-timing findings not explicitly marked "Verified in current snapshot" are inferred from source on another branch, not measured live on this one.
- `docs/ux_v2/` in this snapshot was found to contain screenshots/reference images; the experiment report (`ux_v2_experiment_report.md`) exists only on `feature/ux-v2-clarity-experiment`.
- This audit reflects the repository state at the time it was produced (2026-07-26) and should be re-run or spot-checked if `app.py` changes materially before the MVP work begins.
