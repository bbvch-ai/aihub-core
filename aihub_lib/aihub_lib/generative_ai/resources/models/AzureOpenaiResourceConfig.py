from typing import Annotated

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic import Field

from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceConfig


class AzureOpenaiResourceConfig(ResourceConfig):
    """
    An Azure OpenAI-based resource that is defined through an API and a deployment.
    """

    api_version: Annotated[str, Field(description="Azure OpenAI API version for embeddings.")]
    deployment: Annotated[str | None, Field(description="Deployment name. If not set, defaults to resource name.")] = (
        None
    )

    def get_openai_client(self) -> AsyncAzureOpenAI:
        """
        Returns the Azure OpenAI client for the resource.
        Uses either API key or Azure AD credentials based on configuration.
        """
        if self.api_key:
            return AsyncAzureOpenAI(
                azure_endpoint=self.base_url,
                azure_deployment=self.deployment or self.name,
                api_key=self.api_key,
                api_version=self.api_version,
            )
        else:
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
