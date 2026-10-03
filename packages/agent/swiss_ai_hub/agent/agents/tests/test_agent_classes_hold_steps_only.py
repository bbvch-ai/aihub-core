"""An agent class declares its workflow and nothing else: a helper on a blueprint ties reusable logic to that
blueprint, so another one copies it or subclasses to reach it."""

import importlib
import inspect
import pkgutil

import pytest

import swiss_ai_hub.agent.agents as agents_package
from swiss_ai_hub.agent.agents.agent import Agent


def _blueprints() -> list[type[Agent]]:
    for module in pkgutil.walk_packages(agents_package.__path__, prefix=f"{agents_package.__name__}."):
        if ".tests" not in module.name:
            importlib.import_module(module.name)
    found: set[type[Agent]] = set()
    pending = [Agent]
    while pending:
        for subclass in pending.pop().__subclasses__():
            pending.append(subclass)
            if subclass.__module__.startswith(f"{agents_package.__name__}."):
                found.add(subclass)
    return sorted(found, key=lambda blueprint: blueprint.__name__)


@pytest.mark.parametrize("blueprint", _blueprints(), ids=lambda blueprint: blueprint.__name__)
def test_an_agent_class_defines_only_steps(blueprint: type[Agent]) -> None:
    helpers = [
        name
        for name, member in vars(blueprint).items()
        if inspect.isfunction(inspect.unwrap(getattr(member, "__func__", member)))
        and not getattr(getattr(member, "__func__", member), Agent.STEP_ANNOTATION, False)
    ]

    assert not helpers, f"{blueprint.__name__} defines helpers {helpers}; move them into a class its steps import"
