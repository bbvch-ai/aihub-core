import asyncio

from aihub_lib.agents.step_configs import InsightRetrievalStepConfig
from aihub_lib.generative_ai.retrievers import InsightSourceConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents.InsightRetrievalAgent.configs.InsightRetrievalAgentConfig import InsightRetrievalAgentConfig
from aihub_agent.agents.InsightRetrievalAgent.InsightRetrievalAgent import InsightRetrievalAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=InsightRetrievalAgent,
        default_agent_config=InsightRetrievalAgentConfig(
            agent_class=InsightRetrievalAgent.__name__,
            agent_id="insight_retrieval_dev_agent",
            name=LocaleString(
                en="Insight Retrieval Dev Agent",
                de="Einblickabruf Dev Agent",
                fr="Agent de récupération d'insights Dev",
                it="Agente di recupero insight Dev",
            ),
            description=LocaleString(
                en="Retrieves expert insights from MongoDB for RAG agents",
                de="Ruft Experteneinblicke aus MongoDB für RAG-Agenten ab",
                fr="Récupère les insights experts depuis MongoDB pour les agents RAG",
                it="Recupera gli insight esperti da MongoDB per gli agenti RAG",
            ),
            retrieval=InsightRetrievalStepConfig(
                sources=[
                    InsightSourceConfig(
                        namespace="default",
                        agent_class="ExpertAskingAgent",
                        agent_id="expert_agent",
                    ),
                ],
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
