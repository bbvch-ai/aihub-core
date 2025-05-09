# AIHub Pipeline Core

This project provides a structured data pipeline built with Dagster to process documents from an Azure Data Lake, store
them, and index their content for semantic search.

## Core Assets and Workflow

The pipeline is primarily composed of the following interconnected assets:

1. **`data_lake` (Observable Source Asset):**
    - **Purpose:** Monitors a specified directory in the Azure Data Lake for new or updated files. It dynamically
      creates partitions based on the discovered files and tracks their versions.
    - **Trigger:** Automatically detects changes in the data lake.

2. **`removed_documents`:**
    - **Purpose:** Identifies documents that exist in the Document Store but are no longer present in the Data Lake. It
      then triggers their removal from both the Document Store and the Vector Store.
    - **Input:** The current list of files in the Data Lake (`data_lake`).

3. **`documents`:**
    - **Purpose:** Takes individual files from the Data Lake (as partitions) and converts them into structured
      `RefDocDocument` objects. These documents are then stored in the Document Store.
    - **Input:** Individual data lake files (partitioned).
    - **Output:** `RefDocDocument` objects stored via the `DocStoreIOManager`.

4. **`nodes`:**
    - **Purpose:** Processes the `RefDocDocument` objects (again, as partitions), splitting their content into smaller
      `TextNode` chunks. These nodes are then embedded using an embedding model and indexed in the Vector Store.
    - **Input:** Individual `RefDocDocument` objects (partitioned).
    - **Output:** Embedded `TextNode` objects stored via the `VectorStoreIOManager`.

The typical data flow is: Data Lake -> `data_lake` (observation) -> `removed_documents` (cleanup) -> `documents` (
processing and storage in Document Store) -> `nodes` (chunking, embedding, and storage in Vector Store).

## Key IO Managers

IO Managers are crucial for handling the input and output of assets, abstracting away the details of data storage and
retrieval. This project utilizes the following custom IO Managers:

- **`AzureDataLakeIOManager`:**
    - **Role:** Responsible for reading `DataLakeFile` objects from and writing them to the Azure Data Lake. It handles
      metadata associated with the files and presents them as `DataLakeFile` Python objects within the Dagster pipeline.

- **`DocStoreIOManager`:**
    - **Role:** Manages the storage and retrieval of `RefDocDocument` objects from a Document Store (currently MongoDB).
      When an asset outputs a `RefDocDocument` and is configured to use this IO Manager, the document is automatically
      saved. Subsequent assets that take a `RefDocDocument` as input (with the same IO Manager configuration) will load
      it from the Document Store based on the partition key (which corresponds to the document ID or URI).

- **`VectorStoreIOManager`:**
    - **Role:** Handles the storage and retrieval of `TextNode` objects (representing document chunks) from a Vector
      Store (currently Azure AI Search or Milvus). Similar to the `DocStoreIOManager`, it automatically saves outputted
      `TextNode` lists and loads them as inputs for downstream assets, using the document ID as the key for retrieval.

## Resources

The pipeline relies on various Dagster resources to interact with external systems and services, including:

- **Data Lake Resources (`DataLakeClientResource`, `DataLakeFileSystemResource`, `DataLakeResource`):** Provide
  connections and configurations for interacting with the Azure Data Lake.
- **Document Store Resources (`DocStoreResource`, `MongoDocumentStoreResource`):** Establish connections to the MongoDB
  document store.
- **Vector Store Resources (`AzureAISearchVectorStoreResource`, `MilvusVectorStoreResource`):** Configure connections to
  the Azure AI Search or Milvus vector store.
- **LLM Resources (`EmbeddingModelResource`, `LanguageModelResource`):** Provide access to language models (e.g., Azure
  OpenAI) for embedding generation and potentially other NLP tasks.
- **Parser
  Resources (`DocumentParserResource`, `MarkdownStructuralNodeParserResource`, `RecursiveSummaryParserResource`):**
  Define how different file types are parsed into documents and how documents are split into nodes.

## Usage

To use this project, you would typically:

1. **Define a Dagster `Definitions` object:** This object would include the assets defined in
   `aihub_pipeline.assets.factories`, the IO Managers in `aihub_pipeline.io`, and the resources in
   `aihub_pipeline.resources.factory`.
2. **Configure the resources:** Provide the necessary connection details, API keys, and configurations for your specific
   Azure Data Lake, Document Store, Vector Store, and LLM setup. This is usually done through `dagster.yaml` or when
   launching Dagster.
3. **Run the pipeline:** Dagster will orchestrate the execution of the assets based on dependencies and triggers (e.g.,
   the `data_lake` sensor). The IO Managers will automatically handle the loading and saving of data between the assets
   and the external storage systems.

The `playground` directory provides an example of how these components can be wired together for local testing and
experimentation.

## Repository Structure (Simplified)

aihub_pipeline/
assets/ # Defines the core data processing steps as Dagster assets.
automation/ # Contains logic for automated asset materialization.
io/ # Custom IO Managers for handling data lake, document store, and vector store interactions.
jobs/ # Defines Dagster jobs for orchestrating asset runs.
ops/ # Individual Dagster operations that perform specific tasks.
resources/ # Configurations and connections to external services (data lake, databases, LLMs, etc.).
schedules/ # Defines schedules for recurring job executions.
sensors/ # Defines sensors for reacting to external events (e.g., new data lake files).
types/ # Custom Python types used within the pipeline.
util/ # Utility functions.
playground/ # Example setup for local testing.

```

