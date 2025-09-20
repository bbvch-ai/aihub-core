# AKS (CPU-only, cost-optimized) Terraform

This Terraform creates an AKS cluster optimized for CPU-only workloads with a small on-demand system pool and a Spot user pool that can scale to zero.

## Files
- `main.tf` – providers, resource group, AKS, spot node pool
- `variables.tf` – tunables (region, sizes, counts, pricing, subscription)
- `outputs.tf` – cluster name and kubeconfig

## Default Configuration
- **Resource Group**: `aks-test` (must exist, will not be created/modified)
- **Cluster Name**: `aihub-aks-test` (fixed name for reliable updates)
- **Subscription**: `57b3a4d4-5044-48ba-b2d7-83155639b3a6`
- **System pool**: `Standard_B2als_v2` (1 node, fixed)
- **User pool (Spot)**: `Standard_D4as_v5`, 0 nodes (autoscaling disabled)

## Usage
```bash
# 1) Login to Azure
az login

# 2) Set subscription ID (required for Terraform)
export ARM_SUBSCRIPTION_ID=57b3a4d4-5044-48ba-b2d7-83155639b3a6

# 3) Initialize Terraform
cd terraform
terraform init

# 4) Plan deployment
terraform plan

# 5) Apply configuration
terraform apply

# 6) Configure kubectl
terraform output -raw kube_config > kubeconfig
export KUBECONFIG=$PWD/kubeconfig
kubectl get nodes
```

## Customization
Override defaults with variables:
```bash
terraform plan \
  -var resource_group_name=my-existing-rg \
  -var cluster_name=my-cluster-name \
  -var user_vm_size=Standard_D2as_v5 \
  -var user_max_count=5
```

**Notes**: 
- The resource group must already exist and will not be created or modified
- The cluster name is fixed to avoid recreation on updates
- To enable autoscaling, set `user_max_count` > `user_min_count`

## Cost Optimization
- **Spot pricing**: 60-90% savings on user workloads
- **Scale to zero**: User pool scales down when idle
- **Small system pool**: Minimal baseline cost
- **Taint handling**: Only fault-tolerant workloads run on Spot

## Cleanup
To destroy the infrastructure and avoid ongoing costs:
```bash
# Destroy all resources
terraform destroy

# Or destroy with auto-approval (be careful!)
terraform destroy -auto-approve
```
