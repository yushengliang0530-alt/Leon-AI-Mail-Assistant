# Leon AI V2.1 UI/UX Experience Upgrade

## Status

Approved design direction: **Professional Enterprise AI Workspace**. This work is visual and interaction polish only; existing business workflows, DeepSeek configuration, prompts, Secrets, validation, data handling, and persistence boundaries remain unchanged.

## Product outcome

An employee opening Leon AI should understand, without training:

1. what business task they can complete now;
2. which step they are currently completing;
3. what information is needed next;
4. how to review and copy the final result safely.

The product remains an assistive workspace. It does not automatically send email or make commitments on a user's behalf.

## Audit findings

- Visual rules currently live independently in `app.py`, `ui/pages/home.py`, `ui/pages/reply.py`, and `ui/pages/compose_supplier.py`. The same component ideas use different colors, spacing, radius, and state treatment.
- The home task cards require a selection click before a second start action appears. The primary reply path is direct, while the other two have an unnecessary intermediate state.
- Reply steps are present, but the completed/current/upcoming states are not visually distinct enough. Analysis, decision, generation, coverage, and preflight lack a common page structure.
- Analysis and Send Ready results are mostly card-shaped text blocks. They need a hierarchy of conclusion, important facts, then supporting risk or context.
- The V1 draft-improvement screen still uses the older page shell and does not feel part of the V2 workspace.
- Actual 390px browser inspection showed horizontal clipping on the home page. Existing mobile CSS is not sufficient for the current Streamlit DOM and main content sizing.

## Design principles

- Chinese is primary; concise English is secondary.
- Use a focused task workspace, not a chat UI or marketing landing page.
- One primary action per screen. Secondary help, privacy guidance, and risk detail stay visually subordinate.
- Status has meaning: success, information, confirmation needed, and material risk use the same treatment everywhere.
- Make the current step and next action explicit. Do not expose internal AI or Prompt terminology as the primary interface language.
- Preserve visible user input and existing session state while a page reruns.

## Design tokens

| Role | Token | Value |
| --- | --- | --- |
| Brand / primary action | `--la-primary` | `#2563EB` |
| Primary action hover | `--la-primary-strong` | `#1D4ED8` |
| Ink | `--la-ink` | `#0F172A` |
| Body text | `--la-text` | `#475569` |
| Muted text | `--la-muted` | `#64748B` |
| Canvas | `--la-canvas` | `#F8FAFC` |
| Card | `--la-surface` | `#FFFFFF` |
| Blue support surface | `--la-info-bg` | `#EFF6FF` |
| Divider | `--la-line` | `#E2E8F0` |
| Success | `--la-success` | `#15803D` |
| Check | `--la-warning` | `#B45309` |
| Risk | `--la-risk` | `#B91C1C` |

Use 8px spacing increments, 8px compact radius, 12px standard card radius, 44px minimum touch target, and a maximum main workspace width that leaves readable room for emails without causing narrow-screen overflow.

## Shared UI architecture

Create a small, Streamlit-native component layer instead of a new frontend framework.

- `ui/styles.py`: injected base tokens, stable component classes, responsive rules, focus states, reduced-motion rules.
- `ui/components.py`: shared renderers for global header, page header, workflow stepper, task card, summary card, status badge, notice bar, empty state, loading state, action bar, and email editor chrome.
- Existing page modules remain owners of their current service calls and session-state transitions. They call the new presentation helpers only.
- `app.py` retains routing and V1 generation / optimization behavior; it imports the global shell and uses the same design tokens.

No shared component accepts or mutates AI-service objects. UI helpers receive only display data and Streamlit callbacks already owned by the calling workflow.

## Page changes

### Global shell

- A compact header contains the Leon AI Copilot wordmark, product subtitle, a visible route back to the workspace where relevant, and a compact service/version indicator.
- Task pages receive a common page header with Material icon, Chinese title, one-line outcome statement, and optional workflow progress.
- Privacy, security, and advanced information remain in expanders or secondary panels.

### Home

