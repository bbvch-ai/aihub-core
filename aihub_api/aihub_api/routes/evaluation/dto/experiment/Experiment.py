from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from aihub_api.routes.evaluation.dto.experiment.MinimalExperiment import MinimalExperiment


class TaskSummaryData(BaseModel):
    n_examples: Annotated[int, Field(description="Number of examples in the experiment.")]
    n_runs: Annotated[int, Field(description="Number of task runs executed.")]
    n_errors: Annotated[int, Field(description="Number of errors during task execution.")]
    top_error: Annotated[str | None, Field(description="Most frequent error message, if any.")] = None


class EvaluationSummaryData(BaseModel):
    evaluator: Annotated[str, Field(description="Name of the evaluator.")]
    n: Annotated[int, Field(description="Number of items evaluated.")]
    avg_score: Annotated[float, Field(description="Average score from this evaluator.")]


class EvaluationData(BaseModel):
    name: Annotated[str, Field(description="Name of the evaluator.")]
    annotator_kind: Annotated[Literal["LLM", "Code"], Field(description="Kind of evaluator, either LLM or Code.")]
    score: Annotated[float, Field(description="Score between 0 and 1.")]
    explanation: Annotated[str | None, Field(description="Explanation given by Judge LLM.")] = None
    error: Annotated[str | None, Field(description="Error message if the task run failed.")] = None


class ExperimentRunRecord(BaseModel):
    example_id: Annotated[str, Field(description="ID of the dataset example for this run.")]
    question: Annotated[str, Field(description="Input question.")]
    reference_answer: Annotated[str, Field(description="Expected answer for this example.")]
    assistant_answer: Annotated[str, Field(description="Response given by assistant.")]
    thread_id: Annotated[str, "Unique conversation/workflow identifier within the agent instance"]
    display_id: Annotated[str, "UI-facing grouping ID for events within a thread and run"]
    error: Annotated[str | None, Field(description="Error message if the task run failed.")] = None
    latency_ms: Annotated[float | None, Field(description="Latency of the task run in milliseconds.")] = None
    start_time: Annotated[datetime, Field(description="Start time of the task run.")]
    end_time: Annotated[datetime, Field(description="End time of the task run.")]
    conciseness: Annotated[EvaluationData | None, Field(description="How concise is the answer")] = None
    correctness: Annotated[EvaluationData | None, Field(description="How correct is the answer")] = None
    completeness: Annotated[EvaluationData | None, Field(description="How complete is the answer")] = None


class Experiment(MinimalExperiment):
    conciseness: Annotated[EvaluationSummaryData | None, Field(description="How concise is the answer")] = None
    correctness: Annotated[EvaluationSummaryData | None, Field(description="How correct is the answer")] = None
    completeness: Annotated[EvaluationSummaryData | None, Field(description="How complete is the answer")] = None
    items: Annotated[
        list[ExperimentRunRecord],
        Field(
            description="Detailed records of each run within the experiment, "
            "including inputs, outputs, and evaluations."
        ),
    ]
