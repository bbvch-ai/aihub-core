import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mongoengine import connect, disconnect
from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings
from swiss_ai_hub.core.infrastructure.nats.NatsSettings import NatsSettings
from swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager

from swiss_ai_hub.bot.persistence.entities.ConversationEntity import ConversationEntity
from swiss_ai_hub.bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> AsyncGenerator:
    print(AIHubSettings().startup_banner)
    logging.info("Initializing NATS connection and resources")

    # Connect to MongoDB via Cosmos
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )

    # Configure TTL index after connection is established
    if hasattr(app.state, "conversation_ttl_days"):
        conversation_ttl_days = app.state.conversation_ttl_days
        logging.info(f"Configuring TTL index with {conversation_ttl_days} days")
        ConversationEntity.update_ttl_index(conversation_ttl_days)

    try:
        # Connect to NATS and setup JetStream
        nc = await NatsSettings.create_client()
        js = nc.jetstream()

        topic_manager = AgentTopicManager()

        # Setup Bot In The Loop subscriber
        bot_in_the_loop_handler = BotInTheLoopHandler()
        bot_in_the_loop_subscriber = AgentNCSubscriber.for_all_agent_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=bot_in_the_loop_handler.handle_event,
            subscriber_name="BotInTheLoop",
        )
        await bot_in_the_loop_subscriber.start()

        external_agent_event_distributor = ExternalAgentEventDistributor(
            nc=nc, js=js, name="BotExternalAgentEventDistributor"
        )

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.bot_in_the_loop_handler = bot_in_the_loop_handler
        app.state.external_agent_event_distributor = external_agent_event_distributor

        # Yield control back to FastAPI to start serving requests
        yield

        # Shutdown: stop subscribers
        await bot_in_the_loop_subscriber.stop()
        disconnect()

    finally:
        # Close NATS connection on exit
        await nc.close()
