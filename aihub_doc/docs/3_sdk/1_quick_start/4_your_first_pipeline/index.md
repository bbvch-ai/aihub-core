---
title: "Your First Pipeline"
index: 4
---

# Your First Pipeline

Build your first data processing pipeline using the AI-Hub Pipeline (`aihub_pipeline`) SDK.

## What you'll learn

This quickstart covers pipeline basics:
- **Assets**: Data entities that depend on each other
- **Dependencies**: How data flows between assets
- **Execution**: Running pipelines locally with Dagster UI

## Prerequisites

You need the AI-Hub development environment running. Before you start, make sure you completed the [Development Environment Setup](/3_sdk/1_dev_environment_setup/) steps.

## How pipelines work

Pipelines are **data processing workflows** that transform data through connected steps:
- **Assets**: Functions that create or transform data
- **Dependencies**: Assets can depend on outputs from other assets
- **Execution**: Dagster runs assets in the right order automatically

## Create your first pipeline

Let's build a simple pipeline with 2 assets that process text data.

### Create your assets (`assets.py`)

::: code-group
```python
from dagster import asset, AssetExecutionContext

@asset(description="Raw text data")
def hello_data(context: AssetExecutionContext) -> str:
    message = "Hello from my first pipeline!"
    context.log.info(f"Created: {message}")
    return message

@asset(description="Processed text with word count")  
def processed_data(context: AssetExecutionContext, hello_data: str) -> str:
    # Simple processing: count words and make uppercase
    words = hello_data.split()
    processed = hello_data.upper()
    result = f"{processed} (Word count: {len(words)})"
    
    context.log.info(f"Processed: {result}")
    return result

```
:::

### Create your pipeline definition (`my_pipeline.py`):

::: code-group
```python
from dagster import Definitions

from assets import hello_data, processed_data


# Pipeline definition
defs = Definitions(
    assets=[hello_data, processed_data]
)
```
:::

That's it! This simple pipeline:
- **hello_data**: Creates a text message
- **processed_data**: Takes the message, makes it uppercase, and adds word count

## Run your pipeline

### 1. Start the Dagster UI:

```bash
dagster dev -m my_pipeline
```

Open `http://localhost:3000` to see:
- **Asset lineage graph**: hello_data → processed_data
- **Materialize buttons** to run individual assets or the whole pipeline
- **Asset details** showing inputs, outputs, and logs

### 2. Run in Dagster UI:

1. Click **"Assets"** in the left sidebar
2. Select both assets or click on **processed_data**
3. Click **"Materialize selected"** 
4. Watch the execution progress and see the results

## Understanding the data flow

Your pipeline demonstrates:

1. **Asset dependencies**: `processed_data` automatically gets the output from `hello_data`
2. **Automatic execution order**: Dagster runs `hello_data` first, then `processed_data`
3. **Data passing**: The return value from one asset becomes input to the next

## What you learned

- **Asset basics**: Creating assets with `@asset` decorator
- **Dependencies**: How assets automatically depend on each other
- **Pipeline execution**: Running assets programmatically and via UI
- **Data flow**: How data passes between connected assets

## Next steps

- [Building Pipelines](/3_sdk/3_building_pipelines/) - Learn more advanced patterns
- Explore the Dagster UI to understand asset management
- Try modifying the pipeline to add more processing steps