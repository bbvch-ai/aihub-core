<div align="center">

# swiss-ai-hub-pipeline

**The data-ingestion SDK for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — turn documents into RAG-ready
vectors with [Dagster](https://dagster.io/).**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-pipeline?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-pipeline/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-pipeline?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-pipeline/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/pipeline/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers — LLM gateway (LiteLLM), vector search (Milvus), document parsing
(MinerU), S3 storage (SeaweedFS), SSO (Keycloak), observability (Langfuse), a chat UI (Open-WebUI), and more. Agents
answer questions over your organization's knowledge; **this package is how that knowledge gets in.**

## What is this package?

`swiss-ai-hub-pipeline` is a [Dagster](https://dagster.io/)-based SDK that ingests documents and produces the vectors
RAG agents search. It implements a **two-stage, asset-based pipeline**:

1. **Source → data lake** — monitor a source (SharePoint, OneDrive, Google Drive, S3, local/network shares — anything
   [rclone](https://rclone.org/) supports) and sync changed files into the platform's S3 (SeaweedFS).
2. **Data lake → vector store** — parse each file (MinerU OCR + structure), chunk it, embed it via the LLM gateway, and
   upsert the vectors into Milvus, with full lineage from every embedding back to its source document.

You compose a pipeline from one function, `default_definitions()`, which wires together all the assets, resources, IO
managers, sensors, jobs, and schedules. It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/)
(installed automatically); RAG agents from [`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/) query
its output.

## Should you use this package?

**Probably not directly — most deployments use the pre-built pipeline images.** `rag_pipeline` ingests every knowledge
database users create from the UI, with no redeploy; the legacy `default_rag_pipeline` and `shared_rag_pipeline` still
serve the platform's two built-in buckets.

**Use this PyPI package when you want a custom pipeline** — connect a new data source, ingest into a different bucket,
or tune parsing/chunking/embedding for your documents. It's an SDK for building your own ingestion as a Dagster
[code location](https://docs.dagster.io/concepts/code-locations).

## Installation

```bash
pip install swiss-ai-hub-pipeline
# or
uv add swiss-ai-hub-pipeline
```

Requires **Python 3.13**.

______________________________________________________________________

## Quick start

A pipeline is a Dagster **code location** — a module that exposes a `Definitions` object. `default_definitions()` builds
a complete one:

```python
# my_pipeline/__init__.py
from swiss_ai_hub.pipeline import default_definitions

defs = default_definitions(
    datalake_container_name="my_docs",                  # S3 bucket (Dagster name: letters, digits, underscores)
    embedding_model_name="embedding/bge-m3",            # any embedding model on the LiteLLM gateway
    llm_model_name="text-generation/gemma-4-31B-it",    # for summaries / table & figure refinement
    with_summary_nodes=True,                            # hierarchical RAG summaries
)
```

Run it with the Dagster UI and materialize the assets:

```bash
dagster dev -m my_pipeline      # opens http://localhost:3000
```

Drop a document into the `my_docs` bucket, click **Materialize** on the asset graph, and watch it flow:
`observe → documents (parse) → nodes (chunk + embed) → Milvus`. A RAG agent pointed at that bucket can now answer
questions over it.

To also pull from an external source, combine `default_definitions()` with a Stage-1 builder — e.g.
`default_rclone_to_datalake_definitions(...)` for OneDrive/Google Drive/Dropbox, or
`default_sharepoint_to_datalake_definitions(...)`. The
[source templates](https://github.com/bbvch-ai/aihub-core/tree/main/packages/pipeline/templates/sources) (SharePoint,
OneDrive, S3, Azure Blob, Google Drive, SFTP, local FS) are copy-paste starting points.

______________________________________________________________________

## How it works

`default_definitions()` assembles a graph of Dagster **assets** connected by **IO managers** to the platform's stores:

| Stage                    | Assets                                                                             | Backed by                        |
| ------------------------ | ---------------------------------------------------------------------------------- | -------------------------------- |
| Source → data lake       | `observable_*`, `data_lake_file`, `removed_data_lake_files`                        | SeaweedFS (S3)                   |
| Data lake → vector store | `documents` (parse), `nodes` (chunk + embed), `summary_nodes`, `removed_documents` | MinerU, LiteLLM, MongoDB, Milvus |

Materialization is driven by eager automation, daily schedules, and a NATS sensor that fires when documents are uploaded
through the API — so ingestion keeps up with changes without manual runs. Key `default_definitions()` knobs:
`with_summary_nodes`, `with_table_refinement`, `with_figure_descriptions`, `document_parser_loader_type` (MinerU or
Document Intelligence), and `max_partitions`.

______________________________________________________________________

## Development

The dev stack runs the infrastructure a pipeline needs — SeaweedFS (S3), MongoDB, Milvus, MinerU, and the LiteLLM
gateway — and exposes it on `localhost`:

```bash
# 1. Start the platform infrastructure (from a Swiss AI Hub checkout)
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# 2. Load the dev connection settings into your shell
set -a && source .env && set +a

# 3. Run your pipeline's Dagster UI against the stack
dagster dev -m my_pipeline       # http://localhost:3000
```

Materialize assets from the UI to parse, embed, and store real documents. `dagster definitions validate -m my_pipeline`
loads the whole code location (every asset, resource, and IO manager) without running it — handy as a fast sanity check
and in CI.

> **Settings are not auto-loaded from the environment.** The SDK reads connection settings only when constructed, so
> make sure the variables above are exported in the process that runs Dagster (`set -a && source .env && set +a`).

## Production

In production a pipeline runs as a **Dagster code location**: a gRPC server in a container that the platform's Dagster
webserver and daemon connect to.

**1. Containerize it** as a gRPC code-location server:

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./        # your project, depending on swiss-ai-hub-pipeline
RUN uv sync --frozen --no-dev
COPY . .

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 4000
ENTRYPOINT ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-m", "my_pipeline"]
```

**2. Run it alongside the platform on the right networks** — a pipeline reaches MinerU + LiteLLM (**`backend`**),
MongoDB + Milvus + NATS (**`data`**), and SeaweedFS/S3 (**`storage`**):

```yaml
# docker-compose.my-pipeline.yml — deployed alongside the platform
services:
  my-pipeline:
    image: registry.example.com/my-pipeline:1.0.0
    restart: always
    environment:
      MONGO_CONNECTION_STRING: mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@ferretdb:27017/
      MILVUS_URL: http://milvus-standalone:19530
      S3_STORAGE_ENDPOINT: http://seaweedfs-s3:9000
      S3_STORAGE_ACCESS_KEY: ${S3_STORAGE_ACCESS_KEY}
      S3_STORAGE_SECRET_KEY: ${S3_STORAGE_SECRET_KEY}
      LITE_LLM_PROXY_BASE_URL: http://litellm:4000
      LITE_LLM_PROXY_API_KEY: ${LITELLM_MASTER_KEY}
      MINERU_API_BASE_URL: http://mineru-api:8000
      NATS_ENDPOINT: nats://nats:4222
      NATS_TOKEN: ${NATS_TOKEN}
    networks: [backend, data, storage]

networks:
  backend: { external: true }
  data: { external: true }
  storage: { external: true }
```

**3. Register it in the platform's Dagster workspace** so the webserver/daemon load it:

```yaml
# workspace.yaml
load_from:
  - grpc_server:
      host: my-pipeline      # the service name above
      port: 4000
      location_name: my-pipeline
```

```bash
docker compose -f docker-compose.my-pipeline.yml up -d
```

Reuse the platform's secrets (from its `.env`) for the `${…}` values, and match the actual network names of your
deployment. Your pipeline then shows up as a code location in the platform's Dagster UI, with its schedules and sensors
running under the shared daemon.

> **Network reference.** `backend` = LiteLLM, MinerU, OTEL. `data` = NATS, FerretDB, Milvus. `storage` = SeaweedFS/S3.

______________________________________________________________________

## Making a custom pipeline selectable in the UI

Deploying a pipeline is not enough for a user to create a knowledge database for it from the admin UI — the API must
know the pipeline exists. Two pieces connect a custom pipeline to self-service database creation:

**1. Own the databases you ingest.** Build your Stage 2 with `rag_pipeline_definitions(ingestor="acme_rag", …)` — the
route-per-run RAG pipeline. Its sensors and schedule claim every knowledge database whose `ingestor` equals that string,
so the id you pass here is the routing key.

**2. Register it so users can pick it.** Contribute an `Ingestor` (the same `id`, plus localized labels) to the core
`IngestorRegistry` via a `swiss_ai_hub.ingestors` entry point in your package:

```python
# acme_pipeline/ingestors.py
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import Ingestor

acme_rag = Ingestor(
    id="acme_rag",  # must equal the ingestor passed to rag_pipeline_definitions
    display_name=LocaleString(en="Acme RAG", de="Acme RAG", fr="Acme RAG", it="Acme RAG"),
    description=LocaleString(en="Acme's OCR-heavy ingestion pipeline"),
)
```

```toml
# pyproject.toml
[project.entry-points."swiss_ai_hub.ingestors"]
acme_rag = "acme_pipeline.ingestors:acme_rag"
```

Install that package into the platform's API image. The API auto-discovers the entry point, `GET /knowledge/ingestors`
then offers "Acme RAG" in the create-database dialog, and `create_database` accepts it — with **no** change to the
platform's `IngestorType` enum, API contract, or generated SDK. (A deployment that builds its own API from the
`swiss-ai-hub-api` SDK can instead call `IngestorRegistry.register(acme_rag)` at startup.) See ADR
`2026_06_18_rag_pipeline_route_per_run` for the rationale, including why the `ingestor` field is a plain string at the
API boundary.

______________________________________________________________________

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/
- **Source templates**:
  [`packages/pipeline/templates/sources`](https://github.com/bbvch-ai/aihub-core/tree/main/packages/pipeline/templates/sources)
- **The full SDK** (meta package): https://pypi.org/project/swiss-ai-hub/

## License

Apache-2.0 — see
[packages/pipeline/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/pipeline/LICENSE). For the full
per-package license matrix, see [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
