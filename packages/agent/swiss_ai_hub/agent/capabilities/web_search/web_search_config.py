from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import InputNumber, MultiSelect, Select
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.infrastructure import SearxngEngine, SearxngLanguage, SearxngSafeSearch, SearxngTimeRange

from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import (
    MAX_TIMEOUT_SECONDS,
    MIN_PAGE_CHARACTERS,
    MIN_TIMEOUT_SECONDS,
)
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

MIN_RESULTS, MAX_RESULTS = 1, 20
MIN_READ, MAX_READ = 0, 10
MAX_PAGE_CHARACTERS = 20_000
# The search's result event carries every page read whole twice (its block and its sources), events escape non-ASCII
# text (6 bytes a character, 12 for an emoji), and NATS refuses an event over 1 MB; the pages of one search share this.
PAGES_CHARACTER_BUDGET = 40_000
_I18N = "agent.web_search.config"


class WebSearchConfig(Form):
    """How a profile searches the web. Every limit bounds the chat turn: the search and the pages read finish before
    the answer starts, and all of it goes into the prompt."""

    max_results: Annotated[
        int | InputNumber,
        Field(description="Most hits kept from one search, best first, across all its queries."),
        Ge(MIN_RESULTS),
        Le(MAX_RESULTS),
    ] = 5
    read_top_results: Annotated[
        int | InputNumber,
        Field(
            description="How many of the best hits are read whole; the model sees only the snippet of the rest. "
            "0 answers from snippets alone."
        ),
        Ge(MIN_READ),
        Le(MAX_READ),
    ] = 3
    engines: Annotated[
        list[SearxngEngine] | MultiSelect | None,
        Field(description="The search engines asked; none asks every engine the platform's search runs."),
    ] = None
    language: Annotated[
        SearxngLanguage | Select,
        Field(description="The language results are asked in, or `auto` to leave it to the engines."),
    ] = SearxngLanguage.AUTO
    safe_search: Annotated[
        SearxngSafeSearch | Select, Field(description="How strictly the engines filter adult content.")
    ] = SearxngSafeSearch.MODERATE
    time_range: Annotated[
        SearxngTimeRange | Select | None,
        Field(description="Only results from the last day, week, month or year; none for any age."),
    ] = None
    timeout_seconds: Annotated[
        int | InputNumber,
        Field(description="How long one page read whole may take to load before only its snippet is used."),
        Ge(MIN_TIMEOUT_SECONDS),
        Le(MAX_TIMEOUT_SECONDS),
    ] = 15
    max_page_characters: Annotated[
        int | InputNumber,
        Field(
            description="Longest page text passed to the model; longer pages are cut at a paragraph break. The pages of "
            "one search share 40,000 characters, so reading many pages shortens each."
        ),
        Ge(MIN_PAGE_CHARACTERS),
        Le(MAX_PAGE_CHARACTERS),
    ] = 10_000

    def page_characters(self, pages: int) -> int:
        """The longest text each page of one search keeps, so the pages read together fit the search's budget."""
        return min(self.max_page_characters, PAGES_CHARACTER_BUDGET // max(pages, 1))

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            max_results=InputNumber(**cls._labels("max_results"), min=MIN_RESULTS, max=MAX_RESULTS, step=1),
            read_top_results=InputNumber(**cls._labels("read_top_results"), min=MIN_READ, max=MAX_READ, step=1),
            engines=MultiSelect(
                **cls._labels("engines"),
                options=[{"label": engine.value.capitalize(), "value": engine.value} for engine in SearxngEngine],
                option_label="label",
                option_value="value",
            ),
            language=Select(
                **cls._labels("language"),
                options=[
                    {"label": AgentLocaleString.from_i18n_path(f"{_I18N}.languages.{code}"), "value": code}
                    for code in SearxngLanguage
                ],
                option_label="label",
                option_value="value",
            ),
            safe_search=Select(
                **cls._labels("safe_search"),
                options=[
                    {"label": AgentLocaleString.from_i18n_path(f"{_I18N}.safe_search_levels.{level}"), "value": level}
                    for level in SearxngSafeSearch
                ],
                option_label="label",
                option_value="value",
            ),
            time_range=Select(
                **cls._labels("time_range"),
                options=[
                    {"label": AgentLocaleString.from_i18n_path(f"{_I18N}.time_ranges.{period}"), "value": period}
                    for period in SearxngTimeRange
                ],
                option_label="label",
                option_value="value",
            ),
            timeout_seconds=InputNumber(
                **cls._labels("timeout_seconds"), min=MIN_TIMEOUT_SECONDS, max=MAX_TIMEOUT_SECONDS, step=5
            ),
            max_page_characters=InputNumber(
                **cls._labels("max_page_characters"), min=MIN_PAGE_CHARACTERS, max=MAX_PAGE_CHARACTERS, step=1_000
            ),
        )

    @staticmethod
    def _labels(field: str) -> dict[str, AgentLocaleString]:
        return {
            "label": AgentLocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": AgentLocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
