# =============================================================================
# AZURE TERRAFORM VARIABLES
# =============================================================================

# Common variables (injected by deploy script)
variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version to use"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
}

variable "system_node_count" {
  description = "Number of system nodes"
  type        = number
}

variable "system_os_disk_size_gb" {
  description = "OS disk size for system nodes (GB)"
  type        = number
}

variable "user_node_count" {
  description = "Number of user nodes (fixed, no autoscaling)"
  type        = number
  default     = 0
}

variable "user_os_disk_size_gb" {
  description = "OS disk size for user nodes (GB)"
  type        = number
}

variable "tag_project" {
  description = "Project tag"
  type        = string
}

variable "tag_environment" {
  description = "Environment tag"
  type        = string
}

variable "tag_cloud" {
  description = "Cloud provider tag"
  type        = string
}

variable "tag_managed_by" {
  description = "Managed by tag"
  type        = string
}

# Azure-specific variables

variable "resource_group_name" {
  description = "Azure resource group name (must exist)"
  type        = string
  default     = "aihub-rg"
}

variable "system_vm_size" {
  description = "Azure VM size for system pool"
  type        = string
  default     = "Standard_D4s_v5"
}

variable "user_vm_size" {
  description = "Azure VM size for user pool"
  type        = string
  default     = "Standard_D4as_v5"
}

variable "user_spot_max_price" {
  description = "Max price for Azure Spot nodes (USD/hr). -1 for pay up to on-demand"
  type        = number
  default     = -1
}

variable "network_plugin" {
  description = "Azure CNI plugin (azure or kubenet)"
  type        = string
  default     = "azure"
}

variable "outbound_type" {
  description = "Azure outbound type (loadBalancer or userDefinedRouting)"
  type        = string
  default     = "loadBalancer"
}
