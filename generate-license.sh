#!/bin/bash
# Comprehensive license checker for entire monorepo
# Scans Python, Node.js, and Docker dependencies
# Generates a single LICENSES.md report

set -e

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
done < <(jq -c '.docker_licenses[]' "$CONFIG_FILE")

# Load license overrides into an associative array
declare -A LICENSE_OVERRIDES
while IFS='=' read -r key value; do
    key=$(echo "$key" | tr -d '"')
    value=$(echo "$value" | tr -d '"')
    LICENSE_OVERRIDES["$key"]="$value"
done < <(jq -r '.license_overrides | to_entries | .[] | "\(.key)=\(.value)"' "$CONFIG_FILE" 2>/dev/null || true)


# Initialize report
init_report() {
    cat > "$OUTPUT_FILE_ABS" << EOF
# License Report

Generated on: $(date)

This document contains license information for all dependencies across the monorepo:
- Python packages (Poetry)
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

# check_python_project function
check_python_project() {
    local project="$1"
    echo -e "${BLUE}Checking Python project: $project${NC}"

    if [ ! -d "$project" ]; then
        echo -e "${RED}Warning: Project $project not found${NC}"
        return 1
    fi

    cd "$project"

    echo "Installing dependencies to ensure venv is current..."
    poetry install --no-interaction --sync >/dev/null 2>&1 || {
        echo -e "${RED}Failed to install dependencies for $project${NC}"
        cd ..
        return 1
    }

    echo "Finding virtual environment for $project..."
    local venv_path
    venv_path=$(poetry env info --path)
    if [ -z "$venv_path" ]; then
        echo -e "${RED}Could not find virtual environment for $project. Skipping.${NC}"
        cd ..
        return 1
    fi
    local python_executable="$venv_path/bin/python"
    echo "Scanning packages from: $python_executable"

    local license_data
    license_data=$(poetry run pip-licenses \
        --python="$python_executable" \
        --from=mix \
        --format=json \
        --ignore-packages pip pip-licenses setuptools wheel tomli prettytable wcwidth \
        2>/dev/null || echo "[]")

    local project_total
    project_total=$(echo "$license_data" | jq '. | length')
    TOTAL_PYTHON_DEPS=$((TOTAL_PYTHON_DEPS + project_total))

    echo "### $project" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "| Status | Package | Version | License |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|---------|---------|" >> "$OUTPUT_FILE_ABS"

    echo "$license_data" | jq -c '.[]' | sort | while IFS= read -r line; do
        local name=$(echo "$line" | jq -r '.Name')
        # Skip internal packages
        if [[ -v IGNORE_PACKAGES[$name] ]]; then continue; fi

        local version=$(echo "$line" | jq -r '.Version')
        local license=$(echo "$line" | jq -r '.License')
        # Remove newlines from license string to prevent breaking markdown table
        license=$(echo "$license" | tr '\n' ' ')
        local override_note=""

        if echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            if [[ -v LICENSE_OVERRIDES[$name] ]]; then
                license="${LICENSE_OVERRIDES[$name]}"
                override_note=" (override)"
            fi
        fi

        local display_license
        if [ ${#license} -gt 100 ]; then
            display_license=$(echo "$license" | head -n 1)...
        else
            display_license="$license"
        fi

        local status="" # Start with no status

        if echo "$license" | grep -qE "$REVIEW_LICENSES"; then
            status="⚠️"
            echo -e "${YELLOW}⚠️  Review needed: $name uses $display_license${NC}"
            echo "python:$project:$name:$license" >> "$REVIEW_FILE"
        elif echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $display_license${NC}"
            echo "python:$project:$name:$license" >> "$RESTRICTIVE_FILE"
        elif echo "$license" | grep -qE "$PERMISSIVE_LICENSES"; then
            status="✅"
            # This is an approved permissive license. No console log needed.
        elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            # This specifically catches licenses that scanners explicitly mark as UNKNOWN
            status="❌"
            echo -e "${RED}❌ UNKNOWN LICENSE: $name has $license${NC}"
            echo "python:$project:$name:$license" >> "$UNKNOWN_FILE"
        else
            # This catches any license not in the lists above
            status="❌"
            echo -e "${RED}❌ UNLISTED/UNKNOWN LICENSE: $name has '$license'${NC}"
            echo "python:$project:$name:$license" >> "$UNKNOWN_FILE"
        fi

        echo "| $status | $name | $version | $display_license$override_note |" >> "$OUTPUT_FILE_ABS"
    done

    echo "" >> "$OUTPUT_FILE_ABS"
    cd ..
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
        cd ../..
        return 1
    fi
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies with pnpm..."
        pnpm install --production --silent
    fi

    echo "Analyzing licenses with 'pnpm licenses'..."
    pnpm licenses ls --json --prod > /tmp/web_licenses.json 2>/dev/null || {
        echo -e "${RED}Failed to analyze web dependencies with pnpm.${NC}"
        cd ../..
        return 1
    }

    local web_total=$(jq '[.[] | .[]] | length' /tmp/web_licenses.json)
    TOTAL_NODE_DEPS=$((TOTAL_NODE_DEPS + web_total))

    echo "### aihub_web (Node.js)" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "| Status | Package | Version | License |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|---------|---------|" >> "$OUTPUT_FILE_ABS"

    jq -r 'to_entries[] | .key as $license | .value[] | [.name, .version, $license] | @tsv' /tmp/web_licenses.json | sort | while IFS=$'\t' read -r name version license; do
        # Skip internal packages
        if [[ -v IGNORE_PACKAGES[$name] ]]; then continue; fi
        if [ -z "$name" ]; then continue; fi
        local override_note=""

        if echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            if [[ -v LICENSE_OVERRIDES[$name] ]]; then
                license="${LICENSE_OVERRIDES[$name]}"
                override_note=" (override)"
            fi
        fi

        local status="" # Start with no status

        if echo "$license" | grep -qE "$REVIEW_LICENSES"; then
            status="⚠️"
            echo -e "${YELLOW}⚠️  Review needed: $name uses $license${NC}"
            echo "node:aihub_web:$name:$license" >> "$REVIEW_FILE"
        elif echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $license${NC}"
            echo "node:aihub_web:$name:$license" >> "$RESTRICTIVE_FILE"
        elif echo "$license" | grep -qE "$PERMISSIVE_LICENSES"; then
            status="✅"
            # This is an approved permissive license. No console log needed.
        elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            # This specifically catches licenses that scanners explicitly mark as UNKNOWN
            status="❌"
            echo -e "${RED}❌ UNKNOWN LICENSE: $name has $license${NC}"
            echo "node:aihub_web:$name:$license" >> "$UNKNOWN_FILE"
        else
            # This catches any license not in the lists above
            status="❌"
            echo -e "${RED}❌ UNLISTED/UNKNOWN LICENSE: $name has '$license'${NC}"
            echo "node:aihub_web:$name:$license" >> "$UNKNOWN_FILE"
        fi

        echo "| $status | $name | $version | $license$override_note |" >> "$OUTPUT_FILE_ABS"
    done

    echo "" >> "$OUTPUT_FILE_ABS"
    cd ../..
}

# check_docker_images function
check_docker_images() {
    # This function does not `cd`, so its paths were already correct.
    # For consistency, we'll update it to use the absolute path variable.
    echo -e "${BLUE}Checking Docker images...${NC}"

    local compose_files=(docker-compose*.yml docker-compose*.yaml)
    compose_files=($(ls ${compose_files[@]} 2>/dev/null || true))

    if [ ${#compose_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}No docker-compose files found${NC}"
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

    add_section "Docker Images"

    echo "### External Docker Service Licenses" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "| Status | Service | Image | License | Notes |" >> "$OUTPUT_FILE_ABS"
    echo "|--------|---------|-------|---------|-------|" >> "$OUTPUT_FILE_ABS"

    local unknown_images=()
    for image in "${!seen_images[@]}"; do
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
    for image in "${!seen_images[@]}"; do
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

# (extract_service_name and is_own_image are unchanged)
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

    tail -n +10 "$OUTPUT_FILE_ABS" > "$temp_file"

    cat > "$OUTPUT_FILE_ABS" << EOF
# License Report

Generated on: $(date)

This document contains license information for all dependencies across the monorepo:
- Python packages (Poetry): **$TOTAL_PYTHON_DEPS packages**
- Node.js packages (pnpm): **$TOTAL_NODE_DEPS packages**
- External Docker images: **$TOTAL_DOCKER_IMAGES images**

### License Compatibility

EOF

    if [ "$restrictive_count" -eq 0 ] && [ "$unknown_count" -eq 0 ]; then
        cat >> "$OUTPUT_FILE_ABS" << EOF
✅ **No restrictive licenses found in your code dependencies!**

EOF
    else
        cat >> "$OUTPUT_FILE_ABS" << EOF
❌ **License issues found!** Please review and resolve:

EOF
    fi

    cat >> "$OUTPUT_FILE_ABS" << EOF
### Legend
- ✅ = Permissive license (MIT, BSD, Apache, etc.)
- ⚠️ = Weak copyleft or needs review (MPL, LGPL, etc.)
- ❌ = Restrictive or unknown license

EOF

    if [ "$restrictive_count" -gt 0 ]; then
        echo "### ❌ Restrictive Licenses in Code (Must Remove or Replace)" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "The following dependencies use restrictive copyleft licenses:" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) uses *$license*" >> "$OUTPUT_FILE_ABS"
        done < "$RESTRICTIVE_FILE"
        echo "" >> "$OUTPUT_FILE_ABS"
    fi

    if [ "$unknown_count" -gt 0 ]; then
        echo "### ❌ Unknown Licenses (Must Investigate)" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) has *$license*" >> "$OUTPUT_FILE_ABS"
        done < "$UNKNOWN_FILE"
        echo "" >> "$OUTPUT_FILE_ABS"
    fi

    if [ "$review_count" -gt 0 ]; then
        echo "### ⚠️ Licenses Requiring Review" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
        echo "These licenses are generally compatible but should be reviewed:" >> "$OUTPUT_FILE_ABS"; echo "" >> "$OUTPUT_FILE_ABS"
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
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}Error: poetry is required but not installed.${NC}"; exit 1;
    fi

    init_report
    add_section "Python Dependencies"
    for project in "${PYTHON_PROJECTS[@]}"; do
        check_python_project "$project" || true
    done

    add_section "JavaScript/TypeScript Dependencies"
    check_web_project || true
    add_section "Docker Images"
    check_docker_images || true
    generate_summary

    local restrictive_count=0; local unknown_count=0
    [ -f "$RESTRICTIVE_FILE" ] && restrictive_count=$(wc -l < "$RESTRICTIVE_FILE")
    [ -f "$UNKNOWN_FILE" ] && unknown_count=$(wc -l < "$UNKNOWN_FILE")

    echo ""
    echo -e "${GREEN}License report generated: $OUTPUT_FILE${NC}"
    echo ""
    echo "Summary:"
    echo "- Python dependencies: $TOTAL_PYTHON_DEPS"
    echo "- Node.js dependencies: $TOTAL_NODE_DEPS"
    echo "- External Docker images: $TOTAL_DOCKER_IMAGES"
    echo "- Restrictive licenses in code: $restrictive_count"
    echo "- Unknown licenses: $unknown_count"

    if [ "$restrictive_count" -gt 0 ] || [ "$unknown_count" -gt 0 ]; then
        echo ""; echo -e "${RED}❌ FAILED: Found $restrictive_count restrictive and $unknown_count unknown licenses${NC}"
        echo -e "${RED}Please review $OUTPUT_FILE for details${NC}"; exit 1
    else
        echo ""; echo -e "${GREEN}✅ SUCCESS: No restrictive licenses found in your code dependencies!${NC}"
        echo -e "${YELLOW}⚠️  Note: Review Docker services with AGPL/SSPL for SaaS compatibility${NC}"
        echo -e "${GREEN}You can use BSL 1.1 or any other license for your code.${NC}"; exit 0
    fi
}

main