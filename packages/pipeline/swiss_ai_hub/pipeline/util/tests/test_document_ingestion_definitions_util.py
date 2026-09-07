from dagster import AssetKey, Definitions
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions


def _asset_keys(defs: Definitions) -> set[AssetKey]:
    keys: set[AssetKey] = set()
    for asset in defs.assets or []:
        keys |= set(getattr(asset, "keys", None) or {asset.key})
    return keys


def _partition_names(defs: Definitions) -> set[str]:
    names: set[str] = set()
    for asset in defs.assets or []:
        partitions_def = getattr(asset, "partitions_def", None)
        if partitions_def is not None:
            names.add(partitions_def.name)
    return names


def _job_names(defs: Definitions) -> set[str]:
    return {job.name for job in defs.jobs or []}


def _custom_pipeline() -> Definitions:
    """A custom ingestor must carry the labels the create-database selector renders it with."""
    return document_ingestion_pipeline_definitions(
        ingestor="ocr_heavy_rag",
        display_name=LocaleString(en="OCR-heavy RAG"),
        description=LocaleString(en="RAG tuned for scanned documents"),
    )


class TestDocumentIngestionPipelineNamesAreIngestorScoped:
    """A second pipeline *type* must be deployable alongside the first.

    Asset keys are unique per Dagster deployment and ``DynamicPartitionsDefinition`` names are global to the
    Dagster instance, so every deployment-global name has to be derived from the ingestor. Hardcoding them
    would make two code locations built from this same factory collide instead of coexist.
    """

    def test_two_ingestors_produce_disjoint_asset_keys(self) -> None:
        platform = document_ingestion_pipeline_definitions(ingestor="document_ingestion")
        ocr_heavy = _custom_pipeline()

        assert _asset_keys(platform).isdisjoint(_asset_keys(ocr_heavy))

    def test_two_ingestors_produce_distinct_partition_registries(self) -> None:
        platform = document_ingestion_pipeline_definitions(ingestor="document_ingestion")
        ocr_heavy = _custom_pipeline()

        assert _partition_names(platform) == {"document_ingestion_document_partitions"}
        assert _partition_names(ocr_heavy) == {"ocr_heavy_rag_document_partitions"}

    def test_two_ingestors_produce_distinct_job_names(self) -> None:
        platform = document_ingestion_pipeline_definitions(ingestor="document_ingestion")
        ocr_heavy = _custom_pipeline()

        assert _job_names(platform).isdisjoint(_job_names(ocr_heavy))

    def test_asset_keys_do_not_collide_with_a_bucket_bound_legacy_pipeline(self) -> None:
        """A custom deployment's own pipeline uses ``[container, "datalake_to_vectorstore", …]`` keys."""
        platform = document_ingestion_pipeline_definitions(ingestor="document_ingestion")

        legacy_keys = {
            AssetKey(["pocrag", "datalake_to_vectorstore", name])
            for name in ("data_lake", "documents", "nodes", "summary_nodes", "removed_documents")
        }

        assert _asset_keys(platform).isdisjoint(legacy_keys)


class TestResourcesAreFullyWired:
    """Every resource dependency the ops dereference at run time must be supplied at build time.

    A `ConfigurableResource` with an unset `ResourceDependency` builds fine and only fails when an op
    dereferences it, so a missing one survives every import-level check and surfaces as a failed
    ingestion run instead.
    """

    def test_the_node_parser_knows_which_embedding_model_will_consume_its_nodes(self):
        """Without this the chunker cannot size nodes and every document fails at chunk time."""
        node_parser = document_ingestion_pipeline_definitions().resources["node_parser"]

        assert node_parser.embedding_config is not None
        assert node_parser.llm_config is not None

    def test_the_summary_parser_knows_which_model_writes_its_summaries(self):
        summary_parser = document_ingestion_pipeline_definitions().resources["summary_parser"]

        assert summary_parser.llm_config is not None

    def test_the_table_refiner_knows_which_model_refines_its_tables(self):
        table_refinement = document_ingestion_pipeline_definitions(with_table_refinement=True).resources[
            "table_refinement"
        ]

        assert table_refinement.llm_config is not None
