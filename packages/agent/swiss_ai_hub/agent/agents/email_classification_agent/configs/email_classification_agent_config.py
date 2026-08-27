from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.imap import DraftEmailSettings, EmailClassificationSettings, ImapClientConfig


class EmailClassificationAgentConfig(AgentConfig):
    """Configuration for the email classification agent — the mailbox to read, the model to reason with, and the
    category taxonomy mail is sorted into."""

    imap: Annotated[
        ImapClientConfig,
        Field(description="IMAP connection used to read and file the mailbox."),
    ]
    llm: Annotated[
        LLMConfig,
        Field(description="The agent's main model. Used to classify unless a dedicated classifier model is picked."),
    ]
    classification: Annotated[
        EmailClassificationSettings,
        Field(title="Email classification", description="Categories, fallback folder, and classifier behaviour."),
    ]
    draft: Annotated[
        DraftEmailSettings,
        Field(
            title="Draft email settings",
            description="Reply drafting for the categories opted into it — model, prompt, drafts folder, and whether "
            "attachments are read.",
        ),
    ]

    @property
    def classifier_llm(self) -> LLMConfig:
        """The classifying model: the dedicated picker when set, otherwise the main model.

        Mirrors `RAGAgentConfig.task_llm` — classification is auxiliary work that reuses the main model's generation
        parameters, so only the model itself is separately selectable.
        """
        return self.llm.as_task_llm(self.classification.model_name or self.llm.model_name)

    @property
    def drafting_llm(self) -> LLMConfig:
        """The model that writes the reply body: the dedicated picker when set, otherwise the main model.

        Resolved the same way as `classifier_llm` rather than through `DraftEmailSettings.llm`, which builds a bare
        `LLMConfig` and so would silently drop the agent's configured generation parameters (temperature, timeout).
        """
        return self.llm.as_task_llm(self.draft.model_name or self.llm.model_name)

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            imap=cls._imap_form(),
            llm=LLMConfig.as_form(),
            classification=EmailClassificationSettings.as_form(),
            draft=cls._draft_form(),
        )

    @staticmethod
    def _imap_form() -> ImapClientConfig:
        """The mailbox form without the single-processed-folder move fields.

        `enable_move` and `processed_folder` are meaningless here: this blueprint always files, and always into a
        folder the classifier picked. Overwriting the FormKit elements with plain values makes the fields
        non-configurable, which is what keeps them out of the rendered form — rather than hiding them behind a
        `condition_if`, since a field that must not exist is not the same as one that is conditionally shown.

        The values assigned here are not the runtime values: `get_non_configurable_values()` only walks top-level
        fields, so a leaf baked inside a nested group never reaches the merged config and the field defaults apply.
        That is harmless because nothing on this blueprint reads either field — `do_file_messages` is always given the
        target folder explicitly. Do not add a reader without first making the value reach runtime.
        """
        form = ImapClientConfig.as_form()
        form.enable_move = True
        form.processed_folder = ""
        return form

    @staticmethod
    def _draft_form() -> DraftEmailSettings:
        """The drafting form without the fields that only make sense for a standalone drafting run.

        `source_folder` and `batch_size` belong to `ImapAgent`'s independent chain, which goes looking for candidates.
        This blueprint has no search to do: the batch is whatever it just classified, and the folder is wherever each
        message was filed. Overwriting the FormKit elements with plain values is what keeps the two fields out of the
        rendered form, following `_imap_form` — a field that must not exist is not the same as one conditionally hidden.

        As with `_imap_form`, the values assigned here are not the runtime values: `get_non_configurable_values()`
        walks only top-level fields, so a leaf baked inside a nested group keeps its declared default at runtime.
        Harmless because nothing on this blueprint reads either field — `do_draft_replies` is handed the batch and the
        drafts folder explicitly. Do not add a reader without first making the value reach runtime.
        """
        form = DraftEmailSettings.as_form()
        form.source_folder = ""
        form.batch_size = 1
        return form
