from typing import List, Set

from mongoengine import Document, ListField, StringField


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

    @classmethod
    def get_access_rules_for_roles(cls, role_names: List[str]) -> Set[str]:
        """
        Fetches all roles corresponding to the given role names and returns a
        unique set of all their associated access rules.
        """
        roles_query = cls.objects(name__in=list(set(role_names)))

        all_rules = set()
        for role in roles_query:
            all_rules.update(role.access_rules)

        return all_rules
