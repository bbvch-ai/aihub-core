# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    AllowedBucketConfig,
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    """
    Production runner for NamespaceSelectionAgent.

    This agent orchestrates namespace selection before delegating to RAGAgent.
    It uses LLM-based topic detection and always requires user approval.
    """
    aihub_settings = AIHubSettings()
    servers_list = [NatsSettings().ENDPOINT]

    runner = AgentRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=NamespaceSelectionAgentConfig(
            agent_class=NamespaceSelectionAgent.__name__,
            agent_id="namespace_selection_agent",
            name=LocaleString(
                en="Namespace Selection Agent",
                de="Namespace-Auswahl Agent",
                fr="Agent de selection de namespace",
                it="Agente di selezione namespace",
            ),
            description=LocaleString(
                en="Selects relevant knowledge sources before delegating to RAG",
                de="Wahlt relevante Wissensquellen vor der Weitergabe an RAG",
                fr="Selectionne les sources de connaissances pertinentes avant delegation au RAG",
                it="Seleziona le fonti di conoscenza rilevanti prima della delega al RAG",
            ),
            selection_llm=LLMConfig(model_name="text-generation/mini"),
            allowed_buckets=[
                AllowedBucketConfig(bucket_name=aihub_settings.DEFAULT_BUCKET_NAME, retrieve_k=10),
                AllowedBucketConfig(bucket_name=aihub_settings.SHARED_BUCKET_NAME, retrieve_k=10),
            ],
            rag_agent_class="RAGAgent",
            rag_agent_id="rag_agent",
            max_correction_rounds=3,
            allow_topic_change=True,
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
