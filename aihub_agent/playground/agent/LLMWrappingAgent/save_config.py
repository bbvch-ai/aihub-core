from mongoengine import connect

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument

config = LLMWrappingAgentConfig(
    agent_class=LLMWrappingAgent.__name__,
    agent_id="dev_agent",
    name=LocaleString(en="Dev Agent Override"),
    description=LocaleString(en="This Agent config should override the default config"),
    llm=AzureOpenAILLMConfig(
        name="gpt-4o",
        base_url="https://aihub-dev-openai-che.openai.azure.com/",
        api_version="2024-12-01-preview",
        prompt_tokens_costs_per_thousand=0.0045,
        completion_tokens_costs_per_thousand=0.0133,
        default_parameter=AzureOpenAIParameter(temperature=0.0),
    ),
)

cosmos_conn_singleton = CosmosAccess()
host = cosmos_conn_singleton.get_connection_string()
connect(db=ApiConfig().DB_NAME, host=host)

entity = AgentConfigEntityDocument.from_agent_config(config)
entity.save()
