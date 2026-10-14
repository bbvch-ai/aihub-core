import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline import SourcePipeline
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_entity import SourcePipelineEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_type import SourcePipelineType
from swiss_ai_hub.core.source_pipelines.source_pipeline_config import SourcePipelineConfig


def _source_pipeline(source_id: str = "acme_sync", display_name: str = "Acme Sync") -> SourcePipeline:
    return SourcePipeline.from_config(
        source_id,
        LocaleString(en=display_name),
        LocaleString(en="Acme's custom sync pipeline"),
        SourcePipelineConfig.as_form(),
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
def clean_source_pipelines(mongo_connection):
    SourcePipelineEntity.objects.delete()
    yield
    SourcePipelineEntity.objects.delete()


class TestUpsert:
    def test_a_registered_source_pipeline_is_offered_with_its_labels(self):
        SourcePipelineEntity.upsert(_source_pipeline())

        assert SourcePipelineEntity.find("acme_sync") is not None
        registered = SourcePipelineEntity.all()
        assert [source_pipeline.id for source_pipeline in registered] == ["acme_sync"]
        assert registered[0].display_name.en == "Acme Sync"

    def test_re_registering_is_idempotent_and_refreshes_the_labels(self):
        SourcePipelineEntity.upsert(_source_pipeline())
        SourcePipelineEntity.upsert(_source_pipeline(display_name="Acme Sync v2"))

        registered = SourcePipelineEntity.all()
        assert len(registered) == 1
        assert registered[0].display_name.en == "Acme Sync v2"

    def test_the_announced_form_and_schema_round_trip_through_mongo(self):
        source_pipeline = _source_pipeline()
        source_pipeline.form.append(Password(name="token", label=LocaleString(en="Token")))
        SourcePipelineEntity.upsert(source_pipeline)

        stored = SourcePipelineEntity.all()[0]

        assert type(stored.form[-1]) is Password
        assert stored.config_specs.config_class == "SourcePipelineConfig"

    def test_the_shipped_rclone_pipeline_registers_like_any_other(self):
        SourcePipelineEntity.upsert(_source_pipeline(SourcePipelineType.RCLONE.value))

        assert SourcePipelineEntity.find(SourcePipelineType.RCLONE.value) is not None


class TestOffered:
    def test_an_unregistered_source_pipeline_is_not_offered(self):
        """Without a running pipeline nothing would fill the database, so nothing is offered."""
        assert SourcePipelineEntity.find(SourcePipelineType.RCLONE.value) is None
        assert SourcePipelineEntity.all() == []
