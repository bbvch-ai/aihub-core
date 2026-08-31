import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_entity import IngestorEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


def _ingestor(ingestor_id: str = "acme_rag", display_name: str = "Acme RAG") -> Ingestor:
    return Ingestor(
        id=ingestor_id,
        display_name=LocaleString(en=display_name),
        description=LocaleString(en="Acme's custom ingestion pipeline"),
    )


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_ingestors(mongo_connection):
    IngestorEntity.objects.delete()
    yield
    IngestorEntity.objects.delete()


class TestUpsert:
    def test_a_registered_ingestor_becomes_selectable_and_is_offered_with_its_labels(self):
        IngestorEntity.upsert(_ingestor())

        assert IngestorEntity.is_selectable("acme_rag")
        custom = IngestorEntity.custom()
        assert [ingestor.id for ingestor in custom] == ["acme_rag"]
        assert custom[0].display_name.en == "Acme RAG"

    def test_re_registering_is_idempotent_and_refreshes_the_labels(self):
        """Every sensor tick upserts, and a redeploy may carry renamed labels."""
        IngestorEntity.upsert(_ingestor())
        IngestorEntity.upsert(_ingestor(display_name="Acme RAG v2"))

        custom = IngestorEntity.custom()
        assert len(custom) == 1
        assert custom[0].display_name.en == "Acme RAG v2"


class TestIsSelectable:
    def test_the_platform_pipeline_is_selectable_without_a_row(self):
        assert IngestorEntity.is_selectable(IngestorType.DOCUMENT_INGESTION.value)

    @pytest.mark.parametrize(
        "not_selectable",
        [IngestorType.UNASSIGNED.value, IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value],
    )
    def test_inert_and_legacy_tokens_are_never_selectable(self, not_selectable):
        assert not IngestorEntity.is_selectable(not_selectable)

    def test_an_unregistered_ingestor_is_not_selectable(self):
        assert not IngestorEntity.is_selectable("never_registered")
