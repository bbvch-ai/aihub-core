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

data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

locals {
  aks_name = var.cluster_name
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = local.aks_name
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  dns_prefix          = replace(local.aks_name, "_", "-")

  kubernetes_version = var.kubernetes_version

  default_node_pool {
    name                         = var.system_pool_name
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

  tags = var.tags
}

# Cost-saving CPU user pool on Spot, autoscaling down to 0
resource "azurerm_kubernetes_cluster_node_pool" "cpu_spot" {
  name                  = var.user_pool_name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.user_vm_size
  mode                  = "User"
  min_count             = var.user_min_count
  max_count             = var.user_max_count
  os_disk_size_gb       = var.user_os_disk_size_gb

  # Spot specifics
  priority         = "Spot"
  eviction_policy  = "Delete"
  spot_max_price   = var.user_spot_max_price

  node_labels = {
    "pool"                                      = var.user_pool_name
    "kubernetes.azure.com/scalesetpriority"     = "spot"
  }

  node_taints = [
    "spot=true:NoSchedule"
  ]

  tags = var.tags
}




