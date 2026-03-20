---
name: scaffold-api-repository
description: Generate a MongoEngine Document entity that combines schema definition with repository classmethods in packages/core/persistence/. Follows the Entity-as-repository pattern (no separate DAO/repository classes). Use when user says "create an entity", "scaffold a repository", "add MongoDB model", "new database entity", "generate MongoEngine document", "create persistence layer", or "scaffold data model". Do NOT use for service layer business logic (use scaffold-api-service), controller/endpoint scaffolding (use scaffold-api-endpoint), or event display components (use scaffold-event-display).
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Scaffold a MongoDB Entity (Repository Pattern)

Generate a MongoEngine Document entity for a resource. The resource name should be provided via `$ARGUMENTS`.

## Before You Start

Read these reference entities:

- Agent class: `packages/core/swiss_ai_hub/core/persistence/agents/agent_class_entity.py`
- Agent config: `packages/core/swiss_ai_hub/core/persistence/agents/agent_config_entity_document.py`
- Thread: `packages/core/swiss_ai_hub/core/persistence/messaging/entities/thread_entity.py`
- Notification: `packages/core/swiss_ai_hub/core/persistence/notification/notification_entity.py`
- User: `packages/core/swiss_ai_hub/core/persistence/user/user_entity.py`
- Role: `packages/core/swiss_ai_hub/core/persistence/access/entities/role_entity.py`
- Bearer token: `packages/core/swiss_ai_hub/core/persistence/access/entities/bearer_token.py`

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

File: `packages/core/swiss_ai_hub/core/persistence/<resource>/<resource>_entity.py`

```python
from datetime import UTC, datetime
from typing import Self

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocumentField,
    ListField,
    StringField,
)

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity


class <Resource>Entity(Document):
    """
    MongoDB document for <resource>s.

    Combines schema definition with repository methods.
    Collection: <resource>s
    """

    # ==================== Meta ====================

    meta = {
        "collection": "<resource>s",
        "strict": False,  # Commonly used — allows extra fields for forward compatibility
        "indexes": [
            {"fields": ["name"], "unique": True},
            {"fields": ["user_id"]},
        ],
    }

    # ==================== Schema (Fields) ====================

    name = StringField(required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
    user_id = StringField(required=True)
    status = StringField(required=True, default="active")
    config_data = DictField(default=dict)
    # Add created_at/updated_at only if temporal tracking is needed:
    # created_at = DateTimeField(required=True, default=lambda: datetime.now(UTC))
    # updated_at = DateTimeField(required=True, default=lambda: datetime.now(UTC))
    # If using updated_at, override save() — see AgentConfigEntityDocument for the pattern.

    # ==================== Properties ====================

    @property
    def is_active(self) -> bool:
        """Check if the <resource> is currently active."""
        return self.status == "active"

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

## MongoEngine Quick Reference

Common fields used in this codebase (see [MongoEngine docs](https://docs.mongoengine.org/) for full reference):

```python
# Scalar fields
name = StringField(required=True, unique=True)
count = IntField(default=0)
active = BooleanField(default=True)
created_at = DateTimeField(default=lambda: datetime.now(UTC))
config_data = DictField(default=dict)

# Collection / embedded fields
tags = ListField(StringField())
agents = ListField(EmbeddedDocumentField(AgentInstanceRef))
name = EmbeddedDocumentField(LocaleStringEntity, required=True)

# Field options: required, unique, default, choices=(...), null=True
```

## Meta Configuration

```python
meta = {
    "collection": "<resource>s",          # MongoDB collection name
    "strict": False,                       # Commonly used — allows extra fields
    "indexes": [
        {"fields": ["name"], "unique": True},           # Unique index
        {"fields": ["user_id"]},                         # Simple index
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
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

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
packages/core/swiss_ai_hub/core/persistence/
├── access/
│   └── entities/
│       ├── bearer_token.py
│       └── role_entity.py
├── agents/
│   ├── agent_class_entity.py
│   ├── agent_config_entity.py
│   ├── agent_config_entity_document.py
│   └── agent_config_entity_embedded_document.py
├── i18n/
│   └── locale_string_entity.py
├── messaging/
│   └── entities/
│       ├── thread_entity.py
│       ├── persisted_agent_event_entity.py
│       └── persisted_process_event_entity.py
├── notification/
│   └── notification_entity.py
├── process/
│   ├── process_class_entity.py
│   ├── process_config_entity.py
│   ├── process_config_entity_document.py
│   └── process_config_entity_embedded_document.py
├── rag/
│   └── datalake/
│       └── entities/
│           ├── bucket_entity.py
│           └── namespace_entity.py
├── user/
│   └── user_entity.py
└── <resource>/                  <-- NEW
    └── <resource>_entity.py
```

## Step 2: Verify

1. Confirm the entity is importable:
   `cd packages/core && uv run python -c "from swiss_ai_hub.core.persistence.<resource>.<resource>_entity import <Resource>Entity"`
2. Confirm the service imports the entity (if service already exists)
3. Run tests: `cd packages/core && make test`

## Examples

**Typical invocation**: `/scaffold-api-repository notification`

**Result**: Creates `packages/core/swiss_ai_hub/core/persistence/notification/NotificationEntity.py` with:

- Document class with schema fields
- Repository classmethods (get_by_id, find_by_name, get_all, create, delete)
- Proper indexes and meta configuration
- OpenTelemetry tracing on all methods

## Troubleshooting

| Problem                       | Solution                                                             |
| ----------------------------- | -------------------------------------------------------------------- |
| `DoesNotExist` at runtime     | Entity not found — catch in the service layer, not in the entity     |
| Duplicate key error           | Check `meta["indexes"]` — a unique constraint is being violated      |
| `strict` mode errors          | Set `meta["strict"] = False` to allow extra fields                   |
| Missing collection in MongoDB | MongoEngine auto-creates collections on first write                  |
| Import error from other scope | Ensure entity is in `packages/core`, not in a scope-specific package |

## Key Conventions

- **Entities go in `packages/core`**: They're shared across packages
- **`meta["strict"] = False`**: Commonly used to allow extra fields — check existing entities for precedent
- **`@classmethod` for queries**: All data access is via class methods
- **`@trace_fn` on all methods**: OpenTelemetry tracing
- **`DoesNotExist` exceptions**: MongoEngine throws these — catch in services, not in entities
- **`save()` override**: Only for entities with `updated_at` — see `agent_config_entity_document.py` for the pattern
- **Indexes**: Always index fields used in queries
- **No repository abstraction**: The Entity IS the repository
