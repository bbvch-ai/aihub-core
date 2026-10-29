"""Exercised against the real Valkey the rest of the agent suite already needs, like `MailboxRunLease`."""

from uuid import uuid4

from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.infrastructure import RedisSettings
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.inbox_position import InboxPosition
from swiss_ai_hub.agent.imap.inbox_watermark import InboxWatermark

_AGENT_CLASS = "EmailClassificationAgent"


def _agent_id() -> str:
    """A fresh profile per test, so tests never contend for the same key."""
    return f"mailbox-{uuid4().hex}"


def _imap(username: str = "pocus@example.ch", inbox_folder: str = "INBOX") -> ImapClientConfig:
    return ImapClientConfig(host="imap.example.ch", username=username, password="secret", inbox_folder=inbox_folder)


async def _cleanup(redis, agent_id: str) -> None:
    await redis.delete(f"mailbox:inbox_watermark:{_AGENT_CLASS}:{agent_id}")
    await redis.aclose()


@async_test
async def test_a_profile_that_never_ran_has_no_position():
    redis, agent_id = RedisSettings.create_client(), _agent_id()
    try:
        assert await InboxWatermark(redis).read(_AGENT_CLASS, agent_id, _imap()) is None
    finally:
        await _cleanup(redis, agent_id)


@async_test
async def test_an_advanced_position_is_read_back():
    redis, agent_id = RedisSettings.create_client(), _agent_id()
    try:
        watermark = InboxWatermark(redis)
        await watermark.advance(_AGENT_CLASS, agent_id, _imap(), InboxPosition(uid_validity=7, uid=41))
        await watermark.advance(_AGENT_CLASS, agent_id, _imap(), InboxPosition(uid_validity=7, uid=58))

        assert await watermark.read(_AGENT_CLASS, agent_id, _imap()) == InboxPosition(uid_validity=7, uid=58)
    finally:
        await _cleanup(redis, agent_id)


@async_test
async def test_a_profile_repointed_at_another_mailbox_starts_over():
    """The old mailbox's UIDs say nothing about the new one; reusing them would skip its mail."""
    redis, agent_id = RedisSettings.create_client(), _agent_id()
    try:
        watermark = InboxWatermark(redis)
        await watermark.advance(_AGENT_CLASS, agent_id, _imap(), InboxPosition(uid_validity=7, uid=41))

        assert await watermark.read(_AGENT_CLASS, agent_id, _imap(username="other@example.ch")) is None
        assert await watermark.read(_AGENT_CLASS, agent_id, _imap(inbox_folder="Shared")) is None
    finally:
        await _cleanup(redis, agent_id)
