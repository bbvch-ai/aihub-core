variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "aihub"
}

variable "cluster_name" {
  description = "AKS cluster name"
  type        = string
  default     = "aihub-aks-test"
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = "57b3a4d4-5044-48ba-b2d7-83155639b3a6"
}

variable "resource_group_name" {
  description = "Resource group name (must exist)"
  type        = string
  default     = "aks-test"
}

variable "kubernetes_version" {
  description = "AKS version to use"
  type        = string
  default     = "1.30.2"
}

variable "network_plugin" {
  description = "CNI plugin (azure or kubenet)"
  type        = string
  default     = "azure"
}

variable "outbound_type" {
  description = "Outbound type (loadBalancer or userDefinedRouting)"
  type        = string
  default     = "loadBalancer"
}

variable "system_pool_name" {
  description = "Name of the system node pool"
  type        = string
  default     = "system"
}

variable "system_vm_size" {
  description = "VM size for system pool"
  type        = string
  # B2als_v2 is cheap for system pods; alternative: D2as_v5
  default     = "Standard_B2als_v2"
}

variable "system_node_count" {
  description = "Node count for system pool"
  type        = number
  default     = 1
}

variable "system_os_disk_size_gb" {
  description = "OS disk size for system pool"
  type        = number
  default     = 64
}

variable "user_pool_name" {
  description = "Name of the user CPU spot pool"
  type        = string
  default     = "cpuspot"
}

variable "user_vm_size" {
  description = "VM size for user CPU spot pool"
  type        = string
  # D4as_v5 is a good balance; cheap alternative: D2as_v5
  default     = "Standard_D4as_v5"
}

variable "user_min_count" {
  description = "Min nodes for user pool"
  type        = number
  default     = 0
}

variable "user_max_count" {
  description = "Max nodes for user pool"
  type        = number
  default     = 0
}

variable "user_os_disk_size_gb" {
  description = "OS disk size for user pool"
  type        = number
  default     = 128
}

variable "user_spot_max_price" {
  description = "Max price for Spot node (USD/hr). -1 for pay up to on-demand"
  type        = number
  default     = -1
}

variable "tags" {
  description = "Tags to apply to AKS cluster and node pools"
  type        = map(string)
  default     = {
    project = "aihub"
    env     = "dev"
  }
}



