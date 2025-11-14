#!/bin/bash
# Helper script to access the swiss-llm-cloud-litellm-proxy instance

set -e

# Load environment variables
source "$(dirname "$0")/.env"

# Set OpenStack configuration
export OS_CLIENT_CONFIG_FILE="$(dirname "$0")/PCU-VFJXTLP-clouds.yaml"
export OS_CLOUD="PCP-VFJXTLP-dc4-a"

INSTANCE_ID="c19245dc-8ae8-4e7b-8556-7c41cd4024ea"
INSTANCE_NAME="swiss-llm-cloud-litellm-proxy"
INSTANCE_IP="83.228.225.209"

echo "=========================================="
echo "Swiss LLM Cloud - LiteLLM Proxy Instance"
echo "=========================================="
echo ""
echo "Instance: $INSTANCE_NAME"
echo "IP: $INSTANCE_IP"
echo "Region: dc4-a"
echo ""

# Show instance status
echo "Checking instance status..."
openstack server show "$INSTANCE_ID" --column status --column power_state

echo ""
echo "Available actions:"
echo "  1. Get console URL (for browser access)"
echo "  2. Try SSH access"
echo "  3. Show instance details"
echo ""
read -p "Choose an action (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Getting console URL..."
        openstack console url show "$INSTANCE_ID"
        echo ""
        echo "Steps to add your SSH key via console:"
        echo "  1. Open the URL above in your browser"
        echo "  2. Login as 'ubuntu' user"
        echo "  3. Run: curl -sL https://github.com/YOUR_GITHUB_USERNAME.keys >> ~/.ssh/authorized_keys"
        echo "     OR copy and run the add_ssh_key.sh script"
        ;;
    2)
        echo ""
        echo "Attempting SSH connection..."
        ssh -i "$SWISS_LLM_CLOUD_PUBLIC_KEY%.pub}" "ubuntu@$INSTANCE_IP"
        ;;
    3)
        echo ""
        openstack server show "$INSTANCE_ID"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
