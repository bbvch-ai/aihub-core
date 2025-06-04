from mongoengine import ObjectIdField, StringField

from aihub_lib.persistence.process.ProcessStepInstanceEntity import (
    BaseProcessEntityIn,
    BaseProcessEntityOut,
    ProcessStepInstanceEntity,
)


class AgentIn(BaseProcessEntityIn):
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)


class AgentOut(BaseProcessEntityOut):
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)


class AgentProcessStepInstanceEntity(ProcessStepInstanceEntity):
    start_event_id = ObjectIdField(required=True)
    stop_event_id = ObjectIdField()
