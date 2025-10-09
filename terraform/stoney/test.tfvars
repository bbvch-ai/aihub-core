# Stoney cloud-specific defaults
cluster_name = "aihub-test"
project_name = "aihub"
environment = "test"
region = "RegionOne"
availability_zone = "nova"
keypair_name = "aihub-keypair-test"  # Will be set by deploy script
kubernetes_version = "1.32.8"
image_id = "30ae0fa6-41e1-44de-991b-35be0e10a51f"
flavor_system = "Standard Düdingen c004m0008"
flavor_user = "Standard Düdingen c004m0008"
network_name = "aihub-network-temporary"  # Will be set by deploy script
#subnet_cidr = "10.0.0.0/24"
external_network = "public"

# Use existing Magnum cluster template (provided by Stoney cloud)
#cluster_template_id = "4825d2b9-0e12-48ae-be71-d6a8642ec846"

# Docker volume configuration
docker_volume_size = 64

# Node configuration
system_node_count = 1
system_os_disk_size_gb = 64
user_node_count = 2
user_os_disk_size_gb = 64

# Floating IP for ingress controller
# Set to empty to allocate new IP, then update this value after first deployment
ingress_loadbalancer_ip = "185.85.126.222"

# Tags
tag_project = "aihub"
tag_environment = "test"
tag_cloud = "stoney"
tag_managed_by = "terraform"
