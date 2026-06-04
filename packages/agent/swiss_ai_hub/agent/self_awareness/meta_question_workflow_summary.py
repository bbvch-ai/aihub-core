from collections.abc import Callable

from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.workflow import DispatchableWorkflow

SELF_AWARENESS_STEP_NAMES: frozenset[str] = frozenset(
    {"detect_meta_question_step", "answer_meta_question_step", "stop_after_meta_answer_step"}
)


def summarize_workflow_for_meta_answer(steps: list[Callable], t: LocaleHandler) -> str:
    """
    A human-readable list of an agent's own workflow steps, used to ground meta answers.

    The self-awareness steps themselves are skipped so the agent describes its actual work, not the
    machinery that answers questions about it.
    """
    lines: list[str] = []
    for workflow_step in steps:
        if workflow_step.__name__ in SELF_AWARENESS_STEP_NAMES:
            continue
        name = getattr(workflow_step, DispatchableWorkflow.STEP_NAME_ANNOTATION, None)
        if name is None:
            continue
        description = getattr(workflow_step, DispatchableWorkflow.STEP_DESCRIPTION_ANNOTATION, None)
        detail = f": {t.extract(description)}" if description is not None else ""
        lines.append(f"- {t.extract(name)}{detail}")
    return "\n".join(lines)
