# Swiss AI Hub Pipeline

Data ingestion and processing SDK for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform. A
Dagster-based, asset-oriented framework that turns documents into RAG-ready vectors.

- **Two-stage architecture** — source-specific ingestion (SharePoint, OneDrive, S3, local FS via rclone) into an
  S3-compatible data lake, then a unified parse → chunk → embed → store pipeline into Milvus and MongoDB.
- **Factory pattern** — compose pipelines from asset factories, resources, IO managers, and sensors.
- **Lineage** — every vector embedding traces back to its source document.

## Installation

```bash
pip install swiss-ai-hub-pipeline
```

This pulls in [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/).

## Usage

```python
from swiss_ai_hub.pipeline import default_definitions
```

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
