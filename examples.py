"""Structured V1.0 examples used by the Streamlit interface."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessExample:
    key: str
    title: str
    mode: str
    source_text: str
    tone_choice: str
    country_region: str
    expected_result: str
    localization_note: str = ""


BUSINESS_EXAMPLES = (
    BusinessExample(
        key="supplier_delivery_followup",
        title="供应商交期催办",
        mode="写英文邮件",
        source_text=(
            "供应商原计划本周提交更新后的交付计划，但目前仍未收到。"
            "请要求对方说明延迟原因，并最迟于本周五下午5点前提交更新计划。"
            "继续延迟可能影响项目整体进度。"
        ),
        tone_choice="明确强硬 · Strong",
        country_region="新加坡 / Singapore",
        expected_result="明确说明延迟影响、责任、行动要求和回复期限，同时保持专业。",
    ),
    BusinessExample(
        key="indonesia_meeting_invitation",
        title="印度尼西亚客户会议邀请",
        mode="写英文邮件",
        source_text=(
            "邀请印度尼西亚客户团队参加下周二上午10点的项目协调会议，"
            "讨论文件审批、设备交付和下阶段计划，请对方确认参加人员。"
        ),
        tone_choice="正式 · Formal",
        country_region="印度尼西亚 / Indonesia",
        expected_result="形成结构清楚的正式会议邀请，并明确会议议题和确认事项。",
        localization_note=(
            "如果已知对方习惯使用 Pak 或 Bu，可核对后使用；否则优先使用姓名。"
        ),
    ),
    BusinessExample(
        key="malaysia_management_update",
        title="马来西亚管理层正式汇报",
        mode="写英文邮件",
        source_text=(
            "向马来西亚管理层汇报，本周已完成供应商技术澄清，"
            "但部分文件仍待客户审批，可能对下阶段采购安排产生影响。"
        ),
        tone_choice="高管简洁 · Executive",
        country_region="马来西亚 / Malaysia",
        expected_result="突出已完成事项、当前阻塞和采购影响，保持高管简洁风格。",
        localization_note="如对方具有正式头衔，应根据其邮件签名准确保留。",
    ),
    BusinessExample(
        key="improve_urgent_email",
        title="英文邮件优化",
        mode="优化英文邮件",
        source_text=(
            "Dear Jason,\n\n"
            "Please kindly check below issue and reply us ASAP because it already "
            "delay long time and customer is pushing us.\n\nThanks."
        ),
        tone_choice="正式 · Formal",
        country_region="未指定 / Not Specified",
        expected_result="修正语法、中式英语和过度直接表达，同时保留紧迫性。",
    ),
)
