# MongoDB Migration System

Production-ready migration framework for safely evolving MongoDB schemas in the AI-Hub.

## 🎯 Core Principle

**Every migration MUST have comprehensive tests before merging to production.**  
See the [Testing Guide](tests/README.md) for detailed testing methodologies and frameworks.

## 📁 Directory Structure

```
migrations/
├── DocumentMigrator.py        # Abstract migration interface
├── migrate.py                  # Migration orchestration system  
├── v1/                        # Version 1 migration (schema_version field)
│   ├── DocumentV1Migrator.py   # V1 implementation  
│   └── test_DocumentV1Migrator.py  # V1 tests using SimpleMigrationTest
├── v2/                        # Version 2 migration (created_at optimization)
│   ├── DocumentV2Migrator.py   # V2 implementation
│   └── test_DocumentV2Migrator.py  # V2 tests using SimpleMigrationTest
├── v3/                        # Future migrations follow same pattern
│   ├── DocumentV3Migrator.py
│   └── test_DocumentV3Migrator.py
└── tests/                     # Testing framework and system tests
    ├── README.md               # 📖 Testing methodologies & frameworks
    ├── SimpleMigrationTest.py  # Recommended testing base class
    └── test_migration_orchestrator.py  # System-level tests
```

## 🏗️ Migration Architecture

### DocumentMigrator Interface

All migrations inherit from the `DocumentMigrator` abstract base class:

```python
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from pymongo.asynchronous.database import AsyncDatabase

class DocumentMigrator(ABC):
    version: ClassVar[int]              # Migration version number
    description: ClassVar[str]          # Human-readable description
    affected_collections: ClassVar[list[str]]  # Collections modified

    @abstractmethod
    async def migrate_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Apply migration to a specific collection."""
    
    @abstractmethod  
    async def rollback_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Rollback migration for a specific collection."""
```

### Migration Orchestration

The system uses `migrate.py` to orchestrate migrations:

- **Automatic Discovery**: Migrations are auto-registered based on version numbers
- **Sequential Execution**: Migrations run in version order (1→2→3...)
- **Atomic Operations**: Each migration uses MongoDB transactions for consistency
- **Progress Tracking**: Detailed logging and progress reporting
- **Rollback Support**: Complete reversion capability for disaster recovery

## 🛠️ Creating a New Migration

### Step 1: Create Migration Implementation

```bash
# Create version directory
mkdir -p aihub_lib/persistence/migrations/v3
```

**Create `v3/DocumentV3Migrator.py`**:

```python
"""
Migration V3: Add advanced indexing for performance optimization.
"""

from typing import Any, ClassVar
from pymongo.asynchronous.database import AsyncDatabase
from aihub_lib.persistence.migrations.DocumentMigrator import DocumentMigrator

class DocumentV3Migrator(DocumentMigrator):
    """
    V3 Migration: Optimizes query performance with compound indices.
    
    Changes:
    1. Updates schema_version: 2 → 3 
    2. Adds compound indices for common query patterns
    3. Optimizes existing indices for better performance
    """
    
    version: ClassVar[int] = 3
    description: ClassVar[str] = "Add compound indices for query optimization"
    affected_collections: ClassVar[list[str]] = ["agent_events", "process_events"]

    async def migrate_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Apply V3 migration to collection."""
        collection = db[collection_name]
        
        # Update schema version: v2 → v3
        result = await collection.update_many(
            {"schema_version": 2},
            [{"$set": {"schema_version": 3}}]
        )
        
        # Add performance indices
        await collection.create_index([("agent_id", 1), ("created_at", -1)])
        await collection.create_index([("thread_id", 1), ("event_type", 1)])
        
        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }

    async def rollback_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Rollback V3 migration.""" 
        collection = db[collection_name]
        
        # Revert schema version: v3 → v2
        result = await collection.update_many(
            {"schema_version": 3},
            [{"$set": {"schema_version": 2}}]
        )
        
        # Remove indices created in migration
        try:
            await collection.drop_index([("agent_id", 1), ("created_at", -1)])
            await collection.drop_index([("thread_id", 1), ("event_type", 1)])
        except Exception as e:
            logger.warning(f"Could not drop indices: {e}")
            
        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }
```

### Step 2: Register Migration

Update `migrate.py` to include the new migration:

```python
from aihub_lib.persistence.migrations.v1.DocumentV1Migrator import DocumentV1Migrator
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.persistence.migrations.v3.DocumentV3Migrator import DocumentV3Migrator

# Migrations are auto-discovered based on version order
MIGRATIONS: list[type[DocumentMigrator]] = [
    DocumentV1Migrator,  # v1: Add schema_version field
    DocumentV2Migrator,  # v2: Add root-level created_at field  
    DocumentV3Migrator,  # v3: Add compound indices
]
```

### Step 3: Create Comprehensive Tests

**Create `v3/test_DocumentV3Migrator.py`** following the [SimpleMigrationTest framework](tests/README.md):

