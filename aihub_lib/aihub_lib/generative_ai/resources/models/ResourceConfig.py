from pydantic import BaseModel, Field


class ResourceParameter(BaseModel):
    pass


class ResourceConfig(BaseModel):
    """
    Configuration for a multitude of online resources, identified by their name and their access url.

    ### Why ResourceConfig?
    An application may rely on a variety of services,
    each with different defaults or endpoints. ResourceConfig captures:
    - The model name
    - The base URL
    - Default parameters (via ModelParameter)

    This makes it easy to:
    - Inherit resource definitions
    - Merge per-request parameters with defaults.
    - Instantiate, pass or configure resources.
    """

    name: str = Field(..., description="The name of the model.")
    base_url: str = Field(..., description="The base URL of the model.")
    default_parameter: ResourceParameter = Field(
        ..., description="The default parameters for the model.", default_factory=lambda: ResourceParameter()
    )
