#!/bin/bash
# Auto-translate index.en.md files to German using LLM with change tracking
# Must be run from 'docs' directory

set -euo pipefail
PROMPT_FILE="translate-prompt.md"
LLM_MODEL="gemini-2.5-flash"
SOURCE_LANG="en"
TARGET_LANG="de"
TARGET_SUFFIX=".de.md"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
calculate_sha() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        sha256sum "$file" | awk '{print $1}'
    fi
}

get_source_sha_from_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo ""
        return
    fi

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

needs_translation() {
    local source_file="$1"
    local target_file="$2"

    if [ ! -f "$target_file" ]; then
        return 0
    fi

    local current_sha=$(calculate_sha "$source_file")
    local stored_sha=$(get_source_sha_from_file "$target_file")

    if [ "$current_sha" != "$stored_sha" ]; then
        return 0
    fi

    return 1
}

translate_file() {
    local source_file="$1"
    local target_file="$2"

    echo -e "${BLUE}📝 Translating: $source_file${NC}"

    local source_sha=$(calculate_sha "$source_file")
    local source_content=$(cat "$source_file")
    local prompt_content=$(cat "$PROMPT_FILE")

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

    local stripped_output="$llm_output"
    if echo "$stripped_output" | head -1 | grep -qE '^```'; then
        stripped_output=$(echo "$stripped_output" | tail -n +2)
        stripped_output=$(echo "$stripped_output" | sed '$ { /^```$/d }')
    fi

    local processed_output=$(echo "$stripped_output" | sed "s/%%SOURCE_SHA%%/$source_sha/g")
    local target_dir=$(dirname "$target_file")
    mkdir -p "$target_dir"
    echo "$processed_output" > "$target_file"

    echo -e "${GREEN}✅ Successfully translated to: $target_file${NC}"
    return 0
}

if [ ! -f "$PROMPT_FILE" ]; then
    echo -e "${RED}Error: Prompt file '$PROMPT_FILE' not found.${NC}" >&2
    exit 1
fi

if ! command -v llm &> /dev/null; then
    echo -e "${RED}Error: 'llm' command not found. Please install using 'pipx install llm'.${NC}" >&2
    exit 1
fi

if [ ! -d "docs" ]; then
    echo -e "${RED}Error: 'docs' directory not found. Are you running this from docs/?${NC}" >&2
    exit 1
fi

echo -e "${BLUE}🌍 Starting documentation translation (English → German)${NC}"
echo ""

total_files=0
translated_files=0
skipped_files=0
failed_files=0

# --- MODIFIED: Handle root index.en.md first ---
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
# --- End of modification ---

find docs -type f -name "index.en.md" -not -path "*/node_modules/*" -not -path "*/.*" -not -path "docs/6_code_deep_dive/*" -print0 | while IFS= read -r -d '' source_file; do
    total_files=$((total_files + 1))
    dir=$(dirname "$source_file")
    target_file="${dir}/index${TARGET_SUFFIX}"

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