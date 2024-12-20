
# 6. Pipelines

## 6.1 Data Ingestion with Dagster

> tldr; Data ingestion pipelines ensure that agents always operate on current, consistent, and well-prepared data. By automating ingestion, leveraging observable assets, using dynamic partitions, and maintaining strict traceability, the AI-Hub creates a stable foundation upon which agents can build their intelligent reasoning.
> 
> The result: Reduced manual effort, higher data quality, and a more reliable end-to-end AI solution that adapts gracefully as client needs and data environments evolve.


Before agents can reason intelligently about a domain, the underlying data—such as documents, policies, or reference manuals—must be readily available in a structured, searchable form. Pipelines in the AI-Hub ecosystem handle this critical preparatory stage. They ingest raw data from various sources, parse and transform it, and store it in a format that agents can easily consume, such as vector embeddings for semantic search.

This section introduces how the AI-Hub leverages [Dagster](https://dagster.io/) to implement data ingestion pipelines. Dagster’s rich feature set—such as **Observable Assets**, **Automation Policies**, and **Dynamic Partitions**—helps achieve reliable, transparent, and traceable data workflows. The code snippets provided in the overall repository (some excerpts shown above) illustrate how these concepts are put into practice, but the core principles remain accessible even without diving deeply into the specific implementation details.

### Observable Assets and Automation Policies

**What are Observable Assets?**  
In Dagster, an **Observable Asset** is a data resource whose state can be dynamically monitored. Instead of running pipelines blindly on a fixed schedule, the system can observe whether new documents have appeared in the data lake or if existing content has changed. When changes occur, it can trigger pipeline runs automatically, ensuring the knowledge base stays fresh with minimal manual intervention.

**Automation Policies:**  
- **Eager Automation:** If a pipeline asset is defined with an “eager” automation policy, Dagster attempts to run the pipeline as soon as it detects changes. For example:
  - When a new file arrives in the data lake, a downstream pipeline asset that depends on it will trigger automatically, updating the document store and vector database.
  - If a file is updated or removed, the pipeline reacts accordingly, removing stale data and indexing new content.

This approach reduces manual overhead. Instead of an operator periodically kicking off ingest jobs, the pipelines react to the data’s natural life cycle, saving time and ensuring that agents always have access to current information.

### Document Parsing and Indexing

**From Raw Documents to Structured Data:**  
Raw documents—PDFs, Markdown files, Word documents—require processing before agents can leverage them. The ingestion pipeline typically involves steps like:

1. **Fetching Files from Data Lake:**  
   Pipelines observe a data lake (e.g., Azure Data Lake) to detect new or updated documents.  
   
2. **Conversion into Ref Docs:**  
   Raw files are converted into a standardized reference document (RefDoc), adding metadata such as titles, authors, or timestamps. This normalization ensures downstream assets handle data uniformly, regardless of the original file format.

3. **Chunking and Node Creation:**  
   Long documents are split into smaller chunks or “nodes” using structural parsers (e.g., Markdown structural node parsing). Breaking content into granular nodes makes semantic retrieval more precise and reduces the overhead of repeatedly processing large documents.

4. **Embedding Nodes:**  
   Each node is transformed into a vector embedding using an embedding model (e.g., `text-embedding-ada-002` on Azure OpenAI). These embeddings are stored in a vector database, enabling semantic search capabilities that agents rely on for retrieval-augmented generation.

5. **Insertion into Document and Vector Stores:**  
   Parsed documents and their embedded nodes are inserted into specialized stores (e.g., MongoDB for raw documents and metadata, Azure AI Search for vector embeddings). This ensures that when agents run queries, they can quickly find relevant chunks without re-processing large volumes of text.

**Dynamic Partitions for Scalability:**  
Dagster’s **Dynamic Partitions** allow pipelines to treat each file or document as a separate partition. The pipeline scales as the number of documents grows. When a new file is detected, a new partition is created, and only that partition’s logic runs, avoiding unnecessary reprocessing of all data.

### Reproducibility and Transparency

**Data Versions and Traceability:**  
In a complex system with continuous data updates, ensuring reproducibility and auditability is crucial. Pipelines assign **DataVersions** to each partition, reflecting the current state of the document. If a document changes, its DataVersion changes, prompting re-ingestion and re-indexing. This mechanism ensures that:

- You can always trace which version of the data was used to produce a given agent response.
- Historical runs can be audited and reproduced, supporting debugging and compliance requirements.

**Observability and Monitoring:**  
Dagster’s tools and the AI-Hub’s integration with logging and telemetry frameworks mean that every pipeline run is fully observable. Developers and operators can:
- Inspect which partitions ran, which documents were updated, and when.
- Monitor performance metrics, ensuring pipelines complete efficiently.
- Set up alerts or notifications if certain conditions are met (e.g., missing expected documents or unusually long processing times).

### Putting It All Together

A typical data ingestion scenario might look like this:

1. **Detect Change:** A new Markdown file is uploaded to the data lake.
2. **Observable Asset Triggers Run:** Dagster notices the change and triggers a pipeline run for that specific file (a dynamic partition).
3. **Document Conversion:** The pipeline converts the file into a RefDoc, adding metadata and storing it in the document store.
4. **Chunking & Embedding:** The pipeline splits the RefDoc into nodes, embeds them into vector form, and inserts those embeddings into the vector database.
5. **Agent-Ready Data:** Now, when an agent receives a user query requiring that document, it can semantically retrieve the relevant chunks, confident that the data is up-to-date and well-structured.


## 6.2 Customization and Reuse

> tldr; Customization and reuse are key to ensuring the AI-Hub’s pipelines can handle diverse client scenarios without sacrificing maintainability. By leveraging common pipeline assets, projects start from a high baseline of tested functionality. Introducing custom logic is straightforward and isolated, enabling rapid adaptation to unique requirements.
> 
> This flexible architecture means that no matter how specialized a client’s data ingestion needs may be, the AI-Hub can adapt, scaling from straightforward, generic pipelines to intricate, domain-specific workflows—with minimal overhead and maximum reusability.


While the AI-Hub pipelines provide a robust foundation for data ingestion—covering standard steps such as parsing documents, generating embeddings, and indexing data—each client project may have unique requirements. This is where the AI-Hub’s architecture for customization and reuse shines. By offering a library of common pipeline assets and a clear strategy for introducing client-specific logic, the AI-Hub ensures that developers can adapt pipelines to meet varying needs without reinventing the wheel.

### Common Pipeline Assets

**Purpose of Common Assets:**
- The AI-Hub includes a set of ready-to-use pipeline assets designed for frequent tasks:  
  1. **Data Lake Observers:** Monitor a data lake for new or updated files.  
  2. **Document Converters:** Convert raw files (PDF, Markdown, Word) into RefDocs with consistent metadata.  
  3. **Node Chunkers:** Break down large documents into nodes suitable for embedding.  
  4. **Embedders & Indexers:** Generate vector embeddings and insert them into vector stores or document databases.

By using these predefined assets, developers do not start from scratch for each new project. Instead, they compose existing building blocks to create a pipeline that fits the client’s scenario. This accelerates development, reduces the likelihood of errors, and ensures a consistent approach to data ingestion across multiple projects.

**Easy Composition:**
- Pipelines are written in a way that assembling them into a client-specific workflow is like putting together Lego bricks. You pick the relevant assets—observable data lake sources, document parsing, embedding steps—and chain them together to form a pipeline that exactly matches the client’s data processing requirements.

**Versioned and Maintained:**
- As the AI-Hub evolves, these common assets are improved, tested, and documented. Clients using these assets benefit from ongoing enhancements—like performance optimizations, support for new file types, or improved embedding strategies—without additional implementation effort.

### Introducing Client-Specific Logic

Despite the robust nature of the common pipeline assets, every client has unique aspects that may require customized code. For example:
- **Special File Formats:** A client may have documents with unusual formats, requiring a custom parser.
- **Domain-Specific Metadata Extraction:** Certain projects need to extract proprietary metadata fields from documents that aren’t covered by the standard pipeline assets.
- **Custom Business Rules:** For instance, some clients might only want to ingest documents that meet certain criteria (e.g., containing a specific keyword, or passing a certain validation step).

**Where to Add Custom Code:**
1. **New Ops within Existing Graph Assets:**  
   If the customization involves a small variation—like a custom parser step—developers can introduce a new operation (op) that hooks into the existing pipeline graph. This op might transform data just after it’s fetched from the data lake or right before nodes are inserted into the vector store.

2. **Extended Asset Factories:**  
   The AI-Hub code you’ve seen includes factory functions (like `documents_factory` and `nodes_factory`) that produce assets. Client-specific logic can be introduced by subclassing or wrapping these factories to modify certain steps.  
   - For example, a custom “document parser” resource can be passed into the factory so that it uses a different parsing logic for the client’s documents.

3. **Custom Resource Definitions:**
   Resources define external dependencies and configurations. By swapping a resource—like using a different embedding model or a custom data lake client—developers can alter the pipeline’s behavior without touching the core asset logic.

**Isolation and Maintainability:**
- Client-specific code should be placed in the client’s own GitHub repository or namespace, separate from the AI-Hub core. As discussed in [Section 3.2 (The Role of the AI-Hub in Projects)](3_project_phases_and_client_engagement.md#32-the-role-of-the-ai-hub-in-projects), this ensures that generic code remains in the AI-Hub core repository, while confidential and project-specific logic stays with the client.  
- This separation also simplifies upgrades to the AI-Hub core. When the core is updated, client projects can integrate the new version at their own pace, adjusting their custom code if necessary.

### Balancing Generic and Specific Logic

**Principled Extension:**
- The AI-Hub encourages a layered approach:  
  - **Core Layer:** Provides generic, widely applicable pipeline assets.  
  - **Client Layer:** Extends or customizes the core to address client-specific needs.
  
By separating concerns in this manner, developers maintain a clean architecture. Generic improvements to the pipeline core benefit all clients, while customizations remain isolated and easy to maintain.

**Incremental Adoption:**
- Clients can start with a minimal pipeline—using mostly standard assets—and gradually add customization as they discover unique needs. This reduces initial complexity and shortens the time-to-value, as the team doesn’t need to build everything from scratch at the onset.

### Practical Examples

- **Custom Parser for Specialized Documents:**  
  Suppose a client has a proprietary document format. The developer can write a custom parser op and insert it into the pipeline after the data lake fetch step. The rest of the pipeline remains unchanged.
  
- **Additional Metadata Extraction:**  
  If the client wants to store extra metadata fields in the document store, modify or wrap the asset that converts raw files to RefDocs. The rest of the pipeline still benefits from common embedding and indexing steps.

- **Alternative Embedding Model:**
  If a client’s domain requires a specialized embedding model, replace the standard embedding resource with a custom resource. The same nodes and indexing logic apply, but now powered by a different model tailored to the client’s domain.

