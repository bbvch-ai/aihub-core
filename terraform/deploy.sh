#!/bin/bash

# =============================================================================
# AI HUB MULTI-CLOUD DEPLOYMENT SCRIPT
# =============================================================================
# Simple script that takes one parameter: azure or stoney
# All shared variables are injected directly from the script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage
show_usage() {
    echo "AI Hub Multi-Cloud Deployment Script"
    echo "===================================="
    echo ""
    echo "Usage: $0 <cloud-provider> [environment] [action]"
    echo ""
    echo "Cloud providers:"
    echo "  azure  - Deploy to Microsoft Azure (requires existing resource group)"
    echo "  stoney - Deploy to Stoney cloud (OpenStack)"
    echo ""
    echo "Environment (optional):"
    echo "  test      - Test environment (default)"
    echo "  prod      - Production environment"
    echo ""
    echo "Action (optional):"
    echo "  plan      - Plan deployment (default)"
    echo "  apply     - Apply deployment"
    echo "  destroy   - Destroy resources"
    echo ""
    echo "Examples:"
    echo "  $0 azure test plan"
    echo "  $0 stoney prod apply"
    echo "  $0 azure test destroy"
}

# Check arguments
if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

CLOUD_PROVIDER=$1
ENVIRONMENT=${2:-test}
ACTION=${3:-plan}

