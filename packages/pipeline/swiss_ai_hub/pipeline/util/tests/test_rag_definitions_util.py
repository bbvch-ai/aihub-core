from dagster import AssetKey, Definitions

from swiss_ai_hub.pipeline.util.rag_definitions_util import rag_pipeline_definitions


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


class TestRagPipelineNamesAreIngestorScoped:
    """A second pipeline *type* must be deployable alongside the first.

    Asset keys are unique per Dagster deployment and ``DynamicPartitionsDefinition`` names are global to the
    Dagster instance, so every deployment-global name has to be derived from the ingestor. Hardcoding them
    would make two code locations built from this same factory collide instead of coexist.
    """

    def test_two_ingestors_produce_disjoint_asset_keys(self) -> None:
        rag = rag_pipeline_definitions(ingestor="rag")
        ocr_heavy = rag_pipeline_definitions(ingestor="ocr_heavy_rag")

        assert _asset_keys(rag).isdisjoint(_asset_keys(ocr_heavy))

    def test_two_ingestors_produce_distinct_partition_registries(self) -> None:
        rag = rag_pipeline_definitions(ingestor="rag")
        ocr_heavy = rag_pipeline_definitions(ingestor="ocr_heavy_rag")

        assert _partition_names(rag) == {"rag_document_partitions"}
        assert _partition_names(ocr_heavy) == {"ocr_heavy_rag_document_partitions"}

    def test_two_ingestors_produce_distinct_job_names(self) -> None:
        rag = rag_pipeline_definitions(ingestor="rag")
        ocr_heavy = rag_pipeline_definitions(ingestor="ocr_heavy_rag")

        assert _job_names(rag).isdisjoint(_job_names(ocr_heavy))

    def test_asset_keys_do_not_collide_with_a_bucket_bound_legacy_pipeline(self) -> None:
        """A custom deployment's own pipeline uses ``[container, "datalake_to_vectorstore", …]`` keys."""
        rag = rag_pipeline_definitions(ingestor="rag")

        legacy_keys = {
            AssetKey(["pocrag", "datalake_to_vectorstore", name])
            for name in ("data_lake", "documents", "nodes", "summary_nodes", "removed_documents")
        }

        assert _asset_keys(rag).isdisjoint(legacy_keys)
