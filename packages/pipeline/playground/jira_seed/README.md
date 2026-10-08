# Jira seed tool

Fills a Jira site with the issues the Jira structured source (#1954) is tested against, and changes or removes them
again to test the sync. One scenario file (`scenarios.yaml`) serves Jira Cloud and Jira Data Center: fields a project's
create screen does not offer are skipped and reported, so the same cases run on any site.

Every seeded issue is reported by and assigned to the account that seeds it, whatever the project's default assignee, so
no other member is assigned, mentioned or notified. It carries the labels `aihub-seed` and `aihub-case-<case>`; issues
you created by hand are never touched. Restricted comments go to a project role or group you are in yourself (Jira
allows no other); nobody is added to a role. Without either, the restricted comment is skipped and reported. `seed`
skips cases that already exist, so a run that stopped half way can simply be run again.

## 1. Describe the site

One env file per site, outside the repository:

```bash
# ~/.jira-seed/cloud.env
JIRA_URL=https://acme.atlassian.net
JIRA_DEPLOYMENT=cloud
JIRA_EMAIL=you@acme.com
JIRA_TOKEN=<API token without scopes, from https://id.atlassian.com/manage-profile/security/api-tokens>
```

```bash
# ~/.jira-seed/dc.env
JIRA_URL=https://jira.acme.ch/jira
JIRA_DEPLOYMENT=data_center
JIRA_TOKEN=<personal access token: profile → Personal Access Tokens>
```

The account needs to create issues in the projects. Creating components and versions also needs project admin rights;
without them those fields are skipped.

## 2. Pick the projects

Use two projects, so the database gets two namespaces: our test site seeds its software space (ENG) and its service
management space. Any project works; the seeder adapts and says what it skipped:

- **Issue types:** a space without Bug or Story (a service management space) uses its first standard type instead.
- **Fields:** a team-managed space has no components or versions; a priority scheme may lack High or Low.
- **Sub-tasks:** skipped where the space has no sub-task type.
- **Internal comments:** only a service management space has them; elsewhere the `internal-comment` case gets its public
  reply only.

## 3. Run it

From `packages/pipeline`:

| Command                                                      | What it does                                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| `uv run python playground/jira_seed/seed_jira.py cases`      | Lists the cases and what each should show after a sync                                     |
| `… --env-file ~/.jira-seed/cloud.env seed --projects ENG,SD` | Creates every case in both projects                                                        |
| `… seed --projects ENG --only delete-me`                     | Creates the named cases only                                                               |
| `… seed --projects ENG --only plain --bulk 120`              | Adds 120 small issues, so a search spans several pages                                     |
| `… list --projects ENG,SD`                                   | Lists the seeded issues with their case and status                                         |
| `… check --projects ENG,SD`                                  | Read-only: lead, default assignee, and any seeded issue not assigned to or reported by you |
| `… edit --projects ENG`                                      | Changes the summary of `edit-me` and adds a comment                                        |
| `… delete --projects ENG`                                    | Deletes `delete-me`                                                                        |
| `… clean --projects ENG,SD`                                  | Deletes every seeded issue                                                                 |

## 4. Test the sync

1. Seed, create a knowledge database with the Jira source and both project keys, and run its sync (Dagster job
   `structured_source_sync`, tag `aihub/bucket=<database>`).
2. Check each case against `cases`.
3. Run the sync again: `Files written: 0`.
4. `edit`, sync: one file written. `delete`, sync: that file removed.
5. Set the database's JQL to `issuetype != Bug`, sync: the two bugs of the software space are removed.
6. Move an issue to the other project in Jira (no REST API does this on both editions), sync: the old file is removed
   and a new one is written under the other project.
