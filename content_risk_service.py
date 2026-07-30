"""Local advisory checks for sensitive content before an AI request."""

from dataclasses import dataclass
import re


RISK_LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2}
ADVISORY_NOTICE = "本功能仅提供辅助检查，不能替代公司的保密制度及人工审核。"


@dataclass(frozen=True)
class RiskItem:
    category: str
    description: str
    suggestion: str


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: str
    risk_items: tuple[RiskItem, ...]

    @property
    def requires_confirmation(self) -> bool:
        return self.risk_level == "high"

    @property
    def summary(self) -> str:
        if self.risk_level == "high":
            return "发现可能包含敏感凭证或个人身份信息，请人工核对后再提交。"
        if self.risk_level == "medium":
            return "发现需要注意的商务、个人或承诺类信息，建议发送前核对。"
        return "未发现明显敏感信息，但仍请确认内容符合公司保密规定。"


_CREDENTIAL_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
    re.compile(
        r"(?:api[_\s-]?key|access[_\s-]?token|bearer|password|passwd|"
        r"secret|webhook|otp|验证码|登录凭证)\s*[:=]\s*\S{6,}",
        re.IGNORECASE,
    ),
)
_DOCUMENT_PATTERN = re.compile(
    r"(?:身份证|passport|护照|id\s*(?:number|no\.?))\s*[:：#]?\s*"
    r"[A-Za-z0-9-]{7,}",
    re.IGNORECASE,
)
_BANK_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[\s-]?){13,19}(?!\d)")
_LONG_NUMBER_PATTERN = re.compile(r"(?<!\d)\d{10,18}(?!\d)")
_EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\s()-]?){8,15}(?!\d)")

_CONFIDENTIAL_TERMS = (
    "confidential",
    "internal use only",
    "商业机密",
    "客户机密",
    "内部报价",
    "供应商底价",
    "未公开合同",
    "内部经营数据",
    "尚未公开",
    "contract price",
    "cost data",
    "internal budget",
)
_LEGAL_FINANCIAL_TERMS = (
    "赔偿承诺",
    "违约责任",
    "接受责任",
    "放弃权利",
    "付款承诺",
    "法律结论",
    "indemnify",
    "accept liability",
    "waive our rights",
    "binding commitment",
)
_COMMITMENT_TERMS = (
    "保证完成",
    "确保完成",
    "确定交付",
    "正式承诺",
    "guarantee completion",
    "we guarantee",
    "definite delivery date",
    "commit to deliver",
)
_PRICE_TERMS = (
    "成本数据",
    "内部成本",
    "合同价格",
    "报价",
    "预算",
    "supplier cost",
    "contract value",
    "quotation",
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def _item(category: str, description: str, suggestion: str) -> RiskItem:
    return RiskItem(
        category=category,
        description=description,
        suggestion=suggestion,
    )


def analyze_content_risk(text: str) -> RiskAssessment:
    """Return a bounded local assessment without retaining matched source text."""
    content = text or ""
    items: list[RiskItem] = []
    level = "low"

    if any(pattern.search(content) for pattern in _CREDENTIAL_PATTERNS):
        level = "high"
        items.append(
            _item(
                "系统与账户凭证",
                "检测到疑似 API Key、Token、密码、验证码或 Secret（内容已隐藏）。",
                "删除或替换凭证后再提交；如可能已泄露，请立即轮换凭证。",
            )
        )

    if _DOCUMENT_PATTERN.search(content):
        level = "high"
        items.append(
            _item(
                "个人身份证件",
                "检测到疑似身份证或护照号码（仅显示为 ****）。",
                "删除证件号码，或改用不含身份凭证的描述。",
            )
        )

    if _BANK_CARD_PATTERN.search(content) or _LONG_NUMBER_PATTERN.search(content):
        level = "high"
        items.append(
            _item(
                "长数字或账户信息",
                "检测到可能的账号、银行卡或身份编号（仅显示为 ****）。",
                "确认数字用途；如属于个人或账户信息，请删除后再提交。",
            )
        )

    if _contains_any(content, _CONFIDENTIAL_TERMS):
        if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER["medium"]:
            level = "medium"
        items.append(
            _item(
                "商业机密",
                "内容可能涉及未公开项目、客户机密或内部经营信息。",
                "确认公司保密要求，必要时删除项目名称、价格或内部细节。",
            )
        )

    if _contains_any(content, _LEGAL_FINANCIAL_TERMS):
        if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER["medium"]:
            level = "medium"
        items.append(
            _item(
                "财务与法律责任",
                "内容可能包含付款、赔偿、责任确认或权利放弃。",
                "发送前请由有权限的负责人核对措辞和授权范围。",
            )
        )

    if _contains_any(content, _COMMITMENT_TERMS):
        if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER["medium"]:
            level = "medium"
        items.append(
            _item(
                "商务承诺",
                "内容可能构成确定交期、保证完成或代表公司作出承诺。",
                "确认承诺已获授权，并使用与实际可控范围一致的措辞。",
            )
        )

    if _contains_any(content, _PRICE_TERMS):
        if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER["medium"]:
            level = "medium"
        items.append(
            _item(
                "价格与成本",
                "内容可能涉及报价、合同价值、预算或内部成本。",
                "确认收件人范围及价格信息是否允许通过第三方 AI 处理。",
            )
        )

    if _EMAIL_PATTERN.search(content) or _PHONE_PATTERN.search(content):
        if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER["medium"]:
            level = "medium"
        items.append(
            _item(
                "个人联系方式",
                "检测到可能的个人邮箱或电话号码（具体内容不显示）。",
                "确认联系方式属于必要信息，并符合公司和个人隐私要求。",
            )
        )

    return RiskAssessment(risk_level=level, risk_items=tuple(items))
