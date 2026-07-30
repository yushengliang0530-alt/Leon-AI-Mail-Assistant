# Leon AI V2.0 Phase 2 Scenario Engine Design

Date: 2026-07-30  
Branch: `develop-v2`  
Status: Approved for implementation review

## 1. Scope

Phase 2 builds the first reusable scenario-driven email workflow. It implements
only **Follow Up Supplier / 催供应商**, with four task variants:

- 催报价 / Follow Up Quotation
- 催交期 / Follow Up Delivery
- 更新计划 / Request Plan Update
- 延期解释 / Request Delay Explanation

The phase does not implement reply email, independent preflight checking, other
business scenarios, full navigation, accounts, databases, email integrations,
exports, or automatic sending.

## 2. Product Flow

The workflow contains three main steps:

1. **场景**：choose one supplier follow-up task. No AI request occurs.
2. **信息**：answer a short set of task-specific questions. Local validation
   checks required facts before an AI request is allowed.
3. **邮件**：generate and review the English subject, body, communication
   analysis, localization guidance, risk guidance, and pre-send review.

The user never needs to write a complete Chinese brief or Prompt.

## 3. Architecture

Use a configuration-driven architecture:

- `models/scenario.py` defines immutable `Scenario` and `ScenarioField` models.
- `data/email_scenarios.py` contains reviewed supplier task definitions.
- `services/scenario_service.py` validates facts, filters empty values, builds
  the reviewed AI message contract, and calls the existing DeepSeek service.
- `ui/pages/compose_supplier.py` is a generic three-step renderer driven by the
  selected scenario definition.
- `ui/state.py` owns the minimal `compose__` workflow state.

Adding another scenario that uses supported field types should require adding a
scenario configuration and tests, not another page or a new form implementation.

`app.py` remains responsible only for startup, access protection, service
construction, and choosing between the home, supplier workflow, and V1
compatibility view.

## 4. Scenario Model

`Scenario` contains:

- `id`
- Chinese and English titles
- description
- tuple of `ScenarioField`
- default tone
- risk policy identifier
- prompt policy identifier

`ScenarioField` contains:

- key
- Chinese and English labels
- field type
- required flag
- placeholder
- help text
- maximum length

Prompt and risk policies are reviewed identifiers. Scenario configuration cannot
inject arbitrary system instructions.

Supplier name is required for all four variants. Other required fields vary by
task.

## 5. Supplier Task Fields

### Follow Up Quotation

Required:

- supplier name
- quotation item or scope
- requested reply date or timing
- required supplier action

Optional:

- project name
- original request date
- current situation
- business impact

### Follow Up Delivery

Required:

- supplier name
- order, item, or deliverable
- original delivery date
- current situation
- required supplier action

Optional:

- project name
- requested reply date
- delay impact

### Request Plan Update

Required:

- supplier name
- original planned submission date
- current situation
- requested reply date or timing
- required supplier action

Optional:

- project name
- delay impact

### Request Delay Explanation

Required:

- supplier name
- delayed item or milestone
- original committed date
- current situation
- required supplier action

Optional:

- project name
- requested explanation date
- delay impact

Advanced options shared by all variants:

- tone
- recipient country or region
- recipient
- sender and signature

## 6. AI Contract

The AI request contains:

- stable scenario ID and task name
- selected tone
- recipient and localization context when supplied
- a structured object containing only non-empty user facts

Rules:

- Do not reconstruct an open-ended Chinese brief.
- Do not include empty fields or placeholder text.
- Do not infer dates, amounts, projects, promises, responsibility, causes, or
  deadlines.
- Omit missing facts instead of guessing.
- Generate a concise, professional English subject and body.
- Do not generate a signature; Python appends it locally.
- Continue returning the existing JSON email and communication-analysis
  structure.
- Retain the existing single repair attempt and safe error handling.

## 7. State Design

The supplier workflow uses only `compose__` keys:

- `compose__scenario_family`
- `compose__task_id`
- `compose__step`
- `compose__fields`
- `compose__tone`
- `compose__country_region`
- `compose__recipient`
- `compose__result_subject`
- `compose__result_body`
- `compose__analysis`
- `compose__duration_seconds`
- `compose__usage_tokens`
- `compose__request_in_progress`
- `compose__error`

Shared sender information continues using the existing saved sender values so
that the V1 compatibility workflow remains functional. Page reruns do not call
AI, and returning to an earlier step does not erase entered facts.

## 8. Validation and Request Protection

- Missing required facts show specific Chinese errors and do not call AI.
- Inputs retain the existing 8,000-character upper safety boundary, with shorter
  per-field limits from configuration.
- The generate button is disabled during an active request.
- One explicit generate action produces one normal API request; only the
  existing JSON repair path may produce one additional repair request.
- Results remain in Session State and are not overwritten by unrelated reruns.
- API failures preserve all entered facts and show safe Chinese messages.

## 9. UI Design

The page continues the established navy, cobalt, white, and cool-gray workspace
language. Its distinctive element is a compact progress ledger:

`① 场景  →  ② 信息  →  ③ 邮件`

The active step uses the cobalt accent while completed and future steps remain
visually quiet. The structure is business-workflow oriented rather than a chat
interface.

Desktop:

- centered work area with restrained maximum width;
- task selection cards use two columns;
- information fields use one or two columns according to expected input length;
- advanced options remain collapsed;
- result and advisory information are clearly separated.

Mobile:

- all task cards and form fields become one column;
- no horizontal scrolling;
- all interactive targets are at least 44 pixels high;
- progress labels remain readable at approximately 390 pixels;
- result actions remain available without hover.

## 10. Existing Capability Reuse

Reuse without duplication:

- DeepSeek client and configuration
- strict JSON parsing and one repair attempt
- dynamic local signature formatting
- communication analysis parsing
- localization guidance
- local sensitive-content risk analysis
- service status, duration, and token display
- editable subject and body output
- copy controls

V1 draft improvement remains reachable from the home page and is not rewritten.

## 11. Testing

All automated AI calls are mocked. Tests cover:

- scenario registry and field integrity;
- correct dynamic fields for all four supplier tasks;
- supplier name required in every task;
- missing required facts prevent service calls;
- advanced options are collapsed;
- prompt payload excludes empty facts;
- one generate click produces one service call;
- no AI call during task selection or navigation;
- state isolation under the `compose__` namespace;
- V1 draft improvement remains reachable;
- existing tests continue to pass;
- desktop and approximately 390-pixel mobile browser checks.

## 12. Acceptance Criteria

- A user can generate a usable supplier follow-up email without writing a
  complete Chinese brief.
- The four supplier task variants show different, appropriate fact fields.
- Missing required facts never reach DeepSeek.
- Generated output retains subject, body, communication analysis, localization,
  risk guidance, and pre-send review.
- No empty or invented facts enter the AI Prompt.
- Only the supplier home card opens the new workflow.
- No other Phase 2+ workflow is implemented.
- The complete test suite passes, the app starts locally, and desktop/mobile
  screenshots confirm the workflow.

