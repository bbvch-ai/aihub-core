# Adopt mem0 for Agent Memory with Dual Vector and Graph-Based Storage

## Context

AI-Hub agents operate statelessly, starting each conversation fresh without knowledge of past interactions. This prevents agents from learning user preferences, adapting behavior, or accumulating knowledge about the user's world. Users must repeatedly explain the same context and preferences, reducing efficiency and personalization.

Different agents serve different purposes (RAG, code assistant, process orchestrator). Each should adapt independently to user preferences while sharing a common understanding of organizational context and factual information.

## Decision Drivers

- **Agent Learning**: Agents must improve through experience, learning preferences and adapting behavior
- **Dual Memory Types**: Preferences (agent-specific) vs facts (shared) require different storage mechanisms
- **Mature Framework**: Leverage established solutions to avoid reimplementing complex memory management
- **Continuous Improvement**: Benefit from community-driven enhancements automatically
- **Customization**: Framework must be extensible for Swiss AI Agent Protocol integration
- **Metadata Preservation**: Maintain thread_id, display_id, run_id for traceability

## Decision

We implement a dual-memory architecture using **mem0** (https://mem0.ai) with custom patches:

### Vector-Based Memory (Agent-Specific Preferences)
- **Purpose**: Store user preferences and behavioral adaptations per agent
- **Scope**: Agent-specific (RAGAgent memories ≠ CodeAssistant memories)
- **Retrieval**: Semantic similarity search
- **Example**: "User prefers concise code examples" (CodeAssistant) vs "User wants detailed citations" (RAGAgent)

**Rationale**: Different agents serve different purposes. Preference for detailed explanations in a research agent shouldn't affect preference for concise responses in a code assistant.

### Graph-Based Memory (Shared Factual Knowledge)
- **Purpose**: Store hard facts about user's world as interconnected knowledge graph
- **Scope**: Shared across all agents
- **Retrieval**: Graph traversal
- **Example**: "User works on Project X" → "Project X uses Python 3.11" → relationships enable contextual understanding

**Rationale**: Factual organizational context, projects, and relationships are not agent-specific. When one agent learns "Project Falcon uses microservices," all agents should understand this for consistent assistance.

### Technology: mem0
- **Established**: Production-ready with active community support
- **Dual Storage**: Native vector (embeddings) and graph (Neo4j) support
- **Passive Improvements**: Automatic bug fixes and optimizations from mem0 team
- **LLM Integration**: Built-in memory extraction, deduplication, and semantic search

### Custom Extensions
We extend mem0 in two key areas:

1. **Metadata Preservation**: Ensure complete Swiss AI Agent Protocol context (thread, display, run) is preserved during memory updates for full traceability
2. **Graph Integrity**: Validate entity relationships before creation to prevent orphaned connections in the knowledge graph
3. **Agent Customization**: Configure memory extraction strategies per agent type to capture relevant information

## Consequences

### Positive
- Agents learn and improve through experience
- Reduced repetition—users don't re-explain context
- Personalized interactions per agent type
- Shared organizational knowledge across all agents
- Battle-tested framework with community improvements

### Trade-offs
- Framework dependency requires monitoring for breaking changes
- Custom patches need maintenance during mem0 updates
- Dual storage (Milvus + Neo4j) increases operational complexity
- LLM-extracted memories may need human oversight for accuracy
- Additional LLM calls for memory extraction increase costs
- GDPR compliance requires memory management UI and deletion capabilities
