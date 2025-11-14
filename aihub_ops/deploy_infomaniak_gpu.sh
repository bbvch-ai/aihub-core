#!/bin/bash
set -e

# Infomaniak GPU Server Deployment Script
# This script helps you deploy a GPU server on Infomaniak's OpenStack cloud

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Infomaniak GPU Server Deployment ===${NC}\n"

# Check if OS_PASSWORD is set
if [ -z "$OS_PASSWORD" ]; then
    echo -e "${YELLOW}OS_PASSWORD is not set.${NC}"
    read -sp "Enter your Infomaniak OpenStack password: " OS_PASSWORD
    export OS_PASSWORD
    echo
fi

# Set cloud config file
export OS_CLIENT_CONFIG_FILE="/home/thomas/Projects/aihub-core/aihub_ops/PCU-AALAZWD-clouds.yaml"

# Ask for region
echo -e "\n${YELLOW}Available regions:${NC}"
echo "1) dc3-a"
echo "2) dc4-a"
read -p "Select region [1]: " REGION_CHOICE
REGION_CHOICE=${REGION_CHOICE:-1}

if [ "$REGION_CHOICE" = "1" ]; then
    CLOUD="PCP-AALAZWD-dc3-a"
else
    CLOUD="PCP-AALAZWD-dc4-a"
fi

echo -e "\n${GREEN}Using cloud: $CLOUD${NC}"

# Test connection
echo -e "\n${YELLOW}Testing connection...${NC}"
if ! openstack --os-cloud "$CLOUD" token issue > /dev/null 2>&1; then
    echo -e "${RED}Failed to authenticate. Check your password and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authentication successful${NC}"

# List GPU flavors
echo -e "\n${YELLOW}Searching for GPU flavors...${NC}"
GPU_FLAVORS=$(openstack --os-cloud "$CLOUD" flavor list -f value -c Name -c RAM -c VCPUs | grep -iE "(gpu|a100|v100|h100|rtx|nvidia|tesla|a10|l4|t4)" || true)

if [ -z "$GPU_FLAVORS" ]; then
    echo -e "${YELLOW}No GPU flavors found with standard naming.${NC}"
    echo -e "\n${YELLOW}Showing all available flavors (look for high RAM/vCPU):${NC}"
    GPU_FLAVORS=$(openstack --os-cloud "$CLOUD" flavor list -f value -c Name -c RAM -c VCPUs | sort -k2 -nr | head -20)

    if [ -z "$GPU_FLAVORS" ]; then
        echo -e "${RED}No flavors found in this region.${NC}"
        echo "Try the other region or contact Infomaniak support."
        exit 1
    fi
fi

echo "$GPU_FLAVORS" | nl -w2 -s') '
read -p "Select GPU flavor number: " FLAVOR_NUM

FLAVOR_NAME=$(echo "$GPU_FLAVORS" | sed -n "${FLAVOR_NUM}p" | awk '{print $1}')
echo -e "${GREEN}Selected flavor: $FLAVOR_NAME${NC}"

# List Ubuntu images
echo -e "\n${YELLOW}Finding Ubuntu 24.04 images...${NC}"
IMAGES=$(openstack --os-cloud "$CLOUD" image list -f value -c Name -c ID | grep -i "ubuntu.*24\.04" || true)

if [ -z "$IMAGES" ]; then
    echo -e "${RED}No Ubuntu 24.04 images found.${NC}"
    echo "Available images:"
    openstack --os-cloud "$CLOUD" image list | grep -i ubuntu
    exit 1
fi

echo "$IMAGES" | nl -w2 -s') '
read -p "Select image number [1]: " IMAGE_NUM
IMAGE_NUM=${IMAGE_NUM:-1}

IMAGE_ID=$(echo "$IMAGES" | sed -n "${IMAGE_NUM}p" | awk '{print $NF}')
IMAGE_NAME=$(echo "$IMAGES" | sed -n "${IMAGE_NUM}p" | sed "s/ $IMAGE_ID//")
echo -e "${GREEN}Selected image: $IMAGE_NAME${NC}"

# List networks
echo -e "\n${YELLOW}Available networks:${NC}"
NETWORKS=$(openstack --os-cloud "$CLOUD" network list -f value -c Name -c ID)
echo "$NETWORKS" | nl -w2 -s') '
read -p "Select network number [1]: " NET_NUM
NET_NUM=${NET_NUM:-1}

