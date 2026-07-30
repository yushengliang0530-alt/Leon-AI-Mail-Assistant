# Leon AI V2.0 Phase 4：Send Ready 发送前智能检查设计

日期：2026-07-30
状态：已确认，等待实施
开发分支：`develop-v2`

## 1. 阶段目标

Phase 4 在现有回复邮件工作流末端增加“发送前智能检查”。它不重新写邮件，也不阻止用户复制，而是在用户真正发送前识别遗漏、未经确认的事实、承诺风险和表达问题。

最终回复工作流保持五个主要步骤：

1. 粘贴收到的邮件
2. AI 分析邮件
3. 用户逐项确认回复立场
4. AI 生成回复并执行 Coverage Check
5. Send Ready 发送前检查

Phase 3C 的 Coverage Check 保留为独立检查能力，但不增加第六个页面步骤。Coverage 结果作为第 5 步 Preflight Report 的输入和组成部分展示。

## 2. 范围与非目标

### 本阶段包含

- 为回复邮件选择目标语气：Formal、Friendly、Strong、Executive
- 默认目标语气为 Formal
- 检查客户问题覆盖、行动要求、截止日期、事实增量、附件提醒、称谓、长度、目标语气和商务风险
- 合并 Python 本地规则与 AI 语义检查结果
- 展示结构化 Preflight Report
- 允许用户在存在提醒时继续复制邮件
- 使用独立的 `preflight__` Session State
- 增加自动化测试并在本地验证

### 本阶段不包含

- 重新生成或自动修改邮件
- Outlook、Gmail 或其他邮箱连接
- 自动发送邮件
- 真实附件检测或附件上传
- 用户账号、数据库、历史记录
- 新增商务场景
- 百分制评分或“安全分”

## 3. 产品原则

1. **检查而非代替决策**：报告指出风险和遗漏，不擅自替用户修改立场。
2. **事实优先**：凡日期、金额、责任或承诺无法从来信分析及用户确认信息中找到依据，均需提示。
3. **确定性规则本地执行**：附件关键词、Coverage 状态、长度及可比较的日期和金额优先由 Python 检查。
4. **语义问题交给 AI**：称谓、行动要求清晰度、目标语气匹配和隐含承诺由 AI 检查。
5. **非阻断式提醒**：`CHECK` 或 `WARNING` 不阻止复制，因为用户可能有意暂缓回复某些问题。
6. **无虚假精度**：只使用状态，不输出百分比或分数。

## 4. 目标语气

在生成回复前提供紧凑的目标语气选择，并保存为：

```text
reply__target_tone
```

允许值：

- `Formal`
- `Friendly`
- `Strong`
- `Executive`

默认值为 `Formal`。该值同时传给回复生成 Prompt 和 Preflight 语气检查。语气只能影响表达方式，不得改变用户确认的事实、立场、日期、金额、责任或承诺。

## 5. 检查项目

### 5.1 客户问题覆盖

复用 Phase 3C 的 Coverage 结果，逐项显示：

- `addressed` → `GOOD`
- `partially_addressed` → `CHECK`
- `postponed` → `CHECK`
- `not_addressed` → `CHECK`

`not_addressed` 必须明显提醒，但不阻止复制。报告应说明该项目可能是用户有意不回复，而不是擅自认定邮件错误。

### 5.2 行动要求

AI 判断收件人下一步需要做什么是否清楚。没有必要行动要求的邮件不应被误报；只有上下文确实要求对方行动但正文表达不清楚时才提示。

### 5.3 截止日期

本地规则提取来信分析、用户确认内容和最终回复中的日期表达：

- 已确认且清楚表达 → `GOOD`
- 场景需要期限但没有明确表达 → `CHECK`
- 回复新增了没有依据的具体日期 → `WARNING`

不要求邮件无条件包含截止日期。

### 5.4 未经确认的日期、金额、承诺和责任

比较以下事实来源：

- `IncomingEmailAnalysis`
- `ReplyDecision`
- 用户自定义补充
- 最终 Subject 与 Body

