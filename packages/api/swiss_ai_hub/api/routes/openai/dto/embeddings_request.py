from typing import Annotated, Literal

from pydantic import BaseModel, Field


class EmbeddingsRequest(BaseModel):
    input: Annotated[
        str | list[str] | list[int] | list[list[int]],
        Field(
            description="Input text to embed. Can be a string, array of strings, or arrays of tokens. "
            "Must not exceed max input tokens."
        ),
    ]

    model: Annotated[str, Field(description="ID of the model to use for generating embeddings.")]

    encoding_format: Annotated[
        Literal["float", "base64"] | None,
        Field(description="Format of the returned embeddings. Defaults to 'float'."),
    ] = "float"

    dimensions: Annotated[
        int | None,
        Field(
            description="Number of dimensions for output embeddings. Supported in text-embedding-3 and later models."
        ),
    ] = None

    user: Annotated[
        str | None, Field(description="A unique identifier for the end-user to monitor and detect abuse.")
    ] = None
