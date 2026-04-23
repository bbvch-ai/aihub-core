# Solution B — Close the API-side Event Registry Gap for Agent-Specific Events

## Context

Agent-specific event classes (e.g. `FollowUpQuestionRequestEvent`, `FollowUpQuestionResponseEvent` defined in
`packages/agent/.../namespace_selection_agent/events/follow_up_question_hitl.py`) live in `packages/agent`. The API
process never imports them, so `BaseEvent._event_registry` in the API has no entry for them at deserialization time.

When a user answers a HITL follow-up in chat, `chat_service.py` (lines 113–135) reads the persisted HITL request, builds
a response envelope, and re-serializes. Because the agent subclass is unknown, `deserialize_event()` falls back through
`_parent_event_names`; the parent list assembled in chat_service walks from `HumanInTheLoopResponseEvent` directly,
SKIPPING the intermediate `HumanInTheLoopInputResponseEvent`. The outer event lands on the generic
`HumanInTheLoopResponseEvent[THitlRequestEvent: HumanInTheLoopRequestEvent]`, whose `request_event` binding collapses to
the base `HumanInTheLoopRequestEvent`. The nested field is subsequently persisted and re-published with that loose
typing. On the agent side, `FollowUpQuestionResponseEvent.model_validate(...)` requires
`request_event: HumanInTheLoopInputRequestEvent` — the received `HumanInTheLoopRequestEvent` is a superclass, not a
subclass — and Pydantic raises `model_type` error (observed in `js_poller.poll`).

The same gap affects any API-side deserialization of agent events: `EventPersister`, `ContextualizedAgentEvent`,
`ThreadService`. Solution A (pairing the base response class locally in `chat_service.py`) fixes the symptom for the
HITL response construction path; Solution B eliminates the gap at the source by making the API aware of agent-specific
event classes through the existing discovery protocol.

The existing protocol already carries everything needed: each `AgentClassDiscoveryResponseEvent` ships
`start_events`/`stop_events`/`hitl_request_events`/`hitl_response_events` as `list[EventSpecs]`, and each `EventSpecs`
includes the full `event_parents` chain (`EventSpecs.from_event_class`,
`packages/core/swiss_ai_hub/core/events/discovery/event_specs.py:46-51`). The chain is also persisted in
`AgentClassEntity.{start_events,stop_events,hitl_request_events,hitl_response_events}` as `EventSpec` embedded
documents, so synthesis can happen on startup without waiting for a live discovery cycle.

## Design

Add an `AgentEventClassSynthesizer` service in `packages/api` that, given a list of `EventSpecs`, dynamically creates
Pydantic subclasses of the deepest registered ancestor via `pydantic.create_model(name, __base__=parent)`. Because
`BaseEvent.__pydantic_init_subclass__` auto-registers every subclass by class name, the synthesized classes appear in
`_event_registry` immediately — `deserialize_event()` then finds them on the exact-match path (no fallback, no
type-downgrade). The inherited `request_event` field keeps its narrowed bound from the concrete intermediate class (e.g.
`HumanInTheLoopInputResponseEvent`).

### Algorithm

1. Collect all `EventSpecs` across discovery responses (dedupe by `event_name`).
2. Topologically order by inheritance depth — shallowest first, so that a synthesized class is available when a deeper
   agent event names it as a parent.
3. For each spec:
   1. If `event_name` is already in `BaseEvent._event_registry`, skip (idempotent across cycles and across agents that
      share an event name, e.g. `StartEvent`).
   2. Walk `event_parents` (deepest → shallowest). Pick the first name that IS in `_event_registry` — that's
      `parent_cls`.
   3. Call `pydantic.create_model(event_name, __base__=parent_cls)`. The `__pydantic_init_subclass__` hook in
      `BaseEvent` registers the new class.
4. Log a concise summary ("synthesized N event classes, skipped M already present").

No extra fields are added from `event_schema` in the initial implementation. Agent-specific HITL events in the current
codebase (`FollowUpQuestionRequestEvent`, `FollowUpQuestionResponseEvent`, `NamespaceApprovalRequestEvent`,
`NamespaceApprovalResponseEvent`, playground `HITLTypeSelectionRequestEvent`) either add no fields or add only fields
that the API never needs to introspect (the agent owns the business meaning). If this assumption breaks later, extend
`_create_filtered_model` from `EventModelCreationService` to inject extra fields from `event_specs.event_schema`.

### Two synthesis triggers

**Startup (Mongo-seeded).** `EventPersister` subscribes to all agent events in `lifetime_manager` BEFORE
`AgentEndpointsDiscoveryService` broadcasts. To avoid a cold-start window where events are deserialized with an empty
agent-class registry, seed from MongoDB at startup:

- Query `AgentClassEntity.objects()` after Mongo is initialized.
- Flatten `start_events + stop_events + hitl_request_events + hitl_response_events` via `EventSpec.to_specs()`.
- Run the synthesis algorithm once.
- Only then register NATS subscribers (`EventPersister`, `WebSocketSender`, etc.).

