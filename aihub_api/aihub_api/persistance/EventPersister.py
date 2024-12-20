from bson import ObjectId

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity


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
        """
        Initialize the persister with a given database name.

        :param db: Name of the MongoDB database to store events.
        """
        self.db = db

    async def persist_event(self, event: BaseEvent, topic: AgentTopic) -> None:
        """
        Persist the given event along with its topic metadata into MongoDB.

        :param event: The event object to persist.
        :param topic: The parsed topic metadata (agent_class, agent_id, thread_id, etc.).
        """
        persisted_entity = PersistedEventEntity(
            id=ObjectId(),
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            event_id=event.event_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_data=event.model_dump(),
        )
        persisted_entity.switch_db(self.db)
        persisted_entity.save()
