---
title: Your First Pipeline
---

# Your First Pipeline

Build your first data processing pipeline using the Swiss AI Hub Pipeline (`aihub_pipeline`) SDK - a complete data
transformation pipeline with multiple connected assets.

## What you'll learn

This quickstart covers the essential building blocks:

- **Asset structure**: How pipelines process data through connected assets
- **Data flow**: How data flows between assets automatically
- **Configuration**: Settings and resources that control pipeline behavior
- **Testing**: Running your pipeline locally and in Dagster UI
- **Observability**: Monitoring pipeline execution with built-in tools

## Prerequisites

You need the Swiss AI Hub development environment running. Before you start, make sure you completed the
[Development Environment Setup](../1_dev_environment_setup/) steps.

## How pipelines work

Swiss AI Hub pipelines are **data processing workflows** built on Dagster with three essential parts:

- **Assets**: Functions that create, transform, or consume data
- **Dependencies**: Automatic data flow between assets based on function parameters
- **Resources**: Shared configuration and services to external systems

## Create your first pipeline

Let's build a data pipeline that processes user feedback data.

### Start with a simple pipeline

First, let's understand pipeline basics with a minimal example:

#### 1. Create your basic assets (`simple_pipeline.py`):

```python
from dagster import AssetExecutionContext, Output, asset


@asset(description="Raw text data source")
def raw_feedback_data(context: AssetExecutionContext) -> Output[str]:
    """Source asset that provides raw user feedback data."""
    feedback = "The product is amazing but the documentation could be better!"
    context.log.info(f"Loaded raw feedback: {feedback}")
    return Output(feedback, metadata={"feedback": feedback})


@asset(description="Cleaned and processed feedback")
def cleaned_feedback(context: AssetExecutionContext, raw_feedback_data: str) -> Output[dict]:
    """Transform raw feedback into structured data."""
    # Simple processing: clean text and extract basic metrics
    text = raw_feedback_data.strip().lower()
    words = text.split()

    processed = {
        "original_text": raw_feedback_data,
        "cleaned_text": text,
        "word_count": len(words),
        "sentiment": "positive" if "amazing" in text else "neutral",
    }

    context.log.info(f"Processed feedback: {processed}")
    return Output(
        processed,
        metadata={
            "original_text": processed["original_text"],
            "cleaned_text": processed["cleaned_text"],
            "word_count": processed["word_count"],
            "sentiment": processed["sentiment"],
        },
    )



```

#### 2. Add the pipeline definition (`simple_pipeline.py`):

```python
from dagster import Definitions

## ... your asset definitions from above ...

# Basic pipeline definition
defs = Definitions(assets=[raw_feedback_data, cleaned_feedback])
```

#### 3. Run your basic pipeline:

```bash
uv run dagster dev -f simple_pipeline.py
```

Open `http://localhost:3000` and you'll see:

- **Asset lineage graph**: raw_feedback_data → cleaned_feedback
- **Materialize buttons** to execute assets
- **Asset details** showing inputs, outputs, and execution logs

Click **"Materialize all"** to run the pipeline and see the data flow!

## Build a real Swiss AI Hub pipeline

Now let's create a realistic pipeline using the `aihub_pipeline` SDK that demonstrates document processing patterns.
We'll break this down step by step to understand each component.

### 1. Understanding Swiss AI Hub Pipeline Structure

Swiss AI Hub pipelines follow these key patterns:

- **Asset Factories**: Reusable functions that create configured assets
- **Resources**: Configured services like parsers, stores, and embedding models
- **Dynamic Partitions**: Each document becomes a separate partition for parallel processing

### 2. Set up your pipeline configuration

Start by creating the basic configuration and imports (`my_document_pipeline.py`):

