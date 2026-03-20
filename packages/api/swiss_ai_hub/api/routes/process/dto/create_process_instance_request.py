from typing import Annotated, Any

from pydantic import BaseModel, Field


class CreateProcessInstanceRequest(BaseModel):
    """
    Request body for creating a new process instance.
    The process_class is provided in the URL path, not in the request body.
    """

    process_id: Annotated[
        str,
        Field(
            description="Unique identifier for the process instance. Must be URL-safe.",
            pattern=r"^[a-z0-9_-]+$",
            min_length=1,
            max_length=100,
        ),
    ]
    configuration: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="The full configuration values including name, description, icon, and runtime settings. "
            "Keys should match the 'name' fields from the process's form elements.",
        ),
    ]
