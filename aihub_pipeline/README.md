---
title: AI-Hub Pipelines
index: 5
---

# 🚰 AI-Hub Pipeline Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_pipelines-core&metric=alert_status&token=593ae6b9d8cdff5202906c985f89034fb37d8c93)](https://sonarcloud.io/summary/new_code?id=aihub-core_pipelines-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_pipelines-core&metric=security_rating&token=593ae6b9d8cdff5202906c985f89034fb37d8c93)](https://sonarcloud.io/summary/new_code?id=aihub-core_pipelines-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_pipelines-core&metric=vulnerabilities&token=593ae6b9d8cdff5202906c985f89034fb37d8c93)](https://sonarcloud.io/summary/new_code?id=aihub-core_pipelines-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_pipelines-core&metric=sqale_rating&token=593ae6b9d8cdff5202906c985f89034fb37d8c93)](https://sonarcloud.io/summary/new_code?id=aihub-core_pipelines-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_pipelines-core&metric=ncloc&token=593ae6b9d8cdff5202906c985f89034fb37d8c93)](https://sonarcloud.io/summary/new_code?id=aihub-core_pipelines-core)

## 1. 🎯 Foundational Knowledge of Pipeline Development

This section covers the foundational architecture, patterns, and terminology you need to know before building data
ingestion and processing pipelines.

::: info 
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you
have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_pipeline`

You are contributing to the **aihub_pipeline** scope, which contains definitions for data ingestion and processing
pipelines within the AI-Hub platform. This scope implements robust, scalable data processing workflows using Dagster,
handling the complete lifecycle from document ingestion to vector embedding generation for RAG (Retrieval-Augmented
Generation) systems.

### 📁 Project Structure

The `aihub_pipeline` scope is organized as follows:

```
aihub_pipeline/
├── aihub_pipeline/             # Main package source
│   ├── assets/                 # Asset factories for data pipeline assets
│   │   └── factories/          # Asset creation factories
│   │       ├── data_lake_to_vector_store/    # Data lake to vector store pipeline
│   │       └── share_point_to_data_lake/     # SharePoint to data lake pipeline
│   ├── automation/             # Automation and dependency management
│   ├── executors/              # Job execution configuration
│   ├── io/                     # I/O managers for different storage systems
│   │   ├── AzureDataLakeIOManager.py         # Azure Data Lake I/O
│   │   ├── DocStoreIOManager.py              # Document store I/O
│   │   ├── SharePointIOManager.py            # SharePoint I/O
│   │   └── VectorStoreIOManager.py           # Vector store I/O
│   ├── jobs/                   # Job definitions and factories
│   ├── ops/                    # Operations for data processing
│   │   ├── data_lake/          # Data lake operations
│   │   ├── document/           # Document processing operations
│   │   ├── nodes/              # Node processing operations
│   │   └── share_point/        # SharePoint operations
│   ├── resources/              # Resource definitions and configurations
│   │   ├── data_lake/          # Data lake resource configurations
│   │   ├── doc_store/          # Document store resources
│   │   ├── llm/                # LLM and embedding model resources
│   │   ├── parser/             # Document parser resources
│   │   ├── share_point/        # SharePoint resources
│   │   └── vector_store/       # Vector store resources
│   ├── schedules/              # Pipeline scheduling configurations
│   ├── sensors/                # Event sensors and monitoring
│   ├── types/                  # Custom data types for pipeline
│   └── util/                   # Utility functions and helpers
└── playground/                 # Working example and testing - START HERE
    └── __init__.py             # Complete pipeline example
