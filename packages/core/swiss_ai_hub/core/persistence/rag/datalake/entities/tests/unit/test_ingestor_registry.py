import pytest

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_registry import IngestorRegistry
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


def _ingestor(ingestor_id: str = "acme_rag", display_name: str = "Acme RAG") -> Ingestor:
    return Ingestor(
        id=ingestor_id,
        display_name=LocaleString(en=display_name),
        description=LocaleString(en="Acme's custom ingestion pipeline"),
    )


@pytest.fixture(autouse=True)
def _clear_registry():
    IngestorRegistry._custom.clear()
    IngestorRegistry._entry_points_loaded = True  # skip real entry-point discovery in the unit test
    yield
    IngestorRegistry._custom.clear()
    IngestorRegistry._entry_points_loaded = False


class TestIngestorRegistry:
    def test_registered_ingestor_becomes_selectable(self):
        IngestorRegistry.register(_ingestor("acme_rag"))

        assert IngestorRegistry.is_selectable("acme_rag")
        assert [ingestor.id for ingestor in IngestorRegistry.custom()] == ["acme_rag"]

    def test_custom_ingestors_are_appended_after_the_platform_ones(self):
        IngestorRegistry.register(_ingestor("acme_rag"))

        assert IngestorRegistry.selectable_ids() == [IngestorType.RAG.value, "acme_rag"]

    def test_non_selectable_platform_values_and_unknowns_stay_non_selectable(self):
        assert not IngestorRegistry.is_selectable(IngestorType.UNASSIGNED.value)
        assert not IngestorRegistry.is_selectable(IngestorType.DEFAULT_RAG.value)
        assert not IngestorRegistry.is_selectable("never_registered")

    def test_cannot_shadow_a_platform_ingestor(self):
        with pytest.raises(ValueError):
            IngestorRegistry.register(_ingestor(IngestorType.RAG.value))

    def test_reregistering_identical_metadata_is_idempotent(self):
        IngestorRegistry.register(_ingestor("acme_rag"))
        IngestorRegistry.register(_ingestor("acme_rag"))

        assert len(IngestorRegistry.custom()) == 1

    def test_reregistering_same_id_with_different_metadata_raises(self):
        IngestorRegistry.register(_ingestor("acme_rag", display_name="Acme RAG"))

        with pytest.raises(ValueError):
            IngestorRegistry.register(_ingestor("acme_rag", display_name="Renamed"))
