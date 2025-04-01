import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from aihub_lib.infrastructure.BotConfig import BotConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.NatsConfig import NatsConfig
from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator[None, Any]:
    logging.warning("Initializing NATS connection and resources")

    nc = NATS()

    # Connect to MongoDB via Cosmos
    connect(
        db=BotConfig().BOT_DB_NAME,
        host=CosmosAccess().get_connection_string(),
    )

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()
        external_event_distributor = ExternalEventDistributor(nc=nc, js=js)

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.external_event_distributor = external_event_distributor

        # Yield control back to FastAPI to start serving requests
        yield

        # Cleanup on exit
        logging.warning("Shutting down NATS connection and resources")

    finally:
        # Close NATS connection on exit
        await nc.close()
