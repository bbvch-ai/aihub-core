# MongoDB Migration System

Production-ready migration framework for safely evolving MongoDB schemas in the AI-Hub.

## 🎯 Core Principle

**Every migration MUST have comprehensive tests before merging to production.**

## 📁 Directory Structure

```
migrations/
├── base.py                     # Abstract migration interface
├── migrate.py                  # Migration orchestration system  
├── v2/                        # Version 2 migration
│   ├── DocumentV2Migrator.py   # V2 migration implementation
│   ├── test_DocumentV2Migrator.py  # 🚨 MANDATORY V2-specific tests
│   └── __init__.py
├── v3/                        # Future version 3 migration
│   ├── DocumentV3Migrator.py   # V3 migration implementation
│   ├── test_DocumentV3Migrator.py  # 🚨 MANDATORY V3-specific tests
│   └── __init__.py
└── tests/                     # General framework tests
    ├── test_migration_orchestrator.py  # Orchestration tests
    ├── test_simple_migration.py        # Framework validation tests
    └── run_migration_tests.py          # Test runner with validation
```

## 🚨 **PR Requirements**

### For New Migrations (Mandatory)

Before any migration PR is merged, it **MUST** include:

1. **Migration Implementation** (`vX/DocumentVXMigrator.py`)
   - Inherits from `DocumentMigration`
   - Implements `up()` and `down()` methods
   - Uses MongoDB aggregation pipelines for atomic operations
   - Creates optimized indices for performance

2. **Comprehensive Tests** (`vX/test_DocumentVXMigrator.py`)
   - **Properties Tests**: Version, description, affected collections
   - **Mock Tests**: Database operation validation without real MongoDB
   - **Integration Tests**: Real MongoDB with realistic data scenarios
   - **Edge Case Tests**: Missing fields, malformed data, error conditions  
   - **Performance Tests**: Large dataset migration validation
   - **Rollback Tests**: Complete reversion validation

3. **Registration** (Update `migrate.py`)
   - Add new migrator to `MIGRATIONS` list in version order

### Test Categories

#### 1. **Version-Specific Tests** (`vX/test_DocumentVXMigrator.py`)
- **Purpose**: Test the specific migration logic and requirements
- **Scope**: Only tests for that particular migration version
- **Requirements**: MANDATORY for every new migration
- **Coverage**: 
  - Migration-specific data transformations
  - Version-specific index creation/removal
  - Real integration scenarios with realistic data
  - Performance with large datasets
  - Rollback data integrity

#### 2. **Framework Tests** (`tests/`)
- **Purpose**: Test the general migration system and orchestration
- **Scope**: Framework-wide functionality that works with any migration
- **Coverage**:
  - Migration registration and discovery
  - Version detection and orchestration logic
  - General error handling and retry mechanisms
  - Framework patterns and interfaces

## 🛠️ **Creating a New Migration**

### Step 1: Create Migration Folder and Implementation
```bash
mkdir -p persistence/migrations/v3
```

Create `v3/DocumentV3Migrator.py`:
```python
from typing import Any

from pymongo.database import Database

from aihub_lib.persistence.migrations.base import DocumentMigration

class DocumentV3Migrator(DocumentMigration):
    version = 3
    description = "Your migration description here"
    
    def get_affected_collections(self) -> list[str]:
        return ["agent_events", "process_events"]
    
    async def up(self, db: Database) -> dict[str, Any]:
        # Migration logic here
        pass
    
    async def down(self, db: Database) -> dict[str, Any]:
        # Rollback logic here
        pass
```

### Step 2: Create Comprehensive Tests (MANDATORY)
Create `v3/test_DocumentV3Migrator.py` with all required test categories:

```python
"""
Comprehensive tests for DocumentV3Migrator.
🚨 MANDATORY: These tests must pass before PR can be merged.
"""

class TestDocumentV3MigratorProperties:
    """Test migration properties and metadata."""
    
class TestDocumentV3MigratorMockOperations:
    """Test migration logic with mocked database."""
    
@pytest.mark.mongodb
class TestDocumentV3MigratorIntegration:
    """Integration tests with real MongoDB."""
    
class TestDocumentV3MigratorValidation:
    """Test migration validation and error scenarios."""
```

### Step 3: Register Migration
Update `migrate.py`:
```python
from aihub_lib.persistence.migrations.v3.DocumentV3Migrator import DocumentV3Migrator

MIGRATIONS: list[type[DocumentMigration]] = [
    DocumentV2Migrator,
    DocumentV3Migrator,  # Add in version order
]
```

### Step 4: Run Tests
```bash
# Run new migration tests
poetry run pytest persistence/migrations/v3/test_DocumentV3Migrator.py -v

# Run all migration tests  
poetry run pytest persistence/migrations/ -v
```

## 🧪 **Testing Strategy**

### Local Development
```bash
# Fast unit tests (no MongoDB required)
poetry run pytest persistence/migrations/ -m "not mongodb" -v

# Full integration tests (requires MongoDB)
poetry run pytest persistence/migrations/ --mongodb -v

# Test specific migration
poetry run pytest persistence/migrations/v2/test_DocumentV2Migrator.py --mongodb -v
```

### CI/CD Pipeline
```bash
# Use the provided test runner
poetry run python persistence/migrations/tests/run_migration_tests.py
```

## 📋 **Migration Checklist**

Before submitting a migration PR, ensure:

- [ ] **Migration Implementation**: Inherits from `DocumentMigration`
- [ ] **Up Migration**: Uses aggregation pipeline for atomic operations
- [ ] **Down Migration**: Completely reverts all changes
- [ ] **Index Management**: Creates indices in up(), drops in down()
- [ ] **Error Handling**: Graceful handling of edge cases
- [ ] **Properties Tests**: Version, description, collections ✅
- [ ] **Mock Tests**: Database operations validation ✅  
- [ ] **Integration Tests**: Real MongoDB scenarios ✅
- [ ] **Performance Tests**: Large dataset validation ✅
- [ ] **Rollback Tests**: Complete reversion validation ✅
- [ ] **Registration**: Added to MIGRATIONS list ✅
- [ ] **All Tests Pass**: Both unit and integration tests ✅

## 🚀 **Production Deployment**

Migrations run automatically on API startup via `run_migrations()`:

```python
# In API startup
from aihub_lib.persistence.migrations.migrate import run_migrations

await run_migrations(
    mongodb_url="mongodb://...", 
    database_name="aihub"
)
```

## 🔗 **Related Documentation**

- [Migration Testing Guide](tests/README.md)
- [AI-Hub Library Documentation](../../../README.md)
- [MongoDB Aggregation Pipeline Documentation](https://docs.mongodb.com/manual/core/aggregation-pipeline/)