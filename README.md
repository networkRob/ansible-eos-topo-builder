# Ansible ESXI Topology Builder

This script will help create the necessary files to run an Ansible-Playbook.  The `build` script will call `setup.py` (which is used to create a customized Layer3 Leaf-Spine (L3LS) topology,) and then an `ansible-playbook`.   

The topology built with this script is a L3LS network, where each Leaf switch pairs are connected to each other so they can be in a MLAG domain.  The script will build an isoloated vSwitch based on the name for the topology.  All port-groups created are contained within this single vSwitch. 

This may take serveral minutes for the topology to be built, depending on the size for the topology.

## Rev2.0
This release adds support for Ansible-Vault to encrypt any and all passwords used throughout this script.  The `vault_pwd` file is not tracked via Git and contains the password used for all ansible-vaults created in this script.  

### Typical Port Mappings
#### Spine Switches
- Ethernet1 -> Rack1-Leaf1
- Ethernet2 -> Rack2-Leaf2
- And so on

#### Leaf Switches
Example of a 2 spine 4 leaf topo.  
- Ethernet1 -> "Peer Leaf switch within rack (To be used for MLAG)"
- Ethernet2 -> Link to Spine1
- Ethernet3 -> Link to Spine2
- Ethernet4 -> Additional Link that can connect to a vm/host for testing

## Requirements
You will need the following to make this project work:
* This project uses Ansible to build. This has been tested on 2.7 but should work in previous versions.
* You will need SSH enabled on your ESXi server
* You will need a copy of VMware's `ovftool` in `/files`
* A working ESXi host. All you really need for this is a management IP address and a single datastore.
* You will need the Arista EOS OVA file. Put it in `files/`


## Python Package Dependencies
Here is a list of packages that are required to run `setup.py` and the ansible-playbook
- ruamel.yaml
- ansible
- ansible-vault

## How-To
To run this script, verify all Requirements and Python Package Dependices have been fulfilled. Then to start building a topology to be deployed, run `./build`

Here is an example output of a topology being built.
```
$ ./build
============================================================================

Please answer the following questions to help customize your lab deployment.
============================================================================

How many spine switches will be used? 1
How many leaf switches will be used? 2
What is the name for this topology? AnsiblePush
What is the IP address or hostname for ESXI? esxi-02
What is the username for esxi-02? ansible
What is the password for ansible on esxi-02?
What is the name of the datastore to use on esxi-02? datastore1
What is the name of the EOS OVA? ie EOS-4.21.0F.ova: EOS-4.21.0F.ova
What is the name of the Port-Group for the EOS ma1 interface? LAB-MGMT
Power on the switches when done? (y/n) y
...
{Output of Ansible-Playbook removed}
...
```