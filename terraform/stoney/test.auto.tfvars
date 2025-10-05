# Stoney cloud-specific defaults
region = "RegionOne"
availability_zone = "nova"
keypair_name = "aihub-keypair-test"  # Will be set by deploy script
kubernetes_version = "1.30.2"
image_name = "Ubuntu 22.04 (240702): Kubernetes v1.30.2"
image_id = "db68e8e8-d4b4-4c4f-af41-4166eb33973d"
flavor_system = "Standard Düdingen c004m0008"
flavor_user = "Standard Düdingen c004m0008"
network_name = "aihub-network-test"  # Will be set by deploy script
subnet_cidr = "10.0.0.0/24"
external_network = "public"

# Use existing Magnum cluster template (provided by Stoney cloud)
cluster_template_id = "4825d2b9-0e12-48ae-be71-d6a8642ec846"

# Docker volume configuration
docker_volume_size = 25

# Node configuration
system_node_count = 1
system_os_disk_size_gb = 64
user_node_count = 3
user_os_disk_size_gb = 128
