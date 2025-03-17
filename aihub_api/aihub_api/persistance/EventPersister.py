from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from bson import ObjectId


class EventPersister:
    """
    A utility class for persisting events received from NATS/JetStream into a MongoDB database.

    ### Why EventPersister?
    In an event-driven architecture, it's often necessary to retain a historical log of events for
    auditing, analytics, or debugging. `EventPersister` encapsulates the logic of converting raw
    event data and associated topic details into a stored entity, ensuring a clean separation of
    concerns between event handling and data persistence.

    ### Features
    - Converts `BaseEvent` and associated `AgentTopic` metadata into a `PersistedEventEntity`.
    - Assigns a unique MongoDB ObjectId, populates agent and run details, and stores a fully serializable
      JSON snapshot of the event.

    ### Usage
    Integrated with event subscribers (e.g., JSSubscriber or NCSubscriber), the `persist_event` method
    is called whenever a relevant event arrives, saving a permanent record of that event.

    """

    def __init__(self, db: str):
        """Initialize the persister with a given database name."""
        self.db = db

    async def persist_event(self, event: BaseEvent, topic: AgentTopic) -> None:
        """Persist the given event along with its topic metadata into MongoDB."""
        PersistedEventEntity.persist_event(event, topic, self.db)
