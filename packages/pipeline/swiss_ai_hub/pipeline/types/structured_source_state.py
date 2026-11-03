from typing import Annotated, Any

from pydantic import BaseModel, Field


class StructuredSourceState(BaseModel):
    """What survives between two syncs of one database: dlt's pipeline state, the scope it was built for, and the
    records the last run listed without a file."""

    scope_fingerprint: Annotated[
        str, Field(description="Fingerprint of the non-secret configuration the cursors were advanced under.")
    ]
    pipeline_state: Annotated[
        dict[str, Any], Field(description="dlt's state.json, which holds the incremental cursors.")
    ]
    missing_keys: Annotated[
        list[str],
        Field(
            description="Keys the last run listed without a file. Missing again in the next run means the cursor "
            "passed them; missing once is usually a record created while that run was between its sync and its "
            "listing, which the next run fetches."
        ),
    ] = []
