from typing import Annotated

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel, Field

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.router.RouteOptions import RouteOptions
from swiss_ai_hub.core.nats.events.router.RouterEvent import RouterEvent


async def route_to_event_using_llm(
    instructions: str, routes: list[RouteOptions], llm: LLM, t: LocaleHandler
) -> RouterEvent:
    class RouteSelectionModel(BaseModel):
        """Model for selecting a routing option."""

        selected_option_index: Annotated[
            int, Field(description=t("lib.prompt.router.selected_option_index"), ge=0, lt=len(routes))
        ]
        reason: Annotated[str, Field(description=t("lib.prompt.router.reason"))]

    prompt_text = t("lib.prompt.router.routing_prompt")

    prompt = RichPromptTemplate(prompt_text)

    result = await llm.astructured_predict(RouteSelectionModel, prompt, instructions=instructions, routes=routes)

    return RouterEvent(routes=routes, selected_option=routes[result.selected_option_index], reason=result.reason)
