---
name: nats-events
description: >-
  Reference for NATS messaging, JetStream, and the Swiss AI Agent Protocol. Use when user says
  'how to publish an event', 'create a subscriber', 'NATS subject format', 'event hierarchy',
  'add a new event type', 'JetStream consumer setup', 'RPC pattern', 'Control vs Display event',
  'TopicManager usage', 'how events flow between services', or 'NATS connection config'. Covers
  events, pub/sub, RPC, topics, streams, dispatchers, and tracing.
arguments:
  - name: topic
    description: Topic or question (e.g., "publish event", "RPC pattern", "event hierarchy", "JetStream consumer")
---

# NATS & Events -- Swiss AI Agent Protocol Reference

Look up NATS/event information. Topic or question via `$ARGUMENTS`.

---

## Architecture Overview

The platform uses **NATS** as its central message bus with two tiers:

| Tier          | Protocol                          | Durability                    | Use Case                                    |
| ------------- | --------------------------------- | ----------------------------- | ------------------------------------------- |
| **NATS Core** | `nc.publish()` / `nc.subscribe()` | Ephemeral (fire-and-forget)   | Display events, discovery, real-time UI     |
| **JetStream** | `js.publish()` / `js.subscribe()` | Persistent (30-day retention) | Control events, workflow state, audit trail |

**Key Rule**: Control events go through JetStream (durable). Display events go through NATS Core (ephemeral).

---

## Swiss AI Agent Protocol (SAAP)

### Event Classification

All events inherit from `BaseEvent` and are classified into two categories:

| Category          | Base Class               | Purpose                    | Transport     | Failure Impact      |
| ----------------- | ------------------------ | -------------------------- | ------------- | ------------------- |
| **Control Event** | `ControlEvent`           | Drives workflow execution  | JetStream     | Breaks agent logic  |
| **Display Event** | `DisplayEvent`           | Observability / UI updates | NATS Core     | No workflow impact  |
| **Both**          | `ControlAndDisplayEvent` | Workflow + user-visible    | Both channels | Depends on consumer |

**Core Rule**: Only `ControlEvent` types trigger agent `@step()` methods. Display events MUST NEVER influence workflow
logic.

### Event Hierarchy

```
BaseEvent
├── ControlEvent (workflow-driving)
│   └── ControlAndDisplayEvent (hybrid: workflow + UI)
│       ├── StartEvent
│       │   └── UserMessageEvent (user chat message)
│       ├── StopEvent (run completed)
│       ├── SemanticEvent (OpenInference tracing)
│       │   ├── ExceptionEvent (error, halts run)
│       │   ├── LLMEvent (LLM call details)
│       │   ├── AgentEvent (agent tracing)
│       │   ├── ChainEvent (chain tracing)
│       │   ├── RetrieverEvent (RAG retrieval)
│       │   ├── RerankerEvent (reranking)
│       │   ├── GuardEvent (safety checks)
│       │   ├── ToolEvent (tool invocation)
│       │   └── EmbeddingEvent (vector generation)
│       ├── RouterEvent (LLM routing decision)
│       ├── BaseRetrieveMemoryEvent
│       │   ├── RetrieveUserMemoryEvent
│       │   └── RetrieveOrganizationMemoryEvent
│       ├── BaseStoreMemoryEvent
│       │   ├── StoreUserMemoryEvent
│       │   └── StoreOrganizationMemoryEvent
│       ├── HumanInTheLoopRequestEvent (pause for human input)
│       │   ├── HumanInTheLoopInputRequestEvent
│       │   ├── HumanInTheLoopConfirmationRequestEvent
│       │   └── HumanInTheLoopChatRequestEvent
│       ├── HumanInTheLoopResponseEvent[T] (human replied)
│       ├── AgentInTheLoopRequestEvent (delegate to agent)
│       ├── AgentInTheLoopResponseEvent (agent replied)
│       └── AgentInTheLoopExceptionEvent (agent failed)
│   ├── LanguageEvent
│   └── BotInTheLoopRequestEvent (ask via Slack/Teams)
│
├── DisplayEvent (observability-only)
│   ├── ThoughtEvent (agent reasoning)
│   ├── ChunkEvent (streaming text tokens)
│   ├── CostEvent
│   │   └── LLMCostEvent (token costs)
│   └── (All ControlAndDisplayEvent types also publish as display)
│
├── ProcessEvent (process orchestration)
│   ├── WorkEvent (work completed)
│   │   ├── ProcessStartEvent
│   │   ├── ProcessStopEvent
│   │   ├── ProcessExceptionEvent
│   │   ├── HumanWorkEvent (human submitted form)
│   │   └── ProgramWorkEvent (program submitted data)
│   └── WorkRequestEvent (delegate work)
│       ├── HumanWorkRequestEvent (ask human with forms)
│       └── ProgramWorkRequestEvent (ask program)
│
├── ClassDiscoveryRequestEvent (query agent/process metadata)
├── AgentClassDiscoveryResponseEvent (agent metadata)
├── ProcessClassDiscoveryResponseEvent (process metadata)
└── SourceUpdatedEvent (pipeline trigger)
```

