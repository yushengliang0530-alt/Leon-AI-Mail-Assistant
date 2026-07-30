import base64
import hashlib
import html
import json
import time

import streamlit as st

from access_control import (
    configured_access_code,
    runtime_environment,
    verify_access_code,
)
from ai_service import AIServiceError, DeepSeekEmailService, SenderDetails
from communication_analysis_service import CommunicationAnalysis
from config import (
    APP_VERSION_LABEL,
    APP_VERSION,
    MAX_INPUT_CHARS,
    PRODUCT_NAME_EN,
    PRODUCT_NAME_ZH,
    load_settings,
)
from content_risk_service import (
    ADVISORY_NOTICE,
    RiskAssessment,
    analyze_content_risk,
)
from examples import BUSINESS_EXAMPLES, BusinessExample
from localization_service import (
    COUNTRY_REGION_OPTIONS,
    LocalizationGuidance,
    build_localization_guidance,
)
from services.scenario_service import ScenarioService
from ui.pages.compose_supplier import render_supplier_workflow
from ui.pages.home import render_home
from ui.state import get_home_view, initialize_home_state, return_to_home

st.set_page_config(
    page_title=f"Leon AI · {PRODUCT_NAME_ZH} · {APP_VERSION_LABEL}",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    :root {
        --ink: #10213b;
        --muted: #66758a;
        --line: #dce3ec;
        --paper: #ffffff;
        --canvas: #f4f7fb;
        --blue: #2457d6;
        --blue-dark: #1945b5;
        --blue-soft: #edf3ff;
    }

    .stApp {
        background:
            radial-gradient(circle at 92% 5%, rgba(36, 87, 214, 0.08), transparent 24rem),
            var(--canvas);
        color: var(--ink);
    }

    header[data-testid="stHeader"] {
        display: none;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 880px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 0.72rem;
        margin-bottom: 3.2rem;
    }

    .brand-mark {
        width: 2.1rem;
        height: 2.1rem;
        display: grid;
        place-items: center;
        border-radius: 0.58rem;
        background: var(--ink);
        color: white;
        font-family: Georgia, serif;
        font-size: 1rem;
        letter-spacing: -0.04em;
        box-shadow: 0 8px 24px rgba(16, 33, 59, 0.18);
    }

    .brand-name {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .hero {
        border-left: 3px solid var(--blue);
        padding-left: 1.55rem;
        margin-bottom: 2.3rem;
    }

    .eyebrow {
        margin-bottom: 0.65rem;
        color: var(--blue);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .hero h1 {
        margin: 0;
        color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 760;
        letter-spacing: -0.035em;
        line-height: 1.12;
    }

    .hero p {
        max-width: 39rem;
        margin: 0.9rem 0 0;
        color: #455773;
        font-size: 0.98rem;
        line-height: 1.65;
    }

    .hero .en-subtitle {
        display: block;
        margin-top: 0.32rem;
        color: #8a97a8;
        font-size: 0.79rem;
        font-weight: 500;
        letter-spacing: 0.005em;
    }

    .mode-intro {
        margin: -0.55rem 0 1.25rem;
        padding: 0 0.15rem;
        color: #40536f;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .mode-intro .en,
    .field-label .en,
    .result-note .en,
    .footer-note .en {
        display: block;
        margin-top: 0.12rem;
        color: #8a97a8;
        font-size: 0.74rem;
        font-weight: 500;
    }

    .field-label {
        margin: 0.72rem 0 0.36rem;
        color: #263955;
        font-size: 0.86rem;
        font-weight: 690;
        line-height: 1.35;
    }

    .field-label .status {
        margin-left: 0.3rem;
        color: #8a97a8;
        font-size: 0.72rem;
        font-weight: 500;
    }

    .tone-note {
        margin: -0.25rem 0 0.85rem;
        padding: 0.68rem 0.8rem;
        border-left: 2px solid #b7c8ef;
        background: #f6f8fd;
        color: #51637d;
        font-size: 0.78rem;
        line-height: 1.55;
    }

    .tone-note .en {
        color: #8a97a8;
        font-size: 0.7rem;
    }

    .button-helper {
        margin: -0.35rem 0 0.2rem;
        color: #9aa5b4;
        font-size: 0.7rem;
        text-align: center;
    }

    .result-note {
        margin: -0.38rem 0 1rem;
        color: #65758b;
        font-size: 0.8rem;
    }

    .section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 0.15rem 0 1rem;
    }

    .section-heading h2 {
        margin: 0;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 750;
        letter-spacing: -0.015em;
    }

    .section-heading span {
        color: #8a97a8;
        font-size: 0.76rem;
    }

    div[data-testid="stForm"] {
        padding: 1.55rem 1.6rem 1.45rem;
        border: 1px solid rgba(213, 222, 234, 0.95);
        border-radius: 1.05rem;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 18px 45px rgba(22, 45, 80, 0.07);
    }

    div[data-testid="stSegmentedControl"] {
        margin-bottom: 1.4rem;
    }

    div[data-testid="stSegmentedControl"] > div {
        padding: 0.3rem;
        border: 1px solid var(--line);
        border-radius: 0.8rem;
        background: rgba(255, 255, 255, 0.84);
    }

    div[data-testid="stExpander"] {
        margin: 0.8rem 0 1rem;
        border-color: var(--line);
        border-radius: 0.72rem;
        background: #f8fafe;
    }

    div[data-testid="stExpander"] summary p {
        color: #263955;
        font-size: 0.86rem;
        font-weight: 680;
    }

    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextArea"] textarea {
        border-color: var(--line);
        border-radius: 0.68rem;
        background: #fbfcfe;
    }

    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--blue);
        box-shadow: 0 0 0 3px rgba(36, 87, 214, 0.11);
    }

    div[data-testid="stWidgetLabel"] p {
        color: #263955;
        font-size: 0.84rem;
        font-weight: 650;
    }

    div[role="radiogroup"] {
        gap: 0.5rem;
    }

    div[role="radiogroup"] label {
        padding: 0.48rem 0.72rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: white;
    }

    div[data-testid="stFormSubmitButton"] button {
        min-height: 3rem;
        border: 0;
        border-radius: 0.7rem;
        background: var(--blue);
        box-shadow: 0 10px 24px rgba(36, 87, 214, 0.2);
        font-weight: 720;
        letter-spacing: 0.01em;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: var(--blue-dark);
        transform: translateY(-1px);
    }

    .result-wrap {
        margin-top: 2.2rem;
        padding-top: 2.1rem;
        border-top: 1px solid var(--line);
    }

    .result-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.34rem 0.64rem;
        border-radius: 999px;
        background: #eaf7f1;
        color: #18724f;
        font-size: 0.73rem;
        font-weight: 700;
    }

    .empty-state {
        margin-top: 2rem;
        padding: 2rem;
        border: 1px dashed #c9d3e0;
        border-radius: 0.9rem;
        background: rgba(255, 255, 255, 0.55);
        color: var(--muted);
        text-align: center;
        font-size: 0.9rem;
    }

    .footer-note {
        margin-top: 2.4rem;
        color: #8995a5;
        font-size: 0.76rem;
        text-align: center;
    }

    .service-status {
        margin: 1rem 0 0;
        padding: 0.9rem 1rem;
        border: 1px solid #dce3ec;
        border-radius: 0.8rem;
        background: rgba(255, 255, 255, 0.76);
        color: #52627a;
        font-size: 0.76rem;
        line-height: 1.7;
    }

    .service-status .title {
        margin-bottom: 0.28rem;
        color: #263955;
        font-size: 0.82rem;
        font-weight: 720;
    }

    .service-status .row {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        border-top: 1px solid rgba(220, 227, 236, 0.72);
        padding-top: 0.28rem;
        margin-top: 0.28rem;
    }

    .service-status .value {
        color: #263955;
        font-weight: 650;
        text-align: right;
    }

    .version-badge {
        display: inline-flex;
        align-items: center;
        margin-left: 0.55rem;
        padding: 0.18rem 0.48rem;
        border: 1px solid #b9c9ef;
        border-radius: 999px;
        background: #edf3ff;
        color: #2457d6;
        font-size: 0.65rem;
        font-weight: 750;
        vertical-align: middle;
    }

    .capability-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0 0 1rem;
    }

    .capability-card {
        padding: 0.9rem;
        border: 1px solid #dce3ec;
        border-radius: 0.8rem;
        background: rgba(255, 255, 255, 0.78);
    }

    .capability-card strong {
        display: block;
        color: #20344f;
        font-size: 0.82rem;
    }

    .capability-card span {
        display: block;
        margin-top: 0.3rem;
        color: #6f7e92;
        font-size: 0.72rem;
        line-height: 1.5;
    }

    .analysis-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
        margin: 0.7rem 0;
    }

    .analysis-item {
        padding: 0.72rem 0.8rem;
        border: 1px solid #e0e6ee;
        border-radius: 0.7rem;
        background: #fbfcfe;
    }

    .analysis-item .label {
        color: #7b8798;
        font-size: 0.68rem;
    }

    .analysis-item .value {
        margin-top: 0.2rem;
        color: #263955;
        font-size: 0.8rem;
        line-height: 1.48;
    }

    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.3rem 1rem 2.5rem;
        }

        .brand-row {
            margin-bottom: 2.2rem;
        }

        .hero {
            padding-left: 1rem;
        }

        div[data-testid="stForm"] {
            padding: 1.2rem 1rem;
        }

        .capability-grid,
        .analysis-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


