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
    """

    def __init__(self, js: JetStreamContext, stream_name: str, stream_subject: str):
        self.js = js
        self.stream_name = stream_name
        self.stream_subject = stream_subject

    async def ensure_stream_exists(self):
        """
        Checks if a JetStream stream with the given name exists.
        If not found, it creates it with the specified subject, file storage,
        and default retention policies.

        This should be called once during initialization, ensuring that producers
        or consumers can safely interact with the stream without prior manual setup.
        """
        try:
            await self.js.stream_info(self.stream_name)
            # Stream already exists
        except NotFoundError:
            # Stream does not exist; create it
            logger.debug(f"Creating stream '{self.stream_name}' with subject '{self.stream_subject}'")
            await self.js.add_stream(
                config=api.StreamConfig(
                    name=self.stream_name,
                    subjects=[self.stream_subject],
                    storage=api.StorageType.FILE,
                    retention=api.RetentionPolicy.LIMITS,
                    max_msgs=10_000_000,
                    discard=api.DiscardPolicy.OLD,
                    max_age=60 * 60 * 24 * 30,
                    duplicate_window=60 * 1,
                )
            )

    def __repr__(self):
        return f"JSManager(stream_name={self.stream_name}, stream_subject={self.stream_subject})"