NETWORK_ID=$(echo "$NETWORKS" | sed -n "${NET_NUM}p" | awk '{print $NF}')
NETWORK_NAME=$(echo "$NETWORKS" | sed -n "${NET_NUM}p" | sed "s/ $NETWORK_ID//")
echo -e "${GREEN}Selected network: $NETWORK_NAME${NC}"

# SSH key (optional)
echo -e "\n${YELLOW}SSH Key Setup:${NC}"
KEYPAIRS=$(openstack --os-cloud "$CLOUD" keypair list -f value -c Name 2>/dev/null || true)

if [ -n "$KEYPAIRS" ]; then
    echo "Available SSH keys:"
    echo "$KEYPAIRS" | nl -w2 -s') '
    echo "0) Skip SSH key (use password auth)"
    read -p "Select SSH key number [0]: " KEY_NUM
    KEY_NUM=${KEY_NUM:-0}

    if [ "$KEY_NUM" != "0" ]; then
        KEY_NAME=$(echo "$KEYPAIRS" | sed -n "${KEY_NUM}p")
        SSH_KEY_PARAM="--key-name $KEY_NAME"
        echo -e "${GREEN}Using SSH key: $KEY_NAME${NC}"
    else
        SSH_KEY_PARAM=""
        echo -e "${YELLOW}No SSH key selected. Use password for login.${NC}"
    fi
else
    SSH_KEY_PARAM=""
    echo -e "${YELLOW}No SSH keys found. To add one, run:${NC}"
    echo "openstack --os-cloud $CLOUD keypair create --public-key ~/.ssh/id_rsa.pub my-key"
fi

# Server name
read -p $'\nEnter server name [aihub-gpu-server]: ' SERVER_NAME
SERVER_NAME=${SERVER_NAME:-aihub-gpu-server}

# Summary
echo -e "\n${GREEN}=== Deployment Summary ===${NC}"
echo "Cloud: $CLOUD"
echo "Server Name: $SERVER_NAME"
echo "Flavor: $FLAVOR_NAME"
echo "Image: $IMAGE_NAME"
echo "Network: $NETWORK_NAME"
[ -n "$KEY_NAME" ] && echo "SSH Key: $KEY_NAME"

read -p $'\nProceed with deployment? [y/N]: ' CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Create server
echo -e "\n${YELLOW}Creating server...${NC}"
SERVER_OUTPUT=$(openstack --os-cloud "$CLOUD" server create \
    --flavor "$FLAVOR_NAME" \
    --image "$IMAGE_ID" \
    --network "$NETWORK_ID" \
    $SSH_KEY_PARAM \
    "$SERVER_NAME" \
    -f json)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Server creation initiated!${NC}"

    # Wait for server to become active
    echo -e "\n${YELLOW}Waiting for server to become active...${NC}"
    for i in {1..60}; do
        STATUS=$(openstack --os-cloud "$CLOUD" server show "$SERVER_NAME" -f value -c status 2>/dev/null || echo "ERROR")

        if [ "$STATUS" = "ACTIVE" ]; then
            echo -e "${GREEN}✓ Server is active!${NC}"
            break
        elif [ "$STATUS" = "ERROR" ]; then
            echo -e "${RED}✗ Server creation failed!${NC}"
            openstack --os-cloud "$CLOUD" server show "$SERVER_NAME"
            exit 1
        fi

        echo -n "."
        sleep 5
    done

    # Get server details
    echo -e "\n${GREEN}=== Server Details ===${NC}"
    openstack --os-cloud "$CLOUD" server show "$SERVER_NAME" -c name -c status -c addresses -c flavor

    # Get IP address
    SERVER_IP=$(openstack --os-cloud "$CLOUD" server show "$SERVER_NAME" -f value -c addresses | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1)

    if [ -n "$SERVER_IP" ]; then
        echo -e "\n${GREEN}Server IP: $SERVER_IP${NC}"
        echo -e "\n${YELLOW}To connect:${NC}"
        echo "ssh ubuntu@$SERVER_IP"

        echo -e "\n${YELLOW}To verify GPU:${NC}"
        echo "ssh ubuntu@$SERVER_IP 'nvidia-smi'"
    fi

else
    echo -e "${RED}✗ Failed to create server${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "\n${YELLOW}Useful commands:${NC}"
echo "View server: openstack --os-cloud $CLOUD server show $SERVER_NAME"
echo "Delete server: openstack --os-cloud $CLOUD server delete $SERVER_NAME"
echo "Console log: openstack --os-cloud $CLOUD console log show $SERVER_NAME"
