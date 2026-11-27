from enum import StrEnum


class DocumentIngestionState(StrEnum):
    """Where a document stands in ingestion, as the knowledge list shows it.

    `processing` covers both waiting for and running an attempt: the pipeline records nothing when a run starts,
    because a successful parse rewrites the whole record. Only a failure is written, by the pipeline's retry sensor.
    """

    INGESTED = "ingested"
    PROCESSING = "processing"
    RETRYING = "retrying"
    FAILED = "failed"