```

### 🏗️ The Data Processing Pipeline Architecture

::: info Pipeline Purpose
The AI-Hub pipeline follows a structured approach to document processing and knowledge extraction. Before agents can
reason intelligently about a domain, the underlying data must be readily available in a structured, searchable form.
Pipelines handle this critical preparatory stage by ingesting raw data from various sources, parsing and transforming
it, and storing it in a format that agents can easily consume.
:::

**Key Stages:**

1. **Document Ingestion**: SharePoint files are observed and ingested into the data lake with metadata extraction
2. **Document Processing**: Raw files are parsed and converted to structured RefDoc documents with consistent metadata
3. **Node Generation**: Documents are chunked into nodes using structural parsing strategies for precise retrieval
4. **Embedding Generation**: Text nodes are converted to vector embeddings using AI models (e.g.,
   text-embedding-ada-002)
5. **Vector Storage**: Embeddings are stored in vector databases for retrieval operations
6. **Summary Generation**: Hierarchical summaries are created for better context preservation

**Data Versions and Traceability:**
Each partition is assigned **DataVersions** that reflect the current state of the document. If a document changes, its
DataVersion changes, prompting re-ingestion and re-indexing. This ensures:

- You can always trace which version of the data was used to produce a given agent response
- Historical runs can be audited and reproduced, supporting debugging and compliance requirements

### 👁️ Observable Assets and Automation Policies

::: tip Observable Assets
**Observable Assets** are a core feature of the AI-Hub pipeline architecture. Instead of running pipelines blindly on a
fixed schedule, the system can observe whether new documents have appeared in the data lake or if existing content has
changed.
:::

```python
@observable_source_asset(
    key=AssetKey(["data_lake"]),
    partitions_def=document_partitions,
)
def data_lake_observer(context):
    """Observe data lake for new or changed documents."""
    # Monitor external data source for changes
    # Report new partitions when detected
    pass
```

**Automation Policies:**

- **Eager Automation**: When a pipeline asset is defined with "eager" automation, Dagster triggers runs automatically
  upon detecting changes
- **Reactive Processing**: When a new file arrives in the data lake, downstream assets update automatically
- **Reduced Manual Overhead**: Instead of periodic manual job kicks, pipelines react to data lifecycle changes

**Dynamic Partitions for Scalability:**
Dagster's **Dynamic Partitions** allow pipelines to treat each file or document as a separate partition. The pipeline
scales as documents grow - when a new file is detected, only that partition's logic runs, avoiding unnecessary
reprocessing.

### 🏗️ The Asset-Based Architecture

::: info
Pipelines are built using Dagster's asset-based approach where each stage produces concrete data artifacts:
:::

```python
@graph_asset(
    key=AssetKey(["documents"]),
    partitions_def=document_partitions,
    automation_condition=AutomationCondition.eager(),
)
def documents_asset(data_lake_file: DataLakeFile) -> RefDoc:
    """Process data lake files into structured documents."""
    return process_document_operation(data_lake_file)