GENERATE_TONES = {
    "正式 · Formal": (
        "Formal",
        "适合客户、领导及正式商务沟通。",
    ),
    "友好 · Friendly": (
        "Friendly",
        "适合熟悉的同事、合作伙伴及一般沟通。",
    ),
    "明确强硬 · Strong": (
        "Strong",
        "适合催办、纠正问题或明确责任，同时保持专业和礼貌。",
    ),
    "高管简洁 · Executive": (
        "Executive",
        "表达简短、重点清晰，适合管理层沟通。",
    ),
}

IMPROVE_TONES = {
    "正式 · Formal": ("Formal", "使表达严谨、完整，适合正式商务场景。"),
    "友好 · Friendly": ("Friendly", "使表达自然、友善，适合日常合作沟通。"),
    "简洁 · Concise": ("Concise", "压缩冗余表达，保留关键信息和行动要求。"),
    "高管简洁 · Executive": (
        "Executive",
        "突出结论和下一步行动，适合管理层沟通。",
    ),
}


def field_label(
    chinese: str,
    english: str,
    status: str = "",
) -> None:
    status_html = f'<span class="status">{html.escape(status)}</span>' if status else ""
    st.markdown(
        (
            f'<div class="field-label">{html.escape(chinese)}{status_html}'
            f'<span class="en">{html.escape(english)}</span></div>'
        ),
        unsafe_allow_html=True,
    )


