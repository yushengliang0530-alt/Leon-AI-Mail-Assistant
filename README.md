# Leon AI Copilot — AI商务沟通工作台

**Business Communication Copilot · V2.1**

帮助职场人士通过引导式工作流完成供应商跟进、来信回复、英文草稿优化和发送前检查。用户不需要准备复杂 Prompt，系统会根据已确认的事实生成可编辑、可人工审核的英文商务邮件。

## 产品定位

Leon AI 面向中国职场人员、外贸人员和工程项目人员。V2.1 以 Copilot Workspace 组织任务：系统主动询问必要事实、分析来信诉求、记录用户立场，并检查回复覆盖和发送风险。

本工具不是法律、信息安全或管理审批系统。风险提示和 AI 输出均需人工确认。

## 核心功能

- 催供应商 Guided Workflow：催报价、催交期、更新计划和延期解释
- 收到邮件分析：识别对方目的、要求、问题、日期、责任和风险
- 逐项回复决策：确认接受、部分接受、拒绝、补充信息或暂时无法确认
- 生成完整英文回复，并逐项检查是否覆盖来信问题
- Send Ready 发送前检查：覆盖、行动要求、日期、附件、称谓、语气和承诺风险
- 优化已有英文草稿并保留原始事实和立场
- Formal、Friendly、Strong、Executive 商务语气
- 自定义收件人、主题、发件人和动态邮件签名
- 本地敏感内容检查、高风险确认和本地化称谓建议
- 可编辑及复制邮件主题和正文
- AI 服务状态、耗时和可用 Token 用量
- 可选访问码及 Streamlit Community Cloud 支持

## V2.1 Copilot Workspace Experience Upgrade

- New workspace navigation：从首页直接进入 Reply、Create 或 Improve Workspace
- Redesigned Reply Workspace：来信分析、决策、生成、Coverage 与 Preflight 使用统一流程导航
- Redesigned Create Workspace：场景选择、逐题引导、确认与结果使用同一工作台结构
- Redesigned Improve Workspace：草稿、优化目标和 Before / After 结果对比分离展示
- Unified enterprise design system：统一 Header、Step、Card、状态、加载、错误与响应式规则
- Simplified task flows：移除不必要中间入口，明确每一步的唯一主操作
- 自动化测试使用 Mock 后端，不产生真实 DeepSeek 费用

## 本地运行

推荐 Python 3.12：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

访问 `http://127.0.0.1:8501`。

运行测试：

```bash
python -m unittest discover -s tests -v
```

自动化测试会 mock DeepSeek 客户端，不会产生真实 API 费用。

## 本地 Secrets 配置

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

在本地 `.streamlit/secrets.toml` 中配置：

```toml
DEEPSEEK_API_KEY = "your-deepseek-api-key"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
APP_ACCESS_CODE = "choose-a-test-access-code"
```

`APP_ACCESS_CODE` 可选。不要把 `.streamlit/secrets.toml` 上传到 GitHub，也不要把真实密钥写入 Python 或 Markdown 文件。

## Streamlit Community Cloud 部署

1. 将安全检查后的项目推送到 GitHub。
2. 在 Streamlit Community Cloud 创建应用。
3. 选择仓库、`main` 分支和入口文件 `app.py`。
4. 在高级设置选择 Python 3.12。
5. 在平台 Secrets 设置中粘贴与本地相同结构的 TOML 配置。
6. 部署后验证访问门禁、供应商流程、回复流程、草稿优化、状态区和移动端布局。

`runtime.txt` 同时记录 `python-3.12`；如平台不再以该文件控制版本，请以部署高级设置为准。

## GitHub 上传前检查

```bash
git status --short
git check-ignore .streamlit/secrets.toml .env .venv
git ls-files .streamlit/secrets.toml .env
```

最后一条命令应无输出。仓库中只能提交 `.streamlit/secrets.toml.example`，不能提交真实 Secrets、虚拟环境、缓存或覆盖率文件。

## 安全注意事项

- 用户只有主动点击生成或优化时，输入才会发送至 DeepSeek API。
- 不要输入密码、验证码、银行账号、身份证件、API Key 等敏感凭证。
- 涉及客户、合同、价格、项目或公司内部信息时，应遵守公司保密制度。
- 本地风险检查只提供辅助提示，不能保证发现全部敏感内容。
- 系统当前不主动将输入、分析结果或生成结果写入数据库或项目文件。
- 是否可由第三方 AI 服务处理特定信息，应以用户所在公司的政策为准。
- 页面不会显示 API Key、访问码、系统路径、服务器 IP 或完整内部异常。

## 已知限制

- 可选访问码只是轻量访问保护，不是正式身份认证。
- AI 输出与风险分析可能存在错误、遗漏或误判，发送前必须人工审核。
- 本地化建议不能替代对方名片、邮件签名及正式公司资料。
- 暂无用户注册、支付、额度、历史记录、企业知识库和管理后台。
- 暂不连接 Outlook、Gmail，也不会自动发送邮件。
- 当前场景化新邮件仅正式支持供应商跟进场景。
- DeepSeek 服务可用性和输出质量受账户额度、模型状态与输入完整度影响。
