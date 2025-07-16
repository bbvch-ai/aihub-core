import asyncio

from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.testing.logging.logger import enable_logging
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="dev_agent",
            agent_class=RAGAgent.__name__,
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. "
                "Only use the context information provided, either as documents or images."
                "Analyze the context information and provide a detailed answer to the user question. "
                "If you don't know the answer, say 'I don't know'."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://bbvaihub-openai-sui.openai.azure.com",
                api_version="2025-01-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-3-large",
                    base_url="https://bbvaihub-openai-sui.openai.azure.com",
                    api_version="2024-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                ),
                index_namespaces=["test"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.DEFAULT,
                node_types=["content"],
                vector_store=MilvusVectorStoreConfig(
                    uri="http://localhost:19530",
                    collection_name="test",
                    dimensions=3072,
                ),
                retrieve_prev_next=RetrievePrevNextConfig(num_nodes=10, mode=ModeOptions.BOTH),
            ),
            number_of_input_tokens=100_000,
            condense_question_prompt=LocaleString(
                en="Given the following conversation between a user "
                "and an AI assistant and a follow-up question from the user,"
                "rephrase the follow-up question to be a standalone question."
                "\n"
                "Chat history:"
                "{chat_history}"
                "Follow-up input: {question}"
                "Standalone question:"
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
