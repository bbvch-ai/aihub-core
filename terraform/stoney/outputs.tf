output "cluster_id" {
  description = "OpenStack cluster ID"
  value       = openstack_containerinfra_cluster_v1.cluster.id
}

output "cluster_name" {
  description = "OpenStack cluster name"
  value       = openstack_containerinfra_cluster_v1.cluster.name
}


output "cluster_api_address" {
  description = "OpenStack cluster API address"
  value       = openstack_containerinfra_cluster_v1.cluster.api_address
}

output "kubeconfig_instructions" {
  description = "Instructions to get kubeconfig"
  value       = "Run: openstack coe cluster config --dir ~/.kube ${openstack_containerinfra_cluster_v1.cluster.name}"
}

output "ingress_floating_ip" {
  description = "Floating IP address for ingress controller LoadBalancer"
  value       = local.ingress_ip != null ? local.ingress_ip : "NOT_SET - Allocate manually: openstack floating ip create public"
}

output "ingress_ip_configuration" {
  description = "Instructions for configuring ingress controller with floating IP"
  value       = local.ingress_ip != null ? join("\n", [
    "Floating IP for Ingress Controller: ${local.ingress_ip}",
    "",
    "This IP was allocated MANUALLY outside Terraform and will persist across cluster destroy/recreate.",
    "",
    "To use this IP with nginx-ingress-controller, set the following in your helm values:",
    "  --set controller.service.loadBalancerIP=${local.ingress_ip}",
    "",
    "Or add to values.yaml:",
    "  controller:",
    "    service:",
    "      loadBalancerIP: \"${local.ingress_ip}\""
  ]) : join("\n", [
    "⚠️  WARNING: No floating IP configured!",
    "",
    "To allocate a persistent floating IP:",
    "1. Run: openstack floating ip create public --description \"aihub-${var.environment}-ingress\"",
    "2. Add the IP to ${var.environment}.auto.tfvars:",
    "   ingress_loadbalancer_ip = \"YOUR_ALLOCATED_IP\"",
    "3. Run: terraform apply again"
  ])
}
