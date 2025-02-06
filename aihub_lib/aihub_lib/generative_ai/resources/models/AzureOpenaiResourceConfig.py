from typing import Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic import Field

from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceConfig


class AzureOpenaiResourceConfig(ResourceConfig):
    """
    A azure openai based resources that are defined through an api and a deployment.
    """

    api_version: str = Field(..., description="Azure OpenAI API version for embeddings.")
    deployment: Optional[str] = Field(None, description="Deployment name. If not set, defaults to resource name.")

    def get_openai_client(self) -> AsyncAzureOpenAI:
        """
        Returns the Azure OpenAI client for the resource.
        """
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        return AsyncAzureOpenAI(
            azure_endpoint=self.base_url,
            azure_deployment=self.deployment or self.name,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
        )
