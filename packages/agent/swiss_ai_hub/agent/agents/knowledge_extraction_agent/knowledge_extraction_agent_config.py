from typing import Annotated, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeExtractionAgentConfig(RecordExtractionFields, ToolLoopFields, AgentConfig):
    """
    Configuration for KnowledgeExtractionAgent: the collections and path glob it works on, the extraction model and
    limits, whether a model searches for the documents first, and that search loop's limits (published by the runner
    with the blueprint's tools as options).

    The profile is the hard boundary of what a request may touch: whenever a profile is loaded, the document tools are
    switched on, `#` references only pick among the configured collections, and "every readable collection" is off, so a
    profile stored without these settings, or saved with them off, behaves the same. Without `discovery`, the default
    (`knowledge_documents.discovery`), every document in that boundary is read, so the table cannot miss one for its
    wording.
    """

    instructions: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="Instructions for this profile, added after the agent's own on how to find documents."),
    ] = None

    @model_validator(mode="after")
    def force_the_profile_boundary(self) -> Self:
        """Forced on load rather than baked into `as_form()`: the dispatcher merges only top-level non-configurable
        fields, so a fixed leaf inside `knowledge_documents` never reaches a stored profile and its default would apply.
        """
        self.knowledge_tool = self.knowledge_tool.model_copy(update={"every_readable_collection": False})
        self.knowledge_documents = self.knowledge_documents.model_copy(
            update={"enabled": True, "narrow_references": True}
        )
        return self

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            instructions=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.config.instructions.label"),
                help=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.config.instructions.help"),
                input_type="textarea",
                rows=4,
            ),
            knowledge_tool=KnowledgeToolConfig(sources=[KnowledgeToolSource.as_form()]),
            knowledge_documents=KnowledgeDocumentConfig(
                path_glob=KnowledgeDocumentConfig.path_glob_input(),
                discovery=KnowledgeDocumentConfig.discovery_input(),
            ),
            **cls.conversation_form_elements(),
            **cls.record_extraction_form_elements(),
        )
