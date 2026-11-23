# Document Periods Matched Against Path Dates by Code

## Context

A Document Tables request often names the period its documents are dated in: "the 2025 invoices", "Q1 2026", "since
March 2025" (#2349). Until now the request reading turned such a period into one of two things (ADR
`2026_11_18_document_condition_judged_in_the_first_extraction_window`):

- a **year location** (`invoices/2025/**`) when a folder carried the year, which found nothing on a corpus without year
  folders, so the answer was "nothing at that location";
- a **document condition** in words ("dated between 1 October 2018 and 31 December 2018"), which the extraction model
  judged on the first window of every document, so a document whose path already said it was outside the period still
  cost a model call, and one inside it could still be skipped by a misjudged date in its text.

Most knowledge collections already date their documents in their paths: year and month folders, ISO or compact dates in
scan names, day-first dates in Swiss file names. That information is exact and free, and nothing used it.

## Decision Drivers

- *Never narrow on doubt*: a path's date must contain the document's true date, or the document is kept.
- *Requests without a period behave as before*: same selection, same judge input, same summary.
- *Deterministic*: the same path gives the same date in every run, with no model in the loop.
- *The user sees what the period did*: how many documents it kept, left out, or could not date, and which.
- *No new dependency* and no measurable cost on the event loop.

## Decision

- **The model writes the period as dates, code puts it into words.** The request reading gains `period_start` and
  `period_end` (ISO days, either may be null). A year or any other period is never a location and never part of
  `document_condition`. The reading is normalised once (`with_readable_period`); a period no code can read stays in the
  document condition in the model's words and narrows no path. `{{ today }}` is in the reading prompt for relative
  periods.
- **A reading loses the date folders that only repeat the period** (amendment 2026-11-23, e2e N1). The prompt rule above
  is not enough: on a corpus with `invoices/2024/` and `invoices/2025/`, Kimi-K2.6 read "invoice totals 2025" as
  `invoices/2025/**` plus the period in 5 of 5 readings, and the undated invoices were never read. So the prompt names
  this case, and code backs it: `ExtractionRequestPlainAnswer.without_period_folders` runs on the reading of the request
  (`WholeScopeRequest.reading`), before the form is shown, and on the second reading of a form answer whose dialog kept
  the Location as shown (`ExtractionRequestAnswers.keeps_location`: nothing written under Location, nothing dropped), so
  a reading of the whole conversation cannot bring the year folder back; it is the flag `widens_period_folders` of
  `WholeScopeRequest.read`. It runs after the files the message names have replaced the places the model made of them
  (`_narrowed`), so a named file never makes a widened place drop out. A `path_glob` location with no `path_regex` loses
  each run of literal folders that core's `PathDateParser.folder_dates` reads as nothing but a date (a year, month or
  quarter folder, also one under its dated parent, such as `2025/q1`), when the run's innermost date lies WITHIN the
  period and nests in each folder of the run, and no user turn of the conversation writes the run with a neighbouring
  folder as a path (backslashes read as slashes). A pattern segment (`2025*`) dates neither itself nor a folder below
  it. Each such folder becomes `**` (adjacent `**` merged), so the glob only matches more: `invoices/2025/**` →
  `invoices/**`, `invoices/2025/q1` → `invoices/**` for Q1 2025, `invoices/2025/acme/**` → `invoices/**/acme/**` (`**`,
  not `*`, so an undated `invoices/acme/x.pdf` is read too), `2025/**` → `**`. A location that becomes `**` (or `/**`)
  makes the whole scope the place, since dropping it alone would read fewer documents; duplicates are removed, and each
  widening is logged at info level. Without discovery the location only ever widens; with discovery the widened Location
  is what the search is told, and its own selection decides (`WholeScopeRequest.within` keeps the documents it chose by
  id at the confirmed place). A file or a folder path the user wrote into another part of the dialog still counts on
  that second reading: the named file is placed before the net, and the written path is protected by the written-path
  check over every user turn.
