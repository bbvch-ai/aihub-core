"""Every live collection has exactly one OpenWebUI knowledge entry, readable by the role groups that may read the
collection in our system, and nothing else we created survives a sync."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scim2_models import Group

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_knowledge_sync import OpenWebuiKnowledgeSync

MODULE = "swiss_ai_hub.core.infrastructure.openwebui.openwebui_knowledge_sync"
HR_GROUP = Group(id="g-hr", display_name="aihub:acme:HR")
SALES_GROUP = Group(id="g-sales", display_name="aihub:acme:Sales")
TENANT_RULES = {"acme": ["aihub.user.knowledge.>"]}
ROLE_RULES = {
    ("acme", "HR"): ["aihub.user.knowledge.hr.policies"],
    ("acme", "Sales"): ["aihub.user.knowledge.hr.reports"],
}
POLICIES = ("hr", "policies")
HR_READ = [{"principal_type": "group", "principal_id": "g-hr", "permission": "read"}]


def _entry(openwebui_id: str, database: str, namespace: str) -> MagicMock:
    return MagicMock(openwebui_id=openwebui_id, database=database, namespace=namespace)


def _client(existing: list[dict]) -> MagicMock:
    client = MagicMock()
    client.list_own_knowledge = AsyncMock(return_value=existing)
    client.create_knowledge = AsyncMock(return_value={"id": "new-id"})
    client.update_knowledge = AsyncMock()
    client.delete_knowledge = AsyncMock()
    return client


async def _sync(listing: dict, entries: list[MagicMock], existing: list[dict]) -> tuple[MagicMock, MagicMock]:
    client = _client(existing)
    with (
        patch.object(OpenWebuiKnowledgeSync, "listing", return_value=listing),
        patch(f"{MODULE}.OpenWebuiKnowledgeEntryEntity") as entity,
    ):
        entity.current_entries.return_value = entries
        await OpenWebuiKnowledgeSync(client, "en").sync(MagicMock(), [HR_GROUP, SALES_GROUP], TENANT_RULES, ROLE_RULES)
    return client, entity


@pytest.mark.asyncio
async def test_a_new_collection_gets_an_entry_readable_by_the_groups_that_may_read_it():
    client, entity = await _sync({POLICIES: ("HR / Policies", "Company policies")}, [], [])

    client.create_knowledge.assert_awaited_once()
    _, name, description, grants = client.create_knowledge.await_args.args
    assert (name, description) == ("HR / Policies", "Company policies")
    assert [grant.principal_id for grant in grants] == ["g-hr"]
    recorded_id, reference = entity.record.call_args.args
    assert (recorded_id, reference.database, reference.namespace) == ("new-id", "hr", "policies")


@pytest.mark.asyncio
async def test_an_unchanged_entry_is_left_alone():
    existing = [{"id": "k1", "name": "HR / Policies", "description": "", "access_grants": HR_READ}]

    client, _ = await _sync({POLICIES: ("HR / Policies", "")}, [_entry("k1", *POLICIES)], existing)

    client.create_knowledge.assert_not_awaited()
    client.update_knowledge.assert_not_awaited()
    client.delete_knowledge.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_renamed_collection_or_changed_access_updates_its_entry():
    existing = [{"id": "k1", "name": "HR / Old name", "description": "", "access_grants": []}]

    client, _ = await _sync({POLICIES: ("HR / Policies", "")}, [_entry("k1", *POLICIES)], existing)

    _, knowledge_id, name, _, grants = client.update_knowledge.await_args.args
    assert (knowledge_id, name, [grant.principal_id for grant in grants]) == ("k1", "HR / Policies", ["g-hr"])


@pytest.mark.asyncio
async def test_an_entry_deleted_in_openwebui_is_created_again():
    client, _ = await _sync({POLICIES: ("HR / Policies", "")}, [_entry("k1", *POLICIES)], [])

    client.create_knowledge.assert_awaited_once()


@pytest.mark.asyncio
async def test_the_entry_of_a_deleted_collection_is_removed():
    existing = [{"id": "k1", "name": "HR / Policies", "description": "", "access_grants": HR_READ}]

    client, entity = await _sync({}, [_entry("k1", *POLICIES)], existing)

    client.delete_knowledge.assert_awaited_once()
    assert client.delete_knowledge.await_args.args[1] == "k1"
    entity.retire.assert_called_once_with("k1")


@pytest.mark.asyncio
async def test_an_entry_already_gone_from_openwebui_is_retired_without_deleting():
    """OpenWebUI answers a delete of an id it does not know with 400, which would stop every later sync here."""
    gone, deleted_later = _entry("k1", *POLICIES), _entry("k2", "hr", "reports")
    existing = [{"id": "k2", "name": "HR / Reports", "description": "", "access_grants": []}]

    client, entity = await _sync({}, [gone, deleted_later], existing)

    assert [call.args[1] for call in client.delete_knowledge.await_args_list] == ["k2"]
    assert [call.args[0] for call in entity.retire.call_args_list] == ["k1", "k2"]


def test_databases_the_knowledge_page_hides_are_not_listed():
    shown, hidden = MagicMock(db_name="hr", deleting=False), MagicMock(db_name="sharedknowledge", deleting=False)
    namespace = MagicMock(namespace_name="policies", deleting=False, description=None)

    with (
        patch(f"{MODULE}.BucketEntity.get_all_buckets", return_value=[shown, hidden]),
        patch(f"{MODULE}.NamespaceEntity.get_namespaces_by_bucket", return_value=[namespace]),
        patch(f"{MODULE}.KnowledgeVisibility.is_browsable", side_effect=lambda bucket: bucket is shown),
        patch(f"{MODULE}.KnowledgeCollectionLabel.of", return_value="HR / Policies"),
    ):
        listing = OpenWebuiKnowledgeSync(_client([]), "en").listing()

    assert list(listing) == [("hr", "policies")]


@pytest.mark.asyncio
async def test_an_entry_we_created_but_never_recorded_is_removed():
    existing = [{"id": "orphan", "name": "HR / Policies", "description": "", "access_grants": []}]

    client, _ = await _sync({}, [], existing)

    assert client.delete_knowledge.await_args.args[1] == "orphan"
