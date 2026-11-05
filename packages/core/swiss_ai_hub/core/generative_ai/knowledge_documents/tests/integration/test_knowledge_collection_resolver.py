import uuid
from collections.abc import Iterator

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_not_found_error import (
    KnowledgeCollectionNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_resolver import (
    KnowledgeCollectionResolver,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity

pytestmark = pytest.mark.integration

_RUN = uuid.uuid4().hex[:8]
_BUCKET = f"kdocresolver{_RUN}"
_DB_NAME = f"kdocresolvervec{_RUN}"


@pytest.fixture(autouse=True)
def bucket() -> Iterator[None]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    created = BucketEntity.create_bucket(_BUCKET, db_name=_DB_NAME)
    yield
    created.delete()
    disconnect()


def test_a_reference_names_the_bucket_by_its_vector_collection_name() -> None:
    pair = KnowledgeCollectionResolver.pair_of(KnowledgeReference(database=_DB_NAME, namespace="finance"))

    assert pair == BucketNamespacePair(bucket_name=_BUCKET, namespace_name="finance")


def test_a_reference_to_a_gone_database_is_reported_as_not_found() -> None:
    reference = KnowledgeReference(database=f"gone{_RUN}", namespace="finance")
    with pytest.raises(KnowledgeCollectionNotFoundError, match="does not exist"):
        KnowledgeCollectionResolver.pair_of(reference)
