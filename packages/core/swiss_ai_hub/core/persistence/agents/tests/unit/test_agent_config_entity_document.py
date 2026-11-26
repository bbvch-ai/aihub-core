"""What the Beanie port of agent profiles promises about storage (#1961).

Profiles are written in the shape MongoEngine wrote them, so rolling the API image back needs no data change. The
previous release reads them with a strict MongoEngine document, which raises on a field it does not declare, so
the readback test uses a replica of that document rather than trusting the shape by inspection.
"""

from datetime import datetime

import pytest
from mongoengine import DateTimeField, DictField, Document, EmbeddedDocumentField, StringField, connect, disconnect
from pymongo.asynchronous.database import AsyncDatabase

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_change_hook import AgentConfigChangeHook
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

pytestmark = pytest.mark.beanie

PREVIOUS_RELEASE_ALIAS = "previous_release"


class PreviousReleaseAgentConfig(Document):
    """The fields and collection of `AgentConfigEntityDocument` as MongoEngine declared them before the port."""

    meta = {"collection": "agent_configs", "db_alias": PREVIOUS_RELEASE_ALIAS}

    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    icon = StringField(required=True)
    config_data = DictField(required=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()


@pytest.fixture
def previous_release():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        alias=PREVIOUS_RELEASE_ALIAS,
    )
    yield PreviousReleaseAgentConfig
    disconnect(alias=PREVIOUS_RELEASE_ALIAS)


def _profile(config_data: dict | None = None) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id="hr",
        name=LocaleString(en="HR", de="Personal"),
        description=LocaleString(en="HR profile"),
        icon="meteor-icons:robot",
        config_data=config_data or {"llm": {"temperature": 0.2}, "retired": True},
    )


async def _stored(beanie_test_database: AsyncDatabase, profile: AgentConfigEntityDocument) -> dict:
    return await beanie_test_database["agent_configs"].find_one({"_id": profile.id})


async def test_an_unset_locale_is_left_out_rather_than_stored_as_null(beanie_test_database: AsyncDatabase):
    profile = await _profile().insert()

    stored = await _stored(beanie_test_database, profile)

    assert stored["name"] == {"en": "HR", "de": "Personal"}
    assert stored["description"] == {"en": "HR profile"}
    assert set(stored) == {
        "_id",
        "agent_class",
        "agent_id",
        "name",
        "description",
        "icon",
        "config_data",
        "created_at",
        "updated_at",
    }


async def test_saving_changes_rewrites_a_changed_field_whole(beanie_test_database: AsyncDatabase):
    """A key dropped from `config_data` must be dropped in storage, not left behind by a dotted `$set`."""
    profile = await _profile().insert()

    profile.config_data = {"llm": {"temperature": 0.7}}
    await profile.save_changes()

    assert (await _stored(beanie_test_database, profile))["config_data"] == {"llm": {"temperature": 0.7}}


async def test_saving_changes_leaves_fields_written_elsewhere_alone(beanie_test_database: AsyncDatabase):
    profile = await _profile().insert()
    await beanie_test_database["agent_configs"].update_one({"_id": profile.id}, {"$set": {"icon": "mage:book-open"}})

    profile.config_data = {"llm": {"temperature": 0.7}}
    await profile.save_changes()

    assert (await _stored(beanie_test_database, profile))["icon"] == "mage:book-open"


async def test_every_write_moves_updated_at():
    profile = await _profile().insert()
    inserted_at = profile.updated_at

    profile.icon = "mage:book-open"
    await profile.save_changes()

    stored = await AgentConfigEntityDocument.get(profile.id)
    assert stored.updated_at > inserted_at.replace(tzinfo=None)


async def test_the_previous_release_reads_what_this_one_writes(previous_release):
    profile = await _profile().insert()
    profile.config_data = {"llm": {"temperature": 0.7}}
    await profile.save_changes()

    read_back = previous_release.objects(agent_class="RAGAgent", agent_id="hr").first()

    assert read_back.name.en == "HR"
    assert read_back.name.fr is None
    assert read_back.config_data == {"llm": {"temperature": 0.7}}
    assert isinstance(read_back.updated_at, datetime)


async def test_this_release_reads_what_the_previous_one_wrote(previous_release):
    previous_release(
        agent_class="RAGAgent",
        agent_id="legal",
        name=LocaleStringEntity(en="Legal"),
        description=LocaleStringEntity(en="Legal profile"),
        icon="meteor-icons:robot",
        config_data={"llm": {"temperature": 0.1}},
    ).save()

    profile = await AgentConfigEntityDocument.find_for_class_and_id("RAGAgent", "legal")

    assert profile.name == LocaleString(en="Legal")
    assert profile.config_data == {"llm": {"temperature": 0.1}}


@pytest.mark.parametrize("write", ["insert", "save_changes", "delete"])
async def test_every_write_asks_openwebui_to_resync(write: str, monkeypatch: pytest.MonkeyPatch):
    notified: list[bool] = []
    monkeypatch.setattr(AgentConfigChangeHook, "notify", lambda: notified.append(True))
    profile = _profile()
    if write != "insert":
        await profile.insert()
        notified.clear()
        profile.icon = "mage:book-open"

    await getattr(profile, write)()

    assert notified == [True]
