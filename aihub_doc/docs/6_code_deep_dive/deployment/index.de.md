---
title: Bereitstellung
index: 10
source_sha: "31d8a6b62472cc22c3e8e614292610e9b24e587d680fbd0edc3b5124ed11a9b3"
---

# Bereitstellung

## Openstack einrichten

Unter https://docs.infomaniak.cloud/getting_started/first_project/create_a_project/ erfahren Sie, wie Sie ein neues Projekt in
Infomaniak Openstack erstellen.

Installieren Sie auf der lokalen Maschine die Openstack CLI-Tools:

```bash
pip install python-openstackclient
```

```bash
openstack --os-cloud PCP-XXXXXX-dc3-a keypair create <key_name> > ~/.ssh/<key_name>
```

```bash
openstack --os-cloud PCP-XXXXXX-dc3-a server create --image "Ubuntu 22.04 LTS Jammy Jellyfish" --flavor a12-ram48-disk50-perf1 --key-name <key_name> --network ext-net1 <name_of_instance>

```

## Ansible einrichten

Stellen Sie sicher, dass auf Ihrer lokalen Maschine Python und pip installiert sind. Installieren Sie nun den ansible-navigator:

```bash
pip install ansible-navigator
```

Überprüfen Sie die erfolgreiche Installation, indem Sie Folgendes ausführen:

```bash
ansible-navigator --version
```
