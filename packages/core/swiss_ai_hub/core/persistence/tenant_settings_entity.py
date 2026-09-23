from mongoengine import Document, EmbeddedDocumentField, StringField

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity


class TenantSettingsEntity(Document):
    meta = {"collection": "tenant_settings", "strict": False}

    id = StringField(primary_key=True)
    chat_disclaimer = EmbeddedDocumentField(LocaleStringEntity)

    @classmethod
    @trace_fn
    def get_chat_disclaimer(cls, tenant_id: str) -> LocaleString | None:
        entity = cls.objects(id=tenant_id).first()
        return entity.chat_disclaimer.to_locale_string() if entity and entity.chat_disclaimer else None

    @classmethod
    @trace_fn
    def set_chat_disclaimer(cls, tenant_id: str, text: LocaleString) -> None:
        cls.objects(id=tenant_id).update_one(
            upsert=True,
            set__chat_disclaimer=LocaleStringEntity.from_locale_string(text),
        )
