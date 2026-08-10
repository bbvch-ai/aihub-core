from typing import Annotated

from pydantic import BaseModel, Field


# LLM Response Models
class TableBoundary(BaseModel):
    """Boundary marker for a table within merged table data."""

    start_row: Annotated[int, Field(description="0-based index of first row of this table")]


class TableSplitAnalysis(BaseModel):
    """LLM analysis result for detecting merged tables."""

    # reasoning is declared first on purpose. Under guided JSON decoding the field order is the generation
    # order, and a model that emits the answer first has nothing left to say for a trailing required
    # explanation - but the grammar forbids closing the object without it. Whitespace stays legal, so the
    # model emits it until max_tokens. Measured on gemma-4-31B: answer-first deadlocks every call,
    # reasoning-first returns valid JSON in ~1s.
    reasoning: Annotated[str, Field(description="Brief explanation of why tables were split or kept together")]
    tables: Annotated[
        list[TableBoundary],
        Field(description="List of table boundaries. First table always starts at row 0."),
    ]


class HeaderAnalysis(BaseModel):
    """LLM analysis result for detecting header rows."""

    reasoning: Annotated[str, Field(description="Brief explanation of header structure detected")]
    num_header_rows: Annotated[int, Field(description="Number of header rows (1-4)")]


# Result Models
class TableRefinementStats(BaseModel):
    """Statistics for a single table refinement operation."""

    original_rows: Annotated[int, Field(description="Number of rows in original table")]
    was_split: Annotated[bool, Field(description="Whether the table was split into multiple tables")]
    tables_after_split: Annotated[int, Field(description="Number of tables after splitting")]
    header_rows_detected: Annotated[list[int], Field(description="Header rows detected for each resulting table")]
    split_reasoning: Annotated[str, Field(description="LLM reasoning for split decision")]


class TableRefinementMetadata(BaseModel):
    """Aggregated metadata for all table refinements in a document."""

    tables_found: Annotated[int, Field(description="Number of <table> blocks found in the document")]
    tables_processed: Annotated[int, Field(description="Number of tables actually refined by the LLM")]
    tables_unparseable: Annotated[int, Field(description="Number of tables that could not be parsed into a table")]
    tables_skipped_oversized: Annotated[
        int, Field(description="Number of tables too large to fit the LLM's input limit")
    ]
    tables_split: Annotated[int, Field(description="Number of tables that were split")]
    total_tables_after_split: Annotated[int, Field(description="Total tables after all splitting")]
    table_stats: Annotated[list[TableRefinementStats], Field(description="Per-table statistics")]


class TableRefinementResult(BaseModel):
    """Result of refining tables in a document."""

    content: Annotated[str, Field(description="Refined markdown content")]
    metadata: Annotated[TableRefinementMetadata, Field(description="Refinement statistics")]
