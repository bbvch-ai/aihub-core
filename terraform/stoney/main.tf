terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.48.0"
    }
  }
}

# Data sources for OpenStack resources
locals {
  selected_image_id = var.image_id != "" ? var.image_id : data.openstack_images_image_v2.kubernetes_image[0].id
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

# Create cluster template for Magnum
resource "openstack_containerinfra_clustertemplate_v1" "cluster_template" {
  name                = "${var.cluster_name}-template"
  coe                 = "kubernetes"
  image               = local.selected_image_id
  external_network_id = data.openstack_networking_network_v2.external_network.id
  master_flavor       = data.openstack_compute_flavor_v2.system_flavor.id
  flavor              = data.openstack_compute_flavor_v2.user_flavor.id
  master_lb_enabled   = true
  floating_ip_enabled = true
  network_driver      = "flannel"
  volume_driver       = "cinder"
  docker_volume_size  = 25
  server_type         = "vm"
  cluster_distro      = "ubuntu"
  docker_storage_driver = "overlay2"
  public              = true
  tls_disabled        = false
  registry_enabled    = false
}

# Create the Kubernetes cluster using Magnum
resource "openstack_containerinfra_cluster_v1" "cluster" {
  name                = var.cluster_name
  cluster_template_id = openstack_containerinfra_clustertemplate_v1.cluster_template.id
  master_count        = 1  # Must be odd for etcd
  node_count          = var.system_node_count
  keypair             = var.keypair_name

  # Wait for cluster to be ready
  depends_on = [
    openstack_networking_router_interface_v2.cluster_router_interface
  ]
}

# Create additional node group for user nodes (if needed)
resource "openstack_containerinfra_nodegroup_v1" "user_nodes" {
  count = var.user_max_count > 0 ? 1 : 0
  
  cluster_id     = openstack_containerinfra_cluster_v1.cluster.id
  name           = "user-nodes"
  node_count     = var.user_min_count
  flavor_id      = data.openstack_compute_flavor_v2.user_flavor.id
  image_id       = local.selected_image_id
  min_node_count = var.user_min_count
  max_node_count = var.user_max_count
}
