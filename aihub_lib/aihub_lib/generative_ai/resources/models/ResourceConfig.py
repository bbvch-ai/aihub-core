from pydantic import BaseModel, Field


class ResourceParameter(BaseModel):
    pass


class ResourceConfig(BaseModel):
    """
    Configuration for a Language Model or embedding, including defaults and endpoints.

    ### Why LLMConfig?
    An application may rely on a variety of LLM backends (like OpenAI models or Azure endpoints),
    each with different defaults or endpoints. LLMConfig captures:
    - The model name
    - The base URL
    - Default parameters (via ModelParameter)

    This makes it easy to:
    - Switch between models without changing code.
    - Merge per-request parameters with defaults.
    - Instantiate LLM or embedding objects for llama_index consistently.
    """

    name: str = Field(..., description="The name of the model.")
    base_url: str = Field(..., description="The base URL of the model.")
    default_parameter: ResourceParameter = Field(..., description="The default parameters for the model.")
