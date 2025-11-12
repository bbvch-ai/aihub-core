#!/bin/bash
#
# Whitepaper Generator for Swiss AI-Hub
# Generates business-focused whitepaper chapters using LLM
# Each chapter has its own prompt and source document mapping
#
# Usage: ./generate-whitepaper.sh [chapter_id...]
#   If no chapter_id provided, generates all chapters
#   Example: ./generate-whitepaper.sh 01 03 05

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
SOURCES_DIR="$SCRIPT_DIR/sources"
OUTPUT_DIR="$SCRIPT_DIR/output"
DOCS_ROOT="$SCRIPT_DIR/../docs"

LLM_MODEL="${LLM_MODEL:-claude-3-7-sonnet-20250219}"  # Can override via environment variable
MAX_RETRIES=3
RETRY_DELAY=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- Pre-flight Checks ---
check_requirements() {
    if ! command -v llm &> /dev/null; then
        echo -e "${RED}Error: 'llm' command not found. Please install using 'pipx install llm'${NC}" >&2
        echo "See: https://github.com/simonw/llm" >&2
        exit 1
    fi

    if [ ! -d "$PROMPTS_DIR" ]; then
        echo -e "${RED}Error: Prompts directory not found: $PROMPTS_DIR${NC}" >&2
        exit 1
    fi

    if [ ! -d "$SOURCES_DIR" ]; then
        echo -e "${RED}Error: Sources directory not found: $SOURCES_DIR${NC}" >&2
        exit 1
    fi

    if [ ! -d "$DOCS_ROOT" ]; then
        echo -e "${RED}Error: Documentation root not found: $DOCS_ROOT${NC}" >&2
        exit 1
    fi

    mkdir -p "$OUTPUT_DIR"
}

# --- Helper Functions ---

# Read source file list for a chapter
get_source_files() {
    local chapter_id="$1"
    local source_file="$SOURCES_DIR/${chapter_id}_sources.txt"

    if [ ! -f "$source_file" ]; then
        echo -e "${YELLOW}Warning: No source file found for chapter $chapter_id: $source_file${NC}" >&2
        return 1
    fi

    # Read source file, skip comments and empty lines
    grep -v '^\s*#' "$source_file" | grep -v '^\s*$' || true
}

# Concatenate source documentation files
collect_source_docs() {
    local chapter_id="$1"
    local temp_file="$2"

    echo "# Source Documentation" > "$temp_file"
    echo "" >> "$temp_file"

    local file_count=0
    while IFS= read -r doc_path; do
        # Remove leading/trailing whitespace
        doc_path=$(echo "$doc_path" | xargs)

        local full_path="$DOCS_ROOT/$doc_path"

        if [ -f "$full_path" ]; then
            echo -e "${BLUE}  📄 Including: $doc_path${NC}"
            echo "## Source: $doc_path" >> "$temp_file"
            echo "" >> "$temp_file"
            cat "$full_path" >> "$temp_file"
            echo -e "\n---\n" >> "$temp_file"
            ((file_count++))
        else
            echo -e "${YELLOW}  ⚠️  Source file not found: $full_path${NC}" >&2
        fi
    done < <(get_source_files "$chapter_id")

    if [ $file_count -eq 0 ]; then
        echo -e "${YELLOW}  ⚠️  No source documents found for chapter $chapter_id${NC}"
        echo "No source documentation was provided." >> "$temp_file"
    else
        echo -e "${GREEN}  ✓ Collected $file_count source document(s)${NC}"
    fi
}

