from typing import Annotated

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrievers.RetrievalOverride import KnowledgeRetrievalOverride
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, HumanInTheLoop, StopEvent
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from pydantic import BaseModel, Field

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.RagAgent.events import RAGUserMessageEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


class NamespaceInfo(BaseModel):
    """Information about a single namespace."""

    name: str
    display_name: LocaleString | None = None


class BucketInfo(BaseModel):
    """Information about a bucket and its namespaces."""

    bucket_name: str
    bucket_display_name: LocaleString | None = None
    namespaces: list[NamespaceInfo]


class SelectionParseResult(BaseModel):
    """Result of parsing namespace selections from user response."""

    complete: bool
    selections: dict[str, str]
    follow_up: str = ""


# ThreadContext key for persisted namespace selections
NAMESPACE_SELECTIONS_KEY = "namespace_selections"

# RunContext keys for within-run state
AVAILABLE_NAMESPACES_KEY = "available_namespaces"
PARTIAL_SELECTIONS_KEY = "partial_selections"


class NamespaceSelectionResult(BaseModel):
    """Result of parsing a user's namespace selection response."""

    selected_namespace: str | None
    follow_up: str


def namespace_selection_result_factory(
    t: LocaleHandler,
    valid_namespaces: list[str],
) -> type[NamespaceSelectionResult]:
    """
    Creates a localized NamespaceSelectionResult class with constrained namespace options.

    Uses Literal type to constrain selected_namespace to only valid options,
    improving LLM accuracy with structured output.
    """
    if valid_namespaces:
        from typing import Literal

        namespace_options = tuple(valid_namespaces)
        NamespaceLiteral = Literal[namespace_options]  # type: ignore[valid-type]
    else:
        NamespaceLiteral = str  # type: ignore[misc]

    class LocalizedNamespaceSelectionResult(NamespaceSelectionResult):
        selected_namespace: Annotated[
            NamespaceLiteral | None,
            Field(description=t("agent.namespace_selection.fields.selected_namespace")),
        ]
        follow_up: Annotated[
            str,
            Field(description=t("agent.namespace_selection.fields.follow_up")),
        ]

    LocalizedNamespaceSelectionResult.__doc__ = t("agent.namespace_selection.prompts.parse_selection")
    return LocalizedNamespaceSelectionResult


@precondition()
async def has_namespace_selection(thread_context: ThreadContext) -> bool:
    """Precondition: namespace selection already exists in ThreadContext."""
    selections = await thread_context.get(NAMESPACE_SELECTIONS_KEY)
    return selections is not None and len(selections) > 0


@precondition()
async def no_namespace_selection(thread_context: ThreadContext) -> bool:
    """Precondition: no namespace selection exists yet."""
    selections = await thread_context.get(NAMESPACE_SELECTIONS_KEY)
    return selections is None or len(selections) == 0


