import logging
from typing import Annotated

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

    def __init__(
        self,
        js: JetStreamContext,
        stream_name: str,
        stream_subject: str,
        extra_subjects: Annotated[list[str] | None, "Further subjects the stream must cover"] = None,
        allow_msg_schedules: Annotated[
            bool, "Whether messages may be scheduled for later delivery (NATS 2.12+)"
        ] = False,
        allow_msg_ttl: Annotated[bool, "Whether a message may carry its own time to live (NATS 2.11+)"] = False,
    ):
        self.js = js
        self.stream_name = stream_name
        self.stream_subject = stream_subject
        self.extra_subjects = extra_subjects or []
        self.allow_msg_schedules = allow_msg_schedules
        self.allow_msg_ttl = allow_msg_ttl

    async def ensure_stream_exists(self):
        """
        Creates the stream with file storage and the default retention policies when it is missing, and adds the
        subjects and the scheduling and TTL flags this manager asks for to a stream that exists without them.

        Several services create the same stream, and the first one wins, so a stream created without the extras is
        brought up to date by whichever caller asks for them. Nothing is ever removed: enabling message schedules or
        TTLs cannot be undone on the server.
        """
        try:
            stream = await self.js.stream_info(self.stream_name)
        except NotFoundError:
            logger.debug(f"Creating stream '{self.stream_name}' with subject '{self.stream_subject}'")
            await self.js.add_stream(
                config=api.StreamConfig(
                    name=self.stream_name,
                    subjects=[self.stream_subject, *self.extra_subjects],
                    storage=api.StorageType.FILE,
                    retention=api.RetentionPolicy.LIMITS,
                    max_msgs=10_000_000,
                    discard=api.DiscardPolicy.OLD,
                    max_age=60 * 60 * 24 * 30,
                    duplicate_window=60 * 1,
                    allow_msg_schedules=self.allow_msg_schedules or None,
                    allow_msg_ttl=self.allow_msg_ttl or None,
                )
            )
            return
        await self._add_missing(stream.config)

    async def _add_missing(self, config: api.StreamConfig) -> None:
        subjects = list(config.subjects or [])
        missing_subjects = [subject for subject in self.extra_subjects if subject not in subjects]
        missing_schedules = self.allow_msg_schedules and not config.allow_msg_schedules
        missing_ttl = self.allow_msg_ttl and not config.allow_msg_ttl
        if not missing_subjects and not missing_schedules and not missing_ttl:
            return
        logger.info(
            f"Updating stream '{self.stream_name}': adding subjects {missing_subjects}, "
            f"message schedules {'on' if missing_schedules else 'unchanged'}"
        )
        config.subjects = [*subjects, *missing_subjects]
        if missing_schedules:
            config.allow_msg_schedules = True
        if missing_ttl:
            config.allow_msg_ttl = True
        await self.js.update_stream(config)

    def __repr__(self):
        return f"JSManager(stream_name={self.stream_name}, stream_subject={self.stream_subject})"
