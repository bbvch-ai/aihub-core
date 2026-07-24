#!/usr/bin/env bash
#
# Generate the GitHub Release body for a versioned release candidate (rc) or a
# stable release (latest). Reuses the same LLM mechanism as the CHANGELOG
# generator (`llm` + gemini), plus a References section of PR links.
#
# The caller decides the PR range (this is what makes rc per-build-delta and
# latest cumulative):
#   - latest vX.Y.Z : FROM = previous stable tag,      TO = the release commit
#   - rc     vX.Y.Z-rc.N : FROM = previous rc (or last stable for rc.1), TO = this rc
#
# Usage:  generate-release-notes.sh <from_ref> <to_ref>
# Env:    GH_REPO (owner/repo, required), GH_SERVER_URL (default github.com),
#         RELEASE_NOTES_MODEL (default gemini-2.5-flash)
# Output: the notes markdown on stdout.

set -euo pipefail

FROM="${1:?from_ref required}"
TO="${2:?to_ref required}"
GH_REPO="${GH_REPO:?GH_REPO required (owner/repo)}"
SERVER="${GH_SERVER_URL:-https://github.com}"
MODEL="${RELEASE_NOTES_MODEL:-gemini-2.5-flash}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="${SCRIPT_DIR}/release-notes-prompt.md"

# Match the CHANGELOG generator's exclusions so lockfiles and generated
# artifacts do not pollute the summary.
EXCLUDE_PATTERNS=(
    ':(exclude)*.lock'
    ':(exclude)*lock.json'
    ':(exclude)*-lock.yaml'
    ':(exclude)pnpm-lock.yaml'
    ':(exclude)packages/web/sdk/**'
    ':(exclude)LICENSE_REPORT.md'
    ':(exclude)licenses.config.json'
    ':(exclude)*.drawio'
)

diff_output="$(git diff "$FROM" "$TO" -- . "${EXCLUDE_PATTERNS[@]}" || true)"

# Natural-language, grouped body via the LLM. Degrades gracefully if `llm` is
# unavailable or the call fails, so a release is never blocked on note prose.
body=""
if [ -n "$diff_output" ] && command -v llm >/dev/null 2>&1; then
    body="$(llm --no-stream -m "$MODEL" --system - "$(cat "$PROMPT_FILE")" <<EOF || true
Here is the git diff from ${FROM} to ${TO}. Generate the grouped release notes.
${diff_output}
EOF
)"
fi
[ -n "$body" ] || body="_No summarised changes for this range._"

# References: PR numbers parsed from squash-merge commit subjects in (FROM, TO].
# Squash merges carry "(#123)" in the subject, so this lists every PR in range.
refs="$(git log --format='%s' "${FROM}..${TO}" 2>/dev/null \
    | grep -oE '#[0-9]+' | tr -d '#' | sort -un \
    | sed "s#^#- ${SERVER}/${GH_REPO}/pull/#" || true)"

printf '%s\n' "$body"
if [ -n "$refs" ]; then
    printf '\n### References\n\n%s\n' "$refs"
fi
