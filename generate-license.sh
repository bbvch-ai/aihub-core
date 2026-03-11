#!/bin/bash
# Comprehensive license checker for entire monorepo
# Scans Python, Node.js, and Docker dependencies
# Generates a single LICENSE_REPORT.md report

set -e
export LC_ALL=C

# Create temp files using mktemp
RESTRICTIVE_FILE=$(mktemp)
REVIEW_FILE=$(mktemp)
UNKNOWN_FILE=$(mktemp)
DOCKER_RESTRICTIVE_FILE=$(mktemp)

# Clean up temp files on exit
trap "rm -f $RESTRICTIVE_FILE $REVIEW_FILE $UNKNOWN_FILE $DOCKER_RESTRICTIVE_FILE" EXIT

# Load configuration from JSON
CONFIG_FILE="licenses.config.json"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found!"
    exit 1
fi

# Load configuration
PYTHON_PROJECTS=($(jq -r '.python_projects[]' "$CONFIG_FILE"))
WEB_PROJECT=$(jq -r '.web_project' "$CONFIG_FILE")
OUTPUT_FILE=$(jq -r '.output_file' "$CONFIG_FILE")
OUTPUT_FILE_ABS="$(pwd)/$OUTPUT_FILE"
OWN_IMAGES=($(jq -r '.own_images[]' "$CONFIG_FILE"))

# Create a list of internal packages to ignore during scanning
declare -A IGNORE_PACKAGES
for p in "${PYTHON_PROJECTS[@]}"; do
    IGNORE_PACKAGES["$p"]=1
done
# Assume the web project's package.json name is the same as its directory name
WEB_PROJECT_NAME=$(basename "$WEB_PROJECT")
IGNORE_PACKAGES["$WEB_PROJECT_NAME"]=1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# License categories from config
RESTRICTIVE_LICENSES=$(jq -r '.license_categories.restrictive[]' "$CONFIG_FILE" | paste -sd '|' -)
REVIEW_LICENSES=$(jq -r '.license_categories.review[]' "$CONFIG_FILE" | paste -sd '|' -)
PERMISSIVE_LICENSES=$(jq -r '.license_categories.permissive[]' "$CONFIG_FILE" | paste -sd '|' -)
UNKNOWN_LICENSES=$(jq -r '.license_categories.unknown[]' "$CONFIG_FILE" | paste -sd '|' -)

# Counters
TOTAL_PYTHON_DEPS=0
TOTAL_NODE_DEPS=0
TOTAL_DOCKER_IMAGES=0

# Load Docker licenses from config
declare -A DOCKER_LICENSES
while IFS= read -r line; do
    service=$(echo "$line" | jq -r '.service')
    license=$(echo "$line" | jq -r '.license')
    status=$(echo "$line" | jq -r '.status')
    notes=$(echo "$line" | jq -r '.notes')
    DOCKER_LICENSES["$service"]="$license|$status|$notes"
done < <(jq -c '.docker_licenses[]' "$CONFIG_FILE" 2>/dev/null || true)

# Load license NAME overrides into an associative array
declare -A LICENSE_OVERRIDES
while IFS='=' read -r key value; do
    key=$(echo "$key" | tr -d '"')
    value=$(echo "$value" | tr -d '"')
    LICENSE_OVERRIDES["$key"]="$value"
done < <(jq -r '.license_overrides | to_entries | .[] | "\(.key)=\(.value)"' "$CONFIG_FILE" 2>/dev/null || true)

# Load full manual REVIEW overrides (for status, notes, etc.)
declare -A REVIEWED_OVERRIDES
while IFS= read -r line; do
    name=$(echo "$line" | jq -r '.name')
    REVIEWED_OVERRIDES["$name"]="$line"
done < <(jq -c '.reviewed_packages[]' "$CONFIG_FILE" 2>/dev/null || true)


# Initialize report
init_report() {
    cat > "$OUTPUT_FILE_ABS" << EOF
# License Report

Generated on: $(date +%d.%m.%Y)

This document contains license information for all dependencies across the monorepo:
- Python packages (uv)
- Node.js packages (pnpm)
- Docker images (from docker-compose files)

### License Compatibility

EOF
}

# Add section to report
add_section() {
    local title="$1"
    echo -e "\n## $title\n" >> "$OUTPUT_FILE_ABS"
}

