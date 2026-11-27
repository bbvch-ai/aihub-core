import asyncio
import itertools
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import (
    ChatFeature,
    SearchWebEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
    WebFetchFailure,
    WebSearchedEvent,
)
from swiss_ai_hub.core.generative_ai import IngestedNode, combine_nodes_in_order
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import SearxngClient

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.url_extractor import UrlExtractor
from swiss_ai_hub.agent.capabilities.web_fetch.web_page_fetcher import WebPageFetcher
from swiss_ai_hub.agent.capabilities.web_search.web_search_arguments import WebSearchArguments
from swiss_ai_hub.agent.capabilities.web_search.web_search_config import WebSearchConfig
from swiss_ai_hub.agent.capabilities.web_search.web_search_fields import WebSearchFields
from swiss_ai_hub.agent.capabilities.web_search.web_search_hit import WebSearchHit
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

SEARCH_WEB_TOOL = "search_web"


@precondition()
async def searches_the_web(call: ToolCallApprovedEvent) -> bool:
    return call.name == SEARCH_WEB_TOOL


@precondition()
async def answers_a_search_call(searched: WebSearchedEvent, decided: ToolCallsDecidedEvent) -> bool:
    return searched.tool_call_id is not None and searched.tool_call_id in decided.tool_call_ids


