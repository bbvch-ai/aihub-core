from typing import Annotated

from fastapi import Query

PageNumber = Annotated[
    int,
    Query(
        title="Page Number",
        description="Page number to retrieve (starting from 1)",
        ge=1,
    ),
]
