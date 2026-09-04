from typing import Annotated, Self

import pytest
from dagster import AssetKey, Definitions
from pydantic import Field
from swiss_ai_hub.core.form import InputNumber
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import IngestorType

from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig
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

    def test_every_enrichment_resource_is_wired_whatever_the_deployment_defaults_say(self):
        """The graph is the same for every database; a database opts in or out per run, not the deployment."""
        defs = document_ingestion_pipeline_definitions(
            with_summary_nodes=False, with_table_refinement=False, with_figure_descriptions=False
        )

        assert "table_refinement" in defs.resources
        assert "summary_parser" in defs.resources
        assert AssetKey(["document_ingestion_datalake_to_vectorstore", "summary_nodes"]) in _asset_keys(defs)


def _registration_sensor(defs: Definitions):
    return next(sensor for sensor in defs.sensors if sensor.name.startswith("IngestorRegistrationSensorFor_"))


class _CrawlConfig(DocumentIngestionConfig):
    """A deployment's own knob on top of the shipped ones."""

    crawl_depth: Annotated[int | InputNumber | None, Field(description="How deep to crawl")] = None

    @classmethod
    def as_form(cls, **defaults) -> Self:
        base = DocumentIngestionConfig.as_form(**defaults)
        return cls(**dict(base), crawl_depth=InputNumber(label=LocaleString(en="Crawl depth"), value=2))


class TestIngestorRegistration:
    """A pipeline announces itself — labels, form and schema — through one record the API reads."""

    def test_the_shipped_pipeline_registers_itself_like_any_custom_one(self):
        sensor = _registration_sensor(document_ingestion_pipeline_definitions())

        assert sensor.name == f"IngestorRegistrationSensorFor_{IngestorType.DOCUMENT_INGESTION.value}"

    def test_a_custom_pipeline_registers_under_its_own_id(self):
        assert _registration_sensor(_custom_pipeline()).name == "IngestorRegistrationSensorFor_ocr_heavy_rag"

    def test_a_custom_ingestor_without_labels_is_rejected_at_build_time(self):
        with pytest.raises(ValueError, match="display_name"):
            document_ingestion_pipeline_definitions(ingestor="unlabelled")

    @pytest.mark.parametrize("reserved", [IngestorType.DEFAULT_RAG.value, IngestorType.UNASSIGNED.value, "datalake"])
    def test_a_reserved_id_is_rejected_at_build_time(self, reserved):
        with pytest.raises(ValueError, match="reserved"):
            document_ingestion_pipeline_definitions(
                ingestor=reserved, display_name=LocaleString(en="x"), description=LocaleString(en="y")
            )

    def test_a_custom_config_extends_the_announced_form_without_platform_changes(self):
        """Accepted-when #1 of #1822: a new knob is a pipeline-side declaration and nothing else."""
        defs = document_ingestion_pipeline_definitions(
            ingestor="crawler",
            display_name=LocaleString(en="Crawler"),
            description=LocaleString(en="Crawls sites"),
            config=_CrawlConfig.as_form(llm_model="text-generation/x", embedding_model="embedding/y"),
        )

        assert _registration_sensor(defs).name == "IngestorRegistrationSensorFor_crawler"
