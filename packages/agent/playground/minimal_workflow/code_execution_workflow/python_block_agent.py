from typing import ClassVar

from llama_index.core.base.llms.types import MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.topics import AgentInstanceTopic

from playground.minimal_workflow.code_execution_workflow.code_execution_playground_config import (
    CodeExecutionPlaygroundConfig,
)
from playground.minimal_workflow.code_execution_workflow.python_blocks import PythonBlocks
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities import Conversation, SandboxWorkspace
from swiss_ai_hub.agent.workflow.decorators.step import step


class PythonBlockAgent(Agent):
    """Code execution without a tool loop: the ```python blocks the user sends run as written in their sandbox, and
    the output comes back as a text file. No model decides whether or what to run, so every run takes the same path."""

    name: ClassVar[LocaleString] = LocaleString(en="Python Blocks")
    description: ClassVar[LocaleString] = LocaleString(
        en="Runs the Python blocks of your message in your code sandbox and sends back their output."
    )
    icon: ClassVar[str] = "mdi:language-python"

    @step()
    async def contextualize_step(self, event: UserMessageEvent) -> Conversation.ContextualizeRequest:
        return Conversation.contextualize(history=event.messages, message=event)

    @step()
    async def run_step(
        self,
        ctx: Conversation.Contextualized,
        event: UserMessageEvent,
        config: CodeExecutionPlaygroundConfig,
        displayer: EventDisplayer,
        topic: AgentInstanceTopic,
        user: UserIdentity | None = None,
    ) -> Conversation.CompleteRequest:
        question = next((message for message in reversed(event.messages) if message.role == MessageRole.USER), None)
        blocks = PythonBlocks.in_text((question.content or "") if question else "")
        if not blocks:
            reply = "Send Python code in a ```python block and I run it in your sandbox."
            return Conversation.complete(answer=await PythonBlocks.reply(displayer, reply))
        workspace = SandboxWorkspace.for_user(user, topic, event.files or [])
        await workspace.prepare()
        report, kept = await PythonBlocks.run(workspace, blocks)
        await displayer.display_event(kept)
        reply = f"I ran {len(blocks)} Python block(s); the output:\n\n```text\n{report}```"
        return Conversation.complete(answer=await PythonBlocks.reply(displayer, reply))
