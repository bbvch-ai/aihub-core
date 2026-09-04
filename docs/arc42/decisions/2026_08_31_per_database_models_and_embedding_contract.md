# Per-Database Models: the Ingestion Recipe Belongs to the Knowledge Database

## Context

Before route-per-run, a document ingestion deployment served exactly one knowledge database, so "the deployment's
embedding model" and "this corpus's embedding model" were the same sentence. `DOCUMENT_INGESTION_EMBEDDING_MODEL`,
`DOCUMENT_INGESTION_LLM_MODEL` and a global `MILVUS_DIMENSION` were therefore adequate.

`2026_06_18_rag_pipeline_route_per_run` collapsed that one-to-one relationship: a single deployment now ingests every
self-service knowledge database. Deployment-level model configuration became the wrong shape the moment a tenant could
create a second database — every corpus in the platform would be embedded and enriched identically, regardless of what
it contains or what it costs to process.

The global dimension setting is the sharper problem. A collection's vector width and the model that produces its vectors
are two expressions of one fact, and Milvus does not police the relationship: a collection created with the wrong
dimension is not rejected, it silently truncates or pads every vector that reaches it. Held as two independent settings,
they are one careless edit away from a corpus that indexes cleanly and retrieves nonsense.

## Decision Drivers

1. **Vectors are only comparable within one embedding model.** The embedding model is a property of the corpus, not of
   the cluster that happens to host it. Two databases embedded by different models cannot share a configuration knob.
2. **A dimension must be derived, never configured twice.** Anything a system can compute from a source of truth should
   not also be settable next to it, especially when the failure mode is silent.
3. **Upgrades must not re-embed anything.** Databases created before models were configurable have to keep ingesting
   with exactly what they used before — re-embedding an existing corpus is hours of avoidable compute.
4. **Enrichment is a cost and quality dial.** Summaries, table refinement and figure descriptions are the expensive part
   of ingestion, and how much of it a corpus deserves differs per corpus.

## Decision

**A knowledge database carries the models it is ingested with; the pipeline reads them per run.**

1. **`BucketEntity` gains `llm_model` and `embedding_model`**, both nullable, both chosen at create time through the
   create-database form and the API.

2. **Null means "the deployment's default"** (`DocumentIngestionPipelineSettings`). Rows written before the fields
   existed therefore keep their exact prior behaviour with no migration, and a deployment that never wants per-database
   models can ignore the feature entirely.

3. **The API validates both** against `ModelService.get_model_by_name`, and additionally requires an embedding model to
   declare an `output_vector_size` — a model that does not is rejected with a 400 naming the missing field, rather than
   accepted into a database whose dimension cannot be derived. The platform default `embedding/bge-m3` declares
   `output_vector_size: 1024` in the LiteLLM config for this reason.

4. **The pipeline resolves models from the bucket per run** (`pipeline/util/model_builders.py`), the same way it already
   resolves stores. Model instances are cached per bucket so a partition-per-document graph reuses one client.

5. **The collection's dimension is derived from the embedding model's declared width**, not from `MILVUS_DIMENSION`. The
   two facts now have one source.

6. **Neither field is updatable.** `update_bucket` exposes no parameter for either, so a database's models are fixed for
   its lifetime.

## Consequences

### Positive

- Two databases in one deployment can be ingested concurrently with different models. Verified on a live stack: one
  database enriched through Kimi-K2.6 while another ran on gemma-4-31B-it, in the same minute, through the same
  pipeline.
- The dimension cannot drift from the model that produces the vectors, and a model that would make the dimension
  underivable is refused at the API boundary rather than at index time.
- A corpus that warrants an expensive model can have one without imposing that cost on every other corpus in the
  deployment.

### Trade-offs

- **The query side does not honour this contract yet.** Retrieval still reads a per-agent `embed_model`, so a database
  ingested with one embedding model can be queried with another: retrieval silently degrades, or fails outright on a
  dimension mismatch. Nothing in the platform currently prevents it. Closing the gap means the retriever reads the model
  off the same `BucketEntity` and the per-agent field is removed — roughly 13 files across `packages/core` and
  `packages/agent`, and a breaking change to stored agent configurations. Tracked in #1782. **Until it lands, the
  contract this ADR establishes is enforced on the write path only.**

- **The text-generation model is immutable too, though only the embedding model needs to be.** Re-embedding is what an
  embedding change would require; the enrichment model could safely change for future documents. One rule ("a database's
  models are fixed") is easier to reason about than two, so both are frozen for now — at the cost of forcing a database
  to be recreated to change its enrichment model. Worth revisiting if anyone asks for it.

- **Enrichment flags remain deployment-level.** `WITH_SUMMARY_NODES`, `WITH_TABLE_REFINEMENT` and
  `WITH_FIGURE_DESCRIPTIONS` still apply to every database the deployment serves, so the cost dial is coarser than the
  model choice. Captured as a scope note on #1782.

- **A database outlives its model's registration.** If an embedding model is removed from the LiteLLM config after a
  database was created with it, that database's ingestion fails when the width lookup finds no model — the row still
  names something the gateway no longer serves. Recovery is to restore the model or edit the row directly; there is no
  UI for it.

## Related Decisions

- `2026_09_04_ingestors_announce_their_configuration_form` — supersedes decision 1: the two columns became keys of
  `BucketEntity.configuration`, declared by the pipeline's announced form and validated against its announced schema.
  The dimension contract (decisions 3 and 5) is kept and enforced on the announced `ModelSelect` elements instead of
  fixed fields.
- `2026_06_18_rag_pipeline_route_per_run` — one deployment serving every database, which is what makes per-database
  configuration necessary in the first place.
- `2026_08_31_legacy_rag_pipelines_frozen_and_removed` — the frozen legacy pipelines keep their deploy-time model
  configuration; none of this applies to them.
