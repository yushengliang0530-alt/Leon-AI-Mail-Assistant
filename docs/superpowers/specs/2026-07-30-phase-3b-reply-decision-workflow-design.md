# Leon AI V2.0 Phase 3B — Reply Decision Workflow Design

## 1. Scope

Phase 3B extends the approved Phase 3A incoming-email analysis into a local,
guided decision workflow:

1. Paste and analyze an incoming email.
2. Confirm a response stance for each normalized business item.
3. Review a local decision summary.
4. Stop before any reply subject or body is generated.

This phase does not generate a reply email, send email, perform a final
pre-send check, add another business scenario, or call DeepSeek after the
Phase 3A analysis has completed.

## 2. Product objective

The user should not have to turn an analysis into a prompt. Leon AI presents
one business item at a time, asks the user to make the necessary decision, and
checks whether the decision contains enough factual information for a later
reply-writing phase.

An unanswered item is never treated as accepted. Leon AI must not infer a
commitment, date, responsibility, amount, approval, or business position.

## 3. User flow

### Step 1 of 3 — Paste and analyze

Phase 3A remains the source of truth for the incoming email and analysis. Once
the analysis is valid, the result view adds a clear `开始逐项确认` action.

The analysis continues to show:

- summary and sender intent;
- sender requests;
- questions requiring a reply;
- key dates and numbers;
- risks, urgency, uncertainties, and suggested reply strategy.

No decision data exists until the user explicitly starts Step 2.

### Step 2 of 3 — Confirm each item

The page shows one normalized item at a time:

- item number and stable ID;
- request or question;
- deadline, if present;
- required/optional status;
- uncertainty notice;
- stance selector with no default;
- stance-specific supplemental fields;
- Back and Next actions;
- a compact all-items overview;
- actions to return to analysis or clear the current decision.

Required items cannot be skipped. Optional items may be skipped, but the
summary must state that they will not be included in the later reply.

### Step 3 of 3 — Decision summary

The summary is generated locally and displays:

- decided items and their stances;
- explicitly excluded `no_response` items;
- skipped optional items;
- undecided or invalid required items;
- risks found in user-entered decision content;
- readiness for Phase 3C.

There is no `Generate Reply` action. The final notice states that complete
reply generation will be implemented in Phase 3C.

## 4. Architecture

The recommended implementation keeps Phase 3A responsibilities intact and
adds three focused modules:

```text
models/
  incoming_email.py          # existing Phase 3A analysis contract
  reply_decision.py          # ReplyItem, ReplyDecision, stance constants

services/
  incoming_email_analysis.py # existing Phase 3A AI boundary
  reply_item_service.py      # normalization, validation, summary, digests

ui/pages/
  reply.py                   # input, analysis, minimal step routing
  reply_decision.py          # guided decision and summary UI
```

`app.py` only continues to route to the reply workspace. Business validation
must not be placed in `app.py` or duplicated in the UI.

## 5. Data model

### ReplyItem

```text
item_id: str
item_type: request | question
description: str
deadline: str | None
required: bool
source_request_id: str | None
source_question_ids: tuple[str, ...]
uncertain: bool
```

The item is immutable. `item_id` is stable for the lifetime of the source
analysis.

### ReplyDecision

```text
item_id: str
stance: accept | partial | decline | request_info |
        unable_to_confirm | no_response | custom
confirmed_facts: str
accepted_part: str
declined_part: str
reason: str
alternative: str
requested_information: str
next_update_time: str
custom_instruction: str
include_in_reply: bool
user_notes: str
uncertain: bool
no_response_confirmed: bool
```

Empty optional fields are stored as empty text rather than invented values.
Decisions are stored by `item_id`, not by display order.

## 6. Deterministic item normalization

Normalization is performed locally:

1. Each `sender_request` creates a base `ReplyItem` and retains its original
   `item_id`.
2. A question with `related_request_id` attaches to that request.
3. The merged item retains the request ID and records the question ID in
   `source_question_ids`.
4. An unlinked question becomes its own item and retains its question ID.
5. A merged item is required when either the request needs a response or an
   attached question is required.
6. Uncertainty is true when any merged source is uncertain.
7. A question deadline may fill a missing request deadline. Conflicting,
   non-empty deadlines are not guessed or overwritten; the item is marked
   uncertain and both sources remain traceable.

Phase 3B does not perform fuzzy, model-based semantic deduplication. Explicit
`related_request_id` relationships provide deterministic deduplication and
avoid silently merging separate obligations.

## 7. Stance-specific fields and validation

No stance is selected automatically.

### Accept

- Required: confirmed action.
- Optional: confirmed date, publishable facts, next step.

### Partial acceptance

- Required: accepted part and declined/unconfirmed part.
- Optional: public reason, alternative, confirmed date.

### Decline

- Required: public reason.
- Optional: alternative, next step, internal-approval note.

Internal-only notes must be visually distinguished and excluded from later
reply content unless the user explicitly turns them into publishable text.

