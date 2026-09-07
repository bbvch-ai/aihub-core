"""A step may not require a parameter the dispatcher fills from `RunContext`, because it might not be there.

`AgentDispatcher._build_method_kwargs` asks `_get_parameter_value` for every parameter and then writes it into the
kwargs **only when it is not None**. So a value the dispatcher resolves to `None` — an identity on a run that has
none — produces no kwarg at all, and a *required* parameter then raises
`TypeError: <step>() missing 1 required positional argument` inside the dispatcher, on every such run.

That is not hypothetical. `RAGStartEvent.user` became optional so a scheduled email-classification run could
delegate without an identity, and every one of those delegations then died at `condense_standalone_question_step`
— the answer had already been paid for by the time the step signature rejected it.

The sibling `agents/tests/test_precondition_event_wiring.py` guards the same dispatcher mechanism for
preconditions. This one guards steps.

Scoped to `RAGAgent` on purpose. Other agents declare a required `user` correctly, because they are only startable
from `UserMessageEvent`, which always carries one — a static check cannot see that guarantee, so applying this rule
to them would flag working code.
"""

import inspect
from typing import get_args

import pytest
from swiss_ai_hub.core.auth import UserIdentity

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent

# Resolved by the dispatcher from RunContext rather than from an event, and legitimately absent on an
# identity-less run. Mirrors the `UserIdentity in (annotation, *get_args(annotation))` match in
# `AgentDispatcher._get_parameter_value`.
_NONE_ABLE_TYPES = (UserIdentity,)


def _none_able(annotation) -> bool:
    return any(candidate in (annotation, *get_args(annotation)) for candidate in _NONE_ABLE_TYPES)


@pytest.mark.parametrize("step_method", RAGAgent.get_steps(), ids=lambda step: step.__name__)
def test_no_step_requires_a_parameter_the_dispatcher_may_not_fill(step_method):
    for name, parameter in inspect.signature(step_method).parameters.items():
        if not _none_able(parameter.annotation):
            continue
        assert parameter.default is not inspect.Parameter.empty, (
            f"RAGAgent.{step_method.__name__} requires '{name}', but the dispatcher omits that kwarg entirely on a "
            f"run without one — `_build_method_kwargs` only writes values that are not None. Every identity-less "
            f"run of this agent would raise TypeError before the step body runs. Give it a default: "
            f"`{name}: UserIdentity | None = None`."
        )
