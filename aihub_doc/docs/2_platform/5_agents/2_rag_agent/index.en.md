---
title: RAG Agent
---

# The RAG Agent: Your Knowledge Specialist

One of the default agents included with the Swiss AI Hub is the **RAG Agent**. This agent is your organization's
knowledge specialist, designed to answer questions by consulting your internal documents and data sources. It uses a
powerful technique called **Retrieval-Augmented Generation (RAG)** to provide answers that are accurate, current, and
grounded in your specific business context.

This section explains what the RAG Agent is, how it works, and why it's a cornerstone of trustworthy enterprise AI.

## The Problem with Standard AI: The Knowledge Gap

Large Language Models (LLMs) are trained on vast amounts of public internet data. While this makes them incredibly
knowledgeable about general topics, it also creates critical limitations for enterprise use:

- **Their knowledge is outdated**: Their information is frozen at the time of their last training, which could be months
  or years ago.
- **They don't know your business**: They have no access to your internal reports, policies, project documents, or
  proprietary data.
- **They can "hallucinate"**: When they don't know an answer, they might generate a plausible-sounding but factually
  incorrect response.
- **They can't cite their sources**: You can't easily verify where their information came from.

The RAG Agent is specifically designed to overcome these limitations.

## How the RAG Agent Works

Instead of relying solely on its pre-trained knowledge, the RAG Agent follows a systematic process to ground its answers
in your organization's verified information.

When you ask the RAG Agent a question, it executes a sophisticated workflow:

1. **Question Understanding**: First, the agent uses an LLM to understand and rephrase your question into an optimal
   query for searching its knowledge base. If you're in a long conversation, it condenses the chat history to ensure the
   query is self-contained.
2. **Knowledge Retrieval**: The agent then performs a semantic search across one or more designated **Knowledge Bases**.
   These are vector-indexed collections of your documents, managed through the platform's Knowledge Management service
   and populated by data pipelines (both topics are covered in detail later). The search returns the most relevant
   snippets of text, or "chunks," from your documents.
3. **Context Reconstruction**: An isolated text chunk often lacks meaning. A snippet that says "as per the new policy"
   is useless without the policy's context. The agent intelligently reconstructs the surrounding context by retrieving
   adjacent chunks from the original document or even parent-level summaries, ensuring it understands the full picture.
4. **Re-ranking for Relevance**: The agent may receive dozens of potentially relevant chunks. To improve accuracy, it
   employs a **re-ranking** step. A specialized model evaluates the initial search results against your specific
   question and re-orders them, pushing the most relevant information to the top.
5. **Answer Synthesis**: Finally, the agent takes your original question, the top-ranked, context-rich information it
   has retrieved, and feeds it all to an LLM. It instructs the model to formulate a comprehensive answer based *only* on
   the provided information and to cite its sources.

This rigorous process ensures the answer you receive is not just a guess from a generic AI, but a synthesized response
grounded in your actual data.

### The Role of Knowledge Bases and Pipelines

The RAG Agent's effectiveness depends on the quality and currency of its knowledge. This is where two other core
components of the Swiss AI Hub come into play:

- **Knowledge Bases**: These are the structured, searchable libraries of your organization's information. In the UI, you
  can create and manage different knowledge bases for different topics (e.g., "HR Policies," "Technical Documentation,"
  "Project Alpha Files"). A RAG Agent is always configured to search within one or more specific knowledge bases.
- **Data Ingestion Pipelines**: These are the automated processes that keep your knowledge bases up-to-date. A default
  pipeline can automatically process documents you upload via the UI. More advanced, custom pipelines can be configured
  to continuously synchronize with external sources like **SharePoint**, ensuring that any changes to your documents are
  automatically reflected in the knowledge base.

While these components are documented in detail later, it's important to understand that the RAG Agent works in concert
with them to provide a living, breathing knowledge system.

## Advanced Capabilities

The RAG Agent includes several advanced features to handle complex queries and ensure the quality of its responses.

### Multi-Hop Retrieval

Sometimes, a single search isn't enough to answer a complex question. If the agent's initial retrieval doesn't provide
sufficient information, it can perform **multi-hop retrieval**. The agent analyzes the information gap, formulates a
new, more specific query, and performs another search to gather the missing pieces. This iterative process allows it to
answer questions that require synthesizing information from multiple different documents or sections.

### Guardrails and Safety Checks

Before answering, the agent can employ "guardrails" to validate the query and the retrieved context:

- **Few-Shot Guard**: This checks if your question is appropriate and within the agent's designed scope by comparing it
  against pre-defined examples of good and bad questions. If your query is out of scope, the agent will politely decline
  to answer.
- **Context Sufficiency Guard**: This checks if the retrieved information is actually sufficient to answer your
  question. If not, it can trigger the multi-hop retrieval process to find more information or inform you that a
  complete answer cannot be found in its knowledge base.

These checks prevent the agent from providing low-quality or irrelevant answers, further enhancing its reliability.

## Why the RAG Agent Matters for Your Business

By deploying a RAG Agent, you gain a powerful tool that:

- **Democratizes Knowledge**: Employees can get instant, accurate answers from vast repositories of internal
  documentation without needing to know which document to look for or who to ask.
- **Increases Productivity**: It dramatically reduces the time spent searching for information, allowing your team to
  focus on higher-value tasks.
- **Builds Trust in AI**: By providing verifiable, source-cited answers and operating within defined guardrails, the RAG
  Agent demonstrates that AI can be a reliable and transparent partner in the workplace.
- **Ensures Information Currency**: Thanks to automated data pipelines, the agent's knowledge is always as current as
  your source documents, eliminating the risk of decisions based on outdated information.
