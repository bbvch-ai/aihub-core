from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.imap.attachment_text_extractor import AttachmentTextExtractor
    from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
    from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
    from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
    from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
    from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory
    from swiss_ai_hub.agent.imap.inbox_position import InboxPosition
    from swiss_ai_hub.agent.imap.inbox_watermark import InboxWatermark
    from swiss_ai_hub.agent.imap.mail_language_detector import MailLanguageDetector
    from swiss_ai_hub.agent.imap.mail_store import MailStore
    from swiss_ai_hub.agent.imap.mailbox_lease_lost_error import MailboxLeaseLostError
    from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
    from swiss_ai_hub.agent.imap.quoted_original import QuotedOriginal
    from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer
    from swiss_ai_hub.agent.imap.step_functions import (
        do_draft_replies,
        do_fetch_and_archive,
        do_file_message,
        do_file_messages,
        do_list_unread,
        do_list_unread_above,
    )
    from swiss_ai_hub.agent.imap.token_budget import TokenBudget

__all__ = [
    "AttachmentOutcome",
    "AttachmentTextExtractor",
    "ComposedReply",
    "DraftPromptBuilder",
    "ExtractedAttachment",
    "FetchedMail",
    "ImapClient",
    "ImapClientFactory",
    "InboxPosition",
    "InboxWatermark",
    "MailLanguageDetector",
    "MailStore",
    "MailboxLeaseLostError",
    "MailboxRunLease",
    "QuotedOriginal",
    "ReplyComposer",
    "TokenBudget",
    # Step functions - mailbox business logic shared by IMAP-backed blueprints
    "do_draft_replies",
    "do_fetch_and_archive",
    "do_file_message",
    "do_file_messages",
    "do_list_unread",
    "do_list_unread_above",
]

_EXTRACTED_ATTACHMENT_MODULE = "swiss_ai_hub.agent.imap.extracted_attachment"
_IMAP_CLIENT_MODULE = "swiss_ai_hub.agent.imap.imap_client"
_STEP_FUNCTIONS_MODULE = "swiss_ai_hub.agent.imap.step_functions"

_LAZY_IMPORTS = {
    "AttachmentOutcome": _EXTRACTED_ATTACHMENT_MODULE,
    "AttachmentTextExtractor": "swiss_ai_hub.agent.imap.attachment_text_extractor",
    "ComposedReply": "swiss_ai_hub.agent.imap.composed_reply",
    "DraftPromptBuilder": "swiss_ai_hub.agent.imap.draft_prompt_builder",
    "ExtractedAttachment": _EXTRACTED_ATTACHMENT_MODULE,
    "FetchedMail": "swiss_ai_hub.agent.imap.fetched_mail",
    "ImapClient": _IMAP_CLIENT_MODULE,
    "ImapClientFactory": _IMAP_CLIENT_MODULE,
    "InboxPosition": "swiss_ai_hub.agent.imap.inbox_position",
    "InboxWatermark": "swiss_ai_hub.agent.imap.inbox_watermark",
    "MailLanguageDetector": "swiss_ai_hub.agent.imap.mail_language_detector",
    "MailStore": "swiss_ai_hub.agent.imap.mail_store",
    "MailboxLeaseLostError": "swiss_ai_hub.agent.imap.mailbox_lease_lost_error",
    "MailboxRunLease": "swiss_ai_hub.agent.imap.mailbox_run_lease",
    "QuotedOriginal": "swiss_ai_hub.agent.imap.quoted_original",
    "ReplyComposer": "swiss_ai_hub.agent.imap.reply_composer",
    "TokenBudget": "swiss_ai_hub.agent.imap.token_budget",
    "do_draft_replies": _STEP_FUNCTIONS_MODULE,
    "do_fetch_and_archive": _STEP_FUNCTIONS_MODULE,
    "do_file_message": _STEP_FUNCTIONS_MODULE,
    "do_file_messages": _STEP_FUNCTIONS_MODULE,
    "do_list_unread": _STEP_FUNCTIONS_MODULE,
    "do_list_unread_above": _STEP_FUNCTIONS_MODULE,
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
