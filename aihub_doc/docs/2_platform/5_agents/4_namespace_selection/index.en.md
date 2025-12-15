---
title: Namespace selection agent
---

# Namespace selection agent

The Namespace Selection Agent gives users control over which knowledge collections the AI searches when answering
questions. Instead of searching all available knowledge, users can specify exactly which collections are relevant to
their query.

## Why namespace selection exists

Organizations often have multiple knowledge collections serving different purposes: HR policies, technical
documentation, project files, legal guidelines. When a user asks a question, searching all collections simultaneously
can return irrelevant results and slow down responses.

The Namespace Selection Agent solves this by asking users which collections to search before retrieving information.
This creates a more focused, accurate, and efficient search experience.

## How it works

When you interact with an agent configured with namespace selection, the workflow follows these steps:

1. **You ask a question**: Submit your query through the chat interface.

2. **The agent asks which collections to search**: Before searching, the agent presents you with a list of available
   collections (namespaces) and asks which ones to include in the search.

3. **You select collections**: Choose one or more collections relevant to your question. For example, if asking about
   vacation policies, you might select only the "HR Policies" collection.

4. **The agent searches your selected collections**: The RAG (Retrieval-Augmented Generation) agent retrieves
   information only from the collections you specified.

5. **You receive a focused answer**: The response is generated using only information from your selected collections,
   ensuring relevance and traceability.

## Multi-bucket scenarios

Some deployments organize knowledge into multiple "buckets"—logical groupings of collections. For example:

- **Corporate knowledge bucket**: HR policies, company guidelines, internal procedures
- **Technical knowledge bucket**: API documentation, architecture guides, troubleshooting docs
- **Project bucket**: Project-specific documents, meeting notes, requirements

When multiple buckets are configured, the agent asks you to select collections from each relevant bucket. This allows
cross-domain queries while maintaining clear boundaries between knowledge sources.

## Benefits

### User control

You decide which knowledge sources inform your answers. This is particularly valuable when you know exactly where the
relevant information resides or when you want to exclude certain sources.

### Improved relevance

By narrowing the search space, the agent retrieves more relevant documents. Searching a 50-document HR collection for
policy questions yields better results than searching 10,000 documents across all topics.

### Performance

Smaller search spaces mean faster retrieval times. When you select specific collections, the vector search operates on a
subset of the total knowledge base.

### Transparency

You always know which collections contributed to an answer. This makes verification straightforward—you can check the
cited sources within the specific collection you selected.

## Configuration

Administrators configure which buckets and collections are available to each agent:

- **Buckets**: Define which knowledge buckets the agent can access
- **Collections within buckets**: Each bucket contains multiple collections (namespaces) users can select
- **Default behavior**: Agents can be configured to require selection or use defaults

The configuration determines what options users see when asked to select collections. Users can only choose from
collections they have been granted access to through the agent configuration.

## Interaction patterns

### First-time queries

When you start a new conversation, the agent will ask which collections to search. Your selection persists for the
duration of the conversation thread.

### Follow-up questions

For follow-up questions in the same thread, the agent typically uses your previous selection. Some configurations may
ask you to confirm or update your selection for each question.

### Changing selections

You can request to change your collection selection at any time by asking the agent to search different collections.
The agent will present the selection interface again.

## When namespace selection is not needed

Not all agents use namespace selection. Agents configured to search a single, focused knowledge base may skip the
selection step entirely. The agent's configuration determines whether selection is offered.
