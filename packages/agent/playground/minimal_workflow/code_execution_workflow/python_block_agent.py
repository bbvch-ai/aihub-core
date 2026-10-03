from typing import ClassVar

from llama_index.core.base.llms.types import MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
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

    name: ClassVar[LocaleString] = LocaleString(
        en="Python Blocks", de="Python-Blöcke", fr="Blocs Python", it="Blocchi Python"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Runs the Python blocks of your message in your code sandbox and sends back their output.",
        de="Führt die Python-Blöcke Ihrer Nachricht in Ihrer Code-Sandbox aus und sendet die Ausgabe zurück.",
        fr="Exécute les blocs Python de votre message dans votre bac à sable de code et renvoie leur sortie.",
        it="Esegue i blocchi Python del tuo messaggio nella tua sandbox di codice e restituisce il loro output.",
    )
    icon: ClassVar[str] = "mdi:language-python"
    NO_BLOCKS: ClassVar[LocaleString] = LocaleString(
        en="Send Python code in a ```python block and I run it in your sandbox.",
        de="Senden Sie Python-Code in einem ```python-Block, und ich führe ihn in Ihrer Sandbox aus.",
        fr="Envoyez du code Python dans un bloc ```python et je l'exécute dans votre bac à sable.",
        it="Invia codice Python in un blocco ```python e lo eseguo nella tua sandbox.",
    )
    RAN: ClassVar[LocaleString] = LocaleString(
        en="I ran {count} Python block(s); the output:",
        de="Ich habe {count} Python-Block/Blöcke ausgeführt; die Ausgabe:",
        fr="J'ai exécuté {count} bloc(s) Python ; la sortie :",
        it="Ho eseguito {count} blocco/i Python; l'output:",
    )

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
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> Conversation.CompleteRequest:
        question = next((message for message in reversed(event.messages) if message.role == MessageRole.USER), None)
        blocks = PythonBlocks.in_text((question.content or "") if question else "")
        if not blocks:
            reply = PythonBlocks.text(self.NO_BLOCKS, t.locale)
            return Conversation.complete(answer=await PythonBlocks.reply(displayer, reply))
        workspace = SandboxWorkspace.for_user(user, topic, event.files or [])
        await workspace.prepare()
        report, kept = await PythonBlocks.run(workspace, blocks, t.locale)
        await displayer.display_event(kept)
        reply = f"{PythonBlocks.text(self.RAN, t.locale, count=len(blocks))}\n\n```text\n{report}```"
        return Conversation.complete(answer=await PythonBlocks.reply(displayer, reply))
