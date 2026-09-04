from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.i18n.locale_string import LocaleString


class Ingestor(BaseModel):
    """A user-selectable ingestion pipeline contributed by a deployment.

    ``id`` is stored on ``BucketEntity.ingestor`` and must equal the ``ingestor`` a custom pipeline passes
    to ``document_ingestion_pipeline_definitions`` — that string is the routing guard by which the pipeline claims the
    databases it owns. ``display_name``/``description`` are carried on the object (not resolved from the
    platform's i18n files) because a custom ingestor's labels live in the deployment, not in core.
    """

    id: Annotated[
        str,
        Field(
            pattern=r"^[a-z][a-z0-9_]*$",
            description="Routing id stored on the database and passed to the pipeline (lowercase, alphanumeric/_).",
        ),
    ]
    display_name: Annotated[LocaleString, Field(description="Localized name shown in the create-database selector.")]
    description: Annotated[LocaleString, Field(description="Localized description of what the pipeline does.")]
