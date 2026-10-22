"""Seeds a Jira Cloud or Jira Data Center site with the issues the Jira structured source (#1954) is tested against.

Run it by path from ``packages/pipeline``, which keeps it from importing the playground's Dagster definitions:

    uv run python playground/jira_seed/seed_jira.py cases
    uv run python playground/jira_seed/seed_jira.py --env-file ~/.jira-seed/cloud.env seed --projects ENG,SD

The cases live in ``scenarios.yaml`` beside this file; README.md walks through a full test.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import requests
import yaml
from pydantic import BaseModel, Field

SEED_LABEL = "aihub-seed"
RELEASE_LABEL = "aihub-case-release"
_SCENARIOS = Path(__file__).with_name("scenarios.yaml")
_RELEASE_TICKETS = Path(__file__).with_name("release_tickets.yaml")
_BULK_BATCH = 50
_STATUS_CATEGORIES = {"in_progress": "indeterminate", "done": "done"}
_TYPE_PREFERENCES = {
    "task": ["Task", "Story", "Service Request", "Service request"],
    "story": ["Story", "Task"],
    "bug": ["Bug", "Incident", "Problem"],
    "improvement": ["Improvement", "New Feature", "Story", "Task"],
}
_INTERNAL_COMMENT = {"key": "sd.public.comment", "value": {"internal": True}}
_PREFERRED_ROLES = ["Administrators", "Administrator", "Developers", "Member"]
_FILLER = (
    "The ingestion pipeline splits long documents into chunks before it embeds them, so this paragraph only exists "
    "to make the description long enough to need several of them. It repeats on purpose."
)


class SeedComment(BaseModel):
    body: Annotated[str, Field(description="Wiki markup; {me} becomes a mention of the seeding account.")]
    restricted: Annotated[bool, Field(description="Visible to one project role only.")] = False
    internal: Annotated[
        bool, Field(description="An agents-only comment; only a service management space has them.")
    ] = False


class SeedIssue(BaseModel):
    """One test case: the issue to create and what the synced file should then show."""

    case: Annotated[str, Field(pattern=r"^[a-z0-9-]+$", description="Case id, also a label on the issue.")]
    type: Annotated[Literal["task", "story", "bug", "subtask"], Field(description="Kind of issue type.")] = "task"
    summary: Annotated[str, Field(max_length=255)]
    description: Annotated[
        str | list[str],
        Field(
            description="Wiki markup; {me} becomes a mention. A list is joined by blank lines, which end a wiki list "
            "or table; the YAML formatter strips blank lines inside one block."
        ),
    ] = ""
    filler_paragraphs: Annotated[int, Field(ge=0, description="Paragraphs written before the description.")] = 0
    priority: str | None = None
    labels: list[str] = []
    components: list[str] = []
    fix_versions: list[str] = []
    status: Annotated[Literal["in_progress", "done"] | None, Field(description="Status category to move to.")] = None
    comments: list[SeedComment] = []
    generated_comments: Annotated[int, Field(ge=0, description="Numbered comments added after `comments`.")] = 0
    parent_case: Annotated[str | None, Field(description="Case of the parent issue, for a sub-task.")] = None
    expect: Annotated[str, Field(description="What the synced file should show; printed for the tester.")]

    @property
    def case_label(self) -> str:
        return f"aihub-case-{self.case}"

    def jira_labels(self) -> list[str]:
        return [SEED_LABEL, self.case_label, *self.labels]

    def text(self, mention: str) -> str:
        filler = [f"Paragraph {number}. {_FILLER}" for number in range(1, self.filler_paragraphs + 1)]
        blocks = [self.description] if isinstance(self.description, str) else self.description
        return "\n\n".join([*filler, *(block.strip().replace("{me}", mention) for block in blocks)]).strip()

    def all_comments(self) -> list[SeedComment]:
        count = self.generated_comments
        return [*self.comments, *(SeedComment(body=f"Comment {n} of {count}.") for n in range(1, count + 1))]


class SeedScenario(BaseModel):
    issues: list[SeedIssue]

    @classmethod
    def load(cls, path: Path = _SCENARIOS) -> Self:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def selected(self, only: set[str] | None) -> list[SeedIssue]:
        """Parents first, so a sub-task finds the key of the issue it belongs to."""
        unknown = (only or set()) - {issue.case for issue in self.issues}
        if unknown:
            raise RuntimeError(f"Unknown case(s): {', '.join(sorted(unknown))}. Run `cases` to list them.")
        chosen = [issue for issue in self.issues if not only or issue.case in only]
        return sorted(chosen, key=lambda issue: issue.parent_case is not None)


class ReleaseTicketText(BaseModel):
    summary: Annotated[str, Field(description="Summary template; {area} becomes a product area.")]
    description: Annotated[list[str], Field(description="Wiki-markup blocks, joined by blank lines.")]


class ReleaseTickets(BaseModel):
    """What the tickets of a seeded release say, for the release-notes agent (#1889): each ticket takes the next of
    the requested kinds, and one of that kind's templates with a product area filled in."""

    areas: list[str]
    kinds: dict[str, list[ReleaseTicketText]]

    @classmethod
    def load(cls, path: Path = _RELEASE_TICKETS) -> Self:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def ticket(self, number: int, kinds: list[str]) -> tuple[str, str, str]:
        """Kind, summary and description of ticket ``number`` (from 0). The area changes every round of kinds and
        the template every round of areas, so no two of the first few dozen tickets of a kind read the same. The
        area is filled in by replacement, since a wiki ``{{monospace}}`` would not survive ``str.format``."""
        unknown = set(kinds) - set(self.kinds)
        if unknown:
            raise RuntimeError(
                f"Unknown release ticket kind(s): {', '.join(sorted(unknown))}; use {sorted(self.kinds)}."
            )
        kind = kinds[number % len(kinds)]
        round_number = number // len(kinds)
        templates = self.kinds[kind]
        template = templates[(round_number // len(self.areas)) % len(templates)]
        area = self.areas[round_number % len(self.areas)]
        summary = template.summary.replace("{area}", area)
        description = "\n\n".join(block.replace("{area}", area) for block in template.description)
        return kind, summary[:1].upper() + summary[1:], description


class JiraSite:
    """One signed-in connection to a Jira site, authenticated the way the adapter does: Cloud with the account e-mail
    and an API token, Data Center with a personal access token."""

    def __init__(self, base_url: str, deployment: Literal["cloud", "data_center"], email: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.deployment = deployment
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        if deployment == "cloud":
            self.session.auth = (email, token)
        else:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.me: dict[str, Any] = self.call("GET", "/rest/api/2/myself")

    @classmethod
    def from_environment(cls, env_file: Path | None) -> Self:
        """``JIRA_URL``, ``JIRA_DEPLOYMENT`` (cloud | data_center), ``JIRA_EMAIL`` (Cloud) and ``JIRA_TOKEN``, read
        from the env file when given, else from the environment. One env file per site keeps tokens out of the
        shell history and makes switching sites one flag."""
        values = {**os.environ, **(cls._read_env_file(env_file) if env_file else {})}
        deployment = values.get("JIRA_DEPLOYMENT", "cloud")
        required = ["JIRA_URL", "JIRA_TOKEN", *(["JIRA_EMAIL"] if deployment == "cloud" else [])]
        missing = [name for name in required if not values.get(name)]
        if missing or deployment not in ("cloud", "data_center"):
            raise RuntimeError(f"Set {', '.join(missing) or 'JIRA_DEPLOYMENT to cloud or data_center'}.")
        return cls(values["JIRA_URL"], deployment, values.get("JIRA_EMAIL", ""), values["JIRA_TOKEN"])

    def my_groups(self) -> list[str]:
        groups = self.call("GET", "/rest/api/2/myself", params={"expand": "groups"}).get("groups", {})
        return [group["name"] for group in groups.get("items", [])]

    def is_me_or_my_group(self, actor: dict[str, Any], groups: list[str]) -> bool:
        """A project role actor that is this account, or a group it belongs to (Cloud names users by account id,
        Data Center by user name)."""
        if actor.get("type") == "atlassian-user-role-actor":
            if self.deployment == "cloud":
                return (actor.get("actorUser") or {}).get("accountId") == self.me["accountId"]
            return actor.get("name") == self.me["name"]
        return ((actor.get("actorGroup") or {}).get("name") or actor.get("name")) in groups

    def is_me(self, user: dict[str, Any] | None) -> bool:
        if not user:
            return False
        if self.deployment == "cloud":
            return user.get("accountId") == self.me["accountId"]
        return user.get("name") == self.me["name"]

    def who(self, user: dict[str, Any] | None) -> str:
        if not user:
            return "nobody"
        return f"{user.get('displayName', '?')}{' (you)' if self.is_me(user) else ''}"

    @property
    def mention(self) -> str:
        return f"[~accountid:{self.me['accountId']}]" if self.deployment == "cloud" else f"[~{self.me['name']}]"

    @property
    def myself(self) -> dict[str, str]:
        return {"accountId": self.me["accountId"]} if self.deployment == "cloud" else {"name": self.me["name"]}

    def call(self, method: str, path: str, **kwargs: Any) -> Any:
        """A REST call; rate limiting is waited out, any other error stops the tool with Jira's own message."""
        for attempt in range(6):
            response = self.session.request(method, f"{self.base_url}{path}", timeout=60, **kwargs)
            if response.status_code != 429:
                break
            time.sleep(float(response.headers.get("Retry-After", 2**attempt)))
        if not response.ok:
            raise RuntimeError(f"{method} {path} -> {response.status_code} {response.reason}: {response.text[:600]}")
        return response.json() if response.content else None

    def search(self, jql: str, fields: str = "summary,status,issuetype,labels") -> list[dict[str, Any]]:
        if self.deployment == "cloud":
            return self._search_cloud(jql, fields)
        found: list[dict[str, Any]] = []
        while True:
            params = {"jql": jql, "fields": fields, "startAt": len(found), "maxResults": 100}
            page = self.call("GET", "/rest/api/2/search", params=params)
            found.extend(page["issues"])
            if not page["issues"] or len(found) >= page["total"]:
                return found

    def _search_cloud(self, jql: str, fields: str) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        params: dict[str, Any] = {"jql": jql, "fields": fields, "maxResults": 100}
        while True:
            page = self.call("GET", "/rest/api/2/search/jql", params=params)
            found.extend(page.get("issues", []))
            if page.get("isLast", True) or not page.get("nextPageToken"):
                return found
            params["nextPageToken"] = page["nextPageToken"]

    @staticmethod
    def _read_env_file(path: Path) -> dict[str, str]:
        lines = path.expanduser().read_text(encoding="utf-8").splitlines()
        pairs = [line.split("=", 1) for line in lines if "=" in line and not line.lstrip().startswith("#")]
        return {key.strip().removeprefix("export "): value.strip().strip("'\"") for key, value in pairs}


class JiraSeeder:
    """Creates, changes and removes the test issues in a project.

    Fields the project's create screen does not offer (a team-managed project has no components, a Data Center
    priority scheme may lack "High") are skipped and reported rather than failing the run, so one scenario file
    serves any site.
    """

    def __init__(self, site: JiraSite):
        self.site = site
        self._types: dict[str, list[dict[str, Any]]] = {}
        self._chosen_types: dict[tuple[str, str], dict[str, Any] | None] = {}
        self._fields: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
        self._project_types: dict[str, str] = {}
        self._restrictions: dict[str, dict[str, str] | None] = {}

    def seed(self, project: str, issues: list[SeedIssue]) -> list[tuple[SeedIssue, str]]:
        existing = self._ensure_named(project, "components", {name for i in issues for name in i.components})
        existing |= self._ensure_named(project, "versions", {name for i in issues for name in i.fix_versions})
        created = self._present_cases(project)
        for issue in issues:
            if issue.case in created:
                print(f"  {created[issue.case]:<10} {issue.case} (already there; `clean` for a fresh start)")
                continue
            key = self._create(project, issue, existing, created)
            if key is None:
                continue
            created[issue.case] = key
            self._add_comments(project, key, issue)
            if issue.status:
                self._transition(key, issue.status)
            print(f"  {key:<10} {issue.case}")
        return [(issue, created[issue.case]) for issue in issues if issue.case in created]

    def bulk(self, project: str, count: int) -> None:
        """Many small issues, to run the search across several pages."""
        type_id = self._issue_type(project, "task")["id"]
        for start in range(0, count, _BULK_BATCH):
            numbers = range(start + 1, min(start + _BULK_BATCH, count) + 1)
            updates = [
                {
                    "fields": {
                        "project": {"key": project},
                        "issuetype": {"id": type_id},
                        "summary": f"Bulk issue {number} of {count}",
                        "labels": [SEED_LABEL, "aihub-case-bulk"],
                    }
                }
                for number in numbers
            ]
            result = self.site.call("POST", "/rest/api/2/issue/bulk", json={"issueUpdates": updates})
            if result.get("errors"):
                raise RuntimeError(f"Bulk create failed: {result['errors']}")
            for created in result["issues"]:
                self._assign_to_me(created["key"])
            print(f"  created bulk issues {numbers.start}-{numbers.stop - 1}")

    def release(self, project: str, version: str, count: int, kinds: list[str], tickets: ReleaseTickets) -> None:
        """A fix version holding ``count`` tickets of mixed types, worded like real ones, so a release-notes agent
        has a release of a realistic size to write about. The version is created first, because Data Center refuses
        a search naming a version that does not exist."""
        if version not in self._ensure_named(project, "versions", {version}):
            raise RuntimeError(f"Version {version} does not exist in {project} and could not be created.")
        present = self.site.search(f'project = "{project}" AND labels = "{RELEASE_LABEL}" AND fixVersion = "{version}"')
        if present:
            print(f"  release {version}: {len(present)} tickets already there (`clean` for a fresh start)")
            return
        for start in range(0, count, _BULK_BATCH):
            numbers = range(start, min(start + _BULK_BATCH, count))
            updates = [{"fields": self.release_fields(project, version, tickets.ticket(n, kinds))} for n in numbers]
            result = self.site.call("POST", "/rest/api/2/issue/bulk", json={"issueUpdates": updates})
            if result.get("errors"):
                raise RuntimeError(f"Bulk create failed: {result['errors']}")
            for created in result["issues"]:
                self._assign_to_me(created["key"])
            print(f"  created release {version} tickets {numbers.start + 1}-{numbers.stop}")

    def release_fields(self, project: str, version: str, ticket: tuple[str, str, str]) -> dict[str, Any]:
        kind, summary, description = ticket
        return {
            "project": {"key": project},
            "issuetype": {"id": self._issue_type(project, kind)["id"]},
            "summary": summary,
            "description": description,
            "labels": [SEED_LABEL, RELEASE_LABEL],
            "fixVersions": [{"name": version}],
        }

    def edit(self, project: str) -> str:
        key = self._case_key(project, "edit-me")
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.site.call("PUT", f"/rest/api/2/issue/{key}", json={"fields": {"summary": f"Edit me (edited {stamp})"}})
        self.site.call(
            "POST", f"/rest/api/2/issue/{key}/comment", json={"body": f"Edited by the seed tool at {stamp}."}
        )
        return key

    def delete(self, project: str) -> str:
        key = self._case_key(project, "delete-me")
        self.site.call("DELETE", f"/rest/api/2/issue/{key}")
        return key

    def check(self, project: str) -> list[str]:
        """Read-only: who a new issue would land on by default, and every seeded issue whose assignee or reporter is
        not the seeding account."""
        details = self.site.call("GET", f"/rest/api/2/project/{project}")
        default = details.get("assigneeType", "unknown").replace("_", " ").lower()
        print(f"  lead: {self.site.who(details.get('lead'))}; default assignee: {default}")
        hits = self.site.search(f'project = "{project}" AND labels = "{SEED_LABEL}" ORDER BY key', "assignee,reporter")
        others = [
            f"{hit['key']} {role}: {self.site.who(hit['fields'].get(role))}"
            for hit in hits
            for role in ("assignee", "reporter")
            if not self.site.is_me(hit["fields"].get(role))
        ]
        verdict = "not you:" if others else "every one assigned to and reported by you"
        print(f"  {len(hits)} seeded issue(s), {verdict}")
        for line in others:
            print(f"    {line}")
        return others

    def clean(self, project: str) -> list[str]:
        """Deletes every seeded issue, sub-tasks first: deleting a parent takes its sub-tasks along, and a second
        delete would fail. An issue someone else holds is taken over first, because Jira tells the assignee about a
        deletion."""
        hits = self.site.search(f'project = "{project}" AND labels = "{SEED_LABEL}"', "issuetype,assignee")
        ordered = sorted(hits, key=lambda hit: not hit["fields"]["issuetype"].get("subtask", False))
        for hit in ordered:
            if not self.site.is_me(hit["fields"].get("assignee")):
                self._assign_to_me(hit["key"])
            self.site.call("DELETE", f"/rest/api/2/issue/{hit['key']}", params={"deleteSubtasks": "true"})
        return [hit["key"] for hit in ordered]

    def fields_for(self, project: str, issue: SeedIssue, existing: set[str], parent_key: str | None) -> dict[str, Any]:
        type_id = self._issue_type(project, issue.type)["id"]
        offered = self._field_meta(project, type_id)
        fields: dict[str, Any] = {"project": {"key": project}, "issuetype": {"id": type_id}, "summary": issue.summary}
        wanted = {
            "description": issue.text(self.site.mention) or None,
            "labels": issue.jira_labels(),
            "priority": self._allowed(offered, "priority", issue.priority),
            "components": [{"name": name} for name in issue.components if name in existing] or None,
            "fixVersions": [{"name": name} for name in issue.fix_versions if name in existing] or None,
            "parent": {"key": parent_key} if parent_key else None,
        }
        for field, value in wanted.items():
            if value is not None and field in offered:
                fields[field] = value
            elif value is not None:
                print(f"  ! {issue.case}: '{field}' is not on the create screen of {project}; skipped")
        if "assignee" in offered:
            fields["assignee"] = self.site.myself
        return fields

    def _create(self, project: str, issue: SeedIssue, existing: set[str], created: dict[str, str]) -> str | None:
        if self._issue_type(project, issue.type) is None:
            print(f"  ! {issue.case}: {project} has no sub-task issue type; skipped")
            return None
        fields = self.fields_for(project, issue, existing, self._parent_key(project, issue, created))
        key = self.site.call("POST", "/rest/api/2/issue", json={"fields": fields})["key"]
        if "assignee" not in fields:
            self._assign_to_me(key)
        return key

    def _assign_to_me(self, key: str) -> None:
        """Every seeded issue is the seeding account's own, so no other member is assigned or notified, whatever the
        project's default assignee."""
        self.site.call("PUT", f"/rest/api/2/issue/{key}/assignee", json=self.site.myself)

    def _parent_key(self, project: str, issue: SeedIssue, created: dict[str, str]) -> str | None:
        if issue.parent_case is None:
            return None
        return created.get(issue.parent_case) or self._case_key(project, issue.parent_case)

    def _add_comments(self, project: str, key: str, issue: SeedIssue) -> None:
        for comment in issue.all_comments():
            payload: dict[str, Any] = {"body": comment.body.replace("{me}", self.site.mention)}
            if comment.restricted and self._restriction(project) is None:
                self._skip_restricted(project, issue.case)
                continue
            if comment.restricted:
                payload["visibility"] = self._restriction(project)
            if comment.internal and self.project_type(project) != "service_desk":
                print(f"  ! {issue.case}: {project} is not a service management space; internal comment skipped")
                continue
            if comment.internal:
                payload["properties"] = [_INTERNAL_COMMENT]
            self._post_comment(project, key, issue.case, payload)

    def _post_comment(self, project: str, key: str, case: str, payload: dict[str, Any]) -> None:
        """A site can switch group restrictions off, which only shows when a group-restricted comment is refused."""
        try:
            self.site.call("POST", f"/rest/api/2/issue/{key}/comment", json=payload)
        except RuntimeError as refused:
            if payload.get("visibility", {}).get("type") != "group" or "GROUP_VISIBILITY" not in str(refused):
                raise
            self._restrictions[project] = None
            self._skip_restricted(project, case)

    @staticmethod
    def _skip_restricted(project: str, case: str) -> None:
        print(
            f"  ! {case}: you are in no project role of {project}, and this site allows no group restrictions; "
            f"restricted comment skipped. Add yourself to a role of {project} to test it."
        )

    def _transition(self, key: str, status: str) -> None:
        category = _STATUS_CATEGORIES[status]
        transitions = self.site.call("GET", f"/rest/api/2/issue/{key}/transitions")["transitions"]
        target = next((t for t in transitions if t["to"]["statusCategory"]["key"] == category), None)
        if target is None:
            print(f"  ! {key}: no transition into a '{status}' status; left as is")
            return
        try:
            self.site.call("POST", f"/rest/api/2/issue/{key}/transitions", json={"transition": {"id": target["id"]}})
        except RuntimeError as refused:
            # A service management "Resolve" transition may ask for fields on a screen; the status is a nice-to-have.
            print(f"  ! {key}: transition '{target['name']}' refused, left as is: {refused}")

    def _present_cases(self, project: str) -> dict[str, str]:
        """Cases already seeded in the project, so a seed stopped half way can simply be run again."""
        hits = self.site.search(f'project = "{project}" AND labels = "{SEED_LABEL}"', "labels")
        return {
            label.removeprefix("aihub-case-"): hit["key"]
            for hit in hits
            for label in hit["fields"].get("labels", [])
            if label.startswith("aihub-case-")
        }

    def _case_key(self, project: str, case: str) -> str:
        hits = self.site.search(f'project = "{project}" AND labels = "aihub-case-{case}"', "summary")
        if len(hits) != 1:
            raise RuntimeError(f"Expected one '{case}' issue in {project}, found {len(hits)}; run seed --only {case}.")
        return hits[0]["key"]

    def _issue_type(self, project: str, kind: str) -> dict[str, Any] | None:
        """The project's type for a kind of case. A space without the preferred names (a service management space has
        no Bug or Story) gets its first standard type; only a missing sub-task type means the case cannot be created."""
        if (project, kind) not in self._chosen_types:
            self._chosen_types[(project, kind)] = self._choose_type(project, kind)
        return self._chosen_types[(project, kind)]

    def _choose_type(self, project: str, kind: str) -> dict[str, Any] | None:
        if project not in self._types:
            page = self.site.call("GET", f"/rest/api/2/issue/createmeta/{project}/issuetypes")
            self._types[project] = self._listed(page)
        types = self._types[project]
        if kind == "subtask":
            return next((t for t in types if t.get("subtask")), None)
        standard = {t["name"]: t for t in types if not t.get("subtask")}
        if not standard:
            raise RuntimeError(f"{project} offers no issue type to create.")
        preferred = next((standard[name] for name in _TYPE_PREFERENCES[kind] if name in standard), None)
        if preferred is None:
            preferred = next(iter(standard.values()))
            print(f"  ! {project} has no {' / '.join(_TYPE_PREFERENCES[kind])}; '{kind}' cases use {preferred['name']}")
        return preferred

    def _field_meta(self, project: str, type_id: str) -> dict[str, dict[str, Any]]:
        if (project, type_id) not in self._fields:
            page = self.site.call("GET", f"/rest/api/2/issue/createmeta/{project}/issuetypes/{type_id}")
            self._fields[(project, type_id)] = {entry["fieldId"]: entry for entry in self._listed(page)}
        return self._fields[(project, type_id)]

    @staticmethod
    def _listed(page: dict[str, Any]) -> list[dict[str, Any]]:
        """The one list in a create-metadata page: Cloud and Data Center name it differently (``issueTypes``,
        ``fields``, ``values``) and nothing else in the page is a list."""
        return next((value for value in page.values() if isinstance(value, list)), [])

    @staticmethod
    def _allowed(offered: dict[str, dict[str, Any]], field: str, name: str | None) -> dict[str, str] | None:
        if name is None:
            return None
        allowed = [value["name"] for value in offered.get(field, {}).get("allowedValues", [])]
        match = next((value for value in allowed if value.lower() == name.lower()), None)
        if match is None:
            print(f"  ! '{name}' is not an allowed {field} ({allowed}); skipped")
        return {"name": match} if match else None

    def project_type(self, project: str) -> str:
        if project not in self._project_types:
            self._project_types[project] = self.site.call("GET", f"/rest/api/2/project/{project}")["projectTypeKey"]
        return self._project_types[project]

    def _restriction(self, project: str) -> dict[str, str] | None:
        """Jira restricts a comment only to a project role or a group the author is in. The seeder looks for one and
        never adds anyone to a role."""
        if project not in self._restrictions:
            self._restrictions[project] = self._find_restriction(project)
        return self._restrictions[project]

    def _find_restriction(self, project: str) -> dict[str, str] | None:
        groups = self.site.my_groups()
        roles = self.site.call("GET", f"/rest/api/2/project/{project}/role")
        ranked = sorted(roles, key=lambda name: _PREFERRED_ROLES.index(name) if name in _PREFERRED_ROLES else 99)
        for name in ranked:
            role_id = roles[name].rstrip("/").rsplit("/", 1)[-1]
            actors = self.site.call("GET", f"/rest/api/2/project/{project}/role/{role_id}").get("actors", [])
            if any(self.site.is_me_or_my_group(actor, groups) for actor in actors):
                return {"type": "role", "value": name}
        return {"type": "group", "value": groups[0]} if groups else None

    def _ensure_named(self, project: str, kind: Literal["components", "versions"], names: set[str]) -> set[str]:
        """Components and versions must exist before an issue names them. A project that refuses to create them
        (team-managed, or no admin rights) just gets issues without them."""
        present = {entry["name"] for entry in self.site.call("GET", f"/rest/api/2/project/{project}/{kind}")}
        endpoint = "/rest/api/2/component" if kind == "components" else "/rest/api/2/version"
        for name in sorted(names - present):
            try:
                self.site.call("POST", endpoint, json={"name": name, "project": project})
                present.add(name)
            except RuntimeError as refused:
                print(f"  ! could not create {kind[:-1]} '{name}' in {project}: {refused}")
        return present


class JiraSeedCli:
    """``cases``, ``seed``, ``list``, ``edit``, ``delete`` and ``clean``; see the module docstring."""

    @staticmethod
    def parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("--env-file", type=Path, help="File with JIRA_URL, JIRA_DEPLOYMENT, JIRA_EMAIL, JIRA_TOKEN")
        commands = parser.add_subparsers(dest="command", required=True)
        commands.add_parser("cases", help="List the test cases and what each should show after a sync")
        for name, help_text in [
            ("seed", "Create the test issues"),
            ("list", "List the seeded issues"),
            ("check", "Read-only: the default assignee, and seeded issues not assigned to or reported by you"),
            ("edit", "Change the edit-me issue (summary and a new comment)"),
            ("delete", "Delete the delete-me issue"),
            ("clean", "Delete every seeded issue"),
        ]:
            command = commands.add_parser(name, help=help_text)
            command.add_argument("--projects", required=True, help="Comma-separated project keys, e.g. ENG,SD")
            if name == "seed":
                command.add_argument("--only", help="Comma-separated cases to create, e.g. delete-me")
                command.add_argument("--bulk", type=int, default=0, help="Also create this many small issues")
                command.add_argument("--release", help="Also create a fix version holding many typed tickets, e.g. 2.0")
                command.add_argument("--release-count", type=int, default=120, help="Tickets in the release")
                command.add_argument(
                    "--release-types", default="bug,story,improvement,task", help="Kinds of the release's tickets"
                )
        return parser

    @classmethod
    def run(cls, argv: list[str]) -> None:
        arguments = cls.parser().parse_args(argv)
        scenario = SeedScenario.load()
        if arguments.command == "cases":
            cls._print_cases(scenario.issues)
            return
        site = JiraSite.from_environment(arguments.env_file)
        print(f"Signed in to {site.base_url} ({site.deployment}) as {site.me.get('displayName')}")
        seeder = JiraSeeder(site)
        for project in [key.strip().upper() for key in arguments.projects.split(",") if key.strip()]:
            print(f"{project} ({seeder.project_type(project)} space):")
            cls._run_in(seeder, project, arguments, scenario)

    @classmethod
    def _run_in(cls, seeder: JiraSeeder, project: str, arguments: argparse.Namespace, scenario: SeedScenario) -> None:
        match arguments.command:
            case "seed":
                only = {case.strip() for case in arguments.only.split(",")} if arguments.only else None
                seeder.seed(project, scenario.selected(only))
                if arguments.bulk:
                    seeder.bulk(project, arguments.bulk)
                if arguments.release:
                    kinds = [kind.strip() for kind in arguments.release_types.split(",") if kind.strip()]
                    seeder.release(project, arguments.release, arguments.release_count, kinds, ReleaseTickets.load())
            case "list":
                cls._print_seeded(seeder.site, project)
            case "check":
                seeder.check(project)
            case "edit":
                print(f"  edited {seeder.edit(project)}")
            case "delete":
                print(f"  deleted {seeder.delete(project)}")
            case "clean":
                print(f"  deleted {len(seeder.clean(project))} seeded issues")

    @staticmethod
    def _print_seeded(site: JiraSite, project: str) -> None:
        for hit in site.search(f'project = "{project}" AND labels = "{SEED_LABEL}" ORDER BY key'):
            fields = hit["fields"]
            case = next((label for label in fields["labels"] if label.startswith("aihub-case-")), "")
            case = case.removeprefix("aihub-case-")
            print(f"  {hit['key']:<10} {case:<20} {fields['status']['name']:<12} {fields['summary']}")

    @staticmethod
    def _print_cases(issues: list[SeedIssue]) -> None:
        for issue in issues:
            print(f"{issue.case} ({issue.type}): {issue.summary}\n    expect: {issue.expect}\n")


if __name__ == "__main__":
    try:
        JiraSeedCli.run(sys.argv[1:])
    except RuntimeError as failure:
        sys.exit(f"error: {failure}")
