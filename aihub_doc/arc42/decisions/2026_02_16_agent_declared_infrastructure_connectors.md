# Agent-Declared Infrastructure Connectors

## Context

`AgentRunner` hardcoded connections to NATS, Redis, Milvus, and MongoDB in its `start()` method. Every agent connected
to all four services unconditionally, regardless of whether it actually used them. Three problems resulted:

1. **Unnecessary connections**: Agents like `LLMWrappingAgent` connected to Milvus and MongoDB despite never using
   either. This wasted resources and required all infrastructure to be reachable even when not needed, which also
   complicated health checks by reporting on infrastructure irrelevant to the agent.
2. **Per-step connection waste**: `MilvusVectorStoreConfig.to_llama_index()` created a fresh `MilvusClient` on every
   retrieval step invocation, completely independent of the connection the runner had established. These stale
   connections accumulated over time.
3. **Hidden dependencies**: There was no explicit declaration of which infrastructure an agent required. The runner
   connected to everything, masking the actual dependency graph. `AgentMemory` further obscured this by having a
   transitive dependency on Milvus (via Mem0) that was not obvious to agent developers.

## Decision Drivers

- *Agent class as single source of truth*: Infrastructure requirements should be declared alongside the agent's workflow
  definition, not scattered across deployment files.
- *Shared connections prevent resource waste*: A single Milvus client should be reused across retrieval steps instead of
  creating new connections per step.
- *Minimal configuration*: Agents that don't need specific infrastructure should not require it to be configured.
- *Fail-fast validation*: Missing infrastructure dependencies should be caught at injection time with clear error
  messages, including transitive dependencies like AgentMemory requiring MilvusConnector.

## Decision

Agent classes declare their infrastructure requirements via a `connectors` ClassVar:

```python
class RAGAgent(Agent):
    connectors: ClassVar = [MongoConnector, MilvusConnector]

class LLMWrappingAgent(Agent):
    connectors: ClassVar = []  # inherited from base
```

The lifecycle works as follows:

1. **Declaration**: Agent classes list connector types as `ClassVar[list[type[InfrastructureConnector]]]`.
2. **Auto-discovery**: `AgentRunner` reads `agent_type.connectors` and instantiates connector instances automatically.
   No `connectors=` parameter in `main.py`.
3. **Lifecycle management**: Runner connects/disconnects connectors during start/stop, includes them in health checks.
4. **Dependency injection**: `AgentDispatcher._get_parameter_value()` injects connected connector instances into
   workflow steps that declare them as parameters. It also validates transitive dependencies (e.g., a step requesting
   `AgentMemory` requires `MilvusConnector` to be declared).
5. **Shared Milvus client**: The `MilvusConnector.client` is threaded through the retrieval chain via optional
   parameters (`to_llama_index(client=...)`, `KnowledgeRetriever(config, milvus_client=...)`,
   `retrieve_from_all_sources(..., milvus_client=...)`) so all retrieval steps reuse the same connection.

## Consequences

- Agent classes are self-documenting: looking at the class reveals all infrastructure dependencies.
- `main.py` files are minimal — no connector imports or configuration needed.
- Shared Milvus connections eliminate per-step connection creation during retrieval.
- The `to_llama_index(client=None)` fallback maintains backward compatibility for callers that don't have a shared
  client (e.g., test utilities, pipelines).
- Clear error messages when connector declarations are incomplete (e.g., step requests `MilvusConnector` but agent
  doesn't declare it).
