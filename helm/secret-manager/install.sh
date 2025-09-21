#!/bin/bash

# External Secrets Operator Installation Script
# This script installs External Secrets Operator for Azure Key Vault integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="external-secrets-system"
RELEASE_NAME="external-secrets"
CHART_REPO="https://external-secrets.github.io/external-secrets/"
CHART_NAME="external-secrets/external-secrets"
CHART_VERSION="0.19.2"  # Pinned for stability

echo -e "${GREEN}🔐 Installing External Secrets Operator...${NC}"

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ helm is not installed or not in PATH${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Add the External Secrets Operator Helm repository (if not already added)
echo -e "${YELLOW}📦 Adding External Secrets Operator Helm repository...${NC}"
if ! helm repo list | grep -q "external-secrets"; then
    helm repo add external-secrets $CHART_REPO
else
    echo -e "${BLUE}ℹ️  External Secrets Operator repository already exists${NC}"
fi
helm repo update

# Check if external-secrets-system namespace exists
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${YELLOW}⚠️  Namespace $NAMESPACE already exists${NC}"
    read -p "Do you want to continue? This will upgrade the existing installation (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi
fi

# Install External Secrets Operator
echo -e "${YELLOW}🔧 Installing External Secrets Operator...${NC}"
helm upgrade --install $RELEASE_NAME $CHART_NAME \
    --version $CHART_VERSION \
    --namespace $NAMESPACE \
    --create-namespace \
    --values values.yaml \
    --wait \
    --timeout=5m

# Create Azure Key Vault SecretStore
echo -e "${BLUE}🔒 Creating Azure Key Vault SecretStore...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-keyvault
  namespace: $NAMESPACE
spec:
  provider:
    azurekv:
      tenantId: "YOUR_TENANT_ID"  # Replace with your Azure tenant ID
      vaultUrl: "https://YOUR_VAULT_NAME.vault.azure.net/"  # Replace with your Key Vault URL
      authSecretRef:
        clientId:
          name: azure-credentials
          key: client-id
        clientSecret:
          name: azure-credentials
          key: client-secret
      servicePrincipal:
        tenantId: "YOUR_TENANT_ID"  # Replace with your Azure tenant ID
        clientId: "YOUR_CLIENT_ID"  # Replace with your client ID
        clientSecret:
          name: azure-credentials
          key: client-secret
EOF

# Create Azure credentials secret template
echo -e "${BLUE}🔑 Creating Azure credentials secret template...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: azure-credentials
  namespace: $NAMESPACE
type: Opaque
data:
  client-id: ""  # Base64 encoded client ID
  client-secret: ""  # Base64 encoded client secret
EOF

echo -e "${GREEN}✅ External Secrets Operator installed successfully!${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "   1. Update Azure credentials in the secret:"
echo -e "      kubectl edit secret azure-credentials -n $NAMESPACE"
echo -e "   2. Update the SecretStore with your Azure Key Vault details:"
echo -e "      kubectl edit secretstore azure-keyvault -n $NAMESPACE"
echo -e "   3. Create ExternalSecret resources to sync secrets:"
echo -e "      See examples in the README.md file"
echo -e "   4. Test secret synchronization:"
echo -e "      kubectl get externalsecrets -A"
echo -e "      kubectl get secrets -A"

echo -e "${GREEN}🎉 Installation completed!${NC}"
