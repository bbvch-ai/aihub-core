from typing import Self

from pydantic import ConfigDict

from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.form.secret_field_walker import SecretFieldWalker


class SourcePipelineConfig(Form):
    """
    The configuration a knowledge database carries for the source pipeline that fills it.

    A source pipeline (Stage 1: an external system → the database's data lake) subclasses this and declares its
    knobs in form duality, the way an ingestion pipeline does with ``IngestorConfig``. The two are separate
    axes of one database: the ingestor says how files are processed, the source says where they come from.
    Unlike ``IngestorConfig`` there are no identity fields here — the database's name and description belong
    to the ingestor form, and the source form renders as a second section of the same dialog.

    Credentials are declared as ``str | Password``; ``secret_field_paths`` derives their paths from the announced
    form so the API can encrypt them and the pipeline can decrypt them without either side naming a field.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @classmethod
    def as_form(cls) -> Self:
        """The form-mode config a subclass announces; the base has nothing to declare."""
        return cls()

    @classmethod
    def secret_field_paths(cls) -> set[str]:
        return SecretFieldWalker.secret_paths(cls.as_form().to_formkit_form())
