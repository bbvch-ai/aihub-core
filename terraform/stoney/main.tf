terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1.0"
    }
  }
  
  # Backend configuration for state file location
  # Path will be configured via -backend-config during init
  backend "local" {
    # path will be set via backend config file
  }
}

# Data sources for OpenStack resources
locals {
  selected_image_id             = var.image_id != "" ? var.image_id : data.openstack_images_image_v2.kubernetes_image[0].id
  effective_cluster_template_id = var.cluster_template_id != "" ? var.cluster_template_id : openstack_containerinfra_clustertemplate_v1.generated[0].id
}

data "openstack_images_image_v2" "kubernetes_image" {
  count = var.image_id == "" ? 1 : 0
  name  = var.image_name
}

data "openstack_compute_flavor_v2" "system_flavor" {
  name = var.flavor_system
}

data "openstack_compute_flavor_v2" "user_flavor" {
  name = var.flavor_user
}

data "openstack_networking_network_v2" "external_network" {
  name = var.external_network
}

# Create a network for the cluster
resource "openstack_networking_network_v2" "cluster_network" {
  name           = "${var.cluster_name}-network"
  admin_state_up = true
}

# Create a subnet for the cluster
resource "openstack_networking_subnet_v2" "cluster_subnet" {
  name       = "${var.cluster_name}-subnet"
  network_id = openstack_networking_network_v2.cluster_network.id
  cidr       = var.subnet_cidr
  ip_version = 4
}

# Create a router for external connectivity
resource "openstack_networking_router_v2" "cluster_router" {
  name                = "${var.cluster_name}-router"
  external_network_id = data.openstack_networking_network_v2.external_network.id
}

# Connect the subnet to the router
resource "openstack_networking_router_interface_v2" "cluster_router_interface" {
  router_id = openstack_networking_router_v2.cluster_router.id
  subnet_id = openstack_networking_subnet_v2.cluster_subnet.id
}

resource "openstack_containerinfra_clustertemplate_v1" "generated" {
  count = var.cluster_template_id == "" ? 1 : 0

  name                = "${var.cluster_name}-template"
  coe                 = "kubernetes"
  image               = local.selected_image_id
  external_network_id = data.openstack_networking_network_v2.external_network.id
  master_lb_enabled   = true
  floating_ip_enabled = true
  network_driver      = "flannel"
  volume_driver       = "cinder"
  docker_volume_size    = var.docker_volume_size

  # Use flavors provided via variables
  flavor         = var.flavor_system
  master_flavor  = var.flavor_system

  labels = {
    kube_tag                 = var.kubernetes_version
    auto_scaling_enabled     = "false"
    min_node_count           = tostring(0)
    max_node_count           = tostring(0)
    admission_control_list   = "PodSecurityPolicy:False,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota"
  }
}

# Create the Kubernetes cluster using Magnum
resource "openstack_containerinfra_cluster_v1" "cluster" {
  name                = var.cluster_name
  cluster_template_id = local.effective_cluster_template_id
  master_count        = 1  # Must be odd for etcd
  node_count          = var.user_node_count
  keypair             = var.keypair_name
  docker_volume_size  = var.docker_volume_size

  # Wait for cluster to be ready
  depends_on = [
    openstack_networking_router_interface_v2.cluster_router_interface
  ]

  # LIMITATION: Stoney Cloud's OpenStack Magnum doesn't support updating node_count
  # after cluster creation. Error: "Updating a cluster in this way is not currently supported"
  # To scale: use OpenStack Horizon UI (Container Infra → Clusters → Resize) or OpenStack CLI
  lifecycle {
    ignore_changes = [
      node_count,
      docker_volume_size  # Also typically not updatable
    ]
  }
}

// No additional node groups; total workers are controlled via node_count

# =============================================================================
# FLOATING IP FOR INGRESS CONTROLLER
# =============================================================================

# IMPORTANT: For production use, floating IPs should be allocated MANUALLY
# outside of Terraform to ensure they persist across cluster destroy/recreate.
#
# To allocate manually:
#   openstack floating ip create public --description "aihub-${environment}-ingress"
#
# Then set the IP in your .auto.tfvars file:
#   ingress_loadbalancer_ip = "185.85.126.XXX"

# Data source to look up existing floating IP
# This is used to validate the IP exists and get its details
data "openstack_networking_floatingip_v2" "ingress_ip" {
  count   = var.ingress_loadbalancer_ip != "" ? 1 : 0
  address = var.ingress_loadbalancer_ip
}

# Local value to use throughout the configuration
locals {
  ingress_ip = var.ingress_loadbalancer_ip != "" ? var.ingress_loadbalancer_ip : null
}
