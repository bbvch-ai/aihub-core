# Stoney cloud-specific defaults
region = "RegionOne"
availability_zone = "nova"
keypair_name = "aihub-keypair-test"  # Will be set by deploy script
kubernetes_version = "1.30.2"
image_name = "Ubuntu 22.04 (240702): Kubernetes v1.30.2"
image_id = "db68e8e8-d4b4-4c4f-af41-4166eb33973d"
flavor_system = "Standard Düdingen c002m0004"
flavor_user = "Standard Düdingen c002m0004"
network_name = "aihub-network-test"  # Will be set by deploy script
subnet_cidr = "10.0.0.0/24"
external_network = "public"

# Node configuration
system_node_count = 1
system_os_disk_size_gb = 64
user_min_count = 0
user_max_count = 3
user_os_disk_size_gb = 128
