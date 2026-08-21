from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
    from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory
    from swiss_ai_hub.agent.imap.mail_parser import MailParser
    from swiss_ai_hub.agent.imap.mail_store import MailStore
    from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage
    from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer
    from swiss_ai_hub.agent.imap.step_functions import (
        do_fetch_and_archive,
        do_file_message,
        do_file_messages,
        do_list_unread,
    )

__all__ = [
    "FetchedMail",
    "ImapClient",
    "ImapClientFactory",
    "MailParser",
    "MailStore",
    "ParsedAttachment",
    "ParsedMessage",
    "ReplyComposer",
    # Step functions - mailbox business logic shared by IMAP-backed blueprints
    "do_fetch_and_archive",
    "do_file_message",
    "do_file_messages",
    "do_list_unread",
]

_IMAP_CLIENT_MODULE = "swiss_ai_hub.agent.imap.imap_client"
_PARSED_MESSAGE_MODULE = "swiss_ai_hub.agent.imap.parsed_message"
_STEP_FUNCTIONS_MODULE = "swiss_ai_hub.agent.imap.step_functions"

_LAZY_IMPORTS = {
    "FetchedMail": "swiss_ai_hub.agent.imap.fetched_mail",
    "ImapClient": _IMAP_CLIENT_MODULE,
    "ImapClientFactory": _IMAP_CLIENT_MODULE,
    "MailParser": "swiss_ai_hub.agent.imap.mail_parser",
    "MailStore": "swiss_ai_hub.agent.imap.mail_store",
    "ParsedAttachment": _PARSED_MESSAGE_MODULE,
    "ParsedMessage": _PARSED_MESSAGE_MODULE,
    "ReplyComposer": "swiss_ai_hub.agent.imap.reply_composer",
    "do_fetch_and_archive": _STEP_FUNCTIONS_MODULE,
    "do_file_message": _STEP_FUNCTIONS_MODULE,
    "do_file_messages": _STEP_FUNCTIONS_MODULE,
    "do_list_unread": _STEP_FUNCTIONS_MODULE,
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
