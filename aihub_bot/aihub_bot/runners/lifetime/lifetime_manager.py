import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator[None, Any]:
    logging.warning("Initializing NATS connection and resources")

    nc = NATS()

    # Connect to MongoDB via Cosmos
    connect(
        db="aihub_bot",
        host=CosmosAccess().get_connection_string(),
    )

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()
        ws_receiver = WebSocketReceiver(js=js)

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.ws_receiver = ws_receiver

        # Yield control back to FastAPI to start serving requests
        yield

        # Cleanup on exit
        logging.warning("Shutting down NATS connection and resources")

    finally:
        # Close NATS connection on exit
        await nc.close()
