"""
Simple, real-world tests for DocumentV2Migrator using actual MongoEngine entity structures.

These tests use actual MongoDB with clear before/after states based on real entity schemas,
making them easy to understand and maintain.
"""

from datetime import UTC, datetime
from typing import Any

from aihub_lib.persistence.migrations.tests.SimpleMigrationTest import SimpleMigrationTest
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator

# Use fixed datetime instances to avoid precision issues
FIXED_DATETIME_1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
FIXED_DATETIME_2 = datetime(2025, 1, 2, 12, 0, 0, tzinfo=UTC)


class TestDocumentV2MigratorRealistic(SimpleMigrationTest):
    """
    Realistic tests for DocumentV2Migrator using actual entity data structures.

    V2 migration:
    1. Updates all collections to schema_version=2
    2. Adds root-level created_at field to event collections (agent_events, process_events)
    """

    migration_class = DocumentV2Migrator

    # Real entity data based on actual MongoEngine schemas - all at v1
    initial_state: dict[str, list[dict[str, Any]]] = {
        "users": [
            {
                # UserEntity at v1 (only gets schema version update)
                "schema_version": 1,
                "id": "user-123-oid",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user", "admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            }
        ],
        "agent_events": [
            {
                # PersistedAgentEventEntity at v1 - gets created_at field added to root
                "schema_version": 1,
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-001",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {
                    "created_at": 1640995200000000000,  # This gets copied to root level
                    "content": "Agent started processing user query",
                    "metadata": {"source": "user_input"},
                },
                "event_parents": [],
                "created_at": 1640995200000000000,  # Already exists, but migration still processes it
            },
            {
                "schema_version": 1,
                "agent_class": "RAGAgent",
                "agent_id": "agent-456",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-002",
                "event_type": "display",
                "event_name": "ChunkEvent",
                "event_data": {
                    "created_at": 1640995260000000000,
                    "content": "Retrieved relevant documents...",
                    "chunk_id": 1,
                },
                "event_parents": ["StartEvent"],
                "created_at": 1640995260000000000,
            },
        ],
        "process_events": [
            {
                # PersistedProcessEventEntity at v1 - gets created_at field added to root
                "schema_version": 1,
                "process_class": "UserQueryProcess",
                "process_id": "process-123",
                "process_walkthrough_id": "walkthrough-abc",
                "event_id": "proc-event-001",
                "event_type": "control",
                "event_name": "ProcessStartEvent",
                "event_data": {
                    "created_at": 1640995300000000000,  # This gets copied to root level
                    "workflow": "user_query_processing",
                    "input_data": {"query": "What is AI?"},
                },
                "event_parents": [],
                "created_at": 1640995300000000000,  # Already exists, but migration processes it
            }
        ],
    }

    expected_state_after_up: dict[str, list[dict[str, Any]]] = {
        "users": [
            {
                # UserEntity: Only schema_version updated to v2
                "schema_version": 2,  # Updated by migration
                "id": "user-123-oid",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user", "admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            }
        ],
        "agent_events": [
            {
                # PersistedAgentEventEntity: Schema version updated + created_at optimization
                "schema_version": 2,  # Updated by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-001",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {
                    "created_at": 1640995200000000000,  # Remains in event_data
                    "content": "Agent started processing user query",
                    "metadata": {"source": "user_input"},
                },
                "event_parents": [],
                "created_at": 1640995200000000000,  # Root level created_at (optimized for queries)
            },
            {
                "schema_version": 2,  # Updated by migration
                "agent_class": "RAGAgent",
                "agent_id": "agent-456",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-002",
                "event_type": "display",
                "event_name": "ChunkEvent",
                "event_data": {
                    "created_at": 1640995260000000000,
                    "content": "Retrieved relevant documents...",
                    "chunk_id": 1,
                },
                "event_parents": ["StartEvent"],
                "created_at": 1640995260000000000,  # Root level created_at (optimized for queries)
            },
        ],
        "process_events": [
            {
                # PersistedProcessEventEntity: Schema version updated + created_at optimization
                "schema_version": 2,  # Updated by migration
                "process_class": "UserQueryProcess",
                "process_id": "process-123",
                "process_walkthrough_id": "walkthrough-abc",
                "event_id": "proc-event-001",
                "event_type": "control",
                "event_name": "ProcessStartEvent",
                "event_data": {
                    "created_at": 1640995300000000000,  # Remains in event_data
                    "workflow": "user_query_processing",
                    "input_data": {"query": "What is AI?"},
                },
                "event_parents": [],
                "created_at": 1640995300000000000,  # Root level created_at (optimized for queries)
            }
        ],
    }

    expected_state_after_down: dict[str, list[dict[str, Any]]] = {
        "users": [
            {
                # UserEntity: Schema version rolled back to v1
                "schema_version": 1,  # Rolled back by migration
                "id": "user-123-oid",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user", "admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            }
        ],
        "agent_events": [
            {
                # PersistedAgentEventEntity: Schema version rolled back, root created_at removed
                "schema_version": 1,  # Rolled back by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-001",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {
                    "created_at": 1640995200000000000,  # Preserved in event_data
                    "content": "Agent started processing user query",
                    "metadata": {"source": "user_input"},
                },
                "event_parents": [],
                # Root created_at field removed by rollback
            },
            {
                "schema_version": 1,  # Rolled back by migration
                "agent_class": "RAGAgent",
                "agent_id": "agent-456",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-002",
                "event_type": "display",
                "event_name": "ChunkEvent",
                "event_data": {
                    "created_at": 1640995260000000000,
                    "content": "Retrieved relevant documents...",
                    "chunk_id": 1,
                },
                "event_parents": ["StartEvent"],
                # Root created_at field removed by rollback
            },
        ],
        "process_events": [
            {
                # PersistedProcessEventEntity: Schema version rolled back, root created_at removed
                "schema_version": 1,  # Rolled back by migration
                "process_class": "UserQueryProcess",
                "process_id": "process-123",
                "process_walkthrough_id": "walkthrough-abc",
                "event_id": "proc-event-001",
                "event_type": "control",
                "event_name": "ProcessStartEvent",
                "event_data": {
                    "created_at": 1640995300000000000,  # Preserved in event_data
                    "workflow": "user_query_processing",
                    "input_data": {"query": "What is AI?"},
                },
                "event_parents": [],
                # Root created_at field removed by rollback
            }
        ],
    }