```

**Asset Characteristics:**

- **Materialized**: Assets represent concrete data that can be inspected and debugged
- **Versioned**: Each asset materialization creates a versioned snapshot
- **Lineage**: Dependencies between assets provide clear data lineage tracking
- **Partitioned**: Assets can be partitioned for parallel processing and incremental updates

---

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging data processing pipelines.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

::: warning
Always activate the Poetry environment before working. All subsequent commands must be run from within this activated
shell.
:::

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

```bash
cd aihub_pipeline
poetry shell
```

### 🔍 Step 1: Understanding the Pipeline Architecture

::: info
Before implementing new pipeline components, understand the existing data flow and architecture patterns.
:::

#### 🧩 Core Pipeline Components

1. **Asset Factories**: Create reusable asset definitions

   ```python
   def documents_factory(
       key: AssetKey,
       data_lake_key: AssetKey,
       partitions: DynamicPartitionsDefinition,
   ) -> graph_asset:
       """Factory for creating document processing assets."""
       pass
   ```

2. **Operations**: Define individual processing steps

   ```python
   @op(
       required_resource_keys={"document_parser"},
       ins={"data_lake_file": In(DataLakeFile)},
       out=Out(RefDoc),
   )
   def parse_document(context, data_lake_file: DataLakeFile) -> RefDoc:
       """Parse document from data lake file."""
       pass
   ```

3. **Resources**: Configure external dependencies

   ```python
   class DocumentParserResource(ConfigurableResource):
       loader_type: LoaderType = LoaderType.DOCLING
       
       def get_parser(self) -> DocumentParser:
           """Get configured document parser."""
           pass
   ```

### 🛠️ Step 2: Create Pipeline Assets

::: info
Follow this pattern to create new pipeline assets that integrate with the existing architecture.
:::

#### 🏭 Asset Factory Pattern

1. **Create Asset Factory**: Define a factory function that creates your asset.

   ```python
   # assets/factories/my_domain/my_asset_factory.py
   from dagster import AssetKey, DynamicPartitionsDefinition, graph_asset

   def my_asset_factory(
       key: AssetKey,
       upstream_key: AssetKey,
       partitions: DynamicPartitionsDefinition,
   ) -> graph_asset:
       """Factory for creating my custom asset."""
       
       @graph_asset(
           key=key,
           partitions_def=partitions,
           ins={"input_data": AssetIn(key=upstream_key)},
           automation_condition=AutomationCondition.eager(),
       )
       def my_asset(input_data: MyInputType) -> MyOutputType:
           processed_data = process_my_data(input_data)
           return transform_my_data(processed_data)
       
       return my_asset
   ```

2. **Define Operations**: Create the processing operations.

   ```python
   # ops/my_domain/process_my_data.py
   from dagster import op, In, Out

   @op(
       required_resource_keys={"my_resource"},
       ins={"input_data": In(MyInputType)},
       out=Out(ProcessedType),
   )
   def process_my_data(context, input_data: MyInputType) -> ProcessedType:
       """Process input data using configured resources."""
       resource = context.resources.my_resource
       return resource.process(input_data)
   ```

3. **Create Resources**: Define necessary resources for your operations.

   ```python
   # resources/my_domain/MyResource.py
   from dagster import ConfigurableResource

   class MyResource(ConfigurableResource):
       endpoint: str
       api_key: str
       
       def process(self, data: MyInputType) -> ProcessedType:
           """Process data using external service."""
           pass
   ```

### 🧪 Step 3: Testing Pipeline Components

::: tip
Use Dagster's testing utilities to validate your pipeline components.
:::

#### 🧪 Unit Testing Operations

```python
# tests/ops/test_my_operations.py
from dagster import build_op_context
from aihub_pipeline.ops.my_domain.process_my_data import process_my_data


def test_process_my_data():
    """Test data processing operation."""
    context = build_op_context(
        resources={"my_resource": MyResource(endpoint="test", api_key="test")}
    )

    input_data = MyInputType(content="test data")
    result = process_my_data(context, input_data)

    assert result.processed_content == "processed: test data"
```

#### 🔗 Integration Testing Assets

```python
# tests/assets/test_my_assets.py
from dagster import materialize
from aihub_pipeline.assets.factories.my_domain.my_asset_factory import my_asset_factory


def test_my_asset():
    """Test asset materialization."""
    asset = my_asset_factory(
        key=AssetKey(["test", "my_asset"]),
        upstream_key=AssetKey(["test", "input"]),
        partitions=DynamicPartitionsDefinition(name="test_partitions"),
    )

    result = materialize(
        assets=[asset],
        partition_key="test_partition",
        resources={"my_resource": MyResource(endpoint="test", api_key="test")},
    )

    assert result.success
```

### 🔍 Step 4: Run and Debug the Pipeline

#### 🚀 Start the Dagster Development Server

```bash
# Run the playground example
make playground

# Or run manually
poetry run dagster dev -m playground --use-legacy-code-server-behavior
```

::: info Dagster Web Interface
This starts the Dagster web interface at `http://localhost:3002` where you can:

- View asset lineage and dependencies
- Materialize assets manually
- Monitor pipeline runs
- Debug failures and inspect outputs
:::

#### 🔄 Interactive Development Workflow

