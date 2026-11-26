from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from bson import ObjectId
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import (
    LAST_USE_RESOLUTION,
    TOKEN_PREFIX,
    BearerToken,
)

STATIC_TOKEN_NAME = "superuser-static-token"


@pytest.fixture(autouse=True)
def mongo_connection() -> Generator[None]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture
def user_oid(mongo_connection: None) -> Generator[str]:
    oid = str(ObjectId())
    yield oid
    BearerToken.objects(user_oid=oid).delete()


@pytest.fixture
def other_user_oid(mongo_connection: None) -> Generator[str]:
    oid = str(ObjectId())
    yield oid
    BearerToken.objects(user_oid=oid).delete()


def _in_a_day() -> datetime:
    return datetime.now(UTC) + timedelta(days=1)


def _random_token_value() -> str:
    return f"{TOKEN_PREFIX}{ObjectId()}"


def _upsert_static_token(user_oid: str) -> BearerToken:
    return BearerToken.upsert_static_token(
        name=STATIC_TOKEN_NAME, token_value=_random_token_value(), expiry_date=_in_a_day(), user_oid=user_oid
    )


def _insert_row_from_before_the_static_flag(name: str, user_oid: str) -> ObjectId:
    """Rows written by earlier releases carry neither ``is_static`` nor ``last_used_at``."""
    row = {"name": name, "user_oid": user_oid, "token": _random_token_value(), "expiry_date": _in_a_day()}
    return BearerToken._get_collection().insert_one(row).inserted_id


def _stored_last_use(token: BearerToken) -> datetime:
    return BearerToken._as_utc(BearerToken.objects.get(id=token.id).last_used_at)


def test_first_use_is_recorded(user_oid: str) -> None:
    token = BearerToken.create_new_token("script", _in_a_day(), user_oid)
    used_at = datetime.now(UTC)

    token.record_use(used_at)

    assert abs(_stored_last_use(token) - used_at) < timedelta(milliseconds=1)


def test_use_within_resolution_is_not_written_again(user_oid: str) -> None:
    token = BearerToken.create_new_token("script", _in_a_day(), user_oid)
    first_use = datetime.now(UTC)
    token.record_use(first_use)

    BearerToken.objects.get(id=token.id).record_use(first_use + LAST_USE_RESOLUTION - timedelta(seconds=1))

    assert abs(_stored_last_use(token) - first_use) < timedelta(milliseconds=1)


def test_use_after_resolution_is_written(user_oid: str) -> None:
    token = BearerToken.create_new_token("script", _in_a_day(), user_oid)
    first_use = datetime.now(UTC)
    token.record_use(first_use)
    later_use = first_use + LAST_USE_RESOLUTION + timedelta(seconds=1)

    BearerToken.objects.get(id=token.id).record_use(later_use)

    assert abs(_stored_last_use(token) - later_use) < timedelta(milliseconds=1)


def test_issued_to_lists_own_tokens_newest_first_without_static_ones(user_oid: str, other_user_oid: str) -> None:
    older = BearerToken.create_new_token("older", _in_a_day(), user_oid)
    newer = BearerToken.create_new_token("newer", _in_a_day(), user_oid)
    BearerToken.create_new_token("someone else's", _in_a_day(), other_user_oid)
    _upsert_static_token(user_oid)

    assert [token.id for token in BearerToken.issued_to(user_oid)] == [newer.id, older.id]


def test_issued_to_lists_tokens_created_before_the_static_flag(user_oid: str) -> None:
    legacy_id = _insert_row_from_before_the_static_flag("script", user_oid)

    tokens = BearerToken.issued_to(user_oid)

    assert [token.id for token in tokens] == [legacy_id]
    assert tokens[0].last_used_at is None


def test_upsert_marks_a_static_row_seeded_before_the_flag(user_oid: str) -> None:
    _insert_row_from_before_the_static_flag(STATIC_TOKEN_NAME, user_oid)

    _upsert_static_token(user_oid)

    assert BearerToken.objects(user_oid=user_oid).count() == 1
    assert BearerToken.issued_to(user_oid) == []


def test_static_token_survives_a_revoke_by_its_owner(user_oid: str) -> None:
    static = _upsert_static_token(user_oid)

    assert BearerToken.revoke_issued(str(static.id), user_oid) is False
    assert BearerToken.objects(id=static.id).count() == 1


def test_revoke_issued_deletes_only_the_owners_token(user_oid: str, other_user_oid: str) -> None:
    token = BearerToken.create_new_token("script", _in_a_day(), user_oid)

    assert BearerToken.revoke_issued(str(token.id), other_user_oid) is False
    assert BearerToken.revoke_issued(str(token.id), user_oid) is True
    assert BearerToken.objects(id=token.id).count() == 0


def test_revoke_issued_rejects_a_malformed_id(user_oid: str) -> None:
    assert BearerToken.revoke_issued("not-an-object-id", user_oid) is False


def test_created_at_comes_from_the_document_id(user_oid: str) -> None:
    before = datetime.now(UTC).replace(microsecond=0)
    token = BearerToken.create_new_token("script", _in_a_day(), user_oid)

    assert before <= token.created_at <= datetime.now(UTC)
