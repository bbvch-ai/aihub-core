from typing import Annotated, Any

from pydantic import BaseModel, Field


class StructuredSourceState(BaseModel):
    """What survives between two syncs of one database: dlt's pipeline state and the scope it was built for."""

    scope_fingerprint: Annotated[
        str, Field(description="Fingerprint of the non-secret configuration the cursors were advanced under.")
    ]
    pipeline_state: Annotated[
        dict[str, Any], Field(description="dlt's state.json, which holds the incremental cursors.")
    ]