class WebSearch(Capability):
    """
    Searching the web through the platform's SearXNG, as one call and as a tool any agent can offer:

    - `search(queries)` is answered with `WebSearchedEvent`: the hits, and one context block with the best hits read
      whole and the snippets of the rest, empty while the profile has web search off or the user's Web Search toggle
      is. Pass the block to `Conversation.compose(...)`.
    - In a tool set, the model searches when it decides it needs to, offered only while the toggle is on.

    It serves the Web Search chat toggle, but only on profiles that turned it on: elsewhere no toggle shows. Hits are
    read through the platform's browser like a linked page, and come back cited like retrieved knowledge.
    """

    calls: ClassVar[dict] = {SearchWebEvent: (WebSearchedEvent,)}
    required_config: ClassVar[type[WebSearchFields]] = WebSearchFields
    chat_feature: ClassVar[ChatFeature] = ChatFeature.WEB_SEARCH
    chat_feature_config_field: ClassVar[str] = "web_search"

    SearchRequest = SearchWebEvent
    Searched = WebSearchedEvent

    tool_name: ClassVar[str] = SEARCH_WEB_TOOL
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.web_search.tool.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.web_search.tool.approval_summary"),
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered while the profile searches the web; the tool loop withholds it while the toggle is off."""
        config = context.agent_config
        if not isinstance(config, WebSearchFields) or config.web_search is None:
            return None
        t = context.t
        return ToolDefinition(
            name=SEARCH_WEB_TOOL,
            description=t(
                "agent.web_search.tool.description",
                max_results=config.web_search.max_results,
                read_top_results=config.web_search.read_top_results,
            ),
            parameters=WebSearchArguments.schema_for(t),
        )

    @staticmethod
    def search(queries: list[str], web: WebSearchFields, cite_sources: bool = True) -> SearchWebEvent:
        """The request says whether the profile searches, so a chat client shows search progress only when it may
        happen. The user's toggle is checked by the step, so a blueprint calling this checks it too
        (`RequestedFeatures.contains`) before it asks; the step answers either way."""
        return SearchWebEvent(queries=list(queries), searching=web.web_search is not None, cite_sources=cite_sources)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_search.steps.search_web.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_search.steps.search_web.description"),
        icon="mdi:search-web",
    )
    async def web_search_step(
        agent: Agent, request: SearchWebEvent, web: WebSearchFields, run_context: RunContext, t: LocaleHandler
    ) -> WebSearchedEvent:
        """Search, read the best hits whole and keep the snippets of the rest, as one block.

        Nothing is searched unless the profile searches the web and the user switched on Web Search for this message:
        a search sends words from the conversation outside the platform. Failing to reach SearXNG or the browser
        raises: that is a platform fault, not an empty search.
        """
        config = web.web_search
        queries = [query.strip() for query in request.queries if query.strip()]
        toggled_on = await RequestedFeatures.contains(ChatFeature.WEB_SEARCH, run_context, type(agent))
        if config is None or not queries or not toggled_on:
            return WebSearchedEvent(tool_call_id=request.tool_call_id)
        hits, unresponsive_engines = await WebSearch._hits(queries, config)
        to_read = UrlExtractor.classify([hit.url for hit in hits[: config.read_top_results]]).urls
        read = await WebPageFetcher.fetch_all(to_read, config.timeout_seconds, config.page_characters(len(to_read)))
        pages = {page.url: page for page in read if isinstance(page, FetchedWebPage)}
        failures = [failure for failure in read if isinstance(failure, WebFetchFailure)]
        nodes = [WebSearch._node(hit, pages.get(hit.url), t) for hit in hits]
        return WebSearchedEvent(
            queries=queries,
            results=[hit.to_result(read=hit.url in pages) for hit in hits],
            block=WebSearch._block(queries, nodes, t, request.cite_sources),
            grounding_nodes=nodes,
            failures=failures,
            unresponsive_engines=unresponsive_engines,
            tool_call_id=request.tool_call_id,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_search.steps.search_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_search.steps.search_as_tool.description"),
        icon="mdi:search-web",
        precondition=searches_the_web,
    )
    async def web_search_tool_call_step(agent: Agent, call: ToolCallApprovedEvent) -> SearchWebEvent | ToolResultEvent:
        """The model chose to search: the same search as an explicit call, for the queries it wrote."""
        try:
            arguments = WebSearchArguments.model_validate(call.arguments)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        return SearchWebEvent(queries=arguments.queries, cite_sources=call.cite_sources, tool_call_id=call.tool_call_id)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_search.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_search.steps.answer_tool_call.description"),
        icon="mdi:search-web",
        precondition=answers_a_search_call,
    )
    async def web_search_tool_result_step(
        agent: Agent, searched: WebSearchedEvent, decided: ToolCallsDecidedEvent
    ) -> ToolResultEvent:
        """Hand the hits back to the loop: their text for the model, their block for a gathered answer."""
        content = "\n\n".join(message.content for message in searched.block if message.content)
        return ToolResultEvent(
            tool_call_id=searched.tool_call_id, name=SEARCH_WEB_TOOL, content=content, block=searched.block
        )

    @staticmethod
    async def _hits(queries: list[str], config: WebSearchConfig) -> tuple[list[WebSearchHit], list[str]]:
        """Every query's hits, taken in turns so each query is represented, each site once, the best first; and the
        engines that did not answer, so a search they all refused does not pass for one that matched nothing."""
        client = SearxngClient()
        answers = await asyncio.gather(
            *(
                client.search(
                    query,
                    engines=config.engines,
                    language=config.language,
                    safe_search=config.safe_search,
                    time_range=config.time_range,
                    max_results=config.max_results,
                )
                for query in queries
            )
        )
        unique: dict[str, WebSearchHit] = {}
        for rank in itertools.zip_longest(*(answer.results for answer in answers)):
            for result in rank:
                if result is not None:
                    unique.setdefault(result.url, WebSearchHit.from_searxng(result))
        unresponsive = list(dict.fromkeys(engine for answer in answers for engine in answer.unresponsive_engines))
        return list(unique.values())[: config.max_results], unresponsive

    @staticmethod
    def _node(hit: WebSearchHit, page: FetchedWebPage | None, t: LocaleHandler) -> IngestedNode:
        """A hit read whole is its page; any other hit is its snippet, marked as such."""
        if page is None:
            return hit.to_ingested_node(t("agent.web_search.prompt.snippet_marker"))
        node = page.to_ingested_node()
        if page.truncated:
            node = node.model_copy(
                update={"content": f"{node.content}\n\n{t('agent.web_fetch.prompt.truncated_marker')}"}
            )
        return node.model_copy(update={"document_title": page.title or hit.title or hit.url})

    @staticmethod
    def _block(
        queries: list[str], nodes: list[IngestedNode], t: LocaleHandler, cite_sources: bool
    ) -> list[ChatMessage]:
        """The hits as retrieved knowledge is rendered, or a note that the search found nothing."""
        if not nodes:
            listing = "\n".join(f"- {query}" for query in queries)
            return [
                ChatMessage(role=MessageRole.SYSTEM, content=t("agent.web_search.prompt.no_results", queries=listing))
            ]
        source_rule = "lib.prompt.citations.instruction" if cite_sources else "agent.web_search.prompt.name_sources"
        return [
            combine_nodes_in_order(nodes, t, AgentLocaleString.from_i18n_path("agent.web_search.prompt.context")),
            ChatMessage(role=MessageRole.SYSTEM, content=t(source_rule)),
        ]
