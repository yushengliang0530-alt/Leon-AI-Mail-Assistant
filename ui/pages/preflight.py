"""Send-ready presentation for the Reply workspace."""

from __future__ import annotations

import re

import streamlit as st

from ui.components import (
    PreflightPresentationItem,
    render_completion_panel,
    render_copy_button,
    render_notice_bar,
    render_preflight_items,
    render_preflight_summary,
    render_section_header,
    secondary_action_button,
    tertiary_action_button,
)
from ui.state import clear_reply_state, return_to_reply_decisions


_PUBLIC_TITLES = {
    "action_clarity": "行动要求",
    "deadline_clarity": "截止时间",
    "salutation": "称谓",
    "tone_alignment": "邮件语气",
    "commitment_risk": "承诺与责任",
}


def _public_title(item: object) -> str:
    """Remove workflow IDs and internal category names from visible checks."""
    title = _PUBLIC_TITLES.get(str(item.title), str(item.title))
    suffix = f" · {item.item_id}"
    if title.endswith(suffix):
        return title[: -len(suffix)]
    # Local coverage checks may expose a derived internal ID rather than the
    # preflight item ID. It is implementation detail, never user-facing copy.
    return re.sub(r"\s*·\s*[A-Za-z][A-Za-z0-9_:-]*\s*$", "", title)


def _items_for_status(report: object, status: str) -> tuple[PreflightPresentationItem, ...]:
    return tuple(
        PreflightPresentationItem(
            title=_public_title(item),
            message=item.message,
            suggestion=item.suggestion,
            kind=status.lower(),
        )
        for item in report.items
        if item.status == status
    )


def _render_completion_actions() -> None:
    subject = str(st.session_state.get("reply__subject", ""))
    body = str(st.session_state.get("reply__body", ""))
    render_completion_panel()
    render_copy_button(
        label="复制最终邮件",
        value=f"Subject: {subject}\n\n{body}",
        key="reply__copy_final_email",
        primary=True,
    )
    if secondary_action_button("返回修改回复策略", key="reply__completion_back"):
        return_to_reply_decisions()
        st.rerun()
    if tertiary_action_button("开始新的回复", key="reply__completion_new"):
        clear_reply_state()
        st.rerun()


def render_preflight_panel() -> bool:
    """Render the send-ready report; return whether a check was requested."""
    render_section_header("发送前检查", "SEND READY")
    st.caption("检查当前邮件的遗漏、附件、语气与承诺风险；不会改写或自动发送。")

    status = str(st.session_state.get("preflight__status", "idle"))
    report = st.session_state.get("preflight__report")
    error = str(st.session_state.get("preflight__error", ""))
    if status == "idle":
        render_notice_bar(
            "准备检查",
            "确认邮件内容后运行检查，发送前仍请由您最终审核。",
        )
    elif status == "stale":
        render_notice_bar(
            "检查结果已过期",
            "邮件或回复依据已修改，请重新运行发送前检查。",
            icon="!",
        )
    if error:
        render_notice_bar("检查暂不完整", error, icon="!")

    if report is not None and status in {"success", "partial"}:
        render_preflight_summary(
            status=report.overall_status, summary=report.summary
        )
        groups = (
            ("已通过", "GOOD", "success"),
            ("建议确认", "CHECK", "warning"),
            ("重要风险", "WARNING", "risk"),
        )
        for title, item_status, kind in groups:
            items = _items_for_status(report, item_status)
            if items:
                render_section_header(title, "CHECKLIST")
                render_preflight_items(items, kind=kind)
        if report.overall_status == "WARNING":
            render_notice_bar(
                "存在重要风险",
                "系统不会阻止复制邮件，但建议先完成内部确认。",
                icon="!",
            )
        elif report.overall_status == "CHECK":
            render_notice_bar(
                "建议确认后发送",
                "请处理标记事项，或确认这是有意保留的表达。",
                icon="!",
            )

        duration = st.session_state.get("preflight__duration_seconds")
        tokens = st.session_state.get("preflight__usage_tokens")
        meta = []
        if isinstance(duration, (int, float)):
            meta.append(f"检查耗时 {duration:.2f} 秒")
        if isinstance(tokens, int):
            meta.append(f"本次用量 {tokens} tokens")
        if meta:
            st.caption(" · ".join(meta))
        _render_completion_actions()

    return st.button(
        "重新运行发送前检查" if status in {"success", "partial", "stale", "error"} else "开始发送前检查",
        key="preflight__run",
        type="primary",
        use_container_width=True,
        disabled=(
            status == "running"
            or not str(st.session_state.get("reply__subject", "")).strip()
            or not str(st.session_state.get("reply__body", "")).strip()
        ),
    )