class NamespaceSelectionAgent(Agent):
    """
    Agent that asks the user which namespace to use for each configured bucket,
    then delegates all messages to the configured RAG agent.

    The selection flow uses chat-style HITL (normal messages, not popups) for a
    conversational experience. Once namespaces are selected, they are stored in
    ThreadContext and all future messages are delegated to the RAG agent with
    namespace overrides.

    ### Workflow

    1. **First message (no selection)**: Fetches namespaces for configured buckets,
       generates a question asking the user to select, and waits for response.

    2. **Selection loop**: Parses user response, asks for clarification if needed,
       until all buckets have a selected namespace.

    3. **Subsequent messages**: Delegates directly to RAG agent with namespace overrides.
    """

    @step(
        name=LocaleString(en="Delegate to RAG"),
        description=LocaleString(en="Delegates the user message to the configured RAG agent with namespace overrides."),
        precondition=has_namespace_selection,
        icon="hugeicons:robot-02",
    )
    async def delegate_to_rag_step(
        self,
        event: UserMessageEvent,
        thread_context: ThreadContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Delegates to RAG agent when namespace selection already exists."""
        selections: dict[str, str] = await thread_context.get(NAMESPACE_SELECTIONS_KEY, {})

        await displayer.display_thought(t("agent.namespace_selection.thoughts.delegating_to_rag"))

        namespaces = list(selections.values())
        overrides = {
            agent_config.knowledge_retrieval_agent_id: KnowledgeRetrievalOverride(
                type="knowledge",
                namespaces=namespaces,
            )
        }

        rag_event = RAGUserMessageEvent(
            messages=event.messages,
            locale=event.locale,
            user=event.user,
            retrieval_overrides=overrides,
        )

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_agent.agent_class,
            agent_id=agent_config.rag_agent.agent_id,
            start_event=rag_event,
        )

    @step(
        name=LocaleString(en="Ask Namespace Selection"),
        description=LocaleString(en="Asks the user which namespace to use for each bucket."),
        precondition=no_namespace_selection,
        icon="mdi:folder-question",
    )
    async def ask_selection_step(
        self,
        event: UserMessageEvent,
        run_context: RunContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.chat.request:
        """Fetches namespaces and asks user to select."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.fetching_namespaces"))

        available_namespaces = await self._fetch_available_namespaces(agent_config)
        available_namespaces_serialized = {k: v.model_dump() for k, v in available_namespaces.items()}
        await run_context.set(AVAILABLE_NAMESPACES_KEY, available_namespaces_serialized)
        await run_context.set(PARTIAL_SELECTIONS_KEY, {})

        question = await self._generate_selection_question(
            available_namespaces=available_namespaces,
            user_query=event.user_query,
            agent_config=agent_config,
            t=t,
            displayer=displayer,
        )

        return HumanInTheLoop.chat.invoke(question)

    @step(
        name=LocaleString(en="Parse Selection"),
        description=LocaleString(en="Parses user response and extracts namespace selections."),
        max_executions_per_run=5,
        icon="mdi:check-circle",
    )
    async def parse_selection_step(
        self,
        event: HumanInTheLoop.chat.response,
        start_event: UserMessageEvent,
        run_context: RunContext,
        thread_context: ThreadContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request | HumanInTheLoop.chat.request:
        """Parses user selection and either delegates or asks for clarification."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.parsing_selection"))

        available_namespaces_raw = await run_context.get(AVAILABLE_NAMESPACES_KEY, {})
        available_namespaces: dict[str, BucketInfo] = {
            k: BucketInfo.model_validate(v) for k, v in available_namespaces_raw.items()
        }
        partial_selections: dict[str, str] = await run_context.get(PARTIAL_SELECTIONS_KEY, {})

        result = await self._parse_selection_response(
            user_response=event.response,
            available_namespaces=available_namespaces,
            partial_selections=partial_selections,
            agent_config=agent_config,
            t=t,
            displayer=displayer,
        )

        if result.complete:
            await thread_context.set(NAMESPACE_SELECTIONS_KEY, result.selections)
            await displayer.display_thought(t("agent.namespace_selection.thoughts.selection_complete"))

            namespaces = list(result.selections.values())
            overrides = {
                agent_config.knowledge_retrieval_agent_id: KnowledgeRetrievalOverride(
                    type="knowledge",
                    namespaces=namespaces,
                )
            }

            rag_event = RAGUserMessageEvent(
                messages=start_event.messages,
                locale=start_event.locale,
                user=start_event.user,
                retrieval_overrides=overrides,
            )

            return AgentInTheLoop.invoke(
                agent_class=agent_config.rag_agent.agent_class,
                agent_id=agent_config.rag_agent.agent_id,
                start_event=rag_event,
            )
        else:
            await run_context.set(PARTIAL_SELECTIONS_KEY, result.selections)
            return HumanInTheLoop.chat.invoke(result.follow_up)

    @step(
        name=LocaleString(en="RAG Response"),
        description=LocaleString(en="Passes through the RAG agent's response."),
        icon="hugeicons:robot-02",
    )
    async def rag_response_step(
        self,
        event: AgentInTheLoop.response,
    ) -> LLMStopEvent:
        """Passes through the RAG agent's response."""
        return event.stop_event

    @step(
        name=LocaleString(en="RAG Error"),
        description=LocaleString(en="Handles errors from the RAG agent."),
        icon="mdi:alert",
    )
    async def rag_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handles errors from the RAG agent."""
        await displayer.display_thought(
            t(
                "agent.namespace_selection.thoughts.rag_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.namespace_selection.messages.rag_error"),
            model_name="NamespaceSelectionAgent",
        )
        return StopEvent()

    async def _fetch_available_namespaces(
        self,
        agent_config: NamespaceSelectionAgentConfig,
    ) -> dict[str, BucketInfo]:
        """Fetches namespaces for all configured buckets."""
        result: dict[str, BucketInfo] = {}

        for bucket_ref in agent_config.buckets:
            if bucket_ref.bucket_id:
                bucket = BucketEntity.get_bucket_by_id(bucket_ref.bucket_id)
            else:
                assert bucket_ref.bucket_name is not None
                bucket = BucketEntity.get_bucket_by_bucket_name(bucket_ref.bucket_name)

            bucket_id = str(bucket.id)

            namespaces = NamespaceEntity.get_namespaces_by_bucket(bucket_id)

            namespace_list = [
                NamespaceInfo(
                    name=ns.namespace_name,
                    display_name=ns.display_name.to_locale_string() if ns.display_name else None,
                )
                for ns in namespaces
            ]

            result[bucket_id] = BucketInfo(
                bucket_name=bucket.bucket_name,
                bucket_display_name=bucket.name.to_locale_string() if bucket.name else None,
                namespaces=namespace_list,
            )

        return result

    async def _generate_selection_question(
        self,
        available_namespaces: dict[str, BucketInfo],
        user_query: str,
        agent_config: NamespaceSelectionAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> str:
        """Generates a friendly question asking user to select namespaces."""
        formatted_options = self._format_namespace_options(available_namespaces, t)

        prompt = t("agent.namespace_selection.prompts.ask_selection")
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt,
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"User's question: {user_query}\n\nAvailable namespaces:\n{formatted_options}",
            ),
        ]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            response: ChatResponse = await llm.achat(messages)
            return response.message.content or t("agent.namespace_selection.messages.default_question")

    async def _parse_selection_response(
        self,
        user_response: str,
        available_namespaces: dict[str, BucketInfo],
        partial_selections: dict[str, str],
        agent_config: NamespaceSelectionAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> SelectionParseResult:
        """Parses user's selection response using structured LLM output."""
        merged_selections = {**partial_selections}
        last_follow_up = ""

        for bucket_id, bucket_info in available_namespaces.items():
            if bucket_id in merged_selections:
                continue

            valid_namespaces = [ns.name for ns in bucket_info.namespaces]
            formatted_options = self._format_single_bucket_options(bucket_info, t)

            result_class = namespace_selection_result_factory(t, valid_namespaces)
            prompt_template = PromptTemplate(t("agent.namespace_selection.prompts.parse_selection"))

            async with agent_config.llm.cost_reporting_llm(displayer) as llm:
                result: NamespaceSelectionResult = llm.structured_predict(
                    result_class,
                    prompt_template,
                    user_response=user_response,
                    namespace_options=formatted_options,
                )

            if result.selected_namespace:
                merged_selections[bucket_id] = result.selected_namespace
            else:
                last_follow_up = result.follow_up
                break

        complete = len(merged_selections) >= len(available_namespaces)

        return SelectionParseResult(
            complete=complete,
            selections=merged_selections,
            follow_up=last_follow_up if not complete else "",
        )

    def _format_single_bucket_options(
        self,
        bucket_info: BucketInfo,
        t: LocaleHandler,
    ) -> str:
        """Formats namespace options for a single bucket."""
        lines = []
        for ns in bucket_info.namespaces:
            ns_name = t.extract(LocaleString.model_validate(ns.display_name)) if ns.display_name else ns.name
            lines.append(f"- {ns_name} (name: {ns.name})")
        return "\n".join(lines)

    def _format_namespace_options(
        self,
        available_namespaces: dict[str, BucketInfo],
        t: LocaleHandler,
    ) -> str:
        """Formats namespace options for LLM prompt."""
        lines = []
        for bucket_id, bucket_info in available_namespaces.items():
            if bucket_info.bucket_display_name:
                bucket_name = t.extract(LocaleString.model_validate(bucket_info.bucket_display_name))
            else:
                bucket_name = bucket_info.bucket_name
            lines.append(f"\nBucket: {bucket_name} (ID: {bucket_id})")
            lines.append("Namespaces:")

            for ns in bucket_info.namespaces:
                ns_name = t.extract(LocaleString.model_validate(ns.display_name)) if ns.display_name else ns.name
                lines.append(f"  - {ns_name} (name: {ns.name})")

        return "\n".join(lines)