# Generate a single chapter using LLM
generate_chapter() {
    local chapter_id="$1"
    local prompt_file="$PROMPTS_DIR/${chapter_id}_prompt.md"
    local output_file="$OUTPUT_DIR/${chapter_id}_output.md"

    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Generating Chapter: $chapter_id${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

    if [ ! -f "$prompt_file" ]; then
        echo -e "${RED}✗ Prompt file not found: $prompt_file${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}📝 Using prompt: $prompt_file${NC}"
    echo -e "${BLUE}🤖 Using model: $LLM_MODEL${NC}"

    # Collect source documentation
    local sources_file=$(mktemp)
    trap "rm -f $sources_file" RETURN

    echo -e "${BLUE}📚 Collecting source documentation...${NC}"
    collect_source_docs "$chapter_id" "$sources_file"

    # Read prompt content
    local prompt_content
    prompt_content=$(cat "$prompt_file")

    # Read source documentation
    local source_docs
    source_docs=$(cat "$sources_file")

    # Generate with retry logic
    local attempt=1
    local success=false

    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "${BLUE}🔄 Attempt $attempt/$MAX_RETRIES: Calling LLM...${NC}"

        # Call LLM with prompt and source docs
        if llm_output=$(llm --no-stream -m "$LLM_MODEL" --system "$prompt_content" <<EOF
You are writing a whitepaper chapter for the Swiss AI-Hub platform.

Below is the source documentation from the technical documentation that you should use as input for writing this chapter:

$source_docs

Please generate the chapter content based on the prompt instructions and the source documentation provided above.
Write in business-focused language accessible to non-technical decision makers while maintaining technical accuracy.
EOF
        ); then
            success=true
            break
        else
            echo -e "${YELLOW}⚠️  LLM call failed on attempt $attempt${NC}" >&2
            if [ $attempt -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}⏳ Waiting ${RETRY_DELAY}s before retry...${NC}"
                sleep $RETRY_DELAY
            fi
            ((attempt++))
        fi
    done

    if [ "$success" = false ]; then
        echo -e "${RED}✗ Failed to generate chapter $chapter_id after $MAX_RETRIES attempts${NC}" >&2
        return 1
    fi

    # Write output
    echo "$llm_output" > "$output_file"

    local word_count=$(echo "$llm_output" | wc -w)
    echo -e "${GREEN}✓ Chapter generated successfully${NC}"
    echo -e "${GREEN}  📄 Output: $output_file${NC}"
    echo -e "${GREEN}  📊 Word count: $word_count${NC}"

    return 0
}

# List all available chapters
list_chapters() {
    echo -e "${BLUE}Available chapters:${NC}"
    for prompt_file in "$PROMPTS_DIR"/*_prompt.md; do
        if [ -f "$prompt_file" ]; then
            local chapter_id=$(basename "$prompt_file" _prompt.md)
            local has_sources="✓"
            [ ! -f "$SOURCES_DIR/${chapter_id}_sources.txt" ] && has_sources="✗"
            local has_output="✓"
            [ ! -f "$OUTPUT_DIR/${chapter_id}_output.md" ] && has_output=" "

            echo -e "  ${chapter_id}: sources[$has_sources] output[$has_output]"
        fi
    done
}

# --- Main Logic ---
main() {
    check_requirements

    local chapters_to_generate=()

    # If arguments provided, use them as chapter IDs
    if [ $# -gt 0 ]; then
        chapters_to_generate=("$@")
        echo -e "${GREEN}Generating specified chapters: ${chapters_to_generate[*]}${NC}"
    else
        # Generate all chapters found in prompts directory
        echo -e "${GREEN}No chapters specified, generating all available chapters${NC}"
        for prompt_file in "$PROMPTS_DIR"/*_prompt.md; do
            if [ -f "$prompt_file" ]; then
                local chapter_id=$(basename "$prompt_file" _prompt.md)
                chapters_to_generate+=("$chapter_id")
            fi
        done
    fi

    if [ ${#chapters_to_generate[@]} -eq 0 ]; then
        echo -e "${YELLOW}No chapters found to generate${NC}"
        list_chapters
        exit 0
    fi

    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       Swiss AI-Hub Whitepaper Generator         ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Total chapters to generate: ${#chapters_to_generate[@]}${NC}"
    echo -e "${BLUE}Model: $LLM_MODEL${NC}"
    echo ""

    local success_count=0
    local fail_count=0
    local failed_chapters=()

    for chapter_id in "${chapters_to_generate[@]}"; do
        if generate_chapter "$chapter_id"; then
            ((success_count++))
        else
            ((fail_count++))
            failed_chapters+=("$chapter_id")
        fi
        echo ""
    done

    # Summary
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Generation Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Successful: $success_count${NC}"
    [ $fail_count -gt 0 ] && echo -e "${RED}✗ Failed: $fail_count${NC}"

    if [ ${#failed_chapters[@]} -gt 0 ]; then
        echo -e "${RED}Failed chapters: ${failed_chapters[*]}${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✓ All chapters generated successfully!${NC}"
    echo -e "${BLUE}Output directory: $OUTPUT_DIR${NC}"
}

# Show help
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
Swiss AI-Hub Whitepaper Generator

Usage:
  $0 [chapter_id...]     Generate specific chapters
  $0                     Generate all chapters
  $0 --list              List available chapters
  $0 --help              Show this help

Environment Variables:
  LLM_MODEL              LLM model to use (default: claude-3-7-sonnet-20250219)

Examples:
  $0                     # Generate all chapters
  $0 01 03 05            # Generate chapters 01, 03, and 05
  LLM_MODEL=gpt-4 $0     # Use different model

Chapter Files:
  prompts/${chapter_id}_prompt.md     - Chapter-specific prompt with instructions
  sources/${chapter_id}_sources.txt   - List of technical docs to include
  output/${chapter_id}_output.md      - Generated chapter output

EOF
    exit 0
fi

if [ "${1:-}" = "--list" ] || [ "${1:-}" = "-l" ]; then
    list_chapters
    exit 0
fi

# Run main
main "$@"
