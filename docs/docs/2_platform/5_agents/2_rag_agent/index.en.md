---
title: RAG agent
---

# RAG agent

The RAG Agent answers questions by retrieving information from your internal documents. It uses Retrieval-Augmented
Generation (RAG) to ground responses in your organization's data rather than relying only on the LLM's pre-trained
knowledge.

## LLM limitations

LLMs train on public internet data. This creates limitations for enterprise use:

- Knowledge cutoff: Information freezes at the last training date (months or years ago)
- No business context: LLMs lack access to internal reports, policies, and proprietary data
- Hallucinations: LLMs generate plausible but incorrect answers when they don't know something
- No source attribution: Responses don't include citations for verification

RAG addresses these limitations by retrieving information from your documents before generating answers.

::: tip About "Training" Agents
The Swiss AI Hub does not offer model training or fine-tuning. Instead, the RAG Agent accesses current information by
retrieving it from your knowledge base at query time. This means the agent automatically "knows" about new or updated
documents without any retraining process.
:::

## How RAG works

The RAG Agent follows this workflow:

1. **Question understanding**: The LLM rephrases your question into an optimal search query. For ongoing conversations,
   it condenses chat history to make the query self-contained.

2. **Knowledge retrieval**: Semantic search runs across designated knowledge bases (vector-indexed collections of your
   documents). The search returns relevant text chunks.

3. **Context reconstruction**: Text chunks need surrounding context to be meaningful. The agent retrieves adjacent
   chunks from the original document or parent-level summaries to understand the full picture.

4. **Re-ranking**: A specialized model evaluates retrieved chunks against your question and reorders them by relevance.

5. **Answer synthesis**: The LLM generates an answer using only the top-ranked information and cites its sources.

This process grounds the response in your actual data rather than generic AI knowledge.

### Knowledge bases and pipelines

The agent retrieves information from knowledge bases, which are vector-indexed collections of documents. You configure
which knowledge bases the agent searches. Multiple knowledge bases can be created for different topics (HR policies,
technical documentation, project files).

[Data ingestion pipelines](../../6_pipelines/) maintain knowledge base content. The default pipeline processes documents
uploaded through the UI. Custom pipelines can synchronize with external sources like SharePoint, automatically updating
the knowledge base when source documents change.

## Advanced capabilities

### Multi-hop retrieval

If initial retrieval doesn't provide sufficient information, the agent can perform multi-hop retrieval. It analyzes the
information gap, formulates a new query, and performs another search. This iterative process helps answer questions
requiring information from multiple documents or sections.

### Guardrails

The agent can use [input and output guards](../../13_language_models/3_guards/) to validate queries and responses. For
example, the context sufficiency guard checks if retrieved information is adequate to answer a question. When context is
insufficient, the agent communicates this to the user rather than generating a hallucinated answer.
