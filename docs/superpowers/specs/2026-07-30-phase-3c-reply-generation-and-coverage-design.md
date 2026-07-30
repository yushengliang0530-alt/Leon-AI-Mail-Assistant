# Leon AI V2.0 Phase 3C — Reply Generation and Coverage Design

## 1. Scope

Phase 3C completes the first usable reply-email workflow:

1. receive an incoming email;
2. analyze the email;
3. confirm a stance for each normalized item;
4. generate an editable English reply;
5. independently check whether the reply covers every expected item.

This phase does not send email, connect Outlook or Gmail, implement pre-send
inspection, add another business scenario, add user accounts, or modify the
configured DeepSeek model and base URL.

## 2. Product objective

The feature must do more than write a plausible reply. It must compare the
actual reply against the customer’s requests and questions and make omissions
visible.

Generation and coverage are separate operations:

- generation writes a reply using confirmed facts and positions;
- coverage inspects the resulting text without rewriting it.

This separation prevents the coverage task from silently changing the email
and makes the result easier for the user to audit.

## 3. Five-step workflow

### Step 1 — Incoming email

The user pastes the original subject and email. No API call occurs until the
user explicitly clicks the analysis button.

### Step 2 — Incoming-email analysis

The existing Phase 3A analysis is displayed. The user can review requests,
questions, deadlines, risks, and uncertainties before continuing.

### Step 3 — Reply decisions

The existing Phase 3B guided workflow remains the decision source of truth.
Each required item must have a valid explicit stance. The local decision
summary is shown before generation.

The summary adds one primary action:

`生成英文回复 · Generate Reply`

This is the first Phase 3C action that calls AI.

### Step 4 — Reply generation

The generation request uses only:

- `IncomingEmailAnalysis`;
- normalized `ReplyItem` records;
- validated `ReplyDecision` records;
- country or localization context already captured by the workflow.

The result contains an editable subject and body. The Python service appends
the existing shared sender signature locally.

After a valid generation result is saved, the system automatically performs
one independent coverage request. The progress indicator moves to Step 5 when
the coverage request succeeds or fails; a coverage failure must not discard
the generated reply.

### Step 5 — Coverage and completion

The page shows:

- editable Subject;
- editable Body;
- Copy Subject;
- Copy Body;
- Copy Full Email;
- a prominent coverage summary;
- one visible row or card for every normalized item;
- an action to rerun coverage without regenerating the reply.

The workflow stops here.

## 4. Architecture

Focused additions:

```text
models/
  reply_generation.py

services/
  reply_generation_service.py

ui/pages/
  reply_generation.py

reply_prompts.py
```

Focused modifications:

```text
ai_service.py
ui/state.py
ui/pages/reply.py
ui/pages/reply_decision.py
tests/
```

`app.py` remains a composition root. Reply-generation business rules, coverage
validation, and prompt construction must not be placed there.

## 5. Two-call AI boundary

### Call 1 — Generate Reply

The generation response is strictly:

```json
{
  "subject": "English subject",
  "body": "English reply body"
}
```

The model must not return:

- coverage;
- analysis or explanation;
- Markdown fences;
- a sender name, job title, company, contact details, or signature block.

### Call 2 — Coverage Check

The coverage response is strictly:

```json
{
  "coverage": [
    {
      "item_id": "request_1",
      "status": "addressed",
      "note": "The confirmed point is stated in the reply."
    }
  ]
}
```

The coverage request receives the normalized items, decisions, and current
subject/body. It must not return a rewritten subject or body.

The first coverage request occurs after successful generation. Later manual
checks are user-triggered and do not regenerate the email.

## 6. Reply-generation model

```text
GeneratedReply
  subject: str
  body: str
  usage_tokens: int | None
```

Parsing rules:

- strip an optional Markdown JSON fence;
- require exactly `subject` and `body`;
- require non-empty strings;
- reject unknown fields;
- do not expose invalid model output;
- permit at most one repair request.

