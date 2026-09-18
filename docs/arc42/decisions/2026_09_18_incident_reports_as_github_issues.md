# Incident Reports Are Filed as Issues in a Private GitHub Repository

## Context

Dev and QC receive bug reports they cannot investigate. A report arrives as a sentence in a chat message or a forwarded
screenshot, and the facts that decide whether it can be reproduced — which tenant, which release, which page, which
conversation — are exactly the ones the reporter does not know to include. Asking afterwards costs a round trip per
field, and by then the user has moved on.

Every one of those facts is already in the browser at the moment the user notices the problem. The tenant is in the
route, the version in the runtime config, the conversation id arrives from the chat pipe as each message streams.

The platform had no incident domain at all: no entity, no endpoint, no notification path — `NotificationEntity` exists
but nothing writes one — and no outbound mail. So the question was never how to render a form; it was where a submitted
report should end up, and who gets to change the questions.

A first attempt (PR #1908, kept as a reference and not merged) linked out to a Microsoft Form with the context prefilled
into the URL. It works, and it exposed the two limits that decided this design: Microsoft Forms offers its file-upload
question only to respondents signed in to the form owner's organisation — which AI Hub users are not — and everything in
a prefilled URL is editable by the respondent, so nothing in the resulting response can be trusted as identity.

## Decision Drivers

1. **The reporter should only describe what went wrong.** Every field the platform can know, the platform fills in.
2. **Whoever answers reports should own the questions.** Adding one must not require a frontend change.
3. **Attachments must work for every user**, not only for those who happen to share an identity provider with whoever
   owns the form.
4. **A deployment with no support desk must be unaffected.** This is self-hosted software; the affordance cannot assume
   a destination exists.
5. **A report must never become public.** It carries a customer's prompts and screenshots, and publishing those cannot
   be undone.
6. **The platform must not become a ticketing system.** That road ends in assignment, status, notification and
   escalation, none of which this product is for.

## Decision

A report is filed as a GitHub issue in a **private** repository, by a GitHub App, and the form is a **GitHub issue-form
YAML file** that ships with `packages/core`.

The same file is both the questionnaire and the contract. `IssueFormParser` turns it into the platform's own form
elements, so the existing FormKit renderer draws it with no knowledge of incidents, and into a Pydantic model whose JSON
Schema validates a submission — the same arrangement agents get from `ConfigSpecs`, reached from the other direction
because here the form is data a non-programmer edits rather than a model a programmer writes.

Editing a question is editing that YAML file, reviewed as a pull request. Question `id`s double as the prefill keys:
every field of `IncidentContext` names one, and a test fails if that correspondence breaks.

Attachments are **committed into the repository** and linked from the issue body.

Unset — the default — `IncidentSettings.enabled` is false, no client is constructed, and the endpoints answer 404.

## Alternatives Considered

1. **Keep the Microsoft Forms link (PR #1908).** Cheapest by far: no backend at all. Rejected on drivers 3 and 5 —
   attachments are unavailable to the users who need them, and nothing about the response is verifiable.

2. **Link to GitHub's own issue form.** The definition would live in the repository and the result would be a real
   ticket, satisfying drivers 2 and 6 outright. Rejected because AI Hub users have accounts in AI Hub only: GitHub
   renders an issue form solely for signed-in users with access to the repository.

3. **Attach files to the issue the way a person does in the browser.** This is what "attachments in the issue" means to
   anyone who has filed one, so it was the first thing tried. The endpoint behind it
   (`uploads.github.com/user-attachments/assets`) is undocumented and **rejects App installation tokens outright**; only
   an OAuth user token works. Using it would mean holding a machine user's personal token for an unsupported API.
   Committing the file instead reaches the audience through a documented one — at the cost of a click, see the
   attachment consequence below. It remains the only route to a screenshot that renders inline, so a deployment that
   wants that badly enough has to accept the machine-user token.

4. **Store reports in the platform and deliver them by Apprise or Microsoft Graph.** The only option that makes tenant
   and reporter authoritative *and* accepts attachments. Rejected on drivers 2 and 6: the questions would live in
   Python, so QC could not change one without a release, and having stored a report the platform would immediately owe
   its reader a way to list, assign and close it.

5. **A self-hosted form tool (n8n, Formbricks) as the intake.** Satisfies every driver, and n8n is already named in the
   platform's context as an integration target. Rejected as a second piece of infrastructure to run for one button — but
   it remains the exit if GitHub proves the wrong home.

## Consequences

**The questions are editable without touching the frontend, and a bad edit fails loudly.** `IssueFormParser` refuses an
unsupported question type, a missing `id` or `label`, an optionless dropdown and a duplicate `id`; the form is parsed at
**import** time, so a broken definition breaks CI rather than a user's click.

**Attachments are links, not inline images, and they live in git history permanently.** Embedding needs a URL that
serves the bytes, and a private repository has none that lasts: `raw.githubusercontent.com` refuses anonymous requests
outright, and the `download_url` the contents API returns carries a short-lived `?token=` — measured end-to-end, an
embed built from it works the day the report is filed and breaks afterwards, which is worse than a link. So every
attachment, screenshots included, is linked to its page in the repository, which resolves for exactly the people who can
read the repository. Permanence is the other half of the cost: limits are therefore deliberately small (five files, 5 MB
each) and the form says so. A reporter's filename becomes a repository path, so it is reduced to a basename over a known
character set — five traversal shapes are covered by tests.

**Almost nothing in a submission is authoritative.** The reporter can see and correct every prefilled value, which is
what the platform owner asked for, and means an answer read back out of an issue is a claim rather than a fact. Two
lines of the body come from the caller's token instead: who reported it, and from which tenant. Those are the two that
send an investigation to the wrong place when wrong.

**The endpoints authenticate but do not check a service rule.** Every other controller gates on
`aihub.user.service.<name>`; a narrowly scoped role such as `AIHubAgentUser` does not carry it, and being unable to
report a bug because of an access rule is a worse failure than the alternative. There is nothing to protect here — the
endpoints read a static form and write into a repository nobody else can reach.

**Reports leave the sovereign boundary.** For deployments this is enabled on, that is the operator's decision, taken
once by configuring a repository. A misconfiguration that would publish them is the one failure the code refuses:
`ensure_repository_is_private` runs before anything is written, and a public repository disables the feature rather than
filing into it.

**A GitHub outage loses the report the reporter just typed.** Nothing is stored locally first, deliberately — storing it
would create the obligation alternative 4 was rejected for. The dialog keeps its contents so the reporter can retry. If
that becomes unacceptable, it is the signal that alternative 4 was right after all.

**There is no status for the reporter.** They have no GitHub account, so they are given a reference and an issue number,
not a link they cannot open. Whoever answers does so out of band, by the contact address in the report.

**Multipart upload arrives at the API.** Every other upload in the platform hands the browser a presigned S3 URL; the
destination here is GitHub, which issues no such URL, so these bytes pass through the API. It is the one deliberate
deviation from that pattern.
