---
title: Events Reference
---

# Events Reference

Events are the fundamental communication mechanism in the agent framework. This page provides a complete reference for
the event hierarchy, how to choose the right base event, and a catalog of all available events.

## Control vs display vs combined events

The framework distinguishes between event categories based on their effect on the workflow:

| Category                | Base class               | Triggers dispatcher | Use case                                      |
| ----------------------- | ------------------------ | ------------------- | --------------------------------------------- |
| **Control**             | `ControlEvent`           | Yes                 | Workflow state transitions, step dependencies |
| **Display**             | `DisplayEvent`           | No                  | UI updates, streaming output, observability   |
| **Control and Display** | `ControlAndDisplayEvent` | Yes                 | Both: advances workflow AND shows in UI       |

**Control events** influence the workflow's control flow. When a `ControlEvent` is published, the dispatcher evaluates
all steps to determine if any new steps should execute. Only `ControlEvent` types (or subclasses) can satisfy step input
requirements.

**Display events** do not trigger the dispatcher. Use them for high-frequency updates that should appear in the UI but
should not cause step re-evaluation. A streamed LLM response may emit hundreds of `ChunkEvent` instances per minute;
making these control events would cause unnecessary dispatcher overhead.

**Combined events** need both behaviors — they influence workflow AND appear in the UI. Most semantic events
(`LLMEvent`, `RetrieverEvent`, etc.) inherit from `ControlAndDisplayEvent`.

**Protocol events are combined events.** Calls between steps and capabilities, such as a capability request and its
result or a tool-loop decision, are part of the protocol, and an admin reading a run needs to see them. The event
history lists display events only, so these inherit from `ControlAndDisplayEvent` and give themselves a `_display_name`
and `_display_description`. The description is a short progress phrase ("Recalling memories"), since chat clients such
as OpenWebUI show it as a live status while the agent works. Each one also has a component in the admin UI's event
history. Keep plain `ControlEvent` for internal bookkeeping no reader needs. Only the dispatcher's JetStream copy
triggers steps; the display copy goes out over NATS Core and never re-triggers anything.

```python
from swiss_ai_hub.core.events.control.control_event import ControlEvent
from swiss_ai_hub.core.events.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.control_and_display_event import ControlAndDisplayEvent

# Control event: triggers dispatcher, can satisfy step dependencies
class AnalysisCompleteEvent(ControlEvent):
    summary: str

# Display event: does NOT trigger dispatcher, UI-only
class ProgressUpdateEvent(DisplayEvent):
    percent_complete: float
    status_message: str

# Combined: triggers dispatcher AND displays in UI
class RetrieveEvent(ControlAndDisplayEvent):
    nodes: list[IngestedNode]
```

## Events as flow carriers

Events serve two distinct purposes:

1. **Data carriers:** Transporting values between steps
2. **Flow carriers:** Controlling execution order independent of data

A step may depend on an event solely to ensure execution ordering, without requiring any data from it:

```python
class PathA(ControlEvent):
    pass  # No fields — pure flow control

class PathB(ControlEvent):
    pass

@step()
async def decide(self, event: StartEvent) -> PathA | PathB:
    if condition():
        return PathA()
    return PathB()

@step()
async def handle_path_a(self, _: PathA) -> StopEvent:
    # Underscore signals: "I need this event for flow control, not data"
    return StopEvent()
```

The `_: EventType` convention indicates dependency on an event's existence rather than its contents. This pattern is
essential for:

- **Conditional branching:** Different steps execute based on which event type was emitted
- **Sequencing:** Ensuring step B waits for step A without needing A's output data
- **Synchronization barriers:** Waiting for a signal that work completed

## Event hierarchy

