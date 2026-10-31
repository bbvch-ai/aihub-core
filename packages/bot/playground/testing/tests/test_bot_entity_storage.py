"""What the Beanie port of the bot's entities promises about storage (#1966).

A bot release rolls out next to the previous one, which reads with strict MongoEngine documents: a field it does not
declare makes its read fail. The readback tests therefore use replicas of those documents rather than trusting the
shape by inspection.
"""

from datetime import UTC, datetime

import pytest
from mongoengine import (
    BooleanField,
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
from pymongo.errors import DuplicateKeyError
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings

from swiss_ai_hub.bot.persistence.entities.conversation_entity import (
    Content,
    ConversationEntity,
    ConversationTracker,
    Message,
)
from swiss_ai_hub.bot.persistence.entities.path_entity import PathEntity

pytestmark = pytest.mark.beanie

PREVIOUS_RELEASE_ALIAS = "previous_release_bot"
BOT_ID = "bot-1"


class PreviousReleaseContent(EmbeddedDocument):
    text = StringField(required=True)
    type = StringField(required=True)


class PreviousReleaseMessage(EmbeddedDocument):
    user_id = StringField(required=True)
    content = ListField(EmbeddedDocumentField(PreviousReleaseContent), required=True)
    role = StringField(required=True)
    name = StringField(required=True)


class PreviousReleaseConversation(Document):
    """`ConversationEntity` as MongoEngine declared it before the port."""

    meta = {"collection": "bot_conversations", "db_alias": PREVIOUS_RELEASE_ALIAS, "strict": True}

    is_mentioned = BooleanField(default=False)
    conversation_id = StringField(required=True)
    bot_id = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(PreviousReleaseMessage), required=False)
    last_activity = DateTimeField()


class PreviousReleaseTracker(Document):
    meta = {"collection": "bot_conversation_trackers", "db_alias": PREVIOUS_RELEASE_ALIAS, "strict": True}

    conversation_id = StringField(required=True)
    bot_id = StringField(required=True)
    created_at = DateTimeField()
    explicitly_deleted = BooleanField(default=False)


class PreviousReleaseCredentials(EmbeddedDocument):
    APP_TYPE = StringField(required=False)
    APP_ID = StringField(required=False)
    APP_PASSWORD = StringField(required=False)
    APP_TENANTID = StringField(required=False)


class PreviousReleasePath(Document):
    meta = {"collection": "bot_paths", "db_alias": PREVIOUS_RELEASE_ALIAS, "strict": True}

    path = StringField(required=True)
    credentials = EmbeddedDocumentField(PreviousReleaseCredentials, required=True)
    system_message = StringField(required=False)
    slack_token = StringField(required=False)


@pytest.fixture
def previous_release():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        alias=PREVIOUS_RELEASE_ALIAS,
        uuidRepresentation="standard",
    )
    yield
    disconnect(alias=PREVIOUS_RELEASE_ALIAS)


def _message(text: str) -> Message:
    return Message(user_id="user-1", content=[Content(text=text, type="text")], role="user", name="User")


async def test_the_previous_release_reads_a_conversation_this_one_wrote(previous_release):
    await ConversationEntity.add_messages_to_conversation("conv-1", BOT_ID, [_message("hello")])
    await ConversationEntity.set_conversation_is_mentioned("conv-1", BOT_ID, is_mentioned=True)

    read_back = PreviousReleaseConversation.objects(conversation_id="conv-1", bot_id=BOT_ID).first()

    assert read_back.is_mentioned is True
    assert [message.content[0].text for message in read_back.messages] == ["hello"]


async def test_a_conversation_the_previous_release_wrote_keeps_its_history(previous_release):
    PreviousReleaseConversation(
        conversation_id="conv-2",
        bot_id=BOT_ID,
        messages=[
            PreviousReleaseMessage(
                user_id="user-1", content=[PreviousReleaseContent(text="before", type="text")], role="user", name="U"
            )
        ],
        last_activity=datetime.now(UTC),
    ).save()

    await ConversationEntity.add_messages_to_conversation("conv-2", BOT_ID, [_message("after")])

    messages = await ConversationEntity.get_messages_by_conversation_id("conv-2", BOT_ID)
    assert [message.content[0].text for message in messages] == ["before", "after"]


async def test_a_slack_thread_is_stored_without_its_bot_and_team_prefix():
    slack_bot_id = "B123:T456"

    await ConversationEntity.add_messages_to_conversation(f"{slack_bot_id}:C789:1700000000.000100", slack_bot_id, [])

    stored = await ConversationEntity.find_one({"bot_id": slack_bot_id})
    assert stored.conversation_id == "C789:1700000000.000100"


async def test_a_conversation_is_unique_per_bot():
    await ConversationEntity.create_conversation("conv-3", BOT_ID, [])

    with pytest.raises(DuplicateKeyError):
        await ConversationEntity.create_conversation("conv-3", BOT_ID, [])


async def test_tracking_a_conversation_again_keeps_when_it_was_first_seen(
    beanie_test_database: AsyncDatabase, previous_release
):
    await ConversationTracker.track_conversation("conv-4", BOT_ID)
    first_seen = (await ConversationTracker.get_tracker("conv-4", BOT_ID)).created_at
    await ConversationTracker.mark_explicitly_deleted("conv-4", BOT_ID)

    await ConversationTracker.track_conversation("conv-4", BOT_ID)

    read_back = PreviousReleaseTracker.objects(conversation_id="conv-4", bot_id=BOT_ID).first()
    assert read_back.explicitly_deleted is False
    assert (await ConversationTracker.get_tracker("conv-4", BOT_ID)).created_at == first_seen
    assert await beanie_test_database["bot_conversation_trackers"].count_documents({"conversation_id": "conv-4"}) == 1


async def test_a_path_the_previous_release_wrote_still_configures_the_bot(previous_release):
    PreviousReleasePath(
        path="/api/v1/bot",
        credentials=PreviousReleaseCredentials(APP_TYPE="SingleTenant", APP_ID="app", APP_PASSWORD="secret"),
        slack_token="xoxb-token",
    ).save()

    credentials = await PathEntity.get_credentials_by_path("/api/v1/bot")

    assert credentials.APP_ID == "app"
    assert credentials.APP_TENANTID is None
    assert await PathEntity.get_slack_token_by_path("/api/v1/bot") == "xoxb-token"
    assert await PathEntity.get_system_message_by_path("/api/v1/bot") is None


async def test_the_indexes_keep_their_names(beanie_test_database: AsyncDatabase):
    conversation_indexes = await beanie_test_database["bot_conversations"].index_information()
    tracker_indexes = await beanie_test_database["bot_conversation_trackers"].index_information()
    path_indexes = await beanie_test_database["bot_paths"].index_information()

    assert conversation_indexes["conversation_id_1_bot_id_1"]["unique"] is True
    assert tracker_indexes["conversation_id_1_bot_id_1"]["unique"] is True
    assert path_indexes["path_1"]["unique"] is True
