from typing import ClassVar

from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.tool_loop_workflow.clock_tools import ClockTools
from playground.minimal_workflow.tool_loop_workflow.tool_loop_playground_config import ToolLoopPlaygroundConfig
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities import Conversation, Knowledge, ToolLoop
from swiss_ai_hub.agent.workflow.decorators.step import step


class AnsweringToolLoopAgent(Agent):
    """Loop first: the model decides on tools and its last turn is the reply, like a general assistant."""

    name: ClassVar[LocaleString] = LocaleString(en="Tool Loop (answering)")
    description: ClassVar[LocaleString] = LocaleString(en="Lets the model choose tools and answer itself.")
    icon: ClassVar[str] = "mdi:toolbox-outline"
    tools = ToolLoop.over(Knowledge, ClockTools)

    @step()
    async def contextualize_step(
        self, event: UserMessageEvent, config: ToolLoopPlaygroundConfig
    ) -> Conversation.ContextualizeRequest:
        history = limit_chat_history(chat_history=event.messages, number_of_input_tokens=config.number_of_input_tokens)
        return Conversation.contextualize(history=history, message=event)

    @step()
    async def loop_step(self, ctx: Conversation.Contextualized) -> ToolLoop.RunRequest:
        return AnsweringToolLoopAgent.tools.run(ctx.history)

    @step()
    async def complete_step(self, finished: ToolLoop.Finished) -> Conversation.CompleteRequest:
        return Conversation.complete(answer=finished.answer)
