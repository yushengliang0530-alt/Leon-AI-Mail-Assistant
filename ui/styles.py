"""V2.1 presentation tokens and stable Streamlit styling helpers."""

from __future__ import annotations

import streamlit as st


DESIGN_TOKENS = {
    "primary": "#2563EB",
    "primary_strong": "#1D4ED8",
    "canvas": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_info": "#EFF6FF",
    "border": "#E2E8F0",
    "ink": "#0F172A",
    "text": "#475569",
    "muted": "#64748B",
    "success": "#15803D",
    "warning": "#B45309",
    "risk": "#B91C1C",
    "info": "#2563EB",
}


def inject_global_styles() -> None:
    """Install the V2.1 token layer without altering business behaviour."""
    st.markdown(
        """
        <style>
        :root {
            --la-primary:#2563EB;
            --la-primary-strong:#1D4ED8;
            --la-canvas:#F8FAFC;
            --la-surface:#FFFFFF;
            --la-info-bg:#EFF6FF;
            --la-border:#E2E8F0;
            --la-ink:#0F172A;
            --la-text:#475569;
            --la-muted:#64748B;
            --la-success:#15803D;
            --la-warning:#B45309;
            --la-risk:#B91C1C;
            --la-info:#2563EB;
            --la-space-1:.25rem;
            --la-space-2:.5rem;
            --la-space-3:.75rem;
            --la-space-4:1rem;
            --la-space-5:1.5rem;
            --la-space-6:2rem;
            --la-space-7:3rem;
            --la-space-8:4rem;
            --la-radius-sm:.5rem;
            --la-radius-md:.75rem;
            --la-radius-lg:1rem;
            --la-radius-card:.875rem;
            --la-shadow-sm:0 2px 8px rgba(15,23,42,.05);
            --la-shadow-md:0 12px 28px rgba(15,23,42,.08);
        }

        .stApp {
            overflow-x:clip;
            background:var(--la-canvas);
            color:var(--la-ink);
        }

        header[data-testid="stHeader"] { display:none; }

        [data-testid="stMainBlockContainer"] {
            width:min(100%, 72rem);
            min-width:0;
            padding:var(--la-space-6) var(--la-space-5) var(--la-space-8);
        }

        [data-testid="stMainBlockContainer"] > * { min-width:0; }

        [data-testid="stButton"] > button:focus-visible,
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stTextArea"] textarea:focus-visible {
            outline:3px solid rgba(37,99,235,.22);
            outline-offset:2px;
        }

        .la-global-header,
        .la-summary-card,
        .la-notice,
        .la-empty-state,
        .la-loading-state { min-width:0; }

        .la-global-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:var(--la-space-4);
            margin:0 0 var(--la-space-7);
        }

        .la-brand {
            display:flex;
            align-items:center;
            min-width:0;
            gap:var(--la-space-3);
        }

        .la-brand-mark {
            display:grid;
            flex:0 0 2.5rem;
            width:2.5rem;
            height:2.5rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:var(--la-ink);
            box-shadow:var(--la-shadow-sm);
            color:#fff;
            font-family:Georgia,serif;
            font-size:.92rem;
            letter-spacing:-.04em;
        }

        .la-brand-copy { min-width:0; }
        .la-brand-name {
            color:var(--la-ink);
            font-size:1rem;
            font-weight:760;
            letter-spacing:-.02em;
            line-height:1.25;
        }
        .la-brand-subtitle {
            margin-top:.125rem;
            color:var(--la-muted);
            font-size:.72rem;
            font-weight:560;
            line-height:1.35;
        }

        .la-header-meta {
            display:flex;
            flex-wrap:wrap;
            justify-content:flex-end;
            gap:var(--la-space-2);
        }

        .la-header-meta span,
        .la-status-badge {
            display:inline-flex;
            align-items:center;
            min-height:1.85rem;
            padding:.25rem .55rem;
            border:1px solid var(--la-border);
            border-radius:999px;
            background:var(--la-surface);
            color:var(--la-muted);
            font-size:.68rem;
            font-weight:680;
            line-height:1.2;
            white-space:nowrap;
        }

        .la-status-badge--success { border-color:#bbdfc8; background:#f0fdf4; color:var(--la-success); }
        .la-status-badge--info { border-color:#bfdbfe; background:var(--la-info-bg); color:var(--la-info); }
        .la-status-badge--warning { border-color:#fed7aa; background:#fff7ed; color:var(--la-warning); }
        .la-status-badge--risk { border-color:#fecaca; background:#fef2f2; color:var(--la-risk); }

        .la-section-header {
            display:flex;
            align-items:baseline;
            gap:var(--la-space-2);
            margin:var(--la-space-6) 0 var(--la-space-3);
        }
        .la-section-header__line {
            width:.1875rem;
            height:1rem;
            border-radius:999px;
            background:var(--la-primary);
        }
        .la-section-header__title {
            color:var(--la-ink);
            font-size:.9rem;
            font-weight:760;
        }
        .la-section-header__subtitle {
            color:var(--la-muted);
            font-size:.68rem;
            font-weight:620;
            letter-spacing:.06em;
        }

        .la-summary-card {
            margin:var(--la-space-3) 0;
            padding:var(--la-space-4);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
        }
        .la-summary-card__title {
            margin:0 0 var(--la-space-1);
            color:var(--la-ink);
            font-size:.9rem;
            font-weight:740;
        }
        .la-summary-card__body { color:var(--la-text); font-size:.84rem; line-height:1.6; }

        .la-analysis-summary {
            margin:var(--la-space-2) 0 var(--la-space-6);
            padding:var(--la-space-5);
            border:1px solid #bfdbfe;
            border-radius:var(--la-radius-card);
            background:linear-gradient(135deg,#fff 0%,var(--la-info-bg) 100%);
            box-shadow:var(--la-shadow-sm);
        }
        .la-analysis-summary__topline {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:var(--la-space-3);
        }
        .la-analysis-summary__eyebrow {
            color:var(--la-primary);
            font-size:.68rem;
            font-weight:760;
            letter-spacing:.09em;
        }
        .la-analysis-summary__title {
            margin:var(--la-space-4) 0 var(--la-space-2);
            color:var(--la-ink);
            font-size:1.08rem;
            font-weight:780;
            letter-spacing:-.018em;
        }
        .la-analysis-summary p {
            margin:0;
            color:var(--la-ink);
            font-size:1rem;
            font-weight:590;
            line-height:1.65;
        }
        .la-analysis-summary__intent {
            display:flex;
            gap:var(--la-space-2);
            margin-top:var(--la-space-4);
            padding-top:var(--la-space-3);
            border-top:1px solid rgba(37,99,235,.16);
            color:var(--la-text);
            font-size:.8rem;
            line-height:1.55;
        }
        .la-analysis-summary__intent strong { flex:0 0 auto; color:var(--la-ink); }

        .la-analysis-actions { display:grid; gap:var(--la-space-3); }
        .la-analysis-item {
            display:grid;
            grid-template-columns:2.35rem minmax(0,1fr);
            gap:var(--la-space-3);
            padding:var(--la-space-4);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
        }
        .la-analysis-item--question {
            border-color:#bfdbfe;
            box-shadow:var(--la-shadow-sm);
        }
        .la-analysis-item__index {
            display:grid;
            width:2.35rem;
            height:2.35rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:#f1f5f9;
            color:var(--la-muted);
            font-size:.72rem;
            font-weight:780;
            letter-spacing:.04em;
        }
        .la-analysis-item--question .la-analysis-item__index {
            background:var(--la-info-bg);
            color:var(--la-primary);
        }
        .la-analysis-item__content { min-width:0; }
        .la-analysis-item__content > p {
            margin:0;
            color:var(--la-ink);
            font-size:.9rem;
            font-weight:690;
            line-height:1.55;
        }
        .la-analysis-item__context {
            margin-top:var(--la-space-2);
            color:var(--la-text);
            font-size:.76rem;
            line-height:1.5;
        }
        .la-analysis-item__meta {
            display:flex;
            flex-wrap:wrap;
            gap:var(--la-space-2);
            margin-top:var(--la-space-3);
        }
        .la-analysis-item__deadline,
        .la-analysis-item__flag {
            display:inline-flex;
            align-items:center;
            min-height:1.55rem;
            padding:.2rem .45rem;
            border-radius:999px;
            background:#f8fafc;
            color:var(--la-muted);
            font-size:.67rem;
            font-weight:680;
            line-height:1.2;
        }
        .la-analysis-item__deadline { border:1px solid var(--la-border); }
        .la-analysis-item__flag { background:var(--la-info-bg); color:var(--la-primary); }

        .la-analysis-date-grid {
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));
            gap:var(--la-space-3);
        }
        .la-analysis-date-card {
            display:flex;
            flex-direction:column;
            gap:var(--la-space-1);
            min-height:6.5rem;
            padding:var(--la-space-4);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
        }
        .la-analysis-date-card strong {
            color:var(--la-primary);
            font-size:1rem;
            font-weight:780;
            letter-spacing:-.02em;
            line-height:1.3;
        }
        .la-analysis-date-card span { color:var(--la-text); font-size:.76rem; line-height:1.48; }
        .la-analysis-date-card em { margin-top:auto; color:var(--la-warning); font-size:.66rem; font-style:normal; font-weight:700; }

        .la-analysis-notice {
            display:grid;
            gap:var(--la-space-1);
            margin:var(--la-space-3) 0;
            padding:var(--la-space-3) var(--la-space-4);
            border-left:3px solid var(--la-info);
            border-radius:0 var(--la-radius-md) var(--la-radius-md) 0;
            background:#f8fafc;
        }
        .la-analysis-notice strong { color:var(--la-ink); font-size:.8rem; }
        .la-analysis-notice span { color:var(--la-text); font-size:.76rem; line-height:1.55; }
        .la-analysis-notice--warning { border-left-color:var(--la-warning); background:#fffaf0; }
        .la-analysis-notice--risk { border-left-color:var(--la-risk); background:#fff7f7; }

        .la-strategy-list {
            display:grid;
            gap:var(--la-space-2);
            margin:0;
            padding-left:1.35rem;
            color:var(--la-text);
            font-size:.8rem;
            line-height:1.55;
        }
        .la-strategy-list li::marker { color:var(--la-primary); font-weight:760; }
        .la-strategy-list--more { margin:var(--la-space-2) 0; }

        .la-notice {
            display:flex;
            align-items:flex-start;
            gap:var(--la-space-3);
            margin:var(--la-space-5) 0 0;
            padding:var(--la-space-4);
            border:1px solid #bfdbfe;
            border-radius:var(--la-radius-card);
            background:var(--la-info-bg);
            color:var(--la-text);
            font-size:.82rem;
            line-height:1.6;
        }
        .la-notice strong { color:var(--la-ink); }
        .la-notice__icon {
            display:grid;
            flex:0 0 1.25rem;
            width:1.25rem;
            height:1.25rem;
            place-items:center;
            border-radius:999px;
            background:var(--la-primary);
            color:#fff;
            font-size:.72rem;
            font-weight:760;
            line-height:1;
        }

        .la-empty-state,
        .la-loading-state {
            margin:var(--la-space-5) 0;
            padding:var(--la-space-6) var(--la-space-5);
            border:1px dashed #cbd5e1;
            border-radius:var(--la-radius-card);
            background:rgba(255,255,255,.7);
            color:var(--la-text);
            text-align:center;
        }
        .la-empty-state strong,
        .la-loading-state strong { display:block; margin-bottom:var(--la-space-2); color:var(--la-ink); }
        .la-empty-state span,
        .la-loading-state span { color:var(--la-muted); font-size:.8rem; line-height:1.55; }
        .la-empty-state__icon,
        .la-loading-state__icon {
            display:grid;
            width:2rem;
            height:2rem;
            margin:0 auto var(--la-space-3);
            place-items:center;
            border-radius:999px;
            background:var(--la-info-bg);
            color:var(--la-primary);
            font-size:1rem;
            font-weight:780;
            letter-spacing:.08em;
        }

        .la-action-bar {
            display:flex;
            flex-wrap:wrap;
            gap:var(--la-space-3);
            margin-top:var(--la-space-5);
        }
        [class*="st-key-action_bar__"] {
            margin-top:var(--la-space-5);
        }
        [class*="st-key-action_bar__"] [data-testid="stHorizontalBlock"] {
            gap:var(--la-space-3);
        }
        [class*="st-key-tertiary_action__"] { margin-top:var(--la-space-3); }
        [class*="st-key-tertiary_action__"] [data-testid="stButton"] > button {
            min-height:2.75rem;
            padding:var(--la-space-2) 0;
            border-color:transparent;
            background:transparent;
            box-shadow:none;
            color:var(--la-muted);
            font-size:.76rem;
        }
        [class*="st-key-tertiary_action__"] [data-testid="stButton"] > button:hover {
            border-color:transparent;
            background:transparent;
            color:var(--la-primary);
        }

        .la-workspace-header {
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:var(--la-space-4);
            margin:var(--la-space-3) 0 var(--la-space-5);
            padding:var(--la-space-5);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
        }
        .la-workspace-header__lead {
            display:flex;
            min-width:0;
            gap:var(--la-space-4);
        }
        .la-workspace-header__lead > div { min-width:0; }
        .la-workspace-header__icon {
            display:grid;
            flex:0 0 2.75rem;
            width:2.75rem;
            height:2.75rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:var(--la-info-bg);
            color:var(--la-primary);
        }
        .la-workspace-header__icon svg { width:1.35rem; height:1.35rem; }
        .la-workspace-header__eyebrow {
            margin-bottom:var(--la-space-1);
            color:var(--la-primary);
            font-size:.69rem;
            font-weight:760;
            letter-spacing:.1em;
            text-transform:uppercase;
        }
        .la-workspace-header h1 {
            margin:0;
            color:var(--la-ink);
            font-size:clamp(1.5rem,3.5vw,2.2rem);
            font-weight:780;
            letter-spacing:-.035em;
            line-height:1.18;
        }
        .la-workspace-header p {
            max-width:42rem;
            margin:var(--la-space-2) 0 0;
            color:var(--la-text);
            font-size:.9rem;
            line-height:1.6;
        }
        .la-workspace-header__step {
            display:inline-flex;
            flex:0 0 auto;
            align-items:center;
            min-height:2rem;
            padding:.3rem .65rem;
            border:1px solid #bfdbfe;
            border-radius:999px;
            background:var(--la-info-bg);
            color:var(--la-primary);
            font-size:.7rem;
            font-weight:720;
            white-space:nowrap;
        }

        [class*="st-key-workspace__"][class*="body_layout"] {
            width:100%;
            min-width:0;
        }
        [class*="st-key-workspace__"][class*="body_layout"] [data-testid="stHorizontalBlock"] {
            width:100%;
            min-width:0;
            align-items:flex-start;
        }
        [class*="st-key-workspace__"][class*="body_layout"] [data-testid="stColumn"] {
            min-width:0;
        }
        .la-workflow-nav {
            position:sticky;
            top:var(--la-space-4);
            padding:var(--la-space-3);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:rgba(255,255,255,.76);
        }
        .la-workflow-nav ol {
            display:grid;
            gap:var(--la-space-1);
            margin:0;
            padding:0;
            list-style:none;
        }
        .la-workflow-nav__item {
            display:grid;
            grid-template-columns:1.25rem minmax(0,1fr);
            gap:var(--la-space-2);
            align-items:start;
            padding:var(--la-space-3);
            border-radius:var(--la-radius-md);
            color:var(--la-muted);
        }
        .la-workflow-nav__item strong {
            display:block;
            color:inherit;
            font-size:.82rem;
            font-weight:720;
            line-height:1.35;
        }
        .la-workflow-nav__item small {
            display:block;
            margin-top:.1rem;
            color:inherit;
            font-size:.68rem;
            line-height:1.4;
        }
        .la-workflow-nav__marker {
            display:grid;
            width:1rem;
            height:1rem;
            margin-top:.08rem;
            place-items:center;
            border:1px solid #cbd5e1;
            border-radius:999px;
            background:var(--la-surface);
        }
        .la-workflow-nav__item--complete .la-workflow-nav__marker {
            border-color:var(--la-success);
            background:var(--la-success);
        }
        .la-workflow-nav__item--complete .la-workflow-nav__marker::after {
            color:#fff;
            content:"✓";
            font-size:.62rem;
            font-weight:760;
        }
        .la-workflow-nav__item--current {
            background:var(--la-info-bg);
            color:var(--la-primary);
        }
        .la-workflow-nav__item--current .la-workflow-nav__marker {
            border:4px solid var(--la-primary);
            background:#fff;
        }
        .la-workflow-nav__item--upcoming { color:#94a3b8; }

        .la-workspace-empty-state {
            display:grid;
            min-height:20rem;
            place-content:center;
            justify-items:center;
            gap:var(--la-space-3);
            padding:var(--la-space-6);
            border:1px dashed #cbd5e1;
            border-radius:var(--la-radius-card);
            background:rgba(255,255,255,.66);
            color:var(--la-text);
            text-align:center;
        }
        .la-workspace-empty-state strong { color:var(--la-ink); font-size:1rem; }
        .la-workspace-empty-state span { max-width:26rem; color:var(--la-muted); font-size:.84rem; line-height:1.6; }

        .la-explore-card,
        [class*="st-key-explore__open__"] > button {
            display:grid;
            grid-template-columns:minmax(0,1fr) auto;
            align-items:start;
            gap:var(--la-space-3);
            min-height:7.5rem;
            margin:var(--la-space-3) 0;
            padding:var(--la-space-4);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
            color:var(--la-ink);
            text-align:left;
        }
        [class*="st-key-explore__open__"] > button > div { min-width:0; }
        [class*="st-key-explore__open__"] > button [data-testid="stMarkdownContainer"] p {
            margin:0;
            color:var(--la-text);
            font-size:.82rem;
            line-height:1.55;
            text-align:left;
        }
        [class*="st-key-explore__open__"] > button [data-testid="stMarkdownContainer"] strong {
            display:block;
            margin-bottom:var(--la-space-2);
            color:var(--la-ink);
            font-size:.96rem;
        }
        [class*="st-key-explore__open__"] [data-testid="stIconMaterial"] {
            display:grid;
            width:2.75rem;
            height:2.75rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:var(--la-info-bg);
            color:var(--la-primary);
            font-size:0;
        }
        [class*="st-key-explore__open__"] [data-testid="stIconMaterial"] {
            font-size:1.25rem;
        }
        .la-explore-card strong { display:block; color:var(--la-ink); font-size:.96rem; }
        .la-explore-card small { display:block; margin-top:.15rem; color:var(--la-muted); font-size:.68rem; }
        .la-explore-card p { margin:var(--la-space-2) 0 0; color:var(--la-text); font-size:.8rem; line-height:1.55; }
        .la-explore-card__status {
            align-self:start;
            padding:.25rem .55rem;
            border:1px solid var(--la-border);
            border-radius:999px;
            background:#f8fafc;
            color:var(--la-muted);
            font-size:.66rem;
            font-weight:680;
            white-space:nowrap;
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                width:100%;
                padding:var(--la-space-5) var(--la-space-4) var(--la-space-7);
            }
            .la-global-header { align-items:flex-start; margin-bottom:var(--la-space-6); }
            .la-header-meta { justify-content:flex-start; }
            .la-workspace-header { padding:var(--la-space-4); }
            .la-workflow-nav { position:static; }
            [class*="st-key-workspace__"][class*="body_layout"] [data-testid="stHorizontalBlock"] {
                flex-direction:column;
                gap:var(--la-space-4);
            }
            [class*="st-key-workspace__"][class*="body_layout"] [data-testid="stColumn"] {
                width:100%;
                min-width:0;
                flex:1 1 100%;
            }
            .la-workflow-nav ol {
                grid-template-columns:repeat(auto-fit,minmax(8.5rem,1fr));
            }
        }

        @media (max-width: 480px) {
            [data-testid="stMainBlockContainer"] {
                padding:var(--la-space-4) var(--la-space-3) var(--la-space-6);
            }
            .la-global-header { flex-direction:column; gap:var(--la-space-3); }
            .la-header-meta { width:100%; justify-content:flex-start; }
            .la-brand-subtitle { max-width:16rem; overflow-wrap:anywhere; }
            .la-notice { padding:var(--la-space-3); }
            .la-workspace-header { flex-direction:column; gap:var(--la-space-3); }
            .la-workspace-header__lead { gap:var(--la-space-3); }
            .la-workspace-header__icon { flex-basis:2.4rem; width:2.4rem; height:2.4rem; }
            .la-workspace-header__step { white-space:normal; }
            .la-analysis-summary { padding:var(--la-space-4); }
            .la-analysis-summary__topline { align-items:flex-start; flex-direction:column; }
            .la-analysis-summary p { font-size:.92rem; }
            .la-analysis-summary__intent { flex-direction:column; gap:var(--la-space-1); }
            .la-analysis-date-grid { grid-template-columns:1fr; }
            .la-workflow-nav { display:none; }
            .la-workspace-empty-state { min-height:15rem; padding:var(--la-space-5) var(--la-space-4); }
            .la-explore-card,
            [class*="st-key-explore__open__"] > button {
                grid-template-columns:minmax(0,1fr);
                min-height:6.5rem;
            }
            .la-explore-card__status { justify-self:start; }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { scroll-behavior:auto !important; transition:none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_workspace_home_styles() -> None:
    """Install the home-only layout rules on top of the global token layer."""
    st.markdown(
        """
        <style>
        .st-key-home__workspace {
            min-width:0;
            overflow-x:clip;
        }

        .st-key-home__workspace .la-home-hero {
            max-width:48rem;
            margin-bottom:var(--la-space-6);
        }
        .st-key-home__workspace .la-home-kicker {
            margin-bottom:var(--la-space-3);
            color:var(--la-primary);
            font-size:.7rem;
            font-weight:760;
            letter-spacing:.12em;
            text-transform:uppercase;
        }
        .st-key-home__workspace .la-home-title {
            max-width:42rem;
            margin:0;
            color:var(--la-ink);
            font-size:clamp(2rem,4.6vw,3.15rem);
            font-weight:790;
            letter-spacing:-.045em;
            line-height:1.1;
            overflow-wrap:anywhere;
        }
        .st-key-home__workspace .la-home-copy {
            max-width:38rem;
            margin:var(--la-space-3) 0 0;
            color:var(--la-text);
            font-size:1rem;
            line-height:1.65;
        }
        .st-key-home__workspace .la-home-copy-en {
            display:block;
            margin-top:var(--la-space-1);
            color:var(--la-muted);
            font-size:.78rem;
        }

        .st-key-home__workspace [class*="st-key-home__action__"] {
            min-width:0;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button {
            display:flex;
            align-items:center;
            width:100%;
            min-height:8.25rem;
            padding:var(--la-space-5) var(--la-space-5);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
            color:var(--la-ink);
            text-align:left;
            transition:border-color .16s ease, box-shadow .16s ease, transform .16s ease;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button > div {
            width:100%;
            min-width:0;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button > div > span {
            display:grid;
            grid-template-columns:3.25rem minmax(0,1fr) 2.5rem;
            align-items:center;
            column-gap:var(--la-space-4);
            width:100%;
            min-width:0;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button > div > span::after {
            display:grid;
            width:2.35rem;
            height:2.35rem;
            place-items:center;
            justify-self:end;
            border-radius:999px;
            background:var(--la-info-bg);
            color:var(--la-primary);
            content:"→";
            font-size:1.1rem;
            font-weight:700;
            line-height:1;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button > div > span > span:first-child {
            display:grid;
            width:3.25rem;
            height:3.25rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:var(--la-info-bg);
            color:var(--la-primary);
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button [data-testid="stIconMaterial"] {
            width:auto;
            height:auto;
            margin:0;
            color:inherit;
            font-size:1.4rem;
            line-height:1;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button [data-testid="stMarkdownContainer"] {
            width:100%;
            min-width:0;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button p {
            width:100%;
            margin:0;
            color:var(--la-text);
            font-size:.84rem;
            line-height:1.55;
            text-align:left;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button p strong {
            display:block;
            margin-bottom:var(--la-space-2);
            color:var(--la-ink);
            font-size:1rem;
            font-weight:760;
            line-height:1.35;
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button p br { display:none; }
        .st-key-home__workspace [class*="st-key-home__action__"] button:hover {
            border-color:#a9c2ee;
            box-shadow:var(--la-shadow-md);
            transform:translateY(-1px);
        }
        .st-key-home__workspace [class*="st-key-home__action__"] button:active {
            box-shadow:var(--la-shadow-sm);
            transform:translateY(0);
        }

        .st-key-home__workspace .st-key-home__action__reply button {
            min-height:9rem;
            border-color:var(--la-primary);
            background:var(--la-primary);
            box-shadow:0 16px 30px rgba(37,99,235,.18);
            color:#fff;
        }
        .st-key-home__workspace .st-key-home__action__reply button p,
        .st-key-home__workspace .st-key-home__action__reply button p strong { color:#fff; }
        .st-key-home__workspace .st-key-home__action__reply button p { color:rgba(255,255,255,.9); }
        .st-key-home__workspace .st-key-home__action__reply button > div > span > span:first-child,
        .st-key-home__workspace .st-key-home__action__reply button > div > span::after {
            background:rgba(255,255,255,.16);
            color:#fff;
        }
        .st-key-home__workspace .st-key-home__action__reply button:hover {
            border-color:var(--la-primary-strong);
            background:var(--la-primary-strong);
        }

        .st-key-home__workspace [data-testid="stHorizontalBlock"] { gap:var(--la-space-3); }

        .st-key-home__workspace .la-home-status {
            display:flex;
            flex-wrap:wrap;
            gap:var(--la-space-2) var(--la-space-4);
            margin:var(--la-space-3) 0 0;
            color:var(--la-muted);
            font-size:.72rem;
            line-height:1.5;
        }
        .st-key-home__explore_more > button {
            min-height:3rem;
            margin-top:var(--la-space-3);
            border-style:dashed;
            border-color:#cbd5e1;
            border-radius:var(--la-radius-md);
            background:transparent;
            color:var(--la-text);
            font-size:.82rem;
            font-weight:680;
        }
        .st-key-home__explore_more > button:hover {
            border-color:#a9c2ee;
            background:var(--la-info-bg);
            color:var(--la-primary);
        }

        @media (max-width: 768px) {
            .st-key-home__workspace .la-home-title { font-size:clamp(1.9rem,7vw,2.55rem); }
            .st-key-home__workspace [data-testid="stHorizontalBlock"] {
                flex-wrap:wrap;
            }
        }

        @media (max-width: 640px) {
            .st-key-home__workspace [data-testid="stHorizontalBlock"] {
                flex-direction:column;
                gap:var(--la-space-3);
            }
            .st-key-home__workspace [data-testid="column"] {
                width:100%;
                min-width:0;
                flex:1 1 100%;
            }
            .st-key-home__workspace [class*="st-key-home__action__"] button {
                min-height:6.5rem;
                padding:var(--la-space-4);
            }
            .st-key-home__workspace [class*="st-key-home__action__"] button > div > span {
                grid-template-columns:2.75rem minmax(0,1fr) 2.25rem;
                column-gap:var(--la-space-3);
            }
            .st-key-home__workspace [class*="st-key-home__action__"] button > div > span > span:first-child {
                width:2.75rem;
                height:2.75rem;
            }
            .st-key-home__workspace [class*="st-key-home__action__"] button > div > span::after {
                width:2.15rem;
                height:2.15rem;
            }
            .st-key-home__workspace .st-key-home__action__reply button { min-height:7rem; }
        .st-key-home__workspace .la-home-copy { font-size:.92rem; }
        }

        /* Create Email workspace: scenario, guided facts, review and result. */
        .st-key-workspace__create .la-guided-question__progress {
            margin:0 0 var(--la-space-3); color:var(--la-primary); font-size:.7rem;
            font-weight:760; letter-spacing:.09em; text-transform:uppercase;
        }
        .st-key-workspace__create .la-guided-question__title {
            margin:0; color:var(--la-ink); font-size:clamp(1.35rem,3vw,1.75rem);
            letter-spacing:-.03em; line-height:1.25;
        }
        .st-key-workspace__create .la-guided-question__helper {
            margin:var(--la-space-2) 0 var(--la-space-5); color:var(--la-muted);
            font-size:.86rem; line-height:1.6;
        }
        .st-key-workspace__create [class*="st-key-compose__task__"] > button,
        .st-key-workspace__create [class*="st-key-compose__coming_soon__"] > button {
            min-height:7.5rem; margin-bottom:var(--la-space-3); padding:var(--la-space-4);
            border:1px solid var(--la-border); border-radius:var(--la-radius-card);
            background:var(--la-surface); color:var(--la-ink); box-shadow:var(--la-shadow-sm);
            text-align:left; white-space:pre-line;
        }
        .st-key-workspace__create [class*="st-key-compose__task__"] > button:hover {
            border-color:#93c5fd; background:var(--la-info-bg); box-shadow:var(--la-shadow-md);
        }
        .st-key-workspace__create [class*="st-key-compose__task__"] button p,
        .st-key-workspace__create [class*="st-key-compose__coming_soon__"] button p {
            text-align:left; line-height:1.55;
        }
        .st-key-workspace__create [class*="st-key-compose__question_card"] {
            margin:var(--la-space-3) 0; padding:var(--la-space-6); border:1px solid var(--la-border);
            border-radius:var(--la-radius-card); background:var(--la-surface); box-shadow:var(--la-shadow-sm);
        }
        .st-key-workspace__create [class*="st-key-compose__summary_card"] {
            margin:var(--la-space-3) 0; padding:var(--la-space-2) var(--la-space-5);
            border:1px solid var(--la-border); border-radius:var(--la-radius-card); background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
        }
        .st-key-workspace__create .la-review-item {
            padding:var(--la-space-3) 0; border-bottom:1px solid var(--la-border);
        }
        .st-key-workspace__create .la-review-item span {
            display:block; margin-bottom:var(--la-space-1); color:var(--la-muted); font-size:.72rem; font-weight:700;
        }
        .st-key-workspace__create .la-review-item strong {
            display:block; color:var(--la-ink); font-size:.88rem; font-weight:650; line-height:1.55;
        }
        .st-key-workspace__create .la-email-subject__label,
        .st-key-workspace__create .la-email-editor__label { margin-top:var(--la-space-5); }
        .st-key-workspace__create .la-create-status {
            margin:var(--la-space-3) 0; color:var(--la-muted); font-size:.75rem; line-height:1.55;
        }
        @media (max-width:768px) {
            .st-key-workspace__create [class*="st-key-compose__question_card"] { padding:var(--la-space-4); }
            .st-key-workspace__create [class*="st-key-compose__task__"] > button { min-height:6.4rem; }
        }

        /* Improve Draft workspace: source, focused choices and result comparison. */
        .st-key-workspace__improve [class*="st-key-improve__draft_canvas"] {
            padding:var(--la-space-5); border:1px solid var(--la-border);
            border-radius:var(--la-radius-card); background:var(--la-surface); box-shadow:var(--la-shadow-sm);
        }
        .st-key-workspace__improve [class*="st-key-improve__draft_canvas"] textarea { min-height:20rem; }
        .st-key-workspace__improve [class*="st-key-improve__tone__"] > button {
            min-height:5.6rem; margin-bottom:var(--la-space-2); padding:var(--la-space-3) var(--la-space-4);
            border:1px solid var(--la-border); border-radius:var(--la-radius-md); background:var(--la-surface);
            color:var(--la-ink); text-align:left; white-space:pre-line;
        }
        .st-key-workspace__improve [class*="st-key-improve__tone__"] > button:hover {
            border-color:#93c5fd; background:var(--la-info-bg);
        }
        .st-key-workspace__improve [class*="st-key-improve__tone__"] > button p { text-align:left; line-height:1.55; }
        .st-key-workspace__improve [class*="st-key-improve__before_panel"],
        .st-key-workspace__improve [class*="st-key-improve__after_panel"] {
            min-width:0; padding:var(--la-space-4); border:1px solid var(--la-border);
            border-radius:var(--la-radius-card); background:var(--la-surface); box-shadow:var(--la-shadow-sm);
        }
        .st-key-workspace__improve [class*="st-key-improve__before_panel"] textarea { background:#f8fafc; color:var(--la-text); }
        .la-optimization-summary { display:grid; gap:var(--la-space-2); margin:var(--la-space-3) 0 0; padding:0; list-style:none; }
        .la-optimization-summary li { position:relative; padding-left:1.2rem; color:var(--la-text); font-size:.83rem; line-height:1.55; }
        .la-optimization-summary li::before { position:absolute; left:0; color:var(--la-success); content:"✓"; font-weight:760; }
        @media (max-width:768px) {
            .st-key-workspace__improve [class*="st-key-improve__draft_canvas"] { padding:var(--la-space-4); }
            .st-key-workspace__improve [class*="st-key-improve__before_panel"],
            .st-key-workspace__improve [class*="st-key-improve__after_panel"] { padding:var(--la-space-3); }
        }

        /* Reply decision, generation and send-ready workspace surfaces. */
        .st-key-workspace__reply .la-decision-focus {
            margin:var(--la-space-3) 0 var(--la-space-5);
            padding:var(--la-space-5);
            border:1px solid #bfdbfe;
            border-radius:var(--la-radius-card);
            background:linear-gradient(135deg,#fff 0%,var(--la-info-bg) 100%);
            box-shadow:var(--la-shadow-sm);
        }
        .st-key-workspace__reply .la-decision-focus__step,
        .st-key-workspace__reply .la-decision-focus__label,
        .st-key-workspace__reply .la-coverage-summary__label,
        .st-key-workspace__reply .la-completion-panel__eyebrow {
            color:var(--la-primary);
            font-size:.68rem;
            font-weight:760;
            letter-spacing:.09em;
            text-transform:uppercase;
        }
        .st-key-workspace__reply .la-decision-focus__label { margin-top:var(--la-space-3); }
        .st-key-workspace__reply .la-decision-focus h2 {
            margin:var(--la-space-2) 0;
            color:var(--la-ink);
            font-size:clamp(1.15rem,2vw,1.45rem);
            letter-spacing:-.025em;
            line-height:1.35;
        }
        .st-key-workspace__reply .la-decision-focus__meta {
            color:var(--la-text);
            font-size:.78rem;
            line-height:1.5;
        }
        .st-key-workspace__reply [class*="st-key-reply__decision_option__"] > button {
            min-height:4.45rem;
            margin:0 0 var(--la-space-2);
            padding:var(--la-space-3) var(--la-space-4);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-md);
            background:var(--la-surface);
            color:var(--la-ink);
            text-align:left;
            white-space:pre-line;
        }
        .st-key-workspace__reply [class*="st-key-reply__decision_option__"] > button:hover {
            border-color:#93c5fd;
            background:var(--la-info-bg);
        }
        .st-key-workspace__reply [class*="st-key-reply__decision_option__"] > button[kind="primary"] {
            border-color:var(--la-primary);
            background:var(--la-primary);
            color:#fff;
        }
        .la-decision-summary-cards,
        .la-coverage-items,
        .la-preflight-items { display:grid; gap:var(--la-space-3); margin:var(--la-space-3) 0; }
        .la-decision-summary-card,
        .la-coverage-item,
        .la-preflight-item {
            display:grid;
            grid-template-columns:auto minmax(0,1fr);
            gap:var(--la-space-3);
            padding:var(--la-space-4);
            border:1px solid var(--la-border);
            border-left-width:.25rem;
            border-radius:var(--la-radius-md);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
        }
        .la-decision-summary-card--success,.la-coverage-item--success,.la-preflight-item--success { border-left-color:var(--la-success); }
        .la-decision-summary-card--info,.la-coverage-item--info { border-left-color:var(--la-info); }
        .la-decision-summary-card--warning,.la-coverage-item--warning,.la-preflight-item--warning { border-left-color:var(--la-warning); }
        .la-decision-summary-card--risk,.la-coverage-item--risk,.la-preflight-item--risk { border-left-color:var(--la-risk); }
        .la-decision-summary-card__number {
            display:grid;width:2rem;height:2rem;place-items:center;border-radius:999px;
            background:var(--la-info-bg);color:var(--la-primary);font-size:.72rem;font-weight:760;
        }
        .la-decision-summary-card strong,.la-coverage-item strong,.la-preflight-item strong { display:block;color:var(--la-ink);font-size:.88rem;line-height:1.45; }
        .la-decision-summary-card em,.la-coverage-item em { display:block;margin-top:var(--la-space-1);color:var(--la-text);font-size:.74rem;font-style:normal;font-weight:690; }
        .la-decision-summary-card p,.la-coverage-item p,.la-preflight-item p { margin:var(--la-space-2) 0 0;color:var(--la-text);font-size:.8rem;line-height:1.55; }
        .la-preflight-item { display:block; }
        .la-preflight-item small { display:block;margin-top:var(--la-space-2);color:var(--la-muted);font-size:.75rem;line-height:1.5; }
        .la-email-subject__label,.la-email-editor__label { margin:var(--la-space-3) 0 var(--la-space-2);color:var(--la-muted);font-size:.7rem;font-weight:760;letter-spacing:.08em;text-transform:uppercase; }
        .la-coverage-summary {
            display:flex;flex-wrap:wrap;align-items:baseline;gap:var(--la-space-2) var(--la-space-3);
            margin:var(--la-space-3) 0;padding:var(--la-space-4);border:1px solid #bfdbfe;
            border-radius:var(--la-radius-md);background:var(--la-info-bg);
        }
        .la-coverage-summary strong { color:var(--la-ink);font-size:.96rem; }
        .la-coverage-summary span { color:var(--la-text);font-size:.76rem; }
        .la-preflight-summary { margin:var(--la-space-3) 0;padding:var(--la-space-5);border:1px solid var(--la-border);border-radius:var(--la-radius-card);background:var(--la-surface);box-shadow:var(--la-shadow-sm); }
        .la-preflight-summary p { margin:var(--la-space-3) 0 0;color:var(--la-ink);font-size:.95rem;line-height:1.65; }
        .la-preflight-summary--warning { border-color:#fed7aa;background:#fffaf2; }
        .la-preflight-summary--risk { border-color:#fecaca;background:#fff7f7; }
        .la-completion-panel { margin:var(--la-space-6) 0 var(--la-space-3);padding:var(--la-space-6);border:1px solid #bbdfc8;border-radius:var(--la-radius-card);background:linear-gradient(135deg,#fff 0%,#f0fdf4 100%);box-shadow:var(--la-shadow-sm); }
        .la-completion-panel h2 { margin:var(--la-space-2) 0;color:var(--la-ink);font-size:1.3rem;letter-spacing:-.025em; }
        .la-completion-panel p { margin:0;color:var(--la-text);font-size:.86rem;line-height:1.65; }

        @media (max-width: 640px) {
            .st-key-workspace__reply .la-decision-focus,
            .la-preflight-summary,
            .la-completion-panel { padding:var(--la-space-4); }
            .st-key-workspace__reply [class*="st-key-reply__decision_option__"] > button { min-height:4.65rem; }
            .la-coverage-summary { display:block; }
            .la-coverage-summary strong,.la-coverage-summary span { display:block;margin-top:var(--la-space-2); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
