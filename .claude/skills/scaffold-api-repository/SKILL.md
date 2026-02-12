---
name: scaffold-api-repository
description: Generate a MongoEngine Document entity that combines schema definition
  with repository methods (classmethods). Follows the Entity pattern used instead
  of separate repository classes.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Scaffold a MongoDB Entity (Repository Pattern)

Generate a MongoEngine Document entity for a resource. The resource name should be provided via `$ARGUMENTS`.

## Before You Start

Read these reference entities:
- Agent class: `aihub_lib/aihub_lib/persistence/agents/AgentClassEntity.py`
- Agent config: `aihub_lib/aihub_lib/persistence/agents/AgentConfigEntityDocument.py`
- Thread: `aihub_lib/aihub_lib/persistence/messaging/entities/ThreadEntity.py`
- Notification: `aihub_lib/aihub_lib/persistence/notification/NotificationEntity.py`
- User: `aihub_lib/aihub_lib/persistence/user/UserEntity.py`
- Role: `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`
- Bearer token: `aihub_lib/aihub_lib/persistence/access/entities/BearerToken.py`

## Architecture: No Separate Repository Layer

In this codebase, Entities **ARE** the repositories. Each Entity class combines:

1. **Schema definition** (MongoEngine fields)
2. **Repository methods** (`@classmethod` for queries)
3. **Instance methods** (save, delete, update)

There is NO separate `Repository` or `DAO` class. Services call Entity class methods directly.

```
Service Layer
    |
    v
Entity (@classmethod repository methods)  <-- YOU ARE HERE
    |
    v
MongoEngine ODM
    |
    v
MongoDB (via FerretDB)
```

## Step 1: Create the Entity

File: `aihub_lib/aihub_lib/persistence/<resource>/<Resource>Entity.py`

```python
from datetime import UTC, datetime
from typing import Self

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    DoesNotExist,
    EmbeddedDocumentField,
    ListField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.common.LocaleStringEntity import LocaleStringEntity


class <Resource>Entity(Document):
    """
    MongoDB document for <resource>s.

    Combines schema definition with repository methods.
    Collection: <resource>s
    """

    # ==================== Meta ====================

    meta = {
        "collection": "<resource>s",
        "strict": False,
        "indexes": [
            {"fields": ["name"], "unique": True},
            {"fields": ["user_id"]},
            {"fields": ["created_at"]},
        ],
    }

    # ==================== Schema (Fields) ====================

    name = StringField(required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
    user_id = StringField(required=True)
    status = StringField(required=True, default="active")
    config_data = DictField(default=dict)
    created_at = DateTimeField(required=True, default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(required=True, default=lambda: datetime.now(UTC))

    # ==================== Properties ====================

    @property
    def is_active(self) -> bool:
        """Check if the <resource> is currently active."""
        return self.status == "active"

    # ==================== Instance Methods ====================

    def save(self, *args, **kwargs) -> Self:
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)
        return super().save(*args, **kwargs)

    # ==================== Repository Methods (classmethods) ====================

    @classmethod
    @trace_fn
    def get_by_id(cls, <resource>_id: str) -> Self:
        """Get a <resource> by its MongoDB ObjectId. Raises DoesNotExist."""
        return cls.objects.get(id=<resource>_id)

    @classmethod
    @trace_fn
    def find_by_name(cls, name: str) -> Self | None:
        """Find a <resource> by name. Returns None if not found."""
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def get_all(cls) -> list[Self]:
        """Get all <resource>s."""
        return list(cls.objects())

    @classmethod
    @trace_fn
    def get_for_user(cls, user_id: str) -> list[Self]:
        """Get all <resource>s belonging to a user."""
        return list(cls.objects(user_id=user_id))

    @classmethod
    @trace_fn
    def count_for_user(cls, user_id: str) -> int:
        """Count <resource>s belonging to a user."""
        return cls.objects(user_id=user_id).count()

    @classmethod
    @trace_fn
    def get_paginated_for_user(
        cls, user_id: str, skip: int = 0, limit: int = 20,
    ) -> list[Self]:
        """Get a paginated list of <resource>s for a user."""
        return list(
            cls.objects(user_id=user_id)
            .order_by("-created_at")
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    @trace_fn
    def create_<resource>(cls, name: str, user_id: str, **kwargs) -> Self:
        """Create a new <resource>."""
        entity = cls(
            name=name,
            user_id=user_id,
            **kwargs,
        )
        entity.save()
        return entity

    @classmethod
    @trace_fn
    def create_or_update(cls, name: str, user_id: str, **data) -> Self:
        """Create a new <resource> or update existing one."""
        existing = cls.objects(name=name, user_id=user_id).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.save()
            return existing
        return cls.create_<resource>(name=name, user_id=user_id, **data)

    @classmethod
    @trace_fn
    def delete_by_id(cls, <resource>_id: str) -> None:
        """Delete a <resource> by ID. Raises DoesNotExist."""
        entity = cls.objects.get(id=<resource>_id)
        entity.delete()
```

