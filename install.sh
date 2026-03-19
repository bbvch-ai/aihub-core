#!/usr/bin/env bash
#
# Swiss AI-Hub Installer
#
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash
#
# Or with options:
#   curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --gpu --dir ./my-hub
#
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────

VERSION=""
VERSION_EXPLICIT=false
HARDWARE=""
INSTALL_DIR="./swiss-ai-hub"
GITHUB_REPO="bbvch-ai/aihub-core"

# ── Color / formatting ───────────────────────────────────────────────────────

if [ -t 1 ] && [ -t 2 ]; then
    BOLD='\033[1m'
    DIM='\033[2m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    RESET='\033[0m'
    CHECK="${GREEN}✓${RESET}"
    CROSS="${RED}✗${RESET}"
    WARN="${YELLOW}!${RESET}"
else
    BOLD=''
    DIM=''
    RED=''
    GREEN=''
    YELLOW=''
    RESET=''
    CHECK="[ok]"
    CROSS="[!!]"
    WARN="[!]"
fi

header() { printf "\n  ${BOLD}%s${RESET}\n\n" "$1"; }
item()   { printf "    %-30s %s\n" "$1" "$2"; }
info()   { printf "    %s\n" "$1"; }
err()    { printf "  ${CROSS} ${RED}%s${RESET}\n" "$1" >&2; }
warn()   { printf "  ${WARN} ${YELLOW}%s${RESET}\n" "$1"; }

# ── Usage ─────────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF

  ${BOLD}Swiss AI-Hub Installer${RESET}

  Usage:
    install.sh [OPTIONS]

  Options:
    --version VERSION   Install a specific version (default: latest release)
    --gpu               Force GPU bundle (default: auto-detect)
    --cpu               Force CPU-only bundle (default: auto-detect)
    --dir PATH          Installation directory (default: ./swiss-ai-hub)
    --help              Show this help message

  Examples:
    # Install latest version with auto-detected hardware
    curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash

    # Install specific version with GPU bundle
    curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --version v0.269.2 --gpu

    # Install to a custom directory
    curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --dir /opt/swiss-ai-hub

EOF
    exit 0
}

# ── Argument parsing ──────────────────────────────────────────────────────────

while [ $# -gt 0 ]; do
    case "$1" in
        --version)
            [ $# -ge 2 ] || { err "Missing value for --version"; exit 1; }
            VERSION="$2"; VERSION_EXPLICIT=true; shift 2 ;;
        --gpu)
            HARDWARE="gpu"; shift ;;
        --cpu)
            HARDWARE="cpu"; shift ;;
        --dir)
            [ $# -ge 2 ] || { err "Missing value for --dir"; exit 1; }
            INSTALL_DIR="$2"; shift 2 ;;
        --help|-h)
            usage ;;
        *)
            err "Unknown option: $1"
            err "Run with --help for usage information."
            exit 1 ;;
    esac
done

# ── Preflight checks ─────────────────────────────────────────────────────────

check_command() {
    local name="$1"
    local cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        item "$name" "${CHECK}  found"
        return 0
    else
        item "$name" "${CROSS}  not found"
        return 1
    fi
}

check_versioned() {
    local name="$1"
    local cmd="$2"
    local version_flag="${3:---version}"
    if command -v "$cmd" &>/dev/null; then
        local ver
        ver=$($cmd "$version_flag" 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+[.0-9]*' | head -1)
        item "$name ${ver:-}" "${CHECK}  found"
        return 0
    else
        item "$name" "${CROSS}  not found"
        return 1
    fi
}

header "Swiss AI-Hub Installer"
header "Preflight"

PREFLIGHT_OK=true

check_command "curl" "curl" || PREFLIGHT_OK=false
check_command "tar" "tar" || PREFLIGHT_OK=false
check_command "openssl" "openssl" || PREFLIGHT_OK=false
check_versioned "docker" "docker" "--version" || PREFLIGHT_OK=false

if docker compose version &>/dev/null; then
    dc_ver=$(docker compose version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+[.0-9]*' | head -1)
    item "docker compose ${dc_ver:-}" "${CHECK}  found"
else
    item "docker compose" "${CROSS}  not found"
    PREFLIGHT_OK=false
fi

# GPU detection
GPU_NAME=""
if [ "$HARDWARE" = "gpu" ]; then
    if command -v nvidia-smi &>/dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)
    fi
    if [ -n "$GPU_NAME" ]; then
        item "NVIDIA GPU ($GPU_NAME)" "${CHECK}  found → GPU bundle selected"
    else
        item "NVIDIA GPU" "${WARN}  not detected (--gpu forced)"
    fi
elif [ "$HARDWARE" = "cpu" ]; then
    item "GPU detection" "${DIM}skipped (--cpu)${RESET}"
else
    if command -v nvidia-smi &>/dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)
    fi
    if [ -n "$GPU_NAME" ]; then
        HARDWARE="gpu"
        item "NVIDIA GPU ($GPU_NAME)" "${CHECK}  found → GPU bundle selected"
    else
        HARDWARE="cpu"
        item "NVIDIA GPU" "${DIM}not found → CPU bundle selected${RESET}"
    fi
fi

if [ "$PREFLIGHT_OK" != true ]; then
    printf "\n"
    err "Missing required tools. Please install them and try again."
    exit 1
fi

# ── Resolve version ──────────────────────────────────────────────────────────

if [ -z "$VERSION" ]; then
    VERSION=$(curl -sI "https://github.com/${GITHUB_REPO}/releases/latest" \
        | grep -i "^location:" | sed 's|.*/tag/||' | tr -d '\r\n')
    if [ -z "$VERSION" ]; then
        err "Failed to determine latest release version."
        err "Try specifying a version with --version"
        exit 1
    fi
