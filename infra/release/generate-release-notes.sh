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

# Incremental rc (rc.2, rc.3, ...) — the FROM ref is itself an rc tag — gets a
# compact list of the conventional-commit subjects added since the previous rc,
# not the full grouped template. rc.1 (FROM = last stable) and latest (FROM =
# previous stable) keep the full LLM-grouped notes below.
if printf '%s' "$FROM" | grep -Eq -- '-rc\.[0-9]+$'; then
    body="$(git log --format='- %s' "${FROM}..${TO}" 2>/dev/null \
        | grep -E -- '^- (feat|fix|perf|refactor|docs?|test|build|ci|chore|style|revert)(\([^)]+\))?!?: ' \
        || true)"
    [ -n "$body" ] || body="_No changes since ${FROM}._"
else
    diff_output="$(git diff "$FROM" "$TO" -- . "${EXCLUDE_PATTERNS[@]}" || true)"

    # Guard the model's context window / cost on a big release: if the patch is very
    # large, summarise from the diffstat instead of the full patch.
    MAX_DIFF_LINES="${RELEASE_NOTES_MAX_DIFF_LINES:-6000}"
    diff_note=""
    if [ "$(printf '%s\n' "$diff_output" | wc -l)" -gt "$MAX_DIFF_LINES" ]; then
        diff_output="$(git diff --stat "$FROM" "$TO" -- . "${EXCLUDE_PATTERNS[@]}" || true)"
        diff_note=" (large release — summarised from the diffstat)"
    fi

    # Natural-language, grouped body via the LLM: system prompt from the file, the
    # diff piped as the user turn. Degrades gracefully if `llm` is unavailable or
    # the call fails, so a release is never blocked on note prose.
    body=""
    if [ -n "$diff_output" ] && command -v llm >/dev/null 2>&1; then
        body="$(printf 'Here is the git diff from %s to %s%s. Generate the grouped release notes.\n\n%s\n' \
            "$FROM" "$TO" "$diff_note" "$diff_output" \
            | llm --no-stream -m "$MODEL" --system "$(cat "$PROMPT_FILE")" 2>/dev/null || true)"
    fi
    [ -n "$body" ] || body="_No summarised changes for this range._"
fi

# References: PR numbers parsed from squash-merge commit subjects in (FROM, TO].
# Squash merges carry "(#123)" in the subject, so this lists every PR in range.
refs="$(git log --format='%s' "${FROM}..${TO}" 2>/dev/null \
    | grep -oE '#[0-9]+' | tr -d '#' | sort -un \
    | sed "s#^#- ${SERVER}/${GH_REPO}/pull/#" || true)"

printf '%s\n' "$body"
if [ -n "$refs" ]; then
    printf '\n### References\n\n%s\n' "$refs"
fi
