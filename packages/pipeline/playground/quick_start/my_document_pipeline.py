"""Full document ingestion pipeline: data lake → parsed documents → embedded nodes in Milvus.

Run with ``uv run dagster dev -m playground.quick_start.my_document_pipeline``.

One deployment serves every knowledge database rather than one bucket. The graph carries no bucket
name at all; each run resolves its target from the composite partition key ``{bucket}|{file_uri}``
(ingestion) or the ``aihub/bucket`` run tag (observation and cleanup). Creating a knowledge database
therefore needs no new code location, compose service or environment variable — only a
``BucketEntity`` row naming this pipeline's ingestor, which ``playground/__init__.py`` creates for
the playground bucket.

``document_ingestion_pipeline_definitions`` assembles the whole thing:

* an **observable data lake asset** that lists the bucket and registers one partition per file,
* **documents** — parse each file (MinerU), optionally refine tables and describe figures, and store
  the result as a ``RefDoc`` in the doc store, flagged not-yet-ingested,
* **nodes** — chunk each document, embed the chunks, write them to Milvus, and only then flip the
  document to ingested, because a parsed document without embeddings is not yet retrievable,
* **summary nodes** (optional) — recursive summaries for hierarchical retrieval,
* **removed documents** — prune documents whose source file is gone,

plus the jobs, the daily observation schedule, and the sensors that keep one observation per
database in flight while uploads arrive.
"""

from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings

from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import LoaderType
from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions

settings = DocumentIngestionPipelineSettings()

defs = document_ingestion_pipeline_definitions(
    # Every deployment-global name — asset keys, the dynamic-partition registry, job names — is derived
    # from the ingestor, which is what lets a second pipeline type run alongside this one. It is also the
    # routing guard: this pipeline ingests exactly the databases whose BucketEntity names it.
    ingestor="document_ingestion",
    embedding_model_name=settings.EMBEDDING_MODEL,
    llm_model_name=settings.LLM_MODEL,
    with_summary_nodes=True,
    with_table_refinement=True,
    with_figure_descriptions=True,
    document_parser_loader_type=LoaderType.MINERU,
    observe_job_hour=0,
    observe_job_minute=0,
)
