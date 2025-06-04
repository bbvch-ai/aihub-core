import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from fastapi import FastAPI
from mongoengine import connect, disconnect
from nats.aio.client import Client as NATS

from aihub_bot.persistence.entities.ConversationEntity import ConversationEntity
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator:
    logging.warning("Initializing NATS connection and resources")

    nc = NATS()

    # Connect to MongoDB via Cosmos
    connect(
        db=ApiConfig().DB_NAME,
        host=CosmosAccess().get_connection_string(),
    )

    # Configure TTL index after connection is established
    if hasattr(app.state, "conversation_ttl_days"):
        conversation_ttl_days = app.state.conversation_ttl_days
        logging.info(f"Configuring TTL index with {conversation_ttl_days} days")
        ConversationEntity.update_ttl_index(conversation_ttl_days)

    try:
        # Connect to NATS and setup JetStream
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()

        topic_manager = AgentTopicManager()

        # Setup Bot In The Loop subscriber
        bot_in_the_loop_handler = BotInTheLoopHandler()
        bot_in_the_loop_subscriber = NCSubscriber.for_all_agent_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=bot_in_the_loop_handler.handle_event,
        )
        await bot_in_the_loop_subscriber.start()

        external_event_distributor = ExternalAgentEventDistributor(nc=nc, js=js)

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.bot_in_the_loop_handler = bot_in_the_loop_handler
        app.state.external_event_distributor = external_event_distributor

        # Yield control back to FastAPI to start serving requests
        yield

        # Shutdown: stop subscribers
        await bot_in_the_loop_subscriber.stop()
        disconnect()

    finally:
        # Close NATS connection on exit
        await nc.close()
