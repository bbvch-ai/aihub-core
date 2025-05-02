from typing import List

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent


async def route_to_event_using_llm(
    instructions: str, routes: List[RouteOptions], llm: LLM, t: LocaleHandler
) -> RouterEvent:
    class RouteSelectionModel(BaseModel):
        """Model for selecting a routing option."""

        selected_option_index: int = Field(
            ..., description=t("lib.prompt.router.selected_option_index"), ge=0, lt=len(routes)
        )
        reason: str = Field(..., description=t("lib.prompt.router.reason"))

    # Load the prompt template from the YAML file
    prompt_text = t("lib.prompt.router.routing_prompt")

    # Create the RichPromptTemplate
    prompt = RichPromptTemplate(prompt_text)

    # Get the LLM's decision
    result = await llm.astructured_predict(RouteSelectionModel, prompt, instructions=instructions, routes=routes)

    # Create and return the RouterEvent
    return RouterEvent(routes=routes, selected_option=routes[result.selected_option_index], reason=result.reason)
