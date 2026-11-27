"""Write the body of the issue (or comment) that records a failed nightly external-tests run.

A failing nightly on main has no PR of its own, so the body names the two things a reader needs to triage it: the PRs
merged since the last green nightly (what changed) and the PR that last changed each failing test (who owns it).
Run with `uv run --no-project --with pydantic python .github/scripts/nightly_failure_report.py`; needs `gh`.
"""

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ElementTree
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

WORKFLOW_FILE = "external-tests.yml"
REPORT_SUFFIX = "-pytest-report"
MESSAGE_LIMIT = 200
PR_NUMBER = re.compile(r"\(#(\d+)\)$")


class FailedTest(BaseModel):
    module: str
    test_id: str
    file: str | None
    message: str


class ChangeRef(BaseModel):
    sha: str
    title: str
    author: str | None
    pr: int | None
    files: list[str] = []

    @property
    def label(self) -> str:
        return f"#{self.pr}" if self.pr else f"`{self.sha[:9]}`"


class NightlyFailureReport:
    @staticmethod
    def gh_json(*path: str) -> dict | list:
        result = subprocess.run(["gh", "api", *path], check=True, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout)

    @staticmethod
    def first_line(text: str) -> str:
        return text.strip().splitlines()[0] if text.strip() else ""

    @classmethod
    def change_ref(cls, commit: dict) -> ChangeRef:
        title = cls.first_line(commit["commit"]["message"])
        pr = PR_NUMBER.search(title)
        return ChangeRef(
            sha=commit["sha"],
            title=PR_NUMBER.sub("", title).strip(),
            author=(commit.get("author") or {}).get("login"),
            pr=int(pr.group(1)) if pr else None,
            files=[changed["filename"] for changed in commit.get("files", [])],
        )

    @staticmethod
    def test_file(module: str, classname: str) -> str | None:
        parts = classname.split(".")
        while parts:
            candidate = Path(module, *parts).with_suffix(".py")
            if candidate.is_file():
                return candidate.as_posix()
            parts.pop()
        return None

    @staticmethod
    def module_of(report_dir: Path, modules: list[str]) -> str:
        prefix = report_dir.name.removesuffix(REPORT_SUFFIX)
        return next(module for module in modules if module.replace("/", "-") == prefix)

    @classmethod
    def failed_tests(cls, reports: Path, modules: list[str]) -> tuple[list[FailedTest], set[str]]:
        failures: list[FailedTest] = []
        reported: set[str] = set()
        for report in sorted(reports.glob(f"*{REPORT_SUFFIX}/pytest.xml")):
            module = cls.module_of(report.parent, modules)
            reported.add(module)
            for case in ElementTree.parse(report).iter("testcase"):
                problem = case.find("failure") if case.find("failure") is not None else case.find("error")
                if problem is None:
                    continue
                classname = case.get("classname", "")
                message = cls.first_line(problem.get("message") or problem.text or "")
                failures.append(
                    FailedTest(
                        module=module,
                        test_id=f"{classname.rsplit('.', 1)[-1]}::{case.get('name')}",
                        file=cls.test_file(module, classname),
                        message=message[:MESSAGE_LIMIT],
                    )
                )
        return failures, reported

    @classmethod
    def last_green_sha(cls, repo: str) -> str | None:
        runs = cls.gh_json(
            f"repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs?event=schedule&status=success&branch=main&per_page=1"
        )
        return runs["workflow_runs"][0]["head_sha"] if runs["workflow_runs"] else None

    @classmethod
    def merged_since(cls, repo: str, base: str, head: str) -> list[ChangeRef]:
        compare = cls.gh_json(f"repos/{repo}/compare/{base}...{head}")
        return [cls.change_ref(cls.gh_json(f"repos/{repo}/commits/{commit['sha']}")) for commit in compare["commits"]]

    @classmethod
    def owner(cls, repo: str, file: str, head: str) -> ChangeRef | None:
        commits = cls.gh_json(f"repos/{repo}/commits?path={file}&sha={head}&per_page=1")
        return cls.change_ref(commits[0]) if commits else None

    @staticmethod
    def code_folder(test_file: str) -> str:
        return test_file.split("/tests/", 1)[0] + "/" if "/tests/" in test_file else test_file.rsplit("/", 1)[0] + "/"

    @staticmethod
    def cell(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " ")

    @classmethod
    def failures_section(cls, failures: list[FailedTest], owners: dict[str, ChangeRef | None]) -> list[str]:
        lines = [f"### Failed tests ({len(failures)})", "", "| Module | Test | Reason | Last changed in |", "|---|---|---|---|"]
        for failure in failures:
            owner = owners.get(failure.file or "")
            owned_by = f"{owner.label} @{owner.author}" if owner and owner.author else owner.label if owner else "?"
            lines.append(
                f"| `{failure.module}` | `{cls.cell(failure.test_id)}` | {cls.cell(failure.message)} | {owned_by} |"
            )
        return lines

    @classmethod
    def changes_section(cls, changes: list[ChangeRef] | None, folders: set[str]) -> list[str]:
        if changes is None:
            return ["### Merged since the last green nightly", "", "No earlier green nightly run to compare with."]
        lines = [f"### Merged since the last green nightly ({len(changes)})", ""]
        touching = [change for change in changes if any(file.startswith(tuple(folders)) for file in change.files)]
        for change in changes:
            marker = " **(touches a failing test's folder)**" if change in touching else ""
            lines.append(f"- {change.label} {change.title}{marker}")
        if changes and folders and not touching:
            lines += ["", "None of these touch the failing tests' folders: likely provider or model variance."]
        return lines

    @classmethod
    def render(
        cls,
        run_url: str,
        head: str,
        base: str | None,
        modules: list[str],
        failures: list[FailedTest],
        reported: set[str],
        changes: list[ChangeRef] | None,
        owners: dict[str, ChangeRef | None],
    ) -> str:
        failed_modules = {failure.module for failure in failures}
        folders = {cls.code_folder(failure.file) for failure in failures if failure.file}
        lines = [
            f"## External provider tests failed on main ({datetime.now(UTC):%Y-%m-%d})",
            "",
            f"Run: {run_url} · main @ `{head[:9]}`",
            f"Last green nightly: `{base[:9]}`" if base else "Last green nightly: none found",
            "",
            *cls.failures_section(failures, owners),
            "",
            *cls.changes_section(changes, folders),
            "",
            "### Modules",
            "",
        ]
        for module in modules:
            status = "failed" if module in failed_modules else "passed" if module in reported else "no test report"
            lines.append(f"- `{module}`: {status}")
        lines += [
            "",
            "### Next steps",
            "",
            "- Re-run on main: Actions → External Provider Tests → Run workflow.",
            "- A module with no test report failed before its tests ran (setup or service health); see the run's logs.",
        ]
        return "\n".join(lines) + "\n"

    @classmethod
    def build(cls, repo: str, run_url: str, head: str, reports: Path, modules: list[str]) -> str:
        failures, reported = cls.failed_tests(reports, modules)
        base = cls.last_green_sha(repo)
        changes = cls.merged_since(repo, base, head) if base else None
        owners = {failure.file: cls.owner(repo, failure.file, head) for failure in failures if failure.file}
        return cls.render(run_url, head, base, modules, failures, reported, changes, owners)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--sha", required=True, help="The commit the failed nightly tested")
    parser.add_argument("--reports", type=Path, required=True, help="Folder holding the *-pytest-report artifacts")
    parser.add_argument("--test-matrix", required=True, help="The run's test matrix JSON from ci_targets.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    modules = [entry["module"] for entry in json.loads(args.test_matrix)]
    body = NightlyFailureReport.build(args.repo, args.run_url, args.sha, args.reports, modules)
    args.output.write_text(body, encoding="utf-8")


if __name__ == "__main__":
    main()
