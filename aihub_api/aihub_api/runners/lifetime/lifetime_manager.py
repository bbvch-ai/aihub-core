import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS

from aihub_api.persistance.EventPersister import EventPersister
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager
from aihub_api.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from aihub_api.sockets.sender.WebSocketSender import WebSocketSender
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.TopicManager import TopicManager


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> None:
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
       Initializes a `WebSocketManager`, `WebSocketSender`, and `WebSocketReceiver`.
       Then subscribes to display events via `NCSubscriber` and sends them to connected websockets.
    5. **App State Initialization:**
       Stores references to these resources (`nc`, `js`, `ws_manager`, `ws_sender`, `ws_receiver`) in `app.state`,
       making them accessible throughout the app.
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

    logging.warning("Initializing NATS connection and resources")

    nc = NATS()

    # Connect to MongoDB via Cosmos
    connect(
        db="aihub",
        host=CosmosAccess().get_connection_string(),
    )

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()

        topic_manager = TopicManager()

        # Persist all agent events
        persister = EventPersister("default")
        persist_subscriber = JSSubscriber.for_all_agent_events(
            nc=nc,
            js=js,
            topic_manager=topic_manager,
            handler=persister.persist_event,
            ack_on_fail=False,
        )
        await persist_subscriber.start()

        # Setup WebSocket event flow
        ws_manager = WebSocketManager()
        ws_sender = WebSocketSender(ws_manager=ws_manager)
        ws_subscriber = NCSubscriber.all_for_agent_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=ws_sender.send_event,
        )
        await ws_subscriber.start()

        ws_receiver = WebSocketReceiver(js=js)

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.ws_manager = ws_manager
        app.state.ws_sender = ws_sender
        app.state.ws_receiver = ws_receiver

        # Yield control back to FastAPI to start serving requests
        yield

        # Shutdown: stop subscribers
        await persist_subscriber.stop()
        await ws_subscriber.stop()

    finally:
        # Close NATS connection on exit
        await nc.close()
