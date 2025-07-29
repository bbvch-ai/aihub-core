#!/usr/bin/env python3
"""
SonarCloud Issues Extractor

This script extracts issues from SonarCloud using the Web API and generates a markdown report.
Requires a SonarCloud token for authentication.
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote


class SonarCloudExtractor:
    def __init__(self, token: str = None):
        """
        Initialize the SonarCloud extractor.

        Args:
            token: SonarCloud authentication token. If None, will try to get from environment.
        """
        self.base_url = "https://sonarcloud.io/api"
        self.token = token or os.getenv("SONARCLOUD_TOKEN")

        if not self.token:
            raise ValueError(
                "SonarCloud token is required. Set SONARCLOUD_TOKEN environment variable or pass token parameter."
            )

        # Set up authentication headers
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def get_issues(self, project_key: str, statuses: List[str] = None, page_size: int = 500) -> List[Dict[Any, Any]]:
        """
        Fetch issues from SonarCloud for a given project.

        Args:
            project_key: The project key/ID
            statuses: List of issue statuses to filter by (e.g., ['OPEN', 'CONFIRMED'])
            page_size: Number of issues to fetch per page (max 500)

        Returns:
            List of issue dictionaries
        """
        if statuses is None:
            statuses = ["OPEN", "CONFIRMED"]

        issues = []
        page = 1

        while True:
            # Build query parameters
            params = {
                "componentKeys": project_key,
                "statuses": ",".join(statuses),
                "ps": page_size,  # page size
                "p": page,  # page number
                "facets": "severities,types,rules,tags,resolutions,assignees,author,directories,languages",
            }

            url = f"{self.base_url}/issues/search"

            try:
                print(f"Fetching page {page}...")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                page_issues = data.get("issues", [])

                if not page_issues:
                    break

                issues.extend(page_issues)

                # Check if we've fetched all issues
                total = data.get("total", 0)
                if len(issues) >= total:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching issues: {e}")
                if hasattr(e.response, "text"):
                    print(f"Response: {e.response.text}")
                sys.exit(1)

        print(f"Fetched {len(issues)} issues total")
        return issues

    def format_issue(self, issue: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Format an issue for better readability.

        Args:
            issue: Raw issue dictionary from API

        Returns:
            Formatted issue dictionary
        """
        return {
            "key": issue.get("key"),
            "rule": issue.get("rule"),
            "severity": issue.get("severity"),
            "type": issue.get("type"),
            "status": issue.get("status"),
            "message": issue.get("message"),
            "component": issue.get("component"),
            "project": issue.get("project"),
            "file": issue.get("component", "").split(":")[-1] if issue.get("component") else "",
            "line": issue.get("line"),
            "debt": issue.get("debt"),
            "assignee": issue.get("assignee"),
            "author": issue.get("author"),
            "creation_date": issue.get("creationDate"),
            "update_date": issue.get("updateDate"),
            "tags": issue.get("tags", []),
            "flows": issue.get("flows", []),
        }

    def save_to_markdown(self, issues: List[Dict[Any, Any]], filename: str = None):
        """
        Save issues to a markdown file.

        Args:
            issues: List of issues to save
            filename: Output filename. If None, generates a default name.
        """
        if filename is None:
            filename = f"sonarcloud_issues_{len(issues)}_items.md"

        formatted_issues = [self.format_issue(issue) for issue in issues]

        # Generate markdown content
        md_content = self._generate_markdown(formatted_issues)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"Issues saved to {filename}")

    def _generate_markdown(self, issues: List[Dict[str, Any]]) -> str:
        """
        Generate markdown content from issues.

        Args:
            issues: List of formatted issues

        Returns:
            Markdown content as string
        """

        # Get current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        md_lines = []

        # Header
        md_lines.append("# SonarCloud Issues Report")
        md_lines.append("")
        md_lines.append(f"**Project:** aihub-core_lib-core")
        md_lines.append(f"**Generated:** {now}")
        md_lines.append(f"**Total Issues:** {len(issues)}")
        md_lines.append("")

        # Summary statistics
        if issues:
            severity_counts = {}
            type_counts = {}
            status_counts = {}

            for issue in issues:
                severity = issue.get("severity", "UNKNOWN")
                issue_type = issue.get("type", "UNKNOWN")
                status = issue.get("status", "UNKNOWN")

                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
                status_counts[status] = status_counts.get(status, 0) + 1

            md_lines.append("## Summary")
            md_lines.append("")

            md_lines.append("### By Severity")
            md_lines.append("")
            md_lines.append("| Severity | Count |")
            md_lines.append("|----------|-------|")
            for severity, count in sorted(severity_counts.items()):
                md_lines.append(f"| {severity} | {count} |")
            md_lines.append("")

            md_lines.append("### By Type")
            md_lines.append("")
            md_lines.append("| Type | Count |")
            md_lines.append("|------|-------|")
            for issue_type, count in sorted(type_counts.items()):
                md_lines.append(f"| {issue_type} | {count} |")
            md_lines.append("")

            md_lines.append("### By Status")
            md_lines.append("")
            md_lines.append("| Status | Count |")
            md_lines.append("|--------|-------|")
            for status, count in sorted(status_counts.items()):
                md_lines.append(f"| {status} | {count} |")
            md_lines.append("")

        # Issues details
        md_lines.append("## Issues Details")
        md_lines.append("")

        if not issues:
            md_lines.append("No issues found.")
        else:
            # Group issues by severity for better organization
            severity_order = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
            grouped_issues = {}

            for issue in issues:
                severity = issue.get("severity", "UNKNOWN")
                if severity not in grouped_issues:
                    grouped_issues[severity] = []
                grouped_issues[severity].append(issue)

            # Output issues grouped by severity
            for severity in severity_order:
                if severity in grouped_issues:
                    md_lines.append(f"### {severity} Issues ({len(grouped_issues[severity])})")
                    md_lines.append("")

                    for i, issue in enumerate(grouped_issues[severity], 1):
                        md_lines.append(f"#### {i}. {issue['key']}")
                        md_lines.append("")
                        md_lines.append(f"**Rule:** `{issue['rule']}`")
                        md_lines.append(f"**Type:** {issue['type']}")
                        md_lines.append(f"**Status:** {issue['status']}")
                        md_lines.append(f"**File:** `{issue['file']}`")
                        if issue["line"]:
                            md_lines.append(f"**Line:** {issue['line']}")
                        if issue["debt"]:
                            md_lines.append(f"**Technical Debt:** {issue['debt']}")
                        if issue["assignee"]:
                            md_lines.append(f"**Assignee:** {issue['assignee']}")
                        if issue["tags"]:
                            md_lines.append(f"**Tags:** {', '.join(issue['tags'])}")
                        md_lines.append("")
                        md_lines.append(f"**Message:**")
                        md_lines.append(f"> {issue['message']}")
                        md_lines.append("")
                        md_lines.append("---")
                        md_lines.append("")

            # Handle any remaining severities not in the standard order
            for severity, severity_issues in grouped_issues.items():
                if severity not in severity_order:
                    md_lines.append(f"### {severity} Issues ({len(severity_issues)})")
                    md_lines.append("")

                    for i, issue in enumerate(severity_issues, 1):
                        md_lines.append(f"#### {i}. {issue['key']}")
                        md_lines.append("")
                        md_lines.append(f"**Rule:** `{issue['rule']}`")
                        md_lines.append(f"**Type:** {issue['type']}")
                        md_lines.append(f"**Status:** {issue['status']}")
                        md_lines.append(f"**File:** `{issue['file']}`")
                        if issue["line"]:
                            md_lines.append(f"**Line:** {issue['line']}")
                        if issue["debt"]:
                            md_lines.append(f"**Technical Debt:** {issue['debt']}")
                        if issue["assignee"]:
                            md_lines.append(f"**Assignee:** {issue['assignee']}")
                        if issue["tags"]:
                            md_lines.append(f"**Tags:** {', '.join(issue['tags'])}")
                        md_lines.append("")
                        md_lines.append(f"**Message:**")
                        md_lines.append(f"> {issue['message']}")
                        md_lines.append("")
                        md_lines.append("---")
                        md_lines.append("")

        return "\n".join(md_lines)

    def print_summary(self, issues: List[Dict[Any, Any]]):
        """
        Print a summary of the issues.

        Args:
            issues: List of issues
        """
        if not issues:
            print("No issues found.")
            return

        # Count by severity
        severity_counts = {}
        type_counts = {}
        status_counts = {}

        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            issue_type = issue.get("type", "UNKNOWN")
            status = issue.get("status", "UNKNOWN")

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n=== ISSUES SUMMARY ===")
        print(f"Total Issues: {len(issues)}")

        print(f"\nBy Severity:")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")

        print(f"\nBy Type:")
        for issue_type, count in sorted(type_counts.items()):
            print(f"  {issue_type}: {count}")

        print(f"\nBy Status:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")


