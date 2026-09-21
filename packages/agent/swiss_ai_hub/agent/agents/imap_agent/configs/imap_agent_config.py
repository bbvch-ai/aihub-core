from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig


class ImapAgentConfig(AgentConfig):
    """Configuration for the IMAP demonstrator agent — nests the reusable IMAP connection config and the grouped
    draft-email settings (which message to read, which model drafts it, and where the draft lands)."""

    imap: Annotated[
        ImapClientConfig,
        Field(description="IMAP connection used to read the mailbox."),
    ]
    draft: Annotated[
        DraftEmailSettings,
        Field(title="Draft email settings", description="Reply-drafting behaviour, model, and target folder."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            imap=ImapClientConfig.as_form(),
            draft=cls._draft_form(),
        )

    @staticmethod
    def _draft_form() -> DraftEmailSettings:
        """The drafting form without the fields only `EmailClassificationAgent` acts on.

        The token budget and the four attachment settings are read by `DraftPromptBuilder` and
        `AttachmentTextExtractor`, and this blueprint's drafting chain uses neither — it renders the original inline
        and never opens an attachment. Rendering them here would let an admin set a budget and switch attachment
        reading on to no effect, which is worse than not offering the choice. Overwriting the FormKit elements with
        plain values is what keeps them out of the rendered form, following `EmailClassificationAgentConfig`.

        As there, the values assigned are not the runtime values: `get_non_configurable_values()` walks only top-level
        fields, so a leaf baked inside a nested group keeps its declared default at runtime. Harmless while nothing
        here reads them. Wire this blueprint to the builder and extractor before removing any of these lines.
        """
        form = DraftEmailSettings.as_form()
        form.number_of_input_tokens = 32768
        form.include_attachments = False
        form.max_attachments_per_message = 3
        form.min_attachment_bytes = 8192
        form.attachment_char_limit = 20_000
        return form
