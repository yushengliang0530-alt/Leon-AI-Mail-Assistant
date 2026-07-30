"""Editable reply result and visible Phase 3C coverage cards."""

import html

import streamlit as st
from ui.state import invalidate_preflight


STATUS_META = {
    "addressed": ("✓", "已回复", "#18724f"),
    "partially_addressed": ("!", "部分回复", "#a56600"),
    "postponed": ("◷", "已说明暂缓", "#2858c7"),
    "not_addressed": ("×", "没有回复", "#b64040"),
}


def invalidate_reply_coverage() -> None:
    st.session_state["reply__coverage_digest"] = ""
    st.session_state["reply__coverage_status"] = "stale"
    st.session_state["reply__coverage_error"] = ""
    invalidate_preflight()


def render_reply_result() -> bool:
    st.markdown("### 英文回复邮件")
    st.caption("Reply Email · 可以在复制前直接修改。")
    st.text_input(
        "邮件主题 · Subject",
        key="reply__subject",
        on_change=invalidate_reply_coverage,
    )
    st.text_area(
        "邮件正文 · Body",
        key="reply__body",
        height=360,
        on_change=invalidate_reply_coverage,
    )
    st.caption("点击代码框右上角的复制图标，可复制对应内容。")
    left, right = st.columns(2)
    with left:
        st.markdown("**复制主题 · Copy Subject**")
        st.code(st.session_state.get("reply__subject", ""), language=None)
    with right:
        st.markdown("**复制正文 · Copy Body**")
        st.code(st.session_state.get("reply__body", ""), language=None)
    st.markdown("**复制完整邮件 · Copy Full Email**")
    st.code(
        f"Subject: {st.session_state.get('reply__subject', '')}\n\n"
        f"{st.session_state.get('reply__body', '')}",
        language=None,
    )

    coverage = st.session_state.get("reply__coverage")
    status = st.session_state.get("reply__coverage_status", "idle")
    st.markdown("---")
    st.markdown("### 回复覆盖检查")
    st.caption("Coverage Check · 独立检查，不会修改邮件。")
    if status == "stale":
        st.warning("邮件已修改，请重新检查回复覆盖情况。")
    if st.session_state.get("reply__coverage_error"):
        st.warning(st.session_state["reply__coverage_error"])
    if coverage is not None and status != "stale":
        st.markdown(
            f"## 本次回复覆盖 {coverage.covered_count} / "
            f"{coverage.total_count} 项"
        )
        if coverage.partial_count:
            st.caption(f"部分回复：{coverage.partial_count} 项")
        for item in coverage.items:
            icon, label, color = STATUS_META[item.status]
            st.markdown(
                f"""
                <div class="reply-card">
                  <h3 style="color:{color}">{icon} {html.escape(label)}
                    · {html.escape(item.item_id)}</h3>
                  <p>{html.escape(item.note)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if coverage.not_addressed_count:
            st.warning(
                "仍有事项没有回复。可能是用户主动选择不回应，"
                "发送前请再次确认。"
            )
    return st.button(
        "重新检查覆盖 · Recheck Coverage",
        key="reply__recheck_coverage",
        use_container_width=True,
        disabled=not (
            str(st.session_state.get("reply__subject", "")).strip()
            and str(st.session_state.get("reply__body", "")).strip()
        ),
    )