## 7. Coverage model

Allowed statuses:

```text
addressed
partially_addressed
postponed
not_addressed
```

```text
CoverageItem
  item_id: str
  status: CoverageStatus
  note: str

CoverageResult
  items: tuple[CoverageItem, ...]
  addressed_count: int
  partial_count: int
  postponed_count: int
  not_addressed_count: int
  covered_count: int
  total_count: int
  usage_tokens: int | None
```

Counts and summary text are computed by Python after parsing.

`covered_count` includes `addressed` and `postponed`. A postponed item is
covered because the reply explicitly tells the customer that it cannot yet be
confirmed. `partially_addressed` remains visible as partial and is not counted
as fully covered.

## 8. Strict coverage validation

The expected IDs are the normalized `ReplyItem.item_id` values.

The parser must reject:

- an unknown item ID;
- a duplicate item ID;
- a missing expected item ID;
- an unsupported status;
- an empty note;
- extra root or item fields;
- coverage that is not a list.

Each expected item appears exactly once.

Coverage is evidence about the actual generated or edited email, not merely
about the presence of a decision. The model must compare the email text with
each item.

## 9. Decision-to-coverage semantics

### Accept

`addressed` only when the confirmed action or fact is communicated.

### Partial

`addressed` only when both the accepted and declined/unconfirmed portions are
clearly communicated. Otherwise use `partially_addressed` or
`not_addressed`.

### Decline

`addressed` when the reply communicates the refusal or permitted public reason
without exposing internal-only notes.

### Request information

`addressed` when the reply asks for the required information.

### Unable to confirm

Use `postponed` when the reply explicitly states that the point cannot
currently be confirmed. A date is not required unless the user supplied one.

### No response

Use `not_addressed` when the item is intentionally omitted. The UI labels it as
an explicit user decision, not an accidental omission.

### Custom

Judge the actual reply against the custom instruction and the underlying item.

## 10. Prompt safety and factual constraints

Incoming analysis and decision content are untrusted data, not executable
instructions.

The generation system prompt requires:

- use only confirmed facts and explicit decisions;
- do not invent dates, amounts, names, project numbers, responsibility,
  approval, commitments, or deadlines;
- preserve uncertainty;
- state inability to confirm when that stance is selected;
- omit unavailable facts;
- do not expose internal-only notes;
- do not include the original email or Chinese source text;
- produce concise professional business English;
- do not generate sender identity or signature.

The coverage system prompt requires:

- inspect only;
- do not rewrite the email;
- do not mark all items addressed by default;
- support negative and partial findings;
- base status on actual email content;
- return one entry for every supplied item.

## 11. Signature handling

Phase 3C reuses the existing shared fields:

- sender name;
- job title;
- company;
- contact information.

Python appends the signature after parsing the generated body. The AI is
instructed not to generate a closing or signature.

The reply uses the existing Formal closing rule:

```text
Best regards,
```

Only populated sender fields are appended, in their existing order. When all
fields are empty, only the closing is present. Leon is never used as a default
sender.

Coverage checks the final body including the local closing, but the signature
does not satisfy a business coverage item.

## 12. Editing and invalidation

The generated subject and body are stored separately from their editor widget
state.

### Decision or analysis change

Clear:

- generated reply;
- generation digest;
- coverage;
- coverage digest;
- coverage summary;
- request errors and result metadata.

### Subject or body edit

Preserve the user’s text and generation result, but mark coverage stale by
clearing the coverage digest.

The UI displays:

`邮件已修改，请重新检查回复覆盖情况。`

### Rerun rules

- Streamlit reruns do not invoke AI.
- Back navigation does not invoke AI.
- Copy actions do not invoke AI.
- `Generate Reply` invokes generation once and then coverage once.
- `重新检查覆盖` invokes coverage once only.
- A parse repair is the sole permitted extra call for each operation.

## 13. Session State

