from contextlib import asynccontextmanager

from fastapi import FastAPI
from mongoengine import connect
from nats.aio.client import Client as NATS

from api_core.persistance.EventPersister import EventPersister
from api_core.sockets.manager.WebSocketManager import WebSocketManager
from api_core.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from api_core.sockets.sender.WebSocketSender import WebSocketSender
from lib_core.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from lib_core.nats.subscribers.JSSubscriber import JSSubscriber
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.TopicManager import TopicManager


@asynccontextmanager
async def lifetime_manager(app: FastAPI) -> None:
    nc = NATS()
    connect(
        db="aihub",
        host=CosmosAccess().get_connection_string(),
        alias="aihub",
    )
    try:
        await nc.connect(servers=["nats://localhost:4222"])
        js = nc.jetstream()

        topic_manager = TopicManager()
        persister = EventPersister("aihub")
        persist_subscriber = JSSubscriber.for_all_agent_events(
            nc=nc,
            js=js,
            topic_manager=topic_manager,
            handler=persister.persist_event,
            ack_on_fail=False,
        )
        await persist_subscriber.start()

        ws_manager = WebSocketManager()
        ws_sender = WebSocketSender(ws_manager=ws_manager)
        ws_subscriber = NCSubscriber.all_for_agent_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=ws_sender.send_event,
        )
        await ws_subscriber.start()

        ws_receiver = WebSocketReceiver(js=js)

        app.state.nc = nc
        app.state.js = js
        app.state.ws_manager = ws_manager
        app.state.ws_sender = ws_sender
        app.state.ws_receiver = ws_receiver
        yield
        await persist_subscriber.stop()
        await ws_subscriber.stop()
    finally:
        await nc.close()