# Validate cloud provider
if [[ ! "$CLOUD_PROVIDER" =~ ^(azure|stoney)$ ]]; then
    echo -e "${RED}❌ Invalid cloud provider: $CLOUD_PROVIDER${NC}"
    echo "Valid options: azure, stoney"
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(test|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid options: test, prod"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(plan|apply|destroy)$ ]]; then
    echo -e "${RED}❌ Invalid action: $ACTION${NC}"
    echo "Valid options: plan, apply, destroy"
    exit 1
fi

echo -e "${BLUE}🚀 AI Hub $CLOUD_PROVIDER Deployment ($ENVIRONMENT)${NC}"
echo "=============================================="

# Set cloud-specific directory
CLOUD_DIR="$SCRIPT_DIR/$CLOUD_PROVIDER"

# Check if cloud directory exists
if [ ! -d "$CLOUD_DIR" ]; then
    echo -e "${RED}❌ Cloud directory not found: $CLOUD_DIR${NC}"
    exit 1
fi

cd "$CLOUD_DIR"

# =============================================================================
# SHARED VARIABLES (injected directly)
# =============================================================================

# Common configuration
CLUSTER_NAME="aihub-${CLOUD_PROVIDER}-${ENVIRONMENT}"
KUBERNETES_VERSION="1.30.2"
PROJECT_NAME="aihub"

# Node pool configuration
SYSTEM_NODE_COUNT=1
SYSTEM_OS_DISK_SIZE_GB=64
USER_MIN_COUNT=0
USER_MAX_COUNT=3
USER_OS_DISK_SIZE_GB=128

# Tags (using individual variables instead of JSON)
TAG_PROJECT="$PROJECT_NAME"
TAG_ENVIRONMENT="$ENVIRONMENT"
TAG_CLOUD="$CLOUD_PROVIDER"
TAG_MANAGED_BY="terraform"

# =============================================================================
# CLOUD-SPECIFIC CONFIGURATION
# =============================================================================

if [ "$CLOUD_PROVIDER" = "azure" ]; then
    # Azure-specific variables
    if [ "$ENVIRONMENT" = "test" ]; then
        RESOURCE_GROUP_NAME="aks-test"
    elif [ "$ENVIRONMENT" = "prod" ]; then
        RESOURCE_GROUP_NAME="aks-prod"  # To be determined
    fi
    
    # Get subscription ID from Azure CLI
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    if [ -z "$SUBSCRIPTION_ID" ]; then
        echo -e "${RED}❌ Could not get Azure subscription ID. Please ensure you're logged in.${NC}"
        exit 1
    fi
    
    SYSTEM_VM_SIZE="Standard_D4s_v5"
    USER_VM_SIZE="Standard_D4as_v5"
    USER_SPOT_MAX_PRICE=-1
    NETWORK_PLUGIN="azure"
    OUTBOUND_TYPE="loadBalancer"
    
    # Check prerequisites
    echo -e "${YELLOW}🔍 Checking Azure prerequisites...${NC}"
    
    if ! command -v az &> /dev/null; then
        echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        echo -e "${YELLOW}⚠️  Not logged in to Azure. Please log in first.${NC}"
        az login
    fi
    
    # Check if resource group exists
    if ! az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        echo -e "${RED}❌ Resource group '$RESOURCE_GROUP_NAME' not found. Please create it first.${NC}"
        echo "Create it with: az group create --name $RESOURCE_GROUP_NAME --location 'Switzerland North'"
        echo ""
        echo "If the resource group exists, you may need to re-authenticate:"
        echo "az login --scope https://management.core.windows.net//.default"
        exit 1
    fi

elif [ "$CLOUD_PROVIDER" = "stoney" ]; then
    # Stoney cloud-specific variables
    REGION="RegionOne"
    AVAILABILITY_ZONE="nova"
    KEYPAIR_NAME="aihub-keypair-${ENVIRONMENT}"
    IMAGE_NAME="Ubuntu 22.04 (240702): Kubernetes v1.30.2"
    IMAGE_ID="db68e8e8-d4b4-4c4f-af41-4166eb33973d"
    FLAVOR_SYSTEM="Standard Düdingen c002m0004"
    FLAVOR_USER="Standard Düdingen c002m0004"
    NETWORK_NAME="aihub-network-${ENVIRONMENT}"
    SUBNET_CIDR="10.0.0.0/24"
    EXTERNAL_NETWORK="public"
    
    # Check prerequisites
    echo -e "${YELLOW}🔍 Checking Stoney cloud prerequisites...${NC}"
    
    if ! command -v openstack &> /dev/null; then
        echo -e "${RED}❌ OpenStack CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Require that the environment is already authenticated (no hardcoded RC path)
    if ! openstack token issue &> /dev/null; then
        echo -e "${YELLOW}⚠️  Not authenticated with Stoney cloud.${NC}"
        echo "Source your RC file (e.g., 'source ~/path/to/openrc.sh') or set OS_* variables."
        echo "Alternatively, use application credentials:"
        echo "  export OS_AUTH_TYPE=v3applicationcredential"
        echo "  export OS_APPLICATION_CREDENTIAL_ID=..."
        echo "  export OS_APPLICATION_CREDENTIAL_SECRET=..."
        exit 1
    fi
    
    # Check if keypair exists
    if ! openstack keypair show "$KEYPAIR_NAME" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Keypair '$KEYPAIR_NAME' not found. Please create it first:${NC}"
        echo "openstack keypair create --public-key ~/.ssh/id_rsa.pub $KEYPAIR_NAME"
        exit 1
    else
        echo -e "${GREEN}✅ Keypair '$KEYPAIR_NAME' found${NC}"
    fi
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# =============================================================================
# TERRAFORM EXECUTION
# =============================================================================

# Initialize Terraform
echo -e "${BLUE}🔧 Initializing Terraform...${NC}"
terraform init

# Prepare terraform command with variables
TF_VARS=""
if [ "$CLOUD_PROVIDER" = "azure" ]; then
    TF_VARS="-var cluster_name=$CLUSTER_NAME"
    TF_VARS="$TF_VARS -var kubernetes_version=$KUBERNETES_VERSION"
    TF_VARS="$TF_VARS -var project_name=$PROJECT_NAME"
    TF_VARS="$TF_VARS -var environment=$ENVIRONMENT"
    TF_VARS="$TF_VARS -var system_node_count=$SYSTEM_NODE_COUNT"
    TF_VARS="$TF_VARS -var system_os_disk_size_gb=$SYSTEM_OS_DISK_SIZE_GB"
    TF_VARS="$TF_VARS -var user_min_count=$USER_MIN_COUNT"
    TF_VARS="$TF_VARS -var user_max_count=$USER_MAX_COUNT"
    TF_VARS="$TF_VARS -var user_os_disk_size_gb=$USER_OS_DISK_SIZE_GB"
    TF_VARS="$TF_VARS -var tag_project=$TAG_PROJECT"
    TF_VARS="$TF_VARS -var tag_environment=$TAG_ENVIRONMENT"
    TF_VARS="$TF_VARS -var tag_cloud=$TAG_CLOUD"
    TF_VARS="$TF_VARS -var tag_managed_by=$TAG_MANAGED_BY"
    TF_VARS="$TF_VARS -var subscription_id=$SUBSCRIPTION_ID"
    TF_VARS="$TF_VARS -var resource_group_name=$RESOURCE_GROUP_NAME"
    TF_VARS="$TF_VARS -var system_vm_size=$SYSTEM_VM_SIZE"
    TF_VARS="$TF_VARS -var user_vm_size=$USER_VM_SIZE"
    TF_VARS="$TF_VARS -var user_spot_max_price=$USER_SPOT_MAX_PRICE"
    TF_VARS="$TF_VARS -var network_plugin=$NETWORK_PLUGIN"
    TF_VARS="$TF_VARS -var outbound_type=$OUTBOUND_TYPE"

elif [ "$CLOUD_PROVIDER" = "stoney" ]; then
    TF_VARS="-var cluster_name=$CLUSTER_NAME"
    TF_VARS="$TF_VARS -var kubernetes_version=$KUBERNETES_VERSION"
    TF_VARS="$TF_VARS -var project_name=$PROJECT_NAME"
    TF_VARS="$TF_VARS -var environment=$ENVIRONMENT"
    TF_VARS="$TF_VARS -var system_node_count=$SYSTEM_NODE_COUNT"
    TF_VARS="$TF_VARS -var system_os_disk_size_gb=$SYSTEM_OS_DISK_SIZE_GB"
    TF_VARS="$TF_VARS -var user_min_count=$USER_MIN_COUNT"
    TF_VARS="$TF_VARS -var user_max_count=$USER_MAX_COUNT"
    TF_VARS="$TF_VARS -var user_os_disk_size_gb=$USER_OS_DISK_SIZE_GB"
    TF_VARS="$TF_VARS -var tag_project=$TAG_PROJECT"
    TF_VARS="$TF_VARS -var tag_environment=$TAG_ENVIRONMENT"
    TF_VARS="$TF_VARS -var tag_cloud=$TAG_CLOUD"
    TF_VARS="$TF_VARS -var tag_managed_by=$TAG_MANAGED_BY"
    TF_VARS="$TF_VARS -var region=$REGION"
    TF_VARS="$TF_VARS -var availability_zone=$AVAILABILITY_ZONE"
    TF_VARS="$TF_VARS -var keypair_name=$KEYPAIR_NAME"
    TF_VARS="$TF_VARS -var image_name='$IMAGE_NAME'"
    TF_VARS="$TF_VARS -var flavor_system='$FLAVOR_SYSTEM'"
    TF_VARS="$TF_VARS -var flavor_user='$FLAVOR_USER'"
    TF_VARS="$TF_VARS -var network_name=$NETWORK_NAME"
    TF_VARS="$TF_VARS -var subnet_cidr=$SUBNET_CIDR"
    TF_VARS="$TF_VARS -var external_network=$EXTERNAL_NETWORK"
fi

# Create terraform.tfvars file for complex values
echo -e "${BLUE}📝 Creating terraform.tfvars file...${NC}"
cat > terraform.tfvars << EOF
cluster_name = "$CLUSTER_NAME"
kubernetes_version = "$KUBERNETES_VERSION"
project_name = "$PROJECT_NAME"
environment = "$ENVIRONMENT"
system_node_count = $SYSTEM_NODE_COUNT
system_os_disk_size_gb = $SYSTEM_OS_DISK_SIZE_GB
user_min_count = $USER_MIN_COUNT
user_max_count = $USER_MAX_COUNT
user_os_disk_size_gb = $USER_OS_DISK_SIZE_GB
tag_project = "$TAG_PROJECT"
tag_environment = "$TAG_ENVIRONMENT"
tag_cloud = "$TAG_CLOUD"
tag_managed_by = "$TAG_MANAGED_BY"
EOF

if [ "$CLOUD_PROVIDER" = "azure" ]; then
    cat >> terraform.tfvars << EOF
subscription_id = "$SUBSCRIPTION_ID"
resource_group_name = "$RESOURCE_GROUP_NAME"
system_vm_size = "$SYSTEM_VM_SIZE"
user_vm_size = "$USER_VM_SIZE"
user_spot_max_price = $USER_SPOT_MAX_PRICE
network_plugin = "$NETWORK_PLUGIN"
outbound_type = "$OUTBOUND_TYPE"
EOF
elif [ "$CLOUD_PROVIDER" = "stoney" ]; then
    cat >> terraform.tfvars << EOF
region = "$REGION"
availability_zone = "$AVAILABILITY_ZONE"
keypair_name = "$KEYPAIR_NAME"
image_name = "$IMAGE_NAME"
image_id = "$IMAGE_ID"
flavor_system = "$FLAVOR_SYSTEM"
flavor_user = "$FLAVOR_USER"
network_name = "$NETWORK_NAME"
subnet_cidr = "$SUBNET_CIDR"
external_network = "$EXTERNAL_NETWORK"
EOF
fi

# Execute Terraform command
echo -e "${BLUE}🚀 Running Terraform $ACTION...${NC}"

if [ "$ACTION" = "plan" ]; then
    terraform plan
elif [ "$ACTION" = "apply" ]; then
    terraform plan -out=tfplan
    echo -e "${YELLOW}⚠️  This will create $CLOUD_PROVIDER resources. Do you want to continue? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
        
        # Show cluster information
        echo ""
        echo -e "${BLUE}📊 Cluster Information:${NC}"
        echo "========================"
        echo "Cluster Name: $CLUSTER_NAME"
        echo "Environment: $ENVIRONMENT"
        echo "Cloud Provider: $CLOUD_PROVIDER"
        
        if [ "$CLOUD_PROVIDER" = "azure" ]; then
            echo "Resource Group: $RESOURCE_GROUP_NAME"
            echo ""
            echo -e "${YELLOW}🔧 Setting up kubectl access...${NC}"
            az aks get-credentials --resource-group "$RESOURCE_GROUP_NAME" --name "$CLUSTER_NAME" --overwrite-existing
            
        elif [ "$CLOUD_PROVIDER" = "stoney" ]; then
            echo ""
            echo -e "${YELLOW}🔧 Setting up kubectl access...${NC}"
            openstack coe cluster config --dir ~/.kube "$CLUSTER_NAME"
        fi
        
        # Test cluster access
        if kubectl get nodes &> /dev/null; then
            echo -e "${GREEN}✅ Cluster access successful!${NC}"
            echo ""
            echo -e "${BLUE}📋 Cluster Status:${NC}"
            kubectl get nodes -o wide
        else
            echo -e "${RED}❌ Failed to access cluster. Please check your configuration.${NC}"
        fi
        
    else
        echo -e "${YELLOW}❌ Deployment cancelled by user${NC}"
    fi
elif [ "$ACTION" = "destroy" ]; then
    echo -e "${YELLOW}⚠️  This will DESTROY all $CLOUD_PROVIDER resources. Are you sure? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        terraform destroy -auto-approve
        echo -e "${GREEN}✅ Resources destroyed successfully!${NC}"
    else
        echo -e "${YELLOW}❌ Destruction cancelled by user${NC}"
    fi
fi

# Clean up terraform.tfvars file
rm -f terraform.tfvars

echo ""
echo -e "${GREEN}🎉 $CLOUD_PROVIDER $ACTION completed!${NC}"
