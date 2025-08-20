from typing import Final

# Central schema version registry for the entire AI-Hub database.
#
# This module defines the current schema version that all documents
# in the system should conform to. When updating the schema, increment
# CURRENT_SCHEMA_VERSION and create a corresponding migration.
# This is THE source of truth for the current schema version
CURRENT_SCHEMA_VERSION: Final[int] = 2

SCHEMA_HISTORY = {
    1: "Initial schema version",
    2: (
        "Added root-level created_at to PersistedAgentEventEntity and "
        "PersistedProcessEventEntity for query optimization"
    ),
}
