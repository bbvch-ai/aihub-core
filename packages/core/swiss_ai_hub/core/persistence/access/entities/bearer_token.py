import secrets
from datetime import UTC, datetime
from typing import Self

from beanie import Document
from bson import ObjectId
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

TOKEN_PREFIX = "sk-"


class BearerToken(Document):
    """A bearer API token. All tokens — user-issued and the static superuser token —
    share a single format: ``sk-<url-safe-random>``. Lookup is a direct, indexed
    match on the ``token`` field; no embedded ObjectId or parsing magic.

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`, and a token row losing
    a field on rewrite would be silent data loss on the authentication path.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    version: int = Field(default=1, alias="_version")
    user_oid: str
    name: str
    token: str
    expiry_date: datetime

    class Settings:
        name = "tokens"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [IndexModel([("token", ASCENDING)], unique=True)]

    @classmethod
    @trace_fn
    async def verify_token(cls, token_str: str) -> Self:
        """Validates a bearer token by direct lookup and expiry check.

        Failure modes are distinct in the error message so operators can tell
        malformed inputs (wrong prefix — often a misconfigured client or a stale
        token from before the ``sk-`` migration) from unknown tokens (revoked
        or never existed) from expired tokens (rotation overdue).
        """
        if not token_str.startswith(TOKEN_PREFIX):
            raise ValueError(f"Malformed token: missing '{TOKEN_PREFIX}' prefix")

        token_obj = await cls.find_one({"token": token_str})
        if not token_obj:
            raise ValueError("Unknown token: no matching row (revoked or never issued)")

        expiry_date = token_obj.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=UTC)

        if expiry_date < datetime.now(UTC):
            raise ValueError("Expired token: expiry is in the past")

        return token_obj

    @classmethod
    @trace_fn
    async def create_new_token(cls, name: str, expiry_date: datetime, user_oid: str) -> Self:
        """Creates a new API token with a freshly generated ``sk-<random>`` value."""
        token_value = f"{TOKEN_PREFIX}{secrets.token_urlsafe(48)}"
        return await cls(name=name, expiry_date=expiry_date, user_oid=user_oid, token=token_value).insert()

    @classmethod
    @trace_fn
    async def upsert_static_token(cls, name: str, token_value: str, expiry_date: datetime, user_oid: str) -> Self:
        """Upserts a fixed-value bearer token (used to materialize the superuser token from env).

        Keyed by ``name`` + ``user_oid`` so repeated startup invocations reuse the same row.
        """
        if not token_value.startswith(TOKEN_PREFIX):
            raise ValueError(f"Static token must start with '{TOKEN_PREFIX}'")

        token_obj = await cls.find_one({"name": name, "user_oid": user_oid})
        if token_obj:
            token_obj.token = token_value
            token_obj.expiry_date = expiry_date
            await token_obj.save_changes()
            return token_obj
        return await cls(name=name, user_oid=user_oid, token=token_value, expiry_date=expiry_date).insert()

    @classmethod
    @trace_fn
    async def find_for_user(cls, user_oid: str) -> list[Self]:
        return await cls.find({"user_oid": user_oid}).to_list()

    @classmethod
    @trace_fn
    async def get_for_user(cls, token_id: str, user_oid: str) -> Self | None:
        """The user's token with `token_id`; None for another user's token or an id that is not an ObjectId."""
        if not ObjectId.is_valid(token_id):
            return None
        return await cls.find_one({"_id": ObjectId(token_id), "user_oid": user_oid})
