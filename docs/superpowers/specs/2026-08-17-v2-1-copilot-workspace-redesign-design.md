# Leon AI V2.1 Copilot Workspace Redesign

## Status

Approved design direction: **Option A — Single-app UI Router with independent
workspace shells**.

This specification supersedes the navigation and home-page portions of
`2026-08-17-v2-1-ui-ux-experience-upgrade-design.md`. The existing design
tokens and pure display components remain useful foundations, but V2.1 is no
longer limited to refining task cards. It changes the product's interaction
model from a set of feature pages to a focused AI task workspace.

## Product outcome

Within five seconds, a user should understand what Leon AI can help them
complete today. Once they choose a task, the rest of the experience should
feel like one dedicated workspace: the current step, the next action, and a
safe route back to the workspace home are always clear.

Leon AI remains an assistive tool. It never sends an email or makes a business
commitment automatically.

## Design constraints

- Do not change DeepSeek calls, model configuration, Prompts, risk detection,
  Incoming Email Analysis, Reply Decision, Reply Generation, Coverage,
  Preflight, Supplier rules, or Secrets.
- Preserve the meaning of existing session-state values and workflow
  transitions. A thin UI router may add presentation-only route values.
- Do not migrate to a different frontend framework or Streamlit multipage app.
- No automatic sending, email account integration, new business scenarios, or
  new persistence.

## Information architecture

```text
Leon AI Copilot Workspace
├── Home
│   ├── Reply Email
│   ├── Create Email
│   ├── Improve Draft
│   └── Explore More
├── Reply Workspace
├── Create Email Workspace
├── Improve Draft Workspace
├── Supplier Workspace
└── Explore More Catalog
```

The UI router decides only which workspace frame is visible. Existing page
modules remain responsible for their own service calls, validation, and
session-state business transitions.

## Home

### Purpose

Make the three core outcomes obvious without presenting a catalog of tools.

### Content

- Brand: `Leon AI Copilot`
- Supporting label: `Business Communication Copilot`
- Primary question: `今天需要完成什么商务沟通？`
- Supporting text: `选择任务，Leon AI 会一步步帮助你完成。`

### Task hierarchy

1. **Reply Email / 回复收到的邮件** — one full-width primary launch card.
   `理解对方要求、确认回复立场、生成专业回复并完成发送前检查。`
2. **Create Email / 创建商务邮件** — secondary launch card.
   `通过引导完成一封新邮件。`
3. **Improve Draft / 优化已有邮件** — secondary launch card.
   `让已有英文草稿更清晰、专业。`
4. **Explore More** — a small secondary route to a separate catalog page.

Supplier follow-up remains available in Explore More and opens its own
Supplier Workspace. The home page must not reveal task content underneath a
card or require a second start action.

## Workspace shell

### Desktop layout

```text
Global Header
Leon AI Copilot / Current workspace       service status · version · Home

┌─────────────────────────┬───────────────────────────────────────┐
│ Task flow               │ Current task                           │
│                         │                                       │
│ ● 1 Current step        │ Page header and outcome statement     │
│ ○ 2 Next step           │                                       │
│ ○ 3 Later step          │ Existing workflow content              │
│                         │                                       │
│                         │ [Back]                  [Main action] │
└─────────────────────────┴───────────────────────────────────────┘
```

- The left rail is a visual task map, not a second form.
- Completed steps are quietly marked complete; the current step uses the
  primary color; future steps have reduced contrast.
- Current workflow content is rendered only in the right task canvas.
- The action bar is aligned to the bottom of the content area. It has one
  clear primary action and subordinate back or secondary actions.

### Responsive rules

- Desktop: persistent left rail and wide content canvas.
- Tablet: a compressed horizontal stepper above the canvas when the rail would
  restrict readable content.
- Mobile: `步骤 X / Y · 当前步骤` with a compact progress indicator; all cards,
  controls, and actions are single-column; no horizontal page scrolling;
  touch targets are at least 44px high.

