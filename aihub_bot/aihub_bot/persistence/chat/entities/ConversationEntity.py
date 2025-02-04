from typing import List

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField


class User(EmbeddedDocument):
    user_id = StringField(required=True)


class Message(EmbeddedDocument):
    user_id = StringField(required=True)
    content = StringField(required=True)
    role = StringField(required=True)


class ConversationEntity(Document):
    meta = {
        "collection": "conversations",
        "strict": False,
    }
    conversation_id = StringField(required=True)
    users = ListField(EmbeddedDocumentField(User), required=False)
    messages = ListField(EmbeddedDocumentField(Message), required=False)

    @classmethod
    def create_conversation(cls, conversation_id: str, users: List[User],
                            messages: List[Message]) -> "ConversationEntity":
        conversation = cls(conversation_id=conversation_id, users=users, messages=messages)
        conversation.save()
        return conversation

    @classmethod
    def get_conversation_by_conversation_id(cls, conversation_id: str) -> "ConversationEntity":
        return cls.objects().filter(conversation_id=conversation_id).first()

    @classmethod
    def get_conversations_by_user(cls, user_id: str) -> List["ConversationEntity"]:
        return cls.objects().filter(users__user_id=user_id)

    @classmethod
    def get_conversations_by_users(cls, user_ids: List[str]) -> List["ConversationEntity"]:
        return cls.objects().filter(users__user_id__in=user_ids)

    @classmethod
    def add_user_to_conversation(cls, conversation_id: str, user: User) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.users.append(user)
        conversation.save()
        return conversation

    @classmethod
    def add_message_to_conversation(cls, conversation_id: str, message: Message) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.messages.append(message)
        conversation.save()
        return conversation

    @classmethod
    def get_messages_by_conversation_id(cls, conversation_id: str) -> List[Message]:
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        return conversation.messages

    @classmethod
    def remove_user_from_conversation(cls, conversation_id: str, user_id: str) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.users = [user for user in conversation.users if user.user_id != user_id]
        conversation.save()
        return conversation

    @classmethod
    def delete_conversation(cls, conversation_id: str) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.delete()
        return conversation
