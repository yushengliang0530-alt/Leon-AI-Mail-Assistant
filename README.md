# Leon AI — AI商务沟通优化助手

**AI Business Communication Optimization Assistant · V1.0 · 2026-07-30**

帮助职场人士更安全、专业、高效地完成国际商务沟通。应用保留英文商务邮件生成与优化能力，并增加本地敏感内容提示、本地化称谓建议和商务沟通质量分析。

## 产品定位

Leon AI 面向中国职场人员、外贸人员和工程项目人员。用户可以用中文描述商务需求，或粘贴已有英文邮件，通过 DeepSeek API 获得可编辑的英文邮件和辅助分析。

本工具不是法律、信息安全或管理审批系统。风险提示和 AI 输出均需人工确认。

## 核心功能

- 根据中文需求生成专业英文商务邮件
- 优化已有英文邮件并保留原始事实和立场
- Formal、Friendly、Strong、Executive 商务语气
- 自定义收件人、主题、发件人和动态邮件签名
- 收件人国家或地区、本地化称谓及跨文化沟通建议
- 提交前本地敏感内容检查和高风险确认
- 商务沟通目的、行动要求、截止时间、语气、承诺及歧义分析
- 可编辑及复制邮件主题和正文
- AI 服务状态、耗时和可用 Token 用量
- 四个可一键填充且不会自动调用 AI 的案例
- 可选测试访问码及 Streamlit Community Cloud 支持

## V1.0 新增能力

- 产品定位从“邮件写作”升级为“商务沟通质量分析与优化”
- 增加敏感凭证、个人信息、保密内容和商务承诺的本地规则提示
- 高风险输入默认不提交，用户确认可提交后才调用 AI
- 增加 11 个国家或地区选项及审慎的称谓建议
- 在同一次 DeepSeek 请求中返回结构化商务沟通分析，避免额外分析费用
- 支持非 JSON 邮件正文安全降级，分析不可用时提示人工检查

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
6. 部署后验证访问门禁、生成、优化、状态区和移动端布局。

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

- 当前仍是邀请测试版本，测试访问码不是正式身份认证。
- AI 输出与风险分析可能存在错误、遗漏或误判，发送前必须人工审核。
- 本地化建议不能替代对方名片、邮件签名及正式公司资料。
- 暂无用户注册、支付、额度、历史记录、企业知识库和管理后台。
- DeepSeek 服务可用性和输出质量受账户额度、模型状态与输入完整度影响。
