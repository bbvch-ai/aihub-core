from typing import Optional, Annotated, Dict, Any
from pydantic import BaseModel, Field

class EvaluationScore(BaseModel):
    evaluator_name: Annotated[str, Field(description="Name of the evaluator used.")]
    score: Annotated[Optional[float], Field(description="Numerical score from the evaluator (e.g., 0.0 to 1.0).")] = None
    label: Annotated[Optional[str], Field(description="Categorical label output by the evaluator (e.g., 'YES'/'NO', 'RELEVANT'/'IRRELEVANT').")] = None
    explanation: Annotated[Optional[str], Field(description="Textual explanation or feedback from the evaluator.")] = None
    metadata: Annotated[Optional[Dict[str, Any]], Field(description="Any additional metadata returned by the evaluation.")] = None
    error: Annotated[Optional[str], Field(description="Error message if this specific evaluation failed.")] = None