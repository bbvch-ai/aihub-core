from dagster import ConfigurableResource, InitResourceContext, ResourceDependency
from llama_index.core.llms import LLM

from aihub_pipeline.resources.llm.LlmHandlerResource import LlmHandlerResource


class LanguageModelResource(ConfigurableResource[LLM]):
    """
    This resource provides a language model for the use in any operation or asset.

    To configure this resource, provide the llm handler as well as the model name.

    Example usage:

    1. Use the language model in an asset:

    .. code-block:: python

        from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
        from aihub_pipeline.resources.llm.LlmHandlerResource import LlmHandlerResource
        from aihub_pipeline.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset
        def asset1(language_model: ResourceParam[LLM]):
            response = language_model.predict("The coolest city in Switzerland is: ")

        namespace = NamespaceResource(name="my_namespace", organization="my_organization")
        llm_handler_resource = LlmHandlerResource(namespace=namespace)

        defs = Definitions(
            assets=[asset1],
            resources={
                "language_model": LanguageModelResource(
                        llm_handler_resource=llm_handler_resource,
                        model_name="gpt-4o-mini",
                    )
                }
        )

    """

    llm_handler_resource: ResourceDependency[LlmHandlerResource]
    model_name: str

    def create_resource(self, context: InitResourceContext) -> LLM:
        model = self.llm_handler_resource.chat_model(
            name=self.model_name,
        )
        if not isinstance(model, LLM):
            raise ValueError(f"Model {self.model_name} is not a language model.")

        return model
