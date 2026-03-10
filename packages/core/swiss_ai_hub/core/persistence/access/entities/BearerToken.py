import re
import secrets
from datetime import UTC, datetime
from typing import Self

from bson import ObjectId
from mongoengine import DateTimeField, Document, IntField, StringField
from mongoengine.errors import DoesNotExist

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class BearerToken(Document):
    meta = {"collection": "tokens", "strict": False, "indexes": [{"fields": ["token"], "unique": True}]}
    version = IntField(default=1, db_field="_version")
    user_oid = StringField(required=True)
    name = StringField(required=True)
    token = StringField(required=False)  # Should be stored as "<object_id>.<random_part>"
    expiry_date = DateTimeField(required=True)

    # Pre-compile a regex to parse tokens of the form "<mongo_id>.<random_string>"
    TOKEN_REGEX = re.compile(r"^(?P<oid>[a-fA-F0-9]{24})\.(?P<rand>[A-Za-z0-9\-_]{128})$")

    @classmethod
    @trace_fn
    def verify_token(cls, token_str: str) -> Self:
        """
        Verifies that the provided token string is valid:
          - Matches the expected format.
          - Exists in the DB (looked up by the object id).
          - The stored token exactly matches the provided token.
          - Has not expired.
        """
        match = cls.TOKEN_REGEX.match(token_str)
        if not match:
            raise ValueError("Invalid token format")

        oid = match.group("oid")

        try:
            # Lookup the token document using the organization-specific DB
            token_obj = cls.objects.get(id=ObjectId(oid))
        except DoesNotExist:
            raise ValueError("Token not found")

        if token_obj.token != token_str:
            raise ValueError("Token mismatch")

        # Ensure expiry_date is timezone-aware before comparing
        expiry_date = token_obj.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=UTC)

        if expiry_date < datetime.now(UTC):
            raise ValueError("Token expired")

        return token_obj

    @classmethod
    @trace_fn
    def create_new_token(cls, name: str, expiry_date: datetime, user_oid: str) -> Self:
        """
        Creates a new API token. The token is generated using the document's ID
        and a secure, random string.
        """
        random_part = secrets.token_urlsafe(128)[:128]
        token_obj = cls(
            name=name,
            expiry_date=expiry_date,
            user_oid=user_oid,
        )
        token_obj.save()
        token_value = f"{str(token_obj.id)}.{random_part}"
        token_obj.token = token_value
        token_obj.save()
        return token_obj
