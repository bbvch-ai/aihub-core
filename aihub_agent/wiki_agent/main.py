import asyncio
import logging

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.testing.logging.logger import enable_logging

from wiki_agent.WikiAgent.WikiAgent import WikiAgent
from wiki_agent.WikiAgent.WikiAgentConfig import WikiAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings

enable_logging(level=logging.WARNING)


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    embedding_config = EmbeddingModelConfig(model_name="azure/text-embedding-3-large")
    retrieve_step_config = RetrieveStepConfig(
        embed_model=embedding_config,
        index_namespaces=["focus_day_2"],
        retrieve_k=10,
        query_mode="default",
        node_types=["content"],
        vector_store=MilvusVectorStoreConfig(
            uri=MilvusSettings().URL,
            dimensions=MilvusSettings().DIMENSION,
            collection_name="playground",
        ),
    )
    runner = AgentRunner(
        agent_type=WikiAgent,
        default_agent_config=WikiAgentConfig(
            agent_class=WikiAgent.__name__,
            agent_id="wiki_agent",
            name=LocaleString(en="Wiki Agent"),
            description=LocaleString(en="This is a simple agent created from a template."),
            llm=LLMConfig(model_name="azure/gpt-4o-mini"),
            retrieve_step_config=retrieve_step_config,
            number_of_input_tokens=128000,
            context_prompt=LocaleString(en="Here is some Information available found in our wiki {context}"),
            system_prompt=LocaleString(
                en="""You are a helpful assistant. You are able to answer questions about the wiki."""
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
