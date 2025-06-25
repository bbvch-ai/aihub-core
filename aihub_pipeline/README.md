# AIHub Pipeline Core

This project provides a structured data pipeline built with Dagster to ingest documents from sources like SharePoint,
process them via an Azure Data Lake staging area, store them, and index their content for semantic search.

## Core Assets and Workflow

The pipeline is composed of two primary stages, each with its own set of interconnected assets:

### Stage 1: SharePoint to Data Lake Ingestion

This stage is responsible for synchronizing files from a SharePoint site to Azure Data Lake, which acts as a durable,
versioned source for the main processing pipeline.

1. **`observable_share_point` (Observable Source Asset):**
    - **Purpose:** Monitors a SharePoint site for new or updated files based on their last modified date and etag.
    - **Trigger:** Can be scheduled to run periodically to detect changes.

2. **`data_lake_files`:**
    - **Purpose:** Takes a file reference from SharePoint, downloads its content, and writes it to the Azure Data Lake
      as a `DataLakeFile` object.
    - **Input:** An individual SharePoint file reference.
    - **Output:** A `DataLakeFile` object written to Azure Data Lake via the `AzureDataLakeIOManager`.

3. **`removed_data_lake_files`:**
    - **Purpose:** Identifies files that have been removed from SharePoint but still exist in the Data Lake staging
      area, and deletes them.
    - **Input:** The current list of files in SharePoint.

### Stage 2: Data Lake to Vector Store Processing

This stage picks up files from the Data Lake, processes them, and indexes them for retrieval.

1. **`data_lake` (Observable Source Asset):**
    - **Purpose:** Monitors the Azure Data Lake for new or updated `DataLakeFile` objects. It dynamically creates
      partitions for each file and tracks their versions using a content hash.
    - **Trigger:** Automatically detects changes pushed from Stage 1 or from direct uploads.

2. **`removed_documents`:**
    - **Purpose:** Identifies documents that exist in the final Document Store but are no longer present in the Data
      Lake. It triggers their removal from both the Document Store and the Vector Store.
    - **Input:** The current list of files in the Data Lake (`data_lake`).

3. **`documents`:**
    - **Purpose:** Takes individual files from the Data Lake, parses them, extracts and reformats content like tables
      and figures, and converts them into structured `RefDocDocument` objects. These are then stored in the Document
      Store.
    - **Input:** Individual data lake files (partitioned).
    - **Output:** `RefDocDocument` objects stored via the `DocStoreIOManager`.

4. **`nodes`:**
    - **Purpose:** Processes the `RefDocDocument` objects, splitting their content into smaller `TextNode` chunks. These
      nodes are then embedded using an embedding model and indexed in the Vector Store.
    - **Input:** Individual `RefDocDocument` objects (partitioned).
    - **Output:** Embedded `TextNode` objects stored via the `VectorStoreIOManager`.

## Key IO Managers

IO Managers are crucial for handling the input and output of assets, abstracting away the details of data storage and
retrieval.

- **`SharePointIOManager`:**
    - **Role:** Handles the loading of file information and content from SharePoint.

- **`AzureDataLakeIOManager`:**
    - **Role:** Responsible for reading `DataLakeFile` objects from and writing them to the Azure Data Lake. It handles
      metadata associated with the files and presents them as `DataLakeFile` Python objects.

- **`DocStoreIOManager`:**
    - **Role:** Manages the storage and retrieval of `RefDocDocument` objects from a Document Store (e.g., MongoDB). It
      automatically saves outputs and loads inputs based on the partition key.

- **`VectorStoreIOManager`:**
    - **Role:** Handles the storage and retrieval of `TextNode` objects from a Vector Store (e.g., Azure AI Search or
      Milvus). It saves outputted `TextNode` lists and loads them for downstream assets.

## Resources

The pipeline relies on various Dagster resources to interact with external systems and services:

- **SharePoint Resource (`SharePointResource`):** Provides the client for connecting to and fetching files from a
  SharePoint site.
- **Data Lake Resources (`DataLakeClientResource`, `DataLakeFileSystemResource`, `DataLakeResource`):** Provide
  connections and configurations for interacting with the Azure Data Lake.
- **Document Store Resources (`DocStoreResource`, `MongoDocumentStoreResource`):** Establish connections to the MongoDB
  document store.
- **Vector Store Resources (`AzureAISearchVectorStoreResource`, `MilvusVectorStoreResource`):** Configure connections to
  the Azure AI Search or Milvus vector store.
- **LLM Resources (`EmbeddingModelResource`, `LanguageModelResource`):** Provide access to language models (e.g., Azure
  OpenAI) for embedding generation and other NLP tasks.
- **Parser Resources (`DocumentParserResource`, `MarkdownStructuralNodeParserResource`, etc.):** Define how different
  file types are parsed and how documents are split into nodes.

## Usage

To use this project, you would typically:

1. **Define a Dagster `Definitions` object:** This object would include the assets defined in
   `aihub_pipeline.assets.factories`, the IO Managers in `aihub_pipeline.io`, and the resources in
   `aihub_pipeline.resources.factory`.
2. **Configure the resources:** Provide the necessary connection details, API keys, and configurations for your specific
   setup. This is usually done through environment variables or `dagster.yaml`.
3. **Run the pipeline:** Dagster will orchestrate the execution of the assets based on dependencies and triggers. The IO
   Managers automatically handle the data flow between assets and external storage systems.

The `playground` directory provides an example of how these components can be wired together for local testing and
experimentation.

## Repository Structure (Simplified)

```
aihub_pipeline/
├── assets/       # Defines the core data processing steps as Dagster assets.
├── automation/   # Contains logic for automated asset materialization.
├── io/           # Custom IO Managers for storage interactions.
├── jobs/         # Defines Dagster jobs for orchestrating asset runs.
├── ops/          # Individual Dagster operations that perform specific tasks.
├── resources/    # Configurations and connections to external services.
├── schedules/   # Defines schedules for recurring job executions.
├── sensors/      # Defines sensors for reacting to external events.
├── types/        # Custom Python types (Pydantic models) used in the pipeline.
├── util/         # Utility functions.
└── playground/   # Example setup for local testing.
```
