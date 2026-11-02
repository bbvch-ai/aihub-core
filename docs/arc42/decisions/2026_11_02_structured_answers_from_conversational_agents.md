# Structured Answers from Conversational Agents

## Context

Callers want an agent's answer in a JSON shape they choose. A typical request is an invoice PDF plus a schema with date,
issuer and total, answered with those fields instead of prose (#2342, #2343). Plain models already do this through
OpenAI's `response_format` and forced function calls. Agents did not:

- the answer travelled only as text in `LLMStopEvent.output_messages`;
- `UserMessageEvent` had no field for the request;
- the OpenAI-compatible endpoint accepted `response_format`, `tools` and `tool_choice` for agents and dropped them
  without a word.

The runtime schemas of record extraction (ADR `2026_10_02_runtime_record_schemas_for_structured_extraction`) cover flat
primitive fields only, because jambo reads nothing but `properties`. A caller's schema has nested objects and arrays.

## Decision Drivers

- *Native*: the model that writes the answer is asked for the shape, the way it is asked for tools. No second pipeline
  next to the conversation.
- *Every chat blueprint, without each one opting in*: a blueprint must not be able to forget the shape and answer prose.
- *A caller who asked for a shape gets it or an error*, never prose.
- *One request in the protocol*, whatever API the caller used.
- *Visible in the trace with its cost*, like every other model call.

## Decision

- **The request is `UserMessageEvent.response_schema`**, a core `ResponseSchema` (`name`, `description`, `json_schema`,
  `strict`). A `json_schema` of `None` means any JSON object, OpenAI's `json_object`. The schema is passed to the model
  as is and validated with `jsonschema`, so nested objects and arrays work. There is no separate forced-function
  variant: whether the result comes back as `content` or as a tool call is decided by the OpenAI endpoint, which
  remembers how it was asked.
- **The result is `LLMStopEvent.structured_output`**, the parsed and validated JSON. The answer text holds the same
  JSON, so clients that read text keep working. RAG and Expert RAG end on their own stop events and have no place for
  it.
- **The answering model call is asked for the shape.** `EventDisplayer.display_llm_stream(..., response_schema=...)`
  sends `response_format` next to `tools` when the model declares `supports_response_schema`.
  - LLM Wrapping, Web Fetch and Few-Shot pass the schema in their answering step.
  - The tool loop passes it only on a turn without tools. Sent next to the tools on a live check, the shape decided
    the first turn: the Universal Agent answered at once with an invoice it made up instead of reading the attached
    one. A reply given with tools is put into the shape by the completion.
  - Every call asked for a shape is told, in its leading system message (`ResponseSchemaInstruction`), to take values
    only from the conversation and its documents and to use null otherwise. Without it an undated invoice came back
    dated with the day from the agent's system prompt.
  - The schema reaches these steps through the run context, read with `RequestedResponseSchema`, a sibling of
    `RequestedFeatures`.
- **`Conversation.complete` validates.** With a schema requested, the completion parses the answer instead of generating
  follow-up questions.
  - When the answer does not match, `StructuredAnswer` asks the model once more, non-streamed, from the same prompt with
    the validation error and the schema. A second miss fails the run.
  - This covers a model without structured outputs, one that ignored them, and a blueprint that did not pass the schema
    (MCP ReAct, Knowledge Extraction).
- **The meta-question gate is skipped** for a message with a schema. Its answer is prose that ends the run before the
  completion. A refusal handed to the completion stays a refusal.
- **Support is derived, never declared.** `Agent.supports_response_schema()` holds when a step returns
  `CompleteConversationEvent` and every declared completion stop is an `LLMStopEvent`. Discovery announces it, the class
  entity and the agent DTOs carry it, and the per-agent endpoints answer a schema sent to an agent without support with
  400\.

Rejected alternatives:

- *A second structuring call after every text answer*: it works for every blueprint unchanged, but it doubles the input
  tokens on every structured call, and the answer the caller sees is not the one the model wrote.
- *A dedicated `StructuredStopEvent`*: RAG's typed stops would need parallel structured subclasses, and the API would
  have to know them all.
- *A separate result event ahead of the stop*: the result would no longer be on the event that ends the run, which is
  what the per-agent endpoints return.

## Consequences

- One structured answer costs one model call when the model honours `response_format`, and two when it does not. A
  tool-loop answer usually costs the correction call too, since its last turn still offers tools.
- The answering step streams the JSON as chunks, so the chat shows the JSON as it is written. A corrected answer shows a
  thought, and the corrected JSON arrives only on the stop event; API clients must read the result from the stop event.
- The answering call keeps the model's thinking. A reasoning model whose provider breaks JSON with thinking on is
  corrected by the completion's second call, which runs without streaming.
- `UserMessageEvent` grows by one optional field. Chat clients ignore it.
- The API's model rebuild (`ModelCreationService`) now also restores free-form maps announced as optional (`anyOf` map
  or null) and maps inside optional nested models. Before, the caller's `json_schema` lost every key but `properties`.
