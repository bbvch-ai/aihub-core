"""What the Beanie port of threads promises about storage (#1962).

The MongoEngine document ran `strict: False`, so stored threads may carry fields the model does not declare, and a
write must not drop them. The previous release reads threads with a MongoEngine document, so the readback tests use a
replica of it rather than trusting the shape by inspection.
"""

from datetime import datetime

import pytest
from bson import ObjectId
from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
    connect,
    disconnect,
)
from pymongo.asynchronous.database import AsyncDatabase

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User

pytestmark = pytest.mark.beanie

PREVIOUS_RELEASE_ALIAS = "previous_release_threads"


class PreviousReleaseUser(EmbeddedDocument):
    user_id = StringField(required=True)


class PreviousReleaseAgentInstanceRef(EmbeddedDocument):
    agent_id = StringField(required=True)
    agent_class = StringField(required=True)


class PreviousReleaseThread(Document):
    """The fields and collection of `ThreadEntity` as MongoEngine declared them before the port."""

    meta = {"collection": "threads", "strict": False, "db_alias": PREVIOUS_RELEASE_ALIAS}

    name = StringField(required=True)
    created_at = DateTimeField(required=True)
    process_class = StringField(required=False)
    process_id = StringField(required=False)
    process_walkthrough_id = StringField(required=False)
    users = ListField(EmbeddedDocumentField(PreviousReleaseUser))
    agents = ListField(EmbeddedDocumentField(PreviousReleaseAgentInstanceRef))


@pytest.fixture
def previous_release():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        alias=PREVIOUS_RELEASE_ALIAS,
    )
    yield PreviousReleaseThread
    disconnect(alias=PREVIOUS_RELEASE_ALIAS)


async def _thread() -> ThreadEntity:
    return await ThreadEntity.create_thread(
        "Quarterly report",
        users=[User(user_id="user-1")],
        agents=[AgentInstanceRef(agent_class="RAGAgent", agent_id="hr")],
    )


async def test_a_field_the_model_does_not_declare_survives_a_write(beanie_test_database: AsyncDatabase):
    thread = await _thread()
    await beanie_test_database["threads"].update_one({"_id": thread.id}, {"$set": {"pinned": True}})

    await ThreadEntity.update_thread_name(str(thread.id), "Renamed")

    stored = await beanie_test_database["threads"].find_one({"_id": thread.id})
    assert stored["pinned"] is True
    assert stored["name"] == "Renamed"


async def test_an_unset_process_field_is_left_out_rather_than_stored_as_null(beanie_test_database: AsyncDatabase):
    thread = await _thread()

    stored = await beanie_test_database["threads"].find_one({"_id": thread.id})

    assert "process_class" not in stored
    assert "process_walkthrough_id" not in stored


async def test_created_at_stays_naive_local_time(beanie_test_database: AsyncDatabase):
    """Converting it to UTC is #1971; until then a write must not change the convention under the readers."""
    before = datetime.now()
    thread = await _thread()

    stored = await beanie_test_database["threads"].find_one({"_id": thread.id})

    assert stored["created_at"].tzinfo is None
    assert abs((stored["created_at"] - before).total_seconds()) < 60


async def test_the_previous_release_reads_what_this_one_writes(previous_release):
    thread = await _thread()
    await thread.claim_for_process("CvProcess", "default", "walkthrough-1")

    read_back = previous_release.objects(id=thread.id).first()

    assert read_back.name == "Quarterly report"
    assert [user.user_id for user in read_back.users] == ["user-1"]
    assert [(agent.agent_class, agent.agent_id) for agent in read_back.agents] == [("RAGAgent", "hr")]
    assert read_back.process_walkthrough_id == "walkthrough-1"


async def test_this_release_reads_what_the_previous_one_wrote(previous_release):
    thread_id = ObjectId()
    previous_release(
        id=thread_id,
        name="Legacy",
        created_at=datetime.now(),
        users=[PreviousReleaseUser(user_id="user-2")],
        agents=[PreviousReleaseAgentInstanceRef(agent_class="RAGAgent", agent_id="legal")],
    ).save()

    thread = await ThreadEntity.get_thread_by_id(str(thread_id))

    assert thread.users == [User(user_id="user-2")]
    assert thread.agents == [AgentInstanceRef(agent_class="RAGAgent", agent_id="legal")]
    assert thread.process_class is None