def main():
    """
    Main function to extract SonarCloud issues.
    """
    # Project key from the URL you provided
    project_key = "aihub-core_lib-core"

    # Issue statuses to fetch
    statuses = ["OPEN", "CONFIRMED"]

    try:
        # Initialize extractor
        print(f"Initializing SonarCloud extractor for project: {project_key}")
        extractor = SonarCloudExtractor()

        # Fetch issues
        print(f"Fetching issues with statuses: {', '.join(statuses)}")
        issues = extractor.get_issues(project_key, statuses)

        # Print summary
        extractor.print_summary(issues)

        # Save to markdown file
        extractor.save_to_markdown(issues)

        print(f"\n=== MARKDOWN REPORT GENERATED ===")
        print(f"Your issues have been saved to a formatted markdown file.")
        print(f"The report includes summary statistics and detailed issue information.")

        # Print first few issues as examples
        if issues:
            print(f"\n=== SAMPLE ISSUES ===")
            for i, issue in enumerate(issues[:3]):  # Show first 3 issues
                formatted = extractor.format_issue(issue)
                print(f"\nIssue {i+1}:")
                print(f"  Key: {formatted['key']}")
                print(f"  Rule: {formatted['rule']}")
                print(f"  Severity: {formatted['severity']}")
                print(f"  Message: {formatted['message']}")
                print(f"  File: {formatted['file']}")
                if formatted["line"]:
                    print(f"  Line: {formatted['line']}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("SonarCloud Issues Extractor")
    print("=" * 30)

    # Check if token is available
    token = os.getenv("SONARCLOUD_TOKEN")
    if not token:
        print("\nTo use this script, you need a SonarCloud token.")
        print("Steps to get your token:")
        print("1. Go to SonarCloud.io")
        print("2. Click on your profile → My Account")
        print("3. Go to Security tab")
        print("4. Generate a new token")
        print("5. Set the environment variable:")
        print("   export SONARCLOUD_TOKEN='your_token_here'")
        print("\nAlternatively, you can pass the token directly to SonarCloudExtractor(token='your_token')")
        sys.exit(1)

    main()