# check_python_workspace function
# With uv workspaces there is a single shared .venv at the root,
# so we scan it once instead of per-package to avoid duplicates.
check_python_workspace() {
    echo -e "${BLUE}Checking Python workspace${NC}"

    echo "Syncing all workspace packages..."
    uv sync --all-packages >/dev/null 2>&1 || {
        echo -e "${RED}Failed to sync workspace dependencies${NC}"
        return 1
    }

    echo "Scanning packages from workspace venv: .venv/bin/python"

    local license_data
    local license_stderr
    license_stderr=$(mktemp)
    license_data=$(uv run pip-licenses \
        --from=mixed \
        --format=json \
        --ignore-packages pip pip-licenses setuptools wheel tomli prettytable wcwidth swiss-ai-hub-core swiss-ai-hub-agent swiss-ai-hub-api swiss-ai-hub-bot swiss-ai-hub-pipeline swiss-ai-hub-process \
        2>"$license_stderr") || {
        echo -e "${RED}Failed to run pip-licenses${NC}"
        echo "Error output: $(cat "$license_stderr")"
        license_data="[]"
    }
    rm -f "$license_stderr"

    local project_total
    project_total=$(echo "$license_data" | jq '. | length')
    TOTAL_PYTHON_DEPS=$project_total

    echo "| Status | Package | Version | License | Notes |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|---------|---------|-------|" >> "$OUTPUT_FILE_ABS"

    echo "$license_data" | jq -c 'sort_by(.Name | ascii_downcase) | .[]' | while IFS= read -r line; do
        local name=$(echo "$line" | jq -r '.Name')
        # Skip internal packages
        if [[ -v IGNORE_PACKAGES[$name] ]]; then continue; fi

        local version=$(echo "$line" | jq -r '.Version')
        local raw_license=$(echo "$line" | jq -r '.License')

        # Create a clean display version from the first line only, and trim whitespace
        local display_license
        display_license=$(echo "$raw_license" | head -n 1)
        if [ ${#display_license} -gt 100 ]; then
            display_license="${display_license:0:97}..."
        fi
        display_license=$(echo "$display_license" | xargs)


        # Create a single-line, trimmed version for classification logic
        local license=$(echo "$raw_license" | tr '\n' ' ')
        license=$(echo "$license" | xargs)

        local override_note=""

        # Unconditionally apply license name override if it exists.
        if [[ -v LICENSE_OVERRIDES[$name] ]]; then
            license="${LICENSE_OVERRIDES[$name]}"
            override_note=" (override)"
            display_license="$license" # Update display license as well
        fi

        local status=""
        local final_notes=""

        # Check for a manual "reviewed" override first.
        if [[ -v REVIEWED_OVERRIDES[$name] ]]; then
            local override_data=${REVIEWED_OVERRIDES[$name]}
            status=$(echo "$override_data" | jq -r '.status')
            display_license=$(echo "$override_data" | jq -r '.license') # Use the license from the override
            final_notes=$(echo "$override_data" | jq -r '.notes')
            echo -e "${GREEN}Manually reviewed: $name${NC}"
        else
            # If no manual override, run the standard classification logic
            if echo "$license" | grep -qE "$PERMISSIVE_LICENSES"; then
                status="✅"
            elif echo "$license" | grep -qE "$REVIEW_LICENSES"; then
                status="⚠️"
                echo -e "${YELLOW}⚠️  Review needed: $name uses $display_license${NC}"
                echo "python:workspace:$name:$license" >> "$REVIEW_FILE"
            elif echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
                status="❌"
                echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $display_license${NC}"
                echo "python:workspace:$name:$license" >> "$RESTRICTIVE_FILE"
            elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
                status="❌"
                echo -e "${RED}❌ UNKNOWN LICENSE: $name has '$license'${NC}"
                echo "python:workspace:$name:$license" >> "$UNKNOWN_FILE"
            else
                status="❌"
                echo -e "${RED}❌ UNLISTED/UNKNOWN LICENSE: $name has '$license'${NC}"
                echo "python:workspace:$name:$license" >> "$UNKNOWN_FILE"
            fi
        fi

        echo "| $status | $name | $version | $display_license$override_note | $final_notes |" >> "$OUTPUT_FILE_ABS"
    done

    echo "" >> "$OUTPUT_FILE_ABS"
}

# check_web_project function
check_web_project() {
    echo -e "${BLUE}Checking Web project: $WEB_PROJECT${NC}"

    if [ ! -d "$WEB_PROJECT" ]; then
        echo -e "${RED}Warning: Web project $WEB_PROJECT not found${NC}"
        return 1
    fi

    cd "$WEB_PROJECT"

    if ! command -v pnpm &> /dev/null; then
        echo -e "${RED}Error: pnpm is required for this script but not found.${NC}"
        cd ../../..
        return 1
    fi
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies with pnpm..."
        pnpm install --production --silent
    fi

    echo "Analyzing licenses with 'pnpm licenses'..."
    local pnpm_license_file
    pnpm_license_file=$(mktemp)
    pnpm licenses ls --json --prod > "$pnpm_license_file" 2>/dev/null || {
        echo -e "${RED}Failed to analyze web dependencies with pnpm.${NC}"
        cd ../../..
        return 1
    }

    local web_total=$(jq '[.. | objects | select(has("name") and has("versions"))] | unique_by(.name) | length' "$pnpm_license_file")
    TOTAL_NODE_DEPS=$((TOTAL_NODE_DEPS + web_total))

    echo "### web (Node.js)" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "| Status | Package | Version | License | Notes |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|---------|---------|-------|" >> "$OUTPUT_FILE_ABS"

    jq -r 'to_entries[] | .key as $license | .value[] | [.name, .versions[0], $license] | @tsv' "$pnpm_license_file" | sort | while IFS=$'\t' read -r name version license; do
        # Skip internal packages
        if [[ -v IGNORE_PACKAGES[$name] ]]; then continue; fi
        if [ -z "$name" ]; then continue; fi

        local override_note=""
        local display_license="$license"

        # Unconditionally apply license name override if it exists.
        if [[ -v LICENSE_OVERRIDES[$name] ]]; then
            license="${LICENSE_OVERRIDES[$name]}"
            override_note=" (override)"
            display_license="$license"
        fi

        local status=""
        local final_notes=""

        # Check for a manual "reviewed" override first.
        if [[ -v REVIEWED_OVERRIDES[$name] ]]; then
            local override_data=${REVIEWED_OVERRIDES[$name]}
            status=$(echo "$override_data" | jq -r '.status')
            display_license=$(echo "$override_data" | jq -r '.license')
            final_notes=$(echo "$override_data" | jq -r '.notes')
            echo -e "${GREEN}Manually reviewed: $name${NC}"
        else
            # If no manual override, run the standard classification logic
            if echo "$license" | grep -qE "$REVIEW_LICENSES"; then
                status="⚠️"
                echo -e "${YELLOW}⚠️  Review needed: $name uses $license${NC}"
                echo "node:web:$name:$license" >> "$REVIEW_FILE"
            elif echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
                status="❌"
                echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $license${NC}"
                echo "node:web:$name:$license" >> "$RESTRICTIVE_FILE"
            elif echo "$license" | grep -qE "$PERMISSIVE_LICENSES"; then
                status="✅"
            elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
                status="❌"
                echo -e "${RED}❌ UNKNOWN LICENSE: $name has $license${NC}"
                echo "node:web:$name:$license" >> "$UNKNOWN_FILE"
            else
                status="❌"
                echo -e "${RED}❌ UNLISTED/UNKNOWN LICENSE: $name has '$license'${NC}"
                echo "node:web:$name:$license" >> "$UNKNOWN_FILE"
            fi
        fi

        echo "| $status | $name | $version | $display_license$override_note | $final_notes |" >> "$OUTPUT_FILE_ABS"
    done
    rm "$pnpm_license_file"

    echo "" >> "$OUTPUT_FILE_ABS"
    cd ../../..
}

# check_docker_images function
check_docker_images() {
    echo -e "${BLUE}Checking Docker images...${NC}"

    local compose_files=(infra/docker-compose*.yml infra/docker-compose*.yaml)
    compose_files=($(ls ${compose_files[@]} 2>/dev/null || true))

    if [ ${#compose_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}No docker-compose files found in infra/${NC}"
        return
    fi
    echo "Found docker-compose files: ${compose_files[*]}"

    declare -A image_to_service; declare -A seen_images
    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            local current_service=""
            while IFS= read -r line; do
                if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_-]+):[[:space:]]*$ ]]; then
                    current_service="${BASH_REMATCH[1]}"
                elif [[ "$line" =~ ^[[:space:]]*image:[[:space:]]*(.+)$ ]] && [ -n "$current_service" ]; then
                    local image=$(echo "${BASH_REMATCH[1]}" | tr -d '"' | tr -d "'")
                    image_to_service["$image"]="$current_service"; seen_images["$image"]=1
                fi
            done < "$compose_file"
        fi
    done

    local external_images=0
    for image in "${!seen_images[@]}"; do
        if ! is_own_image "$(extract_service_name "$image")"; then
            external_images=$((external_images + 1))
        fi
    done
    TOTAL_DOCKER_IMAGES=$external_images
    echo "Found ${#seen_images[@]} unique Docker images ($external_images external)"

    echo "### External Docker Service Licenses" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "| Status | Service | Image | License | Notes |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|-------|---------|-------|" >> "$OUTPUT_FILE_ABS"

    local unknown_images=()
    for image in $(printf '%s\n' "${!seen_images[@]}" | sort); do
        local service_name="${image_to_service[$image]}"; local extracted_name=$(extract_service_name "$image")
        if is_own_image "$extracted_name"; then
            echo -e "${GREEN}Skipping own image: $extracted_name${NC}"; continue
        fi

        local found=false; local license=""; local status=""; local notes=""
        for known_service in "${!DOCKER_LICENSES[@]}"; do
            if [[ "$extracted_name" == "$known_service" ]] || [[ "$service_name" == "$known_service" ]]; then
                IFS='|' read -r license status notes <<< "${DOCKER_LICENSES[$known_service]}"; found=true
                if [[ "$license" =~ "AGPL" ]] || [[ "$license" =~ "SSPL" ]]; then
                    echo -e "${YELLOW}⚠️  Docker service with restrictive license: $service_name - $license${NC}"
                    echo "docker:$service_name:$image:$license" >> "$DOCKER_RESTRICTIVE_FILE"
                fi
                break
            fi
        done

        if [ "$found" = true ]; then
            echo "| $status | $extracted_name | \`$image\` | $license | $notes |" >> "$OUTPUT_FILE_ABS"
        else
            echo -e "${RED}❌ UNKNOWN DOCKER IMAGE: $image (service: $service_name, extracted: $extracted_name)${NC}"
            unknown_images+=("$image (service: $service_name)")
            echo "| ❌ | $extracted_name | \`$image\` | **UNKNOWN** | **Add to DOCKER_LICENSES** |" >> "$OUTPUT_FILE_ABS"
        fi
    done
    echo "" >> "$OUTPUT_FILE_ABS"

    echo "### Internal Docker Images (Our Code)" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "The following are our own services and inherit the license we choose:" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    for image in $(printf '%s\n' "${!seen_images[@]}" | sort); do
        local service_name="${image_to_service[$image]}"; local extracted_name=$(extract_service_name "$image")
        if is_own_image "$extracted_name"; then
            echo "- $service_name (\`$image\`)" >> "$OUTPUT_FILE_ABS"
        fi
    done
    echo "" >> "$OUTPUT_FILE_ABS"

    if [ ${#unknown_images[@]} -gt 0 ]; then
        echo "" >> "$OUTPUT_FILE_ABS"
        echo "### ❌ Unknown Docker Images" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "The following Docker images are not in our known licenses list:" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        for unknown in "${unknown_images[@]}"; do
            echo "- $unknown" >> "$OUTPUT_FILE_ABS"
            echo "docker:unknown:$unknown:UNKNOWN" >> "$UNKNOWN_FILE"
        done
        echo "" >> "$OUTPUT_FILE_ABS"
        echo "**Action Required:** Add these images to the DOCKER_LICENSES array in the script!" >> "$OUTPUT_FILE_ABS"
    fi
}

extract_service_name() { local image="$1"; local cleaned=$(echo "$image" | sed 's|^[^/]*/||'); if [[ "$cleaned" == *"/"* ]]; then cleaned=$(echo "$cleaned" | sed 's|^[^/]*/||'); fi; if [[ "$cleaned" == *"/"* ]]; then cleaned=$(echo "$cleaned" | awk -F'/' '{print $NF}'); fi; cleaned=$(echo "$cleaned" | cut -d':' -f1); echo "$cleaned"; }
is_own_image() { local service_name="$1"; for own in "${OWN_IMAGES[@]}"; do if [[ "$service_name" == "$own" ]]; then return 0; fi; done; return 1; }

# generate_summary function
generate_summary() {
    local temp_file=$(mktemp)
    local restrictive_count=0; local review_count=0; local unknown_count=0; local docker_restrictive_count=0
    [ -f "$RESTRICTIVE_FILE" ] && restrictive_count=$(wc -l < "$RESTRICTIVE_FILE")
    [ -f "$REVIEW_FILE" ] && review_count=$(wc -l < "$REVIEW_FILE")
    [ -f "$UNKNOWN_FILE" ] && unknown_count=$(wc -l < "$UNKNOWN_FILE")
    [ -f "$DOCKER_RESTRICTIVE_FILE" ] && docker_restrictive_count=$(wc -l < "$DOCKER_RESTRICTIVE_FILE")

    tail -n +12 "$OUTPUT_FILE_ABS" > "$temp_file"

    local total_issues=$((restrictive_count + review_count + unknown_count))

    cat > "$OUTPUT_FILE_ABS" << EOF
# License Report

Generated on: $(date +%d.%m.%Y)

This document contains license information for all dependencies across the monorepo:
- Python packages (uv): **$TOTAL_PYTHON_DEPS packages**
- Node.js packages (pnpm): **$TOTAL_NODE_DEPS packages**
- External Docker images: **$TOTAL_DOCKER_IMAGES images**

### License Compatibility

EOF

    if [ "$total_issues" -eq 0 ]; then
        cat >> "$OUTPUT_FILE_ABS" << EOF
✅ **All dependencies have approved licenses!**

EOF
    else
        cat >> "$OUTPUT_FILE_ABS" << EOF
❌ **License issues found!** All licenses must be permissive or explicitly approved via the 'reviewed_packages' configuration. Please review and resolve the items below:

EOF
    fi

    cat >> "$OUTPUT_FILE_ABS" << EOF
### Legend
- ✅ = Permissive or Manually Approved License
- ⚠️ = License requires manual review and approval
- ❌ = Restrictive or Unknown License

EOF

    if [ "$restrictive_count" -gt 0 ]; then
        echo "### ❌ Restrictive Licenses (Must Remove or Replace)" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "The following dependencies use restrictive copyleft licenses:" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) uses *$license*" >> "$OUTPUT_FILE_ABS"
        done < "$RESTRICTIVE_FILE"
        echo "" >> "$OUTPUT_FILE_ABS"
    fi

    if [ "$unknown_count" -gt 0 ]; then
        echo "### ❌ Unknown Licenses (Must Investigate)" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "The following packages have licenses that are not recognized or are proprietary." >> "$OUTPUT_FILE_ABS"
        echo "Please add them to the 'reviewed_packages' list in the config if they are approved for use." >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) has *$license*" >> "$OUTPUT_FILE_ABS"
        done < "$UNKNOWN_FILE"
        echo "" >> "$OUTPUT_FILE_ABS"
    fi

    if [ "$review_count" -gt 0 ]; then
        echo "### ⚠️ Licenses Requiring Review (Must be Approved)" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "These licenses require manual approval. Add an entry to the 'reviewed_packages' list in the config to approve them:" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) uses *$license*" >> "$OUTPUT_FILE_ABS"
        done < "$REVIEW_FILE"
        echo "" >> "$OUTPUT_FILE_ABS"
    fi

    cat "$temp_file" >> "$OUTPUT_FILE_ABS"
    rm "$temp_file"
}

