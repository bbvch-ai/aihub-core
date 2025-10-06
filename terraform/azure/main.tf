terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.80.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.1"
    }
  }
}

provider "azurerm" {
  features {}
}

# Data source for existing resource group
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

# AKS cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  dns_prefix          = replace(var.cluster_name, "_", "-")

  kubernetes_version = var.kubernetes_version

  default_node_pool {
    name                         = "system"
    vm_size                      = var.system_vm_size
    node_count                   = var.system_node_count
    os_disk_size_gb              = var.system_os_disk_size_gb
    type                         = "VirtualMachineScaleSets"
    only_critical_addons_enabled = true
    orchestrator_version         = var.kubernetes_version
  }

  identity {
    type = "SystemAssigned"
  }

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  network_profile {
    network_plugin = var.network_plugin
    outbound_type  = var.outbound_type
  }

  tags = {
    project     = var.tag_project
    environment = var.tag_environment
    cloud       = var.tag_cloud
    managed_by  = var.tag_managed_by
  }
}

# User node pool (Spot instances for cost optimization)
resource "azurerm_kubernetes_cluster_node_pool" "user_pool" {
  count                 = var.user_node_count > 0 ? 1 : 0
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.user_vm_size
  mode                  = "User"
  node_count            = var.user_node_count
  os_disk_size_gb       = var.user_os_disk_size_gb

  # Use regular VMs to avoid LowPriorityCores quota
  priority = "Regular"

  node_labels = {
    "pool" = "user"
  }

  # No taints when not using Spot

  tags = {
    project     = var.tag_project
    environment = var.tag_environment
    cloud       = var.tag_cloud
    managed_by  = var.tag_managed_by
  }
}