### BaseEvent Core Fields

```python
class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: int = Field(default_factory=time.time_ns)  # Nanosecond precision
    _event_name: str  # Computed: class name (used for deserialization)
    _parent_event_names: list[str]  # Computed: inheritance chain
    _jetstream_sequence: int | None  # JetStream sequence number (set by subscriber)
```

**Auto-Registration**: Every `BaseEvent` subclass auto-registers in `_event_registry` via `__pydantic_init_subclass__`.
No manual registration needed.

**Deserialization**: `BaseEvent.deserialize_event(data)` looks up `_event_name` in registry, falls back to parent
classes, preserves unknown fields.

**Type Checking Properties**:

```python
event.is_control_event      # "ControlEvent" in _parent_event_names
event.is_display_event      # "DisplayEvent" in _parent_event_names
event.is_semantic_event     # "SemanticEvent" in _parent_event_names
event.is_start_event        # "StartEvent" in _parent_event_names
event.is_stop_event         # "StopEvent" in _parent_event_names
event.is_work_event         # "WorkEvent" in _parent_event_names
event.is_work_request_event # "WorkRequestEvent" in _parent_event_names
event.is_chunk_event        # isinstance check
event.is_hitl_response_event  # isinstance check
```

---

## NATS Subject (Topic) System

### Agent Subject Pattern

```
agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}
  0        1             2          3            4           5         6            7            8
```

| Segment       | Example                           | Purpose                           |
| ------------- | --------------------------------- | --------------------------------- |
| `agent_class` | `RAGAgent`                        | Agent blueprint type              |
| `agent_id`    | `wiki_agent`                      | Specific agent instance           |
| `thread_id`   | `t948a201...`                     | Conversation context (ObjectId)   |
| `display_id`  | `d135bfc9...`                     | UI display grouping (ObjectId)    |
| `run_id`      | `r4fg68bb...`                     | Single execution trace (ObjectId) |
| `event_type`  | `control_event` / `display_event` | Event classification              |
| `event_name`  | `ChunkEvent`                      | Event class name                  |
| `event_id`    | `e423...`                         | Unique event instance ID          |

### Process Subject Pattern

```
process.{process_class}.{process_id}.{walkthrough_id}.{event_type}.{event_name}.{event_id}
```

### RPC Subject Pattern

```
aihub.rpc.config.agent.{agent_class}.{agent_id}
aihub.rpc.config.process.{process_class}.{process_id}
```

### Discovery Subject Pattern

```
class_discovery.agent.{agent_class}.*.request.{call_id}
class_discovery.agent.{agent_class}.*.response.{call_id}
instance_discovery.agent.{agent_class}.{agent_id}.*.request.{call_id}
```

### Hierarchical Scoping (Thread > Display > Run)

| Scope       | Purpose                                        | Access Control                              |
| ----------- | ---------------------------------------------- | ------------------------------------------- |
| **Thread**  | Conversation context, long-lived (days/months) | Users granted access at thread level        |
| **Display** | UI grouping, can span multiple agents          | Shared or isolated between delegated agents |
| **Run**     | Single execution (StartEvent → StopEvent)      | Isolated per workflow invocation            |

**Security**: Users can only observe events from threads they're members of (`ThreadEntity.users`).

### Stream Naming

Streams are named per agent class: `agent_{agent_class}_stream` (e.g., `agent_RAGAgent_stream`).

---

## Topic Managers

Topic managers centralize subject construction. Never build subjects manually — use the appropriate manager.

### TopicManager Hierarchy

