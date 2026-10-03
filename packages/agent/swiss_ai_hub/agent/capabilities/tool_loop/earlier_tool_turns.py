from swiss_ai_hub.core.events.agent import Message

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext


class EarlierToolTurns:
    """The tool calls and results behind a conversation's earlier answers, which chat clients do not send back.

    A chat client sends an earlier answer as its text alone. Asked on a later turn about a file it read before, the
    model sees that it answered but not what the file said, and answers from that wording instead of reading the file
    again. So each answer's calls and results are kept per thread, keyed by the question they answered, and put back in
    front of that answer on the turns that follow.
    """

    KEY = "tool_loop:{loop}:earlier_turns"
    KEPT_TURNS = 5

    def __init__(self, thread_context: ThreadContext, loop: str) -> None:
        self._thread_context = thread_context
        self._key = self.KEY.format(loop=loop)

    async def restore(self, messages: list[Message]) -> list[Message]:
        """The conversation with each earlier answer's tool calls and results back in front of it."""
        turns: dict[str, list[dict]] = await self._thread_context.get(self._key, {})
        if not turns:
            return messages
        restored: list[Message] = []
        question: str | None = None
        for message in messages:
            if message.role == "assistant" and not message.tool_calls and question in turns:
                restored.extend(Message.model_validate(kept) for kept in turns[question])
                question = None
            restored.append(message)
            if message.role == "user":
                question = message.content
        return restored

    async def keep(self, messages: list[Message]) -> None:
        """Keep the calls and results that answered the conversation's last question, for its next turns."""
        last_question = max((index for index, message in enumerate(messages) if message.role == "user"), default=None)
        if last_question is None:
            return
        exchange = [
            message for message in messages[last_question + 1 :] if message.role == "tool" or message.tool_calls
        ]
        if not exchange:
            return
        turns: dict[str, list[dict]] = await self._thread_context.get(self._key, {})
        turns.pop(messages[last_question].content, None)
        turns[messages[last_question].content] = [
            message.model_dump(mode="json", exclude={"content"}) for message in exchange
        ]
        kept_questions = list(turns)[-self.KEPT_TURNS :]
        await self._thread_context.set(self._key, {question: turns[question] for question in kept_questions})
