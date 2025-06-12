import asyncio

from dotenv import load_dotenv
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.logging.logger import enable_logging

enable_logging(30)
load_dotenv()


async def main():
    runner = AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="dev_agent",
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided, either as documents or images."
                "Analyze the context information and provide a detailed answer to the user question. If you don't know the answer, say 'I don't know'."
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
                vector_store=create_milvus_vector_store(
                    uri="http://localhost:19530",
                    collection_name="test",
                    embedding_vector_dimension=3072,
                ),
                retrieve_prev_next=RetrievePrevNextConfig(num_nodes=10, mode=ModeOptions.BOTH),
            ),
            number_of_input_tokens=100_000,
            condense_question_prompt=LocaleString(
                en="Given the following conversation between a user and an AI assistant and a follow-up question from the user,"
                "rephrase the follow-up question to be a standalone question."
                "\n"
                "Chat history:"
                "{chat_history}"
                "Follow-up input: {question}"
                "Standalone question:"
            ),
            context_prompt=LocaleString(
                en="You are provided with some additional context information in form of structured documents with its general"
                "structure and relevant information in more detail. Each document starts with an indicator <REFERENCE_DOCUMENT [metadata]>"
                "and ends with </REFERENCE_DOCUMENT>. Inside the documents images are marked with <IMAGE> tags. Take a look ath the images"
                "if there are any, they might contain relevant information for the user question."
                "Here are the relevant documents for the context:"
                "\n"
                "{context_str}"
                "\n"
                "Instruction: Based on the above documents, provide a detailed answer for the user question below."
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