```
BaseEvent
├── ControlEvent                    # Triggers dispatcher
│   ├── StartEvent                  # Workflow entry points
│   │   └── UserMessageEvent        # User-initiated workflow
│   ├── StopEvent                   # Workflow termination
│   └── ExceptionEvent              # Error signaling
│
├── DisplayEvent                    # UI-only, no dispatcher trigger
│   ├── ChunkEvent                  # Streaming text chunks
│   ├── ThoughtEvent                # Agent reasoning display
│   └── CostEvent                   # Cost tracking display
│       └── LLMCostEvent            # LLM-specific costs
│
├── ControlAndDisplayEvent          # Both behaviors
│   ├── SemanticEvent               # OpenInference-compatible (OTEL/Phoenix/Langfuse)
│   │   ├── LLMEvent                # LLM invocation
│   │   │   └── LLMStopEvent        # Terminal LLM response
│   │   ├── RetrieverEvent          # Document retrieval
│   │   ├── RerankerEvent           # Result reranking
│   │   ├── EmbeddingEvent          # Embedding generation
│   │   ├── ToolEvent               # Tool invocation
│   │   ├── GuardEvent              # Guardrail evaluation
│   │   ├── ChainEvent              # Chain execution
│   │   └── AgentEvent              # Agent invocation
│   │
│   ├── HumanInTheLoopRequestEvent  # HITL requests
│   ├── HumanInTheLoopResponseEvent # HITL responses
│   ├── AgentInTheLoopRequestEvent  # AITL delegation
│   ├── AgentInTheLoopResponseEvent # AITL results
│   ├── BotInTheLoopRequestEvent    # BITL Teams/Slack requests
│   ├── BotInTheLoopResponseEvent   # BITL responses
│   │
│   ├── BaseRetrieveMemoryEvent     # Memory retrieval
│   │   ├── RetrieveUserMemoryEvent
│   │   └── RetrieveOrganizationMemoryEvent
│   ├── BaseStoreMemoryEvent        # Memory persistence
│   │   ├── StoreUserMemoryEvent
│   │   └── StoreOrganizationMemoryEvent
│   │
│   └── RouterEvent                 # LLM routing decisions
```

## Choosing the right base event

When creating a custom event, inherit from the most specific applicable base class:

| If your event represents...      | Inherit from                                                  | Benefits                                    |
| -------------------------------- | ------------------------------------------------------------- | ------------------------------------------- |
| Workflow start condition         | `StartEvent`                                                  | Recognized as entry point                   |
| User message initiating workflow | `UserMessageEvent`                                            | Chat history, locale, user identity         |
| Workflow termination             | `StopEvent`                                                   | Signals completion                          |
| Error/failure                    | `ExceptionEvent`                                              | Error handling patterns                     |
| LLM invocation result            | `LLMEvent`                                                    | Token counts, messages, OpenInference spans |
| LLM terminal response            | `LLMStopEvent`                                                | Combines LLM data with workflow termination |
| Document retrieval               | `RetrieverEvent`                                              | Retrieved nodes, OpenInference spans        |
| Reranking operation              | `RerankerEvent`                                               | Input/output nodes, OpenInference spans     |
| Embedding generation             | `EmbeddingEvent`                                              | Vectors, model info, OpenInference spans    |
| Tool/function call               | `ToolEvent`                                                   | Tool name, parameters, OpenInference spans  |
| Guardrail check                  | `GuardEvent`                                                  | Guard result, OpenInference spans           |
| Human approval needed            | `HumanInTheLoopRequestEvent`                                  | Workflow suspension, UI prompt              |
| Agent delegation                 | `AgentInTheLoopRequestEvent`                                  | Cross-agent communication                   |
| Memory retrieval                 | `RetrieveUserMemoryEvent` / `RetrieveOrganizationMemoryEvent` | Memory search results                       |
| Memory storage                   | `StoreUserMemoryEvent` / `StoreOrganizationMemoryEvent`       | Memory persistence confirmation             |
| Streaming text chunk             | `ChunkEvent`                                                  | Real-time UI updates (display-only)         |
| Agent thought/reasoning          | `ThoughtEvent`                                                | Transparency display (display-only)         |
| Cost information                 | `LLMCostEvent`                                                | Token usage, pricing (display-only)         |
| Generic workflow state           | `ControlAndDisplayEvent`                                      | Triggers dispatcher + UI display            |
| Generic UI update                | `DisplayEvent`                                                | UI-only, no dispatcher overhead             |

