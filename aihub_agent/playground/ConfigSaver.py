from mongoengine import connect

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.agents.AgentConfigEntity import AgentConfigEntity


class ConfigSaver:
    def __init__(self, db_name: str = "aihub"):
        self.connection = connect(
            db=db_name,
            host=CosmosAccess().get_connection_string(),
        )

    def save_config(self, config: AgentConfig) -> AgentConfigEntity:
        if not self.connection:
            raise ValueError(f"{self.__class__.__name__} is not connected to a database.")
        entity = AgentConfigEntity.find_for_class_and_id(agent_class=config.agent_class, agent_id=config.agent_id)
        if entity:
            entity.update_from_agent_config(config)
        else:
            entity = AgentConfigEntity.from_agent_config(config)
        entity.save()
        return entity
