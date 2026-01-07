# ruff: noqa: E402
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

from aihub_agent.agents.NamespaceSelectionAgent.configs.RAGDelegationConfig import RAGDelegationConfig

from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.agents.NamespaceSelectionAgent.configs import NamespaceSelectionAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=NamespaceSelectionAgentConfig(
            agent_class=NamespaceSelectionAgent.__name__,
            agent_id="namespace_selection_dev_agent",
            name=LocaleString(
                en="Namespace Selection Dev Agent",
                de="Namespace-Auswahl Dev Agent",
                fr="Agent de sélection de namespace dev",
                it="Agente di selezione namespace dev",
            ),
            description=LocaleString(
                en="Agent that prompts for namespace selection before delegating to RAG",
                de="Agent, der vor der Delegation an RAG nach Namespace-Auswahl fragt",
                fr="Agent qui demande une sélection de namespace avant de déléguer à RAG",
                it="Agente che richiede la selezione del namespace prima di delegare a RAG",
            ),
            llm=LLMConfig(model_name="text-generation/nano"),
            bucket_names=["defaultknowledge", "sharedknowledge"],
            rag_delegation=RAGDelegationConfig(
                rag_agent_class="RAGAgent",
                rag_agent_id="rag_dev_agent",
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
