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
| `… seed --projects ENG --only plain --release 2.0`           | Adds fix version 2.0 with 120 described bug/story/improvement/task tickets (release notes) |
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
7. Check the failures, each a failed run with nothing removed: a wrong token ("Jira rejected the credentials …"), a
   project key that does not exist ("Jira project … does not exist, or … cannot see it.") and an invalid JQL clause
   ("The JQL clause is invalid: …").
8. Run the sync again with nothing changed: only the issues of the last five minutes before the newest change are
   fetched (`Rows loaded` is small, `Files written: 0`).

## 5. Checking Jira Data Center

The Data Center path was checked live against Jira Software Data Center 10.3.26 on a local instance (§4 steps 1–4, 7 and
8). Internal comments of Jira Service Management were not, since that instance had no Service Management: they are
covered only by tests on responses shaped after its REST API
(`swiss_ai_hub/pipeline/source_pipelines/jira/tests/data_center`). To check it again on a throwaway local instance:

1. Jira 10 has no built-in evaluation database, so it runs next to a PostgreSQL. Put the database settings in an env
   file outside the repository:

   ```bash
   # ~/.jira-seed/jira-dc-docker.env
   POSTGRES_USER=jira
   POSTGRES_DB=jira
   POSTGRES_PASSWORD=<choose one>
   POSTGRES_INITDB_ARGS=--encoding=UTF8 --lc-collate=C --lc-ctype=C
   ATL_DB_TYPE=postgres72
   ATL_DB_DRIVER=org.postgresql.Driver
   ATL_JDBC_URL=jdbc:postgresql://jira-dc-db:5432/jira
   ATL_JDBC_USER=jira
   ATL_JDBC_PASSWORD=<the same>
   JVM_MAXIMUM_MEMORY=2048m
   ```

2. Start both. Jira needs about 3 GB of memory, so stop heavy dev-stack services first if the machine is short. Port
   8090 is often taken by an agent. Use 10.3: the public test licences are reported to be refused by Jira 11.

   ```bash
   docker network create jira-dc-net
   docker run -d --name jira-dc-db --network jira-dc-net --env-file ~/.jira-seed/jira-dc-docker.env -v jira-dc-db:/var/lib/postgresql/data postgres:15-alpine
   docker run -d --name jira-dc --network jira-dc-net --env-file ~/.jira-seed/jira-dc-docker.env -v jira-dc-data:/var/atlassian/application-data/jira -p 8093:8080 atlassian/jira-software:10.3
   ```

3. Open http://localhost:8093 and complete the setup wizard in one browser session (it keeps its progress there): *I'll
   set it up myself*, private mode, base URL `http://localhost:8093`, then the 10-user *Jira Software Data Center* key
   from
   [Atlassian's timebomb licences](https://developer.atlassian.com/platform/marketplace/timebomb-licenses-for-testing-server-apps/),
   an admin account, and no e-mail. The licence expires three hours after Jira starts; restarting the container starts
   the three hours again.

4. Create two projects, `ENG` and `SD`. To check internal comments, `SD` must be a *Jira Service Management* project,
   which needs that app and its timebomb key as well; without it, use a second software project. Over REST, Data Center
   accepts the template `com.pyxis.greenhopper.jira:gh-scrum-template`, not the Cloud template keys.

5. Create a personal access token: profile → *Personal Access Tokens*. Over REST (`POST /rest/pat/latest/tokens`), send
   basic auth without a session cookie, or Jira answers 403. Put the token in `~/.jira-seed/dc.env` (see §1), then
   `seed --projects ENG,SD` with `--env-file ~/.jira-seed/dc.env`.

6. Create a knowledge database with the Jira source, edition *Jira Data Center*, URL `http://localhost:8093`, the token
   and both project keys, and work through §4. On a service management project, the `internal-comment` case must show
   the public reply but never the internal one.

7. Remove the instance afterwards:

   ```bash
   docker rm -f jira-dc jira-dc-db
   ```

   ```bash
   docker volume rm jira-dc-data jira-dc-db
   ```

   ```bash
   docker network rm jira-dc-net
   ```

If a live response differs from the recorded ones, update the files under `tests/data_center` from the live instance so
the tests follow the real API.
