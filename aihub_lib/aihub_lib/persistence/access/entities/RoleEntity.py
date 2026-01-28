from __future__ import annotations

from mongoengine import Document, IntField, ListField, StringField

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class RoleEntity(Document):
    """
    Represents a role in the system, which contains a set of access rules and rate limits.

    Rate limits are merged across roles using most-permissive-wins strategy:
    - If any role has None (unlimited), user gets unlimited
    - Otherwise, highest limit value is used
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

    # Agent rate limits (None = unlimited)
    agent_calls_limit = IntField(default=None)
    agent_calls_period = StringField(default="1mo")

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
    def get_roles_with_limits(cls, role_names: list[str]) -> list[RoleEntity]:
        """
        Fetches roles with their limit configurations for merging.
        Used by RoleLimitService to determine effective limits.
        """
        return list(cls.objects(name__in=list(set(role_names))))
