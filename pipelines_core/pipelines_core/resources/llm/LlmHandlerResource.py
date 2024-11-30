from dagster import ConfigurableResource, InitResourceContext, ResourceDependency

from lib_core.handlers.LLMHandler import LLMHandler
from pipelines_core.pipelines_core.resources.organization.NamespaceResource import NamespaceResource
from pipelines_core.pipelines_core.util.connection_utils import connect_to_mongo_db


class LlmHandlerResource(ConfigurableResource[LLMHandler]):
    """
    This resource gives assets and ops direct access to the llm handler.

    Example usage:

    1. Use the llm handler in an asset:

    .. code-block:: python

        from pipelines_core.resources.llm.LanguageModelResource import LanguageModelResource
        from pipelines_core.resources.llm.LlmHandlerResource import LlmHandlerResource
        from pipelines_core.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset
        def asset1(llm_handler: ResourceParam[LLMHandler]):
            response = llm_handler.gpt4o().predict("The coolest city in Switzerland is: ")

        defs = Definitions(
            assets=[asset1],
            resources={
                "llm_handler": LlmHandlerResource(
                        namespace=NamespaceResource(name="my_namespace", organization="my_organization")
                    )
                }
        )

    """

    namespace: ResourceDependency[NamespaceResource]

    def create_resource(self, context: InitResourceContext) -> LLMHandler:
        connect_to_mongo_db(self.namespace.organization)
        return LLMHandler(self.namespace.organization)
