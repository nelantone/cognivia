import json

import streamlit as st

from frontend.browser.styles import APP_RERENDER_STABILITY_CSS


def _install_app_rerender_stability_guard() -> None:
    """Keep the native dark surface stable while Streamlit replaces stale deltas."""
    css_text = json.dumps(APP_RERENDER_STABILITY_CSS)
    st.html(
        f"""
        <script>
        (() => {{
            const resolveParentDocument = () => {{
                if (!window.parent || window.parent === window) {{
                    return document;
                }}
                try {{
                    return window.parent.document;
                }} catch (error) {{
                    return null;
                }}
            }};
            const appDocument = resolveParentDocument();
            if (!appDocument?.head) {{
                return;
            }}
            const styleId = "cognivia-app-rerender-stability";
            let style = appDocument.getElementById(styleId);
            if (!style) {{
                style = appDocument.createElement("style");
                style.id = styleId;
                appDocument.head.appendChild(style);
            }}
            style.textContent = {css_text};
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _render_noise_to_signal_intro_video_controller() -> None:
    st.html(
        """
        <script>
        (() => {
            const resolveParentContext = () => {
                if (!window.parent || window.parent === window) {
                    return { parentWindow: window, appDocument: document };
                }
                try {
                    return {
                        parentWindow: window.parent,
                        appDocument: window.parent.document,
                    };
                } catch (error) {
                    return null;
                }
            };
            const parentContext = resolveParentContext();
            if (!parentContext) {
                return;
            }
            const { parentWindow, appDocument } = parentContext;
            const playedKey = "cognivia.noise-to-signal.intro-played.v1";
            const domReadyTimeoutMs = 2000;
            let layer = null;
            let video = null;
            let finishTimer = null;
            let domReadyTimer = null;
            let domReadyFrame = null;
            let controllerFinished = false;

            const finishIntro = () => {
                controllerFinished = true;
                if (finishTimer) {
                    window.clearTimeout(finishTimer);
                }
                if (domReadyTimer) {
                    window.clearTimeout(domReadyTimer);
                }
                if (domReadyFrame) {
                    parentWindow.cancelAnimationFrame(domReadyFrame);
                }
                if (video) {
                    video.muted = true;
                    video.pause();
                }
                if (layer) {
                    layer.classList.remove("is-playing");
                    layer.classList.add("is-complete");
                }
            };

            let forceReplay = false;
            try {
                const url = new URL(parentWindow.location.href);
                forceReplay = url.searchParams.get("intro") === "1";
                if (forceReplay) {
                    url.searchParams.delete("intro");
                    const nextUrl = `${url.pathname}${url.search}${url.hash}`;
                    parentWindow.history.replaceState(
                        parentWindow.history.state,
                        "",
                        nextUrl,
                    );
                }
            } catch (error) {
                // URL cleanup is best-effort and must not block the application.
            }

            let alreadyPlayed = false;
            try {
                alreadyPlayed = (
                    parentWindow.localStorage.getItem(playedKey) === "true"
                );
            } catch (error) {
                // If storage is unavailable, the Streamlit session guard still applies.
            }

            let reduceMotion = false;
            try {
                reduceMotion = parentWindow.matchMedia(
                    "(prefers-reduced-motion: reduce)",
                ).matches;
            } catch (error) {
                reduceMotion = false;
            }

            const rememberIntro = () => {
                try {
                    parentWindow.localStorage.setItem(playedKey, "true");
                } catch (error) {
                    // Browser persistence is a progressive enhancement.
                }
            };

            const findIntroElements = () => {
                layer = appDocument.querySelector(".nts-intro-video-layer");
                video = appDocument.getElementById("nts-intro-video");
                return Boolean(layer && video);
            };

            const startIntro = () => {
                if (reduceMotion) {
                    rememberIntro();
                    video.pause();
                    finishIntro();
                } else if (alreadyPlayed && !forceReplay) {
                    video.pause();
                    finishIntro();
                } else {
                    rememberIntro();
                    layer.classList.add("is-playing");
                    video.muted = true;
                    video.defaultMuted = true;
                    video.loop = false;
                    video.addEventListener("ended", finishIntro, { once: true });
                    video.addEventListener("error", finishIntro, { once: true });
                    finishTimer = window.setTimeout(finishIntro, 12000);
                    const playback = video.play();
                    if (playback) {
                        playback.catch(finishIntro);
                    }
                }
            };

            const waitForIntroElements = () => {
                if (controllerFinished) {
                    return;
                }
                if (findIntroElements()) {
                    window.clearTimeout(domReadyTimer);
                    domReadyTimer = null;
                    startIntro();
                    return;
                }
                domReadyFrame = parentWindow.requestAnimationFrame(
                    waitForIntroElements,
                );
            };

            domReadyTimer = window.setTimeout(finishIntro, domReadyTimeoutMs);
            waitForIntroElements();
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _render_noise_to_signal_control_accessibility(
    *,
    focus_results: bool,
) -> None:
    should_focus_results = json.dumps(bool(focus_results))
    st.html(
        f"""
        <script>
        (() => {{
            const resolveParentContext = () => {{
                if (!window.parent || window.parent === window) {{
                    return {{ parentWindow: window, appDocument: document }};
                }}
                try {{
                    return {{
                        parentWindow: window.parent,
                        appDocument: window.parent.document,
                    }};
                }} catch (error) {{
                    return null;
                }}
            }};
            const parentContext = resolveParentContext();
            if (!parentContext) {{
                return;
            }}
            const {{ parentWindow, appDocument }} = parentContext;
            const labels = new Map([
                [
                    ".st-key-noise_to_signal_focus_mode_enter button",
                    "Enter Focus Mode",
                ],
                [
                    ".st-key-noise_to_signal_focus_mode_exit button",
                    "Exit Focus Mode",
                ],
                [
                    ".st-key-noise_to_signal_examples_toggle button",
                    "Toggle Try examples",
                ],
                [
                    ".st-key-noise_to_signal_examples_row_toggle button",
                    "Toggle Try examples",
                ],
            ]);

            const applyLabels = () => {{
                for (const [selector, label] of labels) {{
                    for (const button of appDocument.querySelectorAll(selector)) {{
                        button.setAttribute("aria-label", label);
                    }}
                }}
            }};
            applyLabels();

            const legacyObserverKey = "__cogniviaControlLabelObserver";
            parentWindow[legacyObserverKey]?.disconnect();
            delete parentWindow[legacyObserverKey];
            const controllerKey = "__cogniviaControlController";
            const previousController = parentWindow[controllerKey];
            if (previousController) {{
                previousController.observer.disconnect();
                appDocument.removeEventListener(
                    "keydown",
                    previousController.handleSearchKeydown,
                    true,
                );
            }}
            const searchInputSelector = (
                ".st-key-noise_to_signal_search_shell input"
            );
            const submitButtonSelector = (
                ".st-key-generate_noise_to_signal_decision button"
            );
            const handleSearchKeydown = (event) => {{
                if (
                    event.key !== "Enter"
                    || event.isComposing
                    || event.shiftKey
                    || event.ctrlKey
                    || event.metaKey
                    || event.altKey
                ) {{
                    return;
                }}
                const eventTarget = event.target;
                if (
                    !(eventTarget instanceof parentWindow.HTMLInputElement)
                    || !eventTarget.matches(searchInputSelector)
                ) {{
                    return;
                }}
                const submitButton = appDocument.querySelector(
                    submitButtonSelector
                );
                if (
                    !submitButton
                    || submitButton.disabled
                    || submitButton.getAttribute("aria-disabled") === "true"
                ) {{
                    return;
                }}
                event.preventDefault();
                event.stopPropagation();
                submitButton.click();
            }};
            const observer = new parentWindow.MutationObserver(applyLabels);
            observer.observe(appDocument.body, {{ childList: true, subtree: true }});
            appDocument.addEventListener("keydown", handleSearchKeydown, true);
            parentWindow[controllerKey] = {{
                handleSearchKeydown,
                observer,
            }};

            if ({should_focus_results}) {{
                parentWindow.requestAnimationFrame(() => {{
                    const results = appDocument.querySelector(
                        ".st-key-noise_to_signal_results_panel"
                    );
                    if (!results) {{
                        return;
                    }}
                    results.setAttribute("tabindex", "-1");
                    results.scrollIntoView({{ behavior: "smooth", block: "start" }});
                    results.focus({{ preventScroll: true }});
                }});
            }}
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )
