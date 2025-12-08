from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from mongoengine import connect

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig

config = LLMWrappingAgentConfig(
    agent_class=LLMWrappingAgent.__name__,
    agent_id="dev_agent",
    name=LocaleString(en="Dev Agent Override"),
    description=LocaleString(en="This Agent config should override the default config"),
    llm=LLMConfig(model_name="text-generation/nano"),
)

connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())

entity = AgentConfigEntityDocument.from_agent_config(config)
entity.save()
