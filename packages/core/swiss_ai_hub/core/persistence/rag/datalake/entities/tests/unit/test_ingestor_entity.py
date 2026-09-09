import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.ingestors.ingestor_config import IngestorConfig
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_entity import IngestorEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


def _ingestor(ingestor_id: str = "acme_rag", display_name: str = "Acme RAG") -> Ingestor:
    return Ingestor.from_config(
        ingestor_id,
        LocaleString(en=display_name),
        LocaleString(en="Acme's custom ingestion pipeline"),
        IngestorConfig.as_form(),
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

        assert IngestorEntity.find("acme_rag") is not None
        registered = IngestorEntity.all()
        assert [ingestor.id for ingestor in registered] == ["acme_rag"]
        assert registered[0].display_name.en == "Acme RAG"

    def test_re_registering_is_idempotent_and_refreshes_the_labels(self):
        """Every sensor tick upserts, and a redeploy may carry renamed labels."""
        IngestorEntity.upsert(_ingestor())
        IngestorEntity.upsert(_ingestor(display_name="Acme RAG v2"))

        registered = IngestorEntity.all()
        assert len(registered) == 1
        assert registered[0].display_name.en == "Acme RAG v2"

    def test_the_announced_form_and_schema_round_trip_through_mongo(self):
        """Form elements are stored alias-free (Mongo rejects ``$`` keys) and rehydrated as typed elements."""
        ingestor = _ingestor()
        ingestor.form.append(ModelSelect(name="embedding_model", label=LocaleString(en="Embedding"), mode="embedding"))
        IngestorEntity.upsert(ingestor)

        stored = IngestorEntity.all()[0]

        assert [type(element) for element in stored.form][-1] is ModelSelect
        assert stored.form[-1].mode == "embedding"
        assert set(stored.config_specs.config_schema["properties"]) == {"name", "description"}

    def test_the_shipped_document_ingestion_pipeline_registers_like_any_other(self):
        IngestorEntity.upsert(_ingestor(IngestorType.DOCUMENT_INGESTION.value))

        assert IngestorEntity.find(IngestorType.DOCUMENT_INGESTION.value) is not None


class TestOffered:
    def test_an_unregistered_platform_pipeline_is_not_offered(self):
        """Without a running pipeline nothing would ingest the database, so nothing is offered."""
        assert IngestorEntity.find(IngestorType.DOCUMENT_INGESTION.value) is None
        assert IngestorEntity.all() == []

    @pytest.mark.parametrize("token", [ingestor_type.value for ingestor_type in IngestorType.legacy()])
    def test_inert_and_legacy_tokens_are_never_registered(self, token):
        assert IngestorEntity.find(token) is None

    def test_a_row_without_an_announced_form_is_not_offered(self, mongo_connection):
        """A pre-announcement pipeline image left labels only; an empty form could not be validated."""
        IngestorEntity(
            ingestor_id="legacy_labels_only",
            display_name=LocaleStringEntity(en="Legacy"),
            description=LocaleStringEntity(en="Registered by an older image"),
        ).save()

        assert [ingestor.id for ingestor in IngestorEntity.all()] == []
        assert IngestorEntity.find("legacy_labels_only").config_specs is None
