from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException, Request
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity

from swiss_ai_hub.api.routes.file.figure_access import FigureAccess

_MODULE = "swiss_ai_hub.api.routes.file.figure_access"

THREAD_ID = str(ObjectId())
TENANT_ID = "tenant-1"
BUCKET = "manuals"
DOCUMENT = f"s3://{BUCKET}/devices/Nr 196 1.pdf"
KEY = "devices/__figures__/Nr_196_1_pdf/figure_0a1b2c3d4e5f6a7b.jpg"
REFERENCE = f"s3://{BUCKET}/{KEY}"
AGENT = ("rag_agent", "admin_agent")


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.values[key] = value


def _user(user_id: str = "member") -> UserIdentity:
    tenant = TenantIdentity(id=TENANT_ID, name="Tenant", access_rules=["aihub.user.>"])
    return UserIdentity(id=user_id, name="Viewer", email="v@example.com", roles=[], acting_within_tenant=tenant)


def _figure_node(reference: str = REFERENCE, source: str = DOCUMENT) -> dict:
    return {"content_type": "figure", "content": f"![Figure 1]({reference})", "source": source}


def _event(*nodes: dict) -> SimpleNamespace:
    return SimpleNamespace(agent_class=AGENT[0], agent_id=AGENT[1], event_data={"grounding_nodes": list(nodes)})


def _shown(*nodes: dict):
    return lambda thread_id, event_name: [_event(*nodes)] if event_name == "KnowledgeSearchedEvent" else []


@pytest.fixture
def thread() -> SimpleNamespace:
    stored = SimpleNamespace(users=[SimpleNamespace(user_id="member")], process_class=None, process_id=None)
    with patch(f"{_MODULE}.ThreadEntity.get_thread_by_id", AsyncMock(return_value=stored)):
        yield stored


@pytest.fixture
def events() -> MagicMock:
    with patch(f"{_MODULE}.PersistedAgentEventEntity.display_events_for_thread") as display_events:
        display_events.side_effect = _shown(_figure_node())
        yield display_events


@pytest.fixture
def agent_access() -> MagicMock:
    with patch(f"{_MODULE}.AccessChecker.from_user") as from_user:
        from_user.return_value.has_access_to_agent.return_value = True
        yield from_user.return_value.has_access_to_agent


async def _view(
    user: UserIdentity,
    redis: FakeRedis | None = None,
    key: str = KEY,
    thread_id: str = THREAD_ID,
    tenant_id: str = TENANT_ID,
) -> None:
    await FigureAccess.ensure_may_view(tenant_id, thread_id, BUCKET, key, user, redis or FakeRedis())


async def _refused(**kwargs) -> int:
    with pytest.raises(HTTPException) as error:
        await _view(**kwargs)
    return error.value.status_code


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events")
async def test_should_grant_a_thread_member_the_figure_the_agent_showed_and_cache_it(agent_access: MagicMock) -> None:
    redis = FakeRedis()

    await _view(_user(), redis)
    await _view(_user(), redis)

    agent_access.assert_called_once_with(*AGENT)
    assert len(redis.values) == 1


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events", "agent_access")
async def test_should_refuse_a_viewer_who_is_not_a_member_of_the_thread() -> None:
    assert await _refused(user=_user(user_id="outsider")) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events")
async def test_should_refuse_a_member_no_longer_allowed_to_use_the_agent(agent_access: MagicMock) -> None:
    agent_access.return_value = False

    assert await _refused(user=_user()) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events", "agent_access")
async def test_should_refuse_the_active_tenant_slug() -> None:
    assert await _refused(user=_user(), tenant_id="active") == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events", "agent_access")
async def test_should_refuse_a_figure_the_thread_never_showed() -> None:
    other_key = "devices/__figures__/Nr_196_1_pdf/figure_ffffffffffffffff.jpg"

    assert await _refused(user=_user(), key=other_key) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "agent_access")
async def test_should_refuse_a_reference_found_only_in_a_text_node(events: MagicMock) -> None:
    events.side_effect = _shown({"content_type": "text", "content": f"see ![x]({REFERENCE})", "source": DOCUMENT})

    assert await _refused(user=_user()) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "agent_access")
async def test_should_refuse_a_figure_of_another_document_planted_in_a_node(events: MagicMock) -> None:
    events.side_effect = _shown(_figure_node(source="s3://uploads/attacker/notes.md"))

    assert await _refused(user=_user()) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "agent_access")
async def test_should_grant_a_figure_whose_folder_path_holds_spaces(events: MagicMock) -> None:
    key = "Geräte (alt)/__figures__/a_b_pdf/figure_1.png"
    events.side_effect = _shown(_figure_node(f"s3://{BUCKET}/{key}", source=f"s3://{BUCKET}/Geräte (alt)/a b.pdf"))

    await _view(_user(), key=key)


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "agent_access")
async def test_should_not_match_a_longer_key_that_starts_with_the_requested_one(events: MagicMock) -> None:
    events.side_effect = _shown(_figure_node(f"{REFERENCE}.png"))

    assert await _refused(user=_user()) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("thread", "events", "agent_access")
@pytest.mark.parametrize(
    "key",
    [
        "devices/a.pdf",
        "devices/__figures__/doc/figure.svg",
        "devices/__figures__/../secret/figure.jpg",
        "devices/figure.jpg",
    ],
)
async def test_should_refuse_keys_outside_the_figure_folders(key: str) -> None:
    assert await _refused(user=_user(), key=key) == 403


@pytest.mark.asyncio
@pytest.mark.usefixtures("events", "agent_access")
async def test_should_refuse_an_invalid_thread_id_like_a_foreign_one() -> None:
    assert await _refused(user=_user(), thread_id="not-an-object-id") == 403


def _request(**headers: str) -> Request:
    raw = [(name.replace("_", "-").encode(), value.encode()) for name, value in headers.items()]
    return Request({"type": "http", "headers": raw})


@pytest.mark.parametrize("destination", ["image", "document"])
def test_should_accept_an_image_tag_or_a_new_tab_opened_from_the_same_origin(destination: str) -> None:
    FigureAccess.ensure_requested_from_openwebui(_request(sec_fetch_site="same-origin", sec_fetch_dest=destination))


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"sec_fetch_site": "none", "sec_fetch_dest": "document"},
        {"sec_fetch_site": "same-site", "sec_fetch_dest": "image"},
        {"sec_fetch_site": "same-site", "sec_fetch_dest": "document"},
        {"sec_fetch_site": "same-origin", "sec_fetch_dest": "empty"},
        {"sec_fetch_site": "same-origin", "sec_fetch_dest": "iframe"},
        {"sec_fetch_site": "cross-site", "sec_fetch_dest": "image"},
    ],
)
def test_should_refuse_a_pasted_url_a_script_or_another_site(headers: dict[str, str]) -> None:
    with pytest.raises(HTTPException) as error:
        FigureAccess.ensure_requested_from_openwebui(_request(**headers))

    assert error.value.status_code == 403
