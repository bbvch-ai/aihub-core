from typing import Annotated, Any

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    agent_class: Annotated[str, Field(description="The class name of the agent to be evaluated.")]
    agent_id: Annotated[str, Field(description="The specific ID of the agent instance to be evaluated.")]
    dataset_id: Annotated[str, Field(description="The ID of the Langfuse dataset to use for evaluation.")]

    experiment_name: Annotated[
        str | None,
        Field(description="Custom name for the experiment. If not provided, a name will be auto-generated."),
    ] = None
    experiment_description: Annotated[
        str | None, Field(description="An optional description for the Langfuse experiment.")
    ] = None
    experiment_metadata: Annotated[
        dict[str, Any] | None, Field(description="Optional metadata to associate with the Langfuse experiment.")
    ] = None
