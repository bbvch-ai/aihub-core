from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class VectorStoreInput(PrimeVueElement):
    """
    A FormKit element for selecting a vector store collection, namespaces, and
    the metadata keys publishers are allowed to filter on at query time.

    This element renders as three controls:
    1. Database dropdown (loads from /api/v1/knowledge/databases)
    2. "All namespaces" switch, or a namespace multi-select populated from the selected database
    3. Free-form chips input for `allowed_metadata_filter_fields`

    The output matches the configurable fields of `MilvusVectorStoreConfig`:
    {
        "collection_name": str,
        "index_namespaces": list[str],
        "all_namespaces": bool,
        "allowed_metadata_filter_fields": list[str],
    }

    ### Form Duality
    When used with MilvusVectorStoreConfig, the form submission is validated
    directly into MilvusVectorStoreConfig (connection settings are read from
    MilvusSettings at runtime).

    ### Example Usage
    ```python
    from swiss_ai_hub.core.form.elements.vector_store_input import VectorStoreInput
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig

    class MyRetrieverConfig(Form):
        vector_store: Annotated[
            MilvusVectorStoreConfig | VectorStoreInput,
            Field(description="The vector store configuration"),
        ]

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
            allowed_metadata_filter_fields=["department", "year"],
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

    allowed_filter_fields_placeholder: Annotated[
        LocaleString | str | None,
        Field(
            description="Placeholder for the allowed metadata filter fields chips input.",
            alias="allowedFilterFieldsPlaceholder",
        ),
    ] = None

    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.database_placeholder, LocaleString):
            self_copy.database_placeholder = t.extract(self_copy.database_placeholder)
        if isinstance(self_copy.namespace_placeholder, LocaleString):
            self_copy.namespace_placeholder = t.extract(self_copy.namespace_placeholder)
        if isinstance(self_copy.allowed_filter_fields_placeholder, LocaleString):
            self_copy.allowed_filter_fields_placeholder = t.extract(self_copy.allowed_filter_fields_placeholder)
        return self_copy

    def validate_authorization(
        self,
        field_path: str,
        value: Any,
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> list[ConfigAuthorizationViolation]:
        """Named namespaces are checked one by one; ``all_namespaces`` needs a rule covering the whole database.

        An empty list without the flag is left to model validation, which rejects it.
        """
        if not isinstance(value, dict) or not isinstance(value.get("collection_name"), str):
            return []
        database: str = value["collection_name"]
        namespaces = value.get("index_namespaces") or []
        if not isinstance(namespaces, list):
            return []
        if value.get("all_namespaces") is True:
            if access_checker.has_access_to_all_knowledge_namespaces(database):
                return []
            return [
                ConfigAuthorizationViolation(
                    field=field_path,
                    resource_type="knowledge_database",
                    resource=database,
                    message=t("lib.common.authorization.no_access_whole_knowledge_database", name=database),
                )
            ]
        return [
            ConfigAuthorizationViolation(
                field=field_path,
                resource_type="knowledge_namespace",
                resource=f"{database}/{namespace}",
                message=t(
                    "lib.common.authorization.no_access_knowledge_namespace", database=database, namespace=namespace
                ),
            )
            for namespace in namespaces
            if isinstance(namespace, str) and not access_checker.has_access_to_knowledge_namespace(database, namespace)
        ]
