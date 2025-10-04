# =============================================================================
# OPENSTACK TERRAFORM VARIABLES
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

variable "user_min_count" {
  description = "Minimum number of user nodes"
  type        = number
}

variable "user_max_count" {
  description = "Maximum number of user nodes"
  type        = number
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

# OpenStack-specific variables
variable "region" {
  description = "OpenStack region"
  type        = string
  default     = "RegionOne"
}

variable "availability_zone" {
  description = "OpenStack availability zone"
  type        = string
  default     = "nova"
}

variable "keypair_name" {
  description = "OpenStack keypair name for SSH access"
  type        = string
  default     = "aihub-keypair"
}

variable "image_name" {
  description = "OpenStack image name for nodes"
  type        = string
  default     = "Ubuntu 22.04 (240702): Kubernetes v1.30.2"
}

variable "image_id" {
  description = "Optional explicit image ID to use (overrides image_name lookup)"
  type        = string
  default     = ""
}

variable "flavor_system" {
  description = "OpenStack flavor for system nodes"
  type        = string
  default     = "Standard Düdingen c002m0004"
}

variable "flavor_user" {
  description = "OpenStack flavor for user nodes"
  type        = string
  default     = "Standard Düdingen c002m0004"
}

variable "network_name" {
  description = "OpenStack network name for the cluster"
  type        = string
  default     = "aihub-network"
}

variable "subnet_cidr" {
  description = "CIDR block for the OpenStack subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "external_network" {
  description = "OpenStack external network name for floating IPs"
  type        = string
  default     = "public"
}

# Optional: Use an existing Magnum cluster template instead of creating one
variable "cluster_template_id" {
  description = "Existing OpenStack Magnum cluster template ID to use"
  type        = string
  validation {
    condition     = length(var.cluster_template_id) > 0
    error_message = "You must provide a non-empty cluster_template_id for Stoney deployments."
  }
}

variable "docker_volume_size" {
  description = "Docker volume size for the cluster nodes"
  type        = number
  default     = 25
}