```python
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from dagster import AssetKey, AssetSelection, Definitions, DynamicPartitionsDefinition

# Import Swiss AI Hub pipeline factories
from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)

# Import Swiss AI Hub resources and utilities
from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

# Pipeline configuration - defines where data flows between assets
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])      # Raw file storage 
DOCUMENT_KEY = AssetKey(["playground", "documents"])       # Parsed documents
NODES_KEY = AssetKey(["playground", "nodes"])              # Document chunks with embeddings

# Storage configuration
CONTAINER_NAME = "playground"    # S3 bucket/container name
DIRECTORY_NAME = "documents"     # Folder for documents
NAMESPACE_NAME = DIRECTORY_NAME  # Vector store namespace
STORE_NAME = CONTAINER_NAME      # Document store name

# Dynamic partitions allow parallel processing of individual documents
document_partitions = DynamicPartitionsDefinition(name="document_partitions")
```

### 3. Create your pipeline assets

Next, create the three main assets that form your processing pipeline:

```python
# Create the pipeline assets using Swiss AI Hub factories

# 1. Observable Data Lake - watches for new/changed files
observable_asset = observable_data_lake_factory(
    asset_key=DATA_LAKE_KEY, 
    partitions=document_partitions
)

# 2. Documents Asset - processes raw files into structured documents
documents_asset = documents_factory(
    asset_key=DOCUMENT_KEY,
    data_lake_key=DATA_LAKE_KEY,    # Depends on data lake 
    partitions=document_partitions   # One partition per document
)

# 3. Nodes Asset - chunks documents and creates embeddings
nodes_asset = nodes_factory(
    asset_key=NODES_KEY,
    document_key=DOCUMENT_KEY,       # Depends on documents
    partitions=document_partitions   # One partition per document
)

# Combine all assets
assets = [observable_asset, documents_asset, nodes_asset]
```

**Understanding the asset factories:**

- `observable_data_lake_factory`: Creates an asset that monitors file changes
- `documents_factory`: Creates an asset that parses files into RefDoc objects with metadata
- `nodes_factory`: Creates an asset that chunks documents and generates vector embeddings

### 4. Configure your pipeline resources

Now configure the resources (services) your pipeline needs:

```python
# Resource configuration - split into logical groups for clarity

# A. Storage and I/O Resources
storage_resources = {
    # Data lake I/O managers for S3-compatible storage
    **default_io_manager_s3_datalake_resources(
        container_name=CONTAINER_NAME, 
        directory_name=DIRECTORY_NAME
    ),
    
    # Data lake resources for file management
    **s3_data_lake_resources(
        container_name=CONTAINER_NAME,
        directory_name=DIRECTORY_NAME,
        figures_directory_name="__figures__",  # For extracted images/figures
    ),
}

# B. Document Processing Resources  
processing_resources = {
    # Document parser - uses AI-powered MinerU for PDF/Word/etc
    "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),

    # Node parser - chunks documents using structural elements
    "node_parser": MarkdownStructuralNodeParserResource(),
}

# C. Database and Search Resources
database_resources = {
    # Vector store and document store (MongoDB + Milvus)
    **local_mongo_milvus_storage_context_resource(
        vector_store_uri="http://localhost:19530",  # Milvus connection
        store_name=STORE_NAME,
        namespace_name=NAMESPACE_NAME,
    ),
}

# D. AI Model Resources
ai_resources = {
    # Embedding model for creating vector representations
    "embedding_model": EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(
            model_name="azure/text-embedding-3-large"
        ),
    ),
}

# Combine all resources
all_resources = {
    **storage_resources,
    **processing_resources, 
    **database_resources,
    **ai_resources,
}
```

### 5. Define your complete pipeline

Finally, bring everything together in the pipeline definition:

```python
# Define the complete pipeline
defs = Definitions(
    assets=assets,           # The three processing assets
    resources=all_resources, # All configured services
)
```

**Complete pipeline file** (`my_document_pipeline.py`):

Here's the complete file with all components together:

