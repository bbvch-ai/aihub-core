from pymilvus import MilvusClient
from swiss_ai_hub.core.infrastructure import MilvusSettings


def build_milvus_client() -> MilvusClient:
    """A bare Milvus client for operations on a collection that already exists.

    Deliberately not ``MilvusVectorStoreResource`` / ``create_milvus_vector_store``: those create the collection
    when it is missing, which is the wrong behaviour for a delete, and they build a llama-index wrapper whose
    only delete path is by document id. Teardown removes a whole namespace in one filtered call instead.
    """
    milvus_settings = MilvusSettings()
    return MilvusClient(uri=milvus_settings.URL, token=milvus_settings.get_token())
