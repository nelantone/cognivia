import html

import streamlit as st

from frontend.assets import (
    FOCUS_MODE_ENTER_ICON_PATH,
    FOCUS_MODE_EXIT_ICON_PATH,
    _asset_data_uri,
)

NOISE_TO_SIGNAL_HELPER_TEXT_COLOR = "#94A8B3"
APP_RERENDER_STABILITY_CSS = """
html,
body,
#root,
div[data-testid="stApp"],
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"] {
    background: #0B132B !important;
    background-color: #0B132B !important;
    color: #F4F7FA !important;
    color-scheme: dark;
}
"""


def _render_noise_to_signal_styles() -> None:
    focus_enter_uri = _asset_data_uri(FOCUS_MODE_ENTER_ICON_PATH) or ""
    focus_exit_uri = _asset_data_uri(FOCUS_MODE_EXIT_ICON_PATH) or ""

    st.markdown(
        f"""
        <style>
        :root {{
            --nts-bg: #0B132B;
            --nts-surface: rgba(20, 35, 66, 0.72);
            --nts-surface-strong: rgba(11, 24, 48, 0.94);
            --nts-text: #F4F7FA;
            --nts-muted: #B9C6D5;
            --nts-helper-text: {NOISE_TO_SIGNAL_HELPER_TEXT_COLOR};
            --nts-teal: #38D9C8;
            --nts-border: rgba(143, 174, 213, 0.34);
            --nts-control-bg: #111F38;
            --nts-control-bg-hover: #152844;
            --nts-control-border: rgba(143, 174, 213, 0.42);
            --nts-heading-font: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
            --nts-interface-font: "Inter", "SF Pro Text", "Segoe UI", sans-serif;
            --nts-reading-font: "Atkinson Hyperlegible Next",
                "Atkinson Hyperlegible", "Segoe UI", sans-serif;
        }}

        html,
        body,
        div[data-testid="stAppViewContainer"] {{
            min-height: 100vh;
            overflow-x: hidden;
            background: var(--nts-bg) !important;
            color: var(--nts-text);
            font-family: var(--nts-interface-font);
        }}

        div[data-testid="stAppViewContainer"] {{
            position: relative;
            isolation: isolate;
        }}

        div[data-testid="stAppViewContainer"] > .main,
        div[data-testid="stAppViewContainer"] section.main,
        div[data-testid="stAppViewContainer"] div[data-testid="stMain"] {{
            position: relative;
            z-index: 2;
            background: transparent !important;
        }}

        #MainMenu,
        footer,
        div[data-testid="stToolbarActions"],
        div[data-testid="stDecoration"],
        .stDeployButton {{
            display: none !important;
        }}

        header[data-testid="stHeader"],
        div[data-testid="stHeader"] {{
            min-height: 3rem !important;
            background: transparent !important;
            z-index: 100000 !important;
        }}

        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        button[data-testid="stExpandSidebarButton"] {{
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
            z-index: 100001 !important;
        }}

        div[data-testid="stAppViewContainer"] .block-container {{
            width: min(100%, 1080px);
            max-width: 1080px;
            padding: 1rem 1.5rem 3rem;
        }}

        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        .nts-brand-tagline {{
            font-family: var(--nts-heading-font) !important;
            letter-spacing: 0;
        }}

        div[data-testid="stAppViewContainer"] button,
        div[data-testid="stAppViewContainer"] input,
        div[data-testid="stAppViewContainer"] textarea,
        div[data-testid="stAppViewContainer"] label,
        div[data-testid="stAppViewContainer"] summary {{
            font-family: var(--nts-interface-font) !important;
        }}

        div.st-key-noise_to_signal_results_panel p,
        div.st-key-noise_to_signal_results_panel li,
        div.st-key-noise_to_signal_results_panel blockquote,
        div.st-key-noise_to_signal_results_panel [data-testid="stMarkdownContainer"] {{
            font-family: var(--nts-reading-font) !important;
            line-height: 1.62;
        }}

        div.st-key-noise_to_signal_header {{
            width: min(72vw, 430px);
            margin: 0 auto;
            padding: 0.2rem 0 0.8rem;
            text-align: center;
        }}

        .nts-brand img {{
            display: block;
            width: min(100%, 390px);
            height: auto;
            margin: 0 auto;
            object-fit: contain;
        }}

        .nts-brand-tagline {{
            margin: 0.3rem auto 0;
            color: rgba(244, 247, 250, 0.82);
            font-size: 0.94rem;
            line-height: 1.45;
        }}

        div.st-key-noise_to_signal_home_shell {{
            width: min(100%, 760px);
            margin: 0 auto;
            padding: clamp(1.5rem, 4vh, 3rem) 0 clamp(3rem, 8vh, 5rem);
        }}

        div.st-key-noise_to_signal_landing_card {{
            width: min(100%, 720px);
            margin: 0 auto;
            padding: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            text-align: center;
        }}

        h1.nts-home-question {{
            margin: 0 0 1.25rem;
            color: var(--nts-text);
            font-size: clamp(1.65rem, 3vw, 2.35rem);
            font-weight: 520;
            line-height: 1.2;
            text-align: center;
        }}

        div.st-key-noise_to_signal_search_shell {{
            position: relative;
            width: 100%;
            margin: 0 auto;
        }}

        div.st-key-noise_to_signal_landing_card div[data-baseweb="input"],
        div.st-key-noise_to_signal_landing_card div[data-testid="stTextInputRootElement"],
        div.st-key-noise_to_signal_landing_card div[data-baseweb="base-input"] {{
            min-height: 3.7rem !important;
            border: 1px solid var(--nts-border) !important;
            border-radius: 12px !important;
            background: var(--nts-surface) !important;
            box-shadow: inset 0 -2px 0 rgba(56, 217, 200, 0.84) !important;
        }}

        div.st-key-noise_to_signal_examples_toggle {{
            position: absolute;
            top: 0.54rem;
            left: 0.66rem;
            z-index: 7 !important;
            width: 2.65rem !important;
            height: 2.65rem !important;
            margin: 0 !important;
        }}

        div.st-key-noise_to_signal_examples_toggle button {{
            width: 2.65rem !important;
            height: 2.65rem !important;
            min-height: 2.65rem !important;
            padding: 0 !important;
            overflow: hidden;
            border: 0 !important;
            border-radius: 8px !important;
            background: transparent !important;
            box-shadow: none !important;
            color: transparent !important;
            text-indent: -999px;
        }}

        div.st-key-noise_to_signal_examples_toggle button::before {{
            content: "⌕";
            display: flex;
            width: 100%;
            height: 100%;
            align-items: center;
            justify-content: center;
            color: rgba(210, 223, 237, 0.72);
            font-size: 1.55rem;
            line-height: 1;
            text-indent: 0;
        }}

        div.st-key-noise_to_signal_examples_toggle button:hover::before {{
            color: var(--nts-teal);
        }}

        div.st-key-noise_to_signal_landing_card input {{
            min-height: 3.7rem;
            padding: 0.8rem 4rem 0.8rem 3.55rem !important;
            border: 0 !important;
            background: transparent !important;
            color: var(--nts-text) !important;
            box-shadow: none !important;
            caret-color: var(--nts-teal);
            font-size: 1rem !important;
        }}

        div.st-key-noise_to_signal_landing_card input::placeholder {{
            color: rgba(210, 223, 237, 0.6);
            opacity: 1;
        }}

        div.st-key-noise_to_signal_landing_card input:focus-visible {{
            outline: 2px solid rgba(56, 217, 200, 0.82);
            outline-offset: 3px;
        }}

        div.st-key-generate_noise_to_signal_decision {{
            position: absolute;
            top: 0.54rem;
            right: 0.72rem;
            z-index: 6 !important;
            width: 2.65rem !important;
            height: 2.65rem !important;
            margin: 0 !important;
            padding-left: 0.55rem;
            border-left: 1px solid rgba(210, 223, 237, 0.18);
        }}

        div.st-key-generate_noise_to_signal_decision button {{
            width: 2.1rem !important;
            height: 2.55rem !important;
            min-height: 2.55rem !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            color: rgba(56, 217, 200, 0.78) !important;
            font-size: 1.55rem !important;
            font-weight: 400 !important;
        }}

        div.st-key-generate_noise_to_signal_decision button:hover {{
            color: #8AF2E7 !important;
        }}

        div.st-key-generate_noise_to_signal_decision button kbd {{
            display: none !important;
        }}

        div.st-key-generate_noise_to_signal_decision button:focus-visible,
        div.st-key-noise_to_signal_examples_toggle button:focus-visible,
        div.st-key-noise_to_signal_examples_row_toggle button:focus-visible,
        div.st-key-noise_to_signal_quick_prompts button:focus-visible,
        div.st-key-noise_to_signal_start_guided_intake button:focus-visible,
        div.st-key-noise_to_signal_start_new button:focus-visible,
        div.st-key-noise_to_signal_focus_mode_enter button:focus-visible,
        div.st-key-noise_to_signal_focus_mode_exit button:focus-visible {{
            outline: 2px solid #8AF2E7 !important;
            outline-offset: 3px !important;
        }}

        div.st-key-noise_to_signal_examples_row_toggle {{
            width: 100%;
            margin: 0.35rem auto 0 !important;
            text-align: left;
        }}

        div.st-key-noise_to_signal_examples_row_toggle button {{
            justify-content: flex-start !important;
            width: 100% !important;
            min-height: 2.55rem !important;
            padding: 0.5rem 0.8rem !important;
            border: 1px solid rgba(143, 174, 213, 0.24) !important;
            border-radius: 0 0 12px 12px !important;
            background: rgba(15, 29, 55, 0.84) !important;
            box-shadow: none !important;
            color: rgba(244, 247, 250, 0.78) !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            text-align: left !important;
        }}

        div.st-key-noise_to_signal_examples_row_toggle button:hover {{
            border-color: rgba(56, 217, 200, 0.4) !important;
            background: rgba(56, 217, 200, 0.07) !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_quick_prompts {{
            width: 100%;
            margin: 0 !important;
            padding: 0.18rem 0 0.25rem !important;
            overflow: hidden;
            border: 1px solid rgba(143, 174, 213, 0.24) !important;
            border-top: 0 !important;
            border-radius: 0 0 12px 12px !important;
            background: rgba(15, 29, 55, 0.92) !important;
            box-shadow: inset 0 1px 0 rgba(88, 147, 255, 0.08) !important;
            text-align: left;
        }}

        div.st-key-noise_to_signal_examples_row_toggle:has(+ div.st-key-noise_to_signal_quick_prompts)
        button {{
            border-radius: 0 !important;
            border-bottom-color: rgba(143, 174, 213, 0.14) !important;
        }}

        div.st-key-noise_to_signal_quick_prompts div[data-testid="stButton"] {{
            margin: 0 !important;
        }}

        div.st-key-noise_to_signal_quick_prompts button {{
            justify-content: space-between !important;
            width: 100% !important;
            min-height: 2.55rem !important;
            padding: 0.5rem 0.9rem !important;
            border: 0 !important;
            border-top: 1px solid rgba(143, 174, 213, 0.14) !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            color: rgba(138, 242, 231, 0.88) !important;
            font-size: 0.9rem !important;
            font-weight: 430 !important;
            text-align: left !important;
        }}

        div.st-key-noise_to_signal_quick_prompts button::after {{
            content: "→";
            margin-left: auto;
            color: var(--nts-teal);
            font-size: 1rem;
        }}

        div.st-key-noise_to_signal_quick_prompts button:hover {{
            background: rgba(56, 217, 200, 0.07) !important;
            color: var(--nts-text) !important;
        }}

        .nts-loading-card {{
            width: min(100%, 720px);
            margin: 0.8rem auto 0;
            padding: 0.9rem 1rem;
            border: 1px solid rgba(88, 147, 255, 0.18);
            border-radius: 8px;
            background: #182234;
            color: #F4F7FA;
            box-shadow: none;
        }}

        .nts-loading-title {{
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin: 0;
            color: #F4F7FA;
            font-family: var(--nts-heading-font);
            font-size: 0.98rem;
            font-weight: 650;
            line-height: 1.35;
        }}

        .nts-loading-copy {{
            margin: 0.28rem 0 0;
            color: #B9C6D5;
            font-size: 0.88rem;
            line-height: 1.45;
        }}

        .nts-loading-dots {{
            display: inline-flex;
            align-items: center;
            gap: 0.24rem;
            min-width: 2rem;
        }}

        .nts-loading-dots span {{
            width: 0.32rem;
            height: 0.32rem;
            border-radius: 50%;
            background: #8AF2E7;
            opacity: 0.35;
            animation: ntsLoadingDot 1.2s ease-in-out infinite;
        }}

        .nts-loading-dots span:nth-child(2) {{
            animation-delay: 160ms;
        }}

        .nts-loading-dots span:nth-child(3) {{
            animation-delay: 320ms;
        }}

        body:has(.nts-loading-card)
        div.st-key-generate_noise_to_signal_decision button,
        body:has(.nts-loading-card)
        div.st-key-noise_to_signal_quick_prompts button {{
            pointer-events: none !important;
            cursor: wait !important;
        }}

        @keyframes ntsLoadingDot {{
            0%, 60%, 100% {{
                opacity: 0.3;
                transform: translateY(0);
            }}
            30% {{
                opacity: 0.9;
                transform: translateY(-0.12rem);
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .nts-loading-dots span {{
                animation: none !important;
                opacity: 0.55;
                transform: none !important;
            }}
        }}

        div.st-key-noise_to_signal_start_guided_intake {{
            width: min(100%, 280px);
            margin: 0.9rem auto 0;
        }}

        div.st-key-noise_to_signal_start_guided_intake button {{
            width: 100% !important;
            min-height: 2.8rem !important;
            border: 1px solid rgba(56, 217, 200, 0.72) !important;
            border-radius: 8px !important;
            background: rgba(15, 29, 55, 0.92) !important;
            color: var(--nts-text) !important;
            font-weight: 600 !important;
        }}

        div.st-key-noise_to_signal_start_guided_intake button:hover {{
            background: rgba(56, 217, 200, 0.12) !important;
        }}

        .nts-home-support {{
            margin: 1rem auto 0;
            color: rgba(244, 247, 250, 0.76);
            font-family: var(--nts-heading-font);
            font-size: 1rem;
            line-height: 1.5;
            text-align: center;
        }}

        .nts-home-support::before {{
            content: "↓";
            display: block;
            margin-bottom: 0.15rem;
            color: var(--nts-teal);
            font-size: 1.35rem;
        }}

        .nts-home-support span {{
            color: var(--nts-teal);
        }}

        div.st-key-noise_to_signal_start_new {{
            display: flex;
            width: 100% !important;
            justify-content: flex-end;
            margin: -0.2rem 0 0.7rem;
        }}

        div.st-key-noise_to_signal_start_new div[data-testid="stButton"] {{
            width: auto !important;
            margin-left: auto !important;
        }}

        div.st-key-noise_to_signal_start_new button {{
            width: auto !important;
            min-width: 8rem !important;
            min-height: 2.65rem !important;
            padding: 0.42rem 0.75rem !important;
            border: 1px solid rgba(88, 147, 255, 0.28) !important;
            border-radius: 8px !important;
            background: rgba(10, 22, 42, 0.34) !important;
            box-shadow: none !important;
            color: transparent !important;
            font-size: 0 !important;
            font-weight: 500 !important;
        }}

        div.st-key-noise_to_signal_start_new button p {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}

        div.st-key-noise_to_signal_start_new button::before {{
            content: "↺  New search";
            display: inline-block;
            white-space: nowrap;
            color: rgba(185, 198, 213, 0.9);
            font-size: 0.86rem;
        }}

        div.st-key-noise_to_signal_start_new button:hover {{
            border-color: rgba(56, 217, 200, 0.5) !important;
            background: rgba(56, 217, 200, 0.07) !important;
            color: transparent !important;
        }}

        div.st-key-noise_to_signal_start_new button:hover::before {{
            color: #8AF2E7;
        }}

        div.st-key-noise_to_signal_results_panel {{
            width: min(100%, 980px) !important;
            margin: 1.5rem auto 0 !important;
            padding: 1.35rem 1.5rem 1.65rem !important;
            border: 1px solid rgba(143, 174, 213, 0.24) !important;
            border-radius: 8px !important;
            background: rgba(9, 19, 36, 0.86) !important;
            box-shadow: none !important;
            color: var(--nts-text) !important;
        }}

        .nts-results-compact-callout {{
            margin: 0.75rem 0;
            padding: 0.8rem 0.9rem;
            border: 1px solid rgba(143, 174, 213, 0.24);
            border-radius: 8px;
            background: rgba(17, 31, 56, 0.78);
            color: var(--nts-muted);
            font-size: 0.9rem;
            line-height: 1.5;
        }}

        div[class*="st-key-noise_to_signal_learning_schema_card_"] {{
            margin: 1rem 0 !important;
            padding: 1rem !important;
            border: 1px solid rgba(88, 147, 255, 0.24) !important;
            border-radius: 10px !important;
            background: #111F38 !important;
            box-shadow: inset 0 1px 0 rgba(138, 242, 231, 0.04) !important;
        }}

        .nts-learning-path-map {{
            margin: 0.8rem 0 0.9rem;
            padding: 0.85rem;
            border: 1px solid rgba(143, 174, 213, 0.24);
            border-radius: 9px;
            background: rgba(9, 21, 40, 0.72);
        }}

        .nts-learning-path-map-title {{
            margin: 0 0 0.65rem;
            color: var(--nts-muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .nts-learning-path-steps {{
            display: grid;
            grid-template-columns:
                repeat(var(--nts-step-count), minmax(0, 1fr));
            gap: 1.7rem;
            margin: 0;
            padding: 0;
            list-style: none;
        }}

        .nts-learning-path-step {{
            position: relative;
            display: flex;
            min-width: 0;
            min-height: 4.4rem;
            align-items: center;
            gap: 0.55rem;
            padding: 0.7rem;
            border: 1px solid rgba(143, 174, 213, 0.3);
            border-radius: 8px;
            background: #182234;
            color: var(--nts-text);
        }}

        .nts-learning-path-step:not(:last-child)::after {{
            content: "→";
            position: absolute;
            top: 50%;
            right: -1.35rem;
            color: #8AF2E7;
            font-size: 1.05rem;
            line-height: 1;
            transform: translateY(-50%);
        }}

        .nts-learning-path-step-index {{
            display: inline-flex;
            width: 1.55rem;
            height: 1.55rem;
            flex: 0 0 1.55rem;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(138, 242, 231, 0.58);
            border-radius: 50%;
            color: #8AF2E7;
            font-size: 0.76rem;
            font-weight: 750;
        }}

        .nts-learning-path-step-text {{
            min-width: 0;
            color: var(--nts-text);
            font-size: 0.82rem;
            font-weight: 650;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }}

        .nts-learning-path-details {{
            margin: 0.8rem 0 0.15rem;
            border: 1px solid rgba(143, 174, 213, 0.26);
            border-radius: 8px;
            background: rgba(9, 21, 40, 0.58);
            color: var(--nts-text);
        }}

        .nts-learning-path-details > summary {{
            display: flex;
            min-height: 2.75rem;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.65rem 0.8rem;
            cursor: pointer;
            list-style: none;
            color: var(--nts-text);
            font-size: 0.86rem;
            font-weight: 650;
        }}

        .nts-learning-path-details > summary::-webkit-details-marker {{
            display: none;
        }}

        .nts-learning-path-details > summary::after {{
            content: "›";
            flex: 0 0 auto;
            color: #8AF2E7;
            font-size: 1.2rem;
            line-height: 1;
        }}

        .nts-learning-path-details[open] > summary {{
            border-bottom: 1px solid rgba(143, 174, 213, 0.2);
        }}

        .nts-learning-path-details[open] > summary::after {{
            content: "⌄";
        }}

        .nts-learning-path-details > summary:focus-visible {{
            outline: 2px solid #8AF2E7;
            outline-offset: 2px;
            border-radius: 7px;
        }}

        .nts-learning-path-detail-list {{
            margin: 0;
            padding: 0.75rem 0.8rem 0.8rem 1.9rem;
        }}

        .nts-learning-path-detail-list li {{
            margin: 0.35rem 0;
            color: var(--nts-muted);
            font-size: 0.84rem;
            line-height: 1.45;
        }}

        .nts-learning-path-detail-list strong {{
            color: var(--nts-text);
        }}

        div.st-key-noise_to_signal_results_panel p,
        div.st-key-noise_to_signal_results_panel label,
        div.st-key-noise_to_signal_results_panel h2,
        div.st-key-noise_to_signal_results_panel h3,
        div.st-key-noise_to_signal_results_panel [data-testid="stMarkdownContainer"] {{
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_results_panel div[data-testid="stTabs"]
        button[data-baseweb="tab"] {{
            min-height: 2.75rem;
            padding: 0.55rem 0.85rem;
            border-radius: 7px 7px 0 0;
            background: rgba(9, 21, 40, 0.58) !important;
            color: rgba(185, 198, 213, 0.88) !important;
        }}

        div.st-key-noise_to_signal_results_panel div[data-testid="stTabs"]
        button[data-baseweb="tab"] p {{
            color: inherit !important;
        }}

        div.st-key-noise_to_signal_results_panel div[data-testid="stTabs"]
        button[data-baseweb="tab"]:hover {{
            background: rgba(21, 40, 68, 0.82) !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_results_panel div[data-testid="stTabs"]
        button[data-baseweb="tab"][aria-selected="true"] {{
            border-bottom-color: #8AF2E7 !important;
            background: var(--nts-control-bg-hover) !important;
            color: var(--nts-teal) !important;
            box-shadow: inset 0 -2px 0 rgba(138, 242, 231, 0.86) !important;
        }}

        div.st-key-noise_to_signal_results_panel div[data-testid="stTabs"]
        button[data-baseweb="tab"]:focus-visible {{
            outline: 2px solid #8AF2E7 !important;
            outline-offset: -2px !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"] {{
            border: 1px solid var(--nts-control-border) !important;
            background: var(--nts-control-bg) !important;
            box-shadow: inset 0 1px 0 rgba(138, 242, 231, 0.04) !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:hover,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:hover {{
            border-color: rgba(138, 242, 231, 0.58) !important;
            background: var(--nts-control-bg-hover) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:focus,
        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:focus,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:focus-within {{
            border-color: #8AF2E7 !important;
            background: var(--nts-control-bg-hover) !important;
            box-shadow: 0 0 0 2px rgba(56, 217, 200, 0.24) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:focus-visible,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:focus-visible {{
            outline: 2px solid #8AF2E7 !important;
            outline-offset: 2px !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:active,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:active {{
            border-color: rgba(138, 242, 231, 0.74) !important;
            background: #172D4C !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div[aria-disabled="true"],
        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:has([aria-disabled="true"]),
        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] > div:has(input:disabled),
        div.st-key-noise_to_signal_results_panel
        .stNumberInput [data-testid="stNumberInputContainer"]:has(input:disabled) {{
            border-color: rgba(143, 174, 213, 0.2) !important;
            background: #0D192C !important;
            box-shadow: none !important;
            color: rgba(185, 198, 213, 0.58) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput input[data-testid="stNumberInputField"],
        div.st-key-noise_to_signal_results_panel
        .stNumberInput div[data-baseweb="input"],
        div.st-key-noise_to_signal_results_panel
        .stNumberInput div[data-baseweb="base-input"],
        div.st-key-noise_to_signal_results_panel
        .stSelectbox div[data-baseweb="select"] {{
            background: transparent !important;
            color: var(--nts-text) !important;
            caret-color: var(--nts-teal);
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput input[data-testid="stNumberInputField"]:focus,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput input[data-testid="stNumberInputField"]:focus-visible {{
            outline: 0 !important;
            background: transparent !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput input[data-testid="stNumberInputField"]::placeholder {{
            color: rgba(185, 198, 213, 0.72) !important;
            opacity: 1 !important;
        }}

        div.st-key-noise_to_signal_results_panel .stSelectbox input:disabled,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput input[data-testid="stNumberInputField"]:disabled {{
            background: transparent !important;
            color: rgba(185, 198, 213, 0.58) !important;
            -webkit-text-fill-color: rgba(185, 198, 213, 0.58) !important;
            opacity: 1 !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {{
            border: 1px solid var(--nts-control-border) !important;
            background: var(--nts-control-bg) !important;
            background-color: var(--nts-control-bg) !important;
            box-shadow: inset 0 1px 0 rgba(138, 242, 231, 0.04) !important;
            color: var(--nts-text) !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="base-input"],
        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="base-input"] input,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] textarea {{
            background: var(--nts-control-bg) !important;
            background-color: var(--nts-control-bg) !important;
            color: var(--nts-text) !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:hover div[data-baseweb="base-input"],
        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:hover input,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover > div,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover textarea {{
            border-color: rgba(138, 242, 231, 0.58) !important;
            background: var(--nts-control-bg-hover) !important;
            background-color: var(--nts-control-bg-hover) !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:has(input:focus-visible),
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"]:has(textarea:focus-visible) {{
            border-color: #8AF2E7 !important;
            background: var(--nts-control-bg-hover) !important;
            background-color: var(--nts-control-bg-hover) !important;
            box-shadow: 0 0 0 2px rgba(56, 217, 200, 0.24) !important;
            outline: 2px solid #8AF2E7 !important;
            outline-offset: 2px !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:focus-within div[data-baseweb="base-input"],
        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:focus-within input,
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"]:focus-within > div,
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"]:focus-within textarea {{
            background: var(--nts-control-bg-hover) !important;
            background-color: var(--nts-control-bg-hover) !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="input"]:active,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:active {{
            border-color: rgba(138, 242, 231, 0.74) !important;
            background: #172D4C !important;
            background-color: #172D4C !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="base-input"] input,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] textarea {{
            color: var(--nts-text) !important;
            -webkit-text-fill-color: var(--nts-text) !important;
            caret-color: var(--nts-teal) !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="base-input"] input::placeholder,
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"] textarea::placeholder {{
            color: rgba(185, 198, 213, 0.72) !important;
            -webkit-text-fill-color: rgba(185, 198, 213, 0.72) !important;
            opacity: 1 !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:has(input:disabled),
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"]:has(textarea:disabled) {{
            border-color: rgba(143, 174, 213, 0.2) !important;
            background: #0D192C !important;
            background-color: #0D192C !important;
            box-shadow: none !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextInput"] div[data-baseweb="base-input"]:has(input:disabled),
        body:has(.nts-brand)
        div[data-testid="stTextInput"] input:disabled,
        body:has(.nts-brand)
        div[data-testid="stTextArea"]
        div[data-baseweb="textarea"]:has(textarea:disabled) > div,
        body:has(.nts-brand)
        div[data-testid="stTextArea"] textarea:disabled {{
            background: #0D192C !important;
            background-color: #0D192C !important;
            color: rgba(185, 198, 213, 0.58) !important;
            -webkit-text-fill-color: rgba(185, 198, 213, 0.58) !important;
            opacity: 1 !important;
        }}

        body:has(.nts-brand)
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] textarea {{
            color-scheme: dark;
            resize: vertical !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"],
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"] {{
            border-left: 1px solid rgba(143, 174, 213, 0.22) !important;
            background: #142641 !important;
            color: rgba(244, 247, 250, 0.88) !important;
            box-shadow: none !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"]:hover,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"]:hover,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"]:focus,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"]:focus {{
            background: #1A3355 !important;
            color: #8AF2E7 !important;
            outline: 0 !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"]:focus-visible,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"]:focus-visible {{
            outline: 2px solid #8AF2E7 !important;
            outline-offset: -3px !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"]:active,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"]:active {{
            background: #1D3A60 !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"]:disabled,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"]:disabled,
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepDown"][aria-disabled="true"],
        div.st-key-noise_to_signal_results_panel
        .stNumberInput button[data-testid="stNumberInputStepUp"][aria-disabled="true"] {{
            border-left-color: rgba(143, 174, 213, 0.14) !important;
            background: #0D192C !important;
            color: rgba(185, 198, 213, 0.42) !important;
            cursor: not-allowed !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button {{
            border: 1px solid rgba(56, 217, 200, 0.46) !important;
            background: #142641 !important;
            box-shadow: none !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button p {{
            color: inherit !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button:hover,
        div.st-key-noise_to_signal_generate_guided_path button:focus {{
            border-color: rgba(138, 242, 231, 0.7) !important;
            background: #1A3355 !important;
            color: #F4F7FA !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button:focus-visible {{
            outline: 2px solid #8AF2E7 !important;
            outline-offset: 2px !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button:active {{
            border-color: #8AF2E7 !important;
            background: #1D3A60 !important;
        }}

        div.st-key-noise_to_signal_generate_guided_path button:disabled,
        div.st-key-noise_to_signal_generate_guided_path button[aria-disabled="true"] {{
            border-color: rgba(143, 174, 213, 0.18) !important;
            background: #0D192C !important;
            box-shadow: none !important;
            color: rgba(185, 198, 213, 0.56) !important;
            cursor: not-allowed !important;
            opacity: 1 !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details {{
            border-color: rgba(143, 174, 213, 0.28) !important;
            background: rgba(9, 21, 40, 0.72) !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary {{
            background: #111F38 !important;
            color: rgba(244, 247, 250, 0.9) !important;
            box-shadow: none !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details[open] > summary {{
            background: #152844 !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary:hover,
        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary:focus {{
            background: #1A3355 !important;
            color: var(--nts-text) !important;
            outline: 0 !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary:focus-visible {{
            background: #1A3355 !important;
            outline: 2px solid #8AF2E7 !important;
            outline-offset: -2px !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary:active {{
            background: #1D3A60 !important;
        }}

        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary p,
        div.st-key-noise_to_signal_results_panel
        div[data-testid="stExpander"] details > summary svg {{
            color: inherit !important;
        }}

        body:has(.nts-brand)
        div[data-baseweb="popover"] {{
            color: var(--nts-text) !important;
        }}

        body:has(.nts-brand)
        div[data-baseweb="popover"]
        ul[role="listbox"] {{
            border: 1px solid var(--nts-control-border) !important;
            background: #0F1D34 !important;
            box-shadow: 0 12px 28px rgba(3, 9, 20, 0.36) !important;
        }}

        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"] {{
            background: #0F1D34 !important;
            color: var(--nts-text) !important;
        }}

        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"]:hover,
        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"]:focus,
        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"]:focus-visible,
        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"]:active,
        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"][aria-selected="true"] {{
            background: var(--nts-control-bg-hover) !important;
            color: #8AF2E7 !important;
        }}

        body:has(.nts-brand)
        div[data-baseweb="popover"]
        li[role="option"][aria-disabled="true"] {{
            background: #0D192C !important;
            color: rgba(185, 198, 213, 0.5) !important;
        }}

        div.st-key-noise_to_signal_query_summary {{
            margin-bottom: 1rem;
        }}

        div.st-key-noise_to_signal_query_summary div[data-testid="stChatMessage"] {{
            border: 1px solid rgba(88, 147, 255, 0.18) !important;
            border-radius: 9px !important;
            background: #182234 !important;
            box-shadow:
                inset 0 1px 0 rgba(138, 242, 231, 0.06),
                0 10px 24px rgba(3, 9, 20, 0.18) !important;
            color: var(--nts-text) !important;
        }}

        div.st-key-noise_to_signal_query_summary div[data-testid="stChatMessage"]
        [data-testid="stChatMessageAvatarUser"] {{
            opacity: 0.72;
        }}

        div.st-key-noise_to_signal_focus_mode_enter,
        div.st-key-noise_to_signal_focus_mode_exit {{
            position: fixed;
            right: 0.9rem;
            top: 0.9rem;
            z-index: 100002 !important;
            width: 52px !important;
            height: 52px !important;
        }}

        div.st-key-noise_to_signal_focus_mode_enter button,
        div.st-key-noise_to_signal_focus_mode_exit button {{
            width: 52px !important;
            height: 52px !important;
            min-height: 52px !important;
            padding: 0 !important;
            overflow: hidden;
            border: 1px solid rgba(88, 147, 255, 0.22) !important;
            border-radius: 10px !important;
            background: rgba(10, 22, 42, 0.34) !important;
            box-shadow: none !important;
            color: transparent !important;
            text-indent: -999px;
        }}

        div.st-key-noise_to_signal_focus_mode_enter button::before,
        div.st-key-noise_to_signal_focus_mode_exit button::before {{
            content: "";
            display: block;
            flex: 0 0 44px;
            width: 44px;
            min-width: 44px;
            height: 44px;
            margin: 3px;
            background-position: center;
            background-repeat: no-repeat;
            background-size: 72px 72px;
        }}

        div.st-key-noise_to_signal_focus_mode_enter button:hover,
        div.st-key-noise_to_signal_focus_mode_exit button:hover {{
            border-color: rgba(56, 217, 200, 0.48) !important;
            background: rgba(56, 217, 200, 0.07) !important;
        }}

        div.st-key-noise_to_signal_focus_mode_enter button::before {{
            background-image: url("{html.escape(focus_enter_uri, quote=True)}");
        }}

        div.st-key-noise_to_signal_focus_mode_exit button::before {{
            background-image: url("{html.escape(focus_exit_uri, quote=True)}");
        }}

        body:has(.nts-focus-mode-active) [data-testid="stSidebar"],
        body:has(.nts-focus-mode-active) .nts-runtime-drawer-root,
        body:has(.nts-focus-mode-active) div.st-key-noise_to_signal_header,
        body:has(.nts-focus-mode-active) div.st-key-noise_to_signal_focus_mode_enter {{
            display: none !important;
        }}

        body:has(.nts-focus-mode-active) div[data-testid="stAppViewContainer"] {{
            background: var(--nts-bg) !important;
        }}

        .nts-intro-video-layer {{
            position: fixed;
            inset: 0;
            z-index: 100002;
            overflow: hidden;
            background: var(--nts-bg);
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            transition:
                opacity 480ms cubic-bezier(0.22, 1, 0.36, 1),
                visibility 0s linear 480ms;
        }}

        .nts-intro-video-layer.is-playing {{
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
            animation: ntsIntroFailsafe 12s linear forwards;
        }}

        .nts-intro-video-layer.is-ready {{
            opacity: 1;
        }}

        .nts-intro-video-layer.is-complete {{
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            animation: none;
        }}

        .nts-intro-video-layer video {{
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        @keyframes ntsIntroFailsafe {{
            0%,
            99% {{
                opacity: 1;
                visibility: visible;
                pointer-events: auto;
            }}
            100% {{
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
            }}
        }}

        @media (max-width: 768px) {{
            div[data-testid="stAppViewContainer"] .block-container {{
                padding-right: 0.75rem;
                padding-left: 0.75rem;
            }}

            div.st-key-noise_to_signal_header {{
                width: min(76vw, 360px);
            }}

            .nts-ux-home-shell,
            div.st-key-noise_to_signal_landing_card {{
                width: 100% !important;
                max-width: 100% !important;
            }}

            div.st-key-noise_to_signal_landing_card {{
                margin-top: clamp(1.5rem, 5vh, 3rem);
            }}

            h1.nts-home-question {{
                font-size: clamp(1.45rem, 7vw, 1.9rem);
            }}

            div.st-key-noise_to_signal_results_panel {{
                width: 100% !important;
                margin-top: 1rem !important;
                padding: 1rem 0.8rem 1.2rem !important;
            }}

            .nts-learning-path-steps {{
                grid-template-columns: 1fr;
                gap: 1.7rem;
            }}

            .nts-learning-path-step:not(:last-child)::after {{
                top: auto;
                right: auto;
                bottom: -1.35rem;
                left: 50%;
                transform: translateX(-50%) rotate(90deg);
            }}

        }}

        @media (prefers-reduced-motion: reduce) {{
            *,
            *::before,
            *::after {{
                scroll-behavior: auto !important;
                animation-duration: 1ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 1ms !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
