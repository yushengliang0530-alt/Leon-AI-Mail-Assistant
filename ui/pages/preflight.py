"""Send Ready summary and checklist UI."""

import html

import streamlit as st


STATUS_META = {
    "GOOD": ("✓", "#18724f", "正常"),
    "CHECK": ("!", "#a56600", "请确认"),
    "WARNING": ("!", "#b64040", "重点检查"),
}


def render_preflight_panel() -> bool:
    st.markdown("---")
    st.markdown("### 发送前检查")
    st.caption("Send Ready · 只检查当前邮件，不会改写或自动发送。")

    status = str(st.session_state.get("preflight__status", "idle"))
    report = st.session_state.get("preflight__report")
    error = str(st.session_state.get("preflight__error", ""))

    if status == "idle":
        st.info("准备好后运行检查，确认遗漏、附件、语气和承诺风险。")
    elif status == "stale":
        st.warning("邮件或回复依据已修改，请重新运行发送前检查。")
    if error:
        st.warning(error)

    if report is not None and status in {"success", "partial"}:
        icon, color, label = STATUS_META[report.overall_status]
        st.markdown(
            f"""
            <div class="reply-card">
              <h3 style="color:{color}">{icon} 总体 · {label}</h3>
              <p>{html.escape(report.summary)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        coverage_items = [
            item for item in report.items if item.category == "coverage"
        ]
        other_items = [
            item for item in report.items if item.category != "coverage"
        ]
        if coverage_items:
            st.markdown("#### 客户问题覆盖")
            _render_items(coverage_items)
        if other_items:
            st.markdown("#### 发送检查清单")
            _render_items(other_items)
        if report.overall_status == "WARNING":
            st.warning("存在需要重点确认的内容，但不会阻止您复制邮件。")
        elif report.overall_status == "CHECK":
            st.info("建议确认标记事项后发送。")

        duration = st.session_state.get("preflight__duration_seconds")
        tokens = st.session_state.get("preflight__usage_tokens")
        meta = []
        if isinstance(duration, (int, float)):
            meta.append(f"检查耗时 {duration:.2f} 秒")
        if isinstance(tokens, int):
            meta.append(f"本次用量 {tokens} tokens")
        if meta:
            st.caption(" · ".join(meta))

    return st.button(
        (
            "重新发送前检查 · Recheck"
            if status in {"success", "partial", "stale", "error"}
            else "开始发送前检查 · Run Send Ready"
        ),
        key="preflight__run",
        type="primary",
        use_container_width=True,
        disabled=(
            status == "running"
            or not str(st.session_state.get("reply__subject", "")).strip()
            or not str(st.session_state.get("reply__body", "")).strip()
        ),
    )


def _render_items(items: list) -> None:
    for item in items:
        icon, color, label = STATUS_META[item.status]
        suggestion = (
            f"<p><strong>建议：</strong>{html.escape(item.suggestion)}</p>"
            if item.suggestion
            else ""
        )
        st.markdown(
            f"""
            <div class="reply-card">
              <h3 style="color:{color}">{icon} {html.escape(item.title)}
                · {label}</h3>
              <p>{html.escape(item.message)}</p>
              {suggestion}
            </div>
            """,
            unsafe_allow_html=True,
        )
