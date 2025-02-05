from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class EmbeddingsRequest(BaseModel):
    input: Union[str, List[str], List[int], List[List[int]]] = Field(
        ...,
        description="Input text to embed. Can be a string, array of strings, or arrays of tokens. Must not exceed max input tokens.",
    )
    model: str = Field(..., description="ID of the model to use for generating embeddings.")
    encoding_format: Optional[Literal["float", "base64"]] = Field(
        "float", description="Format of the returned embeddings. Defaults to 'float'."
    )
    dimensions: Optional[int] = Field(
        None, description="Number of dimensions for output embeddings. Supported in text-embedding-3 and later models."
    )
    user: Optional[str] = Field(None, description="A unique identifier for the end-user to monitor and detect abuse.")
