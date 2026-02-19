#!/bin/bash
#
# This script automatically generates changelog entries for new git tags that start with 'v'
# by diffing against the previous 'v*' tag and using an LLM to summarize the changes.
# Adheres to the "Keep a Changelog" format.

# Exit on error, undefined variable, or pipe failure
set -euo pipefail

# --- Configuration ---
CHANGELOG_FILE="CHANGELOG.md"
SYSTEM_PROMPT_FILE="changelog-prompt.md"
LLM_MODEL="gemini-2.5-flash"
EXCLUDE_PATTERNS=(
    ':(exclude)*.lock'
    ':(exclude)*lock.json'
    ':(exclude)*-lock.yaml'
    ':(exclude)pnpm-lock.yaml'
    ':(exclude)aihub_web/aihub_web/sdk/**'
    ':(exclude)LICENSE_REPORT.md'
    ':(exclude)licenses.config.json'
    ':(exclude)*.drawio'
)
# The standard header for the changelog file.
CHANGELOG_HEADER=$(cat <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
EOF
)

# --- Functions ---

# Initializes the changelog file with the standard header if it's new or empty.
initialize_changelog() {
    if ! grep -q "Keep a Changelog" "$CHANGELOG_FILE" 2>/dev/null; then
        echo "Initializing $CHANGELOG_FILE with standard header."
        # The -e interprets the \n characters
        echo -e "$CHANGELOG_HEADER\n" > "$CHANGELOG_FILE"
    fi
}

# --- Pre-flight Checks ---
if [ ! -f "$SYSTEM_PROMPT_FILE" ]; then
    echo "Error: System prompt file '$SYSTEM_PROMPT_FILE' not found." >&2
    exit 1
fi
if ! command -v llm &> /dev/null; then
    echo "Error: 'llm' command not found. Please install using 'pipx install llm'." >&2
    exit 1
fi
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: This script must be run from within a git repository." >&2
    exit 1
fi

touch "$CHANGELOG_FILE"
initialize_changelog

# --- Main Logic ---

# Only find tags that start with 'v' using the -l flag.
mapfile -t sorted_tags < <(git tag -l "v*" --sort=v:refname)

if [ ${#sorted_tags[@]} -lt 2 ]; then
    echo "Need at least two 'v*' tags to generate a changelog entry. Exiting."
    exit 0
fi

echo "Found ${#sorted_tags[@]} 'v*' tags. Checking for new entries to generate..."

# Iterate through tags, starting from the second one.
for i in "${!sorted_tags[@]}"; do
    if [ $i -eq 0 ]; then continue; fi

    current_tag="${sorted_tags[$i]}"
    prev_tag="${sorted_tags[$i-1]}"

    # Check if this tag is already documented.
    if grep -q "^## \[$current_tag\]" "$CHANGELOG_FILE"; then
        echo "Skipping version $current_tag: already exists in $CHANGELOG_FILE."
        continue
    fi

    echo "---"
    echo "Generating entry for $current_tag (comparing with $prev_tag)..."

    diff_args=(git diff "$prev_tag" "$current_tag" -- .)
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        diff_args+=("$pattern")
    done
    diff_output=$("${diff_args[@]}")

    if [ -z "$diff_output" ]; then
        echo "No significant code changes found for $current_tag. Skipping."
        continue
    fi

    echo "Feeding diff to LLM ($LLM_MODEL)..."

    prompt_content=$(cat "$SYSTEM_PROMPT_FILE")

    # Attempt to generate the changelog entry using the LLM.
    if ! llm_output=$(llm --no-stream -m "$LLM_MODEL" --system - "$prompt_content" <<EOF
Here is the git diff from version $prev_tag to $current_tag. Please generate the changelog entry based on these changes.
$diff_output
EOF
); then
        echo "Warning: Failed to generate changelog for $current_tag. The LLM command failed. Skipping." >&2
        continue
    fi

    # Replace placeholders with actual values
    processed_output=$(echo "$llm_output" | sed "s/%%VERSION%%/$current_tag/g")

    # Get the actual date of the tag commit
    tag_date=$(git log -1 --format=%as "$current_tag")
    processed_output=$(echo "$processed_output" | sed "s/%%DATE%%/$tag_date/g")

    echo "Updating $CHANGELOG_FILE..."

    # Atomically insert the new entry just below the main header.
    temp_file=$(mktemp)
    # Get the content of the changelog, skipping the header section.
    header_lines=$(echo -e "$CHANGELOG_HEADER" | wc -l)
    tail -n +$((header_lines + 1)) "$CHANGELOG_FILE" > "$temp_file"

    # Write the new file structure: header, new entry, then the rest of the old content.
    echo -e "$CHANGELOG_HEADER\n" > "$CHANGELOG_FILE"
    echo -e "$processed_output\n\n---\n\n" >> "$CHANGELOG_FILE"
    cat "$temp_file" >> "$CHANGELOG_FILE"

    rm "$temp_file"

    echo "Successfully generated changelog for $current_tag."
done

echo "---"
echo "Changelog generation complete."