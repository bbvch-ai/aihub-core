#!/bin/bash

# Infrastructure Installation Script
# This script installs both NGINX Ingress Controller and cert-manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Installing infrastructure for AIHub...${NC}"

# Check if we're in the right directory
if [ ! -d "ingress-controller" ] || [ ! -d "cert-manager" ] || [ ! -d "secret-manager" ]; then
    echo -e "${RED}❌ Please run this script from the helm directory${NC}"
    echo -e "${YELLOW}Usage: cd helm && ./install-infrastructure.sh${NC}"
    exit 1
fi

# Install NGINX Ingress Controller first
echo -e "${BLUE}🌐 Installing NGINX Ingress Controller...${NC}"
cd ingress-controller
./install.sh
cd ..

# Install cert-manager
echo -e "${BLUE}🔐 Installing cert-manager...${NC}"
cd cert-manager
./install.sh
cd ..

# Install External Secrets Operator
echo -e "${BLUE}🔑 Installing External Secrets Operator...${NC}"
cd secret-manager
./install.sh
cd ..

# Get the external IP of the ingress controller
echo -e "${YELLOW}🌐 Getting external IP of NGINX Ingress Controller...${NC}"
EXTERNAL_IP=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
fi

echo -e "${GREEN}✅ Complete infrastructure installed successfully!${NC}"

if [ -n "$EXTERNAL_IP" ]; then
    echo -e "${GREEN}🌐 External IP: $EXTERNAL_IP${NC}"
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo -e "   1. Update your DNS records to point to: $EXTERNAL_IP"
    echo -e "   2. Update email addresses in ClusterIssuers:"
    echo -e "      kubectl edit clusterissuer letsencrypt-prod"
    echo -e "      kubectl edit clusterissuer letsencrypt-staging"
    echo -e "   3. Configure Azure Key Vault integration:"
    echo -e "      cd secret-manager && ./install.sh"
    echo -e "   4. Deploy your AIHub application:"
    echo -e "      helm upgrade -i aihub ./aihub --namespace aihub --create-namespace --values values.yaml --values values.nightly.yaml"
else
    echo -e "${YELLOW}⚠️  External IP not available yet. Check with:${NC}"
    echo -e "   kubectl get service ingress-nginx-controller -n ingress-nginx"
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo -e "   1. Wait for external IP to be assigned"
    echo -e "   2. Update your DNS records to point to the external IP"
    echo -e "   3. Update email addresses in ClusterIssuers:"
    echo -e "      kubectl edit clusterissuer letsencrypt-prod"
    echo -e "      kubectl edit clusterissuer letsencrypt-staging"
    echo -e "   4. Configure Azure Key Vault integration:"
    echo -e "      cd secret-manager && ./install.sh"
    echo -e "   5. Deploy your AIHub application:"
    echo -e "      helm upgrade -i aihub ./aihub --namespace aihub --create-namespace --values values.yaml --values values.nightly.yaml"
fi

echo -e "${GREEN}🎉 All done! Your infrastructure is ready for AIHub.${NC}"
