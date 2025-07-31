import asyncio

from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
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
        default_agent_config=RAGAgentConfig(
            agent_id="dev_agent",
            agent_class=RAGAgent.__name__,
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            llm=LLMConfig(model_name="azure/gpt-4o-mini"),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=EmbeddingModelConfig(model_name="azure/text-embedding-3-large"),
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
