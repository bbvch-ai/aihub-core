"""Every tool description fits the 1024 characters OpenAI-style tool schemas are held to, in every language, and
carries no Python signature: the parameters reach the model as a schema already."""

from unittest.mock import MagicMock

import pytest
from swiss_ai_hub.core.events.agent import UserUploadedFile

from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
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


def _context(locale: str) -> ToolContext:
    return ToolContext.model_construct(
        agent_config=MagicMock(),
        displayer=MagicMock(),
        t=AgentLocaleHandler(locale),
        files=MOST_FILES_A_MESSAGE_CARRIES,
        knowledge_references=[],
    )


@pytest.mark.parametrize("locale", LOCALES)
def test_every_function_tool_description_fits_without_its_signature(locale: str) -> None:
    tools = UniversalAgent.tool_set("tools").function_tools(_context(locale))
    definitions = {
        name: UniversalAgent.tool_set("tools")._without_signature(
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
