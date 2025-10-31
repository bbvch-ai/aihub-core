---
title: Organizing knowledge with collections
---

# Organizing knowledge with collections

Collections (technically called "namespaces") organize documents within a knowledge database. Each namespace is a
logical container for related documents.

## How collections work

When documents are ingested, they receive a collection label as metadata. This label travels with every chunk of the
document in the vector store. When an agent searches for information, it filters by collection to retrieve only relevant
documents.

![Creating a new collection](../../../../media/knowledge/create_new_collection.png)

Collections don't nest. They're flat metadata attributes. Agents can search across multiple collections simultaneously
without navigating a hierarchy.

## Access control

Collection access control operates at the agent level, not the user level. When you configure an agent to access
specific collections, every user interacting with that agent sees responses based on the same knowledge set.

All users get the same agent responses from a given agent instance. If users shouldn't access certain information, don't
give them access to that agent. The same agent workflow can be deployed multiple times with different collection
configurations, creating distinct instances for different audiences.

## Configuration

Agents specify which collections to search in their retrieval configuration. The platform searches all configured
collections in parallel and merges results by relevance scores. Update agent collection access through configuration
without code changes.

Restricting retrieval to relevant collections reduces search space and improves performance. Collections can follow
different retention policies and update cycles.

## Naming

Collection names can contain alphanumeric characters, hyphens, and underscores. Use clear, descriptive names like "hr,"
"sales-policies," or "technical_docs."

::: info Technical note
While the UI calls these "collections," they're technically implemented as "namespaces" in the codebase and appear as
namespace metadata on document chunks in the vector store.
:::
