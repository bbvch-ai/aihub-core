import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from fastapi import FastAPI
from mongoengine import connect, disconnect
from nats.aio.client import Client as NATS

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler
from aihub_api.persistance.events.EventPersister import EventPersister
from aihub_api.services.AgentEndpointsDiscoveryService import AgentEndpointsDiscoveryService
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager
from aihub_api.sockets.sender.WebSocketSender import WebSocketSender


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator:
    """
    Manages the lifecycle of critical application resources, including NATS connections, JetStream context,
    database connections, and event consumers.

    ### Why Use a Lifetime Manager?
    By leveraging FastAPI's lifespan context, we can:
    - Initialize NATS connections and JetStream before the application starts serving requests.
    - Set up database connections (e.g., MongoEngine with Cosmos).
    - Start subscribers that persist and route events to websockets.
    - Ensure orderly shutdown: stop subscribers and close NATS connections when the app stops.

    ### What Happens Here
    1. **NATS & JetStream Setup:**
       Connects to a NATS server and creates a JetStream context (`js`).
    2. **Database Connection:**
       Connects to MongoDB/Cosmos via `MongoEngine` for event persistence.
    3. **Event Persistence Subscriber:**
       Sets up a `JSSubscriber` that listens to all agent events, using `EventPersister` to store them.
    4. **WebSocket Setup:**
       Initializes a `WebSocketManager`, `WebSocketSender`, and `ExternalAgentEventDistributor`.
       Then subscribes to display events via `NCSubscriber` and sends them to connected websockets.
    5. **App State Initialization:**
       Stores references to these resources (`nc`, `js`, `ws_manager`, `ws_sender`, `external_event_distributor`)
       in `app.state`, making them accessible throughout the app.
    6. **Cleanup on Exit:**
       On shutdown, it stops the subscribers and closes the NATS connection.

    This lifecycle manager ensures that the application has all dependencies ready at startup and cleans up
    gracefully on shutdown, improving reliability and maintainability.

    ### Example
    ```python
    app = FastAPI(lifespan=lifetime_manager)
    ```

    When `app` starts, this manager runs and sets up everything. When `app` stops, it tears down resources.
    """

    logging.info("Initializing NATS connection and resources")

    nc = NATS()

    # Connect to MongoDB via Cosmos
    connect(
        db=ApiConfig().DB_NAME,
        host=CosmosAccess().get_connection_string(),
    )

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()

        # Persist all events
        persister = EventPersister("default")

        agent_topic_manager = AgentTopicManager()
        agent_event_persist_subscriber = AgentNCSubscriber.for_all_agent_events(
            nc=nc, topic_manager=agent_topic_manager, handler=persister.persist_agent_event
        )
        await agent_event_persist_subscriber.start()

        process_topic_manager = ProcessTopicManager()
        process_event_persist_subscriber = ProcessNCSubscriber.for_all_process_events(
            nc=nc, topic_manager=process_topic_manager, handler=persister.persist_process_event
        )
        await process_event_persist_subscriber.start()

        # Setup WebSocket event flow
        ws_manager = WebSocketManager()
        ws_sender = WebSocketSender(ws_manager=ws_manager)
        ws_subscriber = AgentNCSubscriber.for_all_agents_display_events(
            nc=nc,
            topic_manager=agent_topic_manager,
            handler=ws_sender.send_event,
        )
        await ws_subscriber.start()

        external_event_distributor = ExternalAgentEventDistributor(nc=nc, js=js)

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.ws_manager = ws_manager
        app.state.ws_sender = ws_sender
        app.state.external_event_distributor = external_event_distributor

        # Create and start the agent discovery service
        api_app = app.state.api_app
        if hasattr(api_app.state, "agent_controller"):
            agent_discovery_service = AgentEndpointsDiscoveryService(
                nc=nc,
                api_app=api_app,
                agent_controller=api_app.state.agent_controller,
                locale_handler=ApiLocaleHandler(),
                discovery_interval=60,  # Check for new agents every 60 seconds
            )
            await agent_discovery_service.start()
            app.state.agent_discovery_service = agent_discovery_service

        # Yield control back to FastAPI to start serving requests
        yield

        # Shutdown: stop subscribers
        await agent_event_persist_subscriber.stop()
        await process_event_persist_subscriber.stop()
        await ws_subscriber.stop()

        if hasattr(app.state, "agent_discovery_service"):
            # Stop the discovery service
            await app.state.agent_discovery_service.stop()

        disconnect()

    finally:
        # Close NATS connection on exit
        await nc.close()
