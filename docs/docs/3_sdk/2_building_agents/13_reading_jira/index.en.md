---
title: Reading Jira from an Agent
description: Let an agent query Jira Cloud or Jira Data Center for tickets with JQL, with descriptions as readable text.
---

# Reading Jira from an Agent

An agent that acts on live Jira data, such as one writing release notes for a fix version, queries Jira directly. Core
ships a read-only Jira client for this. It works the same against Jira Cloud and Jira Data Center 11.3, and it reads no
agent configuration itself: your agent embeds a connection config and passes it in.

## The connection config

`JiraConnectionConfig` is a `StepConfig`, so the dispatcher injects it into any step that declares it as a parameter.

| Field         | Purpose                                                                                   |
| ------------- | ----------------------------------------------------------------------------------------- |
| `base_url`    | Where Jira is, e.g. `https://acme.atlassian.net` or `https://jira.acme.ch/jira`.          |
| `deployment`  | `cloud` or `data_center`. Decides how the agent signs in and how results are paged.       |
| `email`       | Jira Cloud only: the account the API token belongs to.                                    |
| `api_token`   | A Jira Cloud API token without scopes, or a Jira Data Center personal access token.       |
| `max_tickets` | Fixed by the deployment (1,000): a search matching more fails instead of being cut short. |

The token is a password field. Everyone who can use the agent reads what this account can read, so give the agent a
dedicated read-only account limited to the projects it needs. Creating the tokens is described for the
[Jira knowledge source](../../../2_platform/8_knowledges/#jira-issues); the same tokens work here.

## Finding tickets in a step

Add the config to your agent config, then call `JiraTicketSearch.find_tickets` in a step. It returns every matching
ticket, following Jira's paging to the end, sorted by project and number.

```python
from swiss_ai_hub.core.jira import JiraConnectionConfig, JiraJql, JiraTicketSearch


class ReleaseNotesAgentConfig(AgentConfig):
    jira: JiraConnectionConfig


class ReleaseNotesAgent(Agent):
    @step()
    async def collect_tickets(self, event: ReleaseRequestedEvent, jira: JiraConnectionConfig) -> TicketsFoundEvent:
        tickets = await JiraTicketSearch.find_tickets(
            jira,
            project_keys=["ENG", "SD"],
            clauses=['issuetype != "Sub-task"', f"fixVersion = {JiraJql.string_literal(event.version)}"],
        )
        return TicketsFoundEvent(keys=[ticket.key for ticket in tickets])
```

Each clause is put in parentheses and joined with `AND` after the project restriction, so an `OR` inside one cannot
reach other projects. A value that comes from a chat message, like the version above, must go through
`JiraJql.string_literal()`. Pasted into the query unquoted, `2.4" OR project = HR` would read another project.

A `JiraTicket` carries `key`, `url`, `project`, `issue_type`, `status`, `summary`, `description`, `labels`, `components`
and `fix_versions`. The description is markdown converted from the HTML Jira renders, so headings, lists, tables and
code blocks survive and no rich-text JSON reaches the model. Reporter and assignee are not read.

## Errors

Every failure is a `JiraError` with an English message that never contains the token or the query. Catch the subclasses
to tell your user what went wrong in their language:

| Error                      | Raised when                                                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| `JiraConfigurationError`   | A value is missing, the URL points inside the platform, or no Jira REST API answers at the URL. |
| `JiraAuthenticationError`  | Jira refuses the credentials.                                                                   |
| `JiraProjectNotFoundError` | A project does not exist, the account cannot see it, or it was renamed (`renamed_to`).          |
| `JiraInvalidQueryError`    | Jira rejects the JQL, e.g. an unknown field or fix version; `problems` holds Jira's own words.  |
| `JiraTooManyTicketsError`  | More tickets match than `max_tickets`.                                                          |
| `JiraRequestError`         | Any other error answer from Jira.                                                               |

The checks run before the search, in that order. This matters because Jira Cloud answers an invalid query, and both
editions answer a project the account cannot see, with zero tickets rather than an error, which would otherwise look
like a release without tickets.

## Deployment notes

- **Network**: an agent container needs the `egress` network to reach Jira.
- **Internal Jira**: URLs that point inside the platform (Docker service names, `localhost`, private addresses) are
  refused, because an agent administrator sets the URL. An operator allows a Jira reachable only on the company network
  with `JIRA_ALLOWED_PRIVATE_HOSTS` (comma-separated host names) on the agent's container.
- **Rate limits**: throttling (429) and gateway errors are retried a few times, honouring `Retry-After`; a wait longer
  than 30 seconds fails at once.
- **Cloud tokens**: scoped API tokens and service accounts are not supported yet, because they only answer at
  Atlassian's API gateway instead of the site URL.