### Request more information

- Required: information needed.
- Optional: why it is needed and what can be confirmed after receiving it.

### Unable to confirm

- Required: reason or internal verification needed.
- Optional: next update time.

The workflow must accept this stance without a date.

### No response

- Required: explicit confirmation that the item will not be included.
- Optional: reason.

This stance is never inferred from a blank decision.

### Custom

- Required: custom response instruction.

## 8. State design

The existing `reply__` namespace is extended:

```text
reply__step                         # canonical 1/3, 2/3, 3/3
reply__normalized_items
reply__decisions                    # dict keyed by item_id
reply__decision_digest
reply__current_item_index
reply__decision_risk
reply__decision_risk_confirmed_digest
reply__decision_summary
reply__decision_error
reply__show_all_items
```

There is no second canonical `decision_step`; `reply__step` remains the single
source of truth.

### Invalidation rules

- Editing the original subject, email, or region invalidates analysis,
  normalized items, decisions, decision risk, and summary.
- Reanalysis clears all Phase 3B state.
- Changing a saved decision invalidates only decision risk confirmation and
  summary.
- Rerunning Streamlit without source or decision changes preserves state.
- Back and Next do not call AI.
- Clearing decisions preserves the Phase 3A email and analysis.
- Clearing the full reply workspace preserves no reply state.

Digests use canonical serialized content, stable item IDs, and decision values;
widget ordering must not affect them.

## 9. Content-risk handling

The existing local content-risk service is reused for user-entered decision
content. Analysis text alone does not need to be rescanned.

Before Step 3:

1. Validate all required decisions.
2. Aggregate publishable decision fields.
3. Run the local risk service.
4. If high-risk content is detected, show a clear warning and require explicit
   confirmation tied to the current decision digest.
5. Any decision edit invalidates the previous confirmation.

No raw access codes, API keys, internal paths, or exception stacks are shown.

## 10. Error and fallback behavior

Phase 3B has no AI dependency and therefore no simulated response fallback.

- Missing required stance: remain on the relevant item and show a Chinese
  validation message.
- Invalid stance details: preserve entered values and identify only the
  missing field.
- Stale analysis digest: return to Step 1 and discard stale decisions.
- Empty normalized result: show that no actionable items were identified and
  allow the user to return to the analysis; do not invent an item.
- Unexpected local error: show a safe Chinese error and preserve valid state
  where possible.

## 11. UI and responsive behavior

The UI retains the current Leon AI visual system.

Desktop:

- centered, readable decision card;
- compact progress header `1/3`, `2/3`, `3/3`;
- Back and Next aligned consistently;
- optional all-items overview below the active card;
- no wide data table.

Mobile at 390 px:

- single-column item card;
- full-width actions;
- stance choices wrap vertically;
- summary sections stack;
- stable IDs and secondary metadata use smaller, muted text;
- no horizontal scrolling.

## 12. Test strategy

All existing tests must remain green. Phase 3B adds model, service, state, and
Streamlit tests without real DeepSeek calls.

Minimum coverage:

1. Requests normalize correctly.
2. Linked questions merge into their request.
3. Unlinked questions remain separate.
4. Stable source IDs are preserved.
5. Required flags merge correctly.
6. Uncertainty propagates.
7. Missing deadlines are not invented.
8. Conflicting deadlines are marked uncertain.
9. No stance is selected by default.
10. Required items cannot be skipped.
11. Optional items can be skipped.
12. Accept requires confirmed action.
13. Partial requires accepted and declined parts.
14. Decline requires a public reason.
15. Request-info requires requested information.
16. Unable-to-confirm works without a date.
17. No-response requires explicit confirmation.
18. Custom requires an instruction.
19. Back preserves decisions.
20. Next preserves decisions.
21. Returning to analysis preserves analysis.
22. Clearing decisions preserves analysis.
23. Source editing clears analysis and decisions.
24. Reanalysis clears decisions.
25. Decision editing invalidates the summary.
26. Streamlit rerun preserves unchanged decisions.
27. Summary separates decided, excluded, skipped, and undecided items.
28. Readiness is false with invalid required items.
29. Readiness is true when all required items are valid.
30. High-risk decision content requires confirmation.
31. Phase 3B actions never call the AI backend.
32. No generated subject, body, or reply action appears.

## 13. Acceptance criteria

- The user can move from an existing Phase 3A analysis into Step 2.
- Every normalized item is shown exactly once.
- Every business position comes from an explicit user choice.
- Validation prevents incomplete required decisions.
- The example with delay reason, revised date, and recovery plan produces
  three stable items and supports `accept`, `unable_to_confirm`, and
  `request_info`.
- The summary is generated locally and contains no email subject or body.
- Desktop and 390 px mobile layouts are usable.
- Import checks, all automated tests, and Streamlit startup pass.
- Secrets remain ignored and untracked.
- Implementation is committed locally with
  `feat: add reply decision workflow`.
- No push, merge, deployment, or tag is performed.

