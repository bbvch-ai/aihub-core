---
title: Release Notes Assistant
description: A chat assistant that writes the release notes of a Jira fix version — one note per ticket, grouped by type, in each configured language.
---

# Release Notes Assistant

The **Release Notes Assistant** turns a Jira release into release notes. Ask it for a version — *"Release notes for
2.4.0"* — and it reads every ticket of that fix version in the configured projects, writes one short note per ticket for
your readers, and answers with a changelog grouped into new features, fixes, improvements and other changes. If the
profile names further languages, the same changelog follows in each of them.

It works with **Jira Cloud** and **Jira Data Center** alike, and it only reads: nothing is ever written to Jira.

::: tip Name the version as Jira spells it
The assistant looks for one of the projects' own fix version names in your message. *"Release notes for 2.4.0"*,
*"What's new in 2.4.0?"* or *"v2.4.0 please"* all work. When the message names no version, several, or one Jira does not
have, it answers with the versions it does know instead of guessing.
:::

## What it does

```mermaid
flowchart TD
    A[User message] --> B[Find the fix version<br/>the message names]
    B --> C{Exactly one<br/>known version?}
    C -- No --> D[Ask back, offering<br/>close or recent versions]
    C -- Yes --> E[Read every ticket of that<br/>version in the projects]
    E --> F{Any tickets?}
    F -- No --> G[Say there is<br/>nothing to write about]
    F -- Yes --> H[Write a note per ticket,<br/>showing each batch as it is done]
    H --> I[Translate the notes into<br/>each further language]
    I --> J[Suggest follow-up questions]
```

1. **Find the release.** The assistant lists the fix versions of the configured projects and finds the one the message
   names. A version name counts only as a whole word: *2.4* is not found inside *2.4.0*, while *"for 2.4."* still names
   2.4. Case does not matter, a leading *v* is fine, and quotes the chat turned curly are no problem. A name that exists
   in several of the projects is one release across all of them.
2. **Read the tickets.** Every ticket of that fix version in the configured projects is read, minus whatever the
   profile's JQL filter leaves out.
3. **Write the notes.** The model writes one or two sentences per ticket for the configured readers, from the ticket's
   summary and description. Tickets are sent a batch at a time, several batches at once, and each batch appears in the
   chat as soon as it and the ones before it are done, so the answer starts within seconds even for a large release.
4. **Translate.** Each further language follows as its own block, translated from the written notes.
5. **Follow-ups.** As in every chat assistant, a title is set for the conversation and follow-up questions are
   suggested.

The changelog itself is put together by the platform, not by the model: the model only writes the notes. That is what
lets a release of hundreds of tickets fit models that answer at most a few thousand words at a time.

### Sections

Each ticket goes into a section by its Jira issue type:

| Section          | Issue types                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| **New features** | Story, User Story, New Feature, Feature, and their German, French and Italian names |
| **Fixes**        | Bug, Defect, and their German, French and Italian names                             |
| **Improvements** | Improvement, Enhancement, and their German, French and Italian names                |
| **Other**        | Everything else: Task, Sub-task, Epic, service requests, your own types             |

Within a section, tickets are ordered by project and number. With **Show ticket keys** on, each bullet starts with the
ticket key, linked to the ticket in Jira.

### When something goes wrong

- **A note the model could not write** shows the ticket's summary instead, and a thought in the run says how many did.
- **A note that could not be translated** stays in the writing language, again with a thought saying how many.
- **A Jira problem** — rejected credentials, a project that does not exist or that the account cannot see, an invalid
  JQL filter, an unreachable Jira — is answered with one sentence in the user's language that says who can fix it.
  Jira's own English message goes into a collapsible thought for the administrator.
- **A release with more than 300 tickets** is refused rather than cut short; an administrator can narrow it with the JQL
  filter.

## What it does *not* do

- **It never writes to Jira.** It reads versions and tickets, nothing else.
- **It does not publish anything.** The release notes are a chat answer to copy from; they are not sent or posted
  anywhere.
