from typing import Annotated

from fastapi import Query

PageSize = Annotated[
    int,
    Query(
        title="Page Size",
        description="Number of items per page (maximum 100)",
        ge=1,
        le=100,
    ),
]
