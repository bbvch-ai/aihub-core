# Adopt mem0 for Agent Memory with Dual Storage and Dual Scoping

## Context

Swiss AI Hub agents operate statelessly, starting each conversation fresh without knowledge of past interactions. This
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
- **Privacy Boundaries**: Individual user data must remain isolated from other users while enabling shared
  organizational knowledge
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

**OrganizationMemory**: Tenant scope with optional namespace for department isolation, explicitly provided facts, shared
across all users.

- Example: "We deploy to production on Fridays", "Project Falcon uses microservices architecture"
- Rationale: Organizational knowledge must be accessible to all. When one user documents "Our API uses OAuth2", all
  agents should leverage this for consistent assistance.

### Storage Types

Both scopes use dual storage, but with different purposes:

**In UserMemory context:**

- **Vector store**: Agent-specific preferences. "User prefers concise responses" in CodeAssistant doesn't affect
  RAGAgent behavior.
- **Graph store**: Shared factual knowledge across all agents. "User works on Project Falcon" is relevant to all agents.
- Why both: Preferences must be isolated per agent (different agents serve different purposes), while facts should be
  shared (all agents benefit from knowing user's projects/context).

**In OrganizationMemory context:**

- **Vector store**: Organizational facts via semantic search. Retrieve relevant policies/conventions by meaning.
- **Graph store**: Organizational facts via relationships. "Project Falcon uses microservices" → "Microservices require
  service mesh" enables multi-hop understanding.
- Why both: Some queries need semantic matching ("How do we handle authentication?"), others need relationship traversal
  ("What technologies does Project Falcon depend on?").

**Rationale for dual storage**: Vector search excels at semantic matching but cannot traverse relationships. Graph
storage excels at relationships but requires exact entity matches. UserMemory additionally uses storage type to separate
agent-specific preferences from agent-shared facts.

### Technology: mem0

- **Established**: Production-ready with active community support
- **Dual Storage**: Native vector (embeddings) and graph (Neo4j) support
- **Passive Improvements**: Automatic bug fixes and optimizations from mem0 team
- **LLM Integration**: Built-in memory extraction, deduplication, and semantic search

### Custom Extensions

1. **Metadata Preservation**: Swiss AI Agent Protocol context (thread_id, display_id, run_id) preserved across both
   scopes
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
