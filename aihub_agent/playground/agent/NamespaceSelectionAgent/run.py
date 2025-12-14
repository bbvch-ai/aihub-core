import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.agents.NamespaceSelectionAgent.configs.BucketReference import BucketReference
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.RagAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.AgentReference import AgentReference
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    settings = AIHubSettings()
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=NamespaceSelectionAgentConfig(
            agent_class=NamespaceSelectionAgent.__name__,
            agent_id="namespace_selection_dev_agent",
            name=LocaleString(
                en="Namespace Selection Dev Agent",
                de="Namespace-Auswahl Dev Agent",
                fr="Agent de Selection de Namespace Dev",
                it="Agente di Selezione Namespace Dev",
            ),
            description=LocaleString(
                en="Dev agent that asks users to select which knowledge namespace to search",
                de="Dev Agent, der Benutzer fragt, welchen Wissens-Namespace sie durchsuchen moechten",
                fr="Agent dev qui demande aux utilisateurs de selectionner le namespace de connaissances",
                it="Agente dev che chiede agli utenti di selezionare quale namespace di conoscenza cercare",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            # Reference the default bucket by name - matches playground/dev setup
            buckets=[
                BucketReference(bucket_name=settings.DEFAULT_KNOWLEDGE_BUCKET),
            ],
            # Delegate to the dev RAG agent after namespace selection
            rag_agent=AgentReference(
                agent_class=RAGAgent.__name__,
                agent_id="rag_dev_agent",
            ),
            # The knowledge retrieval agent ID within the RAG agent config
            knowledge_retrieval_agent_id="knowledge_retrieval_dev_agent",
            selection_prompt=LocaleString(
                en="Please select which knowledge area you'd like to search.",
                de="Bitte waehlen Sie den Wissensbereich aus, den Sie durchsuchen moechten.",
                fr="Veuillez selectionner le domaine de connaissances que vous souhaitez rechercher.",
                it="Seleziona l'area di conoscenza che desideri cercare.",
            ),
            max_selection_attempts=5,
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
