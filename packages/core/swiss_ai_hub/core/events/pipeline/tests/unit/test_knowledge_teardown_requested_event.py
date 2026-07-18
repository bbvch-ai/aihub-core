from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.events.pipeline.knowledge_teardown_requested_event import KnowledgeTeardownRequestedEvent


def test_for_database_carries_only_the_bucket_scoped_fields() -> None:
    event = KnowledgeTeardownRequestedEvent.for_database(
        bucket_id="bucket-1", bucket_name="tenant-bucket", db_name="tenant_db"
    )

    assert event.teardown_type == "database"
    assert event.bucket_id == "bucket-1"
    assert event.bucket_name == "tenant-bucket"
    assert event.db_name == "tenant_db"
    assert event.namespace_id is None
    assert event.namespace_name is None
    assert event.folder_name is None


def test_for_namespace_carries_the_namespace_scoped_fields() -> None:
    event = KnowledgeTeardownRequestedEvent.for_namespace(
        bucket_id="bucket-1",
        bucket_name="tenant-bucket",
        db_name="tenant_db",
        namespace_id="ns-1",
        namespace_name="reports",
        folder_name="reports",
    )

    assert event.teardown_type == "namespace"
    assert event.namespace_id == "ns-1"
    assert event.namespace_name == "reports"
    assert event.folder_name == "reports"


def test_round_trips_through_polymorphic_deserialization() -> None:
    """The pipeline consumer relies on the registry resolving the concrete class off the wire."""
    event = KnowledgeTeardownRequestedEvent.for_namespace(
        bucket_id="bucket-1",
        bucket_name="tenant-bucket",
        db_name="tenant_db",
        namespace_id="ns-1",
        namespace_name="reports",
        folder_name="reports",
    )

    restored = BaseEvent.deserialize_event(event.model_dump_json())

    assert isinstance(restored, KnowledgeTeardownRequestedEvent)
    assert restored.teardown_type == "namespace"
    assert restored.db_name == "tenant_db"
    assert restored.folder_name == "reports"
