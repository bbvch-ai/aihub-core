from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Self

from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocumentField,
    ListField,
    StringField,
    ValidationError,
)
from mongoengine.context_managers import switch_db
from pydantic import TypeAdapter

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.persistence.form.config_specs_entity import ConfigSpecsEntity
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline import SourcePipeline
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import PipelineSourceType

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

_SOURCE_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class SourcePipelineEntity(Document):
    """A source pipeline a deployment has made selectable, as advertised by the pipeline itself.

    The sibling of ``IngestorEntity`` for Stage 1. It lives in its own collection rather than as a flag on the
    ingestor record because the two are independent axes of a database: a deployment may run several ingestors
    and several sources, and a database picks one of each.
    """

    meta = {
        "collection": "source_pipelines",
        "strict": False,
        "indexes": [{"fields": ["source_id"], "unique": True}],
    }

    source_id = StringField(required=True, unique=True, regex=_SOURCE_ID_PATTERN)
    display_name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    # Stored without aliases: MongoDB rejects keys starting with '$'. Aliases are restored when serving.
    form = ListField(DictField(), default=list)
    config_specs = EmbeddedDocumentField(ConfigSpecsEntity, required=False)
    last_registered = DateTimeField(required=True, default=lambda: datetime.now(UTC))

    @staticmethod
    def reserved_ids() -> set[str]:
        """Ids no source pipeline may register.

        Every ingestor token is reserved because both kinds of pipeline derive their Dagster job names from
        their token (``{token}_source_observation``) and the single-flight guard matches runs by job name
        across code locations: an ingestor and a source sharing a token would suppress each other's runs.
        The pipeline source types are reserved for the same subject-grammar reason as on ``IngestorEntity``.
        """
        return {ingestor_type.value for ingestor_type in IngestorType} | {
            source_type.value for source_type in PipelineSourceType
        }

    @property
    def form_elements(self) -> list["FormkitElement"]:
        if not self.form:
            return []
        return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(self.form)

    @classmethod
    def upsert(
        cls,
        source_pipeline: Annotated[SourcePipeline, "Source pipeline the deployment advertises"],
        db_alias: str = "default",
    ) -> Self:
        """Registers or refreshes a source pipeline; a redeploy with changed labels or a changed form updates them."""
        if source_pipeline.id in cls.reserved_ids():
            raise ValidationError(f"Source pipeline id '{source_pipeline.id}' is reserved by the platform.")

        with switch_db(cls, db_alias) as SwitchedSourcePipeline:
            return SwitchedSourcePipeline.objects(source_id=source_pipeline.id).modify(
                upsert=True,
                new=True,
                set__display_name=LocaleStringEntity.from_locale_string(source_pipeline.display_name),
                set__description=LocaleStringEntity.from_locale_string(source_pipeline.description),
                set__form=[element.model_dump() for element in source_pipeline.form],
                set__config_specs=ConfigSpecsEntity.from_specs(source_pipeline.config_specs),
                set__last_registered=datetime.now(UTC),
            )

    @classmethod
    def all(cls, db_alias: str = "default") -> list[SourcePipeline]:
        """Every source pipeline that announced a configuration form, as the value object the API serves."""
        with switch_db(cls, db_alias) as SwitchedSourcePipeline:
            registered = SwitchedSourcePipeline.objects(config_specs__exists=True).order_by("source_id")
            return [entity.to_source_pipeline() for entity in registered]

    @classmethod
    def find(cls, source_id: str, db_alias: str = "default") -> Self | None:
        with switch_db(cls, db_alias) as SwitchedSourcePipeline:
            return SwitchedSourcePipeline.objects(source_id=source_id).first()

    def to_source_pipeline(self) -> SourcePipeline:
        return SourcePipeline(
            id=self.source_id,
            display_name=self.display_name.to_locale_string(),
            description=self.description.to_locale_string(),
            form=self.form_elements,
            config_specs=self.config_specs.to_specs() if self.config_specs else ConfigSpecs(),
        )