```
TopicManager (base: RPC_TOPIC, CLASS_DISCOVERY_TOPIC, INSTANCE_DISCOVERY_TOPIC)
├── AgentTopicManager (all-agent subjects, discovery, RPC)
│   ├── AgentClassTopicManager(agent_class) (class-level, streams)
│   │   ├── AgentInstanceTopicManager(agent_class, agent_id) (instance-level)
│   │   │   └── AgentThreadTopicManager(agent_class, agent_id, thread_id, display_id, run_id)
│   │   └── (get_stream() → stream_name, stream_subject)
│   └── (get_agent_config_rpc_subject, get_subject_for_all_*_events)
└── ProcessTopicManager (process equivalents)
    └── ProcessClassTopicManager(process_class)
```

### Common TopicManager Methods

```python
# AgentTopicManager — global agent subjects
tm = AgentTopicManager()
tm.get_subject_for_all_events_in_agent()          # agent.*.*.*.*.*.*.*.*
tm.get_subject_for_all_display_events_in_agent()   # agent.*.*.*.*.*.display_event.*.*
tm.get_subject_for_all_control_events_in_agent()   # agent.*.*.*.*.*.control_event.*.*
tm.get_agent_config_rpc_subject("*", "*")           # aihub.rpc.config.agent.*.*
tm.get_agent_class_discovery_subject_request(call_id)  # class_discovery.agent.*.*.request.{call_id}

# AgentClassTopicManager — per agent class
ctm = AgentClassTopicManager(agent_class="RAGAgent")
ctm.get_stream()  # ("agent_RAGAgent_stream", "agent.RAGAgent.>")
ctm.get_subject_for_all_control_events()  # agent.RAGAgent.*.*.*.*.control_event.*.*

# AgentThreadTopicManager — per thread context
ttm = AgentThreadTopicManager(agent_class="RAGAgent", agent_id="wiki", thread_id="t1", display_id="d1", run_id="r1")
ttm.get_subject_for_control_event_in_thread(event_name="StartEvent", event_id="e1")
ttm.get_subject_for_display_event_in_thread(event_name="ChunkEvent", event_id="e2")
```

**File locations**:

- `aihub_lib/aihub_lib/nats/topic_managers/TopicManager.py`
- `aihub_lib/aihub_lib/nats/topic_managers/agents/AgentTopicManager.py`
- `aihub_lib/aihub_lib/nats/topic_managers/agents/AgentClassTopicManager.py`
- `aihub_lib/aihub_lib/nats/topic_managers/agents/AgentInstanceTopicManager.py`
- `aihub_lib/aihub_lib/nats/topic_managers/agents/AgentThreadTopicManager.py`

---

## Publishers

### NCPublisher (NATS Core — Ephemeral)

```python
from aihub_lib.nats.publishers.NCPublisher import NCPublisher

publisher = NCPublisher("MyPublisher", nc)
await publisher.publish_event(event, subject)
```

**Characteristics**:

- Fire-and-forget, no retry
- Adds OpenTelemetry trace context headers
- Validates event-subject alignment (warns on mismatch)

### JSPublisher (JetStream — Persistent)

```python
from aihub_lib.nats.publishers.JSPublisher import JSPublisher

publisher = JSPublisher("MyPublisher", js)
await publisher.ensure_stream_exists(stream_name, stream_subject)
await publisher.publish_event(event, subject, retries=10)
```

**Characteristics**:

- Retry with 1s backoff, up to 10 attempts (configurable)
- 5-second timeout per attempt
- UUID message ID for deduplication
- ACK confirmation with sequence number
- Raises `RuntimeError` after all retries exhausted

### Publishing Decision Logic

```python
# In dispatchers — the standard pattern:
if event.is_control_event:
    await self.js_publisher.publish_event(event, control_subject)   # JetStream
if event.is_display_event:
    await self.nc_publisher.publish_event(event, display_subject)   # NATS Core
```

**Note**: `ControlAndDisplayEvent` types are published to **both** channels.

### Message Headers

```python
from aihub_lib.nats.tracing.NATSMessageHeaders import NATSMessageHeaders

headers = (
    NATSMessageHeaders()
    .with_trace_context()                          # OpenTelemetry W3C trace context
    .with_header("Nats-Msg-Id", str(uuid.uuid4()))  # Deduplication ID
    .to_dict()
)
```

---

## Subscribers

### NCSubscriber (NATS Core — Ephemeral)

```python
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber

subscriber = NCSubscriber(
    name="MySubscriber",
    nc=nc,
    subject="agent.*.*.*.*.*.display_event.*.*",
    event_cls=DisplayEvent,
    handler=my_handler,
)
await subscriber.start()
# ... later ...
await subscriber.stop()
```

