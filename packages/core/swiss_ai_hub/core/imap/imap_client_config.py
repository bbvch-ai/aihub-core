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
    drafts_folder: Annotated[
        str | InputText,
        Field(default="Drafts", description="Mailbox folder drafts are written to (used by the draft-reply story)."),
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
        )
