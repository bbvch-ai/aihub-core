from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory
    from swiss_ai_hub.agent.imap.imap_command_error import ImapCommandError
    from swiss_ai_hub.agent.imap.mail_attachment_store import MailAttachmentStore
    from swiss_ai_hub.agent.imap.mail_parser import MailParser
    from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage

__all__ = [
    "ImapClient",
    "ImapClientFactory",
    "ImapCommandError",
    "MailAttachmentStore",
    "MailParser",
    "ParsedAttachment",
    "ParsedMessage",
]

_IMAP_CLIENT_MODULE = "swiss_ai_hub.agent.imap.imap_client"
_PARSED_MESSAGE_MODULE = "swiss_ai_hub.agent.imap.parsed_message"

_LAZY_IMPORTS = {
    "ImapClient": _IMAP_CLIENT_MODULE,
    "ImapClientFactory": _IMAP_CLIENT_MODULE,
    "ImapCommandError": "swiss_ai_hub.agent.imap.imap_command_error",
    "MailAttachmentStore": "swiss_ai_hub.agent.imap.mail_attachment_store",
    "MailParser": "swiss_ai_hub.agent.imap.mail_parser",
    "ParsedAttachment": _PARSED_MESSAGE_MODULE,
    "ParsedMessage": _PARSED_MESSAGE_MODULE,
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
