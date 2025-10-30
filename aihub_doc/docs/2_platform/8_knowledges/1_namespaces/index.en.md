---
title: Organizing knowledge with collections
---

# Organizing knowledge with collections

Collections (technically called "namespaces") organize documents within a knowledge database. Each namespace is a logical container for related documents - think of them as folders, but optimized for vector search instead of hierarchical navigation.

## How collections work

When documents are ingested, they receive a collection label as metadata. This label travels with every chunk of the document in the vector store. When an agent searches for information, it can filter by collection to retrieve only relevant documents.

![Creating a new collection](../../../../media/knowledge/create_new_collection.png)

Unlike file system folders, collections don't nest. They're flat metadata attributes. This means agents can search across multiple collections simultaneously without navigating a hierarchy - you get the organizational benefits of categorization with the performance benefits of direct metadata filtering.

## Access control model

The AI-Hub implements collection access control at the agent level, not the user level. When you configure an agent to access specific collections, every user interacting with that agent sees responses based on the same knowledge set.

This has important implications:

**Consistent behavior** - All users get the same agent responses, making testing and validation straightforward. You don't need to test every possible user permission combination.

**Simple security model** - If users shouldn't access information in an agent's collections, don't give them access to that agent. Access control happens at the "should this person use this tool" level, not during query execution.

**Agent reusability** - The same agent workflow can be deployed multiple times with different collection configurations, creating distinct instances for different audiences.

For example, a support agent workflow might deploy as:

```
Public Support Agent
├─ Collections: public
└─ Available to: all customers

Partner Support Agent
├─ Collections: public, partner
└─ Available to: authorized partners

Internal Support Agent
├─ Collections: public, partner, internal
└─ Available to: employees only
```

Each instance uses identical workflow logic but operates on different knowledge scopes.

## Knowledge access patterns

**Domain specialization** - Configure agents with narrow collection access to focus on specific knowledge areas. A regulatory compliance agent might access only legal and compliance collections, improving retrieval relevance by preventing contamination from unrelated information.

**Multi-domain agents** - Agents requiring broader knowledge specify multiple collections in their retrieval configuration. The platform searches all configured collections in parallel and merges results by relevance scores.

**Dynamic scope adjustment** - Update agent collection access through configuration without code changes. Adding a new product line means updating agent configurations to include the new collection.

## Operational benefits

**Independent updates** - Update knowledge in one collection without affecting others. Test new ingestion pipelines in isolated collections without impacting production agents.

**Performance optimization** - Restricting retrieval to relevant collections reduces search space, improving both speed and relevance. As knowledge bases grow, collection-focused retrieval prevents performance degradation.

**Lifecycle management** - Different collections can follow different retention policies and update cycles. Legal documents need long retention with infrequent updates, while product specifications update frequently but expire after discontinuation. Archive inactive collections without affecting current agents.

## Design considerations

When designing collection structure, balance these factors:

**Granularity** - Collections define the finest granularity of access control. Most organizations find the sweet spot at the business unit, product family, or functional area level - coarse enough to avoid excessive agent proliferation, fine enough to enable meaningful access differentiation.

**Stability** - Collection structures should remain relatively stable. Reorganizations require reingestion and agent reconfiguration. Design schemes that accommodate business growth without frequent restructuring.

**Naming conventions** - Collection names must not contain hyphens or underscores. Use simple, lowercase names like "hr," "sales," or "compliance." Clear naming helps administrators understand which collections provide relevant knowledge for specific agent roles and which combinations enable appropriate access scopes.

**Cross-cutting concerns** - Information spanning multiple domains (security policies, brand guidelines) can be duplicated across collections or organized in dedicated collections that most agents access alongside domain-specific ones.

**Agent instance planning** - Think about which collection combinations will deploy as agent instances. If user groups need access to specific knowledge subsets, organize those subsets as coherent groups you can assign to dedicated agent instances.

## Example collection schemes

::: details By department
```
hr
engineering
sales
finance
```
:::

::: details By product
```
alphatechnical
alphamarketing
betatechnical
betamarketing
```
:::

::: details By information type
```
policies
technical
training
compliance
```
:::

::: details By security classification
```
public
internal
confidential
```
:::

Choose a scheme that matches how your organization already thinks about information access and agent deployment.

::: info Technical note
While the UI calls these "collections," they're technically implemented as "namespaces" in the codebase and appear as namespace metadata on document chunks in the vector store.
:::
