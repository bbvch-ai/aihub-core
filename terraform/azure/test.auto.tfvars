# Azure-specific defaults
resource_group_name = "aks-test"
kubernetes_version = "1.30.2"
system_vm_size = "Standard_D4s_v5"
user_vm_size = "Standard_D4as_v5"
user_spot_max_price = -1
network_plugin = "azure"
outbound_type = "loadBalancer"

# Node configuration
system_node_count = 1
system_os_disk_size_gb = 64
user_min_count = 0
user_max_count = 3
user_os_disk_size_gb = 128
