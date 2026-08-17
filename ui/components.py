"""Reusable Streamlit presentation components for the V2.1 workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import html

import streamlit as st


@dataclass(frozen=True)
class TaskCard:
    """A direct, stable-key task entry for the workspace home."""

    action: str
    title: str
    description: str
    icon: str
    action_label: str
    status: str | None = None
    primary: bool = False


@dataclass(frozen=True)
class WorkflowStep:
    """Display-only description of one workspace step."""

    key: str
    label: str
    helper: str
    state: str = "upcoming"


def render_global_header(
    *,
    version: str,
    service_status: str,
    show_guide: bool = True,
) -> None:
    guide = '<span>使用指南</span>' if show_guide else ""
    st.markdown(
        f"""
        <div class="la-global-header">
          <div class="la-brand">
            <span class="la-brand-mark" aria-hidden="true">LA</span>
            <div class="la-brand-copy">
              <div class="la-brand-name">Leon AI Copilot</div>
              <div class="la-brand-subtitle">Business Communication Copilot</div>
            </div>
          </div>
          <div class="la-header-meta" aria-label="工作台状态">
            {guide}
            <span>服务：{html.escape(service_status)}</span>
            <span>{html.escape(version)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    *,
    icon: str,
    title: str,
    description: str,
    eyebrow: str = "LEON AI · WORKSPACE",
) -> None:
    st.markdown(
        f"""
        <div class="la-page-header">
          <div class="la-page-header__icon" aria-hidden="true">{html.escape(icon)}</div>
          <div>
            <div class="la-page-header__eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(description)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workspace_header(
    *,
    title: str,
    description: str,
    eyebrow: str,
    step_label: str = "",
) -> None:
    """Render the neutral task header shared by future workspace migrations."""
    step_html = (
        f'<span class="la-workspace-header__step">{html.escape(step_label)}</span>'
        if step_label
        else ""
    )
    st.markdown(
        f"""
        <section class="la-workspace-header">
          <div>
            <div class="la-workspace-header__eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(description)}</p>
          </div>
          {step_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_nav(steps: tuple[WorkflowStep, ...]) -> None:
    """Render the display-only workflow rail without changing task state."""
    items = "".join(
        f"""
        <li class="la-workflow-nav__item la-workflow-nav__item--{html.escape(step.state)}">
          <span class="la-workflow-nav__marker" aria-hidden="true"></span>
          <span>
            <strong>{html.escape(step.label)}</strong>
            <small>{html.escape(step.helper)}</small>
          </span>
        </li>
        """
        for step in steps
    )
    st.markdown(
        f'<nav class="la-workflow-nav" aria-label="任务流程"><ol>{items}</ol></nav>',
        unsafe_allow_html=True,
    )


def render_workspace_shell(
    *,
    workspace_key: str,
    version: str,
    service_status: str,
    title: str,
    description: str,
    eyebrow: str,
    steps: tuple[WorkflowStep, ...],
    render_task: Callable[[], None],
    on_return_home: Callable[[], None],
) -> None:
    """Render a complete presentation shell around one supplied task canvas."""
    with st.container(key=f"workspace__{workspace_key}"):
        render_global_header(
            version=version,
            service_status=service_status,
            show_guide=False,
        )
        st.button(
            "← 返回工作台",
            key=f"workspace__{workspace_key}__return_home",
            type="secondary",
            on_click=on_return_home,
        )
        render_workspace_header(
            title=title,
            description=description,
            eyebrow=eyebrow,
            step_label=_current_step_label(steps),
        )
        navigation, canvas = st.columns((0.28, 0.72), gap="large")
        with navigation:
            render_workflow_nav(steps)
        with canvas:
            with st.container(key=f"workspace__{workspace_key}__task_area"):
                render_task()


def _current_step_label(steps: tuple[WorkflowStep, ...]) -> str:
    for index, step in enumerate(steps, start=1):
        if step.state == "current":
            return f"步骤 {index} / {len(steps)} · {step.label}"
    return f"{len(steps)} 个步骤"


def render_section_header(title: str, subtitle: str = "") -> None:
    subtitle_html = (
        f'<span class="la-section-header__subtitle">{html.escape(subtitle)}</span>'
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div class="la-section-header">
          <span class="la-section-header__line" aria-hidden="true"></span>
          <span class="la-section-header__title">{html.escape(title)}</span>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_task_card(
    *,
    card: TaskCard,
    on_click: Callable[[], None],
) -> bool:
    """Render one full-width click target using a stable task key."""
    title = card.title if not card.status else f"{card.title} · {card.status}"
    return st.button(
        f"**{title}**  \n{card.description}",
        key=f"home__action__{card.action}",
        type="primary" if card.primary else "secondary",
        icon=f":material/{card.icon}:",
        use_container_width=True,
        on_click=on_click,
    )


def render_status_badge(label: str, kind: str = "info") -> None:
    allowed = {"success", "info", "warning", "risk"}
    safe_kind = kind if kind in allowed else "info"
    st.markdown(
        f'<span class="la-status-badge la-status-badge--{safe_kind}">{html.escape(label)}</span>',
        unsafe_allow_html=True,
    )


def render_summary_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="la-summary-card">
          <div class="la-summary-card__title">{html.escape(title)}</div>
          <div class="la-summary-card__body">{html.escape(body)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_notice_bar(title: str, body: str, *, icon: str = "i") -> None:
    st.markdown(
        f"""
        <aside class="la-notice">
          <span class="la-notice__icon" aria-hidden="true">{html.escape(icon)}</span>
          <span><strong>{html.escape(title)}</strong>：{html.escape(body)}</span>
        </aside>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, helper: str) -> None:
    st.markdown(
        f"""
        <section class="la-empty-state">
          <strong>{html.escape(title)}</strong>
          <span>{html.escape(helper)}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_loading_state(title: str, helper: str) -> None:
    st.markdown(
        f"""
        <section class="la-loading-state" aria-live="polite">
          <strong>{html.escape(title)}</strong>
          <span>{html.escape(helper)}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_workspace_empty_state(title: str, helper: str) -> None:
    """Present an intentionally empty task canvas inside the workspace shell."""
    st.markdown(
        f"""
        <section class="la-workspace-empty-state">
          <strong>{html.escape(title)}</strong>
          <span>{html.escape(helper)}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_action_bar(
    *,
    primary_label: str,
    primary_key: str,
    on_primary: Callable[[], None] | None = None,
    secondary_label: str = "",
    secondary_key: str = "",
    on_secondary: Callable[[], None] | None = None,
) -> None:
    """Render one clear primary action with an optional secondary action."""
    with st.container(key=f"action_bar__{primary_key}"):
        if secondary_label:
            columns = st.columns(2, gap="small")
            with columns[0]:
                secondary_action_button(
                    secondary_label,
                    key=secondary_key,
                    on_click=on_secondary,
                )
            with columns[1]:
                primary_action_button(
                    primary_label,
                    key=primary_key,
                    on_click=on_primary,
                )
        else:
            primary_action_button(
                primary_label,
                key=primary_key,
                on_click=on_primary,
            )


def primary_action_button(
    label: str,
    *,
    key: str,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
) -> bool:
    return st.button(
        label,
        key=key,
        type="primary",
        use_container_width=True,
        on_click=on_click,
        disabled=disabled,
    )


def secondary_action_button(
    label: str,
    *,
    key: str,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
) -> bool:
    return st.button(
        label,
        key=key,
        type="secondary",
        use_container_width=True,
        on_click=on_click,
        disabled=disabled,
    )
