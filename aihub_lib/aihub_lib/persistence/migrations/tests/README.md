# Migration Testing Framework

Advanced testing methodologies and frameworks for ensuring migration safety, reliability, and performance in production deployments.

## 🎯 Testing Philosophy

The AI-Hub migration testing framework prioritizes:

1. **Clarity over Complexity**: Tests define clear before/after states using actual data
2. **Real-world Scenarios**: Uses actual MongoDB with realistic documents  
3. **Easy to Understand**: Minimal mocking - focus on data transformations
4. **Easy to Maintain**: When migrations change, just update the expected states

## 🏗️ SimpleMigrationTest Framework (Recommended)

The **SimpleMigrationTest** base class is the recommended approach for testing migrations. It handles all infrastructure while you focus on defining clear before/after states.

### Basic Usage

```python
from aihub_lib.persistence.migrations.tests.SimpleMigrationTest import SimpleMigrationTest
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator

class TestDocumentV2MigratorRealistic(SimpleMigrationTest):
    """Test V2 migration with realistic production-like data."""
    
    migration_class = DocumentV2Migrator
    
    # Define initial state (before migration)
    initial_state: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            {
                "schema_version": 1,  # V1 state
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "event_data": {"created_at": 1640995200000000000},
                # Note: Root created_at field missing in V1
            }
        ]
    }
    
    # Define expected state after UP migration
    expected_state_after_up: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            {
                "schema_version": 2,  # Updated by migration
                "agent_class": "ChatAgent",
                "agent_id": "agent-123", 
                "event_data": {"created_at": 1640995200000000000},
                "created_at": 1640995200000000000,  # Root field added by migration
            }
        ]
    }
    
    # Define expected state after DOWN migration (rollback)
    expected_state_after_down: dict[str, list[dict[str, Any]]] = {
        "agent_events": [
            {
                "schema_version": 1,  # Rolled back
                "agent_class": "ChatAgent",
                "agent_id": "agent-123",
                "event_data": {"created_at": 1640995200000000000},
                # Root created_at field removed by rollback
            }
        ]
    }
```

### Automatic Test Coverage

Each test class inheriting from `SimpleMigrationTest` automatically gets **5 comprehensive tests**:

- **`test_migration_up()`** - Forward migration transforms data correctly
- **`test_migration_down()`** - Rollback restores original state  
- **`test_migration_up_idempotent()`** - Running migration twice is safe
- **`test_migration_handles_empty_collections()`** - Edge cases handled gracefully
- **`test_full_migration_cycle()`** - Complete up→down→up cycle works

### Framework Features

✅ **Real MongoDB Integration** - Tests with actual database, not mocks  
✅ **Isolated Test Databases** - Each test gets clean, isolated environment  
✅ **Automatic State Verification** - Compares expected vs actual database state  
✅ **Datetime Precision Handling** - Robust comparison handling MongoDB precision issues  
✅ **Detailed Error Messages** - Clear assertions showing exactly what differs  
✅ **Comprehensive Coverage** - 5 tests per class covering all scenarios  

## 📊 Test Scenarios & Patterns

### Multiple Test Classes per Migration

Create separate test classes for different scenarios:

```python
class TestDocumentV2MigratorRealistic(SimpleMigrationTest):
    """Test V2 migration with typical production data."""
    migration_class = DocumentV2Migrator
    # ... realistic data scenarios

class TestDocumentV2MigratorMixedVersions(SimpleMigrationTest):
    """Test V2 migration with documents at different schema versions."""
    migration_class = DocumentV2Migrator  
    # ... mixed version scenarios
    
class TestDocumentV2MigratorEmptyDatabase(SimpleMigrationTest):
    """Test V2 migration on empty database."""
    migration_class = DocumentV2Migrator
    # ... empty database scenarios
```

### Realistic Test Data Design

#### Use Actual Entity Schemas

Base test data on real MongoEngine entities:

```python
from datetime import UTC, datetime

# Fixed datetime instances avoid precision issues
FIXED_DATETIME_1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
FIXED_DATETIME_2 = datetime(2025, 1, 2, 12, 0, 0, tzinfo=UTC)

initial_state = {
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
                "minRow": 1, "margin": 24, "column": 4, 
                "cellHeight": 350, "children": []
            }
        }
    ],
    "agent_events": [
        {
            # PersistedAgentEventEntity without schema_version
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
                "content": "Agent started processing",
                "metadata": {"source": "user_input"}
            },
            "event_parents": [],
            "created_at": 1640995200000000000
        }
    ]
}
```

