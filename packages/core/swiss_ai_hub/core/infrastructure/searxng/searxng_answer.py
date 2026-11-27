from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.searxng.searxng_result import SearxngResult


class SearxngAnswer(BaseModel):
    """One search's hits, and the engines that did not answer it.

    SearXNG answers 200 with no hits when every engine refused (a CAPTCHA, a rate limit), so the engines are what
    tells an empty search apart from a blocked one.
    """

    results: Annotated[list[SearxngResult], Field(description="The hits linking to a web page, best first.")] = []
    unresponsive_engines: Annotated[
        list[str], Field(description="The engines that did not answer, each with SearXNG's reason.")
    ] = []