1. **Asset Materialization**: Click "Materialize" on individual assets to test them
2. **Pipeline Monitoring**: View real-time logs and execution progress
3. **Data Inspection**: Examine asset outputs and intermediate results
4. **Error Debugging**: Access detailed error logs and stack traces

### ✅ Step 5: Ensure Code Quality

::: warning
Before committing your changes, use the provided Makefile commands.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format      # Ruff formatting
make lint        # Ruff linting
make test        # Run tests
make test-cov    # Run tests with coverage
```

::: danger
All pipeline code must use strict Python type annotations and follow Dagster best practices. This is enforced by CI/CD.
:::

---

## 3. 🔧 Customization and Reuse

::: info
While the AI-Hub pipelines provide a robust foundation for data ingestion, each client project may have unique
requirements. The AI-Hub's architecture for customization and reuse ensures that developers can adapt pipelines to meet
varying needs without reinventing the wheel.
:::

### 🧩 Common Pipeline Assets

::: tip Ready-to-Use Assets
The AI-Hub includes a set of ready-to-use pipeline assets designed for frequent tasks:
:::

1. **Data Lake Observers**: Monitor a data lake for new or updated files
2. **Document Converters**: Convert raw files (PDF, Markdown, Word) into RefDocs with consistent metadata
3. **Node Chunkers**: Break down large documents into nodes suitable for embedding
4. **Embedders & Indexers**: Generate vector embeddings and insert them into vector stores or document databases

::: info Benefits of Reusable Assets
By using these predefined assets, developers compose existing building blocks to create client-specific workflows. This
accelerates development, reduces errors, and ensures consistency across projects.
:::

### 📈 Typical Data Ingestion Scenario

::: info Data Ingestion Flow
A typical data ingestion scenario demonstrates how observable assets and automation policies work together:
:::

1. **Detect Change**: A new Markdown file is uploaded to the data lake
2. **Observable Asset Triggers Run**: Dagster notices the change and triggers a pipeline run for that specific file (a
   dynamic partition)
3. **Document Conversion**: The pipeline converts the file into a RefDoc, adding metadata and storing it in the document
   store
4. **Chunking & Embedding**: The pipeline splits the RefDoc into nodes, embeds them into vector form, and inserts those
   embeddings into the vector database
5. **Agent-Ready Data**: When an agent receives a user query requiring that document, it can semantically retrieve the
   relevant chunks, confident that the data is up-to-date and well-structured

::: tip Pipeline Benefits
This approach ensures that data ingestion pipelines reduce manual effort, maintain higher data quality, and create a
more reliable end-to-end AI solution that adapts gracefully as client needs and data environments evolve.
:::

---

## 4. 🎨 Pipeline Patterns and Best Practices

This section covers common patterns and best practices for building robust data processing pipelines.

### 🏭 Asset Factory Patterns

#### 🔄 Dynamic Asset Creation

::: tip
Use asset factories to create configurable, reusable asset definitions:
:::

```python
def document_processing_factory(
        namespace: str,
        source_key: AssetKey,
        config: ProcessingConfig,
) -> list[graph_asset]:
    """Create a complete document processing pipeline."""

    partitions = DynamicPartitionsDefinition(name=f"{namespace}_partitions")

    # Create assets with namespace prefixes
    documents = documents_factory(
        key=AssetKey([namespace, "documents"]),
        data_lake_key=source_key,
        partitions=partitions,
    )

    nodes = nodes_factory(
        key=AssetKey([namespace, "nodes"]),
        document_key=AssetKey([namespace, "documents"]),
        partitions=partitions,
    )

    return [documents, nodes]
```

### 🎛️ Resource Management Patterns

#### 🏭 Resource Factory Pattern

::: tip
Create resource factories for different environments:
:::

```python
def development_resources() -> dict[str, ConfigurableResource]:
    """Development environment resources."""
    return {
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name="dev_store",
            namespace_name="dev",
        ),
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.DOCLING,
        ),
    }


