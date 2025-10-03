output "cluster_id" {
  description = "Azure AKS cluster ID"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "cluster_name" {
  description = "Azure AKS cluster name"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "cluster_fqdn" {
  description = "Azure AKS cluster FQDN"
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "kube_config" {
  description = "Raw kubeconfig for kubectl access"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "resource_group_name" {
  description = "Azure resource group name"
  value       = data.azurerm_resource_group.rg.name
}

output "resource_group_location" {
  description = "Azure resource group location"
  value       = data.azurerm_resource_group.rg.location
}
