import asyncio
import json
from collections.abc import Callable

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import Message, TextContent, ToolDefinition, ToolLoopCondensedEvent, ToolLoopState
from swiss_ai_hub.core.generative_ai import LLMConfig, estimate_prompt_tokens
from swiss_ai_hub.core.i18n import LocaleHandler

SUMMARY_WORDS = 150


class ToolLoopCondenser:
    """Fits a tool loop's conversation back into the prompt when it outgrew it, oldest material first.

    Earlier tool results are condensed to what matters for the request, each keeping its place, so every tool call
    still has its answer. If that is not enough, the conversation before the request becomes one summary; only then
    are the oldest results dropped. The request and the latest round of results are never touched.
    """

    def __init__(
        self,
        llm: LLMConfig,
        budget: int,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> None:
        self._llm = llm
        self._budget = budget
        self._displayer = displayer
        self._t = t
        self._user = user

    @staticmethod
    def outgrown(
        messages: list[Message], tools: list[ToolDefinition], budget: int, counter: Callable[[str], list[int]]
    ) -> bool:
        """The conversation and the offered tools' schemas no longer fit the prompt."""
        return ToolLoopCondenser.size(messages, tools, counter) > budget

    @staticmethod
    def size(messages: list[Message], tools: list[ToolDefinition], counter: Callable[[str], list[int]]) -> int:
        schemas = json.dumps([tool.to_openai() for tool in tools])
        return estimate_prompt_tokens([message.to_llama_index() for message in messages], counter) + len(
            counter(schemas)
        )

    async def condense(self, state: ToolLoopState) -> ToolLoopState:
        counter = self._llm.token_counter
        before = self.size(state.messages, state.tools, counter)
        request_at = self._last_request(state.messages)
        messages, results = await self._condense_results(state.messages, request_at)
        turns = 0
        if self.outgrown(messages, state.tools, self._budget, counter):
            messages, turns = await self._condense_turns(messages, request_at)
        if self.outgrown(messages, state.tools, self._budget, counter):
            messages = self._drop_oldest_results(messages, state.tools)
        await self._displayer.display_event(
            ToolLoopCondensedEvent(
                loop=state.loop,
                description=self._t("agent.tool_loop.status.condensed"),
                tokens_before=before,
                tokens_after=self.size(messages, state.tools, counter),
                condensed_results=results,
                condensed_turns=turns,
            )
        )
        return state.model_copy(update={"messages": messages, "needs_condensing": False})

    async def _condense_results(self, messages: list[Message], request_at: int) -> tuple[list[Message], int]:
        """Every tool result older than the latest round, summarised for the request in its place."""
        earlier = self._earlier_results(messages)
        if not earlier:
            return messages, 0
        request = messages[request_at].content if request_at >= 0 else ""
        summaries = await asyncio.gather(*(self._summarise_result(request, messages[index]) for index in earlier))
        condensed = list(messages)
        for index, summary in zip(earlier, summaries, strict=True):
            text = self._t("agent.tool_loop.prompt.condensed_result", summary=summary)
            condensed[index] = messages[index].model_copy(update={"contents": [TextContent(text=text)]})
        return condensed, len(earlier)

    async def _condense_turns(self, messages: list[Message], request_at: int) -> tuple[list[Message], int]:
        """The conversation between the leading instructions and the request, as one summary."""
        head = self._leading_system(messages)
        earlier = messages[head:request_at] if request_at > head else []
        if not earlier:
            return messages, 0
        transcript = "\n\n".join(f"{message.role}: {message.content}" for message in earlier)
        summary = await self._ask(self._t("agent.tool_loop.prompt.condense_turns", words=SUMMARY_WORDS * 2), transcript)
        summary_message = Message.from_string(
            role="system", content=self._t("agent.tool_loop.prompt.condensed_turns", summary=summary)
        )
        return [*messages[:head], summary_message, *messages[request_at:]], len(earlier)

    def _drop_oldest_results(self, messages: list[Message], tools: list[ToolDefinition]) -> list[Message]:
        """The last resort: earlier results give way, oldest first, until the rest fits."""
        dropped = list(messages)
        for index in self._earlier_results(messages):
            if not self.outgrown(dropped, tools, self._budget, self._llm.token_counter):
                break
            text = self._t("agent.tool_loop.prompt.dropped_result")
            dropped[index] = messages[index].model_copy(update={"contents": [TextContent(text=text)]})
        return dropped

    async def _summarise_result(self, request: str, result: Message) -> str:
        instruction = self._t("agent.tool_loop.prompt.condense_result", words=SUMMARY_WORDS)
        return await self._ask(instruction, f"{request}\n\n---\n\n{result.name}:\n{result.content}")

    async def _ask(self, instruction: str, material: str) -> str:
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=instruction),
            ChatMessage(role=MessageRole.USER, content=material),
        ]
        async with self._llm.cost_reporting_llm(self._displayer, user=self._user) as llm:
            response = await llm.achat(messages)
        return (response.message.content or "").strip()

    @staticmethod
    def _earlier_results(messages: list[Message]) -> list[int]:
        """Tool results answering an assistant turn before the latest one with tool calls."""
        latest_calls = next(
            (index for index in range(len(messages) - 1, -1, -1) if messages[index].tool_calls), len(messages)
        )
        return [index for index, message in enumerate(messages[:latest_calls]) if message.role == "tool"]

    @staticmethod
    def _last_request(messages: list[Message]) -> int:
        return next((index for index in range(len(messages) - 1, -1, -1) if messages[index].role == "user"), -1)

    @staticmethod
    def _leading_system(messages: list[Message]) -> int:
        return next((index for index, message in enumerate(messages) if message.role != "system"), len(messages))