```python
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from dagster import AssetKey, Definitions, DynamicPartitionsDefinition

from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)

from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource

# Configuration
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])  
NODES_KEY = AssetKey(["playground", "nodes"])

CONTAINER_NAME = "playground"
DIRECTORY_NAME = "documents" 
NAMESPACE_NAME = DIRECTORY_NAME
STORE_NAME = CONTAINER_NAME

document_partitions = DynamicPartitionsDefinition(name="document_partitions")

# Assets
observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
documents_asset = documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions)
nodes_asset = nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions)

assets = [observable_asset, documents_asset, nodes_asset]

# Resources
defs = Definitions(
    assets=assets,
    resources={
        **default_io_manager_s3_datalake_resources(CONTAINER_NAME, DIRECTORY_NAME),
        **s3_data_lake_resources(CONTAINER_NAME, DIRECTORY_NAME, "__figures__"),
        **local_mongo_milvus_storage_context_resource("http://localhost:19530", STORE_NAME, NAMESPACE_NAME),
        "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),
        "node_parser": MarkdownStructuralNodeParserResource(),
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(model_name="azure/text-embedding-3-large")
        ),
    },
)
```

### 6. Run your Swiss AI Hub pipeline:

```bash
uv run dagster dev -f my_document_pipeline.py
```

You'll see the complete document processing pipeline:

```
data_lake (observable) → documents → nodes
                            ↓          ↓
                       (DocStore)  (VectorStore)
```

### 7. Understanding the data flow:

1. **Observable Data Lake**: Monitors for new PDF, Word, Markdown, etc. files
2. **Documents**: Parses files using AI-powered document intelligence (MinerU)
3. **Nodes**: Chunks documents using structural parsing and generates embeddings

### 8. Add jobs and scheduling to your pipeline

For production pipelines, you'll want to add jobs and scheduling. Let's extend the pipeline:

```python
# Add these imports to my_document_pipeline.py
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor

# Create jobs for different operations
observe_job = observe_source_job(
    observable_asset=observable_asset,
    namespace_name=NAMESPACE_NAME,
)

# Update your pipeline definition to include jobs and schedules
defs = Definitions(
    assets=assets,
    resources={
        # ... your existing resources ...
    },
    
    # Add jobs for pipeline operations
    jobs=[observe_job],
    
    # Add scheduling - observe daily at midnight
    schedules=[daily_schedule_at(observe_job, hour=0, minute=0)],
    
    # Add sensors for automation
    sensors=[default_automation_sensor(assets)],
)
```

**Understanding jobs and scheduling:**

- **observe_job**: Manually trigger observation of the data lake
- **daily_schedule_at**: Schedule automatic data lake observation
- **default_automation_sensor**: Automatically trigger asset processing when dependencies change

Your pipeline now supports:

- **Manual execution**: Materialize individual assets in Dagster UI
- **Scheduled observation**: Daily checks for new documents
- **Automatic processing**: Assets process automatically when upstream changes detected

### 9. Monitor with Swiss AI Hub observability tools:

- **Dagster UI** (`http://localhost:3000`): Asset lineage, execution logs, and materialization history
- **MongoDB Compass**: Document store inspection
- **Milvus (Attu)**: Vector database monitoring

::: tip SeaweedFS Filer
In production, the SeaweedFS Filer web UI is accessible at `datalake.${DOMAIN}` (OAuth2 protected, requires
AIHubDeveloper role). In development mode, it's available at `http://localhost:8889` for browsing uploaded files and
debugging storage.
:::

### 10. Understanding Swiss AI Hub pipeline patterns

Your Swiss AI Hub pipeline demonstrates key patterns:

1. **Observable Assets**: Automatically detect new documents without manual intervention
2. **Dynamic Partitions**: Each document is processed independently
3. **Resource Management**: Configurable parsers, models, and storage backends
4. **Automation Policies**: Eager processing when upstream assets change

## What you learned

- **Swiss AI Hub SDK Usage**: Using factories, resources, and typed data objects from `aihub_pipeline`
- **Document Processing Pipeline**: Complete flow from raw files to searchable embeddings
- **Asset Factory Usage**: Using existing factories like `documents_factory` and `nodes_factory`
- **Resource Configuration**: Setting up parsers, LLMs, and storage systems
- **Observability**: Monitoring AI-powered pipelines with Dagster
- **Production Readiness**: Scalable, automated, and maintainable pipeline architecture

## Next steps

- [Building Pipelines](../../3_building_pipelines/) - Learn advanced Swiss AI Hub pipeline patterns
