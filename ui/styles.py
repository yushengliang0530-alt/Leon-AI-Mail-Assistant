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
        [data-testid="stTextArea"] textarea:focus {
            outline:3px solid rgba(37,99,235,.22);
            outline-offset:2px;
        }

        .la-page-header,
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

        .la-page-header {
            display:flex;
            align-items:flex-start;
            gap:var(--la-space-4);
            margin:0 0 var(--la-space-6);
            padding:var(--la-space-5);
            border:1px solid var(--la-border);
            border-radius:var(--la-radius-card);
            background:var(--la-surface);
            box-shadow:var(--la-shadow-sm);
        }
        .la-page-header__icon {
            display:grid;
            flex:0 0 2.75rem;
            width:2.75rem;
            height:2.75rem;
            place-items:center;
            border-radius:var(--la-radius-md);
            background:var(--la-info-bg);
            color:var(--la-primary);
        }
        .la-page-header__eyebrow,
        .la-section-header__eyebrow {
            margin:0 0 var(--la-space-1);
            color:var(--la-primary);
            font-size:.69rem;
            font-weight:760;
            letter-spacing:.1em;
            text-transform:uppercase;
        }
        .la-page-header h1 {
            margin:0;
            color:var(--la-ink);
            font-size:clamp(1.65rem,4vw,2.35rem);
            font-weight:780;
            letter-spacing:-.035em;
            line-height:1.18;
        }
        .la-page-header p {
            margin:var(--la-space-2) 0 0;
            color:var(--la-text);
            font-size:.92rem;
            line-height:1.65;
        }

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

        .la-action-bar {
            display:flex;
            flex-wrap:wrap;
            gap:var(--la-space-3);
            margin-top:var(--la-space-5);
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                width:100%;
                padding:var(--la-space-5) var(--la-space-4) var(--la-space-7);
            }
            .la-global-header { align-items:flex-start; margin-bottom:var(--la-space-6); }
            .la-header-meta { justify-content:flex-start; }
        }

        @media (max-width: 480px) {
            [data-testid="stMainBlockContainer"] {
                padding:var(--la-space-4) var(--la-space-3) var(--la-space-6);
            }
            .la-global-header { flex-direction:column; gap:var(--la-space-3); }
            .la-header-meta { width:100%; justify-content:flex-start; }
            .la-brand-subtitle { max-width:16rem; overflow-wrap:anywhere; }
            .la-page-header { padding:var(--la-space-4); gap:var(--la-space-3); }
            .la-page-header__icon { flex-basis:2.4rem; width:2.4rem; height:2.4rem; }
            .la-notice { padding:var(--la-space-3); }
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
        </style>
        """,
        unsafe_allow_html=True,
    )
