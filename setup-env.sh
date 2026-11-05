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

# Random UUIDv4 derived from openssl so the script keeps a single crypto
# dependency (no uuidgen). openssl emits lowercase hex already.
gen_uuid() {
    local h
    h=$(openssl rand -hex 16)
    printf '%s-%s-4%s-%x%s-%s' \
        "${h:0:8}" "${h:8:4}" "${h:13:3}" \
        $((0x8 | (0x${h:16:1} & 0x3))) "${h:17:3}" \
        "${h:20:12}"
}

# 32 bytes → padded base64url, the format cryptography.fernet.Fernet.generate_key() emits
gen_fernet() {
    openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n'
}

# Langfuse generators produce the full value including prefix
gen_langfuse_pk() { echo -n "pk-lf-$(gen_urlsafe_24)"; }
gen_langfuse_sk() { echo -n "sk-lf-$(gen_urlsafe_24)"; }

ASSIGNMENT='^[A-Za-z_][A-Za-z0-9_]*='

# Replace the first occurrence of $2 by $3 on an assignment line (comments stay as written) and
# fail when there is none left. awk rather than `sed -i`, whose in-place and first-match syntax
# differ between GNU and BSD; no pipelines, which `pipefail` would fail on an early-exiting grep.
replace_first() {
    local file="$1" search="$2" value="$3" status=0
    awk -v s="$search" -v v="$value" -v a="$ASSIGNMENT" '
        !done && $0 ~ a && (i = index($0, s)) { $0 = substr($0, 1, i - 1) v substr($0, i + length(s)); done = 1 }
        { print }
        END { exit !done }' "$file" >"$file.tmp" || status=$?
    mv "$file.tmp" "$file"
    return "$status"
}

# Replace all occurrences of a placeholder one at a time, each with a unique value.
# Returns the number of replacements made.
replace_placeholder() {
    local file="$1"
    local placeholder="$2"
    local generator="$3"
    local count=0

    while replace_first "$file" "$placeholder" "$($generator)"; do
        count=$((count + 1))
    done

    echo "$count"
}

# A value may reference another variable as ${NAME}, e.g. a connection string carrying a generated
# password. Substitute the final value so every consumer (compose, python-dotenv, shell scripts that
# grep the file) reads the same literal.
resolve_references() {
    local file="$1" name value
    for name in $(awk -v a="$ASSIGNMENT" '$0 ~ a {
            while (match($0, /\$\{[A-Za-z_][A-Za-z0-9_]*\}/)) {
                print substr($0, RSTART + 2, RLENGTH - 3)
                $0 = substr($0, RSTART + RLENGTH)
            }
        }' "$file" | sort -u); do
        value=$(awk -v n="$name" 'index($0, n "=") == 1 { sub(/^[^=]*=/, ""); sub(/\r$/, ""); print; exit }' "$file")
        if ! grep -qE "^${name}=" "$file"; then
            echo "ERROR: ${name} is referenced but not defined in $file" >&2
            exit 1
        fi
        if [[ "$value" == *'${'* ]]; then
            echo "ERROR: ${name} is referenced but itself holds a reference; nest one level only" >&2
            exit 1
        fi
        value="${value#\'}"
        value="${value%\'}"
        value="${value#\"}"
        value="${value%\"}"
        while replace_first "$file" "\${${name}}" "$value"; do :; done
    done
}

# --- Main ---

cp "$TEMPLATE" "$OUTPUT"

# Placeholder:generator pairs, processed in order. Specific placeholders come before the generic
# REPLACE_WITH_RANDOM_STRING to avoid partial matches. A plain list, not an associative array,
# so the script also runs on the bash 3.2 macOS ships.
PLACEHOLDERS=(
    "pk-lf-REPLACE_WITH_LANGFUSE_PUBLIC_KEY:gen_langfuse_pk"
    "sk-lf-REPLACE_WITH_LANGFUSE_SECRET_KEY:gen_langfuse_sk"
    "REPLACE_WITH_FERNET_KEY:gen_fernet"
    "REPLACE_WITH_64_HEX_CHARS:gen_hex_64"
    "REPLACE_WITH_RANDOM_UUID:gen_uuid"
    "REPLACE_WITH_RANDOM_STRING:gen_urlsafe_32"
)

total=0
echo "Generated $OUTPUT from $TEMPLATE"

for entry in "${PLACEHOLDERS[@]}"; do
    placeholder="${entry%%:*}"
    generator="${entry##*:}"
    count=$(replace_placeholder "$OUTPUT" "$placeholder" "$generator")
    if [[ "$count" -gt 0 ]]; then
        total=$((total + count))
        echo "  ${count}x ${placeholder}"
    fi
done

resolve_references "$OUTPUT"
chmod 600 "$OUTPUT"

echo "  ${total} secrets auto-generated"
echo
echo "Review the file and fill in the remaining values marked with REPLACE_WITH_*."