#### Edge Cases & Variations

Include realistic edge cases:

```python
initial_state = {
    "agent_events": [
        # Document at v1 (should be migrated)
        {"schema_version": 1, "agent_class": "ChatAgent", ...},
        
        # Document already at v2 (should be left alone)  
        {"schema_version": 2, "agent_class": "RAGAgent", ...},
        
        # Document at v3 (should be left alone)
        {"schema_version": 3, "agent_class": "MultiAgent", ...},
        
        # Document with missing fields (edge case)
        {"agent_class": "TestAgent", "event_data": {"content": "Missing created_at"}},
    ]
}
```

## 🔬 Performance Testing

### Large Dataset Testing

```python
@pytest.mark.performance
class TestDocumentV2MigratorPerformance(SimpleMigrationTest):
    """Test V2 migration performance with large datasets."""
    
    migration_class = DocumentV2Migrator
    
    def generate_performance_documents(self, count: int):
        """Generate realistic documents for performance testing."""
        return [
            {
                "schema_version": 1,
                "agent_class": f"TestAgent{i % 10}",
                "agent_id": f"agent_{i:04d}",
                "event_id": f"event_{i:04d}",
                "event_data": {
                    "created_at": 1640995200000000000 + (i * 1000000000),
                    "content": f"Performance test document {i}"
                },
                "event_parents": [],
                "created_at": 1640995200000000000 + (i * 1000000000)
            }
            for i in range(count)
        ]
    
    initial_state: dict[str, list[dict[str, Any]]] = {
        "agent_events": generate_performance_documents(1000)  # 1K documents
    }
```

### Performance Benchmarks

Expected performance on development hardware:

- **Small dataset** (10-100 docs): < 1 second
- **Medium dataset** (1K docs): < 5 seconds  
- **Large dataset** (10K docs): < 30 seconds

## 🆚 Legacy vs Modern Testing Approaches

### ❌ Old Approach: Complex Mocking

```python
# 50+ lines of complex mock setup
def test_up_migration_mock(self):
    mock_db = Mock()
    mock_collection = Mock() 
    mock_result = Mock()
    mock_result.modified_count = 100
    mock_collection.update_many = AsyncMock(return_value=mock_result)
    mock_collection.create_index = AsyncMock()
    mock_db.__getitem__ = Mock(return_value=mock_collection)
    # ... extensive mock configuration
    
    result = await migration.up(mock_db)
    
    # Complex assertions about mock calls
    mock_collection.update_many.assert_called_once_with(...)
```

**Problems:**
- ❌ Hard to understand actual migration behavior
- ❌ Fragile - breaks when implementation changes  
- ❌ Doesn't test real MongoDB interactions
- ❌ Complex mock setup often more complex than migration itself

### ✅ New Approach: Real Data States

```python
class TestDocumentV2MigratorRealistic(SimpleMigrationTest):
    migration_class = DocumentV2Migrator
    
    initial_state = {"agent_events": [{"schema_version": 1, ...}]}
    expected_state_after_up = {"agent_events": [{"schema_version": 2, ...}]}
    expected_state_after_down = initial_state
    
    # That's it! 5 comprehensive tests generated automatically
```

**Benefits:**
- ✅ Crystal clear what migration does
- ✅ Tests real MongoDB behavior
- ✅ Robust - survives implementation changes
- ✅ 20 lines vs 100+ lines of complex mocking
- ✅ Easy to add new test scenarios

## 🛠️ Test Development Workflow

### Prerequisites

```bash
# Ensure MongoDB is running
docker compose -f docker-compose.dev.yml up -d

# Activate poetry environment
cd aihub_lib
```

### Running Tests

```bash
# Run all migration tests
pytest aihub_lib/persistence/migrations/ -v

# Run tests for specific migration
pytest aihub_lib/persistence/migrations/v2/test_DocumentV2Migrator.py -v

# Run performance tests only
pytest aihub_lib/persistence/migrations/ -m performance -v

# Run tests excluding performance tests
pytest aihub_lib/persistence/migrations/ -m "not performance" -v
```

### Test Development Cycle