Phase 3C extends the existing `reply__` namespace:

```text
reply__generated_email
reply__subject
reply__body
reply__coverage
reply__summary
reply__generation_digest
reply__coverage_digest
reply__generation_status
reply__coverage_status
reply__generation_error
reply__coverage_error
reply__generation_duration
reply__coverage_duration
reply__generation_tokens
reply__coverage_tokens
reply__generation_request_in_progress
reply__coverage_request_in_progress
```

The canonical generation digest includes:

- analysis digest;
- stable normalized items;
- validated decisions;
- localization context;
- local sender details.

The canonical coverage digest includes:

- generation digest;
- current subject;
- current body.

## 14. UI design

The reply header displays five progress segments. At narrow widths they remain
compact and horizontally contained; the page itself must not scroll
horizontally.

Coverage cards use visible status treatment:

- green check: addressed;
- amber exclamation: partially addressed;
- blue clock/info: postponed;
- red or strong amber cross: not addressed.

The summary reads:

`本次回复覆盖 X / Y 项`

Partial and omitted counts are displayed separately when non-zero.

Any `not_addressed` status produces a yellow warning. It does not disable copy
buttons because omission may be intentional.

## 15. Error handling and graceful degradation

### Generation failure

- keep the decision summary;
- display a safe Chinese error;
- allow retry;
- do not create mock content.

### Coverage failure

- keep the generated subject and body;
- keep editors and copy actions available;
- display `覆盖检查暂时不可用，请重新检查。`;
- do not invent fallback coverage;
- allow a coverage-only retry.

### Invalid coverage after repair

Treat coverage as unavailable and do not show the invalid JSON.

No raw exception, stack trace, path, API key, model response, or user input is
written to the UI or logs.

## 16. Testing strategy

All AI clients are mocked.

### Models and parsing

- valid generation JSON;
- fenced generation JSON;
- empty or extra generation fields;
- valid coverage for every status;
- missing, duplicate, and unknown coverage IDs;
- invalid status and empty note;
- fenced coverage JSON;
- invalid coverage after repair.

### Prompt tests

- confirmed facts are present;
- unavailable facts are absent;
- internal notes are excluded;
- unable-to-confirm instructions require explicit uncertainty;
- no sender identity is included;
- coverage prompt says inspect, not rewrite.

### Service tests

- generation makes one normal call;
- coverage makes a distinct call;
- each parser permits at most one repair;
- Python appends the shared signature;
- missing sender details never add Leon;
- generation failure does not trigger coverage;
- coverage failure preserves generated email;
- token and duration metadata remain separate.

### State tests

- analysis change invalidates generation and coverage;
- decision edit invalidates generation and coverage;
- subject/body edit invalidates only coverage;
- rerun preserves edited text;
- copy and navigation never call AI.

### UI tests

- full coverage;
- partial coverage;
- complete omission;
- unable-to-confirm maps to postponed;
- intentional no-response remains visible;
- not-addressed warning does not block copy;
- Coverage failure keeps editors available;
- manual edit exposes the stale-coverage notice;
- coverage rerun does not regenerate;
- desktop and 390 px layouts have no horizontal overflow.

## 17. Acceptance criteria

- A valid Phase 3B decision summary can generate an English reply.
- Generation uses only analysis and validated decisions.
- Unknown dates, amounts, responsibility, and commitments are not invented.
- Shared sender information is appended only by Python.
- Coverage is a separate AI operation and cannot rewrite the reply.
- Every normalized item receives exactly one valid coverage result.
- Unable-to-confirm is shown as postponed when communicated.
- Partial and omitted items are obvious.
- A not-addressed item warns but does not block copying.
- Editing the reply invalidates only coverage.
- Coverage failure preserves the email.
- All tests pass without a real DeepSeek request.
- Streamlit starts locally on `develop-v2`.
- Implementation is committed locally and is not pushed, merged, deployed, or
  tagged.

