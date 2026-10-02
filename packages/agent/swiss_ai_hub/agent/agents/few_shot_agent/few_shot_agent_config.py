from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import Checkbox

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig


class FewShotAgentConfig(MemoryFields, AttachedFilesFields, KnowledgeFields, ConversationFields, AgentConfig):
    """
    Configuration for FewShotAgent: the capability mixins plus the few-shot examples and their system prompt.

    Supports form duality pattern for form rendering and data validation.
    """

    few_shot: Annotated[
        FewShotStepConfig,
        Field(description="Few-shot prompting configuration with examples."),
    ]
    condense_question: Annotated[
        bool | Checkbox,
        Field(description="The examples are answered against one standalone question, so it is condensed by default."),
    ] = True

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode FewShotAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
            **cls.attached_files_form_elements(),
            **cls.knowledge_form_elements(),
            few_shot=FewShotStepConfig.as_form(),
        )
