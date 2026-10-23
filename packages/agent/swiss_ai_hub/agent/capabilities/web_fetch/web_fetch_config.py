from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import InputNumber
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

MIN_URLS, MAX_URLS = 1, 20
MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS = 5, 60
MIN_PAGE_CHARACTERS, MAX_PAGE_CHARACTERS = 1_000, 200_000
CHARACTERS_PER_TOKEN = 4


class WebFetchConfig(Form):
    """How a profile reads the pages a message links. Every limit bounds the chat turn: pages are read before the
    answer starts, and all of them go into the prompt."""

    max_urls: Annotated[
        int | InputNumber,
        Field(description="Most links read from one message or tool call; further links are reported, not read."),
        Ge(MIN_URLS),
        Le(MAX_URLS),
    ] = 5
    timeout_seconds: Annotated[
        int | InputNumber,
        Field(description="How long one page may take to load before it is reported as timed out."),
        Ge(MIN_TIMEOUT_SECONDS),
        Le(MAX_TIMEOUT_SECONDS),
    ] = 15
    max_page_characters: Annotated[
        int | InputNumber,
        Field(
            description="Longest page text passed to the model; longer pages are cut at a paragraph break. Counted in "
            "characters, not tokens, because the fetcher that enforces it has no tokenizer."
        ),
        Ge(MIN_PAGE_CHARACTERS),
        Le(MAX_PAGE_CHARACTERS),
    ] = 20_000

    def context_reserve(self, link_count: int) -> int:
        """Tokens to keep free for the pages a message links, so attached files cannot crowd them out."""
        return min(link_count, self.max_urls) * self.max_page_characters // CHARACTERS_PER_TOKEN

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            max_urls=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.web_fetch.config.max_urls.label"),
                help=AgentLocaleString.from_i18n_path("agent.web_fetch.config.max_urls.help"),
                min=MIN_URLS,
                max=MAX_URLS,
                step=1,
            ),
            timeout_seconds=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.web_fetch.config.timeout_seconds.label"),
                help=AgentLocaleString.from_i18n_path("agent.web_fetch.config.timeout_seconds.help"),
                min=MIN_TIMEOUT_SECONDS,
                max=MAX_TIMEOUT_SECONDS,
                step=5,
            ),
            max_page_characters=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.web_fetch.config.max_page_characters.label"),
                help=AgentLocaleString.from_i18n_path("agent.web_fetch.config.max_page_characters.help"),
                min=MIN_PAGE_CHARACTERS,
                max=MAX_PAGE_CHARACTERS,
                step=1_000,
            ),
        )
