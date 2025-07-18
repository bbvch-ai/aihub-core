from datetime import UTC, datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    DoesNotExist,
    EmbeddedDocumentField,
    StringField,
)

from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class NotificationEntity(Document):
    """
    Represents a notification for a user in the database.
    """

    meta = {
        "collection": "notifications",
        "indexes": [{"fields": ["notification_id", "user_id"], "unique": True}],
    }

    notification_id = StringField(required=True)
    user_id = StringField(required=True)
    title = EmbeddedDocumentField(LocaleStringEntity)
    message = EmbeddedDocumentField(LocaleStringEntity)
    read = BooleanField(default=False)
    done = BooleanField(default=False)
    type = StringField(choices=("info", "warning", "success", "danger"), default="info")
    severity = StringField(choices=("low", "medium", "high"), default="medium")
    link = StringField()
    created_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    def get_for_user(
        cls,
        user_id: str,
        page: int,
        page_size: int,
        types: list[str] | None = None,
        severities: list[str] | None = None,
        read: bool | None = None,
        done: bool | None = None,
    ) -> tuple[list["NotificationEntity"], int]:
        """Retrieves a paginated list of notifications, with optional filters."""
        query = cls.objects(user_id=user_id)

        if types:
            query = query.filter(type__in=types)
        if severities:
            query = query.filter(severity__in=severities)
        if read is not None:
            query = query.filter(read=read)
        if done is not None:
            query = query.filter(done=done)

        offset = (page - 1) * page_size
        notifications = query.order_by("-created_at").skip(offset).limit(page_size).all()
        total = query.count()
        return notifications, total

    @classmethod
    def mark_as_read(cls, notification_id: str, user_id: str) -> "NotificationEntity":
        """Marks a specific notification as read."""
        notification = cls.objects(id=notification_id, user_id=user_id).first()
        if not notification:
            raise DoesNotExist("Notification not found.")
        notification.read = True
        notification.save()
        return notification

    @classmethod
    def mark_as_done(cls, notification_id: str, user_id: str) -> "NotificationEntity":
        """Marks a specific notification as done."""
        notification = cls.objects(id=notification_id, user_id=user_id).first()
        if not notification:
            raise DoesNotExist("Notification not found.")
        notification.done = True
        notification.save()
        return notification

    @classmethod
    def mark_all_as_read(cls, user_id: str) -> int:
        """Marks all of a user's unread notifications as read."""
        return cls.objects(user_id=user_id, read=False).update(read=True)

    @classmethod
    def mark_all_as_done(cls, user_id: str) -> int:
        """Marks all of a user's not-done notifications as done."""
        return cls.objects(user_id=user_id, done=False).update(done=True)
