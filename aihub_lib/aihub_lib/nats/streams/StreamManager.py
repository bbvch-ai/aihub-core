import logging

from nats.js import JetStreamContext, api
from nats.js.errors import NotFoundError

logger = logging.getLogger(__name__)


class StreamManager:
    """
    A helper class for ensuring that required NATS JetStream streams exist before use.

    ### Why This Class Exists
    In a system that relies on JetStream for event persistence and replay, you often need to
    guarantee that streams are properly set up with the correct subjects, storage, and retention
    policies. Doing this check dynamically at runtime avoids manual setup steps and reduces the
    likelihood of runtime errors due to missing streams.

    ### Usage
    If a consumer or publisher expects events to be written to or read from a particular stream,
    `StreamManager` can verify that the stream and its configuration exist, creating them if they
    do not. This makes your infrastructure more self-healing and reduces operational overhead.

    ### Example
    The `ensure_agent_stream_exists` method is commonly called before subscribing to agent events,
    ensuring that the underlying stream is ready.
    """

    def __init__(self, js: JetStreamContext, stream_name: str, stream_subject: str):
        self.js = js
        self.stream_name = stream_name
        self.stream_subject = stream_subject

    async def ensure_stream_exists(self, stream_name: str, subject: str):
        """
        Checks if a JetStream stream with the given name exists.
        If not found, it creates it with the specified subject, file storage,
        and default retention policies.

        This should be called once during initialization, ensuring that producers
        or consumers can safely interact with the stream without prior manual setup.
        """
        try:
            await self.js.stream_info(stream_name)
            # Stream already exists
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
        """
        Ensures that the agent-specific stream—identified by this manager's
        stream_name and stream_subject—is created and ready for use.
        """
        return await self.ensure_stream_exists(stream_name=self.stream_name, subject=self.stream_subject)

    def __repr__(self):
        return f"JSManager(stream_name={self.stream_name}, stream_subject={self.stream_subject})"
