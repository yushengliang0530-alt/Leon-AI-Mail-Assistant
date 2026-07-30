# Phase 3A Incoming Email Analysis Implementation Plan

## Scope

Implement the approved two-step Incoming Email Analysis workflow without reply
generation, position selection, sending, uploads, persistence, or real API calls
during automated testing.

## Confirmed test seams

1. `models.incoming_email.parse_incoming_email_analysis` validates the public
   JSON contract.
2. `services.incoming_email_analysis.IncomingEmailAnalysisService` validates
   input and calls an injected backend once.
3. `DeepSeekEmailService.analyze_incoming_email` reuses the existing API
   transport and performs at most one dedicated repair request.
4. `ui/pages/reply.py` is tested through Streamlit `AppTest`.
5. Existing Supplier, V1 improve, access gate, and secret-safety behavior remain
   regression boundaries.

## Vertical slices

1. Add strict immutable analysis models and parser tests.
2. Add injection-resistant analysis and repair prompts with adversarial tests.
3. Add the input-validation service and source digest tests.
4. Add the DeepSeek analysis method, token accounting, error mapping, and
   one-repair tests.
5. Add isolated `reply__` state and invalidation tests.
6. Connect the home route and build Step 1 input/risk flow.
7. Build Step 2 analysis cards and result actions.
8. Add regression tests, run all tests, start Streamlit, and manually verify the
   supplied examples without making a real API request.

## UI direction

- Reuse the established navy, blue, white, border, typography, and spacing
  tokens from the V2 workspace.
- Use a restrained two-step progress rail as the page signature.
- Keep Step 1 focused on one large email surface and one primary action.
- Present Step 2 as compact evidence cards in the order defined by the approved
  specification.
- Use explicit Chinese actions and supporting English labels only where they
  aid orientation.
- Preserve keyboard focus, single-column mobile behavior, and reduced visual
  density on narrow screens.

## Completion checks

- All requests are mocked in tests.
- No reply email is generated or exposed.
- No raw input or model response is logged.
- Existing tests and new Phase 3A tests pass.
- `python -c "import app"` passes.
- Streamlit starts without exceptions.
- `.streamlit/secrets.toml` and `.env` remain ignored and untracked.
- Commit locally on `develop-v2`; do not push, merge, deploy, or tag.
