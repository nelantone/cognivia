import html
import os

import streamlit as st

from frontend.assets import BRAND_ASSET_DIR, _asset_data_uri
from tools.provider_config import OPENAI, OFFLINE, OPENROUTER, get_provider_config
from tools.runtime_status import build_runtime_status_lines


def _render_runtime_status() -> None:
    presentation = _runtime_presentation_data(os.environ)
    st.sidebar.subheader("Runtime")
    with st.sidebar.expander(
        "Technical details",
        expanded=False,
        key="runtime_details",
        on_change="ignore",
    ):
        _render_runtime_technical_details(presentation)


def _runtime_presentation_data(
    config,
) -> dict[str, str]:
    status_lines = build_runtime_status_lines(config)
    (
        _,
        _,
        _,
        _,
        _,
        memory_status,
        evidence_status,
    ) = status_lines
    provider_config = get_provider_config(config)
    mode = (
        "Not configured"
        if provider_config.error
        else {
            OPENAI: "OpenAI",
            OPENROUTER: "OpenRouter",
            OFFLINE: "Offline",
        }.get(provider_config.provider, "Not configured")
    )
    provider = {
        OPENAI: "OpenAI",
        OPENROUTER: "OpenRouter",
        OFFLINE: "None",
    }.get(provider_config.provider, "None")
    if provider_config.error and provider != "None":
        provider = f"{provider} (not configured)"

    memory = {
        "local fallback / no durable DB configured": "Local",
        "PostgreSQL configured": "PostgreSQL",
    }.get(memory_status.removeprefix("Memory:").strip(), "Local")
    persistence = "Persistent" if memory == "PostgreSQL" else "None"
    evidence = evidence_status.removeprefix("Evidence:").strip()
    evidence = evidence.removesuffix(" evidence path").replace("/", " / ")
    evidence = evidence[:1].upper() + evidence[1:]
    api_credits = (
        "Not used"
        if provider_config.error or provider_config.provider == OFFLINE
        else f"May use {provider} credits"
    )

    return {
        "mode": mode,
        "provider": provider,
        "memory": memory,
        "persistence": persistence,
        "evidence": evidence,
        "api_credits": api_credits,
    }


def _runtime_technical_details(
    presentation: dict[str, str],
) -> tuple[tuple[str, str], ...]:
    return (
        ("Mode", presentation["mode"]),
        ("Provider", presentation["provider"]),
        ("Memory", presentation["memory"]),
        ("Persistence", presentation["persistence"]),
        ("Evidence", presentation["evidence"]),
        ("API credits", presentation["api_credits"]),
    )


def _render_runtime_technical_details(presentation: dict[str, str]) -> None:
    for label, value in _runtime_technical_details(presentation):
        st.caption(f"{label}: {value}")


def _runtime_drawer_markup(config) -> str:
    presentation = _runtime_presentation_data(config)
    technical_markup = "".join(
        (
            '<p class="nts-runtime-technical-line">'
            f"<strong>{html.escape(label)}:</strong> {html.escape(value)}"
            "</p>"
        )
        for label, value in _runtime_technical_details(presentation)
    )

    return f"""
        <p class="nts-runtime-drawer-heading">Runtime</p>
        <p class="nts-runtime-status-line nts-runtime-mode">{html.escape(presentation["mode"])}</p>
        <p class="nts-runtime-status-line">
            <strong>Memory:</strong> {html.escape(presentation["memory"])}
        </p>
        <p class="nts-runtime-status-line">
            <strong>Evidence:</strong> {html.escape(presentation["evidence"])}
        </p>
        <details class="nts-runtime-technical">
            <summary>Technical details</summary>
            <div class="nts-runtime-technical-copy">
                {technical_markup}
            </div>
        </details>
    """


def _secondary_runtime_markup() -> str:
    return (
        '<span class="secondary-project-drawer-marker" '
        'data-cognivia-secondary-project-drawer="true" aria-hidden="true"></span>'
    )


