#!/bin/bash
#
# Whitepaper Quality & Length Measurement
# Measures word count, page estimate, and provides quality metrics
#
# Usage: ./measure-whitepaper.sh [combined_markdown]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
TARGET_MAX_PAGES=40
WORDS_PER_PAGE=300  # Conservative estimate for Word documents
TARGET_MAX_WORDS=$((TARGET_MAX_PAGES * WORDS_PER_PAGE))  # 12000 words

# Input file
COMBINED_MD="${1:-$SCRIPT_DIR/swiss_ai_hub_whitepaper.md}"

if [ ! -f "$COMBINED_MD" ]; then
    echo -e "${RED}✗ File not found: $COMBINED_MD${NC}"
    echo "Usage: $0 [combined_markdown_file]"
    exit 1
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Whitepaper Quality & Length Analysis        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Word count
echo -e "${BLUE}📊 Measuring document...${NC}"
total_words=$(wc -w < "$COMBINED_MD")
total_lines=$(wc -l < "$COMBINED_MD")

# Estimated pages
estimated_pages=$(echo "scale=1; $total_words / $WORDS_PER_PAGE" | bc)

# Status
if (( total_words <= TARGET_MAX_WORDS )); then
    status_color=$GREEN
    status="✓ WITHIN TARGET"