```python
"""
Tests for DocumentV3Migrator using SimpleMigrationTest framework.
"""

from aihub_lib.persistence.migrations.tests.SimpleMigrationTest import SimpleMigrationTest
from aihub_lib.persistence.migrations.v3.DocumentV3Migrator import DocumentV3Migrator

class TestDocumentV3MigratorRealistic(SimpleMigrationTest):
    """Test V3 migration with realistic data scenarios."""
    
    migration_class = DocumentV3Migrator
    
    initial_state = {
        "agent_events": [
            {
                "schema_version": 2,  # V2 state
                "agent_class": "ChatAgent",
                "agent_id": "agent-123", 
                "created_at": 1640995200000000000,
                # ... realistic document structure
            }
        ]
    }
    
    expected_state_after_up = {
        "agent_events": [
            {
                "schema_version": 3,  # Updated by V3 migration
                "agent_class": "ChatAgent", 
                "agent_id": "agent-123",
                "created_at": 1640995200000000000,
                # ... same data, version updated + indices created
            }
        ]
    }
    
    expected_state_after_down = initial_state
    
# Additional test classes for edge cases, mixed versions, etc.
```

**✅ Testing is handled by the SimpleMigrationTest framework** - see [Testing Guide](tests/README.md) for details.

### Step 4: Validation

```bash
# Run new migration tests  
pytest aihub_lib/persistence/migrations/v3/ -v

# Run all migration tests to ensure no regressions
pytest aihub_lib/persistence/migrations/ -v
```

## 🚀 Production Deployment

### Automatic Migration Execution

Migrations run automatically on API startup:

```python
# In aihub_api startup lifecycle
from aihub_lib.persistence.migrations.MigrationOrchestrator import run_migrations


async def startup():
    await MigrationOrchestrator.run_migrations(
        connection_string=MongoSettings().CONNECTION_STRING.get_secret_value(),
        db_name="aihub"
    )
```

### Migration Process

1. **Database Connection**: Establishes secure connection to MongoDB
2. **Current Version Detection**: Reads `schema_version` from existing documents  
3. **Sequential Execution**: Runs migrations in order (v1→v2→v3...)
4. **Transaction Safety**: Each migration runs in MongoDB transaction
5. **Progress Logging**: Detailed logs for monitoring and debugging
6. **Error Handling**: Graceful failure with rollback capabilities

### Monitoring & Rollback

```bash
# Monitor migration logs
tail -f /var/log/aihub/migrations.log

# Manual rollback (if needed)
python -m aihub_lib.persistence.migrations.migrate --rollback --to-version=2
```

## 📋 Development Checklist

Before submitting a migration PR:

### Migration Implementation
- [ ] **Inherits from DocumentMigrator**: Proper interface implementation
- [ ] **Version & Description**: Clear version number and human-readable description  
- [ ] **Affected Collections**: List all collections modified by migration
- [ ] **Atomic Operations**: Uses MongoDB aggregation pipelines for consistency
- [ ] **Index Management**: Creates indices in up(), drops in down()
- [ ] **Error Handling**: Graceful handling of edge cases and failures

### Testing Requirements  
- [ ] **SimpleMigrationTest Implementation**: Uses recommended testing framework
- [ ] **Realistic Test Data**: Based on actual MongoEngine entity schemas
- [ ] **Multiple Scenarios**: Realistic data, mixed versions, edge cases, empty database
- [ ] **All Tests Pass**: 15 comprehensive tests per migration (up/down/idempotency/cycles/empty)

### System Integration
- [ ] **Registration**: Added to `MIGRATIONS` list in correct version order
- [ ] **No Regressions**: All existing migration tests still pass
- [ ] **Documentation**: Updated relevant documentation

## 🔍 Best Practices

### Migration Design
- **Incremental Changes**: Keep migrations small and focused
- **Backward Compatible**: Ensure old code can still read new schema during deployment
- **Index Strategy**: Create indices that optimize common query patterns  
- **Data Validation**: Validate document structure before and after migration
- **Performance Testing**: Test with realistic data volumes

### Error Recovery
- **Idempotent Operations**: Migrations can be safely run multiple times
- **Partial Failure Handling**: Graceful handling of interrupted migrations
- **Rollback Testing**: Verify rollback restores exact original state
- **Data Integrity**: Ensure no data loss during migration or rollback

### Security & Compliance
- **Connection Security**: Use secure MongoDB connections with authentication
- **Audit Logging**: Log all migration activities for compliance
- **Data Privacy**: Ensure migrations don't expose sensitive data
- **Access Control**: Restrict migration execution to authorized systems

## 🔗 Related Documentation

- **[Testing Guide](tests/README.md)** - Comprehensive testing methodologies and SimpleMigrationTest framework
- **[AI-Hub Library Documentation](../../README.md)** - Overall library architecture and patterns  
- **[MongoDB Aggregation Pipeline](https://docs.mongodb.com/manual/core/aggregation-pipeline/)** - MongoDB documentation for atomic operations