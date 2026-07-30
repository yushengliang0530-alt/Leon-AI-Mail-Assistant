"""Advisory salutation and localization guidance without identity inference."""

from dataclasses import dataclass
import re


COUNTRY_REGION_OPTIONS = (
    "未指定 / Not Specified",
    "新加坡 / Singapore",
    "中国 / China",
    "印度尼西亚 / Indonesia",
    "马来西亚 / Malaysia",
    "越南 / Vietnam",
    "土耳其 / Türkiye",
    "欧洲 / Europe",
    "美国 / United States",
    "中东 / Middle East",
    "其他 / Other",
)


@dataclass(frozen=True)
class LocalizationGuidance:
    recommended_salutation: str
    salutation_risk: str
    politeness_guidance: str
    cross_cultural_note: str


def _clean_recipient(recipient: str) -> str:
    return " ".join((recipient or "").strip().split())


def _recommended_salutation(recipient: str) -> str:
    clean = _clean_recipient(recipient)
    if not clean:
        return "如无法确认姓名，可考虑使用 Dear Team 或与部门对应的称谓。"
    if re.search(r"\b(team|manager|department|committee)\b", clean, re.I):
        return f"可考虑使用 Dear {clean},；如已知姓名，优先使用姓名会更自然。"
    return f"通常建议使用 Dear {clean},；请以对方邮件签名中的称呼习惯为准。"


def build_localization_guidance(
    *,
    recipient: str,
    country_region: str,
    custom_region: str = "",
    tone: str,
    source_text: str = "",
) -> LocalizationGuidance:
    """Return concise, non-prescriptive guidance for the selected region."""
    clean_recipient = _clean_recipient(recipient)
    region = country_region or COUNTRY_REGION_OPTIONS[0]
    source = f"{clean_recipient} {source_text}".strip()
    salutation = _recommended_salutation(clean_recipient)
    risk = (
        "姓名、性别或称谓偏好不明确时，不要自动添加 Mr.、Ms. 或 Mrs.；"
        "建议核对名片、邮件签名或正式资料。"
    )
    politeness = (
        "在正式商务场景中可考虑使用完整称谓和清晰、礼貌的行动要求；"
        f"当前选择的语气为 {tone}。"
    )
    note = "仍应结合对方公司文化、双方熟悉程度及其既有邮件习惯。"

    if "Indonesia" in region:
        if re.search(r"\b(Pak|Bu)\b", source, re.IGNORECASE):
            note = (
                "检测到 Pak 或 Bu。它们是印度尼西亚常见尊称形式，"
                "使用前仍应确认对方的称谓习惯；不要由系统自行推断或替换。"
            )
        else:
            note = (
                "正式国际商务邮件中，如已知英文姓名，通常可优先使用 Dear + Name。"
                "不要未经确认自动添加 Pak、Bu、Mr. 或 Ms."
            )
    elif "Malaysia" in region:
        title_match = re.search(
            r"\b(Dato'|Datuk|Tan Sri|Dr\.?)\b",
            source,
            re.IGNORECASE,
        )
        if title_match:
            note = (
                "检测到用户提供的正式头衔。通常建议准确保留，并参考对方邮件签名"
                "核对拼写和使用方式。"
            )
        else:
            note = (
                "如无法确认 Dato'、Datuk、Tan Sri、Dr. 等正式头衔，"
                "可优先使用 Dear + Full Name，并核对对方正式资料。"
            )
    elif "Singapore" in region:
        note = (
            "新加坡国际商务场景中通常可使用 Dear + First Name 或 Full Name；"
            "首次正式联系可优先使用全名，熟悉后再结合对方习惯调整。"
        )
    elif "Vietnam" in region:
        note = (
            "越南姓名顺序可能与英语习惯不同，不要自动判断姓或名；"
            "通常建议参考对方邮件签名或自我介绍中的称呼方式。"
        )
    elif "Türkiye" in region:
        note = (
            "不要根据土耳其姓名自动判断性别或称谓。正式初次联系可使用全名，"
            "或在已知时使用准确职位。"
        )
    elif "Europe" in region or "United States" in region:
        note = (
            "首次正式联系可考虑 Dear + Full Name。除非偏好明确，"
            "不要自动添加 Mr. 或 Ms.；建立工作关系后可参考对方邮件习惯。"
        )
    elif "Middle East" in region:
        note = (
            "中东地区称谓和正式头衔差异较大，通常建议保留用户已确认的正式头衔，"
            "不根据姓名推断宗教、族裔或身份。"
        )
    elif "China" in region:
        note = (
            "跨境英文沟通中可考虑 Dear + Full Name 或已确认职位；"
            "仍应参考对方英文签名和双方熟悉程度。"
        )
    elif "Other" in region and custom_region.strip():
        note = (
            f"已选择 {custom_region.strip()}。暂无专门规则，通常建议使用全名或"
            "已确认职位，并结合对方公司文化和既有邮件习惯。"
        )

    return LocalizationGuidance(
        recommended_salutation=salutation,
        salutation_risk=risk,
        politeness_guidance=politeness,
        cross_cultural_note=note,
    )
