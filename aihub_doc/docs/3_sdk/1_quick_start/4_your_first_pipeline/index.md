---
title: "Your First Pipeline"
index: 4
---

# Your First Pipeline

Build your first data processing pipeline using the AI-Hub Pipeline SDK - a simple text processor that reads files, transforms them, and produces outputs.

## What you'll learn

This quickstart covers pipeline essentials:
- **Assets**: Data objects created and managed by the pipeline
- **Operations**: Functions that transform data between assets  
- **Resources**: Configurations for external services
- **Execution**: Running pipelines locally with Dagster UI

## Prerequisites

You need the AI-Hub development environment running. Before you start, make sure you completed the [Development Environment Setup](/3_sdk/1_dev_environment_setup/) steps.

## How pipelines work

AI-Hub pipelines are **data processing workflows** built on Dagster with:
- **Assets**: Data entities that get created and updated (files, processed data, reports)
- **Operations**: Functions that transform data between assets
- **Resources**: Shared services and configurations

## Create your first pipeline

Let's build a simple pipeline with just 2 assets that demonstrate the basic concept: one asset creates data, another uses it.

### Create Assets (`my_pipeline.py`):

```python
from dagster import asset, AssetIn, Definitions

@asset
def hello_asset():
    """First asset that creates some data."""
    message = "Hello from first asset!"
    print(f"Creating: {message}")
    return message

@asset(ins={"hello_asset": AssetIn()})
def world_asset(hello_asset: str):
    """Second asset that depends on the first asset."""
    response = f"{hello_asset} World from second asset!"
    print(f"Processing: {response}")
    return response

# Define your pipeline with both assets
defs = Definitions(
    assets=[hello_asset, world_asset]
)
```

That's it! This simple pipeline shows:
- **hello_asset**: Creates a message (no dependencies)
- **world_asset**: Takes the message and extends it (depends on hello_asset)

## Run your pipeline

### 1. Test the pipeline programmatically:

Add this test code to your file:
```python
if __name__ == "__main__":
    from dagster import materialize
    
    # Run both assets
    result = materialize([hello_asset, world_asset])
    
    print("Pipeline completed!")
    print(f"Final result: {result.asset_value(world_asset)}")
```

Run it:
```bash
python my_pipeline.py
```

Expected output:
```
Creating: Hello from first asset!
Processing: Hello from first asset! World from second asset!
Pipeline completed!
Final result: Hello from first asset! World from second asset!
```

### 2. Start the Dagster UI:

Start the Dagster development server to visualize your pipeline:
```bash
dagster dev -m my_pipeline
```

Open `http://localhost:3000` to see:
- **Asset lineage graph** showing: hello_asset → world_asset  
- **Materialize buttons** to run individual assets
- **Logs and execution details** for each asset
- **Asset values** to inspect the data

### 3. Run in the Dagster UI:

1. Click on **"Assets"** in the left sidebar
2. Select both assets (hello_asset, world_asset)
3. Click **"Materialize selected"** to run the pipeline
4. Watch the execution and see the outputs

## Understanding the data flow

Your pipeline follows this simple flow:
1. **hello_asset** → Creates a message 
2. **world_asset** → Receives the message and extends it

Each asset:
- Returns typed data that flows to dependent assets
- Can be run independently or together
- Has clear dependencies that Dagster manages automatically

## What you learned

- **Asset-based modeling**: Data entities with clear dependencies
- **Data lineage**: How data flows through processing stages
- **Pipeline execution**: Running locally and via Dagster UI  
- **Debugging**: Inspecting asset values and execution logs

## Next steps

- [Building Pipelines](/3_sdk/3_building_pipelines/)