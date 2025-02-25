from mongoengine import Document, ListField, StringField


class UserEntity(Document):
    meta = {
        "collection": "user-data",
        "strict": False,
    }
    id = StringField(primary_key=True)
    favorite_modules = ListField(StringField())

    @classmethod
    def by_oid(cls, user_oid: str) -> "UserEntity":
        return cls.objects.get(id=user_oid)
