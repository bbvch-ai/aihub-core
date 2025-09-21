#!/bin/bash

# Cert-Manager Installation Script
# This script installs cert-manager for automatic SSL certificate management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="cert-manager"
RELEASE_NAME="cert-manager"
CHART_REPO="https://charts.jetstack.io"
CHART_NAME="jetstack/cert-manager"
CHART_VERSION="v1.18.2"  # Pinned for stability

echo -e "${GREEN}🔐 Installing cert-manager...${NC}"

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

# Add the cert-manager Helm repository (if not already added)
echo -e "${YELLOW}📦 Adding cert-manager Helm repository...${NC}"
if ! helm repo list | grep -q "jetstack"; then
    helm repo add jetstack $CHART_REPO
else
    echo -e "${BLUE}ℹ️  Jetstack repository already exists${NC}"
fi
helm repo update

# Check if cert-manager namespace exists
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${YELLOW}⚠️  Namespace $NAMESPACE already exists${NC}"
    read -p "Do you want to continue? This will upgrade the existing installation (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi
fi

# Install cert-manager
echo -e "${YELLOW}🔧 Installing cert-manager...${NC}"
helm upgrade --install $RELEASE_NAME $CHART_NAME \
    --version $CHART_VERSION \
    --namespace $NAMESPACE \
    --create-namespace \
    --values values.yaml \
    --wait \
    --timeout=5m

# Create Let's Encrypt ClusterIssuer
echo -e "${BLUE}🔒 Creating Let's Encrypt ClusterIssuer...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@ai-hub.bbv.ch  # Change this to your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Create staging ClusterIssuer for testing
echo -e "${BLUE}🧪 Creating Let's Encrypt Staging ClusterIssuer...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@ai-hub.bbv.ch  # Change this to your email
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

echo -e "${GREEN}✅ cert-manager installed successfully!${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "   1. Update the email in the ClusterIssuers:"
echo -e "      kubectl edit clusterissuer letsencrypt-prod"
echo -e "      kubectl edit clusterissuer letsencrypt-staging"
echo -e "   2. Test certificate issuance:"
echo -e "      kubectl get certificates -A"
echo -e "   3. Install NGINX Ingress Controller:"
echo -e "      cd ../ingress-controller && ./install.sh"
echo -e "   4. Deploy your AIHub application with SSL annotations"

echo -e "${GREEN}🎉 Installation completed!${NC}"
