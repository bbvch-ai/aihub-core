"""An agent asking which profiles it may offer as tools gets every online profile, and no offline one."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.rpc.callable_agents_responder import CallableAgentsResponder

MODULE = "swiss_ai_hub.api.rpc.callable_agents_responder"
NOW = datetime(2026, 11, 27, 12, 0)


def _class(agent_class: str, online: bool, conversational: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        agent_class=agent_class,
        is_conversational=conversational,
        start_events=[],
        is_online_since=lambda threshold: online,
    )


def _profile(agent_id: str) -> SimpleNamespace:
    return SimpleNamespace(agent_id=agent_id, name=LocaleString(en=agent_id), description=LocaleString(en="d"))


@pytest.mark.asyncio
async def test_every_online_profile_is_listed_and_offline_ones_are_not():
    classes = [_class("RAGAgent", online=True), _class("FewShotAgent", online=False)]
    profiles = {"RAGAgent": [_profile("law"), _profile("hr")], "FewShotAgent": [_profile("faq")]}

    with (
        patch(f"{MODULE}.AgentClassEntity.online_threshold", AsyncMock(return_value=NOW - timedelta(minutes=5))),
        patch(f"{MODULE}.AgentClassEntity.get_all", AsyncMock(return_value=classes)),
        patch(
            f"{MODULE}.AgentConfigEntityDocument.find_for_name",
            AsyncMock(side_effect=lambda agent_class: profiles[agent_class]),
        ),
    ):
        agents = await CallableAgentsResponder.online_agents()

    assert [(agent.agent_class, agent.agent_id) for agent in agents] == [("RAGAgent", "law"), ("RAGAgent", "hr")]
    assert all(agent.is_conversational for agent in agents)
