from typing import List, Optional

from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.openai_like import OpenAILike

from aihub.app.handlers.CostTracker import CostTracker
from aihub.entities.LLM.chat.AzureOpenAILLMEntity import AzureOpenAIParameter
from aihub.entities.LLM.chat.ChatLLMEntity import ChatLLMModelParameter
from aihub.entities.LLM.embedding.AzureOpenAIEmbeddingEntity import AzureOpenAIEmbeddingParameter
from aihub.entities.LLM.embedding.EmbeddingLLMEntity import EmbeddingLLMModelParameter
from aihub.entities.LLM.factory.LLMEntityFactory import LLMEntityFactory
from aihub.entities.LLM.LLMEntity import ModelParameter
from aihub.records.agent.Costs import Costs


class LLMHandler:
    def __init__(self, organization: str):
        self._organization = organization
        self._cost_trackers: List[CostTracker] = []

    def model_by_name(
        self,
        name: str,
        model_parameter: Optional[ModelParameter] = None,
    ) -> OpenAILike | AzureOpenAI | AzureOpenAIEmbedding | TextEmbeddingsInference:
        model_entity = LLMEntityFactory.by_name(self._organization, name)
        model, cost_tracker = model_entity.to_llama_index(model_parameter)
        self._cost_trackers.append(cost_tracker)
        return model

    def chat_model(self, name, model_parameter: Optional[ChatLLMModelParameter] = None) -> OpenAILike | AzureOpenAI:
        return self.model_by_name(name, model_parameter)

    def embedding_model(
        self, name, model_parameter: Optional[EmbeddingLLMModelParameter] = None
    ) -> AzureOpenAIEmbedding | TextEmbeddingsInference:
        return self.model_by_name(name, model_parameter)

    def gpt3(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-35-turbo", model_parameter)

    def gpt3_16k(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-35-turbo-16k", model_parameter)

    def gpt4(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-4", model_parameter)

    def gpt4_32k(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-4-32k", model_parameter)

    def gpt4o(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-4o", model_parameter)

    def gpt4o_mini(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> AzureOpenAI:
        return self.chat_model("gpt-4o-mini", model_parameter)

    def ada2(self, model_parameter: Optional[AzureOpenAIEmbeddingParameter] = None) -> AzureOpenAIEmbedding:
        return self.embedding_model("text-embedding-ada-002", model_parameter)

    def get_total_costs(self) -> Costs:
        prompt_token_count = 0
        completion_token_count = 0
        embedding_token_count = 0
        prompt_tokens_costs = 0
        completion_tokens_costs = 0
        embedding_tokens_costs = 0

        for cost_tracker in self._cost_trackers:
            costs = cost_tracker.get_total_costs()
            prompt_token_count += costs.prompt_token_count
            completion_token_count += costs.completion_token_count
            embedding_token_count += costs.embedding_token_count
            prompt_tokens_costs += costs.prompt_tokens_costs
            completion_tokens_costs += costs.completion_tokens_costs
            embedding_tokens_costs += costs.embedding_tokens_costs

        return Costs(
            prompt_token_count=prompt_token_count,
            completion_token_count=completion_token_count,
            embedding_token_count=embedding_token_count,
            prompt_tokens_costs=prompt_tokens_costs,
            completion_tokens_costs=completion_tokens_costs,
            embedding_tokens_costs=embedding_tokens_costs,
        )