**Handler signature**: `async def handler(event: TEvent, topic: Topic) -> None`

**Characteristics**:

- Ephemeral (no persistence, no replay)
- Non-blocking: spawns `asyncio.Task` per message
- Extracts trace context from headers

### JSSubscriber (JetStream — Durable with Queue Groups)

```python
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber

subscriber = JSSubscriber(
    name="MySubscriber",
    nc=nc,
    subject="agent.RAGAgent.*.*.*.*.control_event.*.*",
    stream_name="agent_RAGAgent_stream",
    stream_subject="agent.RAGAgent.>",
    queue_group="my-worker-group",  # Load balancing
    event_cls=ControlEvent,
    handler=my_handler,
    js=js,
)
await subscriber.start()
```

**Characteristics**:

- Ensures stream exists before subscribing
- Queue groups for load-balanced delivery across instances
- Immediate ACK (at-least-once semantics)
- Semaphore limits concurrent handlers to 1000
- Sets `event._jetstream_sequence` from message metadata

### Typed Subscriber Factories (Preferred)

Use the factory class methods instead of constructing subscribers directly:

```python
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber

# All display events from all agents (NATS Core)
sub = AgentNCSubscriber.for_all_agents_display_events(nc=nc, topic_manager=tm, handler=handler)

# All events from all agents (NATS Core)
sub = AgentNCSubscriber.for_all_agent_events(nc=nc, topic_manager=tm, handler=handler)

# Thread-scoped display events (NATS Core)
sub = AgentNCSubscriber.for_thread_display_events(nc=nc, topic_manager=thread_tm, handler=handler)

# All thread events including control (NATS Core)
sub = AgentNCSubscriber.for_all_thread_events(nc=nc, topic_manager=thread_tm, handler=handler)

# Discovery request events (NATS Core)
sub = AgentNCSubscriber.for_agent_class_discovery_request_events(nc=nc, topic_manager=tm, handler=handler)

# Control events for agent instance (JetStream, load-balanced)
sub = AgentJSSubscriber.for_agent_instance_control_events(
    nc=nc, topic_manager=instance_tm, handler=handler, queue_group="my-group", js=js
)
```

---

## RPC (Request-Reply)

### NCRequester (Client)

```python
from aihub_lib.nats.requester.NCRequester import NCRequester

requester = NCRequester(
    name="AgentConfig",
    nc=nc,
    response_cls=FetchAgentConfigResponse,
    default_timeout_ms=5000,
)

response = await requester.request(
    FetchAgentConfigRequest(agent_class="RAGAgent", agent_id="wiki"),
    subject="aihub.rpc.config.agent.RAGAgent.wiki",
    timeout_ms=5000,
)
```

### NCResponder (Server)

```python
from aihub_lib.nats.responder.NCResponder import NCResponder

responder = NCResponder(
    name="AgentConfig",
    nc=nc,
    subject="aihub.rpc.config.agent.*.*",  # Wildcards for all requests
    request_cls=FetchAgentConfigRequest,
    handler=handle_config_request,
)
await responder.start()
```

**Handler signature**: `async def handler(request: TRequest, subject: str) -> TResponse`

**Error handling**: On exception, responds with `{"error": str, "error_type": str}`. Requester raises `TimeoutError` on
no response.

### High-Level RPC Client (Preferred)

```python
from aihub_lib.nats.rpc.AgentConfigClient import AgentConfigClient

client = AgentConfigClient(nc=nc, timeout_ms=5000)
config = await client.fetch_config(agent_class="RAGAgent", agent_id="wiki")
```

### RPC Models

```python
# aihub_lib/aihub_lib/nats/rpc/models.py
class FetchAgentConfigRequest(BaseModel):
    agent_class: str
    agent_id: str

class FetchAgentConfigResponse(BaseModel):
    agent_class: str
    agent_id: str
    config: dict[str, Any]
    found: bool = True
    error: str | None = None
```

---

## JetStream Event Store

The `JetStreamEventStore` provides durable event storage with full-history replay.

### Startup Sequence

1. Ensure stream exists via `StreamManager`
2. Subscribe to new control events (push consumer, durable)
3. Replay ALL historical events (pull consumer with `DeliverPolicy.ALL`)
4. Delete temporary replay consumer
5. Cache events in `TTLCache(maxsize=100_000, ttl=30 days)`