# main function
main() {
    echo -e "${GREEN}Starting comprehensive license check...${NC}"
    echo "======================================"

    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed.${NC}"; exit 1;
    fi
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv is required but not installed.${NC}"; exit 1;
    fi

    init_report
    add_section "Python Dependencies"
    check_python_workspace || true

    add_section "JavaScript/TypeScript Dependencies"
    check_web_project || true
    add_section "Docker Images"
    check_docker_images || true
    generate_summary

    local restrictive_count=0; local review_count=0; local unknown_count=0
    [ -f "$RESTRICTIVE_FILE" ] && restrictive_count=$(wc -l < "$RESTRICTIVE_FILE")
    [ -f "$REVIEW_FILE" ] && review_count=$(wc -l < "$REVIEW_FILE")
    [ -f "$UNKNOWN_FILE" ] && unknown_count=$(wc -l < "$UNKNOWN_FILE")


    echo ""
    echo -e "${GREEN}License report generated: $OUTPUT_FILE${NC}"
    echo ""
    echo "Summary:"
    echo "- Python dependencies: $TOTAL_PYTHON_DEPS"
    echo "- Node.js dependencies: $TOTAL_NODE_DEPS"
    echo "- External Docker images: $TOTAL_DOCKER_IMAGES"
    echo "- Restrictive licenses: $restrictive_count"
    echo "- Unknown licenses: $unknown_count"
    echo "- Licenses needing review: $review_count"

    if [ "$restrictive_count" -gt 0 ] || [ "$unknown_count" -gt 0 ] || [ "$review_count" -gt 0 ]; then
        echo ""; echo -e "${RED}❌ FAILED: Found $restrictive_count restrictive, $unknown_count unknown, and $review_count unreviewed licenses.${NC}"
        echo -e "${RED}All licenses must be permissive or explicitly approved in 'reviewed_packages'.${NC}"
        echo -e "${RED}Please review $OUTPUT_FILE for details.${NC}"; exit 1
    else
        echo ""; echo -e "${GREEN}✅ SUCCESS: All dependencies have approved licenses!${NC}"
        echo -e "${YELLOW}⚠️  Note: Review Docker services with AGPL/SSPL for SaaS compatibility if applicable.${NC}"; exit 0
    fi
}

main