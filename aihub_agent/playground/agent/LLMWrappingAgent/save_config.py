from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from mongoengine import connect

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig

config = LLMWrappingAgentConfig(
    agent_class=LLMWrappingAgent.__name__,
    agent_id="dev_agent",
    name=LocaleString(en="Dev Agent Override"),
    description=LocaleString(en="This Agent config should override the default config"),
    llm=LLMConfig(model_name="azure/gpt-4o-mini"),
)

cosmos_conn_singleton = CosmosAccess()
host = cosmos_conn_singleton.get_connection_string()
connect(db=ApiConfig().DB_NAME, host=host)

entity = AgentConfigEntityDocument.from_agent_config(config)
entity.save()