class TestDocumentV2MigratorMixedVersions(SimpleMigrationTest):
    """
    Test V2 migration with mixed documents - some at v1, some already at v2 or higher.
    """

    migration_class = DocumentV2Migrator

    initial_state: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            # Document at v1 (should be migrated)
            {
                "schema_version": 1,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v1",
                "thread_id": "thread-1",
                "display_id": "display-1",
                "run_id": "run-1",
                "event_id": "event-v1",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995200000000000, "content": "V1 document"},
                "event_parents": [],
                "created_at": 1640995200000000000,
            },
            # Document already at v2 (should be left alone)
            {
                "schema_version": 2,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v2",
                "thread_id": "thread-2",
                "display_id": "display-2",
                "run_id": "run-2",
                "event_id": "event-v2",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995260000000000, "content": "V2 document"},
                "event_parents": [],
                "created_at": 1640995260000000000,
            },
            # Document at v3 (should be left alone)
            {
                "schema_version": 3,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v3",
                "thread_id": "thread-3",
                "display_id": "display-3",
                "run_id": "run-3",
                "event_id": "event-v3",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995320000000000, "content": "V3 document"},
                "event_parents": [],
                "created_at": 1640995320000000000,
            },
        ]
    }

    expected_state_after_up: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            # Was migrated from v1 to v2
            {
                "schema_version": 2,  # Updated by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-v1",
                "thread_id": "thread-1",
                "display_id": "display-1",
                "run_id": "run-1",
                "event_id": "event-v1",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995200000000000, "content": "V1 document"},
                "event_parents": [],
                "created_at": 1640995200000000000,
            },
            # Was already v2 (unchanged)
            {
                "schema_version": 2,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v2",
                "thread_id": "thread-2",
                "display_id": "display-2",
                "run_id": "run-2",
                "event_id": "event-v2",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995260000000000, "content": "V2 document"},
                "event_parents": [],
                "created_at": 1640995260000000000,
            },
            # Was v3 (unchanged)
            {
                "schema_version": 3,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v3",
                "thread_id": "thread-3",
                "display_id": "display-3",
                "run_id": "run-3",
                "event_id": "event-v3",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995320000000000, "content": "V3 document"},
                "event_parents": [],
                "created_at": 1640995320000000000,
            },
        ]
    }

    expected_state_after_down: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            # V2 rollback to v1
            {
                "schema_version": 1,  # Rolled back by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-v1",
                "thread_id": "thread-1",
                "display_id": "display-1",
                "run_id": "run-1",
                "event_id": "event-v1",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995200000000000, "content": "V1 document"},
                "event_parents": [],
                # Root created_at field removed by rollback
            },
            # Was v2, rollback to v1
            {
                "schema_version": 1,  # Rolled back by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-v2",
                "thread_id": "thread-2",
                "display_id": "display-2",
                "run_id": "run-2",
                "event_id": "event-v2",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995260000000000, "content": "V2 document"},
                "event_parents": [],
                # Root created_at field removed by rollback
            },
            # Was v3, stays unchanged (rollback doesn't touch v3 docs)
            {
                "schema_version": 3,
                "agent_class": "ChatAgent",
                "agent_id": "agent-v3",
                "thread_id": "thread-3",
                "display_id": "display-3",
                "run_id": "run-3",
                "event_id": "event-v3",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {"created_at": 1640995320000000000, "content": "V3 document"},
                "event_parents": [],
                "created_at": 1640995320000000000,
            },
        ]
    }


class TestDocumentV2MigratorEmptyDatabase(SimpleMigrationTest):
    """
    Test V2 migration on empty database.
    """

    migration_class = DocumentV2Migrator

    # Empty database
    initial_state: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_up: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_down: dict[str, list[dict[str, Any]]] = {}
