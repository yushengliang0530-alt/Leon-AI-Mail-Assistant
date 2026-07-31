# Reply Item 来源与零事项降级设计

## 目标

修复来信分析成功但 `Reply Item = 0` 时工作流终止的问题。Reply
Workflow 必须允许用户继续，同时不得通过永久启用按钮或本地关键词猜测业务事实来绕过判断。

本次只调整 Reply Item 的分析输出、规范化、零事项交互和相关测试，不修改邮件生成、Coverage、Preflight、供应商工作流或其他业务功能。

## 已确认方案

采用结构化的 `recommended_reply_items`。Reply Item 按以下来源建立：

1. `sender_requests`：来信明确提出的行动要求。
2. `questions_requiring_reply`：来信明确或隐含需要回答的问题。
3. `recommended_reply_items`：来信没有明确问题，但AI基于邮件事实认为回复中应处理的事项。

不直接把 `reply_strategy` 转成 Reply Item，因为该字段可能包含仅供用户参考的内部策略。Python也不根据“延期”“会议”等关键词自动创造事项。

## 数据结构

`IncomingEmailAnalysis` 增加可选列表 `recommended_reply_items`。每项包含：

- `description`：建议在回复中覆盖的事项；
- `reason`：为什么建议回应；
- `required`：是否建议必须处理；
- `uncertain`：建议是否存在不确定性。

`item_id` 不要求AI生成，由Python根据列表顺序生成稳定技术ID，例如 `recommendation_1`。

AI只能基于邮件中已有事实建议回复事项，不得补充日期、金额、责任、承诺或用户立场。纯状态更新可建议确认收到、说明将评估明确影响、或说明是否需要后续更新，但不能替用户确认尚未决定的承诺。

## Reply Item 规范化

规范化顺序保持稳定：

1. Sender Requests；
2. 与Request明确关联的问题；
3. 未关联的问题；
4. Recommended Reply Items。

推荐事项转换为 `ReplyItem(item_type="recommendation")`。系统对相同来源ID及规范化后完全相同的描述做保守去重，不做模糊语义合并。

Recommendation进入逐项确认后沿用现有立场选择与校验规则，因此用户仍可接受、部分接受、拒绝、请求信息、暂时无法确认、不回应或自定义处理。

## 零事项降级

如果三类来源全部为空，分析结果页不显示禁用的“开始逐项确认”，而显示：

> 未检测到明确需要回复的问题。是否仍希望生成一封确认收到的回复？

用户有两个明确操作：

- **是，继续回复**：Python本地建立一个
  `acknowledgement_1`，类型为 `acknowledgement`，描述为“确认已收到并阅读对方邮件”，然后进入Step 3。
- **返回修改邮件**：保留邮件内容并返回输入页面。

系统不得自动替用户选择“是”，不得在没有用户确认时生成回复，也不得自动调用AI。

## 邮件类型预期

- 有Request或Question：直接生成对应事项。
- 无Question但AI提出结构化建议：生成Recommendation事项。
- 纯通知且AI认为礼貌确认有价值：生成Recommendation事项。
- 纯通知且AI未建议回复：进入零事项降级，由用户决定是否创建Acknowledgement。
- 空邮件、超长邮件、分析失败或风险确认未通过：仍按现有校验阻止进入Reply Workflow。

## 状态处理

新增状态仅用于零事项选择，例如：

- `reply__zero_item_choice`
- `reply__acknowledgement_requested`

重新分析、修改原邮件或清空分析时必须清除这些状态。已有分析、决策、生成、Coverage和Preflight状态失效规则保持不变。

## 测试

至少覆盖：

1. Request与关联Question继续正确合并；
2. 无Question但有Recommendation时可以进入Step 3；
3. 纯状态更新生成多个Recommendation事项；
4. 纯通知且无Recommendation时显示零事项选择；
5. 用户选择继续后只建立一个Acknowledgement；
6. 用户返回修改时保留原邮件；
7. 零事项页面不会自动调用AI；
8. Recommendation与其他事项保守去重；
9. 重新分析会清除零事项选择；
10. 原有Reply Generation、Coverage和Preflight测试继续通过。

## 验收标准

- Reply Workflow不会因分析结果中没有Request或Question而形成死路。
- “开始逐项确认”只在存在真实或用户确认创建的事项时可用。
- 所有进入回复生成的事项都可追溯到来信分析或用户明确选择。
- 不新增业务事实，不自动替用户承诺，不自动发送邮件。
