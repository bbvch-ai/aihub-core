---
title: Knowledge Extraction Agent
description: Collects records from many knowledge documents into one table, such as every hardware position on a supplier's 2025 invoices, each row naming the file it came from.
---

# Knowledge Extraction Agent

The **Knowledge Extraction Agent** answers requests that need every matching line from many documents, not the few most
similar passages a knowledge search returns. A user asks in one chat message, for example *"Find all billing positions
regarding hardware on the 2025 bills from Acme"*, and gets back one table: one row per record found, each row naming the
path and file it came from, with a summary of how many files were read, how many rows were found and which files could
not be read. The whole table is also a CSV file to download.

::: tip When to reach for this agent
Use it when the answer is a list of records collected across documents: invoice lines, contract parties, service levels,
deadlines. For a question one passage answers, the
[Document Intelligence Assistant](../5_document_intelligence_assistant/) is faster and cites its sources. The
[Universal Agent](../13_universal_agent/) offers the same extraction as one of its tools when its profile switches the
document tools on.
:::

## What it does

```mermaid
flowchart LR
    A[User message] --> B[Read the request]
    B --> C[Every document<br/>in scope]
    C --> D[Design the columns]
    D --> E[Extract from every<br/>document in parallel]
    E --> F[Table preview,<br/>summary and CSV]
```

1. **Read the request.** One model call reads the message: the columns the user asks for, which rows to keep, and any
   folder, file or year the user names. A follow-up such as *"the same for 2024"* is read with the conversation.
2. **Take every document in scope.** Every document in the profile's collections and path filter is read, narrowed only
   by the folders, files or years the user named. No search decides which documents count, so a document is never missed
   because it words things differently from the request. A supplier or a topic is a condition on the rows, not a place:
   *"from Acme"* keeps Acme's rows, it does not pick documents.
3. **Design the columns.** The columns are designed from the user's words, such as *date, item, amount, currency*. A
   condition like *"only hardware"* decides which rows are kept and never becomes a column.
4. **Extract.** Every document is read and its matching records are extracted, many documents at the same time.
   Documents are read in overlapping parts, so a line on the last page is found and a line at the boundary between parts
   is not counted twice. A row that may not meet the condition is kept and marked *unsure* in a **Match** column, so a
   person can check it instead of it being dropped. A condition on the whole document, such as its supplier, party or
   year, applies to every row in it: a document that clearly does not meet it gives no rows and is listed under "No rows
   from".
5. **Answer.** The answer shows the first rows of the table (up to 100), followed by the summary, and the whole table as
   a CSV file: attached to the answer in the chat, a download link through the API. A document that could not be read is
   listed under the table with the reason; the other documents' rows are unaffected. Documents that were read but gave
   no rows are named under "No rows from", so an empty result never looks like a missing clause.

The chat shows each step as it happens: a line saying how many documents will be read, which columns the table has and
about how long it takes; a line when a long document starts; one line per document as it is extracted, with its first
rows ("12 of 150 · invoice.pdf: 3 rows — Laptop X1, 1,200; Dock D2, 180"); and, while a document takes more than a
minute, a line saying it is still being read. An answer can take many minutes when many documents are read; the progress
shows it is alive.

### When more than 100 documents would be read

Reading every document of a large scope takes long, so above 100 documents the agent first asks. The answer shows:

- how many documents would be read and about how long that takes;
- what the table would hold: its columns and which rows are kept;
- a **sample** table from five of the documents, those most likely to hold what was asked for: documents whose text
  names what identifies them (a supplier, a number), then those containing typical words of the wanted lines;
- how the documents break down **by folder**, **by year in the path** and **by collection**;
- what you can do: reply *yes* to read all of them in one answer, or narrow the request, for example to one folder or
  year.

The sample can hold no row, for example when the wanted records are rare; the answer then says so and still shows what
the table would hold. Asking something new instead of *yes* replaces the waiting request. Confirming needs the same
conversation, so a client of the OpenAI-compatible API passes the conversation's `thread_id` in `metadata` with every
message, as the chat UI does.

Above **Most Documents per Table** (1000 by default) nothing is read: the answer shows a sample and asks to narrow the
request, and lists the folders and years of the first 1000 documents by path without counts, since the rest were not
looked at.

### Searching for the documents first

A profile can switch on **Search for the Documents First**. The model then works through the documents with three tools
(it lists their paths, searches their text for exact terms such as a supplier name, and reads a document when unsure)
and selects the documents to read; only those are extracted. This is faster on large collections, but a document the
search does not find is missing from the table. The search is bounded by **Maximum Decisions** and **Maximum Tool
Calls**; at the limit the agent selects by folder and checks the request's conditions in each document, and the answer
says so.

