from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ImapClientConfig(StepConfig):
    """IMAP connection configuration — injected as a StepConfig, used by steps to open an ImapClient."""

    host: Annotated[str | InputText, Field(description="IMAP server hostname (e.g. imap.example.com).")]
    port: Annotated[
        int | InputNumber,
        Field(default=993, description="IMAP server port — 993 for implicit TLS."),
        Gt(0),
    ]
    username: Annotated[str | InputText, Field(description="Mailbox login, usually the full email address.")]
    password: Annotated[
        str | Password,
        Field(default="", description="Mailbox password or app-specific token."),
    ]
    use_tls: Annotated[
        bool | ToggleSwitch,
        Field(default=True, description="Connect over implicit TLS. Disable only for plaintext test servers."),
    ]
    inbox_folder: Annotated[
        str | InputText,
        Field(default="INBOX", description="Mailbox folder to read incoming mail from."),
    ]
    max_messages: Annotated[
        int | InputNumber,
        Field(default=50, description="Maximum number of unread messages listed per run — keeps events small."),
        Gt(0),
    ]
    max_message_bytes: Annotated[
        int,
        Field(
            default=50_000_000,
            description="Deployment-fixed hard ceiling on the raw RFC822 size of a message. The size is checked "
            "before the body is downloaded, so a hostile or oversized mail is refused instead of being pulled into "
            "the agent's memory; this is what bounds peak fetch memory (max_body_bytes and max_attachment_bytes only "
            "trim what is kept after parsing).",
        ),
        Gt(0),
    ]
    max_body_bytes: Annotated[
        int,
        Field(
            default=1_000_000,
            description="Deployment-fixed cap on the decoded body carried in a fetch event; longer bodies are "
            "truncated so the persisted/streamed event cannot exceed NATS/FerretDB message-size limits.",
        ),
        Gt(0),
    ]
    max_attachment_bytes: Annotated[
        int,
        Field(
            default=10_000_000,
            description="Deployment-fixed cap on a single stored attachment; larger attachments are skipped so one "
            "message cannot overload the attachment bucket.",
        ),
        Gt(0),
    ]
    drafts_folder: Annotated[
        str | InputText,
        Field(default="Drafts", description="Mailbox folder drafts are written to (used by the draft-reply story)."),
    ]
    enable_move: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Enable moving a processed message into processed_folder. When off, the move step is skipped; "
            "when on, processed_folder must be set.",
        ),
    ]
    processed_folder: Annotated[
        str | InputText,
        Field(
            default="Processed", description="Mailbox folder a processed message is moved to when enable_move is on."
        ),
    ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            host=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.host.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.host.help"),
            ),
            port=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.port.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.port.help"),
                min=1,
                max=65535,
                step=1,
            ),
            username=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.username.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.username.help"),
            ),
            password=Password(
                label=LocaleString.from_i18n_path("lib.imap.config.password.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.password.help"),
            ),
            use_tls=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.use_tls.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.use_tls.help"),
            ),
            inbox_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.inbox_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.inbox_folder.help"),
            ),
            max_messages=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.max_messages.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.max_messages.help"),
                min=1,
                max=500,
                step=1,
            ),
            drafts_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.drafts_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.drafts_folder.help"),
            ),
            enable_move=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.enable_move.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.enable_move.help"),
                ref="move_fetched_mail_enabled",
            ),
            processed_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.processed_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.processed_folder.help"),
                condition_if="$get(move_fetched_mail_enabled).value",
            ),
        )
