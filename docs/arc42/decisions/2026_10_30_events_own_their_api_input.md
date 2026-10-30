# Events Own Their API Input

## Context

API callers send agent events through the per-agent endpoints, which the API registers from the JSON schema each agent
announces. Until now the API decided what a caller may send. `ModelCreationService` dropped a fixed list of server-owned
fields (`event_id`, `user`, `locale`, …) from that schema, and `StartEvent.from_raw_data` /
`HumanInTheLoopResponseEvent.from_raw_data` filled them back in. A caller could only send the fields the agent itself
receives.

Sending a file alongside a message needs a field whose API shape differs from its event shape. A caller wants to send
base64 content in the same request (#2340, #2341). The agent must receive only a `UserUploadedFile` reference. NATS caps
a message at 1 MB in development and 2 MB in production, every event is persisted, and the publishers check no size.
Images sent as `data:` URLs already travel inside `UserMessageEvent` today, which is the risk this avoids.

## Decision Drivers

- *Base64 never reaches NATS*: events carry references, the bytes go to the agent's file bucket first.
- *Nothing is stored for a rejected request*: every inline file is checked before the first is written.
- *The OpenAPI schema documents the inline form*, including for agent-only events the API has no class for.
- *As little event knowledge in the API as possible*, and a pattern the next field of this kind can reuse.
- *Large bodies cannot exhaust the API*, which runs one gunicorn worker.

## Decision

- **An event declares its API input.**
  - `BaseEvent.api_input_model()` is the event's fields without the server-owned ones (`_api_server_fields`, moved from
    `ModelCreationService`), with the types from `api_input_field_overrides()` swapped in.
  - `UserMessageEvent` and `RAGStartEvent` declare `files: list[UserUploadedFile | InlineFile] | None`.
- **An event converts its API input.** `BaseEvent.from_api_payload(payload, event_name, event_parents, context)`
  replaces `from_raw_data`, in this order:
  1. It resolves the registered class the name stands for, falling back to the closest parent. An agent-only subclass of
     `UserMessageEvent` therefore gets its parent's conversion.
  2. It validates the payload against the real input model.
  3. It calls the class's `_api_input_to_event_data` hook.
  4. It fills in the server data: the caller and the locale for start events.
- **`ApiPayloadContext` carries what conversions need**: user, locale, agent class and id, thread and the S3 client. It
  is the same for every event, and events that need none of it ignore it.
- **Agents announce the input schema.** `EventSpecs.api_input_schema`, persisted with the agent class, is what the API
  builds the request model from. The API renders it and passes the validated payload on; it knows nothing about files.
- **`InlineFile.store_all` checks every file before storing any.** It checks the count, the encoded and decoded size,
  that the base64 is valid, and that the type is one `DocumentExtractor.can_extract` reads. Images are refused in favour
  of `image_url`. It then writes each file under the existing `agent-files` key scheme. The limits are
  `AGENT_INLINE_FILE_*`.
- **The OpenAI-compatible endpoint stays custom code.** It turns the `file` parts of the last user message into
  `InlineFile`s and stores them with the same `store_all`.
- **A pure-ASGI `JsonBodySizeLimitMiddleware` rejects any JSON body over `API_REQUEST_MAX_JSON_BODY_BYTES`** (64 MiB)
  while it arrives, before it is parsed. Multipart and binary endpoints keep their own limits.

Rejected alternatives:

- *An API-side converter registry keyed by a schema marker*: generic, but it puts the knowledge of each field in the API
  and duplicates the class resolution `deserialize_event` already does.
- *Making the event's own field a union*: agents would receive a type they must never see.

## Consequences

- A field whose API shape differs from its event shape needs two things: an override in `api_input_field_overrides()`
  and a conversion in `_api_input_to_event_data`. The API needs no change.
- An inline file is validated twice: once by the request model the API rebuilt from the schema, and once by the real
  class. Only the second runs custom checks.
- Agent classes stored before this change have no `api_input_schema` until they are discovered again, which happens
  within a minute of an agent starting.
- Process events still use `ProcessStartEvent.from_raw_data` and the API's own exclusion list. They can move to the same
  pattern when one of them needs it.
- Images sent as `image_url` `data:` URLs still travel inside the event. Moving them to the bucket needs agents to sign
  their references at the LLM boundary, and is tracked separately.
