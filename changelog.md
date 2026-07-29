# Changelog

## Beta 0.9 — 2026-07-29

### Added

- 中文为主、英文为辅的双语界面
- 根据中文需求生成完整英文商务邮件
- 优化用户已有的英文邮件
- Formal、Friendly、Strong、Executive 四种邮件语气
- 自定义收件人、主题和发件人签名
- DeepSeek API 接入
- 邮件主题和正文复制功能
- AI 服务状态、生成耗时和 Token 用量显示
- 测试访问码保护
- Streamlit Community Cloud 云端部署

### Security

- API Key 通过 Streamlit Secrets 管理
- secrets.toml 不进入 Git
- 页面不显示 API Key 和内部异常信息

### Known limitations

- 当前为邀请测试版本
- 暂无正式用户注册和支付功能
- 暂无使用额度和订阅管理
- 暂无 Reply Email 和 Explain Email 功能
- 生成结果发送前仍需用户人工检查

## v0.5

- Prepared Streamlit Community Cloud deployment
- Added optional test access code
- Added external test privacy notice
- Completed cloud compatibility review
- Added Python runtime guidance
- Completed Git and secret safety checks

## v0.4

- Removed remaining preview and mock generation paths
- Improved DeepSeek prompt quality
- Added AI service status and request duration
- Improved JSON parsing and API error handling
- Added duplicate-request and input-length protection
- Added automated tests
- Completed API key security review

## v0.3

- Integrated DeepSeek API
- Replaced local preview content with real AI generation
- Added structured JSON response parsing
- Added secure API key configuration
- Added Chinese API error messages
- Added loading and duplicate-submission protection

## v0.2

- Changed the interface to Chinese-first bilingual design
- Added customizable sender and signature fields
- Removed hardcoded sender name from generated emails
- Added dynamic signature formatting
- Improved Chinese validation and status messages
- Added an Improve Email workflow with shared sender information

## v0.1

- Created the initial Streamlit interface
- Added local preview generation and four tone options
- Added editable subject and body output with copy controls
