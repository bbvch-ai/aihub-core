import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import boto3
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.langfuse.LangfuseProvisioner import LangfuseProvisioner
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.persistence.access.AccessChangeHook import AccessChangeHook
from botocore.config import Config
from fastapi import FastAPI
from mongoengine import connect, disconnect
from pymilvus import MilvusClient

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler
from aihub_api.persistance.events.EventPersister import EventPersister
from aihub_api.routes.agent.AgentFileUploadService import AgentFileUploadService
from aihub_api.rpc.AgentConfigResponder import AgentConfigResponder
from aihub_api.rpc.ProcessConfigResponder import ProcessConfigResponder
from aihub_api.runners.lifetime.initialize_db import (
    initialize_default_tenant,
    initialize_knowledge_buckets,
    initialize_roles,
)
from aihub_api.services.AgentEndpointsDiscoveryService import AgentEndpointsDiscoveryService
from aihub_api.services.ProcessEndpointsDiscoveryService import ProcessEndpointsDiscoveryService
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager
from aihub_api.sockets.sender.WebSocketSender import WebSocketSender

logger = logging.getLogger(__name__)


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
       Stores references to these resources (`nc`, `js`, `ws_manager`, `ws_sender`, `external_agent_event_distributor`)
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

    print(AIHubSettings().startup_banner)
    logging.info("Initializing NATS connection and resources")

    # Connect to MongoDB via Cosmos
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )

    # Connect to Redis
    redis = RedisSettings.create_client()

    # Connect to Milvus
    milvus_settings = MilvusSettings()
    milvus_client = MilvusClient(uri=milvus_settings.URL, token=milvus_settings.get_token())

    # Connect to S3 (SeaweedFS)
    s3_settings = S3StorageSettings()
    s3_client = boto3.client(
        "s3",
        endpoint_url=s3_settings.ENDPOINT,
        aws_access_key_id=s3_settings.ACCESS_KEY,
        aws_secret_access_key=s3_settings.SECRET_KEY.get_secret_value(),
        region_name=s3_settings.REGION,
        config=Config(signature_version="s3v4"),
    )
    # Public client for generating presigned URLs accessible from browsers
    s3_public_client = boto3.client(
        "s3",
        endpoint_url=s3_settings.get_public_endpoint(),
        aws_access_key_id=s3_settings.ACCESS_KEY,
        aws_secret_access_key=s3_settings.SECRET_KEY.get_secret_value(),
        region_name=s3_settings.REGION,
        config=Config(signature_version="s3v4"),
    )

    try:
        # Connect to NATS and setup JetStream
        nc = await NatsSettings.create_client()
        js = nc.jetstream()

        # Persist all events
        persister = EventPersister("default")

        agent_topic_manager = AgentTopicManager()
        agent_event_persist_subscriber = AgentNCSubscriber.for_all_agent_events(
            nc=nc,
            topic_manager=agent_topic_manager,
            handler=persister.persist_agent_event,
            subscriber_name="AgentEventPersister",
        )
        await agent_event_persist_subscriber.start()

        process_topic_manager = ProcessTopicManager()
        process_event_persist_subscriber = ProcessNCSubscriber.for_all_process_events(
            nc=nc,
            topic_manager=process_topic_manager,
            handler=persister.persist_process_event,
            subscriber_name="ProcessEventPersister",
        )
        await process_event_persist_subscriber.start()

        # Setup WebSocket event flow
        ws_manager = WebSocketManager()
        ws_sender = WebSocketSender(ws_manager=ws_manager)
        ws_subscriber = AgentNCSubscriber.for_all_agents_display_events(
            nc=nc, topic_manager=agent_topic_manager, handler=ws_sender.send_event, subscriber_name="WebSockets"
        )
        await ws_subscriber.start()

        external_agent_event_distributor = ExternalAgentEventDistributor(
            nc=nc, js=js, name="AgentExternalAgentEventDistributor"
        )
        external_process_event_distributor = ExternalProcessEventDistributor(nc=nc, js=js)

        # Setup RPC responders for config fetching
        agent_config_responder = AgentConfigResponder(nc=nc)
        await agent_config_responder.start()

        process_config_responder = ProcessConfigResponder(nc=nc)
        await process_config_responder.start()

        # Store resources in app state
        app.state.nc = nc
        app.state.js = js
        app.state.redis = redis
        app.state.milvus_client = milvus_client
        app.state.s3_client = s3_client
        app.state.s3_public_client = s3_public_client
        app.state.s3_settings = s3_settings
        agent_file_upload_service = AgentFileUploadService(
            s3_client=s3_client,
            s3_public_client=s3_public_client,
        )
        agent_file_upload_service.ensure_bucket_exists()
        app.state.agent_file_upload_service = agent_file_upload_service
        app.state.ws_manager = ws_manager
        app.state.ws_sender = ws_sender
        app.state.external_agent_event_distributor = external_agent_event_distributor
        app.state.external_process_event_distributor = external_process_event_distributor
        app.state.agent_config_responder = agent_config_responder
        app.state.process_config_responder = process_config_responder

        api_app = app.state.api_app

        if hasattr(api_app.state, "agent_controller"):
            agent_discovery_service = AgentEndpointsDiscoveryService(
                nc=nc,
                api_app=api_app,
                controller=api_app.state.agent_controller,
                locale_handler=ApiLocaleHandler(),
                redis=redis,
                discovery_interval=60,  # Check for new agents every 60 seconds
            )
            await agent_discovery_service.start()
            app.state.agent_discovery_service = agent_discovery_service
        else:
            logger.warning("Unable to start AgentEndpointsDiscoveryService due to missing state.agent_controller")

        if hasattr(api_app.state, "process_controller"):
            process_discovery_service = ProcessEndpointsDiscoveryService(
                nc=nc,
                api_app=api_app,
                controller=api_app.state.process_controller,
                locale_handler=ApiLocaleHandler(),
                discovery_interval=60,  # Check for new process every 60 seconds
            )
            await process_discovery_service.start()
            app.state.process_discovery_service = process_discovery_service
        else:
            logger.warning("Unable to start ProcessEndpointsDiscoveryService due to missing state.process_controller")

        await initialize_default_tenant()
        await initialize_roles()
        await initialize_knowledge_buckets()

        # Provision Langfuse with AI-Hub LLM connections
        await LangfuseProvisioner().provision()

        # Provision OpenWebUI with groups, workspace models, and access grants
        OpenWebuiProvisioner.initialize(redis)
        await OpenWebuiProvisioner().provision()

        # Re-sync OpenWebUI groups when a user switches active tenant
        def _on_tenant_switch() -> None:
            asyncio.create_task(OpenWebuiProvisioner().sync_access())

        AuthHandler.register_active_tenant_hook(_on_tenant_switch)

        # Re-sync OpenWebUI when roles, tenants, or user-role assignments change
        AccessChangeHook.connect()

        # Yield control back to FastAPI to start serving requests
        yield

        # Shutdown: stop subscribers
        await agent_event_persist_subscriber.stop()
        await process_event_persist_subscriber.stop()
        await ws_subscriber.stop()

        # Stop RPC responders
        if hasattr(app.state, "agent_config_responder"):
            await app.state.agent_config_responder.stop()
        if hasattr(app.state, "process_config_responder"):
            await app.state.process_config_responder.stop()

        # Stop the discovery services
        if hasattr(app.state, "agent_discovery_service"):
            await app.state.agent_discovery_service.stop()

        if hasattr(app.state, "process_discovery_service"):
            await app.state.process_discovery_service.stop()

        disconnect()

        # Close Redis connection
        await redis.aclose()

        # Close Milvus connection
        milvus_client.close()

        # Close S3 connections
        s3_client.close()
        s3_public_client.close()

    finally:
        # Close NATS connection on exit
        await nc.close()
