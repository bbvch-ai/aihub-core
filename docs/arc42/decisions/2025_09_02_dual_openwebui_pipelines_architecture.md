# Dual OpenWebUI Pipeline Architecture: Event-Based vs OpenAI-Compatible

## Context

The Swiss AI Hub platform needed to integrate with Open-WebUI to provide users access to both sophisticated AI agents
and simple LLM models through a unified interface. The challenge was that these represent fundamentally different use
cases:

- **AI Agents**: Complex workflows with tool usage, reasoning steps, knowledge retrieval, and human-in-the-loop
  interactions that generate rich events
- **LLM Models**: Simple text generation without additional capabilities, accessed through standard interfaces

A single pipeline approach would either oversimplify agent capabilities or overcomplicate model access.

## Decision Drivers

- **Agent Workflow Visibility**: Swiss AI Hub agents generate rich events (ThoughtEvent, ToolEvent, RetrieverEvent,
  HumanInTheLoopEvent) that need to be displayed in OpenWebUI using its native UI features (thinking indicators, tool
  execution status, source citations, interactive prompts)
- **OpenWebUI Feature Integration**: OpenWebUI provides specific event types (`"source"`, `"status"`, `"input"`,
  `"replace"`) and HTML rendering capabilities that enable sophisticated agent workflow visualization - these features
  should be leveraged for agent interactions
- **Raw Model Access**: Many use cases need simple LLM access without agent complexity - just pure model inference
  through standard OpenAI-compatible endpoints for programmatic access and existing tooling
- **Integration Scope Separation**:
  - **Agent Integration**: Complex event processing to showcase Swiss AI Hub's sophisticated agent capabilities in
    OpenWebUI
  - **Model Integration**: Direct LLM access without event translation overhead

## Decision

We implement two separate OpenWebUI pipelines in `aihub_integration`:

1. **Event-Based Agent Pipeline** (`aihub_pipeline.py`): Complex event processing to showcase Swiss AI Hub agent
   capabilities with full OpenWebUI feature utilization
2. **OpenAI-Compatible Model Pipeline** (`openai_pipeline.py`): Simple pass-through for direct model access without
   event processing overhead

## Consequences

### Positive

- **Optimized User Experience**: Agent pipeline showcases full Swiss AI Hub capabilities with rich UI features, model
  pipeline provides straightforward LLM access
- **Clear Separation**: Each pipeline serves its specific use case without compromising the other
- **Ecosystem Compatibility**: Model pipeline works seamlessly with existing OpenAI client libraries and tools
- **Performance Match**: Simple model requests avoid event processing overhead, complex agent workflows get full feature
  support

### Negative

- **Maintenance Overhead**: Two separate codebases require independent maintenance, testing, and updates
- **User Choice Complexity**: Users must understand which pipeline matches their specific integration needs
- **OpenWebUI Dependency Risk Differential**:
  - **Agent Pipeline**: Deep integration with OpenWebUI's event system (`__event_emitter__`, event types like
    `"source"`, `"status"`, `"input"`, `"replace"`) makes it more fragile to OpenWebUI internal changes
  - **Model Pipeline**: Lighter dependency on OpenWebUI's pipeline interface, but still dependent on OpenWebUI's
    pipeline system
- **Breaking Change Impact**: OpenWebUI updates may break agent pipeline functionality while leaving model pipeline
  unaffected, or vice versa

### Trade-offs

- **Integration Depth vs Stability**: Agent pipeline's rich OpenWebUI integration provides better UX but higher
  maintenance risk from OpenWebUI changes
- **Feature Richness vs Simplicity**: Agent pipeline enables advanced UI features at the cost of complexity and
  fragility

Both pipelines depend on OpenWebUI, but the agent pipeline's deeper integration with OpenWebUI's internal event system
creates higher coupling and maintenance risk.
