from swiss_ai_hub.core.nats.events.BaseEvent import BaseEvent
from swiss_ai_hub.core.nats.topics import ProcessInstanceTopic
from swiss_ai_hub.core.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.PersistedProcessEventEntity import PersistedProcessEventEntity


class EventPersister:
    """
    A utility class for persisting events received from NATS/JetStream into a MongoDB database.
    In an event-driven architecture, it's often necessary to retain a historical log of events for
    auditing, analytics, or debugging. `EventPersister` encapsulates the logic of converting raw
    event data and associated topic details into a stored entity, ensuring a clean separation of
    concerns between event handling and data persistence.
    """

    def __init__(self, db: str):
        """Initialize the persister with a given database name."""
        self.db = db

    async def persist_agent_event(self, event: BaseEvent, topic: AgentInstanceTopic) -> None:
        """Persist the given agent event along with its topic metadata into MongoDB."""
        PersistedAgentEventEntity.persist_event(event, topic, self.db)

    async def persist_process_event(self, event: BaseEvent, topic: ProcessInstanceTopic) -> None:
        """Persist the given process event along with its topic metadata into MongoDB."""
        PersistedProcessEventEntity.persist_event(event, topic, self.db)
