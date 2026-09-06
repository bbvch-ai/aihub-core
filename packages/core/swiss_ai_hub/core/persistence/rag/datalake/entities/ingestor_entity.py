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
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import PipelineSourceType

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

_INGESTOR_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class IngestorEntity(Document):
    """An ingestion pipeline a deployment has made selectable, as advertised by the pipeline itself.

    The API and the pipelines run in separate containers, so an in-process registry in the pipeline can never
    be read by the API. Mongo is infrastructure both sides already share, which makes the pipeline's own
    deployment — rather than what happens to be installed in the API image — the thing that decides whether
    an ingestor is offered and what its databases can be configured with.
    """

    meta = {
        "collection": "ingestors",
        "strict": False,
        "indexes": [{"fields": ["ingestor_id"], "unique": True}],
    }

    ingestor_id = StringField(required=True, unique=True, regex=_INGESTOR_ID_PATTERN)
    display_name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    # Stored without aliases: MongoDB rejects keys starting with '$'. Aliases are restored when serving.
    form = ListField(DictField(), default=list)
    config_specs = EmbeddedDocumentField(ConfigSpecsEntity, required=False)
    last_registered = DateTimeField(required=True, default=lambda: datetime.now(UTC))

    @staticmethod
    def reserved_ids() -> set[str]:
        """Ids no pipeline may register.

        The inert and frozen legacy routing tokens stay reserved after their code is gone so a new pipeline can
        never adopt a legacy corpus. The pipeline source types are reserved because the type-keyed subject
        grammar puts the ingestor id in the subject's source-type position, where ``datalake`` would collide
        with the legacy per-instance streams.
        """
        return {ingestor_type.value for ingestor_type in IngestorType.legacy()} | {
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
        ingestor: Annotated[Ingestor, "Ingestor the pipeline advertises"],
        db_alias: str = "default",
    ) -> Self:
        """Registers or refreshes an ingestor; a redeploy with changed labels or a changed form updates them."""
        if ingestor.id in cls.reserved_ids():
            raise ValidationError(f"Ingestor id '{ingestor.id}' is reserved by the platform.")

        with switch_db(cls, db_alias) as SwitchedIngestor:
            return SwitchedIngestor.objects(ingestor_id=ingestor.id).modify(
                upsert=True,
                new=True,
                set__display_name=LocaleStringEntity.from_locale_string(ingestor.display_name),
                set__description=LocaleStringEntity.from_locale_string(ingestor.description),
                set__form=[element.model_dump() for element in ingestor.form],
                set__config_specs=ConfigSpecsEntity.from_specs(ingestor.config_specs),
                set__last_registered=datetime.now(UTC),
            )

    @classmethod
    def all(cls, db_alias: str = "default") -> list[Ingestor]:
        """Every ingestor that announced a configuration form, as the value object the API serves.

        A row a pre-announcement pipeline image left behind carries labels but no schema; offering it would render
        an empty form whose submission nothing could validate.
        """
        with switch_db(cls, db_alias) as SwitchedIngestor:
            registered = SwitchedIngestor.objects(config_specs__exists=True).order_by("ingestor_id")
            return [entity.to_ingestor() for entity in registered]

    @classmethod
    def find(cls, ingestor_id: str, db_alias: str = "default") -> Self | None:
        with switch_db(cls, db_alias) as SwitchedIngestor:
            return SwitchedIngestor.objects(ingestor_id=ingestor_id).first()

    def to_ingestor(self) -> Ingestor:
        return Ingestor(
            id=self.ingestor_id,
            display_name=self.display_name.to_locale_string(),
            description=self.description.to_locale_string(),
            form=self.form_elements,
            config_specs=self.config_specs.to_specs() if self.config_specs else ConfigSpecs(),
        )
