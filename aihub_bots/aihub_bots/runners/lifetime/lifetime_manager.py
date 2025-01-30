import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS

from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator[None, Any]:
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
        db="aihub_bots",
        host=CosmosAccess().get_connection_string(),
    )

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=["nats://localhost:4222"])
        js = nc.jetstream()

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js

        # Yield control back to FastAPI to start serving requests
        yield

        # Cleanup on exit
        logging.warning("Shutting down NATS connection and resources")

    finally:
        # Close NATS connection on exit
        await nc.close()
