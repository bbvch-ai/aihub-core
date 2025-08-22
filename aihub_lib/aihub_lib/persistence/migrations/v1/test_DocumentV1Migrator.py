"""
Simple, real-world tests for DocumentV1Migrator using actual MongoEngine entity structures.

These tests use actual MongoDB with clear before/after states based on real entity schemas,
making them easy to understand and maintain.
"""

from datetime import UTC, datetime
from typing import Any

from aihub_lib.persistence.migrations.tests.SimpleMigrationTest import SimpleMigrationTest
from aihub_lib.persistence.migrations.v1.DocumentV1Migrator import DocumentV1Migrator

# Use fixed datetime instances to avoid precision issues
FIXED_DATETIME_1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
FIXED_DATETIME_2 = datetime(2025, 1, 2, 12, 0, 0, tzinfo=UTC)


class TestDocumentV1MigratorRealistic(SimpleMigrationTest):
    """
    Realistic tests for DocumentV1Migrator using actual entity data structures.

    V1 migration adds schema_version=1 to all documents that don't have it.
    Uses real collections: users, agent_events, process_events
    """

    migration_class = DocumentV1Migrator

    # Real entity data based on actual MongoEngine schemas
    initial_state: dict[str, list[dict[str, Any]]] = {
        "users": [
            {
                # UserEntity fields without schema_version (pre-migration state)
                "id": "user-123-oid",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user", "admin"],
                "favorite_modules": [],
                "dashboard": {
                    # Empty dashboard for simplification
                    "minRow": 1,
                    "margin": 24,
                    "column": 4,
                    "cellHeight": 350,
                    "children": [],
                },
            },
            {
                "id": "user-456-oid",
                "name": "Bob Jones",
                "email": "bob@example.com",
                "profile_image": "https://example.com/avatar.jpg",
                "last_updated": FIXED_DATETIME_2,
                "roles": ["user"],
                "favorite_modules": ["chat", "search"],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
        ],
        "agent_events": [
            {
                # PersistedAgentEventEntity fields without schema_version
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-001",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {
                    "created_at": 1640995200000000000,
                    "content": "Agent started processing user query",
                    "metadata": {"source": "user_input"},
                },
                "event_parents": [],
                "created_at": 1640995200000000000,
            },
            {
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
                # PersistedProcessEventEntity fields without schema_version
                "process_class": "UserQueryProcess",
                "process_id": "process-123",
                "process_walkthrough_id": "walkthrough-abc",
                "event_id": "proc-event-001",
                "event_type": "control",
                "event_name": "ProcessStartEvent",
                "event_data": {
                    "created_at": 1640995300000000000,
                    "workflow": "user_query_processing",
                    "input_data": {"query": "What is AI?"},
                },
                "event_parents": [],
                "created_at": 1640995300000000000,
            }
        ],
    }

    expected_state_after_up: dict[str, list[dict[str, Any]]] = {
        "users": [
            {
                "schema_version": 1,  # Added by migration
                "id": "user-123-oid",
                "name": "Alice Smith",
                "email": "alice@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user", "admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            {
                "schema_version": 1,  # Added by migration
                "id": "user-456-oid",
                "name": "Bob Jones",
                "email": "bob@example.com",
                "profile_image": "https://example.com/avatar.jpg",
                "last_updated": FIXED_DATETIME_2,
                "roles": ["user"],
                "favorite_modules": ["chat", "search"],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
        ],
        "agent_events": [
            {
                "schema_version": 1,  # Added by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "thread_id": "thread-abc",
                "display_id": "display-xyz",
                "run_id": "run-001",
                "event_id": "event-001",
                "event_type": "control",
                "event_name": "StartEvent",
                "event_data": {
                    "created_at": 1640995200000000000,
                    "content": "Agent started processing user query",
                    "metadata": {"source": "user_input"},
                },
                "event_parents": [],
                "created_at": 1640995200000000000,
            },
            {
                "schema_version": 1,  # Added by migration
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
                "schema_version": 1,  # Added by migration
                "process_class": "UserQueryProcess",
                "process_id": "process-123",
                "process_walkthrough_id": "walkthrough-abc",
                "event_id": "proc-event-001",
                "event_type": "control",
                "event_name": "ProcessStartEvent",
                "event_data": {
                    "created_at": 1640995300000000000,
                    "workflow": "user_query_processing",
                    "input_data": {"query": "What is AI?"},
                },
                "event_parents": [],
                "created_at": 1640995300000000000,
            }
        ],
    }

    # After rollback, should match initial state (no schema_version fields)
    expected_state_after_down: dict[str, list[dict[str, Any]]] = initial_state


class TestDocumentV1MigratorMixedVersions(SimpleMigrationTest):
    """
    Test V1 migration with mixed documents - some already have schema_version, some don't.
    """

    migration_class = DocumentV1Migrator

    initial_state: dict[str, list[dict[str, Any]]] = {
        "users": [
            # User without schema_version (should be migrated)
            {
                "id": "user-new",
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # User already at v1 (should be left alone)
            {
                "schema_version": 1,
                "id": "user-v1",
                "name": "Diana Prince",
                "email": "diana@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # User already at v2 (should be left alone)
            {
                "schema_version": 2,
                "id": "user-v2",
                "name": "Bruce Wayne",
                "email": "bruce@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
        ]
    }

    expected_state_after_up: dict[str, list[dict[str, Any]]] = {
        "users": [
            # Was migrated from no version to v1
            {
                "schema_version": 1,  # Added by migration
                "id": "user-new",
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # Was already v1 (unchanged)
            {
                "schema_version": 1,
                "id": "user-v1",
                "name": "Diana Prince",
                "email": "diana@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # Was already v2 (unchanged)
            {
                "schema_version": 2,
                "id": "user-v2",
                "name": "Bruce Wayne",
                "email": "bruce@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
        ]
    }

    expected_state_after_down: dict[str, list[dict[str, Any]]] = {
        "users": [
            # V1 rollback removed schema_version
            {
                "id": "user-new",
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["user"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # Was v1, rollback removed schema_version
            {
                "id": "user-v1",
                "name": "Diana Prince",
                "email": "diana@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
            # Was v2, stays unchanged (rollback doesn't touch v2 docs)
            {
                "schema_version": 2,
                "id": "user-v2",
                "name": "Bruce Wayne",
                "email": "bruce@example.com",
                "profile_image": None,
                "last_updated": FIXED_DATETIME_1,
                "roles": ["admin"],
                "favorite_modules": [],
                "dashboard": {"minRow": 1, "margin": 24, "column": 4, "cellHeight": 350, "children": []},
            },
        ]
    }


class TestDocumentV1MigratorEmptyDatabase(SimpleMigrationTest):
    """
    Test V1 migration on empty database.
    """

    migration_class = DocumentV1Migrator

    # Empty database
    initial_state: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_up: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_down: dict[str, list[dict[str, Any]]] = {}