- **It does not read comments, attachments or linked pages** — only each ticket's type, summary and description.
- **It does not remember earlier changelogs.** Asking again, or naming a version in a follow-up, writes the changelog
  anew.
- **It does not write a summary paragraph.** The answer is the changelog: a title per language, then the sections.
- **One Jira per profile.** A profile reads one Jira site and the projects listed on it.

::: details Known limitation: "What changed in 2.0?"
Before anything else, every chat assistant checks whether a message is a question about the assistant itself. Phrased as
*"What changed in 2.0?"* or *"Was hat sich in 2.0 geändert?"*, with nothing but a version after it, the message is
currently read as such a question, and the assistant describes how it works instead of writing the notes. *"What's new
in 2.0?"* or *"Release notes for 2.0"* are not affected.
:::

## Setting it up

1. **Grant the blueprint.** The Release Notes Assistant is not part of a new tenant's default set; a sysadmin grants it
   (see [Access control](../../16_multi_tenancy/4_access_control/)).
2. **Create a profile.** On the Admin UI's **Agents** page, either start from the **Customer Release Notes** template
   (English and German, without ticket keys, sub-tasks left out) or create a profile from the **Release Notes
   Assistant** blueprint.
3. **Connect Jira.** Under **Jira**, enter the URL, the edition and the token:
   - **Jira Cloud:** the site URL (`https://acme.atlassian.net`), the e-mail of the account and a classic **API token
     without scopes**, created at *id.atlassian.com → Security → API tokens*. Scoped tokens are not supported.
   - **Jira Data Center:** the base URL including any context path (`https://jira.acme.ch/jira`) and a **personal access
     token**.
   - Use an account that can browse the projects and nothing more: the assistant reads with its permissions.
4. **List the projects.** Enter the project keys, e.g. `ENG`. Add a **JQL filter** for tickets that should never appear,
   e.g. `issuetype not in subTaskIssueTypes()` or `labels != internal`.
5. **Choose the languages and readers.** Pick the language the notes are written in, optionally further languages, and
   describe who reads them — *"customers using the web app"* gives different notes than *"the support team"*.
6. **Choose the model** and save. Ask the profile for a version you know to check the connection: every connection
   problem is answered in the chat.

::: warning A Jira on your company network
The platform refuses to connect to internal addresses — Docker service names, `localhost`, private IP ranges — so that a
profile cannot be pointed at the platform's own services. To allow a Jira Data Center reachable only internally, an
operator adds its host name to **`JIRA_ALLOWED_PRIVATE_HOSTS`** in the deployment's environment (comma-separated), and
the agent container needs outbound network access to it.
:::

## Configuration reference

| Field                   | Default                             | Description                                                                                               |
| ----------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Jira URL**            | —                                   | Jira's base URL. Redirects are not followed, so enter the address Jira answers at.                        |
| **Jira edition**        | Jira Cloud                          | Jira Cloud or Jira Data Center.                                                                           |
| **Account e-mail**      | —                                   | Jira Cloud only: the e-mail of the account the API token belongs to.                                      |
| **Token**               | —                                   | API token without scopes (Cloud) or personal access token (Data Center).                                  |
| **Jira projects**       | —                                   | Keys of the projects whose fix versions the release notes cover.                                          |
| **JQL filter**          | *(empty)*                           | JQL every ticket must also match.                                                                         |
| **Language**            | English                             | The language the notes are written in.                                                                    |
| **Also translate into** | Off                                 | Further languages; turn it on to pick them. Each gets its own block, translated from the written notes.   |
| **Readers**             | *the customers who use the product* | Who the notes are written for.                                                                            |
| **Show ticket keys**    | On                                  | Lead each bullet with its ticket key, linked to the ticket. Turn it off for readers who cannot open Jira. |
| **Max input tokens**    | `16384`                             | The conversation history kept for each turn. Earlier changelogs are long and only the questions matter.   |

The model settings and the **Task LLM** (titles, follow-up questions, the check for questions about the assistant) are
the same as on the other chat assistants.

Fixed by the deployment, not by the profile: at most **300 tickets** per release, **10 tickets** per model call, **4**
model calls at once, and the first **4,000 characters** of each description.