- **A period on rows that carry their own date filters the rows only.** For statement lines, bookings, transactions or
  time entries the period stays in `instructions` in words ("booking date in February 2025"), and `period_start` and
  `period_end` stay null. A statement's path names the day it was issued, not the days of its bookings: matched against
  the paths, `Kontoauszug_2025-03-01.pdf` covering February would be left out with its February lines.
- **One period per selection.** `KnowledgeDocumentSelection.path_date_range` (`PathDateRange`) is applied by
  `KnowledgeDocumentSelector` after every criterion, to the union of the entries, in one pass off the event loop
  (`KnowledgeDocumentListing.dated_within`). This departs from the ticket's "next to the path glob and regex" on
  purpose: a request names its period once.
- **A hand-written path recogniser in core**, `PathDateParser`, on `re`, reusing `DateTextParser`'s month table and
  builders and `PeriodTextParser` for ranges inside one segment. Rules:
  - year folders; year/month folders with numbers or de/en/fr/it month names (folders only); ISO and compact dates with
    counter suffixes; day-first dot, dash and underscore dates; quarters; `dd.mm.yy` only with two-digit day and month;
  - **day first always**: `04-06-2026` is 4 June; a date that does not exist day first gives no date and is never
    swapped;
  - digit guards, an identifier stop-list (`Nr`, `SIA`, `v`, `RE`, …), and a year window from 1990 to next year;
  - a year glued to letters that no pattern reads (`rev2025`, `Stand2025`, `2025er`) makes its segment unknown, unless
    it is glued to a stop-listed identifier (`RE2025-003`); product numbers such as `Office2019` next to a date are a
    safe loss of this rule;
  - a range or list inside one segment is read as the span `PeriodTextParser` finds, only if that span covers every date
    the segment states and is wider than each; otherwise the path is unknown. A bare day number next to a finer date
    counts as part of such a range (`1-15 März 2025`, `2025-03-01 - 15`), except a counter glued on with `_` or `-`
    (`15.03.2025_1`, `2025-03-15-0001`);
  - a date that is one end of an open period makes the path unknown: a word before it (`ab`, `seit`, `since`, `dès`,
    `dal`, `bis`, `vor`, `pre`, `up to`, `through`, …, also with `Mitte`, `Ende`, `fin`, `mi` and the like in between:
    `ab Mitte 2020`), a word after it (`heute`, `present`, `ff`, `und älter`, `und später`, `onwards`, `or later`,
    `to date`, `à ce jour`, `ad oggi`, …), or a sign between it and the segment's edge (`2020+`, `2020-`, `-2019`,
    `>2020`, `<2020`). Whole words only, each list on its own side of the date; a written range is checked first, so
    `Januar bis März 2025` stays a span;
  - a dash joins a day to a month name only when nothing stands around it (`15-mar-2025`), so `Kapitel 3 - März 2025` is
    no day;
  - a two-digit day number equal to its month's own number (`03 März 2026`) reads as the whole month, since it may
    number the month; `3. März` and `15 März` stay days;
  - dates of different segments must nest; otherwise the path is unknown;
  - results are memoised as small tuples (50,000 paths).
- **Four verdicts.** WITHIN (the path dates the document wholly inside the period) is read and not judged on the period;
  OVERLAPPING and UNDATED are read and judged on the code-written period with the document condition; OUTSIDE is not
  read. The judge's code and prompt are unchanged.
- **Counts, not structured facts.** `PathDateCounts` rides on the run and the summary states it: the counts, up to ten
  left-out paths within 2,000 bytes, and, when nothing is left, the years the left-out paths are dated in.
- **The listing tool takes the same period** (`list_knowledge_documents(period_start=, period_end=)`), so the Universal
  Agent and the discovery loop can preview what a period keeps. `select_knowledge_documents` counts before the period.

Rejected:

- *`dateparser` or a similar library*: research found it drops quarters and compact dates and fills missing parts from
  today's date, which narrows.
