# Changelog

## V2.1 — 2026-10-14 · Public workspace update

- Preserved the selected-03 static business character and blue-white workspace design
- Removed the test access-code gate; Reply, Create and Improve remain directly accessible
- Paused account registration and cloud history development; preserved the separate development branch and staging database
- Added server-side anonymous allowances: 20 actual API calls per session and 200 per process per UTC day, including repair attempts
- Added atomic shared counters and per-session request leases; counters reset on process restart and are not a durable billing cap
- Kept DeepSeek configuration, prompts, signatures, risk rules, Coverage and Preflight business behaviour unchanged
- Expanded public-navigation, session-isolation and allowance regression tests with mocked AI

## V2.1 — 2026-08-18

### Changed

- Introduced the Leon AI Copilot / Business Communication Copilot product identity
- Added workspace-first navigation for Reply, Create and Improve workflows
- Redesigned Reply, Create and Improve as consistent enterprise task workspaces
- Unified the design system for headers, workflow navigation, action hierarchy, cards, loading, empty and status states
- Simplified task flows and refined Chinese-first UI copy
- Improved desktop, tablet and mobile workspace responsiveness

### Quality

- Standardized completed/current/future workflow states across workspaces
- Removed the unused Improve Workspace placeholder page and duplicate Reply return action
- Preserved all DeepSeek, Prompt, risk, Coverage and Preflight business behaviour
- Extended UI regression coverage with mocked AI services

## V2.0 — 2026-07-31

### Added

- Added the Leon AI Business Email Workspace production home
- Added the guided Follow Up Supplier workflow
- Added incoming email analysis and structured request extraction
- Added item-by-item reply decision guidance
- Added editable reply generation based only on confirmed facts
- Added reply coverage checks with addressed, partial, postponed, and missing states
- Added Send Ready preflight checks for coverage, actions, dates, attachments, salutations, tone, commitments, and sensitive risks
- Added responsive production task cards with consistent business icons

### Changed

- Replaced development and Phase placeholders with completed production workflows
- Updated the current product identity and documentation to V2.0
- Kept the existing English draft optimization workflow available
- Limited the production home to reply email, supplier follow-up, and draft optimization

### Security

- Preserved Streamlit Secrets management and optional access-code protection
- Preserved local sensitive-content checks and high-risk confirmation
- Automated tests continue to mock DeepSeek and do not incur API charges
- Generated content remains subject to human review before sending

### Known limitations

- Supplier follow-up is the only production scenario-based new-email workflow
- Outlook, Gmail, automatic sending, attachments, accounts, payments, databases, and history are not included
- AI analysis and generated content can contain errors or omissions

## V1.0 — 2026-07-30

### Changed

- Renamed the product to AI Business Communication Optimization Assistant
- Upgraded the product positioning from email writing to business communication optimization
- Improved page structure and product introduction

### Added

- Added confidentiality and sensitive-content risk guidance
- Added recipient country and region selection
- Added localized salutation and cross-cultural communication guidance
- Added business communication quality analysis
- Added interactive business communication examples
- Added clearer usage and security guidance

### Security

- Added local sensitive-content checks
- Added confirmation before processing potentially high-risk content
- User inputs and generated results are not intentionally stored
- Risk analysis is advisory and does not replace company policies or human review

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
