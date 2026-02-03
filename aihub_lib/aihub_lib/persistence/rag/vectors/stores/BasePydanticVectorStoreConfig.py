import abc
from typing import Annotated

from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.Form import Form


class BasePydanticVectorStoreConfig(Form, abc.ABC):
    """
    Base configuration for vector stores.

    Supports duality pattern for form rendering and data validation.
    """

    dimensions: Annotated[
        int | InputNumber,
        Field(description="Dimensions of the embeddings in the vector store"),
    ]

    @abc.abstractmethod
    def to_llama_index(self) -> BasePydanticVectorStore:
        pass

    @classmethod
    def _dimensions_input(cls) -> InputNumber:
        """Shared input element for dimensions field used by subclasses."""
        return InputNumber(
            label=LocaleString.from_i18n_path("lib.milvus.base.dimensions.label"),
            help=LocaleString.from_i18n_path("lib.milvus.base.dimensions.help"),
            min=1,
            step=1,
        )
