#!/bin/bash
#
# Whitepaper Chapter Combiner
# Combines all generated chapters into a single document
#
# Usage: ./combine-whitepaper.sh [output_dir] [output_name] [include_toc]
#   output_dir: Directory containing XX_output.md files (default: ./output)
#   output_name: Base name for output files (default: swiss_ai_hub_whitepaper)
#   include_toc: Include table of contents (default: true)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
OUTPUT_DIR="${1:-$SCRIPT_DIR/output}"
OUTPUT_NAME="${2:-swiss_ai_hub_whitepaper}"
INCLUDE_TOC="${3:-true}"

# Help
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
Swiss AI-Hub Whitepaper Chapter Combiner

Usage:
  $0 [output_dir] [output_name] [include_toc]

Arguments:
  output_dir      Directory containing XX_output.md files (default: ./output)
  output_name     Base name for output files (default: swiss_ai_hub_whitepaper)
  include_toc     Include table of contents (default: true)

Examples:
  $0                                    # Use defaults
  $0 ./output my_whitepaper true        # Custom name with TOC
  $0 ./output whitepaper false          # Without TOC

Output:
  Creates <output_name>.md and optionally <output_name>.docx (if pypandoc installed)

EOF
    exit 0
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Error: python3 not found${NC}" >&2
    exit 1
fi

# Run the Python script
cd "$SCRIPT_DIR"
python3 combine_whitepaper.py "$OUTPUT_DIR" "$OUTPUT_NAME" "$INCLUDE_TOC"