## MongoEngine Field Reference

### Basic Fields

| Field | Usage | Example |
|-------|-------|---------|
| `StringField` | Text | `name = StringField(required=True, unique=True)` |
| `IntField` | Integer | `count = IntField(default=0)` |
| `FloatField` | Decimal | `cost = FloatField(default=0.0)` |
| `BooleanField` | Boolean | `active = BooleanField(default=True)` |
| `DateTimeField` | Timestamp | `created_at = DateTimeField(default=lambda: datetime.now(UTC))` |
| `DictField` | Flexible JSON | `config_data = DictField(default=dict)` |

### Collection Fields

| Field | Usage | Example |
|-------|-------|---------|
| `ListField(StringField())` | String array | `tags = ListField(StringField())` |
| `ListField(DictField())` | Array of objects | `items = ListField(DictField())` |
| `ListField(EmbeddedDocumentField(X))` | Typed array | `users = ListField(EmbeddedDocumentField(User))` |

### Embedded Documents

| Field | Usage | Example |
|-------|-------|---------|
| `EmbeddedDocumentField(X)` | Nested object | `name = EmbeddedDocumentField(LocaleStringEntity)` |

### Field Options

| Option | Purpose | Example |
|--------|---------|---------|
| `required=True` | Field must be set | `name = StringField(required=True)` |
| `unique=True` | Unique constraint | `email = StringField(unique=True)` |
| `default=value` | Default value | `status = StringField(default="active")` |
| `default=callable` | Default factory | `created_at = DateTimeField(default=lambda: datetime.now(UTC))` |
| `choices=(...)` | Enum constraint | `type = StringField(choices=("info", "warn", "error"))` |
| `null=True` | Allow null | `profile_image = StringField(null=True)` |
| `primary_key=True` | Custom primary key | `id = StringField(primary_key=True)` |

## Meta Configuration

```python
meta = {
    "collection": "<resource>s",          # MongoDB collection name
    "strict": False,                       # Allow extra fields not in schema
    "indexes": [
        {"fields": ["name"], "unique": True},           # Unique index
        {"fields": ["user_id"]},                         # Simple index
        {"fields": ["created_at"]},                      # Date index
        {"fields": ["user_id", "status"]},               # Compound index
        {"fields": ["-created_at"]},                     # Descending index
    ],
}
```

## Repository Method Patterns

### Query Patterns (MongoEngine QuerySet API)

```python
# Get one (raises DoesNotExist)
cls.objects.get(id=resource_id)

# Get first or None
cls.objects(name=name).first()

# Get all
list(cls.objects())

# Filter
cls.objects(user_id=user_id, status="active")

# Chain filters
cls.objects(user_id=user_id).filter(status__in=["active", "pending"])

# Pagination
cls.objects(user_id=user_id).order_by("-created_at").skip(skip).limit(limit)

# Count
cls.objects(user_id=user_id).count()

# Distinct
cls.objects().distinct("status")
```

