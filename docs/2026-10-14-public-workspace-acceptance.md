# 免登录工作台发布验收

日期：2026-10-14。范围：用户批准的方案 A；暂停账号功能，保留 selected-03 静态人物、新首页与现有邮件工作流，移除测试码。

## 基线与边界

- 发布基线：`origin/main` 的 `ed700048281ca0a8791a7159ae6dbb912958c2c5`；重新 fetch 成功后建立独立发布分支。
- 账号开发分支保留在 `codex/account-workspace-phase2`，未整支合并；未操作 Supabase、认证设置或用户记录。
- 人物文件与原分支 Git blob 一致：`961537cf896afa85f030cbc1a461ededb5987401`。
- 实际 Secrets 未修改；`.streamlit/secrets.toml`、`.env` 未跟踪且仍被忽略。只更新无凭证的示例文件。
- DeepSeek 模型、配置、Prompt、解析器、业务服务和核心状态文件没有差异；运行依赖仍为 Streamlit 1.60.0 / OpenAI 2.50.0，推荐 Python 3.12。

## 验收结果

| 检查 | 实际环境 | 结果与证据 |
|---|---|---|
| 导入 | 本地 Python | `python -c "import app"` 成功 |
| 全量测试 | 本地，Mock AI | 202 项通过；不等于账号分支的 310 项或真实模型联通 |
| 依赖 | 本地虚拟环境 | `pip check` 无依赖冲突；未增加依赖 |
| 无门禁导航 | AppTest + 本地 Chromium | 旧测试码即使存在也不启用门禁；Home、Reply、Create、Improve、Explore、Supplier 可进入 |
| Reply | 独立本地 Mock 浏览器入口 | 输入 → 分析 → 暂时无法确认 → 决策摘要 → 生成 → Coverage → Preflight 完成；无裸 HTML、无异常 |
| Create | 独立本地 Mock 浏览器入口 | 必填拦截有效；催报价 8 题 → Review → 生成完成 |
| Improve | 独立本地 Mock 浏览器入口 | 空草稿拦截；目标 → 优化 → Before/After → 编辑 → 复制，复制按钮显示“已复制” |
| 会话隔离 | 两个独立 Streamlit 浏览器会话 + AppTest | B 草稿/签名为空、看不到 A 内容；AppTest 验证会话标识不同 |
| 配额与并发 | Mock + 并发单元测试 | 会话20/进程200、UTC跨日、单会话并发、失败计次、过期租约、一次格式修复计次全部通过 |
| 限额后结果保护 | 真实 UI AppTest + Mock HTTP 客户端 | 第二次请求被拒绝，客户端只调用一次；旧编辑稿仍可通过“查看上次优化结果”打开 |
| 首页响应式 | Chromium 1440 / 1280 / 768 / 390 | 无横向溢出；桌面双栏不重叠；平板/手机入口在人物之前；首页按钮高度至少44px |
| 移动结果页 | Chromium 390px | Improve 上下对比，无横向溢出或裸 HTML |
| 提交安全 | Git | 仅按文件白名单提交；既有用户交付物、其他预览和 Secrets 不加入提交 |

浏览器全流程使用单独的 `/tmp` 测试入口，明确显示“MOCK AI”，并拦截真实 OpenAI 客户端构造；该入口不进入发布仓库。正式 `app.py` 无模拟开关或模拟结果路径。

新增回归覆盖：`tests/test_public_usage.py`、`tests/test_public_workspace.py`。额度拒绝测试发现并修复 Improve 编辑稿仅存在于临时组件状态的问题；通过编辑回调保存至既有会话字段，并提供无 AI 请求的旧结果返回入口。

## 截图

目录：`docs/evidence/public-release-2026-10-14/`。

- `home-1440.png`、`home-1280.png`、`home-768.png`、`home-390.png`：正式本地首页，未调用模型。
- `reply-coverage-mock.png`、`reply-preflight-mock.png`：Mock 回复结果与发送前检查。
- `create-result-mock.png`：Mock 创建结果。
- `improve-result-mock.png`、`improve-mobile-mock.png`：Mock 优化、编辑复制与窄屏对比。

## 明确限制

- 未调用真实 DeepSeek，也未验证真实模型质量或账号、SMTP、短信、数据库隔离；这些不属于本次免登录发布。
- 20次是每会话限额，200次是每应用进程每日限额；UTC 日期，失败及修复请求都计次。重启/部署重置，多实例不共享，不构成固定金额或按人硬预算。用户已明确接受。
- 只保留当前会话内容，请及时复制；没有云端私人记录。不要输入高度敏感信息。
- 本文件记录推送前验收；部署成功必须另以远程 main 提交和实际正式页面确认，不以本地测试代替。
