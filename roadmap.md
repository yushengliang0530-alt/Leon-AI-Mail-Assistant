# Roadmap

## v0.1 — Interface prototype

- Streamlit interface
- Chinese brief input
- Four business tones
- Editable subject and body
- Copy controls

## v0.2 — 中文主界面、发件人与签名

- 中文主显示、英文辅助标注
- “写英文邮件”和“优化英文邮件”共享发件人信息
- 根据语气动态生成邮件签名
- 中文校验、状态和复制反馈
- 不设置默认个人发件人姓名
- 桌面和窄屏响应式适配

## v0.3 — DeepSeek AI integration

- Connect DeepSeek through the OpenAI-compatible Chat Completions API
- Replace local preview generation with real model output
- Add JSON response parsing and one repair attempt
- Add secure Secrets and environment configuration
- Add Chinese API errors, loading state, and duplicate-call protection
- Keep signatures deterministic in local Python code

## v0.4 — Stability and quality validation

- Remove remaining preview and mock production paths
- Strengthen generation and improvement prompts
- Add safe AI service status, duration, and token usage
- Add input-length, repeat-request, and rerun protection
- Expand automated tests without making paid API calls
- Complete API key and deployment-readiness review

## v0.5 — External test deployment preparation

- Prepare Streamlit Community Cloud configuration
- Add an optional invited-tester access code
- Add privacy and external-test guidance
- Pin direct dependencies and document Python 3.12
- Complete Git, Secrets, and cross-platform safety checks

## Later

- Email history
- Reusable sender profiles
- Authentication and team features
- Prompt evaluation and quality regression tests
- Public deployment, rate limiting, and production monitoring