else
    status_color=$RED
    excess_words=$((total_words - TARGET_MAX_WORDS))
    excess_percent=$(echo "scale=1; ($excess_words * 100) / $TARGET_MAX_WORDS" | bc)
    status="✗ EXCEEDS TARGET by $excess_words words (+${excess_percent}%)"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Results${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "Total words:       ${status_color}$(printf "%'d" $total_words)${NC}"
echo -e "Target max words:  $(printf "%'d" $TARGET_MAX_WORDS)"
echo -e "Estimated pages:   ${status_color}${estimated_pages}${NC} (target: max $TARGET_MAX_PAGES)"
echo -e "Status:            ${status_color}${status}${NC}"
echo ""

# Per-chapter analysis
echo -e "${BLUE}📑 Chapter breakdown:${NC}"
echo ""

# Extract chapters and count words
awk '
/^# [0-9]/ {
    if (chapter_name) {
        printf "%s: %d words\n", chapter_name, word_count
    }
    chapter_name = $0
    gsub(/^# /, "", chapter_name)
    word_count = 0
    next
}
{
    word_count += NF
}
END {
    if (chapter_name) {
        printf "%s: %d words\n", chapter_name, word_count
    }
}' "$COMBINED_MD" | while IFS=: read -r chapter words; do
    words=$(echo "$words" | xargs)  # Trim whitespace

    # Determine if chapter is over target
    # Rough estimate: kurz=1000, mittel=1600, lang=2200
    if (( words > 2200 )); then
        echo -e "  ${RED}✗ $chapter: ${words} words (TOO LONG)${NC}"
    elif (( words > 1600 )); then
        echo -e "  ${YELLOW}⚠ $chapter: ${words} words (long)${NC}"
    else
        echo -e "  ${GREEN}✓ $chapter: ${words} words${NC}"
    fi
done

echo ""

# Quality checks
echo -e "${BLUE}🔍 Quality indicators:${NC}"
echo ""

# Count bulletpoints
bulletpoint_count=$(grep -c "^- " "$COMBINED_MD" || true)
bulletpoint_per_1000=$((bulletpoint_count * 1000 / total_words))
if (( bulletpoint_per_1000 > 50 )); then
    echo -e "  ${RED}✗ Bulletpoints: $bulletpoint_count ($bulletpoint_per_1000 per 1000 words) - TOO MANY${NC}"
elif (( bulletpoint_per_1000 > 30 )); then
    echo -e "  ${YELLOW}⚠ Bulletpoints: $bulletpoint_count ($bulletpoint_per_1000 per 1000 words) - high${NC}"
else
    echo -e "  ${GREEN}✓ Bulletpoints: $bulletpoint_count ($bulletpoint_per_1000 per 1000 words)${NC}"
fi

# Count "Die Plattform" repetitions (should be varied)
plattform_count=$(grep -o "Die Plattform" "$COMBINED_MD" | wc -l)
plattform_per_1000=$((plattform_count * 1000 / total_words))
if (( plattform_per_1000 > 15 )); then
    echo -e "  ${RED}✗ 'Die Plattform': $plattform_count ($plattform_per_1000 per 1000 words) - REPETITIVE${NC}"
elif (( plattform_per_1000 > 10 )); then
    echo -e "  ${YELLOW}⚠ 'Die Plattform': $plattform_count ($plattform_per_1000 per 1000 words) - high${NC}"
else
    echo -e "  ${GREEN}✓ 'Die Plattform': $plattform_count ($plattform_per_1000 per 1000 words)${NC}"
fi

# Check for filler words
filler_phrases=(
    "Es ist wichtig zu betonen"
    "In diesem Zusammenhang"
    "Darüber hinaus"
    "Des Weiteren"
    "Wie bereits erwähnt"
)

filler_total=0
for phrase in "${filler_phrases[@]}"; do
    count=$(grep -c "$phrase" "$COMBINED_MD" || true)
    filler_total=$((filler_total + count))
done

if (( filler_total > 5 )); then
    echo -e "  ${RED}✗ Filler phrases: $filler_total occurrences - TOO MANY${NC}"
elif (( filler_total > 0 )); then
    echo -e "  ${YELLOW}⚠ Filler phrases: $filler_total occurrences${NC}"
else
    echo -e "  ${GREEN}✓ Filler phrases: none detected${NC}"
fi

# Check for Business Decision Dimensions
echo ""
echo -e "${BLUE}💼 Business Decision Coverage:${NC}"

dimensions=(
    "Kosten:KOSTEN"
    "TCO:KOSTEN"
    "Sicherheit:SICHERHEIT"
    "Datenschutz:DATENSCHUTZ"
    "revDSG:DATENSCHUTZ"
    "Management:MANAGEMENT"
    "Personal:MANAGEMENT"
    "Skalier:ZUKUNFT"
    "Vendor Lock:ZUKUNFT"
    "Integration:INTEGRATION"
    "Deployment:INTEGRATION"
)

for dim in "${dimensions[@]}"; do
    keyword="${dim%%:*}"
    category="${dim##*:}"
    count=$(grep -i -c "$keyword" "$COMBINED_MD" || true)
    if (( count > 0 )); then
        echo -e "  ${GREEN}✓ $category ($keyword): $count mentions${NC}"
    else
        echo -e "  ${YELLOW}⚠ $category ($keyword): NOT FOUND${NC}"
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Recommendations${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

if (( total_words > TARGET_MAX_WORDS )); then
    excess=$((total_words - TARGET_MAX_WORDS))
    reduction_percent=$(echo "scale=1; ($excess * 100) / $total_words" | bc)

    echo -e "${YELLOW}📉 Document is too long. Need to reduce by $excess words (${reduction_percent}%)${NC}"
    echo ""
    echo "Strategies:"
    echo "  1. Reduce chapter targets in general_prompt.md further"
    echo "  2. Remove redundant explanations across chapters"
    echo "  3. Focus only on most critical Business Decision questions"
    echo "  4. Compress technical explanations (stay business-focused)"
    echo ""
else
    echo -e "${GREEN}✓ Document length is within target!${NC}"
    echo ""
fi

# Try to create Word document if pandoc available
if command -v pandoc &> /dev/null; then
    echo -e "${BLUE}📄 Generating Word document for accurate page count...${NC}"

    docx_output="${COMBINED_MD%.md}.docx"

    if pandoc "$COMBINED_MD" -o "$docx_output" --standalone 2>/dev/null; then
        echo -e "${GREEN}✓ Created: $docx_output${NC}"
        echo ""
        echo "Open the Word document to see actual page count."
        echo "Note: Actual pages may differ from estimate due to formatting."
    else
        echo -e "${YELLOW}⚠ Failed to create Word document${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pandoc not installed - cannot create Word document${NC}"
    echo "Install: sudo apt install pandoc"
fi

echo ""
echo -e "${BLUE}✓ Analysis complete!${NC}"
