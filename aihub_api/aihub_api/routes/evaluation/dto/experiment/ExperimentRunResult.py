from typing import Optional, Annotated, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

# These internal DTOs can be defined here or imported if used elsewhere
class TaskSummaryData(BaseModel):
    n_examples: Annotated[int, Field(description="Number of examples in the experiment.")]
    n_runs: Annotated[int, Field(description="Number of task runs executed.")]
    n_errors: Annotated[int, Field(description="Number of errors during task execution.")]
    top_error: Annotated[Optional[str], Field(description="Most frequent error message, if any.")] = None

class EvaluationSummaryData(BaseModel):
    evaluator: Annotated[str, Field(description="Name of the evaluator.")]
    n: Annotated[int, Field(description="Number of items evaluated.")]
    n_errors: Annotated[Optional[int], Field(description="Number of errors during evaluation for this evaluator.")] = None
    top_error: Annotated[Optional[str], Field(description="Most frequent error for this evaluator.")] = None
    n_scores: Annotated[Optional[int], Field(description="Number of scores recorded.")] = None
    avg_score: Annotated[Optional[float], Field(description="Average score from this evaluator.")] = None
    n_labels: Annotated[Optional[int], Field(description="Number of labels recorded.")] = None
    top_2_labels: Annotated[Optional[Dict[str, int]], Field(description="Top 2 labels and their counts.")] = None


class ExperimentRunEvaluationDetail(BaseModel):
    # Based on RanExperiment.get_evaluations() DataFrame columns
    run_id: Annotated[str, Field(description="ID of the specific task run this evaluation pertains to.")]
    name: Annotated[str, Field(description="Name of the evaluator.")] # Evaluator name
    error: Annotated[Optional[str], Field(description="Error message if evaluation failed.")] = None
    score: Annotated[Optional[float], Field(description="Score from the evaluation.")] = None
    label: Annotated[Optional[str], Field(description="Label from the evaluation.")] = None
    explanation: Annotated[Optional[str], Field(description="Explanation from the evaluation.")] = None
    # Columns from the joined DataFrame (input, output, expected, metadata, example_id)
    input: Annotated[Optional[Dict[str, Any]], Field(description="Input to the task for this run.")] = None
    output: Annotated[Optional[Any], Field(description="Output from the task for this run.")] = None # TaskOutput type
    expected: Annotated[Optional[Dict[str, Any]], Field(description="Expected output (reference data).")] = None
    metadata: Annotated[Optional[Dict[str, Any]], Field(description="Metadata of the example.")] = None
    example_id: Annotated[str, Field(description="ID of the dataset example for this run.")]


class ExperimentRunResult(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the experiment run in Phoenix.")]
    name: Annotated[str, Field(description="The name of the experiment.")]
    description: Annotated[Optional[str], Field(description="The description of the experiment.")] = None
    url: Annotated[str, Field(description="URL to view the full experiment run in the Phoenix UI.")]
    dataset_id: Annotated[str, Field(description="ID of the dataset used.")]
    dataset_version_id: Annotated[str, Field(description="Version ID of the dataset used.")]
    project_name: Annotated[str, Field(description="Phoenix project name.")]

    task_summary: Annotated[Optional[TaskSummaryData], Field(description="Summary statistics of the task executions.")] = None
    evaluation_summaries: Annotated[Optional[List[EvaluationSummaryData]], Field(description="List of summary statistics for each evaluator.")] = None
    # Full evaluation details might be too large; consider if this is needed or if summary is enough.
    # For now, including it as per "results should be included".
    detailed_evaluations: Annotated[Optional[List[ExperimentRunEvaluationDetail]], Field(description="Detailed evaluation results for each run and evaluator.")] = None