## Semantic events and OpenInference

`SemanticEvent` subclasses implement the `to_semantic_convention()` method, producing attributes compatible with the
[OpenInference specification](https://github.com/Arize-ai/openinference). This enables integration with:

- **Arize Phoenix:** Trace visualization and debugging
- **Langfuse:** LLM observability and analytics
- **Any OpenTelemetry-compatible system:** Standard span attributes

```python
from swiss_ai_hub.core.events.semantic import RetrieverEvent

# RetrieverEvent automatically exports OpenInference attributes:
# - openinference.span.kind: "RETRIEVER"
# - retrieval.documents.{i}.document.id
# - retrieval.documents.{i}.document.content
# - retrieval.documents.{i}.document.score

event = RetrieverEvent.from_nodes(retrieved_nodes)
otel_attributes = event.to_semantic_convention()
```

When building agents that require observability, prefer semantic events over generic `ControlAndDisplayEvent`:

```python
# Preferred: semantic event for observability
from swiss_ai_hub.core.events.semantic import RetrieverEvent

@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieverEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieverEvent.from_nodes(nodes)  # OpenInference-compatible

# Discouraged: generic event loses observability benefits
class MyRetrieveEvent(ControlAndDisplayEvent):
    nodes: list[NodeWithScore]  # No OpenInference integration
```

## Available events reference

### Control events (trigger dispatcher)

| Event            | Module                             | Purpose                           |
| ---------------- | ---------------------------------- | --------------------------------- |
| `ControlEvent`   | `control.ControlEvent`             | Base class for all control events |
| `StartEvent`     | `control.start.StartEvent`         | Workflow entry point              |
| `StopEvent`      | `control.stop.StopEvent`           | Workflow termination              |
| `ExceptionEvent` | `control.exception.ExceptionEvent` | Error signaling                   |

### Display events (UI only)

| Event          | Module                 | Purpose                       |
| -------------- | ---------------------- | ----------------------------- |
| `DisplayEvent` | `display.DisplayEvent` | Base class for display events |
| `ChunkEvent`   | `display.ChunkEvent`   | Streaming text output         |
| `ThoughtEvent` | `display.ThoughtEvent` | Agent reasoning transparency  |
| `CostEvent`    | `cost.CostEvent`       | Cost tracking base            |
| `LLMCostEvent` | `cost.LLMCostEvent`    | LLM token/cost reporting      |

### Semantic events (OpenInference compatible)

| Event            | Module                              | OpenInference span kind |
| ---------------- | ----------------------------------- | ----------------------- |
| `SemanticEvent`  | `semantic.SemanticEvent`            | Base class (abstract)   |
| `LLMEvent`       | `semantic.llm.LLMEvent`             | `LLM`                   |
| `LLMStopEvent`   | `semantic.llm.LLMStopEvent`         | `LLM` (terminal)        |
| `RetrieverEvent` | `semantic.retriever.RetrieverEvent` | `RETRIEVER`             |
| `RerankerEvent`  | `semantic.reranker.RerankerEvent`   | `RERANKER`              |
| `EmbeddingEvent` | `semantic.embedding.EmbeddingEvent` | `EMBEDDING`             |
| `ToolEvent`      | `semantic.tool.ToolEvent`           | `TOOL`                  |
| `GuardEvent`     | `semantic.guard.GuardEvent`         | `GUARDRAIL`             |
| `ChainEvent`     | `semantic.chain.ChainEvent`         | `CHAIN`                 |
| `AgentEvent`     | `semantic.agent.AgentEvent`         | `AGENT`                 |

### Interaction events

| Event                                    | Module                        | Purpose                             |
| ---------------------------------------- | ----------------------------- | ----------------------------------- |
| `UserMessageEvent`                       | `user.UserMessageEvent`       | User-initiated workflow start       |
| `HumanInTheLoopRequestEvent`             | `human_in_the_loop.request`   | Base class for HITL requests        |
| `HumanInTheLoopInputRequestEvent`        | `human_in_the_loop.request`   | Popup with text input field         |
| `HumanInTheLoopConfirmationRequestEvent` | `human_in_the_loop.request`   | Yes/No button selection             |
| `HumanInTheLoopChatRequestEvent`         | `human_in_the_loop.request`   | Chat message (fallback)             |
| `HumanInTheLoopResponseEvent`            | `human_in_the_loop.response`  | Base class for HITL responses       |
| `AgentInTheLoopRequestEvent`             | `agent_in_the_loop.request`   | Delegate to another agent           |
| `AgentInTheLoopResponseEvent`            | `agent_in_the_loop.response`  | Delegated agent result              |
| `AgentInTheLoopExceptionEvent`           | `agent_in_the_loop.exception` | Delegated agent failure             |
| `BotInTheLoopRequestEvent`               | `bot_in_the_loop.request`     | Send message to Teams/Slack channel |
| `BotInTheLoopResponseEvent`              | `bot_in_the_loop.response`    | Response from Teams/Slack user      |

**HITL helper classes** (not events, but workflow utilities):

| Helper                       | UI behavior                                           |
| ---------------------------- | ----------------------------------------------------- |
| `HumanInTheLoopInput`        | Popup dialog for free-form text entry                 |
| `HumanInTheLoopConfirmation` | Yes/No button selection                               |
| `HumanInTheLoopChat`         | Message in chat stream (fallback for simple UIs/APIs) |

### Memory events

| Event                             | Module            | Purpose                      |
| --------------------------------- | ----------------- | ---------------------------- |
| `BaseRetrieveMemoryEvent`         | `memory.retrieve` | Memory retrieval base        |
| `RetrieveUserMemoryEvent`         | `memory.retrieve` | User-scoped memory retrieval |
| `RetrieveOrganizationMemoryEvent` | `memory.retrieve` | Org-scoped memory retrieval  |
| `BaseStoreMemoryEvent`            | `memory.store`    | Memory storage base          |
| `StoreUserMemoryEvent`            | `memory.store`    | User-scoped memory storage   |
| `StoreOrganizationMemoryEvent`    | `memory.store`    | Org-scoped memory storage    |
| `AddMemoryToChatHistoryEvent`     | `memory.history`  | Extended chat history        |

### Guard events

| Event                            | Module                      | Purpose                      |
| -------------------------------- | --------------------------- | ---------------------------- |
| `GuardAcceptEvent`               | `guard.GuardAcceptEvent`    | Guard passed                 |
| `GuardRejectionEvent`            | `guard.GuardRejectionEvent` | Guard rejected               |
| `AgentSuitabilityAcceptEvent`    | `guard`                     | Agent can handle request     |
| `AgentSuitabilityRejectEvent`    | `guard`                     | Agent cannot handle request  |
| `ContextSufficientAcceptEvent`   | `guard`                     | Sufficient context available |
| `ContextInsufficientRejectEvent` | `guard`                     | Insufficient context         |
| `SensitiveInfoAcceptEvent`       | `guard`                     | No sensitive info detected   |
| `SensitiveInfoRejectEvent`       | `guard`                     | Sensitive info detected      |

### Capability events

Requests and results of the capabilities every chat blueprint calls (see the agent SDK's capabilities). All of them are
`ControlAndDisplayEvent`s, unless noted otherwise.

| Event                             | Module                           | Purpose                                                               |
| --------------------------------- | -------------------------------- | --------------------------------------------------------------------- |
| `ContextualizeConversationEvent`  | `conversation`                   | Asks for the turn's query, meta-question gate and title               |
| `ConversationContextualizedEvent` | `conversation`                   | The limited history and the query the turn is answered for            |
| `ComposeContextEvent`             | `conversation`                   | Asks for the prompt with context blocks merged in                     |
| `ContextComposedEvent`            | `conversation`                   | The history the model receives, within the input budget               |
| `CompleteConversationEvent`       | `conversation`                   | Ends the turn: follow-up questions, then the stop event               |
| `NotAMetaQuestionEvent`           | `self_awareness`                 | The message is a normal request; releases the entry steps             |
| `RecallMemoryEvent`               | `memory.recall`                  | Asks for the user and organization memories relevant to a query       |
| `MemoryRecalledEvent`             | `memory.recall`                  | One block per memory scope                                            |
| `MemoryStorageRequestedEvent`     | `memory.request`                 | Starts the memory writer's own run, without waiting for it            |
| `SearchKnowledgeEvent`            | `knowledge`                      | Asks for the referenced collections' best sections for a query        |
| `KnowledgeSearchedEvent`          | `knowledge`                      | The block found and its sections, listed as sources                   |
| `ReadAttachedFilesEvent`          | `attached_file`                  | Asks for the message's files, fitted to the room left                 |
| `AttachedFilesReadEvent`          | `attached_file`                  | The files' contents as one context block                              |
| `AttachedFileEvent`               | `attached_file` (`DisplayEvent`) | One file: the text the model received, its status and its citation id |

### Tool-loop events

The model deciding which tools to use, until it is done. All of them are `ControlAndDisplayEvent`s unless noted. The
loop's state travels on these events, so the history shows every iteration.

| Event                       | Module                       | Purpose                                                         |
| --------------------------- | ---------------------------- | --------------------------------------------------------------- |
| `RunToolLoopEvent`          | `tool_loop`                  | Asks the loop to run a tool set, answering or gathering context |
| `ToolLoopIterationEvent`    | `tool_loop`                  | The model's turn to decide, one per iteration                   |
| `ToolCallsDecidedEvent`     | `tool_loop`                  | The tools the model chose this iteration                        |
| `ToolCallApprovedEvent`     | `tool_loop`                  | One call cleared to run, after any approval                     |
| `ToolResultEvent`           | `tool_loop`                  | One call's result, shown in the tool's block in the chat        |
| `ToolLoopFinishedEvent`     | `tool_loop`                  | The reply (answering) or the gathered context (gathering)       |
| `ToolLoopStatusEvent`       | `tool_loop` (`DisplayEvent`) | What the loop is doing while it gathers in the background       |
| `ToolLoopCondensedEvent`    | `tool_loop` (`DisplayEvent`) | Earlier results or turns condensed to fit the model's context   |
| `ToolApprovalRequestEvent`  | `tool_loop`                  | A yes/no confirmation before a tool runs (a HITL request)       |
| `ToolApprovalResponseEvent` | `tool_loop`                  | The user's answer to it                                         |

### Utility events

| Event                              | Module                         | Purpose                |
| ---------------------------------- | ------------------------------ | ---------------------- |
| `RouterEvent`                      | `router.RouterEvent`           | LLM routing decision   |
| `LanguageEvent`                    | `common.LanguageEvent`         | Language detection     |
| `LimitChatHistoryEvent`            | `common.LimitChatHistoryEvent` | Truncated history      |
| `StandaloneQuestionCondenserEvent` | `common`                       | Question reformulation |

## Custom events

Custom events are Pydantic models. All fields require type annotations:

```python
from swiss_ai_hub.core.events.control.control_event import ControlEvent

class AnalysisCompleteEvent(ControlEvent):
    summary: str
    confidence: float
    findings: list[str]
    metadata: dict | None = None
```

::: warning The stop event constraint
No step may depend on `StopEvent` or any subclass as an input parameter. When a `StopEvent` is emitted, the run
terminates and subsequent steps are not scheduled. See the
[execution model](../9_execution_model/#the-dangling-stop-violation) for details and the correct pattern.
:::