### Stream Configuration

```python
StreamConfig(
    name="agent_RAGAgent_stream",
    subjects=["agent.RAGAgent.>"],
    storage=StorageType.FILE,           # Persistent disk storage
    retention=RetentionPolicy.LIMITS,   # Bounded by count/age
    max_msgs=10_000_000,                # Max messages
    discard=DiscardPolicy.OLD,          # Evict oldest
    max_age=60 * 60 * 24 * 30,         # 30 days
    duplicate_window=60,                # 60s dedup window
)
```

### JSPoller (Pull Consumer)

```python
from aihub_lib.nats.polling.JSPoller import JSPoller

poller = JSPoller(js=js, stream_name="...", stream_subject="...", consumer_name="...")
await poller.ensure_consumer_exists(
    deliver_policy=DeliverPolicy.ALL,   # ALL, NEW, LAST_PER_SUBJECT
    ack_policy=AckPolicy.EXPLICIT,      # EXPLICIT, NONE, ALL
    max_deliver=3,
    filter_subject="...",
)

async for msg in poller.poll(batch_size=100, timeout=1.0):
    process(msg.event)
    await msg.ack()
```

---

## Dispatcher Architecture

The `BaseDispatcher` orchestrates event processing using both publishers and the event store:

```python
class BaseDispatcher(abc.ABC):
    nc_publisher: NCPublisher       # Display events (ephemeral)
    js_publisher: JSPublisher       # Control events (durable)
    event_store: JetStreamEventStore  # Event history + replay
    step_store: StepStore           # Step state in Redis (ephemeral)
```

### AgentDispatcher Flow

1. **Receive** `ControlEvent` via `JSSubscriber` (queue group for load balancing)
2. **Lookup** which `@step()` methods accept this event type
3. **Create** fresh agent instance with `RunContext` and `ThreadContext`
4. **Execute** step method → returns new event(s)
5. **Publish** result:
   - `ControlEvent` → JetStream (durable)
   - `DisplayEvent` → NATS Core (ephemeral)
   - `ControlAndDisplayEvent` → both

### ProcessDispatcher Flow

1. **Receive** `WorkEvent` (human/agent/program completed work)
2. **Lookup** which `@process_step()` methods accept this event type
3. **Execute** step → returns `WorkRequestEvent` (delegate to next entity)
4. **Publish** request to appropriate entity

---

## Event Flow: End-to-End

### User Query → Agent Response

```
Frontend → API Gateway (POST /agents/{class}/{id}/{event}/stream)
    ↓
API Gateway → ExternalAgentEventDistributor
    ↓  validates thread membership, creates run_id
    ↓  publishes UserMessageEvent as ControlEvent
NATS (JetStream) → agent.RAGAgent.wiki.thread1.display1.run1.control_event.UserMessageEvent.e1
    ↓
AgentDispatcher (JSSubscriber, queue group)
    ↓  receives ControlEvent, executes @step()
    ↓  agent publishes ChunkEvent (display), StopEvent (control+display)
NATS (Core) → agent.RAGAgent.wiki.thread1.display1.run1.display_event.ChunkEvent.e2
    ↓
API (NCSubscriber) → EventPersister (MongoDB) + WebSocketSender (UI)
    ↓
Frontend WebSocket ← ContextualizedAgentEvent { event, agent_class, thread_id, ... }
```

### Parallel API Subscribers

The API creates two subscribers on startup:

| Subscriber            | Subject                                            | Handler                         | Purpose                |
| --------------------- | -------------------------------------------------- | ------------------------------- | ---------------------- |
| `AgentEventPersister` | `agent.*.*.*.*.*.*.*.*` (all events)               | `persister.persist_agent_event` | MongoDB audit log      |
| `WebSockets`          | `agent.*.*.*.*.*.display_event.*.*` (display only) | `ws_sender.send_event`          | Real-time UI streaming |

### SSE Streaming (OpenAI-compatible)

The API creates **temporary per-request subscribers** for SSE streams:

```python
# ChatService creates temporary subscriber → queue → SSE generator
subscriber = AgentNCSubscriber.for_thread_display_events(nc=nc, topic_manager=ttm, handler=queue_handler)
await subscriber.start()

# SSE generator consumes from queue
async def sse_event_generator():
    while not stop_signal.is_set():
        chunk = await chunk_queue.get()
        yield f"data: {chunk.model_dump_json()}\n\n"
```

