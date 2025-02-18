from dagster import ConfigurableResource, InitResourceContext
from llama_index.core.llms import LLM

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_lib.generative_ai.resources.models.llm.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig


class LanguageModelResource(ConfigurableResource[LLM]):
    """
    This resource provides a language model for the use in any operation or asset.

    Example usage:

    1. Use the language model in an asset:

    .. code-block:: python

        from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource

        from dagster import Definitions, asset

        @asset
        def asset1(language_model: ResourceParam[LLM]):
            response = language_model.predict("The coolest city in Switzerland is: ")

        defs = Definitions(
            assets=[asset1],
            resources={
                "language_model": LanguageModelResource(
                    AzureOpenAILLMConfig(
                        name="gpt-4o",
                        base_url="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-08-01-preview",
                        prompt_tokens_costs_per_thousand=0.0045,
                        completion_tokens_costs_per_thousand=0.0133,
                        default_parameter=AzureOpenAIParameter(temperature=0.0),
                    )
                )
            }
        )

    """

    model: AzureOpenAILLMConfig | SelfHostedLLMConfig

    def create_resource(self, context: InitResourceContext) -> LLM:
        llm, _ = self.model.to_llama_index(self.model.default_parameter)
        return llm
