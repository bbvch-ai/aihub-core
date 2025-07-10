import json
from datetime import datetime

from bson import ObjectId
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)


class EventPayloadField(EmbeddedDocument):
    """Information about an event payload field."""

    type = StringField(required=True)
    description = StringField()


class EventInfo(EmbeddedDocument):
    """Information about an event."""

    name = StringField(required=True)
    full_name = StringField(required=True)
    is_start_event = BooleanField(required=True)
    is_stop_event = BooleanField(required=True)
    payload = DictField(required=True)  # dict[str, EventPayloadField]


class InputEventInfo(EmbeddedDocument):
    """Information about an input event for a step."""

    event_names = ListField(EmbeddedDocumentField(EventInfo), required=True)
    optional = BooleanField(required=True)


class NodeData(EmbeddedDocument):
    """Data for a node in the workflow graph."""

    id = StringField(required=True)
    type = StringField(required=True)
    node_id = StringField(required=True)
    label = StringField(required=True)
    description = StringField()
    icon = StringField()
    input_events = DictField(field=EmbeddedDocumentField(InputEventInfo))  # dict[str, InputEventInfo]
    output_events = ListField(EmbeddedDocumentField(EventInfo))
    max_executions = IntField()
    stop_on_error = BooleanField()


class EdgeData(EmbeddedDocument):
    """Data for an edge in the workflow graph."""

    source = StringField(required=True)
    target = StringField(required=True)
    edge_id = IntField(required=True)
    event_name = StringField(required=True)
    event_full_name = StringField(required=True)
    is_start_event = BooleanField(required=True)
    is_stop_event = BooleanField(required=True)
    payload = DictField(required=True)  # dict[str, EventPayloadField]


class EventSpec(EmbeddedDocument):
    """Information about an event specification."""

    event_name = StringField(required=True)
    event_schema_json = StringField(required=True)  # Store as JSON string to avoid issues with $ in keys
    event_parents = ListField(StringField(), default=list)

    @property
    def event_schema(self):
        """Deserialize the event schema from JSON string to dictionary."""
        return json.loads(self.event_schema_json)

    @classmethod
    def from_dto(cls, event_dto):
        """Create an EventSpec from a DTO object."""
        return cls(
            event_name=event_dto.event_name,
            event_schema_json=json.dumps(event_dto.event_schema),
            event_parents=event_dto.event_parents,
        )


class AgentConfigEntity(EmbeddedDocument):
    agent_id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True)
    system_prompt = StringField(required=True)
    color = StringField(default="#10A37F")
    voice = StringField(default="de-DE-ChristophNeural")
    icon = StringField(default="meteor-icons:robot")


class AgentEntity(Document):
    meta = {
        "collection": "agents",
        "strict": False,
        "indexes": [{"fields": ["agent_class", "agent_id"], "unique": True}],
    }
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    agent_config = EmbeddedDocumentField(AgentConfigEntity, required=True)
    is_conversational = BooleanField(required=True)
    start_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    stop_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    network_graph = DictField(required=True)
    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @classmethod
    def create_agent(
        cls,
        agent_class: str,
        agent_id: str,
        agent_config: AgentConfigEntity,
        is_conversational: bool,
        start_events: list[EventSpec],
        stop_events: list[EventSpec],
        network_graph: dict,
        agent_entity_id: ObjectId | None = None,
    ) -> "AgentEntity":
        agent = cls(
            id=agent_entity_id or ObjectId(),
            agent_class=agent_class,
            agent_id=agent_id,
            agent_config=agent_config,
            is_conversational=is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            network_graph=network_graph,
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        agent.save()
        return agent

    @classmethod
    def create_or_update_from_dto(cls, agent_dto) -> "AgentEntity":
        """
        Creates a new AgentEntity from an AgentDTO or updates an existing one if an agent
        with the same agent_class and agent_id already exists.
        """
        # Check if an agent with the same agent_class and agent_id already exists
        existing_agent = cls.objects(agent_class=agent_dto.agent_class, agent_id=agent_dto.agent_id).first()

        agent_config = AgentConfigEntity(
            agent_id=agent_dto.agent_config.agent_id,
            name=agent_dto.agent_config.name,
            description=agent_dto.agent_config.description,
            system_prompt=agent_dto.agent_config.system_prompt,
            color=agent_dto.agent_config.color,
            voice=agent_dto.agent_config.voice,
            icon=agent_dto.agent_config.icon,
        )

        # Create EventSpec objects, serializing the schema to avoid $ issues
        start_events = [EventSpec.from_dto(event) for event in agent_dto.start_events]
        stop_events = [EventSpec.from_dto(event) for event in agent_dto.stop_events]

        network_graph = agent_dto.network_graph.model_dump()

        if existing_agent:
            # Update existing agent
            existing_agent.agent_config = agent_config
            existing_agent.is_conversational = agent_dto.is_conversational
            existing_agent.start_events = start_events
            existing_agent.stop_events = stop_events
            existing_agent.network_graph = network_graph
            existing_agent.last_discovered = datetime.now()
            existing_agent.save()
            return existing_agent
        else:
            # Create new agent
            return cls.create_agent(
                agent_class=agent_dto.agent_class,
                agent_id=agent_dto.agent_id,
                agent_config=agent_config,
                is_conversational=agent_dto.is_conversational,
                start_events=start_events,
                stop_events=stop_events,
                network_graph=network_graph,
            )

    @classmethod
    def get_agents(cls):
        return cls.objects()

    @classmethod
    def get_agent_by_id(cls, agent_entity_id: str) -> "AgentEntity":
        return cls.objects().get(id=ObjectId(agent_entity_id))

    @classmethod
    def get_agent(cls, agent_class: str, agent_id: str) -> "AgentEntity":
        return cls.objects().get(agent_class=agent_class, agent_id=agent_id)
