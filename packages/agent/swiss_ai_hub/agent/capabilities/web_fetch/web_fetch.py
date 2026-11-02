from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import (
    FetchWebPagesEvent,
    RunToolLoopEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
    UserMessageEvent,
    WebFetchFailure,
    WebFetchFailureReason,
    WebPagesFetchedEvent,
)
from swiss_ai_hub.core.generative_ai import IngestedNode, combine_nodes_in_order
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.url_extractor import UrlExtractor
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_arguments import WebFetchArguments
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_fields import WebFetchFields
from swiss_ai_hub.agent.capabilities.web_fetch.web_page_fetcher import WebPageFetcher
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

FETCH_WEB_PAGES_TOOL = "fetch_web_pages"
# OpenAI-style tool schemas cap a description at this length; the links listed in it give way first.
MAX_TOOL_DESCRIPTION_CHARACTERS = 1024


@precondition()
async def fetches_web_pages(call: ToolCallApprovedEvent) -> bool:
    return call.name == FETCH_WEB_PAGES_TOOL


@precondition()
async def answers_a_fetch_call(fetched: WebPagesFetchedEvent, decided: ToolCallsDecidedEvent) -> bool:
    return fetched.tool_call_id is not None and fetched.tool_call_id in decided.tool_call_ids


class WebFetch(Capability):
    """
    Reading the web pages a user links, as one call and as a tool any agent can offer:

    - `fetch(urls)` is answered with `WebPagesFetchedEvent`, one context block with the pages read and a note naming
      the links that were not, empty when fetching is off for the profile. Pass `WebFetch.links_of(message)`, every
      link pasted into the message or referenced with `#`, and the block to `Conversation.compose(...)`.
    - In a tool set, the model reads the pages it wants, told which ones the message links.

    Pages load through the platform's browser, never from the agent, and come back as markdown cited like retrieved
    knowledge. A page that cannot be read is named in the block with the reason, so the answer reports it instead of
    inventing the page.
    """

    calls: ClassVar[dict] = {FetchWebPagesEvent: (WebPagesFetchedEvent,)}
    required_config: ClassVar[type[WebFetchFields]] = WebFetchFields

    FetchRequest = FetchWebPagesEvent
    Fetched = WebPagesFetchedEvent

    tool_name: ClassVar[str] = FETCH_WEB_PAGES_TOOL
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.web_fetch.tool.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.web_fetch.tool.approval_summary"),
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered when the profile reads web pages and the message links some, since only those may be read; the
        description lists them, so the model reads each of them without being asked."""
        config = context.agent_config
        if not isinstance(config, WebFetchFields) or config.web_fetch is None or not context.web_references:
            return None
        t = context.t
        description = t("agent.web_fetch.tool.description", max_urls=config.web_fetch.max_urls)
        return ToolDefinition(
            name=FETCH_WEB_PAGES_TOOL,
            description=cls._with_links(description, context.web_references, t),
            parameters=WebFetchArguments.schema_for(t),
        )

    @staticmethod
    def links_of(message: UserMessageEvent) -> list[str]:
        """The pages a message points at: the links in its text, then those referenced with `#`, once each."""
        return list(dict.fromkeys([*UrlExtractor.find(message.user_query), *message.web_references]))

    @staticmethod
    def links_note(message: UserMessageEvent, web: WebFetchFields, t: LocaleHandler) -> str | None:
        """What a tool loop's instructions say about the pages a message links.

        While the profile reads web pages, only the pages referenced with `#` need naming: such a link is not in the
        message text, only in the tool's description, and a model asked to summarise "this page" answered that it saw
        no link. While it does not, every link is named as unreadable, since a model handed a bare URL summarised the
        page it imagined from it.
        """
        if web.web_fetch is None:
            links = WebFetch.links_of(message)
            return WebFetch._unreadable_links(links, t) if links else None
        if not message.web_references:
            return None
        links = "\n".join(f"- {url}" for url in message.web_references)
        return t("agent.web_fetch.prompt.referenced_pages", links=links, tool=FETCH_WEB_PAGES_TOOL)

    @staticmethod
    def fetch(urls: list[str], web: WebFetchFields, cite_sources: bool = True) -> FetchWebPagesEvent:
        """The request says whether the profile reads the pages, so a chat client shows reading progress only when
        it happens; the step answers either way."""
        return FetchWebPagesEvent(urls=list(urls), reading=web.web_fetch is not None, cite_sources=cite_sources)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.fetch_web_pages.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.fetch_web_pages.description"),
        icon="mdi:web",
    )
    async def fetch_step(
        agent: Agent, request: FetchWebPagesEvent, web: WebFetchFields, t: LocaleHandler
    ) -> WebPagesFetchedEvent:
        """Read the linked pages within the profile's limits, and answer with them and the unreadable links as one
        block. Failing to reach the browser itself raises: that is a platform fault, not an unreadable page."""
        config = web.web_fetch
        if not request.urls:
            return WebPagesFetchedEvent(tool_call_id=request.tool_call_id)
        if config is None:
            note = ChatMessage(role=MessageRole.SYSTEM, content=WebFetch._unreadable_links(request.urls, t))
            return WebPagesFetchedEvent(block=[note], tool_call_id=request.tool_call_id)
        links = UrlExtractor.classify(request.urls)
        to_read, beyond_limit = links.urls[: config.max_urls], links.urls[config.max_urls :]
        results = await WebPageFetcher.fetch_all(to_read, config.timeout_seconds, config.max_page_characters)
        nodes = [WebFetch._node(result, t) for result in results if isinstance(result, FetchedWebPage)]
        failures = [
            *links.failures,
            *(result for result in results if isinstance(result, WebFetchFailure)),
            *(WebFetchFailure(url=url, reason=WebFetchFailureReason.URL_LIMIT_REACHED) for url in beyond_limit),
        ]
        return WebPagesFetchedEvent(
            block=WebFetch._block(nodes, failures, config, t, request.cite_sources),
            grounding_nodes=nodes,
            failures=failures,
            tool_call_id=request.tool_call_id,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.fetch_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.fetch_as_tool.description"),
        icon="mdi:web",
        precondition=fetches_web_pages,
    )
    async def fetch_tool_call_step(
        agent: Agent, call: ToolCallApprovedEvent, request: RunToolLoopEvent, t: LocaleHandler
    ) -> FetchWebPagesEvent | ToolResultEvent:
        """The model chose to read pages: the same fetch as a linked page, of the ones it named.

        Only pages the user linked are read. A URL the model wrote itself could carry what it read elsewhere in the
        conversation to a site an instruction hidden in a page or file named, and the request alone would deliver
        it. A call naming any other URL is refused whole, with the linked pages listed for the model to choose from.
        """
        try:
            arguments = WebFetchArguments.model_validate(call.arguments)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        urls = [url.strip() for url in arguments.urls]
        unlinked = [url for url in urls if url not in request.web_references]
        if unlinked:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id,
                name=call.name,
                content=t(
                    "agent.web_fetch.tool.unlinked",
                    urls=", ".join(unlinked),
                    linked="\n".join(f"- {url}" for url in request.web_references),
                ),
                is_error=True,
            )
        return FetchWebPagesEvent(urls=urls, cite_sources=call.cite_sources, tool_call_id=call.tool_call_id)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.web_fetch.steps.answer_tool_call.description"),
        icon="mdi:web",
        precondition=answers_a_fetch_call,
    )
    async def fetch_tool_result_step(
        agent: Agent, fetched: WebPagesFetchedEvent, decided: ToolCallsDecidedEvent
    ) -> ToolResultEvent:
        """Hand what was read back to the loop: its text for the model, its block for a gathered answer."""
        content = "\n\n".join(message.content for message in fetched.block if message.content)
        return ToolResultEvent(
            tool_call_id=fetched.tool_call_id, name=FETCH_WEB_PAGES_TOOL, content=content, block=fetched.block
        )

    @staticmethod
    def _node(page: FetchedWebPage, t: LocaleHandler) -> IngestedNode:
        """A shortened page says where it was cut, so the answer does not present its beginning as the whole."""
        node = page.to_ingested_node()
        if not page.truncated:
            return node
        return node.model_copy(update={"content": f"{node.content}\n\n{t('agent.web_fetch.prompt.truncated_marker')}"})

    @staticmethod
    def _block(
        nodes: list[IngestedNode],
        failures: list[WebFetchFailure],
        config: WebFetchConfig,
        t: LocaleHandler,
        cite_sources: bool,
    ) -> list[ChatMessage]:
        """The pages as retrieved knowledge is rendered, followed by the links the answer must report as unread."""
        block = []
        if nodes:
            block.append(
                combine_nodes_in_order(nodes, t, AgentLocaleString.from_i18n_path("agent.web_fetch.prompt.context"))
            )
            source_rule = "lib.prompt.citations.instruction" if cite_sources else "agent.web_fetch.prompt.name_sources"
            block.append(ChatMessage(role=MessageRole.SYSTEM, content=t(source_rule)))
        if failures:
            listing = "\n".join(f"- {failure.url}: {WebFetch._reason(failure, config, t)}" for failure in failures)
            block.append(
                ChatMessage(
                    role=MessageRole.SYSTEM, content=t("agent.web_fetch.prompt.unreadable_pages", failures=listing)
                )
            )
        return block

    @staticmethod
    def _unreadable_links(links: list[str], t: LocaleHandler) -> str:
        """Said to the model when the profile does not read web pages, so the answer asks for the text instead of
        describing a page it never saw."""
        return t("agent.web_fetch.prompt.unreadable_links", links="\n".join(f"- {link}" for link in links))

    @staticmethod
    def _reason(failure: WebFetchFailure, config: WebFetchConfig, t: LocaleHandler) -> str:
        return t(f"agent.web_fetch.failure_reasons.{failure.reason.value}", max_urls=config.max_urls)

    @staticmethod
    def _with_links(description: str, links: list[str], t: LocaleHandler) -> str:
        """Lists as many of the linked pages as the description's limit leaves room for, and counts the rest."""
        listed: list[str] = []
        for link in links:
            if len(WebFetch._describe(description, [*listed, link], len(links), t)) > MAX_TOOL_DESCRIPTION_CHARACTERS:
                break
            listed.append(link)
        return WebFetch._describe(description, listed, len(links), t)

    @staticmethod
    def _describe(description: str, listed: list[str], link_count: int, t: LocaleHandler) -> str:
        parts = [description]
        if listed:
            parts.append(t("agent.web_fetch.tool.linked", links="\n".join(f"- {link}" for link in listed)))
        if link_count > len(listed):
            parts.append(t("agent.web_fetch.tool.linked_unlisted", count=link_count - len(listed)))
        return "\n".join(parts)
