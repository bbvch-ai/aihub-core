---
title: Data Pipelines
---

# Data Pipelines: Creating the AI's Knowledge

An AI agent is only as intelligent as the information it can access. Raw organizational data—spread across PDFs, SharePoint sites, and network drives—is not in a format that an AI can readily use. The **Data Pipeline** layer is the powerful engine that bridges this gap, transforming your disparate documents and data sources into a structured, searchable, and AI-ready **Knowledge Base**.

Think of a data pipeline as an automated factory for knowledge. It takes raw materials (your documents) and runs them through a sophisticated assembly line to produce a refined product (an indexed, searchable knowledge base) that your agents can use to provide accurate, context-aware answers.

## From Documents to Intelligence: The Pipeline Process

At its core, a data pipeline is an automated workflow that ingests, processes, and indexes your information. While this process can be highly customized, every pipeline follows a series of fundamental steps to ensure your data is prepared correctly for AI consumption.

::: info The Goal of a Pipeline
The end-to-end purpose is to convert unstructured documents into a structured **vector index**. This index allows an AI agent to search for information based on semantic meaning, not just keywords, which is the foundation of an effective RAG system.
:::

Here's a look at the key stages in a typical data ingestion pipeline:

**1. Connect & Ingest**
The first step is to connect to your data wherever it lives. The platform provides connectors for a wide range of enterprise systems, allowing pipelines to automatically monitor and retrieve documents from sources like Microsoft SharePoint, network drives, or web pages.

**2. Parse & Understand**
Once a document is retrieved, the pipeline needs to understand its content and structure. It uses advanced parsing techniques to extract text, tables, and metadata from various formats like PDF, Word, and Excel. Crucially, it works to preserve the document's original semantic structure—headings, lists, and sections—which is vital for context.

**3. Chunk & Segment**
LLMs have a limited context window, so they cannot process entire large documents at once. The pipeline intelligently breaks down the documents into smaller, semantically meaningful "chunks." This isn't just a random split; the system tries to create chunks that represent a coherent idea or topic, ensuring the pieces make sense on their own.

**4. Embed & Vectorize**
This is where the magic happens for AI search. The pipeline translates the meaning of each text chunk into a numerical format called a **vector embedding**. These vectors capture the semantic essence of the text, allowing the AI to find chunks with similar meanings, even if they don't share the same keywords.

**5. Index & Store**
Finally, these vector embeddings, along with the original text and metadata, are stored and indexed in a specialized **vector database**. This creates the final, searchable Knowledge Base that your RAG Agents will use to find information.

## The Power of Automation: Living Knowledge

A key feature of the platform's data pipelines is that this is not a one-time, manual process. Pipelines are designed to be **automated and continuous**.

You can configure a pipeline to monitor a data source, like a SharePoint folder, for any changes. When a document is added, updated, or deleted, the pipeline automatically triggers and synchronizes the changes with the Knowledge Base.

::: tip Set It and Forget It
This continuous synchronization ensures your AI's knowledge is always current. When a policy is updated in SharePoint, the pipeline ensures the agent has access to the new version immediately, without any manual intervention. Your knowledge base becomes a living, breathing entity that evolves with your organization.
:::

## Orchestration and Reliability: Built on Dagster

To manage these complex, multi-step workflows, the Swiss AI Hub uses **Dagster**, an industrial-grade data orchestrator. Dagster acts as the conductor for your data pipelines, ensuring every process runs reliably, efficiently, and transparently.

Dagster is responsible for:
-   **Scheduling and Triggering**: Running pipelines on a schedule or in response to events.
-   **Error Handling**: Gracefully managing failures and retries, ensuring transient issues don't corrupt your data.
-   **Observability**: Providing a complete, auditable log of every pipeline run, so you can see exactly how a document was processed and troubleshoot any issues.

This robust foundation means you can trust your data pipelines to operate reliably in a production environment, even at a massive scale.

## The Strategic Advantage: Why This Architecture Matters

The platform's data pipeline architecture provides several critical advantages for any enterprise AI strategy:

::: details A Decoupled Architecture
The separation of data ingestion (pipelines) from AI operation (agents) is a deliberate design choice. It allows your teams to work independently. Data engineering can focus on building robust pipelines and connecting new data sources, while AI developers can focus on building intelligent agent logic. The agents simply consume the high-quality knowledge bases the pipelines produce, without needing to know the complexities of how they were created.
:::

::: details Complete Observability and Governance
Unlike a "black box" system, every step of the pipeline is tracked and logged. If an agent provides a strange answer, you can trace it all the way back through the retrieval process to the exact document chunk and even the pipeline run that processed it. This "glass box" approach is essential for debugging, compliance, and building organizational trust.
:::

::: details Consistency and Quality Control
By defining data processing as code within a pipeline, you ensure that every document is handled in a consistent, repeatable manner. You can embed quality checks, validation rules, and security scans directly into your pipelines, guaranteeing that only high-quality, compliant information makes it into your knowledge bases.