1. **Create test class** inheriting from `SimpleMigrationTest`
2. **Set migration_class** to your migrator
3. **Define realistic initial_state** with actual entity data
4. **Define expected states** for up and down migrations
5. **Run tests** - you get 5 comprehensive tests automatically
6. **Add edge cases** by creating additional test classes

## 🔧 Debugging & Troubleshooting

### Enable Detailed Logging

```python  
from aihub_lib.testing.logging.logger import enable_logging
enable_logging()  # Already enabled in test files
```

### Run Specific Tests

```bash
# Run single test with full output
pytest aihub_lib/persistence/migrations/v2/test_DocumentV2Migrator.py::TestDocumentV2MigratorRealistic::test_migration_up -v -s

# Drop into debugger on failure
pytest aihub_lib/persistence/migrations/tests/ --pdb
```

### Common Issues & Solutions

#### Datetime Precision Problems

The framework automatically handles MongoDB datetime precision issues:

```python
# Framework handles these automatically
expected_utc = expected_value.astimezone(UTC)
actual_utc = actual_value.replace(tzinfo=UTC) if actual_value.tzinfo is None else actual_value.astimezone(UTC)
expected_simplified = expected_utc.replace(microsecond=0) 
actual_simplified = actual_utc.replace(microsecond=0)
```

#### Missing Fields in Rollback

Ensure rollback states correctly remove fields added by migration:

```python
expected_state_after_down = {
    "agent_events": [{
        "schema_version": 1,  # Rolled back
        "agent_class": "ChatAgent",
        "event_data": {"created_at": 1640995200000000000},
        # ✅ Root created_at field properly removed by rollback
    }]
}
```

## 🏗️ Framework Architecture

### SimpleMigrationTest Base Class

```python
class SimpleMigrationTest(ABC):
    """
    Base class for simple, real-world migration testing.
    
    Handles all infrastructure while you focus on data states.
    """
    
    # Override in subclasses
    migration_class: type[DocumentMigrator]
    initial_state: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_up: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_down: dict[str, list[dict[str, Any]]] = {}
    
    @pytest_asyncio.fixture
    async def db(self):
        """Provide clean test database for each test."""
        # Isolated MongoDB test database with automatic cleanup
        
    async def setup_initial_state(self, db: AsyncDatabase):
        """Insert initial documents into database."""
        
    async def verify_state(self, db: AsyncDatabase, expected_state):
        """Verify database matches expected state with detailed assertions."""
```

### Key Framework Features

- **Database Isolation**: Each test gets clean MongoDB test database
- **Automatic Cleanup**: Databases cleaned before/after each test
- **State Verification**: Detailed field-by-field comparison
- **Error Messages**: Clear assertions showing exactly what differs
- **Edge Case Handling**: Empty collections, mixed versions, missing fields

## 🚨 Testing Requirements for New Migrations

Every migration **MUST** have comprehensive tests using SimpleMigrationTest:

### Required Test Classes

1. **Realistic Scenario** - Production-like data
2. **Mixed Versions** - Documents at different schema versions  
3. **Empty Database** - Edge case handling
4. **Performance** (optional) - Large dataset testing

### Required Coverage

- ✅ **15 tests minimum** (3 classes × 5 automatic tests)
- ✅ **All scenarios pass** - up/down/idempotency/cycles/empty
- ✅ **Realistic data** - Based on actual entity schemas
- ✅ **Edge cases** - Missing fields, mixed versions, empty collections

## 🤝 Contributing Test Improvements

### Best Practices

1. **Use SimpleMigrationTest**: Follow the recommended pattern
2. **Realistic data**: Base on actual MongoEngine entity structures  
3. **Multiple scenarios**: Create separate test classes for different cases
4. **Document purpose**: Clear docstrings explaining test class coverage
5. **Performance awareness**: Mark large dataset tests with `@pytest.mark.performance`

### Test Organization

```
v2/
└── test_DocumentV2Migrator.py
    ├── TestDocumentV2MigratorRealistic     # Production-like data
    ├── TestDocumentV2MigratorMixedVersions  # Mixed schema versions  
    └── TestDocumentV2MigratorEmptyDatabase  # Edge cases
```

## 🔗 Related Documentation

- **[Migration System Overview](../README.md)** - Creating migrations, architecture, production deployment
- **[AI-Hub Library Documentation](../../README.md)** - Overall library patterns and architecture
- **[MongoDB Testing Best Practices](https://docs.mongodb.com/manual/administration/analyzing-mongodb-performance/)** - MongoDB performance testing guidance