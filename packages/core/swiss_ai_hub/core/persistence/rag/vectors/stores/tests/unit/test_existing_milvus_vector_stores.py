"""Reading a knowledge database's vectors never creates its collection, and builds each store once."""

from unittest.mock import MagicMock

import pytest
from llama_index.vector_stores.milvus import IndexManagement

from swiss_ai_hub.core.persistence.rag.vectors.stores import existing_milvus_vector_stores
from swiss_ai_hub.core.persistence.rag.vectors.stores.existing_milvus_vector_stores import ExistingMilvusVectorStores


@pytest.fixture
def milvus(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    client = MagicMock()
    store_class = MagicMock()
    settings = MagicMock(URL="http://milvus:19530", DIMENSION=1024)
    settings.get_token.return_value = None
    monkeypatch.setattr(existing_milvus_vector_stores, "MilvusClient", MagicMock(return_value=client))
    monkeypatch.setattr(existing_milvus_vector_stores, "MilvusSettings", MagicMock(return_value=settings))
    monkeypatch.setattr(existing_milvus_vector_stores, "PartitionAwareMilvusVectorStore", store_class)
    monkeypatch.setattr(ExistingMilvusVectorStores, "_client", None)
    monkeypatch.setattr(ExistingMilvusVectorStores, "_stores", {})
    return client, store_class


def test_a_missing_collection_is_reported_as_none_and_never_created(milvus: tuple[MagicMock, MagicMock]) -> None:
    client, store_class = milvus
    client.has_collection.return_value = False

    assert ExistingMilvusVectorStores.find("tenant_db") is None

    client.create_collection.assert_not_called()
    store_class.assert_not_called()


def test_an_existing_collections_store_is_built_once_without_index_checks(milvus: tuple[MagicMock, MagicMock]) -> None:
    client, store_class = milvus
    client.has_collection.return_value = True

    first = ExistingMilvusVectorStores.find("tenant_db")
    second = ExistingMilvusVectorStores.find("tenant_db")

    assert first is second is store_class.return_value
    store_class.assert_called_once()
    built = store_class.call_args.kwargs
    assert (built["client"], built["collection_name"]) == (client, "tenant_db")
    assert (built["index_management"], built["use_async_client"]) == (IndexManagement.NO_VALIDATION, False)


def test_a_dropped_collection_is_forgotten(milvus: tuple[MagicMock, MagicMock]) -> None:
    client, store_class = milvus
    client.has_collection.return_value = True
    ExistingMilvusVectorStores.find("tenant_db")
    client.has_collection.return_value = False

    assert ExistingMilvusVectorStores.find("tenant_db") is None
    assert "tenant_db" not in ExistingMilvusVectorStores._stores
