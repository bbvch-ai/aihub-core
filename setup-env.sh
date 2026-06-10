#!/usr/bin/env bash
#
# Swiss AI Hub - Environment Setup Script
#
# Reads .env.template and generates a .env file with auto-generated secrets
# for all values that can be safely randomized (database passwords, tokens,
# signing keys, etc.).
#
# Values that require manual configuration (domain, API keys, OAuth settings)
# are left unchanged for the operator to fill in.
#
# Usage:
#     ./setup-env.sh                              # generates .env from .env.template
#     ./setup-env.sh -t custom.template -o out.env # custom template and output
#     ./setup-env.sh --force                       # overwrite existing .env

set -euo pipefail

TEMPLATE=".env.template"
OUTPUT=".env"
FORCE=false

usage() {
    echo "Usage: $0 [-t TEMPLATE] [-o OUTPUT] [--force]"
    echo
    echo "Generate .env from .env.template with auto-generated secrets."
    echo
    echo "Options:"
    echo "  -t, --template FILE   Path to the template file (default: .env.template)"
    echo "  -o, --output FILE     Path to the output file (default: .env)"
    echo "      --force           Overwrite output file if it already exists"
    echo "  -h, --help            Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--template) TEMPLATE="$2"; shift 2 ;;
        -o|--output)   OUTPUT="$2"; shift 2 ;;
        --force)       FORCE=true; shift ;;
        -h|--help)     usage ;;
        *) echo "ERROR: Unknown option: $1" >&2; exit 1 ;;
    esac
done

command -v openssl >/dev/null 2>&1 || {
    echo "ERROR: 'openssl' is required but not found." >&2
    exit 1
}

command -v uuidgen >/dev/null 2>&1 || {
    echo "ERROR: 'uuidgen' is required but not found." >&2
    exit 1
}

if [[ ! -f "$TEMPLATE" ]]; then
    echo "ERROR: Template file not found: $TEMPLATE" >&2
    exit 1
fi

if [[ -f "$OUTPUT" ]] && [[ "$FORCE" != true ]]; then
    echo "ERROR: Output file already exists: $OUTPUT" >&2
    echo "       Use --force to overwrite." >&2
    exit 1
fi

# --- Secret generators ---

# 32 bytes → base64url (matches Python secrets.token_urlsafe(32))
gen_urlsafe_32() {
    openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n'
}

# 24 bytes → base64url (matches Python secrets.token_urlsafe(24))
gen_urlsafe_24() {
    openssl rand -base64 24 | tr '+/' '-_' | tr -d '=\n'
}

# 32 bytes → 64 hex chars (matches Python secrets.token_hex(32))
gen_hex_64() {
    openssl rand -hex 32 | tr -d '\n'
}

# Random UUIDv4. uuidgen emits uppercase on some platforms (e.g. macOS), so
# normalize to lowercase for consistency.
gen_uuid() {
    uuidgen | tr 'A-Z' 'a-z' | tr -d '\n'
}

# Replace all occurrences of a placeholder one at a time, each with a unique value.
# Returns the number of replacements made.
replace_placeholder() {
    local file="$1"
    local placeholder="$2"
    local generator="$3"
    local count=0

    while grep -qF "$placeholder" "$file"; do
        local value
        value=$($generator)
        # Use a separator that won't appear in base64url or hex output
        sed -i "0,/${placeholder}/{s|${placeholder}|${value}|}" "$file"
        count=$((count + 1))
    done

    echo "$count"
}

# --- Main ---

cp "$TEMPLATE" "$OUTPUT"

# Placeholder → generator function, processed in order.
# Langfuse placeholders (which contain their prefix) must be processed before
# the generic REPLACE_WITH_RANDOM_STRING to avoid partial matches.
declare -A PLACEHOLDERS=(
    ["pk-lf-REPLACE_WITH_LANGFUSE_PUBLIC_KEY"]="gen_langfuse_pk"
    ["sk-lf-REPLACE_WITH_LANGFUSE_SECRET_KEY"]="gen_langfuse_sk"
    ["REPLACE_WITH_64_HEX_CHARS"]="gen_hex_64"
    ["REPLACE_WITH_RANDOM_UUID"]="gen_uuid"
    ["REPLACE_WITH_RANDOM_STRING"]="gen_urlsafe_32"
)

# Langfuse generators produce the full value including prefix
gen_langfuse_pk() { echo -n "pk-lf-$(gen_urlsafe_24)"; }
gen_langfuse_sk() { echo -n "sk-lf-$(gen_urlsafe_24)"; }

# Process specific placeholders before generic ones to avoid partial matches
ORDERED_KEYS=(
    "pk-lf-REPLACE_WITH_LANGFUSE_PUBLIC_KEY"
    "sk-lf-REPLACE_WITH_LANGFUSE_SECRET_KEY"
    "REPLACE_WITH_64_HEX_CHARS"
    "REPLACE_WITH_RANDOM_UUID"
    "REPLACE_WITH_RANDOM_STRING"
)

total=0
echo "Generated $OUTPUT from $TEMPLATE"

for placeholder in "${ORDERED_KEYS[@]}"; do
    generator="${PLACEHOLDERS[$placeholder]}"
    count=$(replace_placeholder "$OUTPUT" "$placeholder" "$generator")
    if [[ "$count" -gt 0 ]]; then
        total=$((total + count))
        echo "  ${count}x ${placeholder}"
    fi
done

echo "  ${total} secrets auto-generated"
echo
echo "Review the file and fill in the remaining values marked with REPLACE_WITH_*."