- *Deriving the period from `document_condition` with `PeriodTextParser`*: misreads open bounds, negations and
  conditions with several dates.
- *A period per criteria entry*: duplicated across entries, and a model could set different periods for one request.
- *Reading ambiguous US-style dates month first when day first is impossible*: rejected by the user in favour of one
  rule a user can predict.

## Consequences

- On mixed corpora more documents are read: undated documents were sometimes left out by a year location; they are now
  read and judged on the period, one window-0 judgement each.
- US-style file names are misread (`04-06-2026` for 6 April is 4 June) and can be left out wrongly; the excluded-path
  list shows them.
- Postcodes inside the year window (`2000 Neuchâtel`), sequence numbers without a stop-listed prefix
  (`Rechnung_2025_03`), calendar-valid 8-digit ids and bare versions (`10.11.12`) can be read as dates. Tests pin each.
- Listed months (`Jan_Feb_2025`), listed days (`1 und 15 März 2025`), two-year spans (`2025-2026`, `FY2025`), open
  bounds (`ab 2020`, `2020-heute`, `Archiv bis 2019`) and a month word next to a finer date in one segment read as
  unknown: the document is kept and judged. Open-bound words also catch some names (`AB` for Auftragsbestätigung,
  `Prima`) and a number after a date with a spaced dash (`2025-03-15 - 2`); both are safe losses.
- `03 März 2026` reads as all of March 2026 rather than 3 March: a document so named is kept for any period in March.
  `3 März 2026` stays 3 March, so a folder numbering its month with one digit is narrowed to a day.
- The first resolve of a large scope pays about 0.1 ms per path off the event loop; repeated listings hit the cache.
- The date-folder safety net has limits. It widens only a `path_glob` of the request's reading or of a second reading
  whose dialog kept the Location: a Location the user types into the form, a regex and a folder that names more than a
  date (`invoices-2025`) are never changed. A date folder outside the period, or wider than it (`invoices/2025/**` for
  Q1 2025), stays, as an explicit choice; its undated documents are then still left out. A reading that writes the year
  folder without any period is not touched, since there is no period to compare. The second reading of a free typed
  reply relies on the prompt alone for its Location, and so does the discovery search's own selection
  (`select_knowledge_documents`), which the confirmed Location replaces but which is never widened; with discovery a
  widened Location can therefore read fewer documents than the folder would have, when the search chose documents by id
  outside the folder. A folder the user meant, written in words rather than as a path (*"the 2025 folder"*), is widened
  as well; the form shows the widened Location, where the user can type the folder back. A period the model restates in
  words in `document_condition` as well as in `period_start`/`period_end` is not taken out by code (Gemma: "from the
  first quarter of 2025" for "amounts of the invoices from the first quarter of 2025", 2/2), the same class as e2e F3:
  documents the path dates within the period are still judged on that condition (an "unsure" row at worst, a skip only
  for a clear contradiction), and the form shows the period twice. Code cannot tell reliably that free words only
  restate the period, and prompt edits for it destabilised other readings.
- A type word that only rode on a year folder is lost with the folder. Before, "Hardware lines of the Q1 2026 invoices"
  read as Location `invoices/2026/**`, which kept the request to invoices by accident. Now the period has no Location
  and the type word is only `document_kind`, so in a scope that mixes kinds, another kind dated in the period by its
  path (`statements/creditcard-statement-2026-03.pdf`) is read without a judgement and adds its rows (e2e S5: 7 rows
  instead of 4, 4/4 runs). Rows are added, never lost. Reading the type word as a document condition was tried and
  rejected: the models applied it to single-kind scopes too, and the first-window judgement then skips credit notes
  filed among invoices, which turns extra rows into missing ones. A judge that lets a kind admit its corrections and
  credit notes is the follow-up.
- Amends the reading half of ADR `2026_11_18_document_condition_judged_in_the_first_extraction_window`; its judging half
  stands.
