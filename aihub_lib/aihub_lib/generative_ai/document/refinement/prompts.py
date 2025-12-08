SPLIT_DETECTION_PROMPT = """Analyze this table data to detect if it contains multiple tables merged together.

SIGNS OF MERGED TABLES (split when you see these):
- Header-like rows appearing in the middle of data (column names, categories, or descriptive labels)
- A row that looks like it starts a new table (new column headers for a different dataset)
- Text like "Table 2:", "Tabelle:", or a table title/caption appearing mid-data
- Thematic break: data switches to a completely different subject
- Structural reset: the logical structure restarts (new date ranges, new categories, different metrics)

DO NOT split for:
- Empty rows used as visual separators within continuous data
- Subtotal or summary rows that are part of the same dataset
- Category grouping rows within the same table
- Minor formatting variations in data rows

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.

Table Data:
<table_data>
{table_text}
</table_data>

Return table boundaries. The first table always starts at row 0.
If this is a single table, return one entry with start_row=0.
If multiple tables are merged, return multiple entries with each table's starting row.

You MUST use the provided tool to submit your response."""

HEADER_DETECTION_PROMPT = """Analyze this table to determine how many header rows it has.

SIGNS OF MULTI-ROW HEADERS:
- First 1-4 rows contain column names, category labels, or groupings
- Hierarchical headers (e.g., "Q1 2024" with "Jan | Feb | Mar" below)
- Empty cells in header rows where labels span multiple columns
- Unit rows (e.g., "in CHF", "in thousands") below column names
- Subcategory rows that qualify the columns above

SIGNS THAT A ROW IS DATA (not a header):
- Contains numeric values, dates, or specific data points
- Follows a pattern consistent with other data rows
- Contains entity names that are being measured (companies, products, people)

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.

Table Data:
<table_data>
{table_text}
</table_data>

Return the number of header rows (1-4). Most tables have 1-2 header rows.

You MUST use the provided tool to submit your response."""
