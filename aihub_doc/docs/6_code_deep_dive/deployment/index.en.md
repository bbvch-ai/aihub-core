## Setup Openstack

See https://docs.infomaniak.cloud/getting_started/first_project/create_a_project/ for how to create a new project in
Infomaniak Openstack.

On local machine install the Openstack CLI tools:

```bash
pip install python-openstackclient
```

```bash
openstack --os-cloud PCP-XXXXXX-dc3-a keypair create <key_name> > ~/.ssh/<key_name>
```

```bash
openstack --os-cloud PCP-XXXXXX-dc3-a server create --image "Ubuntu 22.04 LTS Jammy Jellyfish" --flavor a12-ram48-disk50-perf1 --key-name <key_name> --network ext-net1 <name_of_instance>

```

## Setup Ansible

Make sure your local machine has python and pip installed. Now make sure you install the ansible-navigator:

# \`\`\`bash

pip install ansible-navigator

````

Check if the installation was successful by running:

```bash
ansible-navigator --version
````