---

## NATS Connection & Configuration

### NatsSettings

```python
# aihub_lib/aihub_lib/infrastructure/nats/NatsSettings.py
class NatsSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("NATS_")
    ENDPOINT: str                    # NATS_ENDPOINT (e.g., "nats://localhost:4222")
    TOKEN: SecretStr | None = None   # NATS_TOKEN (optional auth token)

    @classmethod
    async def create_client(cls) -> NATS:
        settings = cls()
        nc = NATS()
        await nc.connect(servers=[settings.ENDPOINT], token=settings.TOKEN.get_secret_value() if settings.TOKEN else None)
        return nc
```

### FastAPI Dependency Injection

```python
# aihub_lib/aihub_lib/nats/dependencies/use_nats.py
from fastapi import Request, WebSocket

def use_nats(request: Request) -> NATS:
    return request.app.state.nc

def use_nats_ws(request: WebSocket) -> NATS:
    return request.app.state.nc
```

### Lifetime Manager (API Startup)

**File**: `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py`

Startup order:

1. MongoDB → Redis → Milvus → S3
2. **NATS** (`NatsSettings.create_client()`) → **JetStream** (`nc.jetstream()`)
3. Event persisters (NCSubscriber for all agent + process events)
4. WebSocket infrastructure (NCSubscriber for display events)
5. Event distributors (ExternalAgentEventDistributor, ExternalProcessEventDistributor)
6. RPC responders (AgentConfigResponder, ProcessConfigResponder)
7. Discovery services
8. Database initialization

Shutdown: reverse order, NATS closed in `finally` block.

### Environment Variables

| Variable        | Default  | Purpose                                    |
| --------------- | -------- | ------------------------------------------ |
| `NATS_ENDPOINT` | Required | Server URL (e.g., `nats://localhost:4222`) |
| `NATS_TOKEN`    | Optional | Token authentication                       |

### NATS Server Config

**Template**: `deployment/templates/configs/nats-config.conf.j2`

| Setting                      | Dev   | Prod   |
| ---------------------------- | ----- | ------ |
| `max_payload`                | 1MB   | 2MB    |
| `max_connections`            | 64    | 256    |
| `max_subscriptions`          | 1000  | 5000   |
| `max_pending`                | 512MB | 2GB    |
| JetStream `max_memory_store` | 512MB | 2GB    |
| JetStream `max_file_store`   | 10GB  | 50GB   |
| JetStream `sync_interval`    | 1m    | 2m     |
| JetStream `domain`           | `dev` | `prod` |

---

## OpenTelemetry Tracing

All publishers and subscribers automatically propagate trace context via NATS headers.

### Publisher Span Attributes

```python
span.set_attribute("messaging.system", "nats.jetstream")  # or "nats"
span.set_attribute("messaging.destination", subject)
span.set_attribute("messaging.operation", "publish")
span.set_attribute("jetstream.sequence", ack.seq)       # JSPublisher only
span.set_attribute("jetstream.stream", ack.stream)       # JSPublisher only
span.set_attribute("jetstream.attempt", attempt)          # JSPublisher retry
```

### Subscriber Span Attributes

```python
span.set_attribute("messaging.system", "nats.jetstream")
span.set_attribute("messaging.source", msg.subject)
span.set_attribute("messaging.operation", "receive")
span.set_attribute("event.type", event.event_name)
span.set_attribute("jetstream.sequence", msg.metadata.sequence.stream)  # JSSubscriber
span.set_attribute("jetstream.acked", True)  # JSSubscriber
```

### RPC Span Attributes

```python
span.set_attribute("messaging.operation", "request")  # or "respond"
span.set_attribute("rpc.request_type", request.__class__.__name__)
span.set_attribute("rpc.response_type", response_cls.__name__)
span.set_attribute("rpc.success", True)
```

### Trace Context Propagation

```python
# Publishing — inject context
headers = NATSMessageHeaders().with_trace_context().to_dict()

# Subscribing — extract context
parent_context = NATSTraceContextPropagator.extract_and_activate_trace_context(msg.headers)
with tracer.start_as_current_span(..., context=parent_context):
    ...
```

---

## Creating a New Event

### Step 1: Define the Event Class

