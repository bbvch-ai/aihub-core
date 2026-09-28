from collections.abc import Callable

from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    LLMEvent,
    StopEvent,
)

from swiss_ai_hub.agent.agents.agent import Agent


class ConversationWiring:
    """What the spine derives from a blueprint's composed step set, for its barriers and its defaults."""

    @staticmethod
    def count_enrichers(blueprint: type[Agent]) -> int:
        """Steps that contribute a context block; the join waits for one block from each."""
        return sum(1 for step in blueprint.get_steps() if ContextBlockEvent in _outputs(step))

    @staticmethod
    def count_post_answer_hooks(blueprint: type[Agent]) -> int:
        """Steps that report once they are done with the answer; the stop waits for each report."""
        return sum(1 for step in blueprint.get_steps() if AnswerPostProcessedEvent in _outputs(step))

    @staticmethod
    def stops_after_answer(steps: list[Callable]) -> bool:
        """Whether one of these steps already turns the answer into the run's stop event."""
        return any(
            LLMEvent in _inputs(step) and any(issubclass(event, StopEvent) for event in _outputs(step))
            for step in steps
        )


def _outputs(step: Callable) -> set[type]:
    return set(getattr(step, Agent.OUTPUT_EVENTS_ANNOTATION, set()))


def _inputs(step: Callable) -> set[type]:
    return set(getattr(step, Agent.INPUT_EVENTS_ANNOTATION, set()))
