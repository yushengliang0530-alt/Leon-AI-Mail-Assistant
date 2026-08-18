"""Editable reply result and coverage presentation for the Reply workspace."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st

from ui.components import (
    CoveragePresentationItem,
    render_copy_button,
    render_coverage_items,
    render_coverage_summary,
    render_email_editor,
    render_email_subject_card,
    render_notice_bar,
    render_section_header,
    secondary_action_button,
    tertiary_action_button,
)
from ui.state import invalidate_preflight


_COVERAGE_PRESENTATION = {
    "addressed": ("已回复", "success"),
    "partially_addressed": ("部分回复", "warning"),
    "postponed": ("已说明暂缓", "info"),
    "not_addressed": ("暂未回复", "warning"),
}


def invalidate_reply_coverage() -> None:
    """Keep existing invalidation behaviour after a manual email edit."""
    st.session_state["reply__coverage_digest"] = ""
    st.session_state["reply__coverage_status"] = "stale"
    st.session_state["reply__coverage_error"] = ""
    invalidate_preflight()


def _persist_email_edits() -> None:
    """Persist editable fields while the next workspace canvas is displayed."""
    st.session_state["reply__presentation_subject"] = str(
        st.session_state.get("reply__subject", "")
    )
    st.session_state["reply__presentation_body"] = str(
        st.session_state.get("reply__body", "")
    )
    invalidate_reply_coverage()


def render_reply_result(*, item_titles: Mapping[str, str]) -> str | None:
    """Render the email and its independent coverage result.

    Presentation actions are returned to ``reply.py`` so the existing service
    calls and workflow orchestration remain outside this UI adapter.
    """
    render_section_header("回复已生成", "GENERATED REPLY")
    st.caption("邮件可直接编辑；编辑后会提示您重新检查完整性和发送前风险。")
    subject = render_email_subject_card(
        value_key="reply__subject", on_change=_persist_email_edits
    )
    body = render_email_editor(
        value_key="reply__body", on_change=_persist_email_edits
    )
    render_copy_button(
        label="复制完整邮件",
        value=f"Subject: {subject}\n\n{body}",
        key="reply__copy_full_email",
        primary=True,
    )

    render_section_header("回复完整性", "COVERAGE")
    st.caption("此检查只判断是否回应了待处理事项，不会改写邮件。")
    status = str(st.session_state.get("reply__coverage_status", "idle"))
    coverage = st.session_state.get("reply__coverage")
    if status == "stale":
        render_notice_bar(
            "邮件已修改",
            "请重新检查回复完整性，再继续发送前检查。",
            icon="!",
        )
    if st.session_state.get("reply__coverage_error"):
        render_notice_bar(
            "完整性检查暂不可用",
            str(st.session_state["reply__coverage_error"]),
            icon="!",
        )
    if coverage is not None and status != "stale":
        render_coverage_summary(
            covered_count=coverage.covered_count,
            total_count=coverage.total_count,
            partial_count=coverage.partial_count,
            not_addressed_count=coverage.not_addressed_count,
        )
        presentation_items = tuple(
            CoveragePresentationItem(
                title=item_titles.get(item.item_id, "待处理事项"),
                status=_COVERAGE_PRESENTATION.get(
                    item.status, ("需要确认", "warning")
                )[0],
                note=item.note,
                kind=_COVERAGE_PRESENTATION.get(
                    item.status, ("需要确认", "warning")
                )[1],
            )
            for item in coverage.items
        )
        render_coverage_items(presentation_items)
        if coverage.not_addressed_count:
            render_notice_bar(
                "仍有事项暂未回复",
                "这可能是您有意保留的处理方式；复制前请再次确认。",
                icon="!",
            )
    elif status not in {"stale", "error"}:
        render_notice_bar(
            "正在准备完整性检查",
            "生成完成后会独立核对每个已处理事项。",
        )

    if secondary_action_button(
        "重新检查完整性",
        key="reply__recheck_coverage",
        disabled=not (subject.strip() and body.strip()),
    ):
        return "recheck"
    if secondary_action_button(
        "重新生成回复",
        key="reply__regenerate_reply",
        disabled=not (subject.strip() and body.strip()),
    ):
        return "regenerate"
    if tertiary_action_button("返回修改回复立场", key="reply__generation_back"):
        return "back"
    if st.button(
        "进行发送前检查",
        key="reply__continue_preflight",
        type="primary",
        use_container_width=True,
        disabled=not (subject.strip() and body.strip()),
    ):
        return "preflight"
    return None
