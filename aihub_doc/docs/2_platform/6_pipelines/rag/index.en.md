---
title: Document Reconstruction for Context
index: 2
---

# Deep Dive: The RAG Ingestion Pipeline

The RAG Agent's ability to provide context-aware, accurate answers is not magic; it is the direct result of the meticulous work performed by the **RAG Ingestion Pipeline**. This pipeline is the automated process that transforms your raw, unstructured documents into a highly structured and semantically rich knowledge base.

This section delves into the stages of this pipeline, explaining how it goes far beyond simple text extraction to build a foundation for truly intelligent retrieval.

## The Challenge: Raw Text is Not Knowledge

Simply extracting text from a document and putting it into a database is not enough to create a useful knowledge base for an AI. Raw text lacks the critical context and relationships that a human reader understands intuitively. For an AI, a paragraph that says *"see the diagram in Section 3.2"* is meaningless without knowing what Section 3.2 contains.

The fundamental challenge for any RAG system is a trade-off:
-   **Small text chunks** are great for precise searching but lack context.
-   **Large text chunks** have plenty of context but are bad for precise searching and can exceed an LLM's memory limit.

The Swiss AI Hub's RAG pipeline is engineered to solve this problem by not just chunking documents, but by actively mapping and preserving their internal structure.

## The Stages of the RAG Pipeline

The pipeline processes each document through a series of sophisticated stages, building a rich, interconnected representation of the information.

### 1. Ingestion and Parsing
The process begins when the pipeline retrieves a document from a connected source. It then uses advanced parsing technology to extract not just the raw text, but also to identify structural elements like headings, tables, lists, and sections. This structural understanding is the first step toward preserving context.

### 2. Intelligent Chunking
Next, the pipeline breaks the document down into optimally-sized text chunks, or "nodes." This is a critical step that balances retrieval precision with context. The system uses semantic chunking techniques to ensure that these breaks occur at natural topic or section boundaries, keeping coherent thoughts together.

### 3. Enrichment and Relationship Mapping
This is the pipeline's most crucial stage, where it transforms a simple list of chunks into a "knowledge graph." Instead of treating each chunk as an isolated piece of data, the pipeline establishes explicit relationships between them.

**Preserving Sequential Context**
The pipeline analyzes the original document order and creates a bidirectional link between every sequential chunk. Each chunk knows its predecessor and its successor. This effectively turns the document's content into a linked list, allowing an agent to later reconstruct entire passages by traversing these links.

**Capturing Hierarchical Context**
For complex documents with sections and subsections, the pipeline does even more. It identifies the hierarchical structure and can generate summaries at each level (e.g., a summary for Section 3, and another for Section 3.2). It then links the individual text chunks back to their parent summaries. A chunk from subsection 3.2.4 now has a direct link to the summary of 3.2, which in turn links to the summary of Section 3.

### 4. Embedding and Indexing
Finally, each chunk and summary is converted into a vector embedding and stored in the vector database. The critical difference is that these vectors are stored *along with all the relationship metadata* created in the previous step.

::: tip The Output: A Structurally-Aware Knowledge Base
The final product of the RAG pipeline is not just a searchable index of text. It is a structurally-aware knowledge base where every piece of information knows its place within the original document and its relationship to the surrounding content. This rich structure is the key that unlocks the RAG Agent's advanced capabilities.
:::

## How the Pipeline Empowers the RAG Agent

This meticulous preparation by the pipeline is what enables the sophisticated retrieval and reasoning features of the RAG Agent. When an agent queries the knowledge base, it's not just getting back a list of disconnected text snippets; it's getting back a set of entry points into a rich knowledge graph.

::: details Unlocking Advanced Agent Capabilities
-   **Document Reconstruction**: When the agent retrieves a relevant chunk, it can use the "previous-next" links created by the pipeline to fetch the surrounding chunks, effectively reconstructing the full paragraph or passage for complete context. This is how it understands references like *"the requirement specified above."*

-   **Hierarchical Understanding**: If an agent retrieves a very specific detail, it can traverse the "parent" links created by the pipeline to fetch summaries of the containing sections. This helps the agent understand the broader context of a specific piece of information, answering the question *"Where does this detail fit in the big picture?"*

-   **Smarter Multi-Hop Retrieval**: The rich metadata and structure created by the pipeline allow the agent to perform more intelligent multi-hop queries. If the agent determines its initial context is insufficient, it can use the document's structure to formulate a more precise follow-up query, for example, by specifically targeting a different section of the same document.
:::

In essence, the RAG Ingestion Pipeline does the hard work up front. It invests computational resources during the ingestion phase to build a high-fidelity representation of your knowledge. This investment pays off every time a user asks a question, enabling the RAG Agent to perform with a level of contextual understanding and accuracy that simpler systems cannot achieve.