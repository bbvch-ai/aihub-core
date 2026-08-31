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

You compose a pipeline from one function, `document_ingestion_pipeline_definitions()`, which wires together all the assets, resources,
IO managers, sensors, jobs, and schedules. It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/)
(installed automatically); RAG agents from [`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/) query
its output.

## Should you use this package?

**Probably not directly — most deployments use the pre-built `document_ingestion_pipeline` image**, which ingests every knowledge
database users create from the UI, with no redeploy.

**Use this PyPI package when you want a custom pipeline** — connect a new data source, or tune
parsing/chunking/embedding for your documents. It's an SDK for building your own ingestion as a Dagster
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

A pipeline is a Dagster **code location** — a module that exposes a `Definitions` object.
`document_ingestion_pipeline_definitions()` builds a complete one:

```python
# my_pipeline/__init__.py
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.pipeline.util import document_ingestion_pipeline_definitions

defs = document_ingestion_pipeline_definitions(
    ingestor="my_rag",                                  # this pipeline owns every database assigned to it
    display_name=LocaleString(en="My RAG"),             # how users see it when creating a database
    description=LocaleString(en="Tuned for my documents"),
    embedding_model_name="embedding/bge-m3",            # any embedding model on the LiteLLM gateway
    llm_model_name="text-generation/gemma-4-31B-it",    # for summaries / table & figure refinement
    with_summary_nodes=True,                            # hierarchical RAG summaries
)
```

The pipeline carries no bucket name: it serves every knowledge database whose `ingestor` matches, resolving the target
per run. Create one from the admin UI, picking "My RAG" as the ingestor — no redeploy, no new code location.

Run it with the Dagster UI and materialize the assets:

```bash
dagster dev -m my_pipeline      # opens http://localhost:3000
```

Upload a document to that database, and watch it flow:
`observe → documents (parse) → nodes (chunk + embed) → Milvus`. A RAG agent pointed at it can now answer questions over
it.

To also pull from an external source, combine it with a Stage-1 builder — e.g.
`default_rclone_to_datalake_definitions(...)` for OneDrive/Google Drive/Dropbox, or
`default_sharepoint_to_datalake_definitions(...)`. The
[source templates](https://github.com/bbvch-ai/aihub-core/tree/main/packages/pipeline/templates/sources) (SharePoint,
OneDrive, S3, Azure Blob, Google Drive, SFTP, local FS) are copy-paste starting points.

______________________________________________________________________

## How it works

`document_ingestion_pipeline_definitions()` assembles a graph of Dagster **assets** connected by **IO managers** to the platform's
stores:

| Stage                    | Assets                                                                             | Backed by                        |
| ------------------------ | ---------------------------------------------------------------------------------- | -------------------------------- |
| Source → data lake       | `observable_*`, `data_lake_file`, `removed_data_lake_files`                        | SeaweedFS (S3)                   |
| Data lake → vector store | `documents` (parse), `nodes` (chunk + embed), `summary_nodes`, `removed_documents` | MinerU, LiteLLM, MongoDB, Milvus |

A document is reported as ingested only once `nodes` has written its embeddings to Milvus — a parsed document has
markdown but is not yet retrievable, so it stays pending until then.

Materialization is driven by eager automation, daily schedules, and a NATS sensor that fires when documents are uploaded
through the API — so ingestion keeps up with changes without manual runs. Key `document_ingestion_pipeline_definitions()` knobs:
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

### Make targets

`make playground`, `make quickstart`, and `make document-ingestion-pipeline` wrap the three steps above: they source the repo-root
`.env` and install `dagster.local.yaml` into `$DAGSTER_HOME` (`~/.dagster_home` unless you export something else) as
`dagster.yaml` if no config is there yet.

Both parts matter. Without `DAGSTER_HOME`, `dagster dev` builds a throwaway instance in a `.tmp_dagster_home_*` folder
under the working directory on every start — run history is lost between sessions. And without an instance config,
Dagster falls back to `DefaultRunCoordinator`, which launches runs with no concurrency cap and overwhelms MinerU. The
local config uses `QueuedRunCoordinator`, the same coordinator the deployed stages use, with `max_concurrent_runs` as a
literal `2` — deployed stages read that number from `DAGSTER_MAX_CONCURRENT_RUNS`, but a `$DAGSTER_HOME` config has no
guarantee the variable is set, and an unresolvable one breaks every Dagster process on the machine. Edit the installed
copy to tune it.

The copy is skipped when `$DAGSTER_HOME/dagster.yaml` already exists, so local tuning is never overwritten. Delete that
file to pick the repo version back up.

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
know the pipeline exists. Both halves of that come from one call:

```python
# acme_pipeline/__init__.py
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.pipeline.util import document_ingestion_pipeline_definitions

defs = document_ingestion_pipeline_definitions(
    # The routing key: this pipeline's sensors and schedule claim every knowledge database whose
    # `ingestor` equals this string, and nothing else touches those databases.
    ingestor="acme_rag",
    # How the ingestor is offered in the create-database dialog. Required for a custom ingestor —
    # unlabelled, it could only ever render as a bare id.
    display_name=LocaleString(en="Acme RAG", de="Acme RAG", fr="Acme RAG", it="Acme RAG"),
    description=LocaleString(en="Acme's OCR-heavy ingestion pipeline"),
)
```

A sensor in the pipeline publishes those labels to the platform database; `GET /knowledge/ingestors` reads them, so
"Acme RAG" appears in the create-database dialog within a tick of the pipeline coming up, and `create_database` accepts
it — with **no** change to the platform's `IngestorType` enum, API contract, or generated SDK, and nothing to install
into the API image.

The ingestor id must not collide with a platform routing token (`rag`, `unassigned`, the frozen `default_rag` /
`shared_rag`) or with the `datalake` subject token; `document_ingestion_pipeline_definitions` rejects those at definition time.

See ADR `2026_06_18_rag_pipeline_route_per_run` for the rationale, including why registration goes through the database
and why the `ingestor` field is a plain string at the API boundary.

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
