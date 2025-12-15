import asyncio

from aihub_lib.agents.step_configs import KnowledgeRetrievalStepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.models.RetrieveSummariesConfig import RetrieveSummariesConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.KnowledgeRetrievalAgent.configs.KnowledgeRetrievalAgentConfig import (
    KnowledgeRetrievalAgentConfig,
)
from aihub_agent.agents.KnowledgeRetrievalAgent.KnowledgeRetrievalAgent import KnowledgeRetrievalAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    settings = AIHubSettings()
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=KnowledgeRetrievalAgent,
        default_agent_config=KnowledgeRetrievalAgentConfig(
            agent_class=KnowledgeRetrievalAgent.__name__,
            agent_id="shared_knowledge_retrieval_agent",
            name=LocaleString(
                en="Shared Knowledge Retrieval Agent",
                de="Geteiltes Wissensabruf Agent",
                fr="Agent de recuperation de connaissances partagees",
                it="Agente di recupero conoscenze condivise",
            ),
            description=LocaleString(
                en="Retrieves shared knowledge from vector store for RAG agents",
                de="Ruft geteiltes Wissen aus dem Vektorspeicher fuer RAG-Agenten ab",
                fr="Recupere les connaissances partagees du magasin de vecteurs pour les agents RAG",
                it="Recupera le conoscenze condivise dal vector store per gli agenti RAG",
            ),
            retrieval=KnowledgeRetrievalStepConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/large"),
                vector_store=MilvusVectorStoreConfig(
                    uri=MilvusSettings().URL,
                    collection_name=settings.SHARED_KNOWLEDGE_BUCKET,
                    dimensions=MilvusSettings().DIMENSION,
                ),
                namespaces=[settings.SHARED_KNOWLEDGE_NAMESPACE],
                retrieve_k=10,
                query_mode=VectorStoreQueryMode.HYBRID,
                node_types=["content"],
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=10,
                    mode=ModeOptions.BOTH,
                ),
                retrieve_summaries=RetrieveSummariesConfig(
                    max_parent_levels=2,
                ),
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
