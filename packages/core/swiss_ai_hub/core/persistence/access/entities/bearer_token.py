import secrets
from datetime import UTC, datetime
from typing import Self

from mongoengine import DateTimeField, Document, IntField, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

TOKEN_PREFIX = "sk-"


class BearerToken(Document):
    """A bearer API token. All tokens — user-issued and the static superuser token —
    share a single format: ``sk-<url-safe-random>``. Lookup is a direct, indexed
    match on the ``token`` field; no embedded ObjectId or parsing magic.
    """

    meta = {"collection": "tokens", "strict": False, "indexes": [{"fields": ["token"], "unique": True}]}
    version = IntField(default=1, db_field="_version")
    user_oid = StringField(required=True)
    name = StringField(required=True)
    token = StringField(required=True, unique=True)
    expiry_date = DateTimeField(required=True)

    @classmethod
    @trace_fn
    def verify_token(cls, token_str: str) -> Self:
        """Validates a bearer token by direct lookup and expiry check."""
        if not token_str.startswith(TOKEN_PREFIX):
            raise ValueError("Invalid token format")

        token_obj = cls.objects(token=token_str).first()
        if not token_obj:
            raise ValueError("Token not found")

        expiry_date = token_obj.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=UTC)

        if expiry_date < datetime.now(UTC):
            raise ValueError("Token expired")

        return token_obj

    @classmethod
    @trace_fn
    def create_new_token(cls, name: str, expiry_date: datetime, user_oid: str) -> Self:
        """Creates a new API token with a freshly generated ``sk-<random>`` value."""
        token_value = f"{TOKEN_PREFIX}{secrets.token_urlsafe(48)}"
        token_obj = cls(
            name=name,
            expiry_date=expiry_date,
            user_oid=user_oid,
            token=token_value,
        )
        token_obj.save()
        return token_obj

    @classmethod
    @trace_fn
    def upsert_static_token(cls, name: str, token_value: str, expiry_date: datetime, user_oid: str) -> Self:
        """Upserts a fixed-value bearer token (used to materialize the superuser token from env).

        Keyed by ``name`` + ``user_oid`` so repeated startup invocations reuse the same row.
        """
        if not token_value.startswith(TOKEN_PREFIX):
            raise ValueError(f"Static token must start with '{TOKEN_PREFIX}'")

        token_obj = cls.objects(name=name, user_oid=user_oid).first()
        if token_obj:
            token_obj.token = token_value
            token_obj.expiry_date = expiry_date
            token_obj.save()
            return token_obj
        token_obj = cls(name=name, user_oid=user_oid, token=token_value, expiry_date=expiry_date)
        token_obj.save()
        return token_obj
