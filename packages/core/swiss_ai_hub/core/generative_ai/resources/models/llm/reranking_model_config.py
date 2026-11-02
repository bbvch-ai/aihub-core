from typing import Annotated, Self

from cohere import ClientV2
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.postprocessor.cohere_rerank import CohereRerank
from pydantic import Field

from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base import LiteLLMBase
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

# A rerank is one short request–response that normally takes a few seconds, so a call still open after this long
# is stuck rather than slow, and the callers fall back to retrieval order. Cohere's client applies a single float
# to every phase (and overrides a passed-in http client's timeout with it), so the connect cannot be bounded apart.
RERANK_TIMEOUT_SECONDS = 30.0


class RerankingModelConfig(LiteLLMBase[CohereRerank]):
    """
    Configuration for a reranking model.

    Supports duality pattern for form rendering and data validation.
    """

    top_n: Annotated[
        int | InputNumber,
        Field(description="Number of documents to return after reranking."),
        Ge(1),
        Le(100),
    ] = 5

    @classmethod
    def as_form(cls, model_name: str | None = None) -> Self:
        """Factory method to create a form-mode RerankingModelConfig, its picker preset to `model_name` if given."""
        return cls(
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.reranking.config.model.label"),
                help=LocaleString.from_i18n_path("lib.reranking.config.model.help"),
                mode="rerank",
                value=model_name,
            ),
            top_n=InputNumber(
                label=LocaleString.from_i18n_path("lib.reranking.config.top_n.label"),
                help=LocaleString.from_i18n_path("lib.reranking.config.top_n.help"),
                min=1,
                max=100,
                step=1,
            ),
        )

    def to_llama_index(
        self, extra_headers: dict[str, str] | None = None, api_key: str | None = None
    ) -> tuple[CohereRerank, LLMCostTracker]:
        # extra_headers accepted for LiteLLMBase signature parity but unused —
        # llama_index CohereRerank does not expose a header injection point.
        del extra_headers
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            prompt_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
            completion_tokens_costs_per_thousand=0,
        )

        resolved_api_key = api_key or config.API_KEY.get_secret_value()
        reranking_service = CohereRerank(
            model=self.model_name,
            api_key=resolved_api_key,
            base_url=config.BASE_URL,
            top_n=self.top_n,
        )
        # CohereRerank builds its client without a timeout, which leaves cohere's 300 s default.
        reranking_service._client = ClientV2(
            api_key=resolved_api_key, base_url=config.BASE_URL, timeout=RERANK_TIMEOUT_SECONDS
        )

        return reranking_service, cost_tracker
