import logging

from nats.js import JetStreamContext
from nats.js import api

from nats.js.errors import NotFoundError

logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(self, js: JetStreamContext, stream_name: str, stream_subject: str):
        self.js = js
        self.stream_name = stream_name
        self.stream_subject = stream_subject

    async def ensure_stream_exists(self, stream_name: str, subject: str):
        try:
            await self.js.stream_info(stream_name)
            # Stream exists
        except NotFoundError:
            # Stream does not exist; create it
            logger.debug(f"Creating stream '{stream_name}' with subject '{subject}'")
            await self.js.add_stream(
                config=api.StreamConfig(
                    name=stream_name,
                    subjects=[subject],
                    storage=api.StorageType.FILE,
                    retention=api.RetentionPolicy.LIMITS,
                )
            )

    async def ensure_agent_stream_exists(self):
        return await self.ensure_stream_exists(stream_name=self.stream_name, subject=self.stream_subject)

    def __repr__(self):
        return f"JSManager(stream_name={self.stream_name}, stream_subject={self.stream_subject})"
