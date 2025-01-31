import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS

from aihub_bots.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator[None, Any]:
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
