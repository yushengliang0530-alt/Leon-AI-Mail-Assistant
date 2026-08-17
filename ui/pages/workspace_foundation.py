"""Presentation-only V2.1 workspace foundation pages."""

from collections.abc import Callable

import streamlit as st

from product_identity import APP_VERSION_LABEL
from ui.components import (
    WorkflowStep,
    render_action_bar,
    render_notice_bar,
    render_workspace_empty_state,
    render_workspace_shell,
)


CREATE_WORKFLOW_STEPS = (
    WorkflowStep("details", "填写信息", "Details", "current"),
    WorkflowStep("generate", "生成邮件", "Generate", "upcoming"),
    WorkflowStep("review", "审核结果", "Review", "upcoming"),
)

IMPROVE_WORKFLOW_STEPS = (
    WorkflowStep("draft", "粘贴草稿", "Draft", "current"),
    WorkflowStep("improve", "优化表达", "Improve", "upcoming"),
    WorkflowStep("review", "审核结果", "Review", "upcoming"),
)


def render_create_workspace(
    *,
    service_status: str,
    on_return_home: Callable[[], None],
    on_open_editor: Callable[[], None],
) -> None:
    """Render the Create Email shell before its V1 form is migrated."""

    def render_task() -> None:
        render_workspace_empty_state(
            "从必要事实开始创建邮件",
            "创建邮件工作区已准备好。下一阶段会将现有表单迁入这里；现在仍可安全打开现有创建邮件功能。",
        )
        render_notice_bar(
            "当前阶段说明",
            "邮件生成逻辑、表单字段和 AI 调用保持不变。本页面只建立独立工作空间体验。",
        )
        render_action_bar(
            primary_label="打开创建邮件功能",
            primary_key="create_workspace__open_editor",
            on_primary=on_open_editor,
            secondary_label="返回首页",
            secondary_key="create_workspace__return_home",
            on_secondary=on_return_home,
        )

    render_workspace_shell(
        workspace_key="create",
        version=APP_VERSION_LABEL,
        service_status=service_status,
        title="创建商务邮件",
        description="Create Email · 通过引导完成一封结构清晰、可人工审核的商务邮件。",
        eyebrow="LEON AI · CREATE EMAIL",
        steps=CREATE_WORKFLOW_STEPS,
        render_task=render_task,
        on_return_home=on_return_home,
    )


def render_improve_workspace(
    *,
    service_status: str,
    on_return_home: Callable[[], None],
    on_open_editor: Callable[[], None],
) -> None:
    """Render the Optimize Draft shell before the existing editor is migrated."""

    def render_task() -> None:
        render_workspace_empty_state(
            "让已有草稿更清晰、更适合商务沟通",
            "草稿优化工作区已准备好。现有优化功能保持可用，后续会在这里完成迁移。",
        )
        render_notice_bar(
            "当前阶段说明",
            "优化提示词、风险规则和 AI 调用保持不变。本页面只建立独立工作空间体验。",
        )
        render_action_bar(
            primary_label="打开草稿优化功能",
            primary_key="improve_workspace__open_editor",
            on_primary=on_open_editor,
            secondary_label="返回首页",
            secondary_key="improve_workspace__return_home",
            on_secondary=on_return_home,
        )

    render_workspace_shell(
        workspace_key="improve",
        version=APP_VERSION_LABEL,
        service_status=service_status,
        title="优化已有邮件",
        description="Improve Draft · 保留原意，改善英文表达、商务语气和邮件结构。",
        eyebrow="LEON AI · IMPROVE DRAFT",
        steps=IMPROVE_WORKFLOW_STEPS,
        render_task=render_task,
        on_return_home=on_return_home,
    )
