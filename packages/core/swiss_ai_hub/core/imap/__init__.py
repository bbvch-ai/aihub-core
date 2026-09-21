from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.imap.draft_email_settings import DraftEmailSettings
    from swiss_ai_hub.core.imap.email_classification_settings import EmailClassificationSettings
    from swiss_ai_hub.core.imap.imap_client_config import ImapClientConfig
    from swiss_ai_hub.core.imap.mail_category import MailCategory
    from swiss_ai_hub.core.imap.mail_parser import MAX_SUBJECT_CHARACTERS, MailParser
    from swiss_ai_hub.core.imap.parsed_attachment import ParsedAttachment
    from swiss_ai_hub.core.imap.parsed_message import ParsedMessage

__all__ = [
    "MAX_SUBJECT_CHARACTERS",
    "DraftEmailSettings",
    "EmailClassificationSettings",
    "ImapClientConfig",
    "MailCategory",
    "MailParser",
    "ParsedAttachment",
    "ParsedMessage",
]

_MAIL_PARSER_MODULE = "swiss_ai_hub.core.imap.mail_parser"

_LAZY_IMPORTS = {
    "MAX_SUBJECT_CHARACTERS": _MAIL_PARSER_MODULE,
    "DraftEmailSettings": "swiss_ai_hub.core.imap.draft_email_settings",
    "EmailClassificationSettings": "swiss_ai_hub.core.imap.email_classification_settings",
    "ImapClientConfig": "swiss_ai_hub.core.imap.imap_client_config",
    "MailCategory": "swiss_ai_hub.core.imap.mail_category",
    "MailParser": _MAIL_PARSER_MODULE,
    "ParsedAttachment": "swiss_ai_hub.core.imap.parsed_attachment",
    "ParsedMessage": "swiss_ai_hub.core.imap.parsed_message",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
