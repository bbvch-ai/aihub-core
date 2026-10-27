import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.inbox_position import InboxPosition

logger = logging.getLogger(__name__)

_KEY_PREFIX = "mailbox:inbox_watermark"
_MAILBOX_FIELD = "mailbox"
_UID_VALIDITY_FIELD = "uid_validity"
_UID_FIELD = "uid"


class InboxWatermark:
    """Remembers how far into a profile's inbox the classifier has read, for the mail it leaves there.

    Moving a message out of the inbox is what normally stops the next run from classifying it again. Mail kept in the
    inbox needs another record, and the mailbox cannot carry it: Microsoft 365 accepts no custom IMAP keyword, and every
    flag it does accept (`\\Answered`, `\\Flagged`, `$MDNSent`, …) means something to the person reading the mail. The
    record is therefore the highest UID a run has classified, kept here next to `MailboxRunLease`.

    It is stored with the mailbox it describes, so a profile repointed at another account or inbox starts from nothing
    rather than skipping that mailbox's mail. Losing the key costs one more classification of the mail kept in the
    inbox; it never skips a message.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def read(self, agent_class: str, agent_id: str, imap_config: ImapClientConfig) -> InboxPosition | None:
        """The position the last run reached in this mailbox, or None when there is none for it."""
        stored = await self._redis.hgetall(self._key(agent_class, agent_id))
        fields = {self._text(name): self._text(value) for name, value in stored.items()}
        if fields.get(_MAILBOX_FIELD) != self._mailbox(imap_config):
            if fields:
                logger.info("[watermark] %s/%s points at another mailbox — starting over", agent_class, agent_id)
            return None
        return InboxPosition(uid_validity=int(fields[_UID_VALIDITY_FIELD]), uid=int(fields[_UID_FIELD]))

    async def advance(
        self, agent_class: str, agent_id: str, imap_config: ImapClientConfig, position: InboxPosition
    ) -> None:
        """Record that every unread message up to ``position`` has been classified."""
        await self._redis.hset(
            self._key(agent_class, agent_id),
            mapping={
                _MAILBOX_FIELD: self._mailbox(imap_config),
                _UID_VALIDITY_FIELD: position.uid_validity,
                _UID_FIELD: position.uid,
            },
        )
        logger.info(
            "[watermark] %s/%s advanced to uid %s (UIDVALIDITY %s)",
            agent_class,
            agent_id,
            position.uid,
            position.uid_validity,
        )

    @staticmethod
    def _mailbox(imap_config: ImapClientConfig) -> str:
        return f"{imap_config.username}@{imap_config.host}:{imap_config.port}/{imap_config.inbox_folder}"

    @staticmethod
    def _text(value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

    @staticmethod
    def _key(agent_class: str, agent_id: str) -> str:
        """Deliberately outside the run_context_*/thread_context_* namespaces `BaseContext.delete_all` clears."""
        return f"{_KEY_PREFIX}:{agent_class}:{agent_id}"
