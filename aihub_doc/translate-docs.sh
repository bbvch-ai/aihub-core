#!/bin/bash
#
# This script automatically translates all index.en.md files to German (index.de.md)
# using an LLM. It tracks changes using SHA256 hashes in the frontmatter to avoid
# retranslating unchanged files.
#
# The script must be run from within the 'aihub_doc' directory.

# Exit on error, undefined variable, or pipe failure
set -euo pipefail

# --- Configuration ---
PROMPT_FILE="translate-prompt.md"
LLM_MODEL="gemini-2.5-flash"
SOURCE_LANG="en"
TARGET_LANG="de"
TARGET_SUFFIX=".de.md"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Functions ---

# Calculate SHA256 hash of a file
calculate_sha() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        shasum -a 256 "$file" | awk '{print $1}'
    else
        # Linux/WSL
        sha256sum "$file" | awk '{print $1}'
    fi
}

# Extract source_sha from frontmatter
get_source_sha_from_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo ""
        return
    fi

    # Extract source_sha from YAML frontmatter
    # Use a counter to track when we're inside the frontmatter block
    local sha=$(awk 'BEGIN{in_fm=0}
        /^---$/ {
            in_fm++
            if (in_fm==2) exit
            next
        }
        in_fm==1 && /^source_sha:/ {
            gsub(/^source_sha: *"?/, "")
            gsub(/"$/, "")
            print
            exit
        }' "$file")

    echo "$sha"
}

# Check if translation is needed
needs_translation() {
    local source_file="$1"
    local target_file="$2"

    # If target doesn't exist, translation is needed
    if [ ! -f "$target_file" ]; then
        return 0  # true in bash
    fi

    # Calculate current source hash
    local current_sha=$(calculate_sha "$source_file")

    # Get stored hash from target file
    local stored_sha=$(get_source_sha_from_file "$target_file")

    # If hashes don't match, translation is needed
    if [ "$current_sha" != "$stored_sha" ]; then
        return 0  # true
    fi

    return 1  # false
}

# Translate a single file using LLM
translate_file() {
    local source_file="$1"
    local target_file="$2"

    echo -e "${BLUE}📝 Translating: $source_file${NC}"

    # Calculate source hash
    local source_sha=$(calculate_sha "$source_file")

    # Read source content
    local source_content=$(cat "$source_file")

    # Read prompt
    local prompt_content=$(cat "$PROMPT_FILE")

    # Call LLM to translate
    echo -e "${YELLOW}🤖 Calling LLM ($LLM_MODEL)...${NC}"

    if ! llm_output=$(llm --no-stream -m "$LLM_MODEL" --system "$prompt_content" <<EOF
Please translate the following Markdown documentation from English to German.
Remember to preserve all frontmatter, add source_sha: "%%SOURCE_SHA%%", and maintain exact formatting.

$source_content
EOF
); then
        echo -e "${RED}❌ Error: Failed to translate $source_file${NC}" >&2
        return 1
    fi

    # Replace the %%SOURCE_SHA%% placeholder with actual hash
    local processed_output=$(echo "$llm_output" | sed "s/%%SOURCE_SHA%%/$source_sha/g")

    # Ensure the target directory exists
    local target_dir=$(dirname "$target_file")
    mkdir -p "$target_dir"

    # Write the translated content
    echo "$processed_output" > "$target_file"

    echo -e "${GREEN}✅ Successfully translated to: $target_file${NC}"
    return 0
}

# --- Pre-flight Checks ---

if [ ! -f "$PROMPT_FILE" ]; then
    echo -e "${RED}Error: Prompt file '$PROMPT_FILE' not found.${NC}" >&2
    exit 1
fi

if ! command -v llm &> /dev/null; then
    echo -e "${RED}Error: 'llm' command not found. Please install using 'pipx install llm'.${NC}" >&2
    exit 1
fi

if [ ! -d "docs" ]; then
    echo -e "${RED}Error: 'docs' directory not found. Are you running this from aihub_doc?${NC}" >&2
    exit 1
fi

# --- Main Logic ---

echo -e "${BLUE}🌍 Starting documentation translation (English → German)${NC}"
echo ""

# Track statistics
total_files=0
translated_files=0
skipped_files=0
failed_files=0

# Find all index.en.md files (excluding node_modules and hidden directories)
find docs -type f -name "index.en.md" -not -path "*/node_modules/*" -not -path "*/.*" -print0 | while IFS= read -r -d '' source_file; do
    total_files=$((total_files + 1))

    # Determine target file path (same directory, but .de.md suffix)
    dir=$(dirname "$source_file")
    target_file="${dir}/index${TARGET_SUFFIX}"

    # Check if translation is needed
    if needs_translation "$source_file" "$target_file"; then
        echo -e "${YELLOW}🔄 Translation needed for: $source_file${NC}"

        if translate_file "$source_file" "$target_file"; then
            translated_files=$((translated_files + 1))
        else
            failed_files=$((failed_files + 1))
        fi

        echo ""
    else
        echo -e "${GREEN}⏭️  Skipping (up-to-date): $source_file${NC}"
        skipped_files=$((skipped_files + 1))
    fi
done

# Also translate root index.en.md if it exists
if [ -f "index.en.md" ]; then
    total_files=$((total_files + 1))

    if needs_translation "index.en.md" "index.de.md"; then
        echo -e "${YELLOW}🔄 Translation needed for: index.en.md (root)${NC}"

        if translate_file "index.en.md" "index.de.md"; then
            translated_files=$((translated_files + 1))
        else
            failed_files=$((failed_files + 1))
        fi

        echo ""
    else
        echo -e "${GREEN}⏭️  Skipping (up-to-date): index.en.md (root)${NC}"
        skipped_files=$((skipped_files + 1))
    fi
fi

# --- Summary ---
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Translation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "Total files found:    ${total_files}"
echo -e "${GREEN}Translated:           ${translated_files}${NC}"
echo -e "${YELLOW}Skipped (up-to-date): ${skipped_files}${NC}"
echo -e "${RED}Failed:               ${failed_files}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $failed_files -gt 0 ]; then
    echo -e "${RED}⚠️  Some translations failed. Please check the errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}✨ Translation complete!${NC}"
exit 0
