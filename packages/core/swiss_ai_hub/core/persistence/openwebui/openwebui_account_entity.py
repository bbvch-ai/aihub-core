from mongoengine import Document, StringField


class OpenWebuiAccountEntity(Document):
    """Which OpenWebUI account belongs to which of our users.

    OpenWebUI's code sandbox keys each user's home by the OpenWebUI user id, so an agent running code for a user
    needs that id to work in the same home the user's chats and Files panel see. The group sync matches the accounts
    anyway and records the result here.
    """

    meta = {
        "collection": "openwebui_accounts",
        "indexes": [{"fields": ["user_id"], "unique": True}],
    }

    user_id = StringField(required=True)
    openwebui_id = StringField(required=True)

    @classmethod
    def record_all(cls, openwebui_ids_by_user: dict[str, str]) -> None:
        """Replace the recorded accounts with this sync's matches; a user no longer matched loses their entry."""
        cls.objects(user_id__nin=list(openwebui_ids_by_user)).delete()
        for user_id, openwebui_id in openwebui_ids_by_user.items():
            cls.objects(user_id=user_id).update_one(set__openwebui_id=openwebui_id, upsert=True)

    @classmethod
    def openwebui_id_of(cls, user_id: str) -> str | None:
        account = cls.objects(user_id=user_id).first()
        return account.openwebui_id if account else None