fi

# Ensure version starts with 'v'
case "$VERSION" in
    v*) ;;
    *)  VERSION="v${VERSION}" ;;
esac

# ── Build bundle name ────────────────────────────────────────────────────────

if [ "$HARDWARE" = "gpu" ]; then
    BUNDLE="swissaihub-${VERSION}-gpu"
else
    BUNDLE="swissaihub-${VERSION}"
fi
ARCHIVE="${BUNDLE}.tar.gz"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/${ARCHIVE}"

# ── Detect fresh install vs upgrade ──────────────────────────────────────────

UPGRADE=false
if [ -f "${INSTALL_DIR}/.env" ] && [ -f "${INSTALL_DIR}/docker-compose.yml" ]; then
    UPGRADE=true
fi

if [ "$UPGRADE" = true ]; then
    header "Upgrade"
else
    header "Install"
fi

if [ "$VERSION_EXPLICIT" = true ]; then
    item "Version" "${VERSION}"
else
    item "Version" "${VERSION} (latest)"
fi
item "Bundle" "${ARCHIVE}"
item "Directory" "${INSTALL_DIR}"
if [ "$UPGRADE" = true ]; then
    item "Mode" "upgrade (existing installation detected)"
fi
printf "\n"

# ── Upgrade: warn about running containers ────────────────────────────────────

if [ "$UPGRADE" = true ]; then
    running=$(docker compose -f "${INSTALL_DIR}/docker-compose.yml" ps -q 2>/dev/null | wc -l || echo "0")
    if [ "$running" -gt 0 ]; then
        warn "Detected ${running} running container(s) in ${INSTALL_DIR}."
        warn "Consider running: docker compose -f ${INSTALL_DIR}/docker-compose.yml down"
        printf "\n"
    fi
fi

# ── Download and extract ─────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

info "Downloading ${ARCHIVE}..."
if ! curl -fSL --progress-bar -o "${TMPDIR}/${ARCHIVE}" "$DOWNLOAD_URL"; then
    err "Download failed: ${DOWNLOAD_URL}"
    err "Check that version ${VERSION} exists at:"
    err "  https://github.com/${GITHUB_REPO}/releases"
    exit 1
fi

info "Extracting..."
tar -xzf "${TMPDIR}/${ARCHIVE}" -C "$TMPDIR"

# The archive contains a top-level directory named after the bundle
EXTRACTED="${TMPDIR}/${BUNDLE}"
if [ ! -d "$EXTRACTED" ]; then
    err "Unexpected archive structure — expected directory: ${BUNDLE}"
    exit 1
fi

# ── Fresh install ─────────────────────────────────────────────────────────────

if [ "$UPGRADE" = false ]; then
    mkdir -p "$INSTALL_DIR"
    cp -a "${EXTRACTED}/." "$INSTALL_DIR/"

    info "Generating secrets (setup-env.sh)..."
    (cd "$INSTALL_DIR" && bash setup-env.sh)

    header "Next steps"
    info "1. cd ${INSTALL_DIR}"
    info "2. Edit .env — set DOMAIN, OAuth credentials, and LLM provider keys"
    info "   ${DIM}(see: https://bbvch-ai.github.io/swiss-ai-hub/2_platform/1_quick_start/)${RESET}"
    info "3. docker compose up -d"
    printf "\n"
    info "${DIM}Docs:    https://bbvch-ai.github.io/swiss-ai-hub/${RESET}"
    info "${DIM}Discord: https://discord.gg/wArT8zDB${RESET}"
    printf "\n"
    exit 0
fi

# ── Upgrade ───────────────────────────────────────────────────────────────────

info "Backing up .env..."
cp "${INSTALL_DIR}/.env" "${TMPDIR}/.env.backup"

info "Replacing bundle files..."
# Remove old bundle files but keep .env (already backed up)
rm -f "${INSTALL_DIR}/docker-compose.yml"
rm -f "${INSTALL_DIR}/.env.template"
rm -f "${INSTALL_DIR}/setup-env.sh"
rm -rf "${INSTALL_DIR}/configs"

# Copy new bundle files
cp -a "${EXTRACTED}/." "$INSTALL_DIR/"

info "Restoring .env..."
cp "${TMPDIR}/.env.backup" "${INSTALL_DIR}/.env"

# Detect new environment variables
if [ -f "${INSTALL_DIR}/.env.template" ]; then
    NEW_VARS=""
    while IFS= read -r line; do
        # Skip comments and empty lines
        case "$line" in
            '#'*|'') continue ;;
        esac
        # Extract variable name (everything before the first =)
        var_name="${line%%=*}"
        # Check if this variable exists in the current .env
        if ! grep -q "^${var_name}=" "${INSTALL_DIR}/.env" 2>/dev/null; then
            NEW_VARS="${NEW_VARS}    ${var_name}\n"
        fi
    done < "${INSTALL_DIR}/.env.template"

    if [ -n "$NEW_VARS" ]; then
        printf "\n"
        warn "New environment variables in this release:"
        printf '%b' "$NEW_VARS"
        info ""
        info "Compare with the template:"
        info "  diff ${INSTALL_DIR}/.env ${INSTALL_DIR}/.env.template"
    fi
fi

header "Next steps"
info "1. cd ${INSTALL_DIR}"
info "2. Review any new environment variables listed above"
info "3. docker compose up -d"
printf "\n"
info "${DIM}Docs:    https://bbvch-ai.github.io/swiss-ai-hub/${RESET}"
info "${DIM}Discord: https://discord.gg/wArT8zDB${RESET}"
printf "\n"