def _render_secondary_project_drawer() -> None:
    presentation = _runtime_presentation_data(os.environ)
    runtime_markup = _secondary_runtime_markup()

    st.sidebar.subheader("Runtime")

    st.sidebar.html(
        f"""
        <style>
            body:has([data-cognivia-secondary-project-drawer="true"])
            [data-testid="stSidebar"] {{
                box-sizing: border-box;
                height: 100dvh;
                max-height: 100dvh;
                min-width: 0;
                overflow: hidden;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarContent"] {{
                display: flex;
                flex-direction: column;
                box-sizing: border-box;
                height: 100%;
                max-height: 100dvh;
                min-width: 0;
                overflow: hidden;
                overscroll-behavior: contain;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarHeader"] {{
                position: sticky;
                top: 0;
                z-index: 2;
                order: 0;
                display: flex;
                flex: 0 0 auto;
                min-width: 0;
                min-height: 2.75rem;
                height: auto;
                margin: 0;
                padding: 0.25rem 0;
                border-bottom: 1px solid rgba(143, 174, 213, 0.22);
                background: #111F38;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarHeader"]
            div[data-testid="stLogoSpacer"] {{
                height: 0;
                min-width: 0;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarUserContent"] {{
                order: 1;
                flex: 1 1 auto;
                box-sizing: border-box;
                min-width: 0;
                min-height: 0;
                max-width: 100%;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
                overflow-wrap: anywhere;
                padding-bottom: max(2rem, env(safe-area-inset-bottom));
                touch-action: pan-y;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarUserContent"] > div,
            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarUserContent"]
            div[data-testid="stVerticalBlock"],
            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarUserContent"]
            div[data-testid="stElementContainer"] {{
                box-sizing: border-box;
                min-width: 0;
                max-width: 100%;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapseButton"],
            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapseButton"] button,
            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapsedControl"],
            body:has([data-cognivia-secondary-project-drawer="true"])
            button[data-testid="stExpandSidebarButton"] {{
                pointer-events: auto;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapseButton"] button {{
                width: 2.25rem;
                min-width: 2.25rem;
                height: 2.25rem;
                min-height: 2.25rem;
                padding: 0;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapseButton"]
            [data-testid="stIconMaterial"] {{
                font-size: 1.2rem;
            }}

            body:has([data-cognivia-secondary-project-drawer="true"])
            div[data-testid="stSidebarCollapsedControl"],
            body:has([data-cognivia-secondary-project-drawer="true"])
            button[data-testid="stExpandSidebarButton"] {{
                position: fixed;
                top: 0.5rem;
                left: 0.5rem;
                z-index: 100001;
            }}

            .secondary-project-drawer-marker {{
                display: none;
            }}

            div.st-key-secondary_runtime_technical_details {{
                min-width: 0;
                max-width: 100%;
                margin-bottom: 0.75rem;
                font-size: 0.8rem;
                overflow-wrap: anywhere;
            }}
        </style>
        {runtime_markup}
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
            const controllerKey = "__cogniviaSecondaryDrawerController";
            const markerSelector = (
                '[data-cognivia-secondary-project-drawer="true"]'
            );
            const sidebarSelector = '[data-testid="stSidebar"]';
            const collapseButtonSelector = (
                'div[data-testid="stSidebarCollapseButton"] button'
            );
            const expandButtonSelector = (
                'button[data-testid="stExpandSidebarButton"]'
            );
            const setAttributeIfChanged = (element, name, value) => {{
                if (element.getAttribute(name) !== value) {{
                    element.setAttribute(name, value);
                }}
            }};

            const synchronizeToggleSemantics = () => {{
                const isSecondaryDrawer = Boolean(
                    appDocument.querySelector(markerSelector)
                );
                const sidebar = appDocument.querySelector(sidebarSelector);
                if (isSecondaryDrawer && sidebar) {{
                    sidebar.id = "cognivia-secondary-project-drawer";
                }}
                const isExpanded = sidebar?.getAttribute("aria-expanded") === "true";
                const accessibleName = (
                    isSecondaryDrawer ? "Toggle project drawer" : "Toggle sidebar"
                );
                for (const selector of [
                    collapseButtonSelector,
                    expandButtonSelector,
                ]) {{
                    for (const button of appDocument.querySelectorAll(selector)) {{
                        setAttributeIfChanged(button, "aria-label", accessibleName);
                        setAttributeIfChanged(
                            button,
                            "aria-expanded",
                            String(isExpanded),
                        );
                        if (isSecondaryDrawer) {{
                            setAttributeIfChanged(
                                button,
                                "aria-controls",
                                "cognivia-secondary-project-drawer",
                            );
                            button.title = (
                                isExpanded
                                    ? "Close project drawer"
                                    : "Open project drawer"
                            );
                        }} else {{
                            button.removeAttribute("aria-controls");
                            button.title = isExpanded ? "Close sidebar" : "Open sidebar";
                        }}
                    }}
                }}
            }};

            const previousController = parentWindow[controllerKey];
            if (previousController) {{
                previousController.observer.disconnect();
            }}
            const observer = new parentWindow.MutationObserver(
                synchronizeToggleSemantics
            );
            observer.observe(appDocument.body, {{
                attributes: true,
                attributeFilter: ["aria-expanded"],
                childList: true,
                subtree: true,
            }});
            parentWindow[controllerKey] = {{ observer }};
            synchronizeToggleSemantics();
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )

    with st.sidebar.expander(
        "Technical details",
        expanded=False,
        key="secondary_runtime_technical_details",
        on_change="ignore",
    ):
        _render_runtime_technical_details(presentation)


def _render_noise_to_signal_runtime_drawer() -> None:
    forward_uri = _asset_data_uri(BRAND_ASSET_DIR / "forward.svg")
    backward_uri = _asset_data_uri(BRAND_ASSET_DIR / "backward.svg")
    if not forward_uri or not backward_uri:
        return

    drawer_markup = _runtime_drawer_markup(os.environ)
    escaped_forward_uri = html.escape(forward_uri, quote=True)
    escaped_backward_uri = html.escape(backward_uri, quote=True)

    st.html(
        f"""
        <style>
            html,
            body {{
                margin: 0;
                width: 100%;
                height: 100%;
                overflow: visible;
                background: transparent;
            }}

            .nts-runtime-drawer-root {{
                position: fixed;
                top: 9.9rem;
                left: 0.75rem;
                z-index: 99999;
                pointer-events: none;
                opacity: 1;
                visibility: visible;
            }}

            .nts-runtime-drawer-toggle {{
                display: flex;
                width: 52px;
                height: 52px;
                align-items: center;
                justify-content: center;
                padding: 0;
                border: 0;
                border-radius: 50%;
                background: rgba(7, 21, 28, 0.3);
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
                cursor: pointer;
                pointer-events: auto;
            }}

            .nts-runtime-drawer-toggle img {{
                display: block;
                width: 30px;
                height: 30px;
                object-fit: contain;
                pointer-events: none;
            }}

            .nts-runtime-drawer-panel {{
                display: none;
                box-sizing: border-box;
                width: min(340px, calc(100vw - 24px));
                max-width: calc(100vw - 24px);
                margin-top: 0.35rem;
                padding: 0.85rem 0.95rem;
                overflow-x: hidden;
                pointer-events: auto;
                border: 1px solid rgba(216, 239, 242, 0.42);
                border-radius: 14px;
                background: rgba(7, 21, 28, 0.9);
                box-shadow: 0 16px 34px rgba(0, 0, 0, 0.3);
                color: #f4fbfc;
                font: 0.82rem/1.4 sans-serif;
                overflow-wrap: anywhere;
            }}

            .nts-runtime-drawer-panel.is-open {{
                display: block;
            }}

            .nts-runtime-drawer-panel .nts-runtime-drawer-heading {{
                min-width: 0;
                margin: 0;
                color: rgba(244, 251, 252, 0.76);
                font-size: 0.73rem;
                font-weight: 700;
                letter-spacing: 0.07em;
                text-transform: uppercase;
            }}

            .nts-runtime-drawer-panel .nts-runtime-status-line {{
                min-width: 0;
                margin: 0.25rem 0 0;
                color: rgba(244, 251, 252, 0.84);
                font-size: 0.82rem;
                line-height: 1.4;
            }}

            .nts-runtime-drawer-panel .nts-runtime-mode {{
                margin-top: 0.12rem;
                color: #ffffff;
                font-size: 0.93rem;
                font-weight: 650;
            }}

            .nts-runtime-drawer-panel .nts-runtime-status-line strong {{
                color: #f4fbfc;
                font-weight: 650;
            }}

            .nts-runtime-drawer-panel .nts-runtime-technical {{
                max-width: 100%;
                margin-top: 0.65rem;
                padding-top: 0.55rem;
                border-top: 1px solid rgba(216, 239, 242, 0.2);
            }}

            .nts-runtime-drawer-panel .nts-runtime-technical summary {{
                color: rgba(244, 251, 252, 0.86);
                font-weight: 650;
                cursor: pointer;
            }}

            .nts-runtime-drawer-panel .nts-runtime-technical-copy {{
                min-width: 0;
                margin-top: 0.45rem;
                color: rgba(244, 251, 252, 0.72);
            }}

            .nts-runtime-drawer-panel .nts-runtime-technical-copy p {{
                margin: 0.28rem 0 0;
            }}

            @media (max-width: 768px) {{
                .nts-runtime-drawer-root {{
                    top: 7.3rem;
                    left: 0.75rem;
                }}

                .nts-runtime-drawer-panel {{
                    padding: 0.8rem 0.85rem;
                }}
            }}
        </style>
        <div
            class="nts-runtime-drawer-root"
            data-cognivia-runtime-drawer="true"
        >
            <button
                type="button"
                class="nts-runtime-drawer-toggle"
                data-cognivia-runtime-drawer-toggle="true"
                aria-label="Open runtime details"
                aria-expanded="false"
            >
                <img src="{escaped_forward_uri}" alt="">
            </button>
            <section
                class="nts-runtime-drawer-panel"
                data-cognivia-runtime-drawer-panel="true"
                aria-label="Runtime details"
                aria-hidden="true"
            >
                {drawer_markup}
            </section>
        </div>
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
            const forwardIcon = "{escaped_forward_uri}";
            const backwardIcon = "{escaped_backward_uri}";
            const stateKey = "__cogniviaRuntimeDrawerOpen";
            const controllerKey = "__cogniviaRuntimeDrawerController";
            const rootSelector = "[data-cognivia-runtime-drawer]";
            const toggleSelector = "[data-cognivia-runtime-drawer-toggle]";
            const panelSelector = "[data-cognivia-runtime-drawer-panel]";

            const synchronizeRoot = (root, isOpen) => {{
                const toggle = root.querySelector(toggleSelector);
                const panel = root.querySelector(panelSelector);
                const icon = toggle?.querySelector("img");
                if (!toggle || !panel || !icon) {{
                    return;
                }}
                panel.classList.toggle("is-open", isOpen);
                panel.setAttribute("aria-hidden", String(!isOpen));
                toggle.setAttribute("aria-expanded", String(isOpen));
                toggle.setAttribute(
                    "aria-label",
                    isOpen ? "Close runtime details" : "Open runtime details",
                );
                icon.src = isOpen ? backwardIcon : forwardIcon;
            }};

            const synchronizeDrawer = () => {{
                const isOpen = Boolean(parentWindow[stateKey]);
                for (const root of appDocument.querySelectorAll(rootSelector)) {{
                    synchronizeRoot(root, isOpen);
                }}
            }};

            const handleDrawerClick = (event) => {{
                const eventTarget = event.target;
                if (!(eventTarget instanceof parentWindow.Element)) {{
                    return;
                }}
                const clickedToggle = eventTarget.closest(toggleSelector);
                if (!clickedToggle || !clickedToggle.closest(rootSelector)) {{
                    return;
                }}
                parentWindow[stateKey] = !Boolean(parentWindow[stateKey]);
                synchronizeDrawer();
            }};

            const previousController = parentWindow[controllerKey];
            if (previousController) {{
                appDocument.removeEventListener(
                    "click", previousController.handleDrawerClick
                );
                previousController.observer.disconnect();
            }}

            const observer = new parentWindow.MutationObserver(synchronizeDrawer);
            const appRoot = (
                appDocument.querySelector('div[data-testid="stApp"]')
                || appDocument.body
            );
            observer.observe(appRoot, {{ childList: true, subtree: true }});
            appDocument.addEventListener("click", handleDrawerClick);
            parentWindow[controllerKey] = {{
                handleDrawerClick,
                observer,
            }};
            synchronizeDrawer();
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )
