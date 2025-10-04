# AI Hub Multi-Cloud Terraform

Simple multi-cloud deployment for AI Hub Kubernetes clusters supporting both Azure and Stoney cloud.

## 🎯 **Simple Architecture**

```
terraform/
├── azure/           # Standalone Azure Terraform
├── stoney/          # Standalone Stoney cloud Terraform  
└── deploy.sh        # Single script: ./deploy.sh azure|stoney
```

## 🚀 **Quick Start**

### **Deploy to Azure**
```bash
# Plan deployment
./deploy.sh azure test plan

# Apply deployment
./deploy.sh azure test apply

# Destroy resources
./deploy.sh azure test destroy
```

### **Deploy to Stoney cloud**
```bash
# Plan deployment
./deploy.sh stoney test plan

# Apply deployment
./deploy.sh stoney test apply

# Destroy resources
./deploy.sh stoney test destroy
```

## 📋 **Usage**

```bash
./deploy.sh <cloud-provider> [environment] [action]
```

**Parameters:**
- `cloud-provider`: `azure` or `stoney`
- `environment`: `test` or `prod` (default: `test`)
- `action`: `plan`, `apply`, or `destroy` (default: `plan`)

## 🔧 **Configuration**

All shared variables are **automatically injected** by the script:
- **Cluster name**: `aihub-{cloud}-{environment}`
- **Kubernetes version**: `1.30.2`
- **Project name**: `aihub`
- **Node configuration**: 1 system node, 0-3 user nodes
- **Disk sizes**: 64GB system, 128GB user
- **Tags**: Project, environment, cloud provider
- **Azure subscription ID**: Automatically detected from Azure CLI

## ☁️ **Cloud-Specific Setup**

### **Azure Prerequisites**
```bash
# Install Azure CLI
az login

# Create resource groups (required)
# Test environment
az group create --name aks-test --location "Switzerland North"

# Production environment (name to be determined)
az group create --name aks-prod --location "Switzerland North"
```

### **Stoney cloud Prerequisites**
```bash
# Install OpenStack CLI
# Source your OpenStack RC file or set environment variables
source your-project-openrc.sh

# Create keypair (required)
openstack keypair create --public-key ~/.ssh/id_rsa.pub aihub-keypair-dev
```

### **Accessing Stoney Kubernetes Cluster**

After successful deployment, set up kubectl access to your cluster:

```bash
# Get cluster name (automatically generated)
CLUSTER_NAME="aihub-stoney-test"  # or aihub-stoney-prod

# Create .kube directory if it doesn't exist
mkdir -p ~/.kube

# Download kubeconfig for the cluster
openstack coe cluster config --dir ~/.kube "$CLUSTER_NAME"

# Verify cluster access
kubectl get nodes -o wide
```

**Alternative kubeconfig location:**
```bash
# If you want to store kubeconfig in a different location
export KUBECONFIG=/path/to/your/kubeconfig
openstack coe cluster config --dir /path/to/your/directory "$CLUSTER_NAME"
```

**Verify cluster is healthy:**
```bash
# Check cluster status
openstack coe cluster list

# Check nodes
kubectl get nodes

# Check system pods
kubectl get pods -A
```

## 🎯 **Key Features**

✅ **No manual configuration** - All variables injected automatically  
✅ **Simple command** - One script for both clouds  
✅ **Environment support** - dev/test/prod environments  
✅ **Prerequisites checking** - Validates cloud access  
✅ **Consistent naming** - Same patterns across clouds  
✅ **Cost optimization** - Spot instances for user nodes (Azure)  

## 📊 **What Gets Created**

### **Azure**
- AKS cluster with system and user node pools
- Spot instances for cost optimization
- System-assigned managed identity
- OIDC issuer and workload identity enabled

### **Stoney cloud**
- Magnum Kubernetes cluster
- Network, subnet, and router
- Cluster template with proper image
- Node groups for system and user nodes

## 🔍 **Examples**

```bash
# Plan Azure test environment
./deploy.sh azure test plan

# Deploy Stoney cloud prod environment
./deploy.sh stoney prod apply

# Destroy Azure test environment
./deploy.sh azure test destroy

# Show help
./deploy.sh
```

## 🎉 **That's It!**

No complex configuration files, no manual copying, no modules to understand. Just run the script with your cloud provider and you're done!