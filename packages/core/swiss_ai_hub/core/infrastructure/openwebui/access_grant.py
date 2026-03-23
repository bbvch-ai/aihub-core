from typing import Annotated

from pydantic import BaseModel, Field


class AccessGrant(BaseModel):
    """A single access grant for an OpenWebUI workspace model."""

    principal_type: Annotated[str, Field(description="Type of principal (e.g. 'group')")]
    principal_id: Annotated[str, Field(description="ID of the principal in OpenWebUI")]
    permission: Annotated[str, Field(description="Permission level (e.g. 'read')")]
