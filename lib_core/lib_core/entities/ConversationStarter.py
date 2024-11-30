from typing import List

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, IntField, ListField, StringField

from lib_core.records.conversation_starters.ConversationStarterResponse import ConversationStarterResponse


class ConversationStarterMessage(EmbeddedDocument):
    role = StringField(required=True)
    content = StringField(required=True)
    name = StringField()


class ConversationStarter(Document):
    meta = {
        "collection": "conversationstarter",
        "strict": False,
    }
    version = IntField(default=1, db_field="_version")
    source_user_email = StringField(required=True)
    target_user_email = StringField(required=True)
    source_agent_id = StringField(required=True)
    target_agent_id = StringField(required=True)
    source_conversation_id = StringField(required=False)
    target_conversation_id = StringField(required=False)
    title = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(ConversationStarterMessage))

    @staticmethod
    def for_user_and_agent(organization_shortname: str, email: str, agent_ids: List[str]):
        return ConversationStarter.objects.using(organization_shortname).filter(
            target_user_email=email, target_agent_id__in=agent_ids
        )

    def to_record(self):
        return ConversationStarterResponse(**self.to_mongo().to_dict())