With **Rank Documents by Meaning**, the search also ranks the documents by meaning, which finds documents written in
other words or another language than the request. In the default mode the same ranking only decides which documents are
sampled and read first; no document is ever left out because of its rank.

::: tip Which mode for which profile
Reading every document is the safe default: nothing is missed, but each document's rows are judged by the extraction
model on its own. When a request names one supplier or party among many in the same folders (*"Acme's 2025 hardware"*
over every supplier's invoices), that judgement now and then keeps a row from another supplier's document, and every
document costs a model call. For profiles used for such exact, narrow requests over large mixed collections, switch on
**Search for the Documents First**: only the documents the search selects are read, which is faster and cheaper, at the
risk that a document the search does not find is missing.
:::

### Long documents

A document longer than **Longest Fully Read Document** (500,000 characters by default, a few hundred pages) is read only
in its relevant parts: its opening, which states what every row shares, and the parts where the wanted lines most likely
are. Its rows are marked **(partly read)** next to the file name, and the summary lists it under "Partly read (rows may
be missing)", because a line in a part that was not read is not found. See the ADR
`2026_10_21_partial_reads_of_long_documents_in_record_extraction`.

## What it does *not* do

- **It does not compare or reconcile documents.** Matching an invoice line to its contract line, or flagging deviations,
  is a different task.
- **It does not keep the file forever.** The CSV file is kept for seven days; the copy attached to a chat stays with the
  chat.
- **It never reads outside its scope.** Only the profile's collections are used, narrowed to those the asking user may
  read and to the profile's path filter. A request for other documents, or a `#` reference to a collection the profile
  does not list, is left out and the answer says so; a file the user names outside the scope is reported as not found,
  never replaced by a similar one.

## Limits

Every request is bounded, and nothing is cut without the answer saying so:

| Limit                           | What happens at the limit                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Most Documents per Table**    | Above it nothing is read; the answer shows a sample and asks to narrow the request.                         |
| **More than 100 documents**     | A sample first; everything is read once the user confirms.                                                  |
| **Longest Fully Read Document** | A longer document is read in its relevant parts and its rows are marked *partly read*.                      |
| **Model Calls at Once**         | How many extraction calls one agent instance makes at the same time; bounds the load and how long it takes. |
| **Maximum Decisions / Calls**   | Only with **Search for the Documents First**: the search stops and the agent selects by folder.             |
| **Rows shown in the answer**    | The first 100 rows (fewer when they are very long); the CSV file holds every row, with every cell complete. |

If a collection the sample was taken from is no longer available when you confirm, nothing is read and the answer says
so; ask again to extract from what is available.

## Setting it up

1. **Grant the blueprint.** The Knowledge Extraction Agent is not part of a new tenant's default set; a sysadmin grants
   it (see [Access control](../../16_multi_tenancy/4_access_control/)).
2. **Create a profile.** In **Admin > Agents > Blueprints**, select **Knowledge Extraction Agent** and click **Create
   Profile**, or start from the **Document Tables** template.
3. **Choose the collections.** Under **Knowledge Tool**, list the databases and collections the agent works on. Saving
   checks that you may read them.
4. **Set a path filter** (recommended). Under **Knowledge Documents**, a pattern such as `invoices/**` limits the agent
   to matching documents; it can never look outside it. Every request reads every document in this scope, so a narrow
   scope keeps answers fast.
5. **Choose the models.** The main model reads the request and designs the columns. The **Extraction Model** reads each
   document; a smaller, cheaper model works well.
6. **Review the limits** and save.

## Configuration reference

| Field                                               | Default     | Description                                                                 |
| --------------------------------------------------- | ----------- | --------------------------------------------------------------------------- |
| **Instructions**                                    | *(empty)*   | Added to the agent's instructions, e.g. how documents are named.            |
| **Search for the Documents First**                  | off         | Let the model search for the documents and read only those it selects.      |
| **Knowledge Tool > Collections**                    | —           | The databases and collections the agent works on.                           |
| **Knowledge Documents > Document Path Filter**      | *(empty)*   | Only documents whose path matches this pattern, e.g. `invoices/2025/**`.    |
| **Knowledge Documents > Rank Documents by Meaning** | off         | Rank documents by meaning: in the search, and to choose what is read first. |
| **Table Extraction > Extraction Model**             | main model  | The model that reads each document and extracts its rows.                   |
| **Table Extraction > Most Documents per Table**     | `1000`      | Above it, the user is only asked to narrow the request.                     |
| **Table Extraction > Longest Fully Read Document**  | `500000`    | Longer documents (in characters) are read in their relevant parts.          |
| **Table Extraction > Model Calls at Once**          | `4`         | Extraction calls one agent instance makes at the same time.                 |
| **Tools > Maximum Decisions / Maximum Tool Calls**  | `15` / `30` | How long the model may search, with **Search for the Documents First**.     |
