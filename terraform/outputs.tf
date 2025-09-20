output "resource_group_name" {
  value       = data.azurerm_resource_group.rg.name
  description = "Resource group name"
}

output "aks_name" {
  value       = azurerm_kubernetes_cluster.aks.name
  description = "AKS cluster name"
}

output "kube_config" {
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
  description = "Raw kubeconfig for kubectl access"
}



