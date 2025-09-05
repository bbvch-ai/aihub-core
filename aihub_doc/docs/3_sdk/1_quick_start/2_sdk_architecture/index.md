---
title: SDK Architecture
index: 2
---

[@mhoegger](https://github.com/mhoegger) [WIP]

# SDK Architecture: The Technical Foundation

The Swiss AI Hub SDK consists of multiple interconnected packages that provide a complete development framework for
enterprise AI applications. Each package serves a specific architectural purpose while maintaining seamless integration
with the underlying platform.

## The Six-Package Architecture

```


┌───────────────────────────────────────────────────────────────────────────────┐
│                             Your Custom Code                                  │
├─────────────┬───────────────┬─────────────────┬────────────┬──────────────────┤
│ aihub_agent │ aihub_process │ aihub_pipeline  │ aihub_api  │   aihub_bot      │
│ (Workflows) │(Orchestration)│(Data Processing)│ (REST/WS)  │ (Chat Interfaces)│
├─────────────┴───────────────┴─────────────────┴────────────┴──────────────────┤
│                            aihub_lib (Foundation)                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                          Platform Services Layer                              │
│               (Authentication, Tracing, Storage, Messaging...)                │
└───────────────────────────────────────────────────────────────────────────────┘
```

This layered approach ensures clear separation of concerns while maximizing code reuse and maintainability across all
components.

## `aihub_lib`: The Universal Foundation

At the architectural foundation sits `aihub_lib`, providing shared infrastructure that all other SDK packages depend on.
This is the abstraction layer that makes platform integration seamless.

**Core Services Integration:**

- **Event System**: NATS-based messaging with strongly-typed events and automatic serialization
- **Authentication & Authorization**: SSO integration, role-based access control, and user identity management
- **Data Access**: Unified interfaces to MongoDB, vector databases, and object storage
- **LLM Gateway**: Multi-provider LLM access through LiteLLM with automatic cost tracking
- **Observability**: Phoenix tracing, structured logging, and performance metrics
- **Configuration Management**: Pydantic-based configuration with validation and documentation

**Design Philosophy:**

```python
# Instead of managing complex platform integrations:
connection = MongoClient(uri, auth_mechanism="SCRAM-SHA-256")
vector_client = MilvusClient(uri="http://localhost:19530")
llm_client = OpenAI(api_key=api_key, base_url=base_url)

# aihub_lib provides unified, injected resources:
@step()
async def process_document(
    self, 
    doc: Document, 
    doc_store: DocStore,      # Automatically configured
    vector_store: VectorStore, # Platform-managed
    llm: LLM                  # Cost-tracked and monitored
) -> ProcessedDocument:
    # Focus on business logic, not infrastructure
    pass
```

## `aihub_agent`: Event-Driven Workflow Engine

Agents are event-driven workflows where each step transforms strongly-typed events. The architecture emphasizes
predictable, observable behavior over open-ended AI exploration.

**Core Architecture:**

- **Step-Based Workflows**: Each `@step()` decorator creates a processing node
- **Event-Driven Communication**: All interactions happen through typed events
- **State Management**: RunContext (ephemeral) and ThreadContext (persistent)
- **Flow Control**: Conditional routing, parallel processing, and error handling

```python
class DocumentAnalysisAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentUploadEvent) -> AnalysisEvent:
        # Strongly typed input and output
        # Automatic tracing and audit logging
        # Platform resource injection
        return AnalysisEvent(findings=analysis_results)
    
    @step()
    async def generate_report(self, event: AnalysisEvent) -> ReportEvent:
        # Steps chain through event types
        # Each step is independently testable
        return ReportEvent(report=generated_report)
```

**Built-in Agent Types:**

- **RagAgent**: Complete RAG implementation with document retrieval
- **LLMWrappingAgent**: Direct LLM integration with conversation management
- **StreamingAgents**: Real-time response streaming capabilities

## `aihub_pipeline`: Observable Data Processing

Pipelines handle data ingestion and processing using Dagster's asset-based architecture. They keep AI systems fed with
fresh, properly processed data.

**Asset-Based Design:**

- **Materialized Assets**: Concrete data artifacts that can be inspected and versioned
- **Dynamic Partitioning**: Process only changed data, scale with data volume
- **Observable Processing**: Complete lineage tracking and monitoring
- **Automation Policies**: React to data changes rather than scheduled processing

```python
@graph_asset(
    key=AssetKey(["processed_documents"]),
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager()
)
def document_processor(raw_files: DataLakeFile) -> RefDoc:
    return parse_and_structure_document(raw_files)
```

**Key Components:**

- **Asset Factories**: Create reusable processing patterns
- **I/O Managers**: Handle different storage systems (ADLS, MongoDB, Milvus)
- **Observable Assets**: Monitor external systems for changes
- **Resource Management**: Configure parsers, embeddings, and LLM services

## `aihub_process`: Collaborative Orchestration

Processes orchestrate collaboration between AI agents, human experts, and external systems. They delegate work rather
than executing it directly.

**Delegation Architecture:**

- **Entity Types**: Agent, Human, Program, and Process delegation
- **Transformation Focus**: Steps transform data between entity boundaries
- **Workflow Orchestration**: Manage complex multi-actor business processes

```python
class DocumentApprovalProcess(AgenticProcess):
    @process_step()
    def analyze_document(
        self,
        doc: Annotated[Document, Program.In(route="/upload", method="POST")]
    ) -> Annotated[AnalysisRequest, Agent.Out(agent_class="DocumentAnalyzer", agent_id="production")]:
        return AnalysisRequest(document=doc, priority="high")

    @process_step()
    def request_approval(
        self,
        analysis: Annotated[AnalysisResult, Agent.In(agent_class="DocumentAnalyzer", agent_id="production")]
    ) -> Annotated[ApprovalRequest, Human.Out(users=["manager@company.com"])]:
        return ApprovalRequest(analysis=analysis, deadline="24h")
```

## `aihub_api`: REST and WebSocket Gateway

The API package provides HTTP endpoints and real-time communication, following a Controller-Service-DTO pattern for
clean architecture.

**Architectural Pattern:**

- **Controllers**: Handle HTTP concerns and routing
- **Services**: Implement business logic and external integrations
- **DTOs**: Define request/response structures with validation

```python
class AgentController(Controller):
    def chat_completion(self, route: str = "/chat") -> "AgentController":
        @self.router.post(route, tags=self.tags)
        async def chat_completion(
            request: ChatCompletionRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.chat"))],
        ) -> ChatCompletionResponse:
            return await AgentService.process_chat(nc, request, user)
        return self
```

**Key Features:**

- **Dynamic Endpoints**: Automatically generate endpoints for discovered agents/processes
- **WebSocket Streaming**: Real-time event streaming to frontends
- **Authentication Integration**: Platform security enforcement
- **OpenAPI Documentation**: Automatic API documentation generation

## `aihub_bot`: Multi-Channel Conversational Interfaces

The bot package provides conversational interfaces across multiple channels (Teams, Slack, Web) using Microsoft Bot
Framework.

**Multi-Channel Architecture:**

- **Base Bot Classes**: Common functionality across all channels
- **Completion Handlers**: Different strategies for generating responses
- **Channel Adapters**: Handle channel-specific message formatting
- **Conversation Management**: Persistent state with configurable TTL

```python
class AgentChatBot(BaseChatBot):
    def __init__(
        self,
        path: str,
        completion_handler: CompletionHandler,
        handler_kwargs: dict[str, Any],
    ):
        super().__init__(path, completion_handler, handler_kwargs)
    
    @override
    async def on_message_activity(self, turn_context: TurnContext):
        # Handle incoming messages
        # Route to appropriate completion handler
        # Stream responses back to user
        await super().on_message_activity(turn_context)
```

**Bot Types:**

- **AgentChatBot**: Connects to AI-Hub agents via NATS messaging
- **OpenaiChatBot**: Direct LLM integration for simple interactions
- **StreamingBots**: Real-time response streaming across channels

## Cross-Package Integration Patterns

### Dependency Injection Architecture

All SDK packages use a unified dependency injection system:

```python
@step()
async def processing_step(
    self,
    event: InputEvent,
    llm: LLM,                    # From aihub_lib
    vector_store: VectorStore,   # Platform-configured
    run_context: RunContext,     # Agent-specific
    user: UserIdentity          # From API layer
) -> OutputEvent:
    # All dependencies injected with proper configuration
    # No manual resource management required
    pass
```

### Event-First Design

All packages communicate through strongly-typed events:

- **Platform Events**: System lifecycle and control events
- **Domain Events**: Business logic events specific to your application
- **Display Events**: UI-specific events for frontend integration
- **Work Events**: Process delegation and completion events

### Configuration Management

Unified configuration system across all packages:

```python
class MyAgentConfig(AgentConfig):
    llm: Annotated[ChatLLMConfig, Field(description="LLM configuration")]
    confidence_threshold: Annotated[float, Field(ge=0.0, le=1.0)]
    custom_parameter: Annotated[str, Field(description="Domain-specific setting")]
```

### Testing Infrastructure

Each package provides specialized testing utilities:

- **AgentTestRunner**: Isolated agent testing with event observation
- **ProcessTestRunner**: Multi-entity process testing with BDD support
- **ApiTestRunner**: HTTP endpoint testing with authentication
- **BotTestRunner**: Conversational interface testing

