from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class EvaluationDatasetItemDTO(BaseModel):
    """
    Represents a single item (e.g., a question-answer pair) within an evaluation dataset.
    """
    id: Optional[str] = Field(None, description="Unique identifier for the dataset item (managed by Phoenix).")
    question: str = Field(..., description="The input question for the agent evaluation.")
    answer: str = Field(..., description="The reference (expected) answer for the question.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the dataset item.")

class EvaluationDatasetCreateDTO(BaseModel):
    """
    DTO for creating or updating an evaluation dataset.
    """
    dataset_name: str = Field(..., description="Name of the dataset in Arize Phoenix. This will be used as the identifier.")
    items: List[EvaluationDatasetItemDTO] = Field(..., description="List of question-answer pairs with optional metadata.")
    description: Optional[str] = Field(None, description="Optional description for the dataset.")

class EvaluationDatasetResponseDTO(BaseModel):
    """
    DTO for responding with dataset details from Arize Phoenix.
    Fields like description, input_keys, etc., are more reliably populated for create/update
    responses where this information is taken from the input. For 'get' responses,
    these might be None if not directly available on the Phoenix Dataset object.
    """
    id: str = Field(..., description="Phoenix dataset ID.") # Corresponds to Dataset.id
    dataset_name: str = Field(..., description="Name of the dataset in Arize Phoenix.") # From input for C/U, or query param for Get
    version: str = Field(..., description="Dataset version ID in Phoenix.") # Corresponds to Dataset.version_id
    items: List[EvaluationDatasetItemDTO] = Field(..., description="List of question-answer pairs.")

    # These fields are known during create/update from the input DTO
    # For 'get' operations, they might be None as client.get_dataset() returns a minimal Dataset object
    description: Optional[str] = Field(None, description="Description of the dataset.")
    input_keys: Optional[List[str]] = Field(None, description="Input keys defined for the dataset in Phoenix.")
    output_keys: Optional[List[str]] = Field(None, description="Output keys defined for the dataset in Phoenix.")
    metadata_keys: Optional[List[str]] = Field(None, description="Metadata keys defined for the dataset in Phoenix.")

    # Timestamps for the dataset/version are not directly on the minimal Dataset object
    created_at: Optional[datetime] = Field(None, description="Timestamp related to dataset version (availability depends on source).")
    updated_at: Optional[datetime] = Field(None, description="Timestamp related to dataset examples (availability depends on source).")

