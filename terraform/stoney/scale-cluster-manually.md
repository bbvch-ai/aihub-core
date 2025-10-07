# Manual Cluster Scaling Guide

## Problem
**Stoney Cloud's OpenStack Magnum does NOT support updating `node_count` after cluster creation** via Terraform or API updates. The error message is:
```
Updating a cluster in this way is not currently supported
```

This is a **limitation of their Magnum deployment**, not a Terraform bug.

## Solution Options

### Option 1: Scale via OpenStack Horizon (Web UI)
1. Log in to https://os.stoney-cloud.com
2. Navigate to: **Container Infra → Clusters**
3. Click on cluster: `aihub-stoney-test`
4. Click **Update Cluster** or **Resize Cluster** (if available)
5. Change **Node Count** from `4` to `5`
6. Apply changes

### Option 2: Scale via OpenStack CLI ✅ **RECOMMENDED**
If you have OpenStack credentials configured:

```bash
# Export OpenStack credentials
source ~/dev/stoney.sh

# IMPORTANT: Use 'resize' not 'update'!
# The 'update' command doesn't work - you'll get "not currently supported" error
openstack coe cluster resize aihub-stoney-test 5

# Monitor the status
openstack coe cluster show aihub-stoney-test | grep -E "(status|node_count)"

# Wait for status to become UPDATE_COMPLETE and node_count to change to 5
# Then verify in Kubernetes
kubectl get nodes
```

**Note**: `openstack coe cluster update` does NOT work. You MUST use `openstack coe cluster resize`.

### Option 3: Scale via Heat Stack (Direct)
The cluster is backed by a Heat stack. You can update it directly:

```bash
# Find the Heat stack ID
openstack stack list | grep aihub-stoney-test

# Update the stack parameter
openstack stack update <STACK_ID> --parameter node_count=5

# Monitor the update
openstack stack show <STACK_ID>
```

### Option 4: Scale via Kubernetes Node Autoscaler
If the cluster has cluster-autoscaler installed, you can scale by adjusting workload demands.

### Option 5: Contact Stoney Cloud Support
Ask if there's a supported way to scale clusters, or if this is a known limitation:
- **Issue**: Cannot update `node_count` via Terraform or API after cluster creation
- **Cluster ID**: `16253de2-db08-4c53-bce6-4183842a53e4`
- **Error**: `Updating a cluster in this way is not currently supported`
- **Request**: Is there a resize/scale operation available?

### Option 6: Use Kubernetes Cluster Autoscaler
Instead of manually managing node count, deploy the Kubernetes Cluster Autoscaler which can automatically add/remove nodes based on pod resource requests.

## After Manual Scaling
Once the cluster is scaled to 5 nodes manually:

```bash
cd terraform/stoney

# Refresh Terraform state to match reality
terraform refresh

# Verify state matches
terraform plan  # Should show "No changes"
```

## Future Terraform Updates
The `lifecycle { ignore_changes = [node_count, docker_volume_size] }` block prevents Terraform from attempting unsupported updates. To scale in the future:

1. Update `user_node_count` in `test.auto.tfvars` (for documentation purposes)
2. Scale manually using one of the options above
3. Run `terraform refresh` to sync state

## If Stoney Cloud Adds Update Support
If Stoney Cloud enables cluster updates in the future:
1. Remove the `lifecycle { ignore_changes }` block from `main.tf`
2. Terraform will resume managing node_count automatically

## Alternative: Recreate Cluster
If manual scaling doesn't work and you need a different size:
1. Update `user_node_count` in `test.auto.tfvars`
2. Run `terraform destroy` (backup data first!)
3. Run `terraform apply` to create a new cluster with the desired size

