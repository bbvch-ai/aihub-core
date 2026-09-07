from typing import Annotated, Self

from mongoengine import Document, EmbeddedDocumentField, StringField, ValidationError
from mongoengine.context_managers import switch_db

from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import PipelineSourceType

_INGESTOR_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class IngestorEntity(Document):
    """A custom ingestion pipeline a deployment has made selectable, as advertised by the pipeline itself.

    The API and the pipelines run in separate containers, so an in-process registry in the pipeline can never
    be read by the API. Mongo is infrastructure both sides already share, which makes the pipeline's own
    deployment — rather than what happens to be installed in the API image — the thing that decides whether
    an ingestor is offered.
    """

    meta = {
        "collection": "ingestors",
        "strict": False,
        "indexes": [{"fields": ["ingestor_id"], "unique": True}],
    }

    ingestor_id = StringField(required=True, unique=True, regex=_INGESTOR_ID_PATTERN)
    display_name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)

    @staticmethod
    def reserved_ids() -> set[str]:
        """Ids a custom pipeline may not claim.

        The ``IngestorType`` values are the platform's own routing tokens — including the frozen legacy ones,
        which stay reserved after their code is gone so a new pipeline can never adopt a legacy corpus. The
        pipeline source types are reserved because the type-keyed subject grammar puts the ingestor id in the
        subject's source-type position, where ``datalake`` would collide with the legacy per-instance streams.
        """
        return {ingestor_type.value for ingestor_type in IngestorType} | {
            source_type.value for source_type in PipelineSourceType
        }

    @classmethod
    def upsert(
        cls,
        ingestor: Annotated[Ingestor, "Ingestor the pipeline advertises"],
        db_alias: str = "default",
    ) -> Self:
        """Registers or refreshes a custom ingestor; a redeploy with changed labels updates them."""
        if ingestor.id in cls.reserved_ids():
            raise ValidationError(f"Ingestor id '{ingestor.id}' is reserved by the platform.")

        with switch_db(cls, db_alias) as SwitchedIngestor:
            return SwitchedIngestor.objects(ingestor_id=ingestor.id).modify(
                upsert=True,
                new=True,
                set__display_name=LocaleStringEntity.from_locale_string(ingestor.display_name),
                set__description=LocaleStringEntity.from_locale_string(ingestor.description),
            )

    @classmethod
    def custom(cls, db_alias: str = "default") -> list[Ingestor]:
        """Every registered custom ingestor, as the value object the API serves."""
        with switch_db(cls, db_alias) as SwitchedIngestor:
            return [entity.to_ingestor() for entity in SwitchedIngestor.objects.order_by("ingestor_id")]

    @classmethod
    def is_selectable(cls, ingestor_id: str, db_alias: str = "default") -> bool:
        """Whether a user may assign this ingestor to a new knowledge database."""
        if ingestor_id in {ingestor_type.value for ingestor_type in IngestorType.selectable()}:
            return True
        with switch_db(cls, db_alias) as SwitchedIngestor:
            return bool(SwitchedIngestor.objects(ingestor_id=ingestor_id).first())

    def to_ingestor(self) -> Ingestor:
        return Ingestor(
            id=self.ingestor_id,
            display_name=self.display_name.to_locale_string(),
            description=self.description.to_locale_string(),
        )
