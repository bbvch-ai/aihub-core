from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ToolLoopMode, UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.tool_loop_workflow.clock_tools import ClockTools
from playground.minimal_workflow.tool_loop_workflow.tool_loop_playground_config import ToolLoopPlaygroundConfig
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities import Conversation, Knowledge, ToolLoop
from swiss_ai_hub.agent.workflow.decorators.step import step


class GatheringToolLoopAgent(Agent):
    """Loop, then the blueprint's own answer: the model gathers context with tools, and a fixed step answers from
    it, the way a knowledge agent keeps its prompt and checks while the web or code become options."""

    name: ClassVar[LocaleString] = LocaleString(en="Tool Loop (gathering)")
    description: ClassVar[LocaleString] = LocaleString(en="Gathers context with tools, then answers in a fixed step.")
    icon: ClassVar[str] = "mdi:toolbox"
    tools = ToolLoop.over(Knowledge, ClockTools)

    @step()
    async def contextualize_step(
        self, event: UserMessageEvent, config: ToolLoopPlaygroundConfig
    ) -> Conversation.ContextualizeRequest:
        history = limit_chat_history(chat_history=event.messages, number_of_input_tokens=config.number_of_input_tokens)
        return Conversation.contextualize(history=history, message=event)

    @step()
    async def gather_step(self, ctx: Conversation.Contextualized) -> ToolLoop.RunRequest:
        return GatheringToolLoopAgent.tools.run(ctx.history, mode=ToolLoopMode.GATHER)

    @step()
    async def compose_step(
        self, ctx: Conversation.Contextualized, gathered: ToolLoop.Finished
    ) -> Conversation.ComposeRequest:
        return Conversation.compose(ctx.history, blocks=[gathered.block])

    @step()
    async def answer_step(
        self,
        composed: Conversation.Composed,
        config: ToolLoopPlaygroundConfig,
        displayer: EventDisplayer,
        user: UserIdentity | None = None,
    ) -> Conversation.CompleteRequest:
        async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
            answer = await displayer.display_llm_stream(config.llm, llm, composed.history)
        return Conversation.complete(answer=answer)
