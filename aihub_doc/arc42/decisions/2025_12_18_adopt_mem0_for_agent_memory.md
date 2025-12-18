# Adopt mem0 for Agent Memory with Dual Storage and Dual Scoping

## Context

AI-Hub agents operate statelessly, starting each conversation fresh without knowledge of past interactions. This
prevents agents from learning user preferences, adapting behavior, or accumulating knowledge about the user's world.
Users must repeatedly explain the same context and preferences, reducing efficiency and personalization.

Different agents serve different purposes (RAG, code assistant, process orchestrator). Each should adapt independently
to user preferences while sharing a common understanding of organizational context and factual information.

Additionally, multi-tenant deployments require clear separation between:
- Individual user knowledge (private, personal context)
- Organizational knowledge (shared across all users within a tenant)

## Decision Drivers

- **Agent Learning**: Agents must improve through experience, learning preferences and adapting behavior
- **Dual Storage Types**: Preferences (agent-specific) vs facts (shared) require different storage mechanisms
- **Dual Scopes**: User-private memories vs organization-shared memories serve different use cases
- **Privacy Boundaries**: Individual user data must remain isolated from other users while enabling shared organizational knowledge
- **Mature Framework**: Leverage established solutions to avoid reimplementing complex memory management
- **Continuous Improvement**: Benefit from community-driven enhancements automatically
- **Customization**: Framework must be extensible for Swiss AI Agent Protocol integration
- **Metadata Preservation**: Maintain thread_id, display_id, run_id for traceability
- **Multi-Tenancy**: Support department-level memory isolation via tenant namespaces

## Decision

We implement a dual-scope, dual-storage memory architecture using **mem0** (https://mem0.ai):

### Memory Scopes

**UserMemory**: Individual user scope, LLM-inferred from conversations, private.
- Example: "User prefers concise code examples"
- Rationale: Personal preferences and context must remain isolated. Different users have different working styles.

**OrganizationMemory**: Tenant scope with optional namespace for department isolation, explicitly provided facts, shared across all users.
- Example: "We deploy to production on Fridays", "Project Falcon uses microservices architecture"
- Rationale: Organizational knowledge must be accessible to all. When one user documents "Our API uses OAuth2", all agents should leverage this for consistent assistance.

### Storage Types

**Vector-Based (Milvus)**: Stores memories as embeddings for semantic similarity search.
- Why: Retrieve relevant context based on semantic meaning of current conversation. "Tell me about authentication" should surface OAuth2 memories even without exact keyword match.

**Graph-Based (Neo4j)**: Stores entities and their relationships in a knowledge graph.
- Why: Enable relational understanding that vector search alone cannot provide. When agent learns "User works on Project Falcon" → "Project Falcon uses microservices" → "Microservices require service mesh", graph traversal provides multi-hop contextual understanding. Vector search would miss these transitive relationships.
- Critical for: Organizational hierarchies, project dependencies, technology stack relationships, team structures.

**Rationale for dual storage**: Vector search excels at semantic matching but cannot traverse relationships. Graph storage excels at relationships but cannot perform semantic search. Both are necessary for complete memory functionality.

### Technology: mem0

- **Established**: Production-ready with active community support
- **Dual Storage**: Native vector (embeddings) and graph (Neo4j) support
- **Passive Improvements**: Automatic bug fixes and optimizations from mem0 team
- **LLM Integration**: Built-in memory extraction, deduplication, and semantic search

### Custom Extensions

1. **Metadata Preservation**: Swiss AI Agent Protocol context (thread_id, display_id, run_id) preserved across both scopes
2. **Graph Integrity**: Validate entity relationships before creation
3. **Dual Scope Implementation**: Separate UserMemory/OrganizationMemory classes with distinct NATS events

## Consequences

### Positive

- Agents learn and adapt to individual user preferences while respecting privacy
- Shared organizational knowledge accessible to all users for consistent assistance
- Reduced repetition—users don't re-explain context
- Vector search for semantic retrieval, graph traversal for relational understanding
- Battle-tested framework with community improvements
- Department-level isolation via tenant namespaces

### Trade-offs

- Dual scope + dual storage increases conceptual and operational complexity
- Developers must choose correct scope when implementing agents
- LLM-inferred memories may need human oversight for accuracy
- Additional LLM calls for memory extraction increase costs
- Explicit organization memories require user effort to document
- Framework dependency requires monitoring for breaking changes
- GDPR compliance requires memory management UI and deletion capabilities for both scopes
- Organization memory deletion affects all users (requires careful access control)
