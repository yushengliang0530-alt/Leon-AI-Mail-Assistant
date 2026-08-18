"""Reusable Streamlit presentation components for the V2.1 workspace."""

from __future__ import annotations

from collections.abc import Callable
import base64
from dataclasses import dataclass
import html
import json

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


@dataclass(frozen=True)
class ScenarioCard:
    """A concise, display-only definition for a selectable email scenario."""

    key: str
    title: str
    description: str
    icon: str
    available: bool = True
    status: str = ""


@dataclass(frozen=True)
class ReviewItem:
    """One fact shown in the compact confirmation step of a workspace."""

    key: str
    label: str
    value: str


@dataclass(frozen=True)
class OptimizationOption:
    """A presentation-only choice mapped to an existing optimization tone."""

    key: str
    title: str
    description: str
    icon: str


@dataclass(frozen=True)
class AnalysisAction:
    """Presentation-only information required by one analysis action card."""

    title: str
    deadline: str | None = None
    required: bool = False
    uncertain: bool = False
    related_context: str | None = None


@dataclass(frozen=True)
class AnalysisDate:
    """Presentation-only information required by one analysis date card."""

    value: str
    meaning: str
    uncertain: bool = False


@dataclass(frozen=True)
class AnalysisNotice:
    """Presentation-only information required by one analysis notice."""

    title: str
    body: str
    kind: str = "info"


@dataclass(frozen=True)
class DecisionOption:
    """One user-facing reply-position choice in the guided decision canvas."""

    key: str
    title: str
    helper: str


@dataclass(frozen=True)
class DecisionSummaryEntry:
    """A concise, presentation-only account of one confirmed decision."""

    number: int
    title: str
    position: str
    explanation: str
    kind: str = "info"


@dataclass(frozen=True)
class CoveragePresentationItem:
    """A user-facing coverage item without exposing a workflow identifier."""

    title: str
    status: str
    note: str
    kind: str


@dataclass(frozen=True)
class PreflightPresentationItem:
    """A user-facing send-ready check without exposing implementation fields."""

    title: str
    message: str
    suggestion: str | None
    kind: str


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


def render_scenario_cards(
    cards: tuple[ScenarioCard, ...],
    *,
    key_prefix: str,
    on_select: Callable[[str], None] | None = None,
) -> str | None:
    """Render one consistent scenario-card family without embedding workflow rules."""
    selected: str | None = None
    with st.container(key=f"scenario_cards__{key_prefix}"):
        for card in cards:
            label = f"{card.title}\n{card.description}"
            if not card.available:
                label = f"{card.title} · {card.status or 'Coming soon'}\n{card.description}"
            if st.button(
                label,
                key=f"{key_prefix}{card.key}",
                type="secondary",
                icon=f":material/{card.icon}:",
                use_container_width=True,
                disabled=not card.available,
            ):
                selected = card.key
                if on_select:
                    on_select(card.key)
    return selected


def render_guided_question_header(
    *,
    current: int,
    total: int,
    title: str,
    helper: str,
    required: bool,
) -> None:
    """Render the reusable heading for a one-question-at-a-time task canvas."""
    requirement = "必填" if required else "可选"
    st.markdown(
        f"""
        <div class="la-guided-question__progress">问题 {current} / {total} · {requirement}</div>
        <h2 class="la-guided-question__title">{html.escape(title)}</h2>
        <p class="la-guided-question__helper">{html.escape(helper)}</p>
        """,
        unsafe_allow_html=True,
    )


