import secrets
from datetime import UTC, datetime, timedelta
from typing import Self

from bson import ObjectId
from mongoengine import BooleanField, DateTimeField, Document, IntField, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

TOKEN_PREFIX = "sk-"
LAST_USE_RESOLUTION = timedelta(minutes=5)


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
    last_used_at = DateTimeField()
    is_static = BooleanField(default=False)

    @property
    def created_at(self) -> datetime:
        return self.id.generation_time

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """MongoEngine hands back naive datetimes that are UTC by convention."""
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    @classmethod
    @trace_fn
    def verify_token(cls, token_str: str) -> Self:
        """Validates a bearer token by direct lookup and expiry check.

        Failure modes are distinct in the error message so operators can tell
        malformed inputs (wrong prefix — often a misconfigured client or a stale
        token from before the ``sk-`` migration) from unknown tokens (revoked
        or never existed) from expired tokens (rotation overdue).
        """
        if not token_str.startswith(TOKEN_PREFIX):
            raise ValueError(f"Malformed token: missing '{TOKEN_PREFIX}' prefix")

        token_obj = cls.objects(token=token_str).first()
        if not token_obj:
            raise ValueError("Unknown token: no matching row (revoked or never issued)")

        if cls._as_utc(token_obj.expiry_date) < datetime.now(UTC):
            raise ValueError("Expired token: expiry is in the past")

        return token_obj

    @trace_fn
    def record_use(self, used_at: datetime) -> None:
        """Writes at most once per ``LAST_USE_RESOLUTION``, so a script calling the API in a loop does not turn
        every request into a database write."""
        if self.last_used_at is not None and self._as_utc(self.last_used_at) > used_at - LAST_USE_RESOLUTION:
            return
        self.update(set__last_used_at=used_at)
        self.last_used_at = used_at

    @classmethod
    @trace_fn
    def issued_to(cls, user_oid: str) -> list[Self]:
        """The user's own tokens, newest first. Static tokens are left out: internal services authenticate with them,
        and revoking one would cut those services off until the next restart."""
        return list(cls.objects(user_oid=user_oid, is_static__ne=True).order_by("-id"))

    @classmethod
    @trace_fn
    def revoke_issued(cls, token_id: str, user_oid: str) -> bool:
        """False when the user holds no such token, so a caller cannot tell another user's token from none."""
        if not ObjectId.is_valid(token_id):
            return False
        return cls.objects(id=token_id, user_oid=user_oid, is_static__ne=True).delete() > 0

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

        Keyed by ``name`` + ``user_oid`` so repeated startup invocations reuse the same row. Marked static so its owner
        can neither see nor revoke it through the token endpoints.
        """
        if not token_value.startswith(TOKEN_PREFIX):
            raise ValueError(f"Static token must start with '{TOKEN_PREFIX}'")

        token_obj = cls.objects(name=name, user_oid=user_oid).first()
        if token_obj:
            token_obj.token = token_value
            token_obj.expiry_date = expiry_date
            token_obj.is_static = True
            token_obj.save()
            return token_obj
        token_obj = cls(name=name, user_oid=user_oid, token=token_value, expiry_date=expiry_date, is_static=True)
        token_obj.save()
        return token_obj