- Hero question: **今天需要完成什么商务沟通？**
- The reply-email card remains the prominent primary action and opens its workflow directly.
- Supplier follow-up and draft improvement are direct usable task cards, rather than requiring an extra selected-action confirmation panel.
- Future or unavailable capabilities remain absent from the main action area.
- All cards use the same shared renderer: icon, title, concise outcome, action cue, focus/hover/pressed state, and mobile stack behavior.

### Reply workflow

- Five-step stepper: 来信 / 分析 / 回复立场 / 回复 / 检查.
- Completed steps show a quiet completion marker; the current step has the primary blue treatment; future steps are reduced contrast.
- Incoming-analysis output becomes:
  1. `AI理解结果` summary;
  2. important response requests, reply items, and dates;
  3. risk, uncertainty, and response strategy in supporting cards.
- Reply decision stays one item at a time, with a clear `事项 x / y` header, the original request, a concise choice set, and only the fields needed by the selected stance.
- Generated email becomes a structured editor surface, with clear Subject and Body labels and a primary `复制完整邮件` action. Recheck and back actions are secondary.
- Coverage becomes `回复完整性`: concise counts followed by status cards with the original issue, coverage status, and one short note.
- Preflight becomes `发送前检查`: an overall conclusion first, then passed, confirmation-needed, and material-risk groups. It never blocks copying and never claims a score.

### Supplier workflow

- Keep the current four-step guided flow and its required-field behavior.
- Make the current question feel like one focused task: step header, context label, one question, one answer control, and a consistent back/continue action bar.
- Review uses a structured summary card, with advanced options collapsed and clearly separated from core facts.
- Generated email and supporting analysis use the common email/result components.

### Draft improvement

- Retain all V1 inputs, validation, risk checks, localization guidance, and API behavior.
- Wrap the screen in the V2 task header and common editor/result components so it belongs to the same workspace.

## States and feedback

- Loading copy is task-specific: `正在分析来信`, `正在整理回复事项`, `正在生成商务回复`, and `正在执行发送前检查`.
- Every loading state describes the useful work being performed rather than “AI thinking”.
- Empty states include an icon, one outcome-oriented line, and one next action.
- Error states explain what failed and the safe next action. Raw exception details remain hidden.
- Existing risk and validation behavior is preserved; only presentation changes.

## Responsive behavior

- Validate desktop 1440px, laptop 1280px, tablet 768px, and mobile 390px.
- At 768px and below, cards and summary groups may stack. At 390px, all action cards and control rows are single-column with 44px or larger touch targets.
- The stepper condenses to short labels and numeric progress on narrow screens. Long email content remains readable with no horizontal page scroll.
- Use container-level stable classes and sizing rules; do not depend on Streamlit-generated emotion classes.

## Non-goals

- No new task scenario, reply strategy, AI model, Prompt rule, data store, login, access-code behavior, email integration, or automatic sending.
- No migration of the Streamlit application to another framework.
- No changes to `.streamlit/secrets.toml`, API keys, or real DeepSeek use in tests.

## Implementation phases

1. Add tokenized base styles and pure display components, then test imports and key uniqueness.
2. Replace the home shell and direct task-card interactions while preserving routes.
3. Apply the shared shell, stepper, cards, states, and action bars to Reply.
4. Apply the same presentation system to Supplier and V1 draft optimization.
5. Add mobile-specific fixes, visual regressions, documentation, V2.1 identity, and test coverage.

Every phase must leave the app importable and all existing tests passing.

## Verification

- `python -c "import app"` with safe local settings.
- Existing unit tests plus focused UI-contract tests for direct home entries, common components, stepper states, empty/loading/error state copy, stable keys, and no API calls from UI-only transitions.
- Browser inspection of Home, Reply input/analysis/decision/generation/coverage/preflight, Supplier steps/review/result, and draft optimization at 1440, 1280, 768, and 390px.
- Check no horizontal overflow, clipped text, inaccessible focus treatment, or mobile touch targets below 44px.
- Confirm Git excludes Secrets and that main remains unmerged and undeployed until final user approval.
