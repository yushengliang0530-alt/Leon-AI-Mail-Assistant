"""Reviewed supplier follow-up scenario definitions."""

from models.scenario import Scenario, ScenarioField


def _field(
    key: str,
    label_zh: str,
    label_en: str,
    *,
    required: bool = False,
    field_type: str = "text",
    placeholder: str = "",
    help_text: str = "",
    max_length: int = 600,
) -> ScenarioField:
    return ScenarioField(
        key=key,
        label_zh=label_zh,
        label_en=label_en,
        required=required,
        field_type=field_type,
        placeholder=placeholder,
        help_text=help_text,
        max_length=max_length,
    )


SUPPLIER_NAME = _field(
    "supplier_name",
    "供应商名称",
    "Supplier Name",
    required=True,
    placeholder="例如：ABC Components",
)
PROJECT_NAME = _field(
    "project_name",
    "项目名称",
    "Project Name",
    placeholder="例如：North Plant Upgrade",
)
CURRENT_SITUATION = _field(
    "current_situation",
    "现在是什么情况",
    "Current Situation",
    required=True,
    field_type="textarea",
    placeholder="只填写已知事实，例如：尚未收到更新版本。",
)
REQUESTED_REPLY = _field(
    "requested_reply",
    "希望什么时候回复",
    "Requested Reply Time",
    placeholder="例如：请在本周五前回复",
)
BUSINESS_IMPACT = _field(
    "business_impact",
    "延期会造成什么影响",
    "Business Impact",
    field_type="textarea",
    placeholder="例如：将影响下阶段施工安排；不确定可留空。",
)
REQUIRED_ACTION = _field(
    "required_action",
    "需要供应商采取什么行动",
    "Required Supplier Action",
    required=True,
    field_type="textarea",
    placeholder="例如：确认可行交期并提供更新后的计划。",
)


SUPPLIER_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="supplier_quotation",
        title_zh="催报价",
        title_en="Follow Up Quotation",
        description="跟进尚未收到的报价，并明确需要回复的内容和时间。",
        fields=(
            SUPPLIER_NAME,
            _field(
                "quotation_scope",
                "需要报价的产品或范围",
                "Quotation Item or Scope",
                required=True,
                field_type="textarea",
                placeholder="例如：三套控制柜及现场调试服务。",
            ),
            PROJECT_NAME,
            _field(
                "original_request_date",
                "最初请求报价的时间",
                "Original Request Date",
                placeholder="例如：7月22日；不确定可留空。",
            ),
            _field(
                "current_situation",
                "现在是什么情况",
                "Current Situation",
                field_type="textarea",
                placeholder="例如：尚未收到正式报价。",
            ),
            _field(
                "requested_reply",
                "希望什么时候回复",
                "Requested Reply Time",
                required=True,
                placeholder="例如：请在本周五前回复。",
            ),
            BUSINESS_IMPACT,
            REQUIRED_ACTION,
        ),
        default_tone="Formal",
        risk_policy="supplier_follow_up",
        prompt_policy="supplier_facts_only",
    ),
    Scenario(
        id="supplier_delivery",
        title_zh="催交期",
        title_en="Follow Up Delivery",
        description="确认订单、物料或交付物的当前状态和可靠交期。",
        fields=(
            SUPPLIER_NAME,
            _field(
                "deliverable",
                "订单、物料或交付物",
                "Order, Item, or Deliverable",
                required=True,
                field_type="textarea",
                placeholder="例如：PO 2026-018中的阀门。",
            ),
            PROJECT_NAME,
            _field(
                "original_plan_date",
                "原计划交付日期",
                "Original Delivery Date",
                required=True,
                placeholder="例如：2026年8月10日。",
            ),
            CURRENT_SITUATION,
            REQUESTED_REPLY,
            BUSINESS_IMPACT,
            REQUIRED_ACTION,
        ),
        default_tone="Strong",
        risk_policy="supplier_follow_up",
        prompt_policy="supplier_facts_only",
    ),
    Scenario(
        id="supplier_plan_update",
        title_zh="更新计划",
        title_en="Request Plan Update",
        description="要求供应商提供最新计划、关键节点和下一步行动。",
        fields=(
            SUPPLIER_NAME,
            PROJECT_NAME,
            _field(
                "original_plan_date",
                "原计划提交日期",
                "Original Planned Submission Date",
                required=True,
                placeholder="例如：2026年8月5日。",
            ),
            CURRENT_SITUATION,
            _field(
                "requested_reply",
                "希望什么时候回复",
                "Requested Reply Time",
                required=True,
                placeholder="例如：请在明天下午5点前回复。",
            ),
            BUSINESS_IMPACT,
            REQUIRED_ACTION,
        ),
        default_tone="Formal",
        risk_policy="supplier_follow_up",
        prompt_policy="supplier_facts_only",
    ),
    Scenario(
        id="supplier_delay_explanation",
        title_zh="延期解释",
        title_en="Request Delay Explanation",
        description="要求供应商说明已知延期事实、原因和恢复计划。",
        fields=(
            SUPPLIER_NAME,
            _field(
                "delayed_item",
                "延期的事项或里程碑",
                "Delayed Item or Milestone",
                required=True,
                field_type="textarea",
                placeholder="例如：设备图纸最终版。",
            ),
            PROJECT_NAME,
            _field(
                "original_plan_date",
                "原承诺日期",
                "Original Committed Date",
                required=True,
                placeholder="例如：2026年8月5日。",
            ),
            CURRENT_SITUATION,
            _field(
                "requested_reply",
                "希望什么时候提供解释",
                "Requested Explanation Time",
                placeholder="例如：请在今天下班前回复。",
            ),
            BUSINESS_IMPACT,
            REQUIRED_ACTION,
        ),
        default_tone="Strong",
        risk_policy="supplier_follow_up",
        prompt_policy="supplier_facts_only",
    ),
)

SUPPLIER_SCENARIO_BY_ID = {
    scenario.id: scenario for scenario in SUPPLIER_SCENARIOS
}


def get_supplier_scenario(scenario_id: str) -> Scenario:
    try:
        return SUPPLIER_SCENARIO_BY_ID[scenario_id]
    except KeyError as exc:
        raise ValueError("未知的供应商任务。") from exc