## Workspace flows

| Workspace | Visual step sequence | Existing workflow ownership |
| --- | --- | --- |
| Reply Email | Email → Analysis → Decision → Generate → Check | `ui/pages/reply.py` keeps all business transitions and services. |
| Create Email | Details → Generate → Review | Existing V1 writing behavior remains unchanged. |
| Improve Draft | Draft → Improve → Review | Existing V1 improvement behavior remains unchanged. |
| Supplier | Task → Guided Questions → Review → Email | `ui/pages/compose_supplier.py` keeps its guided rules. |

Future steps must not be made clickable if the current workflow already blocks
them. Previously completed steps may use the existing safe back/edit behavior.

## Component boundaries

- `AppShell`: canvas, content width, responsive padding.
- `GlobalHeader`: brand, current workspace label, service/version metadata,
  and a single Home action.
- `WorkspaceLayout`: left task rail plus right content canvas.
- `WorkspaceStepper`: static display of completed/current/upcoming workflow
  steps. It receives display data only.
- `WorkspacePageHeader`: title, bilingual helper, and outcome statement.
- `TaskLaunchCard`: the shared launch card used for all home task entries.
- `ExploreCatalog`: secondary task directory, separate from Home.
- `ActionBar`: standard primary and secondary action placement.
- `StatusBadge`, `NoticeBar`, `SummaryCard`, `ResultPanel`, `EmptyState`,
  `LoadingState`, and `ErrorState`: shared presentation-only feedback.

Components do not receive or mutate AI services. They receive text, status,
stable keys, and callbacks owned by the existing page module.

## Visual direction

- Quiet blue-gray canvas, white task surfaces, dark ink, and one primary blue.
- Clear alignment, generous working whitespace, and restrained shadows.
- A workspace rail, not a decorative side navigation.
- Chinese as the primary interface language; concise English as a supporting
  label only.
- No Prompt, model, or internal AI terminology in the primary user journey.
- Status colors have consistent meaning: success, information, confirmation
  needed, and material risk.

## Migration plan

### Phase 1 — Router, workspace foundation, and Home

- Introduce presentation-only route helpers and the workspace shell.
- Replace Home with three core launch cards and a separate Explore More route.
- Route existing Reply, Create, Improve, and Supplier paths into independent
  workspace frames; do not modify their internal task UI yet.
- Add UI-contract tests for direct routes, stable keys, access control, and
  service-status preservation.

Acceptance: no home card expands content; all task entries open independent
workspace routes; existing tests pass without real API calls.

### Phase 2 — Reply Workspace migration

- Wrap the existing five Reply states with the shell, stepper, page headers,
  and action bar.
- Preserve all Reply service calls and decision logic.

Acceptance: users can see their current Reply step and the next action across
Email, Analysis, Decision, Generate, and Check.

### Phase 3 — Create and Improve Workspace migration

- Apply the shell and common editor/result presentation to existing V1 create
  and draft-improvement pages.

Acceptance: both V1 tasks feel part of the same product without behavior
changes.

### Phase 4 — Supplier Workspace and Explore catalog

- Apply the shell to the existing Supplier guided flow.
- Expose Supplier only through Explore More in the new home information
architecture.

Acceptance: Supplier remains fully usable without returning to a feature-card
homepage pattern.

### Phase 5 — Responsive, accessibility, and cleanup

- Validate 1440px, 1280px, 768px, and 390px layouts.
- Remove replaced home-only styles and reduce legacy duplicate presentation
  rules where safe.
- Confirm focus visibility, reduced motion, touch target size, service status,
  access gate, and no horizontal overflow.

## Verification

- Full automated suite with mocked AI calls.
- `python -c "import app"`.
- Browser checks for each direct route and all specified breakpoints.
- No real DeepSeek calls in UI-only verification.
- `.streamlit/secrets.toml` and `.env` remain ignored and untracked.
- No push, merge, deployment, or V2.1 release until explicit approval.
