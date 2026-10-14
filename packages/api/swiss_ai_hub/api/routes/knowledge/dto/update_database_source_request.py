from typing import Annotated, Any

from pydantic import BaseModel, Field


class UpdateDatabaseSourceRequest(BaseModel):
    source: Annotated[
        str | None,
        Field(
            description="The deployed source pipeline that fills this database, as served by "
            "GET /knowledge/source-pipelines; null switches the database back to manual upload."
        ),
    ] = None
    source_configuration: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="The source's settings as submitted through its announced form. Secret fields may carry the "
            "mask returned by the API to keep the stored value.",
        ),
    ]
    replace_existing_documents: Annotated[
        bool,
        Field(
            description="Acknowledges that handing a database to a different source, from manual upload or from "
            "another source, gives its content to that source: documents the new source does not have are removed on "
            "its next sync. Required when the database already holds documents; not needed to edit the current "
            "source's settings or to switch back to manual upload."
        ),
    ] = False