```python
# aihub_lib/aihub_lib/nats/events/my_feature/MyEvent.py
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent

# Choose ONE base:
# - ControlEvent: workflow-driving only
# - DisplayEvent: UI/observability only
# - ControlAndDisplayEvent: both

class MyFeatureEvent(ControlAndDisplayEvent):
    """Signals that my feature completed."""

    _display_name: ClassVar[LocaleString] = from_i18n_path("events.my_feature.display_name")
    _display_description: ClassVar[LocaleString] = from_i18n_path("events.my_feature.description")

    result: str
    confidence: float
```

**No registration needed** — `__pydantic_init_subclass__` auto-registers the class.

### Step 2: Use in Agent Step

```python
@step()
async def my_step(self, ev: StartEvent) -> MyFeatureEvent:
    result = await do_work()
    return MyFeatureEvent(result=result, confidence=0.95)
```

### Step 3: Subscribe to It

```python
# The agent dispatcher handles this automatically for ControlEvents.
# For custom subscribers:
subscriber = NCSubscriber(
    name="MyFeatureHandler",
    nc=nc,
    subject="agent.*.*.*.*.*.control_event.MyFeatureEvent.*",
    event_cls=MyFeatureEvent,
    handler=my_handler,
)
```

---

## Creating a New Publisher/Subscriber Pair

### Custom Publisher

```python
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher

# For durable events:
js_pub = JSPublisher("MyServicePublisher", js)
await js_pub.ensure_stream_exists(stream_name, stream_subject)
await js_pub.publish_event(my_event, subject)

# For ephemeral events:
nc_pub = NCPublisher("MyServicePublisher", nc)
await nc_pub.publish_event(my_event, subject)
```

### Custom Subscriber with Factory Pattern

```python
class MyNCSubscriber(NCSubscriber[MyEvent]):
    @classmethod
    def for_all_my_events(
        cls,
        nc: NATS,
        topic_manager: MyTopicManager,
        handler: Callable[[MyEvent, MyTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        subject = topic_manager.get_subject_for_all_events()
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=MyEvent,
            handler=handler,
        )
```

---

## Key File Reference

### Core Infrastructure

| File                                                      | Purpose                |
| --------------------------------------------------------- | ---------------------- |
| `aihub_lib/aihub_lib/infrastructure/nats/NatsSettings.py` | NATS connection config |
| `aihub_lib/aihub_lib/nats/dependencies/use_nats.py`       | FastAPI DI             |

### Publishers

| File                                                       | Purpose              |
| ---------------------------------------------------------- | -------------------- |
| `aihub_lib/aihub_lib/nats/publishers/AbstractPublisher.py` | Publisher base class |
| `aihub_lib/aihub_lib/nats/publishers/NCPublisher.py`       | NATS Core publisher  |
| `aihub_lib/aihub_lib/nats/publishers/JSPublisher.py`       | JetStream publisher  |

### Subscribers

| File                                                              | Purpose                       |
| ----------------------------------------------------------------- | ----------------------------- |
| `aihub_lib/aihub_lib/nats/subscribers/AbstractSubscriber.py`      | Subscriber base class         |
| `aihub_lib/aihub_lib/nats/subscribers/NCSubscriber.py`            | NATS Core subscriber          |
| `aihub_lib/aihub_lib/nats/subscribers/JSSubscriber.py`            | JetStream subscriber          |
| `aihub_lib/aihub_lib/nats/subscribers/agent/AgentNCSubscriber.py` | Agent NC subscriber factories |
| `aihub_lib/aihub_lib/nats/subscribers/agent/AgentJSSubscriber.py` | Agent JS subscriber factories |

### RPC

| File                                                | Purpose                     |
| --------------------------------------------------- | --------------------------- |
| `aihub_lib/aihub_lib/nats/requester/NCRequester.py` | RPC client                  |
| `aihub_lib/aihub_lib/nats/responder/NCResponder.py` | RPC server                  |
| `aihub_lib/aihub_lib/nats/rpc/AgentConfigClient.py` | Agent config RPC client     |
| `aihub_lib/aihub_lib/nats/rpc/models.py`            | RPC request/response models |
| `aihub_api/aihub_api/rpc/AgentConfigResponder.py`   | Agent config RPC server     |

### Events

