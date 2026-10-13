from collections import Counter

from swiss_ai_hub.core.events.agent import Message

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext


class EarlierToolTurns:
    """The tool calls and results behind a conversation's earlier answers, which chat clients do not send back.

    A chat client sends an earlier answer as its text alone. Asked on a later turn about a file it read before, the
    model sees that it answered but not what the file said, and answers from that wording instead of reading the file
    again. So each answer's calls and results are kept per thread, keyed by the question they answered, and put back in
    front of that answer on the turns that follow. A question asked again ("continue", "yes") is its own key, counted
    by how often its text was asked, so its calls are put back once and only in front of their own answer.
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
        questions = self._question_keys(messages)
        restored: list[Message] = []
        question: str | None = None
        for index, message in enumerate(messages):
            if message.role == "assistant" and not message.tool_calls and question in turns:
                restored.extend(Message.model_validate(kept) for kept in turns[question])
                question = None
            restored.append(message)
            if message.role == "user":
                question = questions[index]
        return restored

    async def keep(self, question: str | None, messages: list[Message]) -> None:
        """Keep the calls and results that answered the conversation's last question, for its next turns.

        The question's key comes from `last_question` on the conversation as the client sent it, since condensing
        merges the earlier questions it counts. An answer without tools drops what was kept for its question, so a
        regenerated answer does not get the calls of the one it replaced."""
        asked_at = max((index for index, message in enumerate(messages) if message.role == "user"), default=None)
        if question is None or asked_at is None:
            return
        exchange = [message for message in messages[asked_at + 1 :] if message.role == "tool" or message.tool_calls]
        turns: dict[str, list[dict]] = await self._thread_context.get(self._key, {})
        replaced = turns.pop(question, None)
        if exchange:
            turns[question] = [message.model_dump(mode="json", exclude={"content"}) for message in exchange]
        elif replaced is None:
            return
        kept_questions = list(turns)[-self.KEPT_TURNS :]
        await self._thread_context.set(self._key, {question: turns[question] for question in kept_questions})

    @classmethod
    def last_question(cls, messages: list[Message]) -> str | None:
        """The key the conversation's last question keeps its calls under."""
        questions = cls._question_keys(messages)
        return questions[max(questions)] if questions else None

    @staticmethod
    def _question_keys(messages: list[Message]) -> dict[int, str]:
        """Each user message's key: its text and how many times that text was asked up to it."""
        asked: Counter[str] = Counter()
        keys: dict[int, str] = {}
        for index, message in enumerate(messages):
            if message.role == "user":
                asked[message.content] += 1
                keys[index] = f"{message.content} #{asked[message.content]}"
        return keys
