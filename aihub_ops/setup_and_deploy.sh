#!/bin/bash
set -e

# If running in Poetry environment, use poetry's openstack
if [ -n "$VIRTUAL_ENV" ]; then
    OPENSTACK_CMD="openstack"
else
    # Try to use Poetry's virtualenv openstack directly
    POETRY_OPENSTACK="/home/thomas/.cache/pypoetry/virtualenvs/aihub-core-vhpK4mlS-py3.13/bin/openstack"
    if [ -x "$POETRY_OPENSTACK" ]; then
        OPENSTACK_CMD="$POETRY_OPENSTACK"
    else
        OPENSTACK_CMD="openstack"
    fi
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    set -o allexport
    source .env
    set +o allexport
else
    echo "Error: .env file not found"
    exit 1
fi

# Ensure OS_PASSWORD is exported
export OS_PASSWORD

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Infomaniak OpenStack Setup ===${NC}\n"

# Check if OpenStack CLI is installed
if ! command -v openstack &> /dev/null; then
    echo -e "${RED}OpenStack CLI not found!${NC}"
    echo "Installing python-openstackclient..."
    pip install python-openstackclient
fi

# Ensure clouds.yaml symlink exists
CLOUDS_FILE="$(pwd)/PCU-AALAZWD-clouds.yaml"
OPENSTACK_CONFIG_DIR="$HOME/.config/openstack"
CLOUDS_YAML_LINK="$OPENSTACK_CONFIG_DIR/clouds.yaml"

if [ ! -L "$CLOUDS_YAML_LINK" ] || [ "$(readlink -f "$CLOUDS_YAML_LINK")" != "$CLOUDS_FILE" ]; then
    echo -e "${YELLOW}Setting up clouds.yaml symlink...${NC}"
    mkdir -p "$OPENSTACK_CONFIG_DIR"
    ln -sf "$CLOUDS_FILE" "$CLOUDS_YAML_LINK"
    echo -e "${GREEN}✓ clouds.yaml configured${NC}"
fi

# Ask for region
echo -e "${YELLOW}Select region:${NC}"
echo "1) dc3-a"
echo "2) dc4-a"
read -p "Choice [1]: " REGION_CHOICE
REGION_CHOICE=${REGION_CHOICE:-1}

if [ "$REGION_CHOICE" = "1" ]; then
    CLOUD="PCP-AALAZWD-dc3-a"
else
    CLOUD="PCP-AALAZWD-dc4-a"
fi

echo -e "\n${GREEN}Using cloud: $CLOUD${NC}"

# Test authentication
echo -e "\n${YELLOW}Testing authentication...${NC}"
set +e  # Temporarily disable exit on error
AUTH_OUTPUT=$(openstack --os-cloud "$CLOUD" token issue 2>&1)
AUTH_EXIT_CODE=$?
set -e  # Re-enable exit on error

if [ $AUTH_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Authentication failed!${NC}"
    echo "$AUTH_OUTPUT"
    echo -e "\n${YELLOW}Debug info:${NC}"
    echo "OS_PASSWORD length: ${#OS_PASSWORD}"
    echo "Cloud: $CLOUD"
    exit 1
fi
echo -e "${GREEN}✓ Authentication successful${NC}"

# Check/upload SSH key
echo -e "\n${YELLOW}Checking SSH key...${NC}"

if [ ! -f "$SWISS_LLM_CLOUD_PUBLIC_KEY" ]; then
    echo -e "${RED}SSH public key not found at: $SWISS_LLM_CLOUD_PUBLIC_KEY${NC}"
    echo "Do you want to continue without SSH key setup? (you'll use password login)"
    read -p "[y/N]: " SKIP_SSH
    if [ "$SKIP_SSH" != "y" ] && [ "$SKIP_SSH" != "Y" ]; then
        exit 1
    fi
    USE_SSH_KEY=false
else
    # Check if key already exists in OpenStack
    KEY_NAME="swiss-llm-cloud-key"
    set +e
    openstack --os-cloud "$CLOUD" keypair show "$KEY_NAME" &> /dev/null
    KEY_EXISTS=$?
    set -e

    if [ $KEY_EXISTS -eq 0 ]; then
        echo -e "${GREEN}✓ SSH key '$KEY_NAME' already exists in OpenStack${NC}"
    else
        echo -e "${YELLOW}Uploading SSH key to OpenStack...${NC}"
        openstack --os-cloud "$CLOUD" keypair create \
            --public-key "$SWISS_LLM_CLOUD_PUBLIC_KEY" \
            "$KEY_NAME"
        echo -e "${GREEN}✓ SSH key uploaded${NC}"
    fi
    USE_SSH_KEY=true
fi

# Now run the deployment script
echo -e "\n${GREEN}=== Starting Deployment ===${NC}\n"
export CLOUD
export KEY_NAME
export USE_SSH_KEY

# Run the deployment script
./deploy_infomaniak_gpu.sh
