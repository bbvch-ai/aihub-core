from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.agent import Agent, step
from swiss_ai_hub.agent.capabilities import (
    AttachedFiles,
    Conversation,
    ExtractionHistory,
    Knowledge,
    KnowledgeDocumentTools,
    Memory,
    RecordExtraction,
    RecordSelectionTools,
    SandboxTools,
    ToolLoop,
    UserFilesTools,
    WebFetch,
)
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import MemoryStorageRequestedEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.ee.agents.universal_agent.universal_agent_config import UniversalAgentConfig
from swiss_ai_hub.ee.i18n.enterprise_locale_string import EnterpriseLocaleString


class UniversalAgent(Agent):
    """One agent an admin configures once: the model decides for itself whether to search our knowledge, read the
    attached files, recall memory, read the web pages the user links, work on whole knowledge documents and extract
    tables from them (when the profile switches the document tools on) or, with Code Interpreter on, work in the
    user's code sandbox, and keeps going until it can answer.

    Three steps of its own: hand the instructed history to the conversation, let the model work through its tools,
    and complete with the reply. Nothing is loaded into the prompt up front; every tool call shows in the chat as the
    capability's own events. The fixed-flow blueprints stay the predictable option.
    """

    name: ClassVar[EnterpriseLocaleString] = EnterpriseLocaleString.from_i18n_path(
        "agent.universal_agent.metadata.name"
    )
    description: ClassVar[EnterpriseLocaleString] = EnterpriseLocaleString.from_i18n_path(
        "agent.universal_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:stars-c"
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

    @step(
        name=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.contextualize.name"),
        description=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.contextualize.description"),
        icon="mage:edit",
    )
    async def contextualize_step(
        self, event: UserMessageEvent, agent_config: UniversalAgentConfig, t: LocaleHandler
    ) -> Conversation.ContextualizeRequest:
        """The agent's instructions and the profile's lead a single system message, ahead of the client's own,
        followed by what it should know about the pages the message links. With the document tools on, the
        instructions say when to search by keyword and when to rank by meaning."""
        links_note = WebFetch.links_note(event, agent_config, t)
        documents = agent_config.knowledge_documents.enabled is True
        instructions = [
            t("agent.universal_agent.prompt.instructions"),
            *([t("agent.universal_agent.prompt.document_search")] if documents else []),
            *([agent_config.instructions.in_locale(event.locale)] if agent_config.instructions else []),
            *([links_note] if links_note else []),
        ]
        history = merge_consecutive_messages(
            [
                ChatMessage(role=MessageRole.SYSTEM, content="\n\n".join(instructions)),
                *(message for message in event.messages if message.role == MessageRole.SYSTEM),
                *ExtractionHistory.condensed(
                    [message for message in event.messages if message.role != MessageRole.SYSTEM]
                ),
            ]
        )
        head, conversation = history[:1], history[1:]
        limited = limit_chat_history(chat_history=conversation, number_of_input_tokens=agent_config.input_budget)
        return Conversation.contextualize(history=[*head, *limited], message=event)

    @step(
        name=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.loop.name"),
        description=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.loop.description"),
        icon="mdi:toolbox-outline",
    )
    async def loop_step(self, ctx: Conversation.Contextualized, event: UserMessageEvent) -> ToolLoop.RunRequest:
        return UniversalAgent.tools.run(
            ctx.history,
            files=event.files,
            knowledge_references=event.knowledge_references,
            web_references=WebFetch.links_of(event),
        )

    @step(
        name=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.complete.name"),
        description=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.steps.complete.description"),
        icon="mage:message",
    )
    async def complete_step(
        self,
        finished: ToolLoop.Finished,
        ctx: Conversation.Contextualized,
        agent_config: UniversalAgentConfig,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """The memory delegation first, so it is published before the run tears down, and the completion last."""
        remember = Memory.remember(
            query=ctx.query,
            answer=finished.answer,
            user=user,
            topic=topic,
            agent_config=agent_config,
            memory=agent_config,
            locale=t.locale,
        )
        return [*([remember] if remember else []), Conversation.complete(answer=finished.answer)]
