from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import MemoryStorageRequestedEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent_config import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.capabilities.sandbox.sandbox_tools import SandboxTools
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class UniversalAgent(Agent):
    """One agent an admin configures once: the model decides for itself whether to search our knowledge, read the
    attached files, recall memory or, with Code Interpreter on, work in the user's code sandbox, and keeps going
    until it can answer.

    Three steps of its own: hand the instructed history to the conversation, let the model work through its tools,
    and complete with the reply. Nothing is loaded into the prompt up front; every tool call shows in the chat as the
    capability's own events. The fixed-flow blueprints stay the predictable option.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.universal_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.universal_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:stars-c"
    tools = ToolLoop.over(Knowledge, AttachedFiles, Memory, SandboxTools)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.contextualize.name"),
        description=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.contextualize.description"),
        icon="mage:edit",
    )
    async def contextualize_step(
        self, event: UserMessageEvent, agent_config: UniversalAgentConfig, t: LocaleHandler
    ) -> Conversation.ContextualizeRequest:
        """The agent's instructions and the profile's lead a single system message, ahead of the client's own."""
        instructions = [
            t("agent.universal_agent.prompt.instructions"),
            *([agent_config.instructions.in_locale(event.locale)] if agent_config.instructions else []),
        ]
        history = merge_consecutive_messages(
            [
                ChatMessage(role=MessageRole.SYSTEM, content="\n\n".join(instructions)),
                *(message for message in event.messages if message.role == MessageRole.SYSTEM),
                *(message for message in event.messages if message.role != MessageRole.SYSTEM),
            ]
        )
        head, conversation = history[:1], history[1:]
        limited = limit_chat_history(
            chat_history=conversation, number_of_input_tokens=agent_config.number_of_input_tokens
        )
        return Conversation.contextualize(history=[*head, *limited], message=event)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.loop.name"),
        description=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.loop.description"),
        icon="mdi:toolbox-outline",
    )
    async def loop_step(self, ctx: Conversation.Contextualized, event: UserMessageEvent) -> ToolLoop.RunRequest:
        return UniversalAgent.tools.run(ctx.history, files=event.files, knowledge_references=event.knowledge_references)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.complete.name"),
        description=AgentLocaleString.from_i18n_path("agent.universal_agent.steps.complete.description"),
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
