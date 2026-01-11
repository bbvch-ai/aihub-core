# Complete Guide: Building and Deploying AI Agents in Swiss AI-Hub

**Version**: 1.0
**Last Updated**: 2026-01-11
**For**: Developers building custom AI agents in the Swiss AI-Hub platform

---

## Table of Contents

1. [Overview and Architecture](#1-overview-and-architecture)
2. [Prerequisites and Setup](#2-prerequisites-and-setup)
3. [Core Concepts](#3-core-concepts)
4. [Step-by-Step Agent Creation](#4-step-by-step-agent-creation)
5. [Configuration and Customization](#5-configuration-and-customization)
6. [Testing Your Agent](#6-testing-your-agent)
7. [Deployment](#7-deployment)
8. [Debugging and Observability](#8-debugging-and-observability)
9. [Advanced Patterns](#9-advanced-patterns)
10. [Complete Example: Custom RAG Agent](#10-complete-example-custom-rag-agent)
11. [Reference and Resources](#11-reference-and-resources)

---

## 1. Overview and Architecture

### What is the Swiss AI-Hub?

Swiss AI-Hub is an **enterprise-grade, sovereign AI platform** designed for integrating AI into business processes with a focus on **privacy, transparency, and Swiss data sovereignty**.

### Three-Tier Architecture

- **Tier 1**: Secure LLM access (OpenWebUI chat interface)
- **Tier 2**: AI agents with organizational knowledge (RAG, vector search) ← **YOU ARE HERE**
- **Tier 3**: Process orchestration (agents + humans + external systems)

### What Are AI Agents in This Platform?

AI Agents in Swiss AI-Hub are **NOT black boxes**. They are:

- **Transparent workflows** composed of discrete, traceable steps
- **Event-driven** components that consume and produce typed events
- **Stateless** classes (state managed externally in Redis/Valkey)
- **Observable** through OpenTelemetry and Arize Phoenix tracing
- **Composable** (agents can delegate to other agents)

### Key Differentiators

| Traditional AI Agents | Swiss AI-Hub Agents |
|----------------------|---------------------|
| Black box execution | Every step is transparent and traceable |
| Opaque reasoning | Explicit workflow with named steps |
| Hard to debug | Full OpenTelemetry integration |
| Stateful objects | Stateless with external state management |
| Direct LLM calls | Event-driven with protocol compliance |

---

## 2. Prerequisites and Setup

### Required Knowledge

- **Python 3.13+** (async/await, type hints, Pydantic)
- **FastAPI** basics (dependency injection)
- **Event-driven architecture** concepts
- **Docker** and **Docker Compose**
- **Git** workflow

### System Requirements

```bash
# Clone repository
git clone https://github.com/bbvch-ai/aihub-core
cd aihub-core

# Set up Python environment
cd aihub_agent
poetry shell
poetry install

# Start infrastructure (dev environment)
cd /home/user/aihub-core
docker compose -f docker-compose.dev.yml up -d
```

### Verify Setup

```bash
# Check services are running
docker compose -f docker-compose.dev.yml ps

# Access points (verify in browser):
# - OpenWebUI: http://localhost:8080
# - Admin UI: http://localhost:3000
# - API: http://localhost:8000
# - Phoenix (Observability): http://localhost:6006
```

### Development Environment

```bash
# Always work within Poetry shell
cd /home/user/aihub-core/aihub_agent
poetry shell

# Verify environment
python --version  # Should be 3.13+
which python      # Should point to Poetry virtualenv
```

---

## 3. Core Concepts

### 3.1 The Swiss AI Agent Protocol

The **Swiss AI Agent Protocol** is an internal event-driven communication protocol that governs all agent interactions.

#### Event Hierarchy

```
BaseEvent (root)
├── ControlEvent ─────────► Drives workflow execution
│   ├── StartEvent ───────► Initiates a run
│   ├── StopEvent ────────► Terminates a run
│   └── ExceptionEvent ───► Signals errors
│
├── DisplayEvent ─────────► UI/observability only
│   ├── ChunkEvent ───────► LLM streaming tokens
│   └── ThoughtEvent ─────► Agent reasoning
│
└── ControlAndDisplayEvent ─► Most practical events inherit from this
    ├── UserMessageEvent
    ├── LLMEvent
    └── RetrieverEvent
```

**Critical Rule**: Only `ControlEvent` types can drive workflow steps. `DisplayEvent` types inform UIs but don't trigger steps.

#### Event Publishing and Subscription

Agents **don't explicitly publish/subscribe**. Instead:

1. **Subscribe** by defining a `@step()` method with an event parameter type
2. **Publish** by returning an event from a step

```python
class MyAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> CustomEvent:
        # This step SUBSCRIBES to UserMessageEvent
        # This step PUBLISHES CustomEvent (by returning it)
        return CustomEvent(data="processed")
```

#### NATS Message Bus

- **Transport**: NATS JetStream (persistent, at-least-once delivery)
- **Subject Pattern**: `agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}`
- **Hierarchical Scoping**: Thread → Display → Run for security and tracing

### 3.2 Workflow Architecture

#### DispatchableWorkflow

All agents inherit from `DispatchableWorkflow`, which provides:

- **Step Discovery**: Automatically finds all `@step()` methods
- **Event Routing**: Routes incoming events to appropriate steps
- **Execution Control**: Manages step execution order, preconditions, and limits

#### The @step Decorator

The `@step()` decorator is the **heart of agent definition**:

```python
@step(
    name=LocaleString(en="My Step"),           # UI display name (i18n)
    description=LocaleString(en="Does X"),     # UI description
    icon="mdi:robot",                          # UI icon (Iconify)
    max_executions_per_run=5,                  # Limit executions
    stop_on_error=True,                        # Stop workflow on error
    precondition=my_precondition_fn            # Conditional execution
)
async def my_step(self, event: InputEvent, config: MyConfig) -> OutputEvent:
    # Step logic
    return OutputEvent()
```

**What the decorator does**:

1. Extracts input event types from function signature
2. Extracts output event types from return type annotation
3. Attaches metadata for workflow visualization
4. Registers step with the dispatcher

#### Step Execution Flow

```
1. Event arrives via NATS
2. Dispatcher checks if any step is ready (preconditions, input events available)
3. Dispatcher builds kwargs from available events and contexts
4. Step executes asynchronously
5. Result events published to NATS
6. Repeat until StopEvent
```

### 3.3 Context Management

Agents are **stateless**. State is managed externally in **Valkey (Redis v5)** via two context types:

#### RunContext (Ephemeral)

- **Scope**: Single run execution
- **Lifetime**: Duration of run (30-day TTL)
- **Use Cases**: Loop counters, temporary calculations, intermediate data
- **Storage**: `run_context_{thread_id}_{run_id}`

```python
@step()
async def my_step(self, event: MyEvent, run_context: RunContext):
    count = await run_context.get("iteration_count", 0)
    await run_context.set("iteration_count", count + 1)
```

#### ThreadContext (Persistent)

- **Scope**: All runs within a conversation thread
- **Lifetime**: Thread duration (30-day TTL)
- **Use Cases**: Chat history, user preferences, session state
- **Storage**: `thread_context_{thread_id}`

```python
@step()
async def my_step(self, event: MyEvent, thread_context: ThreadContext):
    history = await thread_context.get("chat_history", [])
    history.append({"role": "user", "content": event.message})
    await thread_context.set("chat_history", history)
```

**Key Difference**: RunContext resets per run; ThreadContext persists across runs.

### 3.4 Agent Types and Roles

#### As an Assistant (Conversational)

- Accepts `UserMessageEvent` as start event
- Responds to user queries
- Example: ChatGPT-like interface

#### As an Agent in a Process

- Executes discrete work within a larger orchestration
- Emits `WorkEvent` on completion
- Coordinated by process orchestrator

#### As a Sub-Agent (Agent-in-the-Loop)

- Called by another agent to perform specialized tasks
- Parent agent delegates work, waits for result
- Example: RAG agent called by namespace selection agent

---

## 4. Step-by-Step Agent Creation

### Step 1: Define Your Agent's Purpose

**Exercise**: Answer these questions before coding:

1. **Input**: What event type triggers my agent? (`UserMessageEvent`, custom event?)
2. **Output**: What does my agent produce? (`StopEvent` with result data?)
3. **Steps**: What operations must happen to transform input → output?
4. **State**: What data needs to persist across runs? (Thread vs Run context)
5. **Role**: Is this an assistant, process agent, or sub-agent?

**Example**: "My agent retrieves product information based on user queries, checks inventory, and returns availability."

### Step 2: Create Directory Structure

```bash
cd /home/user/aihub-core/aihub_agent/aihub_agent/agents

# Create agent package
mkdir -p MyAgent/configs MyAgent/events
touch MyAgent/__init__.py
touch MyAgent/MyAgent.py
touch MyAgent/configs/MyAgentConfig.py
touch MyAgent/events/__init__.py
```

**File Structure**:
```
MyAgent/
├── __init__.py
├── MyAgent.py              # Main agent class
├── configs/
│   └── MyAgentConfig.py    # Pydantic configuration
└── events/
    └── CustomEvent.py      # Custom events (if needed)
```

### Step 3: Define Configuration

**File**: `MyAgent/configs/MyAgentConfig.py`

```python
from pydantic import BaseModel, Field
from aihub_agent.configs.AgentConfig import AgentConfig
from aihub_lib.generative_ai.configs.LLMConfig import LLMConfig


class MyAgentConfig(AgentConfig):
    """
    Configuration for MyAgent.

    Inherits from AgentConfig which provides:
    - agent_class: str
    - agent_id: str
    - llm_config: LLMConfig
    """

    # Custom configuration fields
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    custom_prompt: str = Field(default="You are a helpful assistant")

    # Nested configurations
    retrieval_config: dict | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent_class": "MyAgent",
                "agent_id": "my-agent-001",
                "max_retries": 3,
                "temperature": 0.7,
            }
        }
```

**Key Points**:

- Inherit from `AgentConfig`
- Use Pydantic `Field` for validation and documentation
- Provide defaults for all fields
- Use type hints (`int | None`, not `Optional[int]`)

### Step 4: Define Custom Events (If Needed)

**File**: `MyAgent/events/ProductInfoEvent.py`

```python
from pydantic import Field
from aihub_lib.nats.events import ControlAndDisplayEvent
from aihub_lib.i18n.LocaleString import LocaleString


class ProductInfoEvent(ControlAndDisplayEvent):
    """
    Event containing product information retrieved by the agent.
    """

    product_name: str = Field(..., description="Name of the product")
    in_stock: bool = Field(..., description="Whether product is in stock")
    price: float = Field(..., description="Product price")

    # Display metadata for UI
    display_name: LocaleString = LocaleString(
        en="Product Information",
        de="Produktinformationen"
    )
    display_description: LocaleString = LocaleString(
        en="Retrieved product details",
        de="Abgerufene Produktdetails"
    )
```

**When to create custom events**:

- When built-in events (UserMessageEvent, StopEvent, etc.) don't carry your data
- When you need to pass structured data between steps
- When you want UI-specific metadata

### Step 5: Implement the Agent Class

**File**: `MyAgent/MyAgent.py`

```python
from aihub_lib.nats.events import UserMessageEvent, StopEvent, ChunkEvent
from aihub_lib.i18n.LocaleString import LocaleString
from llama_index.core.llms import ChatMessage

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.step import step
from aihub_agent.agents.MyAgent.configs.MyAgentConfig import MyAgentConfig
from aihub_agent.agents.MyAgent.events.ProductInfoEvent import ProductInfoEvent


class MyAgent(Agent):
    """
    Custom agent that retrieves product information and checks availability.

    Workflow:
    1. Receive user query (UserMessageEvent)
    2. Parse query and retrieve product info
    3. Check inventory status
    4. Return structured result (StopEvent with product data)
    """

    @step(
        name=LocaleString(en="Parse User Query", de="Benutzeranfrage analysieren"),
        description=LocaleString(en="Extract product name from user message"),
        icon="mdi:text-search"
    )
    async def parse_query_step(
        self,
        event: UserMessageEvent,
        agent_config: MyAgentConfig,
        thread_context: ThreadContext
    ) -> ProductInfoEvent:
        """
        Step 1: Parse user query to extract product information.
        """
        # Get last user message
        user_message = event.messages[-1].content

        # Call LLM to extract product name (using agent_config.llm_config)
        llm = agent_config.llm_config.as_llm()

        extraction_prompt = f"{agent_config.custom_prompt}\n\nExtract the product name from: {user_message}"
        response = await llm.acomplete(extraction_prompt)
        product_name = response.text.strip()

        # Simulated database lookup (replace with real logic)
        product_info = await self._fetch_product_info(product_name)

        # Store in thread context for history
        history = await thread_context.get("product_queries", [])
        history.append(product_name)
        await thread_context.set("product_queries", history)

        return ProductInfoEvent(
            product_name=product_info["name"],
            in_stock=product_info["in_stock"],
            price=product_info["price"]
        )

    @step(
        name=LocaleString(en="Format Response", de="Antwort formatieren"),
        description=LocaleString(en="Create user-friendly response"),
        icon="mdi:format-text"
    )
    async def format_response_step(
        self,
        event: ProductInfoEvent,
        agent_config: MyAgentConfig
    ) -> ChunkEvent:
        """
        Step 2: Format product info for user display.
        """
        if event.in_stock:
            message = f"✅ {event.product_name} is in stock at ${event.price:.2f}"
        else:
            message = f"❌ {event.product_name} is out of stock (price: ${event.price:.2f})"

        return ChunkEvent(content=message)

    @step(
        name=LocaleString(en="Complete", de="Abschließen"),
        description=LocaleString(en="Finalize agent execution"),
        icon="mdi:check-circle"
    )
    async def complete_step(
        self,
        event: ChunkEvent
    ) -> StopEvent:
        """
        Step 3: Terminate workflow.
        """
        return StopEvent(result={"message": event.content})

    # Helper methods (not steps)
    async def _fetch_product_info(self, product_name: str) -> dict:
        """Simulated product database lookup."""
        # Replace with actual database/API call
        return {
            "name": product_name,
            "in_stock": True,
            "price": 99.99
        }
```

**Key Implementation Notes**:

1. **Always inherit from `Agent`**
2. **Every step is async** (even if it doesn't use await)
3. **Type hint everything**: Parameters AND return types
4. **Dependency injection**: `agent_config`, `thread_context`, `run_context` are auto-injected
5. **Return events**: Don't publish manually—just return

### Step 6: Register Your Agent

**File**: `MyAgent/__init__.py`

```python
from aihub_agent.agents.MyAgent.MyAgent import MyAgent
from aihub_agent.agents.MyAgent.configs.MyAgentConfig import MyAgentConfig

__all__ = ["MyAgent", "MyAgentConfig"]
```

**File**: `aihub_agent/aihub_agent/agents/__init__.py` (add your agent)

```python
# Existing imports...
from aihub_agent.agents.MyAgent import MyAgent, MyAgentConfig

# Add to __all__
__all__ = [
    # ...existing...
    "MyAgent",
    "MyAgentConfig",
]
```

---

## 5. Configuration and Customization

### LLM Configuration

All agents inherit `llm_config` from `AgentConfig`:

```python
from aihub_lib.generative_ai.configs.LLMConfig import LLMConfig

# In your agent step
@step()
async def my_step(self, event: MyEvent, agent_config: MyAgentConfig):
    llm = agent_config.llm_config.as_llm()

    # Use LlamaIndex LLM interface
    response = await llm.acomplete("Your prompt here")

    # Chat interface
    messages = [
        ChatMessage(role="system", content="You are helpful"),
        ChatMessage(role="user", content="Hello")
    ]
    chat_response = await llm.achat(messages)
```

**Supported LLM Providers** (via LiteLLM):

- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Google GenAI (Gemini)
- Anthropic (Claude)
- Local models (vLLM, llama.cpp)

### Retrieval (RAG) Configuration

For agents that need retrieval:

```python
from aihub_lib.generative_ai.configs.RetrieverConfig import RetrieverConfig

class MyRAGAgentConfig(AgentConfig):
    retriever_config: RetrieverConfig = Field(...)

# In your step
@step()
async def retrieve_step(self, event: MyEvent, agent_config: MyRAGAgentConfig):
    retriever = agent_config.retriever_config.as_retriever()

    nodes = await retriever.aretrieve("user query")
    # nodes is list[NodeWithScore] from LlamaIndex
```

### Internationalization (i18n)

Swiss AI-Hub supports **4 languages**: German (de), English (en), French (fr), Italian (it).

**Default locale**: German (`de`)

```python
from aihub_lib.i18n.LocaleString import LocaleString

# Define multi-language strings
step_name = LocaleString(
    de="Daten abrufen",
    en="Retrieve Data",
    fr="Récupérer les données",
    it="Recupera dati"
)

@step(name=step_name)
async def my_step(self, event: MyEvent):
    # Step logic
    pass
```

**Runtime locale resolution**:

```python
from aihub_lib.i18n.LocaleHandler import LocaleHandler

@step()
async def my_step(self, event: MyEvent, locale_handler: LocaleHandler):
    # LocaleHandler auto-injected based on user's language
    localized_text = locale_handler.translate("greeting.hello")
```

---

## 6. Testing Your Agent

### 6.1 Unit Testing with AgentTestRunner

**File**: `aihub_agent/tests/test_my_agent.py`

```python
import pytest
from aihub_lib.nats.events import UserMessageEvent
from aihub_agent.agents.MyAgent import MyAgent, MyAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


@pytest.mark.asyncio
async def test_my_agent_basic_flow():
    """Test basic agent workflow."""

    # Create test runner
    runner = AgentTestRunner(agent_class=MyAgent)

    # Configure agent
    config = MyAgentConfig(
        agent_class="MyAgent",
        agent_id="test-agent",
        max_retries=3,
        temperature=0.7
    )

    # Create start event
    start_event = UserMessageEvent.create_for_user_message(
        user_id="test-user",
        content="What is the price of Widget X?"
    )

    # Run agent
    result = await runner.run(
        agent_config=config,
        start_event=start_event
    )

    # Assertions
    assert result.stop_event is not None
    assert "Widget X" in result.stop_event.result["message"]
    assert result.exception_event is None


@pytest.mark.asyncio
async def test_my_agent_context_persistence():
    """Test ThreadContext persistence across runs."""

    runner = AgentTestRunner(agent_class=MyAgent)
    config = MyAgentConfig(agent_class="MyAgent", agent_id="test-agent")

    # First run
    event1 = UserMessageEvent.create_for_user_message(
        user_id="test-user",
        content="Price of Widget A?"
    )
    result1 = await runner.run(agent_config=config, start_event=event1)

    # Second run (same thread)
    event2 = UserMessageEvent.create_for_user_message(
        user_id="test-user",
        content="Price of Widget B?"
    )
    result2 = await runner.run(agent_config=config, start_event=event2)

    # Verify history accumulated
    history = await runner.thread_context.get("product_queries", [])
    assert len(history) == 2
    assert "Widget A" in history[0]
    assert "Widget B" in history[1]
```

### 6.2 BDD Testing with pytest-bdd

**File**: `aihub_agent/tests/features/my_agent.feature`

```gherkin
Feature: Product Information Agent
  As a user
  I want to query product availability
  So that I can make purchasing decisions

  Scenario: Query in-stock product
    Given the MyAgent is configured
    And the product "Widget X" is in stock
    When I ask "Is Widget X available?"
    Then I should receive a confirmation message
    And the message should include the price

  Scenario: Query out-of-stock product
    Given the MyAgent is configured
    And the product "Widget Y" is out of stock
    When I ask "Is Widget Y available?"
    Then I should receive an out-of-stock message
```

**File**: `aihub_agent/tests/test_my_agent_bdd.py`

```python
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from aihub_lib.nats.events import UserMessageEvent
from aihub_agent.agents.MyAgent import MyAgent, MyAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios('features/my_agent.feature')


@pytest.fixture
def context():
    """Test context to share state between steps."""
    return {}


@given("the MyAgent is configured")
async def configure_agent(context):
    context["runner"] = AgentTestRunner(agent_class=MyAgent)
    context["config"] = MyAgentConfig(agent_class="MyAgent", agent_id="test-agent")


@given(parsers.parse('the product "{product_name}" is in stock'))
async def product_in_stock(context, product_name):
    context["product_name"] = product_name
    context["in_stock"] = True


@when(parsers.parse('I ask "{question}"'))
async def ask_question(context, question):
    event = UserMessageEvent.create_for_user_message(
        user_id="test-user",
        content=question
    )
    context["result"] = await context["runner"].run(
        agent_config=context["config"],
        start_event=event
    )


@then("I should receive a confirmation message")
def verify_confirmation(context):
    assert context["result"].stop_event is not None
    assert "✅" in context["result"].stop_event.result["message"]
```

### 6.3 Interactive Testing with trigger.py

**File**: `MyAgent/trigger.py`

```python
import asyncio
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_agent.agents.MyAgent import MyAgent, MyAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    enable_logging()

    runner = AgentTestRunner(agent_class=MyAgent)

    config = MyAgentConfig(
        agent_class="MyAgent",
        agent_id="trigger-test",
        max_retries=3,
        temperature=0.7
    )

    # Test different scenarios
    test_queries = [
        "What is the price of Widget X?",
        "Is Widget Y available?",
        "Tell me about Product Z"
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)

        event = UserMessageEvent.create_for_user_message(
            user_id="test-user",
            content=query
        )

        result = await runner.run(agent_config=config, start_event=event)

        if result.stop_event:
            print(f"✅ Success: {result.stop_event.result}")
        if result.exception_event:
            print(f"❌ Error: {result.exception_event.exception}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Run it**:

```bash
cd /home/user/aihub-core/aihub_agent
poetry shell
python -m aihub_agent.agents.MyAgent.trigger
```

### 6.4 Pre-Commit Testing

**CRITICAL**: Run these before every commit:

```bash
cd /home/user/aihub-core/aihub_agent
poetry shell

# Format, lint, type check (MUST pass)
make pr-ready

# Run all tests (MUST pass)
make test

# Run specific tests
pytest tests/test_my_agent.py -v

# Run excluding Azure integration tests
pytest -k "not azure"
```

---

## 7. Deployment

### 7.1 Local Development Deployment

**Step 1: Configure Environment**

```bash
cd /home/user/aihub-core

# Copy dev environment
cp .env.dev .env

# Edit .env if needed (LLM API keys, etc.)
nano .env
```

**Step 2: Start Infrastructure**

```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# Verify services
docker compose -f docker-compose.dev.yml ps

# Check logs
docker compose -f docker-compose.dev.yml logs -f aihub-agent
```

**Step 3: Register Agent in OpenWebUI**

1. Open http://localhost:8080
2. Login (create account if first time)
3. Navigate to **Admin Settings → Agents**
4. Click **Add Agent**
5. Configure:
   - **Name**: "My Product Agent"
   - **Agent Class**: `MyAgent`
   - **Configuration**: Paste JSON config:

```json
{
  "agent_class": "MyAgent",
  "agent_id": "my-agent-prod-001",
  "max_retries": 3,
  "temperature": 0.7,
  "llm_config": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

6. **Save**

**Step 4: Test via OpenWebUI**

1. Create new chat
2. Select "My Product Agent" from agent dropdown
3. Send message: "What is the price of Widget X?"
4. Verify response

### 7.2 Production Deployment

**Docker Compose Production**:

```bash
# Generate production compose file
make generate-compose

# Start production stack
docker compose -f docker-compose.yml up -d

# Configure secrets (Azure, OpenAI keys)
# Edit .env.prod with production values
```

**Azure Deployment (Pulumi)**:

The platform includes Pulumi IaC for Azure deployment:

```bash
cd /home/user/aihub-core/infrastructure/pulumi

# Configure Azure credentials
pulumi config set azure-native:location switzerlandnorth
pulumi config set --secret openai-api-key YOUR_KEY

# Deploy
pulumi up
```

**Agent Registration in Production**:

1. Deploy via Admin UI (same as local)
2. OR register via API:

```bash
curl -X POST http://your-domain.com/api/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "agent_class": "MyAgent",
    "config": {
      "agent_class": "MyAgent",
      "agent_id": "my-agent-prod-001",
      "max_retries": 3,
      "temperature": 0.7
    }
  }'
```

### 7.3 CI/CD Integration

Agents are automatically tested and deployed via GitHub Actions:

**File**: `.github/workflows/test-agents.yml` (already configured)

```yaml
name: Test Agents
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd aihub_agent
          pip install poetry
          poetry install
      - name: Run tests
        run: |
          cd aihub_agent
          poetry run make pr-ready
          poetry run make test
```

**Deployment triggered by**:

- **Push to `main`**: Auto-deploy to nightly environment
- **Tagged release**: Deploy to production
- **Manual trigger**: Via GitHub Actions UI

---

## 8. Debugging and Observability

### 8.1 Arize Phoenix (OpenTelemetry Tracing)

**Access**: http://localhost:6006

Phoenix visualizes **every step** of your agent execution with full tracing.

**What you can see**:

- Workflow execution flow (step-by-step)
- Event routing (which events triggered which steps)
- LLM calls (prompts, responses, token usage, latency)
- Retrieval operations (queries, documents, scores)
- Errors and exceptions (full stack traces)
- Context reads/writes (RunContext, ThreadContext)

**How to use**:

1. Run your agent (via OpenWebUI, trigger.py, or tests)
2. Open Phoenix: http://localhost:6006
3. Navigate to **Traces** tab
4. Find your agent's trace (search by `agent_class` or `thread_id`)
5. Click to expand full trace tree
6. Inspect each span for details

**Phoenix MCP Integration**:

Query traces programmatically via Model Context Protocol:

```python
# Example: Get recent traces for your agent
# (This would be called via MCP client)
from phoenix.client import PhoenixClient

client = PhoenixClient("http://localhost:6006")
traces = client.get_traces(filter={"agent_class": "MyAgent"}, limit=10)
```

### 8.2 Logging

**Enable detailed logging**:

```python
from aihub_lib.infrastructure.logging.logger import enable_logging

# In your trigger.py or test
enable_logging()
```

**Log levels**:

- `DEBUG`: Step execution, event routing
- `INFO`: Agent lifecycle, configuration
- `WARNING`: Non-critical issues
- `ERROR`: Exceptions, failures

**View logs**:

```bash
# Docker logs
docker compose -f docker-compose.dev.yml logs -f aihub-agent

# Application logs (if running locally)
tail -f /var/log/aihub/agent.log
```

### 8.3 Event Store Inspection

All events are stored in **NATS JetStream** for replay and auditing.

**View events via NATS CLI**:

```bash
# Install NATS CLI
brew install nats-io/nats-tools/nats

# List streams
nats stream ls

# View events in agent stream
nats stream view agent_MyAgent_instance-123

# Get specific event
nats stream get agent_MyAgent_instance-123 --id <event-id>
```

### 8.4 Context Inspection (Redis)

**View RunContext/ThreadContext**:

```bash
# Connect to Redis
docker exec -it aihub-redis redis-cli

# List all keys
KEYS *

# View thread context
GET thread_context_thread-123

# View run context
GET run_context_thread-123_run-456
```

### 8.5 Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Step not executing** | Event arrives but step doesn't run | Check preconditions, input event types, max_executions_per_run |
| **Missing type hints** | `AttributeError` in dispatcher | Ensure all parameters and return types are type-hinted |
| **Event not routing** | Step never receives event | Verify event inheritance (ControlEvent vs DisplayEvent) |
| **Context not persisting** | State lost between runs | Check Redis connection, TTL, key names |
| **LLM call failing** | `OpenAI API Error` | Verify API keys in .env, check LLMConfig |
| **Import errors** | `ModuleNotFoundError` | Run `poetry install` in aihub_agent, check __init__.py registrations |

---

## 9. Advanced Patterns

### 9.1 Human-in-the-Loop (HITL)

**Use Case**: Agent needs user confirmation or additional input mid-workflow.

```python
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput

class ApprovalAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> HumanInTheLoopInput.request:
        # Ask user for approval
        return HumanInTheLoopInput.invoke(
            question="Do you want to proceed with this action?",
            options=["Yes", "No"]
        )

    @step()
    async def handle_approval(self, event: HumanInTheLoopInput.response) -> StopEvent:
        if event.response == "Yes":
            # Proceed with action
            result = await self._perform_action()
            return StopEvent(result=result)
        else:
            return StopEvent(result={"status": "cancelled"})
```

**How it works**:

1. Agent publishes `HumanInTheLoopRequestEvent`
2. UI (OpenWebUI) displays question to user
3. User responds via UI
4. Response published as `HumanInTheLoopResponseEvent`
5. Agent's next step receives response

### 9.2 Agent-in-the-Loop (AITL)

**Use Case**: Orchestrator agent delegates work to specialist agent.

```python
from aihub_lib.nats.events.agent_in_the_loop import AgentInTheLoop

class OrchestratorAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # Delegate to specialist RAG agent
        return AgentInTheLoop.invoke(
            agent_id="rag-specialist",
            agent_class="RAGAgent",
            start_event=event,  # Forward user message
            config={
                "agent_class": "RAGAgent",
                "agent_id": "rag-specialist",
                "llm_config": {...}
            }
        )

    @step()
    async def handle_rag_response(
        self,
        event: AgentInTheLoop.response
    ) -> StopEvent:
        # Process RAG agent's result
        rag_result = event.stop_event.result

        # Further processing
        final_result = await self._enrich_result(rag_result)

        return StopEvent(result=final_result)
```

**Real Example**: `NamespaceSelectionAgent` delegates to `RAGAgent` after namespace selection.

### 9.3 Preconditions (Parallel Synchronization)

**Use Case**: Wait for multiple parallel steps to complete before proceeding.

```python
from aihub_agent.workflow.decorators.precondition import precondition

@precondition()
async def all_parallel_events_ready(
    events: list[ParallelEvent],
    config: MyAgentConfig
) -> bool:
    """Wait until all parallel branches emit their events."""
    return len(events) == config.number_of_parallel_branches

class SyncAgent(Agent):
    @step()
    async def fan_out_step(self, event: StartEvent) -> list[ParallelEvent]:
        # Create 3 parallel events
        return [
            ParallelEvent(branch_id=1),
            ParallelEvent(branch_id=2),
            ParallelEvent(branch_id=3)
        ]

    @step()
    async def process_parallel(self, event: ParallelEvent) -> ResultEvent:
        # Each branch processes independently
        result = await self._process_branch(event.branch_id)
        return ResultEvent(data=result)

    @step(precondition=all_parallel_events_ready)
    async def sync_step(self, events: list[ResultEvent]) -> StopEvent:
        # Only runs when ALL 3 ResultEvents are available
        combined_result = [e.data for e in events]
        return StopEvent(result=combined_result)
```

**Reference**: `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/precondition_workflow`

### 9.4 Bounded Loops

**Use Case**: Retry logic, iterative refinement.

```python
class RetryAgent(Agent):
    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        run_context: RunContext
    ) -> ProcessEvent:
        return ProcessEvent()

    @step(max_executions_per_run=5)
    async def retry_step(
        self,
        event: ProcessEvent,
        run_context: RunContext
    ) -> ProcessEvent | StopEvent:
        attempt = await run_context.get("attempt", 0)
        await run_context.set("attempt", attempt + 1)

        success = await self._try_operation()

        if success:
            return StopEvent(result={"success": True, "attempts": attempt + 1})
        else:
            # Return same event type to trigger retry
            return ProcessEvent()
```

**Key**: `max_executions_per_run` prevents infinite loops.

### 9.5 Streaming Responses

**Use Case**: Real-time LLM output to UI.

```python
from aihub_lib.nats.events import ChunkEvent

class StreamingAgent(Agent):
    @step()
    async def stream_step(
        self,
        event: UserMessageEvent,
        agent_config: MyAgentConfig
    ) -> list[ChunkEvent | StopEvent]:
        llm = agent_config.llm_config.as_llm()

        events = []

        # Stream LLM response
        async for chunk in llm.astream_complete(event.messages[-1].content):
            events.append(ChunkEvent(content=chunk.delta))

        # Final stop event
        events.append(StopEvent())

        return events
```

**UI receives**: Real-time `ChunkEvent` updates, then `StopEvent` on completion.

### 9.6 Multi-Hop Retrieval

**Use Case**: Iterative retrieval for complex queries.

```python
class MultiHopRAGAgent(Agent):
    @step()
    async def initial_retrieval(
        self,
        event: UserMessageEvent,
        agent_config: RAGAgentConfig
    ) -> RetrieverEvent:
        retriever = agent_config.retriever_config.as_retriever()
        nodes = await retriever.aretrieve(event.messages[-1].content)
        return RetrieverEvent(nodes=nodes, query=event.messages[-1].content)

    @step()
    async def check_sufficiency(
        self,
        event: RetrieverEvent,
        agent_config: RAGAgentConfig
    ) -> ContextSufficientEvent | ContextInsufficientEvent:
        # Use LLM to judge if context is sufficient
        llm = agent_config.llm_config.as_llm()

        context = "\n".join([node.text for node in event.nodes])
        judgment = await llm.acomplete(
            f"Is this context sufficient to answer '{event.query}'?\n\n{context}"
        )

        if "yes" in judgment.text.lower():
            return ContextSufficientEvent(nodes=event.nodes)
        else:
            return ContextInsufficientEvent(query=event.query)

    @step(max_executions_per_run=3)
    async def additional_retrieval(
        self,
        event: ContextInsufficientEvent,
        agent_config: RAGAgentConfig,
        run_context: RunContext
    ) -> RetrieverEvent:
        # Refine query and retrieve again
        hop_count = await run_context.get("hop_count", 0)
        await run_context.set("hop_count", hop_count + 1)

        refined_query = await self._refine_query(event.query, hop_count)

        retriever = agent_config.retriever_config.as_retriever()
        nodes = await retriever.aretrieve(refined_query)

        return RetrieverEvent(nodes=nodes, query=refined_query)

    @step()
    async def generate_response(
        self,
        event: ContextSufficientEvent,
        agent_config: RAGAgentConfig
    ) -> StopEvent:
        # Generate final answer
        context = "\n".join([node.text for node in event.nodes])
        llm = agent_config.llm_config.as_llm()

        response = await llm.acomplete(f"Context:\n{context}\n\nAnswer the query.")

        return StopEvent(result={"answer": response.text})
```

**Reference**: `RAGAgent` in `/home/user/aihub-core/aihub_agent/aihub_agent/agents/RagAgent/RAGAgent.py`

---

## 10. Complete Example: Custom RAG Agent

Let's build a **Legal Document Q&A Agent** that retrieves from legal knowledge base with citation tracking.

### File Structure

```
LegalRAGAgent/
├── __init__.py
├── LegalRAGAgent.py
├── configs/
│   └── LegalRAGAgentConfig.py
└── events/
    ├── __init__.py
    ├── CitedAnswerEvent.py
    └── LegalRetrievalEvent.py
```

### Configuration

**File**: `configs/LegalRAGAgentConfig.py`

```python
from pydantic import Field
from aihub_agent.configs.AgentConfig import AgentConfig
from aihub_lib.generative_ai.configs.RetrieverConfig import RetrieverConfig


class LegalRAGAgentConfig(AgentConfig):
    """Configuration for Legal RAG Agent."""

    retriever_config: RetrieverConfig = Field(..., description="Retrieval configuration")
    max_citations: int = Field(default=5, description="Maximum citations to include")
    require_citations: bool = Field(default=True, description="Require citations in response")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum relevance score")
```

### Custom Events

**File**: `events/LegalRetrievalEvent.py`

```python
from pydantic import Field
from aihub_lib.nats.events import ControlAndDisplayEvent
from llama_index.core.schema import NodeWithScore


class LegalRetrievalEvent(ControlAndDisplayEvent):
    """Retrieved legal documents with metadata."""

    nodes: list[NodeWithScore] = Field(..., description="Retrieved documents")
    query: str = Field(..., description="User query")
    total_documents: int = Field(..., description="Total documents found")
```

**File**: `events/CitedAnswerEvent.py`

```python
from pydantic import Field
from aihub_lib.nats.events import ControlAndDisplayEvent


class CitedAnswerEvent(ControlAndDisplayEvent):
    """Legal answer with citations."""

    answer: str = Field(..., description="Generated answer")
    citations: list[dict] = Field(..., description="List of citation metadata")
    confidence: float = Field(..., description="Answer confidence score")
```

### Agent Implementation

**File**: `LegalRAGAgent.py`

```python
from llama_index.core.llms import ChatMessage
from aihub_lib.nats.events import UserMessageEvent, StopEvent, ChunkEvent
from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.step import step
from aihub_agent.agents.LegalRAGAgent.configs.LegalRAGAgentConfig import LegalRAGAgentConfig
from aihub_agent.agents.LegalRAGAgent.events.LegalRetrievalEvent import LegalRetrievalEvent
from aihub_agent.agents.LegalRAGAgent.events.CitedAnswerEvent import CitedAnswerEvent


class LegalRAGAgent(Agent):
    """
    Legal document Q&A agent with citation tracking.

    Workflow:
    1. Receive user legal query
    2. Retrieve relevant legal documents
    3. Filter by confidence threshold
    4. Generate answer with citations
    5. Track query history in thread context
    """

    @step(
        name=LocaleString(en="Retrieve Legal Documents", de="Rechtsdokumente abrufen"),
        description=LocaleString(en="Search legal knowledge base"),
        icon="mdi:file-document-search"
    )
    async def retrieve_documents_step(
        self,
        event: UserMessageEvent,
        agent_config: LegalRAGAgentConfig,
        thread_context: ThreadContext
    ) -> LegalRetrievalEvent:
        """Retrieve relevant legal documents."""

        # Get user query
        query = event.messages[-1].content

        # Retrieve documents
        retriever = agent_config.retriever_config.as_retriever()
        nodes = await retriever.aretrieve(query)

        # Filter by confidence threshold
        filtered_nodes = [
            node for node in nodes
            if node.score >= agent_config.confidence_threshold
        ]

        # Limit to max_citations
        top_nodes = filtered_nodes[:agent_config.max_citations]

        # Store query in thread context
        history = await thread_context.get("query_history", [])
        history.append({
            "query": query,
            "num_results": len(top_nodes)
        })
        await thread_context.set("query_history", history)

        return LegalRetrievalEvent(
            nodes=top_nodes,
            query=query,
            total_documents=len(filtered_nodes)
        )

    @step(
        name=LocaleString(en="Generate Cited Answer", de="Zitierte Antwort generieren"),
        description=LocaleString(en="Create answer with legal citations"),
        icon="mdi:gavel"
    )
    async def generate_answer_step(
        self,
        event: LegalRetrievalEvent,
        agent_config: LegalRAGAgentConfig
    ) -> CitedAnswerEvent:
        """Generate answer with citations."""

        llm = agent_config.llm_config.as_llm()

        # Build context from retrieved documents
        context_parts = []
        citations = []

        for i, node in enumerate(event.nodes, 1):
            # Extract metadata
            doc_id = node.node.metadata.get("document_id", "unknown")
            doc_title = node.node.metadata.get("title", "Untitled")
            doc_section = node.node.metadata.get("section", "")

            # Add to context
            context_parts.append(f"[{i}] {node.node.text}\n(Source: {doc_title}, {doc_section})")

            # Track citation
            citations.append({
                "index": i,
                "document_id": doc_id,
                "title": doc_title,
                "section": doc_section,
                "relevance_score": node.score
            })

        context = "\n\n".join(context_parts)

        # Construct prompt
        prompt = f"""You are a legal assistant. Answer the user's question based on the provided legal documents.

IMPORTANT: Include citation numbers [1], [2], etc. in your answer to reference the sources.

Legal Documents:
{context}

User Question: {event.query}

Answer (with citations):"""

        # Generate response
        response = await llm.acomplete(prompt)

        # Calculate confidence (average of top node scores)
        confidence = sum(n.score for n in event.nodes) / len(event.nodes) if event.nodes else 0.0

        return CitedAnswerEvent(
            answer=response.text,
            citations=citations,
            confidence=confidence
        )

    @step(
        name=LocaleString(en="Format Response", de="Antwort formatieren"),
        description=LocaleString(en="Format answer with citations for display"),
        icon="mdi:format-text"
    )
    async def format_response_step(
        self,
        event: CitedAnswerEvent,
        agent_config: LegalRAGAgentConfig
    ) -> ChunkEvent:
        """Format response with citations."""

        # Build formatted response
        response_parts = [event.answer]

        if event.citations:
            response_parts.append("\n\n**Citations:**")
            for cite in event.citations:
                response_parts.append(
                    f"[{cite['index']}] {cite['title']} - {cite['section']} "
                    f"(Relevance: {cite['relevance_score']:.2f})"
                )

        response_parts.append(f"\n*Confidence: {event.confidence:.2%}*")

        formatted_response = "\n".join(response_parts)

        return ChunkEvent(content=formatted_response)

    @step(
        name=LocaleString(en="Complete", de="Abschließen"),
        description=LocaleString(en="Finalize agent execution"),
        icon="mdi:check-circle-outline"
    )
    async def complete_step(
        self,
        event: ChunkEvent
    ) -> StopEvent:
        """Finalize workflow."""

        return StopEvent(result={
            "response": event.content,
            "agent_type": "legal_rag"
        })
```

### Testing

**File**: `tests/test_legal_rag_agent.py`

```python
import pytest
from aihub_lib.nats.events import UserMessageEvent
from aihub_agent.agents.LegalRAGAgent import LegalRAGAgent, LegalRAGAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


@pytest.mark.asyncio
async def test_legal_rag_agent():
    """Test legal RAG agent workflow."""

    runner = AgentTestRunner(agent_class=LegalRAGAgent)

    config = LegalRAGAgentConfig(
        agent_class="LegalRAGAgent",
        agent_id="test-legal-agent",
        retriever_config={
            "retriever_type": "vector",
            "index_name": "legal_docs",
            "top_k": 5
        },
        max_citations=3,
        confidence_threshold=0.7
    )

    event = UserMessageEvent.create_for_user_message(
        user_id="test-user",
        content="What are the requirements for contract formation?"
    )

    result = await runner.run(agent_config=config, start_event=event)

    assert result.stop_event is not None
    assert "Citations:" in result.stop_event.result["response"]
    assert "Confidence:" in result.stop_event.result["response"]
```

### Trigger Script

**File**: `LegalRAGAgent/trigger.py`

```python
import asyncio
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_agent.agents.LegalRAGAgent import LegalRAGAgent, LegalRAGAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    enable_logging()

    runner = AgentTestRunner(agent_class=LegalRAGAgent)

    config = LegalRAGAgentConfig(
        agent_class="LegalRAGAgent",
        agent_id="trigger-test",
        retriever_config={
            "retriever_type": "vector",
            "index_name": "legal_docs",
            "top_k": 5
        },
        max_citations=3,
        confidence_threshold=0.7
    )

    queries = [
        "What are the requirements for contract formation?",
        "Explain the doctrine of promissory estoppel",
        "What are the remedies for breach of contract?"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        event = UserMessageEvent.create_for_user_message(
            user_id="test-user",
            content=query
        )

        result = await runner.run(agent_config=config, start_event=event)

        if result.stop_event:
            print("\n📄 Response:")
            print(result.stop_event.result["response"])

        if result.exception_event:
            print(f"\n❌ Error: {result.exception_event.exception}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 11. Reference and Resources

### Essential Documentation

| Resource | Location |
|----------|----------|
| **Platform Overview** | `/home/user/aihub-core/README.md` |
| **Agent Developer Guide** | `/home/user/aihub-core/AGENTS.md` |
| **aihub_agent Scope Guide** | `/home/user/aihub-core/aihub_agent/AGENTS.md` |
| **aihub_lib Scope Guide** | `/home/user/aihub-core/aihub_lib/AGENTS.md` |
| **Swiss AI Agent Protocol** | `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/` |
| **ADRs** | `/home/user/aihub-core/aihub_doc/arc42/decisions/` |

### Key Files Reference

| Component | File |
|-----------|------|
| **Agent Base Class** | `/home/user/aihub-core/aihub_agent/aihub_agent/agents/Agent.py` |
| **Step Decorator** | `/home/user/aihub-core/aihub_agent/aihub_agent/workflow/decorators/step.py` |
| **Precondition Decorator** | `/home/user/aihub-core/aihub_agent/aihub_agent/workflow/decorators/precondition.py` |
| **RunContext** | `/home/user/aihub-core/aihub_agent/aihub_agent/context/run/RunContext.py` |
| **ThreadContext** | `/home/user/aihub-core/aihub_agent/aihub_agent/context/thread/ThreadContext.py` |
| **AgentTestRunner** | `/home/user/aihub-core/aihub_agent/aihub_agent/runners/AgentTestRunner.py` |
| **Event Hierarchy** | `/home/user/aihub-core/aihub_lib/aihub_lib/nats/events/` |
| **BaseDispatcher** | `/home/user/aihub-core/aihub_lib/aihub_lib/nats/dispatcher/BaseDispatcher.py` |

### Example Agents to Study

| Agent | Purpose | Complexity | Location |
|-------|---------|------------|----------|
| **SimpleAgent** | Linear A→B→C workflow | Beginner | `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/simple_workflow/` |
| **HumanInTheLoopAgent** | HITL pattern | Beginner | `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/human_in_the_loop_workflow/` |
| **ContextAgent** | RunContext/ThreadContext usage | Beginner | `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/context_workflow/` |
| **PreconditionAgent** | Parallel synchronization | Intermediate | `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/precondition_workflow/` |
| **RAGAgent** | Full production RAG | Advanced | `/home/user/aihub-core/aihub_agent/aihub_agent/agents/RagAgent/` |
| **NamespaceSelectionAgent** | Multi-pattern (HITL + AITL) | Advanced | `/home/user/aihub-core/aihub_agent/aihub_agent/agents/NamespaceSelectionAgent/` |

### Playground Examples

Located in `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/`:

- `simple_workflow/` - Basic linear flow
- `conditional_workflow/` - Branching logic
- `human_in_the_loop_workflow/` - User input
- `agent_in_the_loop_workflow/` - Agent delegation
- `bounded_loop/` - Iteration with limits
- `fan_out_workflow/` - Parallel processing
- `precondition_workflow/` - Parallel sync
- `context_workflow/` - State management
- `configured_workflow/` - AgentConfig usage
- `multi_locale_workflow/` - Internationalization
- `displaying_workflow/` - DisplayEvents
- `semantic_workflow/` - OpenTelemetry integration

### Access Points (Dev Environment)

| Service | URL | Purpose |
|---------|-----|---------|
| **OpenWebUI** | http://localhost:8080 | Chat interface |
| **Admin UI** | http://localhost:3000 | Agent management |
| **API** | http://localhost:8000 | REST API + WebSocket |
| **Phoenix** | http://localhost:6006 | Observability + tracing |
| **Dagster** | http://localhost:3000 | Pipeline orchestration |
| **SeaweedFS** | http://localhost:8889 | Object storage UI |

### Development Commands

```bash
# Setup
cd /home/user/aihub-core/aihub_agent
poetry shell
poetry install

# Code Quality
make format              # Black formatter
make lint                # Ruff + MyPy
make pr-ready            # Format + lint (run before commit)

# Testing
make test                # All tests
pytest tests/test_my_agent.py -v  # Specific test
pytest -k "not azure"    # Exclude Azure tests

# Utilities
make clean               # Remove build artifacts
make help                # Show all commands
```

### Community and Support

- **GitHub**: https://github.com/bbvch-ai/aihub-core
- **Issues**: https://github.com/bbvch-ai/aihub-core/issues
- **Project Board**: `gh project view 13 --owner bbvch-ai`

### Architecture Decision Records (ADRs)

Before making significant architectural changes, consult:

```bash
ls /home/user/aihub-core/aihub_doc/arc42/decisions/
```

Create ADR for:
- New dependencies
- New frameworks
- Pattern changes (e.g., event structure, context management)

### Next Steps

1. **Study Examples**: Start with `simple_workflow`, then `human_in_the_loop_workflow`
2. **Build Prototype**: Create minimal agent using this guide
3. **Add Complexity**: Incrementally add HITL, AITL, preconditions
4. **Test Thoroughly**: Write unit tests, BDD scenarios, use Phoenix
5. **Deploy Locally**: Test in OpenWebUI before production
6. **Monitor**: Use Phoenix to verify behavior in production
7. **Iterate**: Refine based on observability data

---

## Appendix: Quick Start Checklist

- [ ] Clone repository
- [ ] Set up Poetry environment (`poetry install`)
- [ ] Start Docker stack (`docker-compose.dev.yml up`)
- [ ] Verify services (Phoenix, OpenWebUI, API)
- [ ] Study `simple_workflow` example
- [ ] Create agent directory structure
- [ ] Define `AgentConfig` subclass
- [ ] Implement agent with `@step()` methods
- [ ] Write unit tests
- [ ] Run `make pr-ready` (must pass)
- [ ] Run `make test` (must pass)
- [ ] Test with `trigger.py`
- [ ] Verify in Phoenix (http://localhost:6006)
- [ ] Deploy to OpenWebUI
- [ ] Test end-to-end
- [ ] Monitor and iterate

---

**End of Guide**

This guide provides a complete foundation for building AI agents in Swiss AI-Hub. For advanced topics, refer to the playground examples and production agents. Happy coding!
