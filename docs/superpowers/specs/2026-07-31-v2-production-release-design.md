# Leon AI V2.0 正式发布设计

## 目标

将 `develop-v2` 中已经完成并验证的 Leon AI Business Email Workspace
发布为 V2.0 正式版，替代当前 V1.0。此次发布不新增业务功能，不修改
DeepSeek 模型、Prompt、Secrets 或工作流逻辑。

## 正式版功能边界

首页只展示已经完成且可运行的三个入口：

1. 回复收到的邮件
2. 催供应商
3. 优化已有草稿

回复流程继续包含：

- Incoming Email Analysis
- Reply Decision
- Reply Generation
- Coverage Check
- Send Ready Preflight

Preflight 是回复流程的最后一步，不作为尚未实现的独立首页入口。邀请会议、
项目进展汇报、请求审批、确认计划和更多场景等占位入口不进入 V2.0 正式首页。

## 发布态界面

- 产品名称：Leon AI · Business Email Workspace
- 版本号：V2.0
- 移除 `Development`、`开发中`、开发预览和 Phase 占位提示
- 保留人工审核、安全提醒、AI 服务状态和测试访问保护
- 不改变已有入口的交互、Session State 或服务注入

## 文档

- README 将当前产品和版本更新为 V2.0
- Changelog 在顶部增加 V2.0 Release Notes
- Roadmap 将 V2.0 标记为完成，并把未实现能力保留在后续规划
- 历史设计文档保留原有 Phase 和 Development 描述，作为开发记录，不改写历史

## 验证

发布提交前必须通过：

1. `python -c "import app"`
2. 全部自动化测试
3. Streamlit 启动检查
4. 首页三个正式入口检查
5. Reply、Supplier 和 V1 Improve 工作流回归
6. Requirements、Python 3.12、Secrets 忽略状态检查
7. 工作区和提交内容检查

自动化测试继续 Mock DeepSeek，不产生真实调用费用。

## Git 与发布

1. 在 `develop-v2` 创建 V2.0 发布提交
2. 将 `main` fast-forward 到 `develop-v2`
3. 在最终提交创建注释标签 `v2.0.0`
4. 推送 `main` 和 `v2.0.0`
5. 创建 GitHub Release：`Leon AI Business Email Workspace V2.0`
6. 由当前 Streamlit Community Cloud 应用从 `main` 部署
7. 验证远端分支、标签、Release 和正式应用

## 回滚

- GitHub 以 `v1.0.0` 保留 V1.0 稳定基线
- 如正式应用出现阻断问题，可将部署目标临时回退到 `v1.0.0`，或对 V2.0
  发布提交执行显式 revert
- 不移动或重写 `v1.0.0`

