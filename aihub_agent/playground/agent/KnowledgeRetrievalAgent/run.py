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
            agent_id="knowledge_retrieval_dev_agent",
            name=LocaleString(
                en="Knowledge Retrieval Dev Agent",
                de="Wissensabruf Dev Agent",
                fr="Agent de récupération de connaissances Dev",
                it="Agente di recupero conoscenze Dev",
            ),
            description=LocaleString(
                en="Retrieves knowledge from vector store for RAG agents",
                de="Ruft Wissen aus dem Vektorspeicher für RAG-Agenten ab",
                fr="Récupère les connaissances du magasin de vecteurs pour les agents RAG",
                it="Recupera le conoscenze dal vector store per gli agenti RAG",
            ),
            retrieval=KnowledgeRetrievalStepConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/large"),
                vector_store=MilvusVectorStoreConfig(
                    uri=MilvusSettings().URL,
                    collection_name=settings.DEFAULT_KNOWLEDGE_BUCKET,
                    dimensions=MilvusSettings().DIMENSION,
                ),
                namespaces=[settings.DEFAULT_KNOWLEDGE_NAMESPACE],
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
