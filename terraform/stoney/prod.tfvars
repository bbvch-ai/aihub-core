# Stoney cloud-specific defaults
cluster_name = "aihub-prod"
project_name = "aihub"
environment = "prod"
region = "RegionOne"
availability_zone = "nova"
keypair_name = "aihub-keypair-prod"  # Will be set by deploy script
kubernetes_version = "1.32.8"
image_id = "30ae0fa6-41e1-44de-991b-35be0e10a51f"
flavor_system = "Standard Düdingen c004m0008"
flavor_user = "Standard Düdingen c004m0008"
network_name = "aihub-network-temporary"  # Will be set by deploy script
#subnet_cidr = "10.0.0.0/24"
external_network = "public"

# Use existing Magnum cluster template (provided by Stoney cloud)
cluster_template_id = "4825d2b9-0e12-48ae-be71-d6a8642ec846"

# Docker volume configuration
docker_volume_size = 64

# Node configuration
system_node_count = 1
system_os_disk_size_gb = 64
user_node_count = 5
user_os_disk_size_gb = 64

# Floating IP for ingress controller
# Leave empty to allocate a new IP (first deployment)
# After first deployment, set this to the allocated IP from terraform output
ingress_loadbalancer_ip = "185.85.126.232"

# Tags
tag_project = "aihub"
tag_environment = "prod"
tag_cloud = "stoney"
tag_managed_by = "terraform"
