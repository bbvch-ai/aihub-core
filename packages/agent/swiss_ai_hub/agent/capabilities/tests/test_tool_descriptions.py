"""Every tool description fits the 1024 characters OpenAI-style tool schemas are held to, in every language, and
carries no Python signature: the parameters reach the model as a schema already."""

from unittest.mock import MagicMock

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import UserUploadedFile
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import KnowledgeDocumentTools
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import RecordSelectionTools
from swiss_ai_hub.agent.capabilities.sandbox.sandbox_tools import SandboxTools
from swiss_ai_hub.agent.capabilities.sandbox.user_files_tools import UserFilesTools
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch import WebFetch
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_fields import WebFetchFields
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

LIMIT = 1024
LOCALES = ["de", "en", "fr", "it"]
MOST_FILES_A_MESSAGE_CARRIES = [
    UserUploadedFile(
        filename=f"quarterly-financial-report-{index}-2026.xlsx",
        file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_id=f"{index}{index}{index}{index}{index}{index}{index}{index}-1111-4111-8111-111111111111",
    )
    for index in range(1, 5)
]


class EveryToolAgent(Agent):
    """Offers every capability that runs as a tool, so each of their descriptions is checked."""

    tools = ToolLoop.over(
        Knowledge,
        AttachedFiles,
        Memory,
        WebFetch,
        SandboxTools,
        UserFilesTools,
        KnowledgeDocumentTools,
        RecordSelectionTools,
        RecordExtraction,
    )


class _Config(
    MemoryFields,
    AttachedFilesFields,
    RecordExtractionFields,
    KnowledgeToolFields,
    KnowledgeFields,
    WebFetchFields,
    ToolLoopFields,
    ConversationFields,
    AgentConfig,
):
    pass


def _config() -> _Config:
    """A real config with every optional tool on, so the descriptions of the tools a profile can switch on are checked
    too; a stand-in config would make those specs offer nothing."""
    return _Config(
        agent_id="descriptions",
        name=LocaleString(en="Descriptions"),
        description=LocaleString(en="Descriptions fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True),
    )


def _context(locale: str) -> ToolContext:
    return ToolContext.model_construct(
        agent_config=_config(),
        displayer=MagicMock(),
        t=AgentLocaleHandler(locale),
        files=MOST_FILES_A_MESSAGE_CARRIES,
        knowledge_references=[],
    )


@pytest.mark.parametrize("locale", LOCALES)
def test_every_function_tool_description_fits_without_its_signature(locale: str) -> None:
    tools = EveryToolAgent.tool_set("tools").function_tools(_context(locale), ToolLoopConfig())
    definitions = {
        name: EveryToolAgent.tool_set("tools")._without_signature(
            name, tool.metadata.to_openai_tool(skip_length_check=True)["function"]["description"]
        )
        for name, tool in tools.items()
    }

    assert not [name for name, description in definitions.items() if description.startswith(f"{name}(")]
    assert {name: len(text) for name, text in definitions.items() if len(text) > LIMIT} == {}


@pytest.mark.parametrize("locale", LOCALES)
def test_the_attached_files_description_fits_with_the_most_files_a_message_carries(locale: str) -> None:
    definition = AttachedFiles.tool_definition(_context(locale))

    assert len(definition.description) <= LIMIT, len(definition.description)


@pytest.mark.parametrize("locale", LOCALES)
def test_the_extraction_tool_description_fits(locale: str) -> None:
    assert len(AgentLocaleHandler(locale)("agent.record_extraction.tools.extract.description")) <= LIMIT
