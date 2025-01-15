from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig


class RAGAgentConfig(AgentConfig):
    """
    Describes the configuration for the RAG agent.

    The RAGAgent needs to be configured with the LLM and retrieval step configuration to function.
    This allows us to customize the agent with which models to use and how to retrieve information.

    ### Example

        ```python
        RAGAgentConfig(
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0, max_tokens=50000),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-ada-002",
                    api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                    default_parameter=AzureOpenAIEmbeddingParameter(),
                ),
                index_name="development",
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode="hybrid",
                node_types=["content"],
            ),
            condense_question_prompt=LocaleString(
                en='Given the following conversation between a user and an AI assistant and a follow-up question from the user, rephrase the follow-up question to be a standalone question. Chat history: {chat_history} Follow-up input: {question} Standalone question:'
            ),
            context_prompt=LocaleString(
                en='Given the following conversation between a user and an AI assistant, order the nodes in the conversation based on the context provided. Chat history: {chat_history}'
            ),
        )
        ```

    """
    llm: AzureOpenAILLMConfig = Field(..., description="The LLM configuration for the agent.")
    retrieve_step_config: RetrieveStepConfig = Field(..., description="The configuration for the retrieval step.")
    number_of_input_tokens: int = Field(..., description="Maximum number of input tokens to use for the LLM.")
    condense_question_prompt: LocaleString = Field(..., description="The prompt for condensing standalone questions.")
    context_prompt: LocaleString = Field(..., description="The prompt around the context information (nodes).")
