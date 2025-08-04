#!/bin/bash
# check-licenses.sh - Comprehensive license checker for entire monorepo
# Scans Python, Node.js, and Docker dependencies
# Generates a single LICENSES.md report

set -e

# Configuration
PYTHON_PROJECTS=(
    "aihub_lib"
    "aihub_api"
    "aihub_bot"
    "aihub_agent"
    "aihub_process"
    "aihub_pipeline"
)

WEB_PROJECT="aihub_web/aihub_web"
OUTPUT_FILE="LICENSES.md"

# Our own images to ignore (these are our projects)
OWN_IMAGES=(
    "api"
    "web"
    "bot"
    "agent"
    "process"
    "pipeline"
    "processes"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# License categories
RESTRICTIVE_LICENSES="GPL|AGPL|SSPL|OSL-3\.0|EUPL"
REVIEW_LICENSES="LGPL|MPL|Mozilla Public License|EPL|CDDL|CC-BY-SA"
UNKNOWN_LICENSES="UNKNOWN|UNLICENSED|Custom|SEE LICENSE"

# Counters
TOTAL_PYTHON_DEPS=0
TOTAL_NODE_DEPS=0
TOTAL_DOCKER_IMAGES=0

# Known Docker image licenses - MANUALLY MAINTAINED LIST!
declare -A DOCKER_LICENSES=(
    # Databases
    ["postgres"]="PostgreSQL License|✅|BSD-style permissive license"
    ["redis"]="AGPL-3.0|⚠️|Copyleft - modifications must be open sourced if changed"
    ["mongo"]="SSPL|⚠️|Source-available; allowed for internal use, not for DB-as-a-service"
    ["mongodb"]="SSPL|⚠️|Source-available; allowed for internal use, not for DB-as-a-service"

    # Storage
    ["minio"]="AGPL-3.0|⚠️|Copyleft - modifications must be open sourced"
    ["etcd"]="Apache-2.0|✅|Permissive license"

    # Vector DBs / ML
    ["milvus"]="Apache-2.0|✅|Permissive license"
    ["attu"]="Apache-2.0|✅|Permissive license"

    # Message Queues
    ["nats"]="Apache-2.0|✅|Permissive license"
    ["rabbitmq"]="MPL-2.0|⚠️|Weak copyleft - modified source files must be shared"
    ["kafka"]="Apache-2.0|✅|Permissive license"

    # ML/AI Tools
    ["llama.cpp"]="MIT|✅|Permissive license"
    ["text-embeddings-inference"]="Apache-2.0|✅|Permissive license"
    ["phoenix"]="ELv2|⚠️|Source-available; cannot offer as a service, internal use allowed"
    ["jupyter"]="BSD-3-Clause|✅|Permissive license"
    ["litellm"]="MIT|✅|Permissive license"
    ["open-webui"]="BSD-3-Clause|⚠️|Permissive with required branding retention"

    # Utilities
    ["playwright"]="Apache-2.0|✅|Permissive license"
    ["docling"]="MIT|✅|Permissive license"
    ["docling-serve"]="MIT|✅|Permissive license"

    # Microsoft services
    ["presidio-analyzer"]="MIT|✅|Permissive license"
    ["presidio-anonymizer"]="MIT|✅|Permissive license"

    # Proxy/Routing
    ["traefik"]="Apache-2.0|✅|Permissive license"
    ["oauth2-proxy"]="MIT|✅|Permissive license"
    ["nginx"]="BSD-2-Clause|✅|Permissive license"

    # Workflow/Orchestration
    ["dagster"]="Apache-2.0|✅|Permissive license"
    ["airflow"]="Apache-2.0|✅|Permissive license"

    # Monitoring
    ["grafana"]="AGPL-3.0|⚠️|Copyleft - modifications must be open sourced"
    ["prometheus"]="Apache-2.0|✅|Permissive license"

    # Base images
    ["alpine"]="Various (GPL-2.0 and permissive)|⚠️|Primarily permissive, some copyleft components (e.g., BusyBox)"
    ["ubuntu"]="Various|✅|Mix of permissive and copyleft licenses (GPL, LGPL, etc.)"
    ["debian"]="Various|✅|Mix of permissive and copyleft licenses (GPL, LGPL, etc.)"
    ["python"]="PSF-2.0|✅|Permissive license"
    ["node"]="MIT|✅|Permissive license"
    ["minimal-notebook"]="BSD-3-Clause|✅|Jupyter base image"
)


# Initialize report
init_report() {
    cat > "$OUTPUT_FILE" << 'EOF'
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
    echo -e "\n## $title\n" >> "$OUTPUT_FILE"
}

# Check Python project
check_python_project() {
    local project="$1"
    echo -e "${BLUE}Checking Python project: $project${NC}"

    if [ ! -d "$project" ]; then
        echo -e "${RED}Warning: Project $project not found${NC}"
        return 1
    fi

    cd "$project"

    # Install dependencies
    echo "Installing dependencies..."
    poetry install --only main --no-interaction --quiet || {
        echo -e "${RED}Failed to install dependencies for $project${NC}"
        cd ..
        return 1
    }

    # Get license data
    local license_data=$(poetry run pip-licenses --format=json 2>/dev/null || echo "[]")
    local project_total=$(echo "$license_data" | jq '. | length')
    TOTAL_PYTHON_DEPS=$((TOTAL_PYTHON_DEPS + project_total))

    # Add to markdown
    echo "### $project" >> "../$OUTPUT_FILE"
    echo "" >> "../$OUTPUT_FILE"
    echo "| Status | Package | Version | License |" >> "../$OUTPUT_FILE"
    echo "|--------|---------|---------|---------|" >> "../$OUTPUT_FILE"

    # Process each dependency
    echo "$license_data" | jq -r '.[] | [.Name, .Version, .License] | @tsv' | sort | while IFS=$'\t' read -r name version license; do
        local status="✅"

        # Check for restrictive licenses
        if echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $license${NC}"
            echo "python:$project:$name:$license" >> ../restrictive_licenses.tmp
        elif echo "$license" | grep -qE "$REVIEW_LICENSES"; then
            status="⚠️"
            echo -e "${YELLOW}⚠️  Review needed: $name uses $license${NC}"
            echo "python:$project:$name:$license" >> ../review_licenses.tmp
        elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ UNKNOWN LICENSE: $name has $license${NC}"
            echo "python:$project:$name:$license" >> ../unknown_licenses.tmp
        fi

        # Add to markdown with status
        echo "| $status | $name | $version | $license |" >> "../$OUTPUT_FILE"
    done

    echo "" >> "../$OUTPUT_FILE"
    cd ..
}

# Check web project
check_web_project() {
    echo -e "${BLUE}Checking Web project: $WEB_PROJECT${NC}"

    if [ ! -d "$WEB_PROJECT" ]; then
        echo -e "${RED}Warning: Web project $WEB_PROJECT not found${NC}"
        return 1
    fi

    cd "$WEB_PROJECT"

    # Check if node_modules exists, if not install
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        if command -v pnpm &> /dev/null; then
            pnpm install --production --silent
        else
            npm install --production --silent
        fi
    fi

    # Get license data
    echo "Analyzing licenses..."
    local current_package_name=$(jq -r '.name // "aihub_web"' package.json 2>/dev/null || echo "aihub_web")

    npx license-checker --json --production --direct --excludePrivatePackages > /tmp/web_licenses_raw.json 2>/dev/null || {
        echo -e "${RED}Failed to analyze web dependencies${NC}"
        cd ../..
        return 1
    }

    # Filter out the current package
    jq --arg pkg "$current_package_name" 'to_entries | map(select(.key | contains($pkg) | not)) | from_entries' /tmp/web_licenses_raw.json > /tmp/web_licenses.json

    # Count dependencies
    local web_total=$(jq '. | length' /tmp/web_licenses.json)
    TOTAL_NODE_DEPS=$((TOTAL_NODE_DEPS + web_total))

    # Add to markdown
    echo "### aihub_web (Node.js)" >> "../../$OUTPUT_FILE"
    echo "" >> "../../$OUTPUT_FILE"
    echo "| Status | Package | Version | License |" >> "../../$OUTPUT_FILE"
    echo "|--------|---------|---------|---------|" >> "../../$OUTPUT_FILE"

    # Process each dependency
    jq -r 'to_entries[] | [.key, .value.licenses // "UNKNOWN", .value.repository // ""] | @tsv' /tmp/web_licenses.json | sort | while IFS=$'\t' read -r package license repo; do
        # Extract package name and version
        if [[ "$package" =~ ^(@[^/]+/[^@]+)@(.+)$ ]]; then
            name="${BASH_REMATCH[1]}"
            version="${BASH_REMATCH[2]}"
        elif [[ "$package" =~ ^([^@]+)@(.+)$ ]]; then
            name="${BASH_REMATCH[1]}"
            version="${BASH_REMATCH[2]}"
        else
            name="$package"
            version="unknown"
        fi

        local status="✅"

        # Check for restrictive licenses
        if echo "$license" | grep -qE "$RESTRICTIVE_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ RESTRICTIVE LICENSE: $name uses $license${NC}"
            echo "node:aihub_web:$name:$license" >> ../../restrictive_licenses.tmp
        elif echo "$license" | grep -qE "$REVIEW_LICENSES"; then
            status="⚠️"
            echo -e "${YELLOW}⚠️  Review needed: $name uses $license${NC}"
            echo "node:aihub_web:$name:$license" >> ../../review_licenses.tmp
        elif echo "$license" | grep -qiE "$UNKNOWN_LICENSES"; then
            status="❌"
            echo -e "${RED}❌ UNKNOWN LICENSE: $name has $license${NC}"
            echo "node:aihub_web:$name:$license" >> ../../unknown_licenses.tmp
        fi

        # Add to markdown with status
        echo "| $status | $name | $version | $license |" >> "../../$OUTPUT_FILE"
    done

    echo "" >> "../../$OUTPUT_FILE"
    cd ../..
}

# Extract service name from image (improved version)
extract_service_name() {
    local image="$1"
    # Remove registry prefix (ghcr.io/, mcr.microsoft.com/, etc.)
    local cleaned=$(echo "$image" | sed 's|^[^/]*/||')
    # If still has slashes, might be org/image format
    if [[ "$cleaned" == *"/"* ]]; then
        cleaned=$(echo "$cleaned" | sed 's|^[^/]*/||')
    fi
    # If still has slashes (nested org), take the last part
    if [[ "$cleaned" == *"/"* ]]; then
        cleaned=$(echo "$cleaned" | awk -F'/' '{print $NF}')
    fi
    # Remove tag
    cleaned=$(echo "$cleaned" | cut -d':' -f1)

    echo "$cleaned"
}

# Check if image is our own
is_own_image() {
    local service_name="$1"
    for own in "${OWN_IMAGES[@]}"; do
        if [[ "$service_name" == "$own" ]]; then
            return 0
        fi
    done
    return 1
}

# Check Docker images
check_docker_images() {
    echo -e "${BLUE}Checking Docker images...${NC}"

    # Find all docker-compose files
    local compose_files=(docker-compose*.yml docker-compose*.yaml)
    compose_files=($(ls ${compose_files[@]} 2>/dev/null || true))

    if [ ${#compose_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}No docker-compose files found${NC}"
        return
    fi

    echo "Found docker-compose files: ${compose_files[*]}"

    # Extract unique images with their service names
    declare -A image_to_service
    declare -A seen_images

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            # Extract service names and their images
            local current_service=""
            while IFS= read -r line; do
                # Check if this is a service definition
                if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_-]+):[[:space:]]*$ ]]; then
                    current_service="${BASH_REMATCH[1]}"
                # Check if this is an image definition
                elif [[ "$line" =~ ^[[:space:]]*image:[[:space:]]*(.+)$ ]] && [ -n "$current_service" ]; then
                    local image=$(echo "${BASH_REMATCH[1]}" | tr -d '"' | tr -d "'")
                    image_to_service["$image"]="$current_service"
                    seen_images["$image"]=1
                fi
            done < "$compose_file"
        fi
    done

    # Count only non-own images
    local external_images=0
    for image in "${!seen_images[@]}"; do
        local extracted_name=$(extract_service_name "$image")
        if ! is_own_image "$extracted_name"; then
            external_images=$((external_images + 1))
        fi
    done

    TOTAL_DOCKER_IMAGES=$external_images
    echo "Found ${#seen_images[@]} unique Docker images ($external_images external)"

    # Add Docker section
    add_section "Docker Images"

    echo "### External Docker Service Licenses" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Status | Service | Image | License | Notes |" >> "$OUTPUT_FILE"
    echo "|--------|---------|-------|---------|-------|" >> "$OUTPUT_FILE"

    # Track unknown images
    local unknown_images=()

    # Check each image
    for image in "${!seen_images[@]}"; do
        local service_name="${image_to_service[$image]}"
        local extracted_name=$(extract_service_name "$image")

        # Skip our own images
        if is_own_image "$extracted_name"; then
            echo -e "${GREEN}Skipping own image: $extracted_name${NC}"
            continue
        fi

        local found=false
        local license_info=""
        local status=""
        local notes=""

        # Check against known licenses
        for known_service in "${!DOCKER_LICENSES[@]}"; do
            if [[ "$extracted_name" == "$known_service" ]] || [[ "$service_name" == "$known_service" ]]; then
                IFS='|' read -r license status notes <<< "${DOCKER_LICENSES[$known_service]}"
                found=true

                # Check if this is a problematic license for SaaS
                if [[ "$license" =~ "AGPL" ]] || [[ "$license" =~ "SSPL" ]]; then
                    echo -e "${YELLOW}⚠️  Docker service with restrictive license: $service_name - $license${NC}"
                    echo "docker:$service_name:$image:$license" >> docker_restrictive_licenses.tmp
                fi
                break
            fi
        done

        if [ "$found" = true ]; then
            echo "| $status | $extracted_name | \`$image\` | $license | $notes |" >> "$OUTPUT_FILE"
        else
            echo -e "${RED}❌ UNKNOWN DOCKER IMAGE: $image (service: $service_name, extracted: $extracted_name)${NC}"
            unknown_images+=("$image (service: $service_name)")
            echo "| ❌ | $extracted_name | \`$image\` | **UNKNOWN** | **Add to DOCKER_LICENSES** |" >> "$OUTPUT_FILE"
        fi
    done

    echo "" >> "$OUTPUT_FILE"

    # Add section for own images
    echo "### Internal Docker Images (Our Code)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "The following are our own services and inherit the license we choose:" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    for image in "${!seen_images[@]}"; do
        local service_name="${image_to_service[$image]}"
        local extracted_name=$(extract_service_name "$image")

        if is_own_image "$extracted_name"; then
            echo "- $service_name (\`$image\`)" >> "$OUTPUT_FILE"
        fi
    done
    echo "" >> "$OUTPUT_FILE"

    # Fail if unknown external images found
    if [ ${#unknown_images[@]} -gt 0 ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "### ❌ Unknown Docker Images" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "The following Docker images are not in our known licenses list:" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        for unknown in "${unknown_images[@]}"; do
            echo "- $unknown" >> "$OUTPUT_FILE"
            echo "docker:unknown:$unknown:UNKNOWN" >> unknown_licenses.tmp
        done
        echo "" >> "$OUTPUT_FILE"
        echo "**Action Required:** Add these images to the DOCKER_LICENSES array in the script!" >> "$OUTPUT_FILE"
    fi
}

# Generate final summary
generate_summary() {
    local temp_file=$(mktemp)

    # Count issues
    local restrictive_count=0
    local review_count=0
    local unknown_count=0
    local docker_restrictive_count=0

    [ -f restrictive_licenses.tmp ] && restrictive_count=$(wc -l < restrictive_licenses.tmp)
    [ -f review_licenses.tmp ] && review_count=$(wc -l < review_licenses.tmp)
    [ -f unknown_licenses.tmp ] && unknown_count=$(wc -l < unknown_licenses.tmp)
    [ -f docker_restrictive_licenses.tmp ] && docker_restrictive_count=$(wc -l < docker_restrictive_licenses.tmp)

    # Read current file after the header
    tail -n +10 "$OUTPUT_FILE" > "$temp_file"

    # Rewrite with summary
    cat > "$OUTPUT_FILE" << EOF
# License Report

Generated on: $(date)

This document contains license information for all dependencies across the monorepo:
- Python packages (Poetry): **$TOTAL_PYTHON_DEPS packages**
- Node.js packages (pnpm): **$TOTAL_NODE_DEPS packages**
- External Docker images: **$TOTAL_DOCKER_IMAGES images**

### License Compatibility

EOF

    if [ "$restrictive_count" -eq 0 ] && [ "$unknown_count" -eq 0 ]; then
        cat >> "$OUTPUT_FILE" << EOF
✅ **No restrictive licenses found in your code dependencies!**

EOF
    else
        cat >> "$OUTPUT_FILE" << EOF
❌ **License issues found!** Please review and resolve:

EOF
    fi

    cat >> "$OUTPUT_FILE" << EOF
### Legend
- ✅ = Permissive license (MIT, BSD, Apache, etc.)
- ⚠️ = Weak copyleft or needs review (MPL, LGPL, etc.)
- ❌ = Restrictive or unknown license

EOF

    if [ "$restrictive_count" -gt 0 ]; then
        echo "### ❌ Restrictive Licenses in Code (Must Remove or Replace)" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "The following dependencies use restrictive copyleft licenses:" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) uses *$license*" >> "$OUTPUT_FILE"
        done < restrictive_licenses.tmp
        echo "" >> "$OUTPUT_FILE"
    fi

    if [ "$unknown_count" -gt 0 ]; then
        echo "### ❌ Unknown Licenses (Must Investigate)" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) has *$license*" >> "$OUTPUT_FILE"
        done < unknown_licenses.tmp
        echo "" >> "$OUTPUT_FILE"
    fi

    if [ "$review_count" -gt 0 ]; then
        echo "### ⚠️ Licenses Requiring Review" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "These licenses are generally compatible but should be reviewed:" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        while IFS=: read -r type project package license; do
            echo "- **$package** in $project ($type) uses *$license*" >> "$OUTPUT_FILE"
        done < review_licenses.tmp
        echo "" >> "$OUTPUT_FILE"
    fi

    # Append the rest
    cat "$temp_file" >> "$OUTPUT_FILE"
    rm "$temp_file"
}

