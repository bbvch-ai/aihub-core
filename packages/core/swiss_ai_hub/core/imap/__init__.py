from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.imap.draft_email_settings import DraftEmailSettings
    from swiss_ai_hub.core.imap.email_classification_settings import EmailClassificationSettings
    from swiss_ai_hub.core.imap.imap_client_config import ImapClientConfig
    from swiss_ai_hub.core.imap.mail_category import MailCategory

__all__ = [
    "DraftEmailSettings",
    "EmailClassificationSettings",
    "ImapClientConfig",
    "MailCategory",
]

_LAZY_IMPORTS = {
    "DraftEmailSettings": "swiss_ai_hub.core.imap.draft_email_settings",
    "EmailClassificationSettings": "swiss_ai_hub.core.imap.email_classification_settings",
    "ImapClientConfig": "swiss_ai_hub.core.imap.imap_client_config",
    "MailCategory": "swiss_ai_hub.core.imap.mail_category",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
