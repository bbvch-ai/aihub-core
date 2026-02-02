from __future__ import annotations

from typing import Annotated

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentListField, IntField, ListField, StringField
from pydantic import BaseModel, Field

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class RoleUsageLimit(BaseModel):
    """Typed representation of a single usage limit rule from a role."""

    pattern: Annotated[str, Field(description="Full dotted resource pattern with optional wildcards")]
    limit: Annotated[int, Field(ge=0, description="Maximum number of allowed calls in the period")]
    period: Annotated[str, Field(description="Time window for the limit (1h, 1d, 7d, 1mo)")]


class UsageLimit(EmbeddedDocument):
    """Pattern-based usage limit rule (NATS-style wildcards: * single-level, > multi-level)."""

    pattern = StringField(required=True)
    limit = IntField(required=True, min_value=0)
    period = StringField(required=True, choices=["1h", "1d", "7d", "1mo"])


class RoleEntity(Document):
    """
    Represents a role in the system, which contains a set of access rules.
    """

    meta = {
        "collection": "roles",
        "strict": False,
        "indexes": [
            {"fields": ["name"], "unique": True},
        ],
    }

    name = StringField(required=True, unique=True)
    description = StringField(required=True)
    access_rules = ListField(StringField(), default=list)
    usage_limits = EmbeddedDocumentListField(UsageLimit, default=list)

    @classmethod
    @trace_fn
    def get_role_by_name(cls, role_name: str) -> RoleEntity | None:
        """
        Fetches a role by its name. Returns None if the role does not exist.
        """
        return cls.objects(name=role_name).first()

    @classmethod
    @trace_fn
    def get_access_rules_for_roles(cls, role_names: list[str]) -> set[str]:
        """
        Fetches all roles corresponding to the given role names and returns a
        unique set of all their associated access rules.
        """
        roles_query = cls.objects(name__in=list(set(role_names)))

        all_rules = set()
        for role in roles_query:
            all_rules.update(role.access_rules)

        return all_rules

    @staticmethod
    @trace_fn
    def filter_existing_roles(role_names: list[str]) -> list[str]:
        """
        Filters a list of potential role names, returning only those that
        exist in the database.
        """
        existing_roles_query = RoleEntity.objects(name__in=role_names).only("name")
        return [role.name for role in existing_roles_query]

    @classmethod
    @trace_fn
    def get_usage_limits_for_roles(cls, role_names: list[str]) -> list[list[RoleUsageLimit]]:
        """
        Returns a list of usage_limits per role.
        """
        roles = cls.objects(name__in=role_names).only("usage_limits")
        return [
            [RoleUsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in role.usage_limits]
            for role in roles
        ]