def production_resources() -> dict[str, ConfigurableResource]:
    """Production environment resources."""
    return {
        **mongo_aisearch_storage_context_resources(
            store_name="prod_store",
            namespace_name="production",
        ),
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.DOCLING,
            timeout=300,
        ),
    }
```

### 👁️ Monitoring and Observability Patterns

#### 📊 Custom Metadata and Logging

```python
@op
def documented_operation(context, input_data: InputType) -> OutputType:
    """Operation with comprehensive logging and metadata."""
    context.log.info(f"Processing {len(input_data)} items")

    result = process_data(input_data)

    # Add metadata for monitoring
    context.add_output_metadata(
        metadata={
            "items_processed": len(input_data),
            "processing_time": result.processing_time,
            "quality_score": result.quality_score,
        }
    )

    return result
```

### 📖 Glossary of Pipeline-Specific Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_pipeline` scope,
building upon the core AI-Hub terminology.

| Term                   | Definition                                                                                                                                                                |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Asset**              | A Dagster concept representing a data object or file that is produced by a pipeline. Assets can be materialized (computed) and have dependencies on other assets.         |
| **Asset Factory**      | A function that creates and configures Dagster assets with specific parameters, enabling reusable asset definitions across different pipeline configurations.             |
| **Data Lake File**     | A structured representation of a document stored in Azure Data Lake, containing content, metadata, and URI information for downstream processing.                         |
| **Dagster**            | The core orchestration framework used for building and managing data pipelines. Provides scheduling, monitoring, and dependency management capabilities.                  |
| **Document Parser**    | A resource that extracts text content and metadata from various document formats (PDF, Word, PowerPoint, etc.) using different parsing strategies.                        |
| **Dynamic Partitions** | Dagster's mechanism for handling datasets where the partition keys are determined at runtime, allowing flexible processing of varying document sets.                      |
| **Embedding Model**    | AI model resource that converts text content into high-dimensional vector representations for semantic search and retrieval applications.                                 |
| **Graph Asset**        | A Dagster asset composed of multiple operations (ops) that work together to transform input data into output data through a defined workflow.                             |
| **I/O Manager**        | Dagster resource responsible for storing and retrieving assets from specific storage systems (Azure Data Lake, MongoDB, Milvus, etc.).                                    |
| **Job Definition**     | A Dagster construct that defines a selection of assets to materialize, along with their execution configuration and resource requirements.                                |
| **Language Model**     | LLM resource used for generating summaries, descriptions, and other text-based processing tasks within the pipeline.                                                      |
| **Node**               | A processed chunk of a document that has been parsed, embedded, and prepared for storage in a vector database for retrieval operations.                                   |
| **Observable Asset**   | A Dagster asset that monitors external systems for changes and reports new partitions, triggering downstream processing when new data is available.                       |
| **Operation (Op)**     | A Dagster concept representing a single unit of computation that takes inputs and produces outputs, forming the building blocks of pipeline workflows.                    |
| **Partition**          | A subset of data that can be processed independently, typically representing individual documents or time-based slices of data.                                           |
| **Pipeline**           | A complete data processing workflow that transforms source data through multiple stages to produce final outputs, typically from document ingestion to vector embeddings. |
| **RefDoc**             | A reference document that serves as the authoritative source for a particular piece of content, stored in the document store with associated metadata.                    |
| **Resource**           | A Dagster concept for managing external dependencies and configurations (databases, APIs, models) that are shared across multiple operations.                             |
| **Run Config**         | Configuration object that specifies how a particular pipeline run should be executed, including resource configurations and parameter values.                             |
| **Sensor**             | A Dagster component that monitors external systems or schedules and triggers pipeline runs based on specific conditions or time intervals.                                |
| **Share Point File**   | A document retrieved from Microsoft SharePoint, containing raw content and metadata that serves as input for the data processing pipeline.                                |
| **Summary Node**       | A processed document chunk that contains summarized information, created using recursive summarization techniques for better context preservation.                        |
| **Vector Store**       | A database optimized for storing and searching high-dimensional vectors, supporting similarity search operations for RAG applications.                                    |