**Live discovery.** In `_broadcast_discovery`
(`packages/api/swiss_ai_hub/api/services/agent_endpoints_discovery_service.py:128-186`), after the response set is
finalized but BEFORE `AgentClassEntity.create_or_update(...)`, run the synthesis algorithm again with the fresh specs.
Any newly added agent event class becomes resolvable for the next message without restart.

### Fix the parent-list bug in chat_service

Keep the minimal correctness fix as part of Solution B: in
`packages/core/swiss_ai_hub/core/routes/chat/chat_service.py:122-135`, compute `parent_classes` starting from
`type(open_hitl_request)` instead of hard-coding `HumanInTheLoopResponseEvent`. Use the paired response class from the
three HITL helpers (`HumanInTheLoopInput`, `HumanInTheLoopConfirmation`, `HumanInTheLoopChat`). This removes the
`HumanInTheLoopInputResponseEvent`-skipping bug so that even if synthesis has not yet run on a freshly booted API (edge
case: first-ever deploy, no persisted `AgentClassEntity`), deserialization falls back to the correct intermediate,
preserving the `request_event` narrowing.

## Files to modify / create

**New**

- `packages/api/swiss_ai_hub/api/events/agent_event_class_synthesizer.py`
  - Stateless service with a single `@staticmethod synthesize(specs: list[EventSpecs]) -> int` method that returns the
    number of newly registered classes. Idempotent; safe to call repeatedly.

**Modify**

- `packages/api/swiss_ai_hub/api/runners/lifetime/lifetime_manager.py`
  - After Mongo init, before creating `EventPersister` subscribers, seed the registry from `AgentClassEntity`.
- `packages/api/swiss_ai_hub/api/services/agent_endpoints_discovery_service.py`
  - In `_broadcast_discovery`, call the synthesizer with the collected `EventSpecs` before persistence/endpoint
    registration.
- `packages/core/swiss_ai_hub/core/routes/chat/chat_service.py`
  - Replace hard-coded `HumanInTheLoopResponseEvent.event_name_from_class()` with dispatch on `type(open_hitl_request)`
    → paired response class (`HumanInTheLoopInput.response`, `HumanInTheLoopConfirmation.response`,
    `HumanInTheLoopChat.response` at
    `packages/core/swiss_ai_hub/core/events/agent/hitl/human_in_the_loop_{input,confirmation,chat}.py`).

**Existing utilities to reuse**

- `pydantic.create_model` — already used in the codebase at `packages/core/swiss_ai_hub/core/form/form.py:340-341` and
  `packages/api/swiss_ai_hub/api/events/event_model_creation_service.py:68`.
- `EventSpec.to_specs()` — `packages/core/swiss_ai_hub/core/persistence/agents/agent_class_entity.py:55`.
- `BaseEvent._event_registry` — direct dict read for the idempotency check.
- Inheritance-depth helper `get_inheritance_depth` — `packages/core/swiss_ai_hub/core/events/utils.py` (used by
  `parent_event_names_from_class`).

## Verification

1. **Unit: synthesizer** — `packages/api/swiss_ai_hub/api/events/tests/test_agent_event_class_synthesizer.py`

   - Given an `EventSpecs` with parents
     `[FollowUpQuestionRequestEvent, HumanInTheLoopInputRequestEvent, HumanInTheLoopRequestEvent, ControlAndDisplayEvent, ControlEvent, DisplayEvent]`,
     after `synthesize(...)`:
     - `BaseEvent._event_registry["FollowUpQuestionRequestEvent"]` exists.
     - It is a subclass of `HumanInTheLoopInputRequestEvent`.
     - Calling `synthesize(...)` again returns `0` (idempotent, no ValueError from duplicate registration).
   - Topological ordering: given a list where deeper events come before shallower, confirm all get registered without
     `KeyError`.

2. **Integration: HITL round-trip** — extend
   `packages/api/playground/testing/tests/sockets/test_contextualized_agent_event.py` or add a new test under
   `playground/testing/tests/thread/`:

   - Use `SimulatedAgentApiTestRunner` to simulate an agent that publishes a `FollowUpQuestionRequestEvent`-like event
     (already modelled as a stand-in in `test_contextualized_agent_event.py:21`).
   - Call the chat reply endpoint.
   - Assert the published NATS payload contains `_event_name=FollowUpQuestionResponseEvent` and nested
     `request_event._event_name=FollowUpQuestionRequestEvent`.
   - Deserialize the payload with `BaseEvent.deserialize_event(...)` in the test process (where the agent classes ARE
     imported) and assert `isinstance(event.request_event, HumanInTheLoopInputRequestEvent)`.

3. **Manual end-to-end** (Docker dev stack):

   - `/docker-dev start`
   - Run the namespace selection agent: `cd packages/agent && python app/namespace_selection_agent/main.py`
   - Run the API: `cd packages/api && make run-dev`
   - Open OpenWebUI, trigger a namespace agent run that produces a `FollowUpQuestionRequestEvent`, reply in chat.
   - Confirm no `js_poller.poll` validation error in the agent log and that the agent step `process_follow_up_step`
     executes (observable via Langfuse trace or agent debug log).

4. **Regression** — run `make test` in `packages/api`, `packages/core`, and `packages/agent`.
