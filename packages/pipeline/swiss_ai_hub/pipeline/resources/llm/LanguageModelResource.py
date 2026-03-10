from dagster import ConfigurableResource, InitResourceContext, ResourceDependency
from llama_index.core.llms import LLM
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig


class LanguageModelResource(ConfigurableResource[LLM]):
    """
    This resource provides a language model for the use in any operation or asset.

    Example usage:

    1. Use the language model in an asset:

    .. code-block:: python

        from swiss_ai_hub.pipeline.resources.llm.LanguageModelResource import LanguageModelResource

        from dagster import Definitions, asset

        @asset
        def asset1(language_model: ResourceParam[LLM]):
            response = language_model.predict("The coolest city in Switzerland is: ")

        defs = Definitions(
            assets=[asset1],
            resources={
                "language_model": LanguageModelResource(
                    llm_config=LLMConfig(model_name="azure/gpt-4o-mini")
                )
            }
        )

    """

    llm_config: ResourceDependency[LLMConfig]

    def create_resource(self, context: InitResourceContext) -> LLM:
        llm, _ = self.llm_config.to_llama_index()
        if not isinstance(llm, LLM):
            raise ValueError("The returned model is not an instance of LLM.")
        return llm
