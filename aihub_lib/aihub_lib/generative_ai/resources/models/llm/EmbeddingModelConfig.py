from typing import Annotated, Literal, Self

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.openai_like import OpenAILikeEmbedding
from opentelemetry.propagate import inject
from pydantic import Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
from aihub_lib.nats.events.form.constraints import Ge
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.ModelSelect import ModelSelect
from aihub_lib.nats.events.form.elements.Select import Select
from aihub_lib.nats.events.form.Form import Form


class EmbeddingLLMParameter(Form):
    """
    Parameters specific to embedding models.

    Supports duality pattern: instantiate with FormkitElements for form mode,
    or with primitive values for data mode.
    """

    max_retries: Annotated[
        int | InputNumber,
        Field(description="Maximum number of retries."),
        Ge(0),
    ] = 10
    timeout: Annotated[
        float | InputNumber,
        Field(description="Timeout for each request."),
        Ge(0),
    ] = 60.0
    encoding_format: Annotated[
        Literal["float", "base64"] | None | Select,
        Field(description="Format of the returned embeddings. Defaults to 'float'."),
    ] = "float"
    dimensions: Annotated[
        int | None | InputNumber,
        Field(
            description="Number of dimensions for output embeddings. Supported in text-embedding-3 and later models."
        ),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode EmbeddingLLMParameter with input elements."""
        return cls(
            max_retries=InputNumber(
                label=LocaleString.from_i18n_path("lib.embedding.config.max_retries.label"),
                help=LocaleString.from_i18n_path("lib.embedding.config.max_retries.help"),
                min=0,
                step=1,
            ),
            timeout=InputNumber(
                label=LocaleString.from_i18n_path("lib.embedding.config.timeout.label"),
                help=LocaleString.from_i18n_path("lib.embedding.config.timeout.help"),
                min=0,
                step=5,
            ),
            encoding_format=Select(
                label=LocaleString.from_i18n_path("lib.embedding.config.encoding_format.label"),
                help=LocaleString.from_i18n_path("lib.embedding.config.encoding_format.help"),
                options=[
                    {"label": "Float", "value": "float"},
                    {"label": "Base64", "value": "base64"},
                ],
                option_label="label",
                option_value="value",
            ),
            dimensions=InputNumber(
                label=LocaleString.from_i18n_path("lib.embedding.config.dimensions.label"),
                help=LocaleString.from_i18n_path("lib.embedding.config.dimensions.help"),
                min=1,
                step=1,
            ),
        )


class EmbeddingModelConfig(LiteLLMBase[OpenAILikeEmbedding]):
    """
    Configuration for an embedding model.

    ### Why EmbeddingModelConfig?
    Embedding models produce vector representations of text. They may have different endpoints
    and possibly fewer parameters compared to chat models. This config ensures each embedding
    model can be integrated uniformly with llama_index and cost tracking.
    """

    model_name: Annotated[str | ModelSelect, Field(description="Name of the embedding model.")]
    default_parameter: Annotated[
        EmbeddingLLMParameter,
        Field(
            description="Default parameters for the embedding model.",
            title="Embedding Parameters",
        ),
    ] = EmbeddingLLMParameter()

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode EmbeddingModelConfig."""
        return cls(
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.embedding.config.model.label"),
                help=LocaleString.from_i18n_path("lib.embedding.config.model.help"),
                mode="embedding",
            ),
            default_parameter=EmbeddingLLMParameter.as_form(),
        )

    def to_llama_index(self) -> tuple[OpenAILikeEmbedding, LLMCostTracker]:
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            embedding_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
        )

        default_headers = {}
        inject(default_headers)

        open_ai_like_embedding = OpenAILikeEmbedding(
            model_name=self.model_name,
            api_base=config.BASE_URL,
            api_key=config.API_KEY.get_secret_value(),
            max_retries=self.default_parameter.max_retries,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.default_parameter.timeout,
            default_headers=default_headers,
        )

        return open_ai_like_embedding, cost_tracker
