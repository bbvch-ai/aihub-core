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
            description="The source's settings as submitted through its announced form. Secret fields may carry the "
            "mask returned by the API to keep the stored value."
        ),
    ] = {}
