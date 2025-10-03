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
