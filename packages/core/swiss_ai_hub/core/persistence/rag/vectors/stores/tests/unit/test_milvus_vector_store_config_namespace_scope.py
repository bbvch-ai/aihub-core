import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig


class TestNamespaceScope:
    """The scope must be explicit: an unset scope used to mean "everything", which nobody had chosen."""

    def test_named_namespaces_restrict_retrieval(self):
        config = MilvusVectorStoreConfig(collection_name="db", dimensions=8, index_namespaces=["reports"])
        assert config.namespace_filter == ["reports"]

    def test_all_namespaces_lifts_the_filter(self):
        config = MilvusVectorStoreConfig(collection_name="db", dimensions=8, all_namespaces=True)
        assert config.namespace_filter is None

    def test_an_empty_scope_is_rejected(self):
        with pytest.raises(ValidationError, match="at least one namespace"):
            MilvusVectorStoreConfig(collection_name="db", dimensions=8)

    def test_naming_namespaces_and_all_at_once_is_rejected(self):
        with pytest.raises(ValidationError, match="not both"):
            MilvusVectorStoreConfig(collection_name="db", dimensions=8, index_namespaces=["a"], all_namespaces=True)