### Filter Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `__exact` | Exact match (default) | `name=value` |
| `__in` | In list | `status__in=["active", "pending"]` |
| `__ne` | Not equal | `status__ne="deleted"` |
| `__gt`, `__gte` | Greater (or equal) | `created_at__gte=cutoff_date` |
| `__lt`, `__lte` | Less (or equal) | `cost__lt=100` |
| `__contains` | String contains | `name__contains="test"` |
| `__icontains` | Case-insensitive contains | `name__icontains="test"` |
| `__exists` | Field exists | `config__exists=True` |

### Bulk Update Patterns

```python
# Update multiple documents
cls.objects(id__in=ids, user_id=user_id).update(set__read=True)

# Atomic update
cls.objects(id=entity_id).update_one(inc__count=1)

# Push to array
cls.objects(id=entity_id).update_one(push__tags="new_tag")

# Pull from array
cls.objects(id=entity_id).update_one(pull__tags="old_tag")
```

### MongoDB Aggregation Pipeline

For complex queries, use the aggregation framework:

```python
@classmethod
def get_aggregated_statistics(cls, resource_id: str) -> list[dict]:
    pipeline = [
        {"$match": {"resource_id": resource_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_cost": {"$sum": "$cost"},
        }},
        {"$sort": {"count": -1}},
    ]
    return list(cls.objects.aggregate(pipeline))
```

## Embedded Documents

For nested structures, define `EmbeddedDocument` classes:

```python
from mongoengine import EmbeddedDocument, StringField

class AgentInstanceRef(EmbeddedDocument):
    """Reference to an agent instance (embedded in ThreadEntity)."""
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
```

Used in parent entity:
```python
class ThreadEntity(Document):
    agents = ListField(EmbeddedDocumentField(AgentInstanceRef))
```

## i18n Locale Strings

For multilingual text, use `LocaleStringEntity`:

```python
from aihub_lib.persistence.common.LocaleStringEntity import LocaleStringEntity

class MyEntity(Document):
    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
```

`LocaleStringEntity` stores:
```python
class LocaleStringEntity(EmbeddedDocument):
    en = StringField()
    de = StringField()
    fr = StringField()
    it = StringField()

    def to_locale_string(self) -> LocaleString:
        return LocaleString(en=self.en, de=self.de, fr=self.fr, it=self.it)

    @classmethod
    def from_locale_string(cls, locale_string: LocaleString) -> Self:
        return cls(en=locale_string.en, de=locale_string.de, fr=locale_string.fr, it=locale_string.it)
```

## File Placement

```
aihub_lib/aihub_lib/persistence/
├── access/
│   └── entities/
│       ├── BearerToken.py
│       └── RoleEntity.py
├── agents/
│   ├── AgentClassEntity.py
│   └── AgentConfigEntityDocument.py
├── messaging/
│   └── entities/
│       ├── ThreadEntity.py
│       └── PersistedAgentEventEntity.py
├── notification/
│   └── NotificationEntity.py
├── user/
│   └── UserEntity.py
├── common/
│   └── LocaleStringEntity.py
└── <resource>/                  <-- NEW
    └── <Resource>Entity.py
```

## Key Conventions

- **Entities go in `aihub_lib`**: They're shared across packages
- **`meta["strict"] = False`**: Allow extra fields for forward compatibility
- **`@classmethod` for queries**: All data access is via class methods
- **`@trace_fn` on all methods**: OpenTelemetry tracing
- **`DoesNotExist` exceptions**: MongoEngine throws these — catch in services
- **`save()` override**: Update `updated_at` timestamp automatically
- **Indexes**: Always index fields used in queries
- **No repository abstraction**: The Entity IS the repository
