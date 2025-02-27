import asyncio
import logging
from dotenv import load_dotenv
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pathlib import Path

from aihub_agent.agents.rag.MultiHopRAGAgent.MultiHopRAGAgent import MultiHopRAGAgent
from aihub_agent.agents.rag.MultiHopRAGAgent.configs.MultiHopRAGAgentConfig import MultiHopRAGAgentConfig
from aihub_agent.agents.rag.RAGAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import create_azure_ai_search_vector_store

logging.getLogger("opentelemetry").setLevel(logging.ERROR)

load_dotenv(Path(__file__).parent / ".env")


async def main():
    vector_store = create_azure_ai_search_vector_store("development", semantic_configuration_name="default")
    return AgentTestRunner(
        agent_type=MultiHopRAGAgent,
        agent_config=MultiHopRAGAgentConfig(
            agent_id="multi_hop_rag_agent",
            name=LocaleString(en="Multi Hop RAG Agent"),
            description=LocaleString(
                en="This is an agent that can be used to answer user questions using Multi Hop RAG"
            ),
            system_prompt=LocaleString(en="You're answering user requests. Only use the context information provided."),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-08-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-ada-002",
                    base_url="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-05-15",
                    embedding_tokens_costs_per_thousand=0.0,
                    default_parameter=AzureOpenAIEmbeddingParameter(),
                ),
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.HYBRID,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode="both",
                ),
            ),
            number_of_input_tokens=100000,
            hops=hops,
            decompose_chat_history_prompt=LocaleString(
                en="""
                Given the following conversation between a user and an assistant and a follow-up question from the user,
                rephrase the follow-up question into multiple questions.

                Chat history:
                {chat_history}
                Follow-up input: {question}
                Multiple questions:"""
            ),
            context_prompt=LocaleString(
                en="""
                You are provided with some additional context information in form of structured documents with its general
                structure and relevant information in more detail. Each document starts with an indicator <DOC_START [documentname]>
                and ends with <DOC_END [documentname]>.
                Here are the relevant documents for the context:

                {context_str}

                Instruction: Based on the above documents, provide a detailed answer for the user question below."""
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
