#!/bin/bash

# NGINX Ingress Controller Installation Script
# This script installs the NGINX Ingress Controller using Helm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse environment parameter
ENVIRONMENT="${1:-prod}"

# Validate environment parameter
if [[ "$ENVIRONMENT" != "test" && "$ENVIRONMENT" != "prod" ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Usage: ./install.sh [test|prod]${NC}"
    echo -e "${YELLOW}Default: prod${NC}"
    exit 1
fi

# Set values file based on environment
VALUES_FILE="values.${ENVIRONMENT}.yaml"

# Check if environment-specific values file exists
if [ ! -f "$VALUES_FILE" ]; then
    echo -e "${RED}❌ Values file not found: $VALUES_FILE${NC}"
    exit 1
fi

# Configuration
NAMESPACE="ingress-nginx"
RELEASE_NAME="ingress-nginx"
CHART_REPO="https://kubernetes.github.io/ingress-nginx"
CHART_NAME="ingress-nginx/ingress-nginx"
CHART_VERSION="4.13.2"  # Pinned for stability

echo -e "${GREEN}🚀 Installing NGINX Ingress Controller (${ENVIRONMENT})...${NC}"
echo -e "${YELLOW}📄 Using values files: values.yaml, ${VALUES_FILE}${NC}"

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

echo -e "${YELLOW}📋 Prerequisites check passed${NC}"

# Add the NGINX Ingress Helm repository (if not already added)
echo -e "${YELLOW}📦 Adding NGINX Ingress Helm repository...${NC}"
if ! helm repo list | grep -q "ingress-nginx"; then
    helm repo add ingress-nginx $CHART_REPO
else
    echo -e "${BLUE}ℹ️  NGINX Ingress repository already exists${NC}"
fi
helm repo update

# Check if ingress-nginx namespace exists
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${YELLOW}⚠️  Namespace $NAMESPACE already exists${NC}"
    read -p "Do you want to continue? This will upgrade the existing installation (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi
fi

# Install or upgrade NGINX Ingress Controller
echo -e "${YELLOW}🔧 Installing NGINX Ingress Controller...${NC}"
helm upgrade --install $RELEASE_NAME $CHART_NAME \
    --version $CHART_VERSION \
    --namespace $NAMESPACE \
    --create-namespace \
    --values values.yaml \
    --values $VALUES_FILE \
    --wait \
    --timeout=5m

# Get the external IP
echo -e "${YELLOW}🌐 Getting external IP...${NC}"
EXTERNAL_IP=$(kubectl get service $RELEASE_NAME-controller -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get service $RELEASE_NAME-controller -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ -n "$EXTERNAL_IP" ]; then
    echo -e "${GREEN}✅ NGINX Ingress Controller installed successfully!${NC}"
    echo -e "${GREEN}🌐 External IP: $EXTERNAL_IP${NC}"
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo -e "   1. Update your DNS records to point to: $EXTERNAL_IP"
    echo -e "   2. Install cert-manager for SSL certificates:"
    echo -e "      cd ../cert-manager && ./install.sh"
    echo -e "   3. Deploy your AIHub application:"
    echo -e "      helm upgrade -i aihub ./helm/aihub --namespace aihub --create-namespace --values values.yaml --values values.nightly.yaml"
else
    echo -e "${YELLOW}⚠️  External IP not available yet. Check with:${NC}"
    echo -e "   kubectl get service $RELEASE_NAME-controller -n $NAMESPACE"
fi

echo -e "${GREEN}🎉 Installation completed!${NC}"
