# Migration Testing Guide

This directory contains comprehensive tests for the AI-Hub database migration system. The tests are designed to ensure migration safety, reliability, and performance before deploying to production.

## 🎯 Test Categories

### 1. **Unit Tests** (Fast, No External Dependencies)

- **Mock-based tests**: Test migration logic without real database
- **Algorithm validation**: Test schema transformation logic
- **Edge case handling**: Test error conditions and invalid data

### 2. **Integration Tests** (Require MongoDB)

- **Real database operations**: Test with actual MongoDB instance
- **Data integrity validation**: Ensure no data loss during migration
- **Performance testing**: Validate migration speed with large datasets

### 3. **End-to-End Tests**

- **Complete migration cycles**: Test up/down migration sequences
- **Production simulation**: Test with realistic data volumes
- **Rollback validation**: Ensure complete revertability

## 🚀 Running Tests

### Prerequisites

```bash
# Ensure MongoDB is running (required for integration tests)
docker compose -f docker-compose.dev.yml up -d

# Activate poetry environment
cd aihub_lib
poetry shell
```

### Quick Test Commands

```bash
# Run all migration tests (requires MongoDB)
pytest aihub_lib/persistence/migrations/ -v

# Run tests for specific migrator
pytest aihub_lib/persistence/migrations/v2/test_DocumentV2Migrator.py -v

# Run performance tests
pytest aihub_lib/persistence/migrations/tests/ -m performance -v
```

### Test Configuration Options

```bash
# Custom MongoDB URL (default: mongodb://admin:admin@localhost:27017)
pytest aihub_lib/persistence/migrations/tests/ --mongodb-url="mongodb://localhost:27017"

# Run specific test categories
pytest aihub_lib/persistence/migrations/tests/ -m "not performance"
pytest aihub_lib/persistence/migrations/tests/ -m "performance"
```

## 📋 Test Structure

### BaseMigrationTest

Abstract base class providing common migration testing infrastructure:

- **Database setup/teardown**: Automatic test database isolation
- **Data validation methods**: Pre/post migration data verification
- **Performance testing**: Large dataset migration validation
- **Error handling**: Partial failure and recovery testing

### Migration-Specific Tests

Each migrator (e.g., `DocumentV2Migrator`) has comprehensive tests:

```python
class TestDocumentV2Migrator(BaseMigrationTest):
    migration_class = DocumentV2Migrator
    test_collections = ["agent_events", "process_events"]
    
    async def create_pre_migration_data(self, db):
        # Create realistic v1 test data
        
    async def validate_post_migration_data(self, db, pre_data):
        # Validate v2 transformation
        
    async def validate_post_rollback_data(self, db, pre_data):
        # Validate v1 restoration
```

## 🔬 Test Coverage Areas

### Data Integrity

- ✅ **No data loss**: All original data preserved during migration
- ✅ **Correct transformation**: Schema changes applied accurately
- ✅ **Referential integrity**: Relationships maintained across collections

### Performance

- ✅ **Large dataset handling**: Test with 1000+ documents per collection
- ✅ **Migration timing**: Ensure reasonable completion times
- ✅ **Memory usage**: Validate resource consumption

### Error Handling

- ✅ **Partial failures**: Test recovery from interrupted migrations
- ✅ **Invalid data**: Handle documents missing required fields
- ✅ **Concurrent access**: Test behavior with simultaneous database operations

### Rollback Safety

- ✅ **Complete reversion**: Down migration restores original state
- ✅ **Data preservation**: No data loss during rollback
- ✅ **Index cleanup**: Migration-created indices properly removed

## 🏗️ Creating Tests for New Migrations

### 1. Create Migration Test Class

```python
# aihub_lib/persistence/migrations/v3/test_DocumentV3Migrator.py
from aihub_lib.persistence.migrations.tests.base_migration_test import BaseMigrationTest
from aihub_lib.persistence.migrations.v3.DocumentV3Migrator import DocumentV3Migrator

class TestDocumentV3Migrator(BaseMigrationTest):
    migration_class = DocumentV3Migrator
    test_collections = ["your_collections"]
    
    async def create_pre_migration_data(self, db):
        # Create v2 test data representing pre-migration state
        
    async def validate_post_migration_data(self, db, pre_data):
        # Validate v3 schema changes
        
    async def validate_post_rollback_data(self, db, pre_data):
        # Validate rollback to v2
```

### 2. Add Test Data Generators

```python
async def create_realistic_test_data(self, db):
    """Create test data that mirrors production scenarios."""
    # Use actual field names and realistic values
    # Include edge cases (null values, empty strings, etc.)
    # Cover different document variants in your schema
```

### 3. Add Performance Tests

```python
async def create_large_test_dataset(self, db):
    """Create performance test dataset."""
    # Generate sufficient data to test performance
    # Aim for 1000+ documents per affected collection
    # Include variety in document structure
```

## 🔍 Debugging Test Failures

### Enable Detailed Logging

```python
from aihub_lib.testing.logging.logger import enable_logging
enable_logging()  # Already enabled in test files
```

### Debug Specific Test

```bash
# Run single test with full output
pytest aihub_lib/persistence/migrations/tests/test_DocumentV2Migrator.py::TestDocumentV2Migrator::test_migration_up_transforms_data_correctly -v -s

# Drop into debugger on failure
pytest aihub_lib/persistence/migrations/tests/ --pdb
```

### Inspect Test Database

```python
# Add temporary debugging code in tests
async def debug_database_state(self, db):
    stats = await migration_test_helper.get_collection_stats(db, "agent_events")
    print(f"Collection stats: {stats}")
    
    # Sample documents
    async for doc in db["agent_events"].find().limit(3):
        print(f"Sample doc: {doc}")
```

## 🚨 Pre-Production Checklist

Before running migrations in production, ensure all tests pass:

```bash
# Complete test suite
pytest aihub_lib/persistence/migrations/ -v

# Performance validation
pytest aihub_lib/persistence/migrations/ -m performance

# Specific migrator validation
pytest aihub_lib/persistence/migrations/v2/test_DocumentV2Migrator.py
```

### Key Validations:

- [ ] **All unit tests pass**: Mock-based logic tests
- [ ] **All integration tests pass**: Real MongoDB tests
- [ ] **Performance within limits**: Large dataset tests complete reasonably
- [ ] **Rollback functionality works**: Down migrations properly revert changes
- [ ] **Data integrity maintained**: No data loss or corruption
- [ ] **Index creation successful**: Required indices are created
- [ ] **Error handling robust**: Graceful handling of edge cases

## 📈 Performance Benchmarks

### Expected Performance (Development Hardware):

- **Small dataset** (10-100 docs): < 1 second
- **Medium dataset** (1K docs): < 5 seconds
- **Large dataset** (10K docs): < 30 seconds

### Performance Test Results:

```bash
# View performance test results
pytest aihub_lib/persistence/migrations/ -m performance -v
```

## 🤝 Contributing New Migration Tests

1. **Follow the pattern**: Use `BaseMigrationTest` for comprehensive coverage
2. **Test realistic data**: Use production-like document structures
3. **Cover edge cases**: Test with invalid/missing data scenarios
4. **Validate performance**: Include large dataset tests
5. **Document expectations**: Add clear assertions with meaningful messages

## 🔗 Related Documentation

- [Migration Framework Documentation](../../../persistence/migrations/README.md)
- [BaseEvent Schema](../../../nats/events/BaseEvent.py)
- [VersionedDocument Base Class](../../../persistence/base/versioned_document.py)