def render_review_items(
    items: tuple[ReviewItem, ...],
    *,
    action_key_prefix: str,
) -> str | None:
    """Render fact-first review rows and return the field selected for editing."""
    selected: str | None = None
    with st.container(key=f"review_items__{action_key_prefix}"):
        for item in items:
            content, action = st.columns((5, 1), gap="small")
            with content:
                st.markdown(
                    f"""
                    <article class="la-review-item">
                      <span>{html.escape(item.label)}</span>
                      <strong>{html.escape(item.value)}</strong>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
            with action:
                if secondary_action_button(
                    "修改",
                    key=f"{action_key_prefix}{item.key}",
                ):
                    selected = item.key
    return selected


def render_optimization_option_cards(
    options: tuple[OptimizationOption, ...],
    *,
    selected: str,
    key_prefix: str,
) -> str | None:
    """Render one clear choice without changing the underlying tone values."""
    chosen: str | None = None
    with st.container(key=f"optimization_options__{key_prefix}"):
        for option in options:
            is_selected = option.key == selected
            if st.button(
                f"{option.title}\n{option.description}",
                key=f"{key_prefix}{option.key}",
                type="primary" if is_selected else "secondary",
                icon=f":material/{option.icon}:",
                use_container_width=True,
            ):
                chosen = option.key
    return chosen


def render_before_after_panel(
    *,
    original_subject: str,
    original_body: str,
    render_after: Callable[[], None],
) -> None:
    """Present the original as read-only beside an editable final email."""
    before, after = st.columns(2, gap="large")
    with before:
        with st.container(key="improve__before_panel"):
            st.markdown("#### 原始版本")
            st.caption("Original draft · 只读参考")
            st.markdown('<div class="la-email-subject__label">Subject</div>', unsafe_allow_html=True)
            st.text_input(
                "原始主题",
                value=original_subject or "未提供主题",
                disabled=True,
                key="improve__before_subject",
                label_visibility="collapsed",
            )
            st.markdown('<div class="la-email-editor__label">Email Body</div>', unsafe_allow_html=True)
            st.text_area(
                "原始正文",
                value=original_body,
                height=420,
                disabled=True,
                key="improve__before_body",
                label_visibility="collapsed",
            )
    with after:
        with st.container(key="improve__after_panel"):
            st.markdown("#### 优化版本")
            st.caption("Improved draft · 可继续编辑")
            render_after()


def render_optimization_summary(items: tuple[str, ...]) -> None:
    """Keep the outcome explanation short and tied to existing result analysis."""
    if not items:
        return
    st.markdown(
        '<ul class="la-optimization-summary">'
        + "".join(f"<li>{html.escape(item)}</li>" for item in items[:4])
        + "</ul>",
        unsafe_allow_html=True,
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


def render_analysis_summary_panel(
    *,
    summary: str,
    sender_intent: str,
    urgency_label: str,
    urgency_kind: str,
) -> None:
    """Present the one-screen summary for an incoming-email analysis."""
    allowed = {"success", "info", "warning", "risk"}
    safe_kind = urgency_kind if urgency_kind in allowed else "info"
    st.markdown(
        f"""
        <section class="la-analysis-summary">
          <div class="la-analysis-summary__topline">
            <span class="la-analysis-summary__eyebrow">快速理解 · ANALYSIS</span>
            <span class="la-status-badge la-status-badge--{safe_kind}">{html.escape(urgency_label)}</span>
          </div>
          <div class="la-analysis-summary__title">邮件摘要</div>
          <p>{html.escape(summary)}</p>
          <div class="la-analysis-summary__intent"><strong>对方意图</strong>{html.escape(sender_intent)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_action_cards(
    items: tuple[AnalysisAction, ...],
    *,
    variant: str,
) -> None:
    """Render structured requests or questions without exposing internal IDs."""
    safe_variant = "question" if variant == "question" else "request"
    cards = "".join(
        _analysis_action_card(item, index=index, variant=safe_variant)
        for index, item in enumerate(items, start=1)
    )
    st.markdown(
        f'<div class="la-analysis-actions la-analysis-actions--{safe_variant}">{cards}</div>',
        unsafe_allow_html=True,
    )


def _analysis_action_card(
    item: AnalysisAction,
    *,
    index: int,
    variant: str,
) -> str:
    metadata: list[str] = []
    if item.deadline:
        metadata.append(
            f'<span class="la-analysis-item__deadline">截止：{html.escape(item.deadline)}</span>'
        )
    if item.required:
        metadata.append('<span class="la-analysis-item__flag">必须回复</span>')
    if item.uncertain:
        metadata.append('<span class="la-analysis-item__flag">信息待确认</span>')
    context = (
        f'<div class="la-analysis-item__context">关联要求：{html.escape(item.related_context)}</div>'
        if item.related_context
        else ""
    )
    return f"""
        <article class="la-analysis-item la-analysis-item--{variant}">
          <span class="la-analysis-item__index">{index:02d}</span>
          <div class="la-analysis-item__content">
            <p>{html.escape(item.title)}</p>
            {context}
            <div class="la-analysis-item__meta">{''.join(metadata)}</div>
          </div>
        </article>
    """


def render_analysis_date_cards(items: tuple[AnalysisDate, ...]) -> None:
    """Render key dates with concise value-first visual emphasis."""
    cards = "".join(
        f"""
        <article class="la-analysis-date-card">
          <strong>{html.escape(item.value)}</strong>
          <span>{html.escape(item.meaning)}</span>
          {"<em>待确认</em>" if item.uncertain else ""}
        </article>
        """
        for item in items
    )
    st.markdown(
        f'<div class="la-analysis-date-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_analysis_notices(items: tuple[AnalysisNotice, ...]) -> None:
    """Render supportive, severity-aware notices for analysis follow-up."""
    allowed = {"info", "warning", "risk"}
    notices = "".join(
        f"""
        <aside class="la-analysis-notice la-analysis-notice--{item.kind if item.kind in allowed else 'info'}">
          <strong>{html.escape(item.title)}</strong>
          <span>{html.escape(item.body)}</span>
        </aside>
        """
        for item in items
    )
    st.markdown(notices, unsafe_allow_html=True)


def render_strategy_list(
    items: tuple[str, ...],
    *,
    initial_limit: int = 3,
) -> None:
    """Keep advice concise first, with optional details kept out of the way."""
    visible = items[:initial_limit]
    remaining = items[initial_limit:]
    st.markdown(
        '<ol class="la-strategy-list">'
        + "".join(f"<li>{html.escape(item)}</li>" for item in visible)
        + "</ol>",
        unsafe_allow_html=True,
    )
    if remaining:
        with st.expander("查看更多建议", expanded=False):
            st.markdown(
                '<ol class="la-strategy-list la-strategy-list--more">'
                + "".join(f"<li>{html.escape(item)}</li>" for item in remaining)
                + "</ol>",
                unsafe_allow_html=True,
            )


def render_decision_focus_card(
    *,
    index: int,
    total: int,
    title: str,
    deadline: str | None,
    required: bool,
    uncertain: bool,
) -> None:
    """Keep the current business item legible before asking for a decision."""
    metadata = ["必须回复" if required else "可选事项"]
    if deadline:
        metadata.append(f"原要求截止时间：{deadline}")
    if uncertain:
        metadata.append("信息待确认")
    st.markdown(
        f"""
        <section class="la-decision-focus">
          <div class="la-decision-focus__step">事项 {index} / {total}</div>
          <div class="la-decision-focus__label">对方希望你回复</div>
          <h2>{html.escape(title)}</h2>
          <div class="la-decision-focus__meta">{html.escape(' · '.join(metadata))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_decision_option_cards(
    options: tuple[DecisionOption, ...],
    *,
    selected: str,
    key_prefix: str,
) -> str | None:
    """Render selection cards and return the key selected during this rerun."""
    clicked: str | None = None
    with st.container(key=f"decision_options__{key_prefix}"):
        for option in options:
            is_selected = option.key == selected
            if st.button(
                f"{option.title}\n{option.helper}",
                key=f"{key_prefix}__{option.key}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                clicked = option.key
    return clicked


def render_guided_action_bar(
    *,
    back_label: str,
    back_key: str,
    next_label: str,
    next_key: str,
) -> tuple[bool, bool]:
    """Render a consistent previous/next action pair for a guided step."""
    with st.container(key=f"guided_action_bar__{next_key}"):
        columns = st.columns((0.42, 0.58), gap="small")
        with columns[0]:
            back_clicked = secondary_action_button(back_label, key=back_key)
        with columns[1]:
            next_clicked = primary_action_button(next_label, key=next_key)
    return back_clicked, next_clicked


def render_decision_summary_cards(
    entries: tuple[DecisionSummaryEntry, ...],
) -> None:
    """Display the facts and positions that will guide reply generation."""
    allowed = {"info", "warning", "risk", "success"}
    cards = "".join(
        f"""
        <article class="la-decision-summary-card la-decision-summary-card--{entry.kind if entry.kind in allowed else 'info'}">
          <span class="la-decision-summary-card__number">{entry.number:02d}</span>
          <div>
            <strong>{html.escape(entry.title)}</strong>
            <em>{html.escape(entry.position)}</em>
            <p>{html.escape(entry.explanation)}</p>
          </div>
        </article>
        """
        for entry in entries
    )
    st.markdown(
        f'<div class="la-decision-summary-cards">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_email_subject_card(
    *,
    value_key: str,
    on_change: Callable[[], None],
) -> str:
    """Render the editable subject as a dedicated, compact email surface."""
    with st.container(key=f"email_subject__{value_key}"):
        st.markdown('<div class="la-email-subject__label">Subject</div>', unsafe_allow_html=True)
        value = st.text_input(
            "邮件主题",
            key=value_key,
            label_visibility="collapsed",
            on_change=on_change,
        )
        render_copy_button(
            label="复制主题",
            value=value,
            key=f"copy_subject__{value_key}",
        )
    return value


def render_email_editor(
    *,
    value_key: str,
    on_change: Callable[[], None],
) -> str:
    """Render the editable body in a roomy email-oriented writing surface."""
    with st.container(key=f"email_editor__{value_key}"):
        st.markdown(
            '<div class="la-email-editor__label">Email Body</div>',
            unsafe_allow_html=True,
        )
        value = st.text_area(
            "邮件正文",
            key=value_key,
            label_visibility="collapsed",
            height=420,
            on_change=on_change,
        )
        render_copy_button(
            label="复制正文",
            value=value,
            key=f"copy_body__{value_key}",
        )
    return value


def render_copy_button(
    *, label: str, value: str, key: str, primary: bool = False
) -> None:
    """Offer a graceful clipboard control without relying on server-side copy."""
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    safe_label = html.escape(label)
    background = "#2563eb" if primary else "#fff"
    color = "#fff" if primary else "#334155"
    border = "#2563eb" if primary else "#dbe5f1"
    st.iframe(
        f"""
        <button id="{html.escape(key)}" onclick="copyValue()" style="
          width:100%;height:40px;border:1px solid {border};border-radius:10px;
          background:{background};color:{color};font:650 13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;cursor:pointer">
          {safe_label}
        </button>
        <script>
        async function copyValue() {{
          const button = document.getElementById({json.dumps(key)});
          try {{
            const bytes = Uint8Array.from(atob({json.dumps(encoded)}), c => c.charCodeAt(0));
            await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
            button.textContent = "已复制";
          }} catch (error) {{
            button.textContent = "复制失败，请手动复制";
          }}
        }}
        </script>
        """,
        height=46,
        width="stretch",
    )


def render_coverage_summary(
    *,
    covered_count: int,
    total_count: int,
    partial_count: int,
    not_addressed_count: int,
) -> None:
    parts = [f"{covered_count} 项已覆盖"]
    if partial_count:
        parts.append(f"{partial_count} 项部分覆盖")
    if not_addressed_count:
        parts.append(f"{not_addressed_count} 项暂未回复")
    st.markdown(
        f"""
        <section class="la-coverage-summary">
          <div class="la-coverage-summary__label">回复完整性</div>
          <strong>{html.escape(' · '.join(parts))}</strong>
          <span>共 {total_count} 个需要处理的事项</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_coverage_items(items: tuple[CoveragePresentationItem, ...]) -> None:
    allowed = {"success", "info", "warning", "risk"}
    cards = "".join(
        f"""
        <article class="la-coverage-item la-coverage-item--{item.kind if item.kind in allowed else 'info'}">
          <div><strong>{html.escape(item.title)}</strong><em>{html.escape(item.status)}</em></div>
          <p>{html.escape(item.note)}</p>
        </article>
        """
        for item in items
    )
    st.markdown(f'<div class="la-coverage-items">{cards}</div>', unsafe_allow_html=True)


def render_preflight_summary(*, status: str, summary: str) -> None:
    presentation = {
        "GOOD": ("未发现明显需要修改的问题", "success"),
        "CHECK": ("建议确认后发送", "warning"),
        "WARNING": ("存在需要重点确认的内容", "risk"),
    }
    title, kind = presentation.get(status, presentation["CHECK"])
    st.markdown(
        f"""
        <section class="la-preflight-summary la-preflight-summary--{kind}">
          <span class="la-status-badge la-status-badge--{kind}">{html.escape(title)}</span>
          <p>{html.escape(summary)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_preflight_items(
    items: tuple[PreflightPresentationItem, ...],
    *,
    kind: str,
) -> None:
    allowed = {"success", "warning", "risk"}
    safe_kind = kind if kind in allowed else "warning"
    rows = "".join(
        f"""
        <article class="la-preflight-item la-preflight-item--{safe_kind}">
          <strong>{html.escape(item.title)}</strong>
          <p>{html.escape(item.message)}</p>
          {f'<small>建议：{html.escape(item.suggestion)}</small>' if item.suggestion else ''}
        </article>
        """
        for item in items
    )
    st.markdown(f'<div class="la-preflight-items">{rows}</div>', unsafe_allow_html=True)


def render_completion_panel() -> None:
    """Make the end of the workflow explicit without implying send capability."""
    st.markdown(
        """
        <section class="la-completion-panel">
          <div class="la-completion-panel__eyebrow">REPLY READY</div>
          <h2>邮件已准备完成</h2>
          <p>Leon AI 已完成内容生成、回复完整性和发送前检查。请在 Outlook 或 Gmail 中最终确认后发送。</p>
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


def tertiary_action_button(
    label: str,
    *,
    key: str,
    on_click: Callable[[], None] | None = None,
) -> bool:
    """Render an intentionally quiet optional action with a stable key."""
    with st.container(key=f"tertiary_action__{key}"):
        return st.button(
            label,
            key=key,
            type="secondary",
            on_click=on_click,
        )
