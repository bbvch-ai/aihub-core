"""Taking a value out of a context reads and removes it in one Redis command, so two readers never both get it."""

from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.core.context.base_context import BaseContext


@pytest.mark.asyncio
async def test_pop_reads_and_removes_the_value_in_one_command():
    redis = AsyncMock()
    redis.getdel.return_value = b'{"name": "run_command"}'

    value = await BaseContext(redis, "run_context_t_r").pop("pending")

    assert value == {"name": "run_command"}
    redis.getdel.assert_awaited_once_with("run_context_t_r:pending")


@pytest.mark.asyncio
async def test_pop_of_a_missing_key_returns_the_default():
    redis = AsyncMock()
    redis.getdel.return_value = None

    assert await BaseContext(redis, "run_context_t_r").pop("pending", "nothing") == "nothing"