def sender_fields() -> tuple[str, str, str, str]:
    """Render the shared sender fields inside the active form."""
    with st.expander("发件人与邮件签名 · Sender & Signature", expanded=False):
        field_label("发件人姓名", "Sender Name", "可选")
        sender_name = st.text_input(
            "发件人姓名",
            placeholder="例如：David Chen",
            key="shared_sender_name",
            label_visibility="collapsed",
        )
        field_label("职位", "Job Title", "可选")
        job_title = st.text_input(
            "职位",
            placeholder="例如：Project Coordinator",
            key="shared_job_title",
            label_visibility="collapsed",
        )
        field_label("公司", "Company", "可选")
        company = st.text_input(
            "公司",
            placeholder="例如：ABC Engineering Co., Ltd.",
            key="shared_company",
            label_visibility="collapsed",
        )
        field_label("联系方式", "Contact Information", "可选")
        contact_information = st.text_input(
            "联系方式",
            placeholder="例如：david.chen@example.com",
            key="shared_contact_information",
            label_visibility="collapsed",
        )
    return sender_name, job_title, company, contact_information


def copy_button(
    chinese_label: str,
    english_label: str,
    success_message: str,
    value: str,
    key: str,
) -> None:
    encoded_value = base64.b64encode(value.encode("utf-8")).decode("ascii")
    safe_chinese_label = html.escape(chinese_label)
    safe_english_label = html.escape(english_label)
    safe_success_message = html.escape(success_message)
    st.iframe(
        f"""
        <button id="{key}" onclick="copyText()" style="
            width:100%;
            height:40px;
            border:1px solid #d7e0eb;
            border-radius:9px;
            background:#ffffff;
            color:#263955;
            font:600 13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            cursor:pointer;
            transition:all .18s ease;
        ">
            <span>{safe_chinese_label}</span>
            <span style="margin-left:6px;color:#8a97a8;font-size:11px;font-weight:500">
                {safe_english_label}
            </span>
        </button>
        <script>
        async function copyText() {{
            const button = document.getElementById({json.dumps(key)});
            try {{
                const bytes = Uint8Array.from(
                    atob({json.dumps(encoded_value)}),
                    character => character.charCodeAt(0)
                );
                const text = new TextDecoder().decode(bytes);
                await navigator.clipboard.writeText(text);
                button.textContent = {json.dumps(safe_success_message)};
                button.style.color = "#18724f";
                button.style.borderColor = "#a9dcc7";
                setTimeout(() => {{
                    button.innerHTML = `
                        <span>{safe_chinese_label}</span>
                        <span style="margin-left:6px;color:#8a97a8;font-size:11px;font-weight:500">
                            {safe_english_label}
                        </span>`;
                    button.style.color = "#263955";
                    button.style.borderColor = "#d7e0eb";
                }}, 1600);
            }} catch (error) {{
                button.textContent = "复制失败，请手动选择内容复制。";
            }}
        }}
        </script>
        """,
        height=46,
        width="stretch",
    )


def read_streamlit_secrets() -> dict[str, str]:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def sender_details(
    name: str,
    job_title: str,
    company: str,
    contact_information: str,
) -> SenderDetails:
    return SenderDetails(
        name=name,
        job_title=job_title,
        company=company,
        contact_information=contact_information,
    )


def region_selector(prefix: str) -> tuple[str, str]:
    field_label("收件人所在国家或地区", "Recipient Country or Region")
    region = st.selectbox(
        "收件人所在国家或地区",
        COUNTRY_REGION_OPTIONS,
        key=f"{prefix}_country_region",
        label_visibility="collapsed",
    )
    custom_region = ""
    if region == "其他 / Other":
        field_label("请填写国家或地区", "Please specify the country or region", "可选")
        custom_region = st.text_input(
            "请填写国家或地区",
            key=f"{prefix}_custom_region",
            label_visibility="collapsed",
        )
    return region, custom_region


def render_risk_assessment(assessment: RiskAssessment) -> None:
    st.markdown("#### 信息安全提示 · Sensitive Information Check")
    if assessment.risk_level == "high":
        st.error(f"高风险提示：{assessment.summary}")
    elif assessment.risk_level == "medium":
        st.warning(f"注意：{assessment.summary}")
    else:
        st.success(f"普通提示：{assessment.summary}")
    for item in assessment.risk_items:
        st.markdown(
            f"- **{item.category}**：{item.description} {item.suggestion}"
        )
    st.caption(ADVISORY_NOTICE)