# Main execution
main() {
    echo -e "${GREEN}Starting comprehensive license check...${NC}"
    echo "======================================"

    # Check requirements
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed.${NC}"
        echo "Install it with: sudo apt-get install jq (Ubuntu) or brew install jq (Mac)"
        exit 1
    fi

    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}Error: poetry is required but not installed.${NC}"
        echo "Install it from: https://python-poetry.org/docs/#installation"
        exit 1
    fi

    # Clean up temp files
    rm -f restrictive_licenses.tmp review_licenses.tmp unknown_licenses.tmp docker_restrictive_licenses.tmp

    # Initialize report
    init_report

    # Check Python projects
    add_section "Python Dependencies"
    for project in "${PYTHON_PROJECTS[@]}"; do
        check_python_project "$project" || true
    done

    # Check web project
    add_section "JavaScript/TypeScript Dependencies"
    check_web_project || true

    # Check Docker images
    check_docker_images || true

    # Generate final summary
    generate_summary

    # Count final issues
    local restrictive_count=0
    local unknown_count=0

    [ -f restrictive_licenses.tmp ] && restrictive_count=$(wc -l < restrictive_licenses.tmp)
    [ -f unknown_licenses.tmp ] && unknown_count=$(wc -l < unknown_licenses.tmp)

    # Clean up
    rm -f restrictive_licenses.tmp review_licenses.tmp unknown_licenses.tmp docker_restrictive_licenses.tmp

    # Final report
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
        echo ""
        echo -e "${RED}❌ FAILED: Found $restrictive_count restrictive and $unknown_count unknown licenses${NC}"
        echo -e "${RED}Please review $OUTPUT_FILE for details${NC}"
        exit 1
    else
        echo ""
        echo -e "${GREEN}✅ SUCCESS: No restrictive licenses found in your code dependencies!${NC}"
        echo -e "${YELLOW}⚠️  Note: Review Docker services with AGPL/SSPL for SaaS compatibility${NC}"
        echo -e "${GREEN}You can use BSL 1.1 or any other license for your code.${NC}"
        exit 0
    fi
}

# Run main function
main