| File                                                                  | Purpose                                 |
| --------------------------------------------------------------------- | --------------------------------------- |
| `aihub_lib/aihub_lib/nats/events/BaseEvent.py`                        | Event base + registry + deserialization |
| `aihub_lib/aihub_lib/nats/events/control/ControlEvent.py`             | Workflow event base                     |
| `aihub_lib/aihub_lib/nats/events/display/DisplayEvent.py`             | UI event base                           |
| `aihub_lib/aihub_lib/nats/events/ControlAndDisplayEvent.py`           | Hybrid event base                       |
| `aihub_lib/aihub_lib/nats/events/control/start/StartEvent.py`         | Run start                               |
| `aihub_lib/aihub_lib/nats/events/control/stop/StopEvent.py`           | Run stop                                |
| `aihub_lib/aihub_lib/nats/events/control/exception/ExceptionEvent.py` | Error                                   |
| `aihub_lib/aihub_lib/nats/events/display/ChunkEvent.py`               | Streaming text                          |
| `aihub_lib/aihub_lib/nats/events/display/ThoughtEvent.py`             | Agent reasoning                         |
| `aihub_lib/aihub_lib/nats/events/user/UserMessageEvent.py`            | User chat message                       |

### Topics & Streams

| File                                                                  | Purpose               |
| --------------------------------------------------------------------- | --------------------- |
| `aihub_lib/aihub_lib/nats/topics/Topic.py`                            | Topic base + registry |
| `aihub_lib/aihub_lib/nats/topics/agents/AgentInstanceTopic.py`        | Full agent topic      |
| `aihub_lib/aihub_lib/nats/topic_managers/TopicManager.py`             | Subject builder base  |
| `aihub_lib/aihub_lib/nats/topic_managers/agents/AgentTopicManager.py` | Agent subjects        |
| `aihub_lib/aihub_lib/nats/streams/StreamManager.py`                   | Stream creation       |

### Dispatcher & Event Store

| File                                                                      | Purpose            |
| ------------------------------------------------------------------------- | ------------------ |
| `aihub_lib/aihub_lib/nats/dispatcher/BaseDispatcher.py`                   | Dispatcher base    |
| `aihub_lib/aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py` | Event store        |
| `aihub_lib/aihub_lib/nats/polling/JSPoller.py`                            | Pull consumer      |
| `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py`                  | Agent dispatcher   |
| `aihub_process/aihub_process/dispatchers/ProcessDispatcher.py`            | Process dispatcher |

### Tracing

| File                                                             | Purpose               |
| ---------------------------------------------------------------- | --------------------- |
| `aihub_lib/aihub_lib/nats/tracing/NATSMessageHeaders.py`         | Header builder        |
| `aihub_lib/aihub_lib/nats/tracing/NATSTraceContextPropagator.py` | W3C trace propagation |

### Lifetime & Integration

| File                                                                    | Purpose                 |
| ----------------------------------------------------------------------- | ----------------------- |
| `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py`              | API startup/shutdown    |
| `aihub_api/aihub_api/sockets/sender/WebSocketSender.py`                 | NATS → WebSocket bridge |
| `aihub_api/aihub_api/sockets/manager/WebSocketManager.py`               | WebSocket connections   |
| `aihub_lib/aihub_lib/nats/distributor/ExternalAgentEventDistributor.py` | API → NATS bridge       |
| `aihub_agent/aihub_agent/runners/AgentRunner.py`                        | Agent NATS bootstrap    |

### Documentation

| File                                                                             | Purpose                     |
| -------------------------------------------------------------------------------- | --------------------------- |
| `aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/index.en.md` | Protocol spec               |
| `deployment/templates/configs/nats-config.conf.j2`                               | NATS server config template |

---

## Conventions Checklist

- [ ] Events inherit from `ControlEvent`, `DisplayEvent`, or `ControlAndDisplayEvent`
- [ ] Event class names are unique (auto-registration enforced)
- [ ] Display events include `_display_name` and `_display_description` as `ClassVar[LocaleString]`
- [ ] Control events published via `JSPublisher` (durable)
- [ ] Display events published via `NCPublisher` (ephemeral)
- [ ] `ControlAndDisplayEvent` types published to both channels
- [ ] Never build NATS subjects manually — use `TopicManager` subclasses
- [ ] Publishers and subscribers have descriptive `name` (appears in OpenTelemetry spans)
- [ ] RPC handlers return response even on error (don't leave requester hanging)
- [ ] All handlers are `async` with signature `(event: TEvent, topic: Topic) -> None`
- [ ] Subscribers started in lifetime manager and stopped on shutdown
- [ ] Streams named `{entity}_{class}_stream` (e.g., `agent_RAGAgent_stream`)
- [ ] Queue groups used for JetStream subscribers that need load balancing
