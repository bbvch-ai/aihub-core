from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.form.base.PrimeVueElement import PrimeVueElement


class VectorStoreInput(PrimeVueElement):
    """
        A FormKit element for selecting a vector store collection and namespaces.

        This element renders as a cascading selection:
        1. Database dropdown (loads from /api/v1/knowledge/databases)
        2. Namespace multi-select (populated based on selected database)

        The output is a structured object containing both the collection name and
        the selected namespaces, matching the MilvusVectorStoreConfig fields:
        {"collection_name": str, "index_namespaces": list[str]}

        ### Form Duality
        When used with MilvusVectorStoreConfig, the form submission is validated
        directly into MilvusVectorStoreConfig (connection settings are read from
        MilvusSettings at runtime).

        ### Example Usage
        ```python
        from swiss_ai_hub.core.nats.events.form.elements.VectorStoreInput import VectorStoreInput
        from swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig

        class MyRetrieverConfig(Form):
            vector_store: Annotated[
                MilvusVectorStoreConfig | VectorStoreInput,
                Field(description="The vector store configuration"),
            ]
    reranking_model
        # Form mode - for rendering:
        config = MyRetrieverConfig(
            vector_store=VectorStoreInput(
                label=LocaleString(en="Vector Store", de="Vektorspeicher"),
            ),
        )

        # Data mode - from submission (Pydantic validates into MilvusVectorStoreConfig):
        config = MyRetrieverConfig(
            vector_store=MilvusVectorStoreConfig(
                collection_name="my-database",
                index_namespaces=["namespace1", "namespace2"],
            ),
        )
        ```
    """

    formkit: Annotated[
        Literal["vectorStoreInput"],
        Field(description="Vector store input element."),
    ] = "vectorStoreInput"

    database_placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for database select", alias="databasePlaceholder"),
    ] = None

    namespace_placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for namespace select", alias="namespacePlaceholder"),
    ] = None

    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.database_placeholder, LocaleString):
            self_copy.database_placeholder = t.extract(self_copy.database_placeholder)
        if isinstance(self_copy.namespace_placeholder, LocaleString):
            self_copy.namespace_placeholder = t.extract(self_copy.namespace_placeholder)
        return self_copy
