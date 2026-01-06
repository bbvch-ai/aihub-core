from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.rag import KnowledgeSource
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.llms import LLM

from aihub_agent.agents.NamespaceSelectionAgent.events.KeepSourcesEvent import KeepSourcesEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.SelectNewSourcesEvent import SelectNewSourcesEvent


async def route_topic_change_response(
    llm: LLM,
    t: LocaleHandler,
    user_response: str,
    current_sources: list[KnowledgeSource],
) -> RouterEvent:
    """
    Route user's response to topic change question.

    Uses LLM router pattern to interpret whether the user wants to keep
    using the current knowledge sources or select new ones for their query.

    Routes:
    - KeepSourcesEvent: User wants to continue with current sources
    - SelectNewSourcesEvent: User wants to select new/different sources
    """
    instructions = t(
        "lib.prompt.routing.topic_response.instructions",
        user_response=user_response,
    )

    routes = [
        RouteOptions.for_event(
            event=KeepSourcesEvent(
                current_sources=current_sources,
                reasoning=t("lib.prompt.routing.topic_response.keep_reasoning"),
            ),
            instructions=t("lib.prompt.routing.topic_response.keep_instructions"),
        ),
        RouteOptions.for_event(
            event=SelectNewSourcesEvent(
                reasoning=t("lib.prompt.routing.topic_response.select_new_reasoning"),
                user_preference=user_response,
            ),
            instructions=t("lib.prompt.routing.topic_response.select_new_instructions"),
        ),
    ]

    return await route_to_event_using_llm(instructions, routes, llm, t)
