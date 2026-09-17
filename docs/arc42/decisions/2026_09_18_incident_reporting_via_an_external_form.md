# Incident Reports Are Collected by an External Form the Platform Only Links To

## Context

Dev and QC receive bug reports that cannot be investigated. A report arrives as a sentence in a chat message or a
forwarded screenshot, and the facts that decide whether it can be reproduced — which tenant, which release, which page,
which conversation — are the ones the reporter does not know to include. Asking for them afterwards costs a round trip
per field, and by then the user has moved on.

Every one of those facts is already in the browser when the user notices the problem. The tenant is in the route, the
version is in the runtime config, the conversation id arrives from the chat pipe as each message streams. Nothing about
collecting them requires the user to know anything.

What they get collected *into* is the open question. The platform has no incident domain: no entity, no endpoint, no
notification path — `NotificationEntity` exists but nothing in the codebase writes one — and no outbound mail. Support
for this product is not run by the platform team in any case; it is run by whoever operates a deployment, with the
tooling they already have.

## Decision Drivers

1. **The reporter should only describe what went wrong.** Every field the platform can know, the platform fills in.
2. **Whoever answers reports should own the form.** Adding a question must not require a platform release.
3. **A deployment that has no support desk must be unaffected.** This is a self-hosted product; the affordance cannot
   assume a form exists.
4. **Leaving the platform's trust boundary must be visible.** Data sovereignty is the product's premise, so sending
   incident data to a third party is a decision the deployment makes and the reporter sees — not a side effect.
5. **The platform must not become a ticketing system.** That path ends in assignment, status, notification and
   escalation, none of which the product is for.

## Decision

The platform contributes an affordance and a context; it does not collect, store, or route reports.

A deployment sets `INCIDENT_FORM_URL_TEMPLATE` to the URL of an externally hosted form, carrying `{placeholders}` for
the facts the UI knows: tenant, version, page URL, reporter name and email, browser, date and time, and the conversation
and model the report is about. The UI substitutes them, shows the reporter what is about to travel with the report, and
opens the form. Unset — the default — there is no button and the UI is exactly as it was.

The form itself is Microsoft Forms for the first deployment, but nothing in the platform knows that. The template is an
opaque URL, so the same mechanism serves any provider that accepts prefill by query string.

## Alternatives Considered

1. **An in-house form, stored in the platform and delivered by Apprise or Microsoft Graph.** It is the only option that
   makes the tenant and reporter authoritative rather than advisory, and the only one that accepts attachments from
   every user. Rejected on drivers 2 and 5: the form's questions would live in `packages/core`, so QC could not change
   one without a release, and having stored a report the platform would immediately owe its reader a way to list,
   assign and close it.

2. **Link to a GitHub issue form.** The definition lives outside the platform and the result is a real ticket, which
   drivers 2 and 5 both favour. Rejected because AI Hub users have accounts in AI Hub only: GitHub issue forms render
   solely for signed-in users with access to the repository.

3. **A form hosted by a self-hosted form tool (n8n, Formbricks).** Satisfies every driver including attachments, and
   n8n is already named in the platform's context as an integration target. Rejected for now as a second piece of
   infrastructure to run for one button; it remains the exit if Forms' limits bite.

4. **Feed the existing thumbs-down in the chat UI.** Already exists and costs nothing, but it carries a reason tag and
   a comment — no steps to reproduce, no expected result, no impact. It answers a different question and stays as it is.

## Consequences

**Attachments do not travel with the report.** Microsoft Forms offers its file-upload question only to respondents
signed in to the form owner's organisation, and AI Hub users are not. The form asks for a link instead, and the
conversation id covers the common case, because a file the user already sent in chat is in the platform's own storage.
A deployment that needs true attachments has to change providers, not settings.

**Prefilled values are advisory.** The respondent can edit any of them, and an anonymous form records no identity. The
conversation id is the field that can be checked against the platform, so it is the one to trust.

**The form and the template are coupled by opaque ids.** Microsoft generates a parameter name per question, and editing
the form can change them. Prefill then stops silently: the form still opens, the fields are simply empty. Whoever edits
the form re-generates the pre-filled link and hands the operator a new template; a smoke test after any form change is
part of owning it.

**Incident data leaves the sovereign boundary.** For the deployments this is enabled on, that is the operator's
decision, taken per deployment, with the reporter told before each report. Deployments that will not accept it leave the
variable empty and lose only the button.

**There is no status for the reporter.** A report is a one-way message; whoever answers it does so out of band. If that
becomes unacceptable, it is the signal that alternative 1 was the right answer after all.
