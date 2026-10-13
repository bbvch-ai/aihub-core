from enum import StrEnum


class ToolLoopMode(StrEnum):
    """What the loop's last turn is for.

    ANSWER: the model's final turn is the reply, for blueprints that let the loop answer. GATHER: the loop collects
    tool results as context and the blueprint answers itself, keeping its own prompt, citations and checks.
    """

    ANSWER = "answer"
    GATHER = "gather"
