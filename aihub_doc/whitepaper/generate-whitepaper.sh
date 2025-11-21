#!/bin/bash
#
# Whitepaper Generator for Swiss AI-Hub
# Generates business-focused whitepaper chapters using LLM
# Each chapter has its own prompt and source document mapping
#
# Features:
#   - Generates new chapters from technical documentation
#   - Intelligently improves existing chapters when regenerating
#   - Preserves manual adjustments while integrating new information
#   - Maintains consistency across all chapters
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
DOCS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)/docs"
GENERAL_PROMPT="$SCRIPT_DIR/general_prompt.md"

LLM_MODEL="gemini-2.5-flash"  # Can override via environment variable
MAX_RETRIES=3
RETRY_DELAY=5
LANG_SUFFIX=".de.md"  # Use German documentation (.de.md)

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

    if [ ! -f "$GENERAL_PROMPT" ]; then
        echo -e "${RED}Error: General prompt file not found: $GENERAL_PROMPT${NC}" >&2
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

# Build combined prompt with source docs
build_combined_prompt() {
    local chapter_id="$1"
    local prompt_file="$PROMPTS_DIR/${chapter_id}_prompt.md"

    # Start with clear structure
    echo "# WHITEPAPER-KAPITEL GENERIERUNG"
    echo ""
    echo "Sie schreiben ein Whitepaper-Kapitel für die Swiss AI-Hub Plattform."
    echo "Unten finden Sie:"
    echo "1. Bereits generierte vorherige Kapitel (für Konsistenz)"
    echo "2. Quelldokumentation aus der technischen Dokumentation"
    echo "3. Spezifische Kapitelanweisungen und -anforderungen"
    echo "4. Allgemeine Schreibanweisungen für alle Kapitel"
    echo ""
    echo "Ihre Aufgabe: Generieren Sie den Kapitelinhalt gemäss den Anweisungen und verwenden Sie die Quelldokumentation als faktische Grundlage."
    echo "Achten Sie auf einen konsistenten Stil und Flow mit den bereits generierten Kapiteln."
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

     # Add previously generated chapters for consistency
    echo "## BEREITS GENERIERTE KAPITEL"
    echo ""
    echo "Nachfolgend finden Sie die bereits generierten vorherigen Kapitel."
    echo "Verwenden Sie diese, um einen konsistenten Schreibstil, Ton und Struktur beizubehalten."
    echo ""

    local prev_chapter_count=0
    local current_chapter_num=$((10#$chapter_id))  # Convert to decimal number

    # Loop through all previous chapters (00 to current-1)
    for ((i=0; i<current_chapter_num; i++)); do
        local prev_id=$(printf "%02d" $i)
        local prev_output="$OUTPUT_DIR/${prev_id}_output.md"

        if [ -f "$prev_output" ]; then
            echo "### Kapitel $prev_id"
            echo ""
            cat "$prev_output"
            echo ""
            echo "---"
            echo ""
            ((prev_chapter_count++))
        fi
    done

    if [ $prev_chapter_count -eq 0 ]; then
        echo "*(Keine vorherigen Kapitel vorhanden - dies ist das erste Kapitel)*"
        echo ""
    else
        echo "**Hinweis**: Achten Sie darauf, dass Ihr neues Kapitel nahtlos an diese vorherigen Kapitel anschliesst."
        echo ""
    fi

    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Add current chapter version if it exists (for improvement/updates)
    local output_file="$OUTPUT_DIR/${chapter_id}_output.md"
    echo "## AKTUELLE VERSION DES KAPITELS"
    echo ""

    if [ -f "$output_file" ]; then
        echo "Nachfolgend finden Sie die aktuelle Version dieses Kapitels."
        echo "Ihre Aufgabe ist es, diese Version zu **verbessern und zu aktualisieren**, falls in der"
        echo "bereitgestellten Quelldokumentation neue oder aktualisierte Informationen verfügbar sind."
        echo ""
        echo "**Wichtig**:"
        echo "- Behalten Sie manuelle Anpassungen bei, sofern sie nicht im Widerspruch zur Quelldokumentation stehen"
        echo "- Integrieren Sie neue Informationen nahtlos in die bestehende Struktur"
        echo "- Bewahren Sie den Schreibstil und Ton der bestehenden Version"
        echo "- Aktualisieren Sie nur die Teile, die durch neue Quelldokumentation überholt sind"
        echo ""
        echo "### Aktuelle Kapitelversion:"
        echo ""
        cat "$output_file"
        echo ""
    else
        echo "*(Keine bestehende Version vorhanden - erstellen Sie das Kapitel neu)*"
        echo ""
        echo "Da keine bestehende Version existiert, schreiben Sie das Kapitel komplett neu"
        echo "basierend auf der bereitgestellten Quelldokumentation und den Anweisungen."
        echo ""
    fi

    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Add source documentation
    echo "## QUELLDOKUMENTATION"
    echo ""
    echo "Nachfolgend die technische Dokumentation, die Sie als Quellenmaterial verwenden sollen:"
    echo ""

    local file_count=0
    while IFS= read -r doc_path; do
        # Strip whitespace and carriage returns (handles both LF and CRLF line endings)
        doc_path=$(echo "$doc_path" | tr -d '\r' | xargs)

        # Convert to German documentation path if it has .en.md suffix
        local de_doc_path="${doc_path//.en.md/$LANG_SUFFIX}"
        local full_path="$DOCS_ROOT/$de_doc_path"

        if [ -f "$full_path" ]; then
            echo "### Quelldatei: $de_doc_path"
            echo ""
            cat "$full_path"
            echo ""
            echo "---"
            echo ""
            ((file_count++))
        else
            # Fallback: try original path if German version doesn't exist
            full_path="$DOCS_ROOT/$doc_path"
            if [ -f "$full_path" ]; then
                echo "### Quelldatei: $doc_path"
                echo ""
                cat "$full_path"
                echo ""
                echo "---"
                echo ""
                ((file_count++))
            fi
        fi
    done < <(get_source_files "$chapter_id")

    if [ $file_count -eq 0 ]; then
        echo "*(Keine Quelldokumentation bereitgestellt)*"
        echo ""
    fi

    # Add chapter-specific instructions
    echo "## KAPITEL-SPEZIFISCHE ANWEISUNGEN"
    echo ""
    cat "$prompt_file"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Add general instructions (common for all chapters)
    echo "## ALLGEMEINE ANWEISUNGEN"
    echo ""
    cat "$GENERAL_PROMPT"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""



    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "## IHRE AUFGABE"
    echo ""
    if [ -f "$output_file" ]; then
        echo "**Verbessern und aktualisieren Sie die aktuelle Kapitelversion:**"
        echo ""
        echo "1. Prüfen Sie die bereitgestellte Quelldokumentation auf neue oder aktualisierte Informationen"
        echo "2. Falls neue Informationen vorhanden sind, integrieren Sie diese in die bestehende Version"
        echo "3. Behalten Sie manuelle Anpassungen und den bestehenden Stil bei"
        echo "4. Stellen Sie sicher, dass das aktualisierte Kapitel konsistent mit den vorherigen Kapiteln ist"
        echo "5. Falls keine neuen Informationen vorhanden sind, geben Sie die aktuelle Version unverändert zurück"
    else
        echo "**Generieren Sie den Kapitelinhalt neu:**"
        echo ""
        echo "1. Verwenden Sie die Quelldokumentation als faktische Grundlage"
        echo "2. Folgen Sie den kapitel-spezifischen und allgemeinen Anweisungen"
        echo "3. Stellen Sie sicher, dass der Stil mit den vorherigen Kapiteln konsistent ist"
    fi
    echo ""
    echo "Schreiben Sie auf Deutsch (Schweizer Hochdeutsch) in einem geschäftsorientierten Stil."
    echo ""
    echo "**WICHTIG**: Geben Sie NUR den Kapitelinhalt zurück, keine Meta-Kommentare oder Erklärungen."
}

# Generate a single chapter using LLM
generate_chapter() {
    local chapter_id="$1"
    local prompt_file="$PROMPTS_DIR/${chapter_id}_prompt.md"
    local output_file="$OUTPUT_DIR/${chapter_id}_output.md"

    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    if [ -f "$output_file" ]; then
        echo -e "${GREEN}Improving Existing Chapter: $chapter_id${NC}"
    else
        echo -e "${GREEN}Generating New Chapter: $chapter_id${NC}"
    fi
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

    if [ ! -f "$prompt_file" ]; then
        echo -e "${RED}✗ Prompt file not found: $prompt_file${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}📝 Using prompt: $prompt_file${NC}"
    echo -e "${BLUE}🤖 Using model: $LLM_MODEL${NC}"
    echo -e "${BLUE}📂 DOCS_ROOT: $DOCS_ROOT${NC}"

    if [ -f "$output_file" ]; then
        echo -e "${YELLOW}📄 Existing chapter found - will improve with new documentation${NC}"
    fi
    echo -e "${BLUE}📚 Collecting source documentation...${NC}"

    # Show which source files are being collected
    local file_count=0
    while IFS= read -r doc_path; do
        # Strip whitespace and carriage returns (handles both LF and CRLF line endings)
        doc_path=$(echo "$doc_path" | tr -d '\r' | xargs)
        local full_path="$DOCS_ROOT/$doc_path"
        if [ -f "$full_path" ]; then
            echo -e "${BLUE}  📄 $doc_path${NC}"
            ((file_count++))
        else
            echo -e "${YELLOW}  ⚠️  Not found: $doc_path${NC}" >&2
            echo -e "${YELLOW}      (Looking for: $full_path)${NC}" >&2
        fi
    done < <(get_source_files "$chapter_id")

    echo -e "${GREEN}  ✓ Collected $file_count source document(s)${NC}"

    # Count and show previously generated chapters
    echo -e "${BLUE}📖 Checking for previous chapters...${NC}"
    local prev_chapter_count=0
    local current_chapter_num=$((10#$chapter_id))

    for ((i=0; i<current_chapter_num; i++)); do
        local prev_id=$(printf "%02d" $i)
        local prev_output="$OUTPUT_DIR/${prev_id}_output.md"
        if [ -f "$prev_output" ]; then
            echo -e "${BLUE}  📗 Chapter $prev_id (for context)${NC}"
            ((prev_chapter_count++))
        fi
    done

    if [ $prev_chapter_count -eq 0 ]; then
        echo -e "${BLUE}  ℹ️  No previous chapters (this is the first chapter)${NC}"
    else
        echo -e "${GREEN}  ✓ Including $prev_chapter_count previous chapter(s) for consistency${NC}"
    fi

    # Build the complete combined prompt
    echo -e "${BLUE}🔨 Building combined prompt...${NC}"
    local combined_prompt
    combined_prompt=$(build_combined_prompt "$chapter_id")

    # Show size of combined prompt
    local prompt_size=$(echo "$combined_prompt" | wc -c)
    echo -e "${BLUE}  📊 Combined prompt size: $(numfmt --to=iec-i --suffix=B $prompt_size)${NC}"

    # Generate with retry logic
    local attempt=1
    local success=false

    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "${BLUE}🔄 Attempt $attempt/$MAX_RETRIES: Calling LLM...${NC}"

        # Call LLM with the combined prompt using temp file (more robust for large prompts)
        # Using temp file to avoid shell argument length limits and special character issues
        local temp_prompt_file=$(mktemp)
        echo "$combined_prompt" > "$temp_prompt_file"

        # Run LLM and capture both stdout and exit code
        set +e  # Temporarily disable exit on error
        llm_output=$(llm --no-stream -m "$LLM_MODEL" < "$temp_prompt_file" 2>&1)
        local exit_code=$?
        set -e  # Re-enable exit on error

        rm -f "$temp_prompt_file"

        if [ $exit_code -eq 0 ]; then
            success=true
            break
        else
            echo -e "${YELLOW}⚠️  LLM call failed on attempt $attempt (exit code: $exit_code)${NC}" >&2
            if [ -n "$llm_output" ]; then
                echo -e "${YELLOW}     Error output: ${llm_output:0:300}${NC}" >&2
            fi
            if [ $attempt -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}⏳ Waiting ${RETRY_DELAY}s before retry...${NC}"
                sleep $RETRY_DELAY
            fi
            attempt=$((attempt + 1))
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
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}Processing chapter $chapter_id ($(( success_count + fail_count + 1 ))/${#chapters_to_generate[@]})${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        if generate_chapter "$chapter_id"; then
            success_count=$((success_count + 1))
            echo -e "${GREEN}✓ Chapter $chapter_id completed successfully${NC}"
        else
            fail_count=$((fail_count + 1))
            failed_chapters+=("$chapter_id")
            echo -e "${RED}✗ Chapter $chapter_id failed${NC}"
        fi
        echo ""
        echo -e "${BLUE}Progress: ✓ $success_count successful, ✗ $fail_count failed${NC}"
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
  LLM_MODEL              LLM model to use (default: gemini-2.5-flash)

Examples:
  $0                     # Generate all chapters
  $0 01 03 05            # Generate chapters 01, 03, and 05
  LLM_MODEL=gpt-4 $0     # Use different model

Chapter Files:
  prompts/XX_prompt.md     - Chapter-specific prompt with instructions
  sources/XX_sources.txt   - List of technical docs to include
  output/XX_output.md      - Generated chapter output (XX = chapter ID like 00, 01, etc.)

Features:
  - Automatically includes all previously generated chapters in the prompt
  - Ensures consistent writing style, tone, and flow across chapters
  - Intelligently improves existing chapters when regenerating
  - Preserves manual adjustments while integrating new documentation
  - Generate chapters sequentially (00, 01, 02...) for best results
  - Each chapter learns from and builds upon previous ones

Regeneration Workflow:
  When regenerating an existing chapter, the script will:
  1. Include the current chapter version in the prompt
  2. Instruct the LLM to improve it with new information from documentation
  3. Preserve manual adjustments that don't conflict with source docs
  4. Maintain consistency with the existing style and structure

  This allows you to:
  - Make manual edits to generated chapters
  - Update source documentation
  - Regenerate chapters to integrate new information
  - Keep consistency even after manual adjustments

Note:
  For best consistency, generate chapters in order. When generating chapter N,
  all chapters 00 to N-1 from the output/ directory will be included in the
  prompt context to maintain a cohesive narrative and writing style.

EOF
    exit 0
fi

if [ "${1:-}" = "--list" ] || [ "${1:-}" = "-l" ]; then
    list_chapters
    exit 0
fi

# Run main
main "$@"
