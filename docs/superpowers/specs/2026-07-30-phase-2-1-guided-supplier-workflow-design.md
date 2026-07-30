# Leon AI V2.0 Phase 2.1 Guided Supplier Workflow Design

Date: 2026-07-30  
Branch: `develop-v2`  
Status: Approved for implementation review

## 1. Scope

Phase 2.1 upgrades only the existing **Follow Up Supplier / 催供应商**
workflow from a multi-field form to a guided, question-by-question workflow.

It does not add business scenarios, reply email, independent pre-send checking,
accounts, databases, email integrations, exports, or automatic sending.

The existing Scenario Engine, facts-only Prompt contract, DeepSeek client,
analysis, localization, risk guidance, signatures, and V1 draft improvement
remain in place.

## 2. Product Principle

The workflow should behave like a structured business adviser:

- ask one clear business question at a time;
- explain why the requested fact matters when useful;
- prevent required facts from being skipped;
- allow unknown optional facts to be skipped;
- preserve answers when moving backward;
- summarize the confirmed facts before any AI request;
- let the user edit facts before generation;
- call AI only after explicit confirmation on the Review step.

The interface remains a workflow, not a chat transcript and not a long form.

## 3. Four-Step Flow

### Step 1/4: Choose the supplier task

Display:

- 催报价 / Follow Up Quotation
- 催交期 / Follow Up Delivery
- 更新计划 / Request Plan Update
- 要求解释延期 / Request Delay Explanation

Selecting a task enters the guided questions. No AI call occurs.

### Step 2/4: Guided questions

The selected Scenario's ordered `fields` tuple defines the question sequence.
Only the current question is rendered.

The page shows:

- current task;
- `问题 X / N`;
- Chinese question as the primary heading;
- smaller English label;
- optional help text;
- one text input or text area;
- Back and Next buttons.

Rules:

- A required question cannot advance while empty.
- An optional question displays `暂时跳过`.
- Next stores the current answer and advances one question.
- Skip stores an empty answer and advances one question.
- Back stores the current answer when valid and returns to the previous question.
- Existing answers are restored when revisiting a question.
- The final question advances to Review.
- Navigation never calls AI.

### Step 3/4: Review

Display a professional Summary Card titled `本次商务沟通信息`.

The card shows only non-empty facts in Scenario order, using Chinese business
labels. It does not display internal keys, empty rows, or placeholder text.

Actions:

- `修改` beside a fact returns to that exact question.
- `返回继续修改` returns to the last guided question.
- `生成英文邮件` confirms the reviewed facts and starts the AI request.

Changing an answer invalidates the previous Review confirmation and any older
generated result. Returning without changing an answer does not erase data.

### Step 4/4: Generated email

Retain the current Phase 2 output:

- editable subject;
- editable body;
- copy subject and body;
- DeepSeek status, duration, and token usage;
- business communication analysis;
- risk guidance;
- localization guidance;
- pre-send advisory checklist;
- modify information and return-to-workspace actions.

AI failure returns the user to Review with all answers preserved and a safe
Chinese error. It does not return to the beginning or use mock output.

## 4. State Design

Continue using the `compose__` namespace.

Required workflow state:

- `compose__step`: current major step from 1 through 4;
- `compose__question_index`: zero-based current question;
- `compose__answers`: current fact answers;
- `compose__completed_questions`: stable field keys already answered or skipped;
- `compose__review_ready`: whether all questions have been visited;
- `compose__review_confirmed`: whether the current answer snapshot was confirmed;
- `compose__edit_field_key`: field selected for modification;
- existing result, analysis, duration, token, error, and request state.

The existing `compose__fields` remains the validated non-empty snapshot sent to
the Scenario Service. V1 keys remain untouched.

Selecting a different supplier task resets question progress, answers, Review,
and generated output for this workflow only. Shared sender information remains.

## 5. Component Boundaries

`models/scenario.py`

- remains the source of supported question metadata;
- no guided behavior is encoded in the model.

`data/email_scenarios.py`

- retains field order as question order;
- adds concise help text only where it helps the user answer correctly.

`ui/state.py`

- owns guided navigation and answer state transitions;
- exposes small functions for starting a task, advancing, going back, editing a
  Review field, entering Review, and invalidating stale results.

`ui/pages/compose_supplier.py`

- renders the four major steps;
- renders exactly one ScenarioField during Step 2;
- renders the Review Summary Card;
- delegates validation and AI generation to existing services.

`services/scenario_service.py`

- remains responsible for final validation, empty-field filtering, and backend
  generation;
- does not manage UI navigation.

`app.py`

- requires no new business logic.

## 6. Validation and Editing Rules

- Required answers are trimmed and validated before advancing.
- Per-field maximum length is enforced by the existing field configuration.
- Optional answers may be skipped.
- Review never includes empty answers.
- Editing a fact returns directly to that question.
- After an edited answer is saved, the user returns to Review rather than being
  forced through all remaining questions again.
- If a required answer is cleared during editing, Review cannot be re-entered
  until the answer is restored.
- High-risk local confirmation remains immediately before the AI request.
- The AI receives only the final validated, non-empty answer snapshot.

## 7. Advanced Options

Tone, recipient region, recipient, and sender signature are not mixed into the
main business-question sequence.

They appear in a collapsed `高级选项` section on Review. Their values continue
to use existing keys and shared sender state. Changing advanced options
invalidates Review confirmation but does not erase business answers.

## 8. UI Direction

Continue the established navy, cobalt, white, and cool-gray visual system.

The signature UI element is a focused question card with:

- a small task and question counter;
- one prominent question;
- generous whitespace;
- a restrained answer area;
- clearly separated Back, Skip, and Next actions.

The Review Summary Card uses aligned label/value rows and a quiet `修改` action
for each row. It should look like a business brief, not a web form.

Desktop:

- centered single-question card;
- content width kept narrow enough for focused reading;
- Summary Card may use two columns when values are short.

Mobile at approximately 390 pixels:

- one-column question and Review rows;
- no horizontal scrolling;
- progress labels remain readable;
- buttons remain at least 44 pixels high;
- no behavior depends on hover.

## 9. AI and Prompt Contract

The existing facts-only Prompt remains authoritative:

- no invented dates, amounts, projects, causes, responsibility, promises, or
  commitments;
- missing optional facts are omitted;
- signatures remain local;
- one normal API request per generate action;
- the existing single JSON repair attempt remains the only possible additional
  request;
- automated and browser validation use mock services only.

## 10. Testing

Tests cover:

- fields appear in Scenario order one at a time;
- required answers cannot be skipped or advanced empty;
- optional questions can be skipped;
- Back returns to the previous question and preserves answers;
- Review displays the correct non-empty facts in order;
- editing from Review returns to the selected question;
- edited Review content replaces the previous value;
- generation cannot occur before Review;
- navigation and Review do not call AI;
- one generate click calls the mocked backend once;
- reruns do not repeat generation;
- task switching resets only `compose__` workflow state;
- V1 draft improvement remains available;
- the full existing test suite passes;
- desktop and approximately 390-pixel layouts have no browser errors or
  horizontal overflow.

## 11. Acceptance Criteria

- The user sees one main business question at a time.
- Required facts cannot be skipped.
- Optional facts can be skipped without creating empty Review rows.
- Back and Review editing preserve valid answers.
- Review clearly communicates what will be sent to AI.
- No AI request occurs before explicit generation from Review.
- The generated result retains all Phase 2 advisory and editing capabilities.
- No new business scenario or later-phase workflow is introduced.

