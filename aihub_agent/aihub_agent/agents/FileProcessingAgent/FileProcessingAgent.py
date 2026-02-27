from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.chat_history.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.document.download_and_format_files import download_and_format_files
from aihub_lib.nats.events import LimitChatHistoryEvent, LLMStopEvent, UserMessageEvent
from aihub_lib.nats.topics import AgentInstanceTopic
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.FileProcessingAgent.FileProcessingAgentConfig import FileProcessingAgentConfig
from aihub_agent.agents.FileProcessingAgent.events.FileContentEvent import FileContentEvent
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString
from aihub_agent.workflow.decorators.step import step


def _has_files(event: UserMessageEvent) -> bool:
    return bool(event.files)


def _files_ready(event: UserMessageEvent, file_content: FileContentEvent | None) -> bool:
    """Wait for FileContentEvent if files were uploaded, proceed immediately otherwise."""
    if event.files:
        return file_content is not None
    return True


class FileProcessingAgent(Agent):
    """LLM chat agent that can optionally process user-uploaded files."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.file_processing_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.file_processing_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:file"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.extract_files.name"),
        description=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.extract_files.description"),
        icon="mage:file-download",
        precondition=_has_files,
    )
    async def extract_files_step(
        self,
        event: UserMessageEvent,
        topic: AgentInstanceTopic,
    ) -> FileContentEvent:
        return FileContentEvent(file_context=download_and_format_files(event.files, topic))

    @step(
        name=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.prepare_messages.name"),
        description=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.prepare_messages.description"),
        icon="mage:edit",
        precondition=_files_ready,
    )
    async def prepare_messages_step(
        self,
        event: UserMessageEvent,
        file_content: FileContentEvent | None,
        agent_config: FileProcessingAgentConfig,
    ) -> LimitChatHistoryEvent:
        chat_history = _build_chat_history(event, file_content, agent_config)
        limited = limit_chat_history(
            chat_history=chat_history,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.process.name"),
        description=AgentLocaleString.from_i18n_path("agent.file_processing_agent.steps.process.description"),
        icon="mage:message",
    )
    async def process_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: FileProcessingAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMStopEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.limited_history, as_stop_step=True)


def _build_chat_history(
    event: UserMessageEvent,
    file_content: FileContentEvent | None,
    agent_config: FileProcessingAgentConfig,
) -> list[ChatMessage]:
    """Assemble the full chat history with system prompt and optional file context."""
    locale = event.locale
    system_messages = [msg for msg in event.messages if msg.role == MessageRole.SYSTEM]
    system_prompt = ChatMessage(role=MessageRole.SYSTEM, content=agent_config.system_prompt.in_locale(locale))
    regular_messages = [msg for msg in event.messages if msg.role != MessageRole.SYSTEM]

    if file_content and file_content.file_context:
        last_msg = regular_messages[-1]
        enriched = ChatMessage(role=last_msg.role, content=f"{file_content.file_context}\n\n{last_msg.content}")
        regular_messages = [*regular_messages[:-1], enriched]

    return [*system_messages, system_prompt, *regular_messages]
