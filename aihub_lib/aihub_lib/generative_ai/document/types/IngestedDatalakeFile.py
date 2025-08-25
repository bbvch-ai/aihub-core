from typing import Annotated

from pydantic import Field

from aihub_lib.generative_ai.document.types.IngestedBase import IngestedBase


class IngestedDatalakeFile(IngestedBase):
    """
    Set of default metadata for a data lake file. A data lake file is a file that was uploaded to a data lake storage.
    """

    id: Annotated[str, Field(description="Unique identifier for the document.")]