回复中出现无法在已确认来源中找到依据的新日期或金额时，标记为 `WARNING`。承诺和责任表达由本地关键词规则与 AI 语义检查共同判断，避免只依赖关键词。

### 5.5 附件提醒

若正文出现 `attachment`、`attached`、`please find attached` 等含义，显示：

> 邮件提到了附件，请在发送前确认附件已添加。

该项目为 `CHECK`。系统不读取电脑文件，也不声称已经检查真实附件。

### 5.6 称谓

AI 检查称谓是否存在、是否与已知收件人信息明显冲突、是否过于随意或不自然。缺少收件人姓名时，允许合理的通用称谓。

### 5.7 邮件长度

使用稳定的本地词数规则：

- 不超过 450 个英文单词：`GOOD`
- 451–700 个英文单词：`CHECK`
- 超过 700 个英文单词：`WARNING`

长度提醒只说明可读性风险，不自动删减正文。

### 5.8 目标语气

AI 根据 `reply__target_tone` 检查正文表达：

- Formal：专业、礼貌、稳妥
- Friendly：自然、合作、不过度随意
- Strong：行动和责任清楚，但无威胁或失礼
- Executive：简短直接，重点和下一步清楚

不得仅根据结束语判断语气。

### 5.9 商务风险

重点识别：

- 赔偿或损失承担
- 付款承诺或金额
- 法律责任
- 明确交付承诺
- 未经确认的责任归属

AI 只指出需人工确认的语句和原因，不提供法律结论。

## 6. 状态模型

所有检查项只允许：

- `GOOD`：未发现需要用户处理的问题
- `CHECK`：需要确认或可能是有意选择，不构成阻断
- `WARNING`：存在较明显的事实、承诺或商务风险

总体状态按最高风险确定：

```text
WARNING > CHECK > GOOD
```

报告不输出百分比、分数或绝对安全结论。

建议的数据模型：

```python
PreflightItem(
    item_id: str,
    category: str,
    status: Literal["GOOD", "CHECK", "WARNING"],
    title: str,
    message: str,
    suggestion: str | None,
    source: Literal["local", "ai", "coverage"],
)

PreflightReport(
    overall_status: Literal["GOOD", "CHECK", "WARNING"],
    summary: str,
    items: list[PreflightItem],
)
```

AI 使用严格 JSON 返回语义检查结果。解析允许移除 Markdown 代码块，并最多进行一次修复性重试；最终失败时保留本地检查结果并显示安全的中文提示。

## 7. 技术架构

采用“本地规则 + AI 语义检查”的混合架构。

### 建议新增文件

```text
models/preflight.py
preflight_prompts.py
services/preflight_service.py
ui/pages/preflight.py
tests/test_preflight_models.py
tests/test_preflight_service.py
tests/test_preflight_page.py
```

### 建议修改文件

```text
app.py
ai_service.py
ui/state.py
ui/pages/reply_generation.py
ui/pages/reply_decision.py
相关样式和既有测试文件
```

职责划分：

- `models/preflight.py`：严格状态、检查项和报告模型
- `preflight_prompts.py`：仅检查、不改写的语义检查 Prompt
- `services/preflight_service.py`：本地规则、AI 结果合并、总体状态计算
- `ai_service.py`：DeepSeek 请求、JSON 解析和一次修复性重试
- `ui/pages/preflight.py`：Summary 与 Checklist 展示
- `ui/state.py`：独立 Preflight 状态初始化、失效和重置

## 8. AI Prompt 约束

AI 必须：

- 只检查当前 Subject、Body、IncomingEmailAnalysis、ReplyDecision 和目标语气
- 不改写 Subject 或 Body
- 不返回新邮件
- 不补充日期、金额、责任或承诺
- 不将 Coverage 全部默认判为已覆盖
- 指出具体风险句及原因
- 严格返回约定 JSON

AI 不负责附件存在性检查，也不重复执行可由 Python 确定的词数检查。

## 9. Session State

使用独立命名空间：

```text
preflight__status
preflight__source_digest
preflight__local_items
preflight__ai_items
preflight__report
preflight__error
preflight__duration_seconds
preflight__usage_tokens
```

