import pytest
from mongoengine import ValidationError

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_entity import IngestorEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


def _ingestor(ingestor_id: str) -> Ingestor:
    return Ingestor(
        id=ingestor_id,
        display_name=LocaleString(en="Acme RAG"),
        description=LocaleString(en="Acme's custom ingestion pipeline"),
    )


class TestReservedIds:
    @pytest.mark.parametrize("reserved", [ingestor_type.value for ingestor_type in IngestorType])
    def test_every_platform_routing_token_is_reserved(self, reserved):
        """The legacy tokens stay reserved after their code is gone: those corpora are frozen, and a new
        pipeline adopting one would ingest on top of it."""
        assert reserved in IngestorEntity.reserved_ids()

    def test_the_legacy_subject_source_type_is_reserved(self):
        """A stream filtered on ``pipeline.datalake.>`` would overlap the legacy per-instance streams."""
        assert "datalake" in IngestorEntity.reserved_ids()

    def test_upsert_rejects_a_reserved_id_before_touching_the_database(self):
        reserved_ingestor = _ingestor(IngestorType.DOCUMENT_INGESTION.value)

        with pytest.raises(ValidationError, match="reserved"):
            IngestorEntity.upsert(reserved_ingestor)
