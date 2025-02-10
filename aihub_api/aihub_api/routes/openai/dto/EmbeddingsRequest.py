from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class EmbeddingsRequest(BaseModel):
    input: Annotated[
        Union[str, List[str], List[int], List[List[int]]],
        Field(
            description="Input text to embed. Can be a string, array of strings, or arrays of tokens. Must not exceed max input tokens."
        ),
    ]

    model: Annotated[str, Field(description="ID of the model to use for generating embeddings.")]

    encoding_format: Annotated[
        Optional[Literal["float", "base64"]],
        Field(description="Format of the returned embeddings. Defaults to 'float'."),
    ] = "float"

    dimensions: Annotated[
        Optional[int],
        Field(
            description="Number of dimensions for output embeddings. Supported in text-embedding-3 and later models."
        ),
    ] = None

    user: Annotated[
        Optional[str], Field(description="A unique identifier for the end-user to monitor and detect abuse.")
    ] = None
