# Leon AI V2.0 首页任务卡片对齐与图标设计

日期：2026-07-30
状态：已确认，等待实施
开发分支：`develop-v2`

## 1. 目标

本次只调整 Leon AI V2.0 首页任务卡片的内部排版、图标和响应式表现。重点解决“催供应商、邀请会议、汇报项目进展、请求审批”四张两列卡片中文字起点、基线、内边距和高度不一致的问题。

不修改 Reply Workflow、Guided Supplier Workflow、AI 服务、Prompt、Session State、路由、Secrets 或版本号。

## 2. 方案选择

采用 Streamlit 内置 Material Symbols 线性图标：

- 使用 `st.button(..., icon=":material/<name>:")`
- 不下载图片
- 不使用外部 CDN
- 不增加图标库依赖
- 保留原生按钮的键盘、焦点和点击行为
- 图标均来自同一套线性视觉语言

未选择内嵌 SVG Data URI，是因为它需要为每个按钮生成额外的 DOM/CSS 映射，维护成本和 Streamlit DOM 兼容风险更高。Unicode 仅作为未来必要时的降级方案，不作为本次主实现。

## 3. 统一任务配置

首页入口集中定义为不可变任务配置。每项至少包含：

```text
action
title
description
icon
status
primary
```

入口与图标映射：

| 入口 | Material Symbol |
|---|---|
| 回复收到的邮件 | `reply` |
| 催供应商 | `local_shipping` |
| 邀请会议 | `calendar_month` |
| 汇报项目进展 | `monitoring` |
| 请求审批 | `assignment_turned_in` |
| 确认交期或计划 | `event_available` |
| 优化已有草稿 | `edit_note` |
| 发送前检查 | `verified_user` |
| 更多场景 | `folder_open` |

`status` 单独保存，例如“发送前检查”的“开发中”，不把状态硬编码进标题。

## 4. 统一渲染组件

将现有 `_action_button` 替换为统一公开范围内的首页组件：

```python
render_task_card(
    *,
    action: str,
    title: str,
    description: str,
    icon: str,
    status: str | None = None,
    primary: bool = False,
    on_click: Callable[[], None] | None = None,
) -> None
```

职责：

- 生成稳定且唯一的 `home__action__<action>` key
- 组合标题、状态和一句说明
- 传入统一 Material Symbol
- 保持既有 `on_click` 或 `set_selected_home_action` 行为
- 主卡片只改变配色，不改变内部对齐模型

所有九个首页入口必须通过同一个组件渲染，不复制第二套按钮 HTML 或布局结构。

## 5. 卡片内部结构

原生 Streamlit 按钮使用统一 CSS 网格：

```text
┌──────────────────────────────────────────┐
│  ┌──────────┐  标题                     │
│  │  图标    │  一句说明                 │
│  └──────────┘                           │
└──────────────────────────────────────────┘
```

桌面端：

- 图标容器：52 × 52px
- 图标本体：24px
- 图标与文字间距：18px
- 卡片水平内边距：18px
- 卡片垂直内边距：16px
- 标题与说明间距：5px
- 点击区域最小高度：高频卡片 100px

移动端：

- 图标容器：44 × 44px
- 图标本体：22px
- 图标与文字间距：14px
- 点击区域不低于 76px，且始终超过 44px

图标容器统一使用品牌蓝的浅色背景，图标使用现有品牌蓝色。回复主卡片中图标容器改用半透明白色背景，图标为白色，以保持对比度。

## 6. 文字对齐与高度

全部卡片：

- 标题和说明左对齐
- 文字区域占据剩余宽度，不被图标挤压
- 图标列宽固定
- 标题行高、字重一致
- 说明行高、颜色一致
- 整体内容垂直居中

高频商务场景：

- 四张两列卡片使用同一最小高度
- 两列标题基线一致
- 两列说明起始基线一致
- 较长说明允许换行，但不改变顶部基线
- 每一行的点击区域尺寸一致

“确认交期或计划”保持整行宽度，但内部图标、文字起点、间距和高频卡片完全一致。

工具区三张卡片使用同一高度和内部结构。回复主卡片可保持更高、更醒目的品牌蓝背景，但内部仍使用同一图标列和文字列。

## 7. CSS策略

只定义一套通用布局规则：

```text
.task-card
.task-card-icon
.task-card-content
.task-card-title
.task-card-description
```

由于 Streamlit 原生按钮 DOM 不允许直接添加任意内部 class，实现中将使用首页容器和稳定 key 选择器统一映射到上述视觉职责；不得为单张卡片写不同 margin 或 padding。

允许的差异选择器仅用于：

- 主卡片品牌蓝配色
- 工具区浅色背景
- 状态文字

不得针对“催供应商”“邀请会议”等单张卡片设置独立位置。

交互状态包括：

- 默认
- Hover
- Keyboard focus-visible
- Active

Hover 不作为唯一反馈。启用 `prefers-reduced-motion` 时取消位移动画。

## 8. 响应式设计

桌面端：

- 高频场景保持两列
- 同一区域卡片等高
- “确认交期或计划”整行
- 工具区保持三列

宽度不超过 640px：

- 所有多列区域切换为单列
- 卡片保持图标与文字横向排列
- 标题和说明正常换行
- 图标不缩小文字列
- 首页容器 `overflow-x: hidden`
- 不出现横向滚动

390px 手动检查必须确认：

- 任务卡完整显示
- 图标清晰
- 文本无截断
- 点击区域足够
- 反馈面板不造成横向溢出

## 9. 点击与业务兼容

必须保留以下既有行为：

- 回复收到的邮件直接进入 Reply Workspace
- 催供应商显示既有确认区域并进入 Supplier Workflow
- Phase 2 场景继续显示既有提示
- 优化已有草稿继续进入 V1 功能
- 发送前检查继续显示当前 Phase 提示逻辑
- 更多场景继续显示场景分类

不得修改现有 action 名称和 `home__action__<action>` key。

## 10. 测试

自动化测试至少覆盖：

1. 九个首页入口全部存在
2. 九个 action 值唯一
3. 九个组件 key 唯一
4. 每项配置均有非空图标
5. 所有卡片均通过统一组件渲染
6. 四张高频卡片使用同一配置结构
7. 回复主入口点击逻辑保持
8. 催供应商入口保持
9. 优化已有草稿入口保持
10. Phase 提示逻辑保持
11. 首页存在桌面两列和移动单列 CSS
12. Material Symbols 不需要网络资源
13. 全部原有测试通过
14. 测试不调用真实 DeepSeek
15. Secrets 未被跟踪

## 11. 手动验收

桌面端检查：

- 四张高频卡片图标位置一致
- 标题和说明基线一致
- 卡片高度、内边距和点击区域一致
- 整行卡片内部对齐一致
- 工具区三张卡片一致

390px 检查：

- 自动单列
- 无横向滚动
- 图标与文字保持横向排列
- 文本完整换行
- 点击和焦点状态可见

## 12. Git与安全

- 当前分支保持 `develop-v2`
- 实施后创建本地提交：`style: align workspace cards and add task icons`
- 不 Push
- 不 Merge
- 不部署
- 不创建标签
- 不修改或提交 Secrets