def render_localization_guidance(guidance: LocalizationGuidance) -> None:
    with st.expander(
        "称谓与本地化建议 · Salutation & Localization Guidance",
        expanded=False,
    ):
        st.markdown(f"**推荐称谓**：{guidance.recommended_salutation}")
        st.markdown(f"**称谓风险**：{guidance.salutation_risk}")
        st.markdown(f"**礼貌程度**：{guidance.politeness_guidance}")
        st.markdown(f"**跨文化提醒**：{guidance.cross_cultural_note}")
        st.caption("以上内容仅为辅助建议，请结合对方公司文化和双方熟悉程度。")


def localization_context(guidance: LocalizationGuidance) -> str:
    return (
        f"Recommended salutation: {guidance.recommended_salutation}\n"
        f"Salutation risk: {guidance.salutation_risk}\n"
        f"Politeness guidance: {guidance.politeness_guidance}\n"
        f"Cross-cultural note: {guidance.cross_cultural_note}"
    )


def render_communication_analysis(analysis: CommunicationAnalysis) -> None:
    st.markdown(
        """
        <div class="result-wrap">
            <div class="section-heading">
                <h2>商务沟通分析 <small style="color:#8a97a8;font-size:.7rem;font-weight:500">Business Communication Analysis</small></h2>
                <span>辅助提示 · 人工确认</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rows = (
        ("沟通目的", analysis.purpose),
        ("行动要求", analysis.action_required),
        ("截止时间", analysis.deadline),
        ("商务语气", analysis.tone),
        ("承诺风险", analysis.commitment_risk),
        ("歧义风险", analysis.ambiguity_risk),
        ("本地化提示", analysis.localization_note),
    )
    cards = "".join(
        (
            '<div class="analysis-item">'
            f'<div class="label">{html.escape(label)}</div>'
            f'<div class="value">{html.escape(value)}</div>'
            "</div>"
        )
        for label, value in rows
    )
    st.markdown(f'<div class="analysis-grid">{cards}</div>', unsafe_allow_html=True)
    if analysis.improvement_suggestions:
        st.markdown("**改进建议**")
        for index, suggestion in enumerate(
            analysis.improvement_suggestions,
            start=1,
        ):
            st.markdown(f"{index}. {suggestion}")
    if not analysis.available:
        st.warning("暂时无法完成完整分析，请人工检查邮件内容。")


def _content_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def record_high_risk_confirmation(
    source_key: str,
    checkbox_key: str,
    digest_key: str,
) -> None:
    if st.session_state.get(checkbox_key):
        source = str(st.session_state.get(source_key, ""))
        st.session_state[digest_key] = _content_digest(source)
    else:
        st.session_state[digest_key] = ""


def apply_example(example: BusinessExample) -> None:
    st.session_state.writing_mode = example.mode
    if example.mode == "写英文邮件":
        st.session_state.saved_generate_request = example.source_text
        st.session_state.generate_request = example.source_text
        st.session_state.saved_generate_tone_choice = example.tone_choice
        st.session_state.generate_tone_choice = example.tone_choice
        st.session_state.generate_country_region = example.country_region
    else:
        st.session_state.saved_improve_original_email = example.source_text
        st.session_state.improve_original_email = example.source_text
        st.session_state.saved_improve_tone_choice = example.tone_choice
        st.session_state.improve_tone_choice = example.tone_choice
        st.session_state.improve_country_region = example.country_region


def render_examples() -> None:
    with st.expander("案例演示 · Examples", expanded=False):
        for example in BUSINESS_EXAMPLES:
            st.markdown(f"#### {example.title}")
            st.markdown(f"**使用场景**：{example.title}")
            st.markdown(f"**输入示例**：{example.source_text}")
            st.markdown(
                f"**推荐语气**：{example.tone_choice}　"
                f"**国家或地区**：{example.country_region}"
            )
            st.markdown(f"**预期效果**：{example.expected_result}")
            if example.localization_note:
                st.caption(example.localization_note)
            st.button(
                "使用此案例 · Use This Example",
                key=f"use_example_{example.key}",
                on_click=apply_example,
                args=(example,),
            )
            st.divider()


runtime_secrets = read_streamlit_secrets()
settings = load_settings(runtime_secrets)
app_access_code = configured_access_code(runtime_secrets)


def submit_access_code() -> None:
    provided_code = str(st.session_state.get("access_code_input", ""))
    is_valid = verify_access_code(app_access_code, provided_code)
    st.session_state.access_granted = is_valid
    st.session_state.access_code_error = not is_valid
    st.session_state.access_code_input = ""


if "access_granted" not in st.session_state:
    st.session_state.access_granted = False
if "access_code_error" not in st.session_state:
    st.session_state.access_code_error = False

if app_access_code and not st.session_state.access_granted:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">LA</div>
            <div class="brand-name">Leon AI</div>
        </div>
        <div class="hero">
            <div class="eyebrow">INVITED TESTING · 受邀测试</div>
            <h1>Leon AI 内部测试版</h1>
            <p>本版本目前仅面向受邀测试用户，请输入访问码继续。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_input(
        "测试访问码",
        type="password",
        key="access_code_input",
        placeholder="请输入测试访问码",
    )
    st.button(
        "进入应用",
        type="primary",
        use_container_width=True,
        on_click=submit_access_code,
    )
    if st.session_state.access_code_error:
        st.error("访问码不正确，请重新输入。")
    st.caption("此访问码仅用于小范围测试访问控制，不是正式安全认证。")
    st.stop()

try:
    current_app_url = str(st.context.url)
except Exception:
    current_app_url = ""
environment_label = runtime_environment(current_app_url)
access_protection_label = (
    "已启用" if app_access_code else "测试访问保护尚未启用"
)


SESSION_DEFAULTS = {
    "writing_mode": "写英文邮件",
    "generated": False,
    "email_subject": "",
    "email_body": "",
    "generated_analysis": CommunicationAnalysis(),
    "improved": False,
    "improved_subject": "",
    "improved_body": "",
    "improved_analysis": CommunicationAnalysis(),
    "shared_sender_name": "",
    "shared_job_title": "",
    "shared_company": "",
    "shared_contact_information": "",
    "saved_generate_recipient": "",
    "saved_generate_topic": "",
    "saved_generate_request": "",
    "saved_generate_tone_choice": "正式 · Formal",
    "saved_improve_original_email": "",
    "saved_improve_tone_choice": "正式 · Formal",
    "generate_country_region": COUNTRY_REGION_OPTIONS[0],
    "generate_custom_region": "",
    "improve_country_region": COUNTRY_REGION_OPTIONS[0],
    "improve_custom_region": "",
    "generate_high_risk_confirmed": False,
    "generate_confirmed_digest": "",
    "improve_high_risk_confirmed": False,
    "improve_confirmed_digest": "",
    "request_in_progress": False,
    "deepseek_connected": False,
    "last_request_duration": None,
    "last_usage_tokens": None,
}

for state_key, default_value in SESSION_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

initialize_home_state()


PAGE_WIDGETS = {
    "generate_recipient": "saved_generate_recipient",
    "generate_topic": "saved_generate_topic",
    "generate_request": "saved_generate_request",
    "generate_tone_choice": "saved_generate_tone_choice",
    "improve_original_email": "saved_improve_original_email",
    "improve_tone_choice": "saved_improve_tone_choice",
}


def preserve_page_inputs() -> None:
    """Keep page-specific fields when the user switches writing modes."""
    for widget_key, saved_key in PAGE_WIDGETS.items():
        if widget_key in st.session_state:
            st.session_state[saved_key] = st.session_state[widget_key]


def restore_page_inputs(widget_keys: list[str]) -> None:
    for widget_key in widget_keys:
        saved_key = PAGE_WIDGETS[widget_key]
        if widget_key not in st.session_state:
            st.session_state[widget_key] = st.session_state[saved_key]


current_home_view = get_home_view()

if current_home_view == "home":
    home_service_status = "已配置" if settings.is_configured else "未配置"
    render_home(
        ai_service_status=home_service_status,
        environment_label=environment_label,
        access_protection_label=access_protection_label,
    )
    st.stop()

if current_home_view == "compose_supplier":
    render_supplier_workflow(
        scenario_service=ScenarioService(DeepSeekEmailService(settings)),
    )
    st.stop()

st.button(
    "← 返回工作台",
    key="legacy__return_home",
    on_click=return_to_home,
)
st.caption("V1.0 兼容功能 · 当前打开：优化已有草稿")


st.markdown(
    f"""
    <div class="brand-row">
        <div class="brand-mark">LA</div>
        <div class="brand-name">Leon AI <span class="version-badge">V{APP_VERSION}</span></div>
    </div>
    <div class="hero">
        <div class="eyebrow">BUSINESS COMMUNICATION · 商务沟通</div>
        <h1>{PRODUCT_NAME_ZH}</h1>
        <p>
            帮助职场人士更安全、专业、高效地完成国际商务沟通。
            <span class="en-subtitle">{PRODUCT_NAME_EN}<br>Create safer, clearer and more professional business communication.</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-heading">
        <h2>核心功能 <small style="color:#8a97a8;font-size:.7rem;font-weight:500">Core Capabilities</small></h2>
    </div>
    <div class="capability-grid">
        <div class="capability-card"><strong>商务邮件生成</strong><span>根据中文业务需求生成结构完整的英文商务邮件。</span></div>
        <div class="capability-card"><strong>英文表达优化</strong><span>修正语法、中式英语、逻辑结构和商务语气。</span></div>
        <div class="capability-card"><strong>沟通风险分析</strong><span>提示可能存在的敏感信息、承诺风险和表达歧义。</span></div>
        <div class="capability-card"><strong>本地化沟通建议</strong><span>提供称谓、礼貌程度和跨文化表达辅助建议。</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.info(
    "安全提醒：请勿输入密码、身份证件、银行账号、API Key 或其他敏感凭证。"
    "风险提示仅供辅助，最终请人工确认。"
)

active_page = st.segmented_control(
    "写作模式",
    ["写英文邮件", "优化英文邮件"],
    key="writing_mode",
    on_change=preserve_page_inputs,
    label_visibility="collapsed",
)

if active_page == "写英文邮件":
    restore_page_inputs(
        [
            "generate_recipient",
            "generate_topic",
            "generate_request",
            "generate_tone_choice",
        ]
    )
    st.markdown(
        """
        <div class="mode-intro">
            根据中文需求生成完整的英文商务邮件。
            <span class="en">Generate Email · Create a complete business email from your Chinese brief.</span>
        </div>
        <div class="section-heading">
            <h2>写英文商务邮件</h2>
            <span>标注“必填”的内容不可为空</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    country_region, custom_region = region_selector("generate")

    with st.form("email_form", border=True):
        field_label("收件人", "Recipient", "可选")
        recipient = st.text_input(
            "收件人",
            placeholder="例如：Mr. Smith、项目团队或供应商名称",
            key="generate_recipient",
            label_visibility="collapsed",
        )
        field_label("邮件主题", "Email Subject", "可选")
        topic = st.text_input(
            "邮件主题",
            placeholder="例如：交付计划调整",
            key="generate_topic",
            label_visibility="collapsed",
        )
        field_label("中文需求", "Chinese Brief", "必填")
        request = st.text_area(
            "中文需求",
            placeholder="请用中文说明邮件背景、需要传达的信息、希望对方采取的行动以及重要时间节点。",
            height=170,
            key="generate_request",
            label_visibility="collapsed",
        )
        field_label("邮件语气", "Tone")
        tone_choice = st.radio(
            "邮件语气",
            list(GENERATE_TONES),
            horizontal=True,
            key="generate_tone_choice",
            label_visibility="collapsed",
        )
        tone, tone_help = GENERATE_TONES[tone_choice]
        st.markdown(
            (
                f'<div class="tone-note">{html.escape(tone_help)}'
                f'<span class="en">{html.escape(tone)}</span></div>'
            ),
            unsafe_allow_html=True,
        )
        sender_name, job_title, company, contact_information = sender_fields()
        submitted = st.form_submit_button(
            "生成英文邮件",
            key="legacy__generate_submit",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.request_in_progress,
        )
        st.markdown(
            '<div class="button-helper">Generate Email</div>',
            unsafe_allow_html=True,
        )

    risk_assessment = analyze_content_risk(request)
    guidance = build_localization_guidance(
        recipient=recipient,
        country_region=country_region,
        custom_region=custom_region,
        tone=tone,
        source_text=request,
    )
    high_risk_confirmed = False
    if request.strip():
        render_risk_assessment(risk_assessment)
        if risk_assessment.requires_confirmation:
            st.checkbox(
                "我已检查并确认内容可以提交给 AI 处理。",
                key="generate_high_risk_confirmed",
                on_change=record_high_risk_confirmation,
                args=(
                    "generate_request",
                    "generate_high_risk_confirmed",
                    "generate_confirmed_digest",
                ),
            )
            high_risk_confirmed = (
                st.session_state.generate_high_risk_confirmed
                and st.session_state.generate_confirmed_digest
                == _content_digest(request)
            )
        render_localization_guidance(guidance)

    if submitted:
        preserve_page_inputs()
        if not request.strip():
            st.error("请先填写中文需求。")
        elif len(request) > MAX_INPUT_CHARS:
            st.error(f"中文需求不能超过 {MAX_INPUT_CHARS} 个字符。")
        elif risk_assessment.requires_confirmation and not high_risk_confirmed:
            st.error("检测到高风险内容。请先完成人工检查并勾选确认后再提交。")
        elif st.session_state.request_in_progress:
            st.warning("当前请求正在处理中，请稍候。")
        else:
            st.session_state.request_in_progress = True
            request_started_at = time.perf_counter()
            try:
                with st.spinner("正在生成英文邮件，请稍候……"):
                    result = DeepSeekEmailService(settings).generate_email(
                        recipient=recipient,
                        requested_subject=topic,
                        chinese_brief=request,
                        tone=tone,
                        country_region=(
                            custom_region.strip()
                            if country_region == "其他 / Other"
                            else country_region
                        ),
                        localization_context=localization_context(guidance),
                        sender=sender_details(
                            sender_name,
                            job_title,
                            company,
                            contact_information,
                        ),
                    )
                st.session_state.email_subject = result.subject
                st.session_state.email_body = result.body
                st.session_state.subject_editor = result.subject
                st.session_state.body_editor = result.body
                st.session_state.generated_analysis = (
                    result.communication_analysis
                )
                st.session_state.generated = True
                st.session_state.deepseek_connected = True
                st.session_state.last_request_duration = (
                    time.perf_counter() - request_started_at
                )
                st.session_state.last_usage_tokens = result.usage_tokens
            except AIServiceError as exc:
                st.error(exc.user_message)
            finally:
                st.session_state.request_in_progress = False

    if st.session_state.generated:
        if "subject_editor" not in st.session_state:
            st.session_state.subject_editor = st.session_state.email_subject
        if "body_editor" not in st.session_state:
            st.session_state.body_editor = st.session_state.email_body
        render_communication_analysis(st.session_state.generated_analysis)
        st.markdown(
            """
            <div class="result-wrap">
                <div class="section-heading">
                    <h2>您的英文邮件 <small style="color:#8a97a8;font-size:.7rem;font-weight:500">Your Email</small></h2>
                    <span class="result-badge">● 预览已生成 · Preview Ready</span>
                </div>
            </div>
            <div class="result-note">
                您可以在复制前直接修改生成结果。
                <span class="en">You can edit the result before copying.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        field_label("邮件主题", "Subject")
        st.session_state.email_subject = st.text_input(
            "邮件主题",
            key="subject_editor",
            label_visibility="collapsed",
        )
        copy_button(
            "复制主题",
            "Copy Subject",
            "邮件主题已复制。",
            st.session_state.email_subject,
            "copy-subject",
        )

        field_label("邮件正文", "Email Body")
        st.session_state.email_body = st.text_area(
            "邮件正文",
            height=310,
            key="body_editor",
            label_visibility="collapsed",
        )
        copy_button(
            "复制正文",
            "Copy Body",
            "邮件正文已复制。",
            st.session_state.email_body,
            "copy-body",
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                生成后的英文邮件主题和正文将显示在这里。<br>
                <span style="color:#98a3b2;font-size:.72rem">Your generated email will appear here.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    restore_page_inputs(
        [
            "improve_original_email",
            "improve_tone_choice",
        ]
    )
    st.markdown(
        """
        <div class="mode-intro">
            优化已经写好的英文邮件，使表达更加专业、自然。
            <span class="en">Improve Email · Refine an existing email for clearer, more natural business English.</span>
        </div>
        <div class="section-heading">
            <h2>优化英文商务邮件</h2>
            <span>标注“必填”的内容不可为空</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    improve_country_region, improve_custom_region = region_selector("improve")

    with st.form("improve_form", border=True):
        field_label("原始英文邮件", "Original English Email", "必填")
        original_email = st.text_area(
            "原始英文邮件",
            placeholder="请粘贴需要优化的英文邮件全文。",
            height=240,
            key="improve_original_email",
            label_visibility="collapsed",
        )
        field_label("目标语气", "Target Tone")
        improve_tone_choice = st.radio(
            "目标语气",
            list(IMPROVE_TONES),
            horizontal=True,
            key="improve_tone_choice",
            label_visibility="collapsed",
        )
        improve_tone, improve_tone_help = IMPROVE_TONES[improve_tone_choice]
        st.markdown(
            (
                f'<div class="tone-note">{html.escape(improve_tone_help)}'
                f'<span class="en">{html.escape(improve_tone)}</span></div>'
            ),
            unsafe_allow_html=True,
        )
        sender_name, job_title, company, contact_information = sender_fields()
        improve_submitted = st.form_submit_button(
            "优化英文邮件",
            key="legacy__improve_submit",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.request_in_progress,
        )
        st.markdown(
            '<div class="button-helper">Improve Email</div>',
            unsafe_allow_html=True,
        )

    improve_risk_assessment = analyze_content_risk(original_email)
    improve_guidance = build_localization_guidance(
        recipient="",
        country_region=improve_country_region,
        custom_region=improve_custom_region,
        tone=improve_tone,
        source_text=original_email,
    )
    improve_high_risk_confirmed = False
    if original_email.strip():
        render_risk_assessment(improve_risk_assessment)
        if improve_risk_assessment.requires_confirmation:
            st.checkbox(
                "我已检查并确认内容可以提交给 AI 处理。",
                key="improve_high_risk_confirmed",
                on_change=record_high_risk_confirmation,
                args=(
                    "improve_original_email",
                    "improve_high_risk_confirmed",
                    "improve_confirmed_digest",
                ),
            )
            improve_high_risk_confirmed = (
                st.session_state.improve_high_risk_confirmed
                and st.session_state.improve_confirmed_digest
                == _content_digest(original_email)
            )
        render_localization_guidance(improve_guidance)

    if improve_submitted:
        preserve_page_inputs()
        if not original_email.strip():
            st.error("请先粘贴需要优化的英文邮件。")
        elif len(original_email) > MAX_INPUT_CHARS:
            st.error(f"原始英文邮件不能超过 {MAX_INPUT_CHARS} 个字符。")
        elif (
            improve_risk_assessment.requires_confirmation
            and not improve_high_risk_confirmed
        ):
            st.error("检测到高风险内容。请先完成人工检查并勾选确认后再提交。")
        elif st.session_state.request_in_progress:
            st.warning("当前请求正在处理中，请稍候。")
        else:
            st.session_state.request_in_progress = True
            request_started_at = time.perf_counter()
            try:
                with st.spinner("正在优化英文邮件，请稍候……"):
                    result = DeepSeekEmailService(settings).improve_email(
                        original_email=original_email,
                        tone=improve_tone,
                        country_region=(
                            improve_custom_region.strip()
                            if improve_country_region == "其他 / Other"
                            else improve_country_region
                        ),
                        localization_context=localization_context(
                            improve_guidance
                        ),
                        sender=sender_details(
                            sender_name,
                            job_title,
                            company,
                            contact_information,
                        ),
                    )
                st.session_state.improved_subject = result.subject
                st.session_state.improved_body = result.body
                st.session_state.improved_subject_editor = result.subject
                st.session_state.improved_body_editor = result.body
                st.session_state.improved_analysis = (
                    result.communication_analysis
                )
                st.session_state.improved = True
                st.session_state.deepseek_connected = True
                st.session_state.last_request_duration = (
                    time.perf_counter() - request_started_at
                )
                st.session_state.last_usage_tokens = result.usage_tokens
            except AIServiceError as exc:
                st.error(exc.user_message)
            finally:
                st.session_state.request_in_progress = False

    if st.session_state.improved:
        if "improved_subject_editor" not in st.session_state:
            st.session_state.improved_subject_editor = st.session_state.improved_subject
        if "improved_body_editor" not in st.session_state:
            st.session_state.improved_body_editor = st.session_state.improved_body
        render_communication_analysis(st.session_state.improved_analysis)
        st.markdown(
            """
            <div class="result-wrap">
                <div class="section-heading">
                    <h2>您的英文邮件 <small style="color:#8a97a8;font-size:.7rem;font-weight:500">Your Email</small></h2>
                    <span class="result-badge">● 预览已生成 · Preview Ready</span>
                </div>
            </div>
            <div class="result-note">
                您可以在复制前直接修改生成结果。
                <span class="en">You can edit the result before copying.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        field_label("邮件主题", "Subject")
        st.session_state.improved_subject = st.text_input(
            "邮件主题",
            key="improved_subject_editor",
            label_visibility="collapsed",
        )
        copy_button(
            "复制主题",
            "Copy Subject",
            "邮件主题已复制。",
            st.session_state.improved_subject,
            "copy-improved-subject",
        )

        field_label("邮件正文", "Email Body")
        st.session_state.improved_body = st.text_area(
            "邮件正文",
            height=310,
            key="improved_body_editor",
            label_visibility="collapsed",
        )
        copy_button(
            "复制正文",
            "Copy Body",
            "邮件正文已复制。",
            st.session_state.improved_body,
            "copy-improved-body",
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                优化后的英文邮件主题和正文将显示在这里。<br>
                <span style="color:#98a3b2;font-size:.72rem">Your improved email will appear here.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

render_examples()

with st.expander("如何使用 · How to Use", expanded=False):
    st.markdown(
        """
        1. 选择“写英文邮件”或“优化英文邮件”。
        2. 填写收件人、国家或地区、沟通背景及行动要求。
        3. 检查信息安全和保密提示。
        4. 选择合适的商务语气。
        5. 生成后查看商务沟通分析。
        6. 核对姓名、日期、金额、承诺和项目敏感信息。
        7. 人工确认后再复制发送。

        输入越完整，生成结果通常越准确。建议说明沟通背景、沟通对象、
        需要对方采取的行动、截止时间和语气要求。
        """
    )

with st.expander("使用与安全说明 · Usage & Security Notice", expanded=False):
    st.markdown(
        """
        - 本工具为 AI 辅助商务沟通工具，生成内容可能存在错误或遗漏。
        - 用户必须在发送前人工审核。
        - 不应输入密码、银行账号、身份证件、API Key 或其他敏感凭证。
        - 涉及客户、合同、价格、项目或公司内部信息时，应遵守公司保密制度。
        - 风险提示不代表内容已经通过公司信息安全、法务或管理审批。
        - 系统当前不主动持久化保存用户输入和生成结果。
        - 是否可以使用第三方 AI 服务处理特定信息，应以公司政策为准。
        """
    )

if not settings.is_configured:
    footer_status = f"Leon AI · V{APP_VERSION} · 尚未配置AI服务"
    footer_english = "DeepSeek API Key Not Configured"
    service_state = "未配置"
elif st.session_state.deepseek_connected:
    footer_status = (
        f"Leon AI · V{APP_VERSION} · DeepSeek AI 驱动 · DeepSeek AI已连接"
    )
    footer_english = "Powered by DeepSeek API"
    service_state = "连接成功"
else:
    footer_status = f"Leon AI · V{APP_VERSION} · DeepSeek AI 驱动"
    footer_english = "Powered by DeepSeek API"
    service_state = "已配置"

st.markdown(
    (
        f'<div class="footer-note">{html.escape(footer_status)}'
        f'<span class="en">{html.escape(footer_english)}</span></div>'
    ),
    unsafe_allow_html=True,
)

status_rows = [
    '<div class="row"><span>AI服务</span><span class="value">DeepSeek</span></div>',
    (
        '<div class="row"><span>状态</span>'
        f'<span class="value">{html.escape(service_state)}</span></div>'
    ),
    (
        '<div class="row"><span>运行环境</span>'
        f'<span class="value">{html.escape(environment_label)}</span></div>'
    ),
    (
        '<div class="row"><span>测试访问保护</span>'
        f'<span class="value">{html.escape(access_protection_label)}</span></div>'
    ),
]
if st.session_state.deepseek_connected:
    duration = st.session_state.last_request_duration
    if isinstance(duration, (int, float)):
        status_rows.append(
            '<div class="row"><span>本次生成耗时</span>'
            f'<span class="value">{duration:.2f} 秒</span></div>'
        )
    tokens = st.session_state.last_usage_tokens
    if isinstance(tokens, int):
        status_rows.append(
            '<div class="row"><span>本次用量</span>'
            f'<span class="value">{tokens} tokens</span></div>'
        )

st.markdown(
    (
        '<div class="service-status"><div class="title">AI服务状态</div>'
        + "".join(status_rows)
        + "</div>"
    ),
    unsafe_allow_html=True,
)
