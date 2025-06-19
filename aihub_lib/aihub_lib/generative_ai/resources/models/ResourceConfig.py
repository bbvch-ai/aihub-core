from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Optional


class ResourceParameter(BaseModel):
    pass


class ResourceConfig(BaseModel):
    """
    Configuration for a multitude of online resources, identified by their name and their access URL.

    ### Why ResourceConfig?
    An application may rely on a variety of services,
    each with different defaults or endpoints. ResourceConfig captures:
    - The model name
    - The base URL
    - Default parameters (via ModelParameter)

    This makes it easy to:
    - Inherit resource definitions
    - Merge per-request parameters with defaults.
    - Instantiate, pass, or configure resources.
    """

    name: Annotated[str, Field(description="The name of the model.")]
    base_url: Annotated[str, Field(description="The base URL of the model.")]
    api_key: Annotated[
        Optional[str],
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
    ] = None

    # Using default_factory, so keeping Field() explicitly
    default_parameter: Annotated[
        ResourceParameter,
        Field(
            description="The default parameters for the model.",
        ),
    ] = ResourceParameter()