同时增加：

```text
reply__target_tone
```

状态规则：

1. 进入页面不会自动调用 AI。
2. 只有用户点击“发送前检查”才调用一次正常 AI 请求。
3. Streamlit rerun 不得重复发起请求。
4. Subject、Body、ReplyDecision 或目标语气变化时，旧 Preflight Report 失效。
5. 编辑邮件只使 Preflight 失效，不删除已经生成的回复和 Coverage 数据。
6. 重置回复工作流时同步清理 `preflight__` 状态。

`preflight__source_digest` 根据检查输入生成，用于判断报告是否仍对应当前内容。

## 10. 页面与交互

第 5 步顶部显示：

```text
发送前检查
Send Ready

邮件整体结构完整。建议确认附件和交付日期后发送。
```

下方以明显的 Checklist 卡片展示：

```text
✓ 客户问题
全部回复。

! 附件
邮件提到了附件，请在发送前确认附件已添加。

! 交付日期
该日期构成明确承诺，请确认已经获得授权。

✓ 称谓
称谓合理。
```

Coverage 项与其他检查项在同一报告中分组展示，但保留其原始问题标题和说明。页面应支持桌面和手机单列阅读，不使用宽表格。

操作区保留：

- 返回修改
- 重新检查
- 复制主题
- 复制正文
- 复制完整邮件（仅在现有能力允许时复用，不扩展自动发送）

存在 `CHECK` 或 `WARNING` 时仍允许复制，并显示“建议确认后发送”，不使用禁止性文案。

## 11. 错误与降级

- 缺少回复 Subject 或 Body：中文提示，不调用 AI
- 缺少 API Key：显示安全配置提示，不展示内部异常
- AI 请求失败：保留本地规则检查结果，显示“AI 语义检查暂时不可用”
- AI JSON 最终解析失败：不展示原始 JSON，保留本地结果
- Coverage 不存在：Preflight 明确显示“回复覆盖结果不可用”，不得假装全部覆盖
- 快速重复点击：同一请求只执行一次

所有自动化测试必须 Mock AI，不产生真实 DeepSeek 费用。

## 12. 测试要求

至少覆盖：

1. 所有项目均为 `GOOD`
2. 存在 `WARNING`
3. 存在 `CHECK`
4. 附件关键词触发提醒
5. Coverage 存在 `not_addressed`
6. 新增日期、金额或承诺触发风险
7. `Unable to Confirm` 对应的 postponed 项不会被错误判为已解决
8. 目标语气正确传入生成和检查
9. AI 不返回邮件改写内容
10. JSON 正常解析、代码块解析及异常处理
11. 编辑邮件后旧报告失效
12. 生成前及页面 rerun 不调用 AI
13. 每次主动检查只产生一次正常 API 请求
14. AI 请求全部 Mock
15. V1 草稿优化及现有 V2 工作流回归测试通过

## 13. 验收标准

- 回复工作流完整呈现五个步骤
- 回复生成前可以选择目标语气，默认 Formal
- 第 5 步展示一句话 Summary 和清晰 Checklist
- Coverage 结果在 Preflight 中明显可见
- 附件、长度和可比较的事实增量由 Python 稳定检查
- 行动要求、称谓、语气和语义风险由 AI 检查
- 报告只使用 `GOOD`、`CHECK`、`WARNING`
- 不显示百分比分数
- 检查不修改邮件，也不阻止复制
- 所有测试通过，Streamlit 可本地启动
- 不调用真实 DeepSeek 进行自动化测试
- 不修改或提交 Secrets
- 不 Push、不 Merge、不部署、不创建标签

## 14. 已知限制

- 附件检查只根据正文关键词提醒，无法确认真实附件是否存在。
- 日期和金额抽取使用保守规则，复杂自然语言可能需要 AI 辅助判断。
- 商务责任与法律风险仅作写作提醒，不构成法律意见。
- AI 语义判断可能存在误报或漏报，最终发送仍需用户人工确认。
- 本阶段仅接入回复邮件工作流，不扩展到 Outlook、Gmail 或自动发送。
